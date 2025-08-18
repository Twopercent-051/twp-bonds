import asyncio
from datetime import datetime
from typing import Literal

import aiohttp
from aiohttp import ClientConnectorError, ClientPayloadError, ClientResponseError, ServerTimeoutError
from bs4 import BeautifulSoup

from config import config
from create_app import logger
from models.schemas import DbBondDTO, MoexBondDTO


class MoexAPI:

    @staticmethod
    async def __get_request(section: Literal["TQOB", "TQCB"], retries: int = 10, delay: float = 3) -> str:
        url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/boards/{section}/securities.xml"
        attempt = 0
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url, proxy=config.rus_proxy) as resp:
                        if resp.status == 200:
                            return await resp.text()
                        else:
                            logger.warning(f"MOEX RESP NON-200: {resp.status}")
                            raise ClientResponseError(resp.request_info, resp.history, status=resp.status)
            except (ConnectionResetError, ClientConnectorError, ClientPayloadError, ServerTimeoutError) as ex:
                attempt += 1
                logger.warning(f"Попытка {attempt}/{retries} не удалась: {ex!r}")
                if attempt >= retries:
                    raise
                await asyncio.sleep(delay)
            except Exception as ex:
                logger.error(f"Неожиданная ошибка при запросе MOEX: {ex!r}")
                raise

    @staticmethod
    async def __get_one_bond_data(moex_data_list: list[str], sql_bond: DbBondDTO) -> MoexBondDTO | None:
        for moex_data in moex_data_list:
            soup = BeautifulSoup(moex_data, features="xml")
            rows = soup.find(name="data", attrs={"id": "securities"}).find_all("row")
            for row in rows:
                if row["SECID"] == sql_bond.isin:
                    redemption_date = row["MATDATE"] if row["BUYBACKDATE"] == "0000-00-00" else row["BUYBACKDATE"]
                    redemption_date = datetime.strptime(redemption_date, "%Y-%m-%d").date()
                    coupon_date = datetime.strptime(row["NEXTCOUPON"], "%Y-%m-%d").date()
                    nominal = int(row["FACEVALUE"]) * sql_bond.amount * 100
                    price = int(float(row["PREVWAPRICE"]) * nominal * 0.01)
                    nkd = int(float(row["ACCRUEDINT"]) * sql_bond.amount * 100)
                    return MoexBondDTO(
                        id=sql_bond.id,
                        amount=sql_bond.amount,
                        title=row["SECNAME"],
                        isin=sql_bond.isin,
                        coupon_date=coupon_date,
                        coupon_price=int(float(row["COUPONVALUE"]) * sql_bond.amount * 100),
                        nominal=nominal,
                        price=price + nkd,
                        redemption_date=redemption_date,
                        cur_coupon=sql_bond.cur_coupon,
                        cur_nominal=sql_bond.cur_nominal,
                    )
        return None

    @classmethod
    async def get_bonds_profiles(cls, sql_bonds: list[DbBondDTO]) -> list[MoexBondDTO]:
        ofz_moex_data = await cls.__get_request(section="TQOB")
        other_moex_data = await cls.__get_request(section="TQCB")
        result = []
        for sql_bond in sql_bonds:
            bond_data = await cls.__get_one_bond_data(
                moex_data_list=[other_moex_data, ofz_moex_data], sql_bond=sql_bond
            )
            result.append(bond_data)
        return sorted(result, key=lambda bond: bond.coupon_date)

    @classmethod
    async def get_one_bond_profile(cls, db_bond: DbBondDTO) -> MoexBondDTO | None:
        ofz_moex_data = await cls.__get_request(section="TQOB")
        other_moex_data = await cls.__get_request(section="TQCB")
        bond_data = await cls.__get_one_bond_data(
            moex_data_list=[other_moex_data, ofz_moex_data],
            sql_bond=db_bond,
        )
        return bond_data
