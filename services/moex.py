import asyncio
from datetime import datetime
from typing import Literal

import aiohttp
from bs4 import BeautifulSoup

from models.schemas import DbBondDTO, MoexBondDTO


class MoexAPI:

    @staticmethod
    async def __get_request(section: Literal["TQOB", "TQCB"]) -> str:
        url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/boards/{section}/securities.xml"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                return await resp.text()

    @staticmethod
    async def __get_one_bond_data(moex_data_list: list[str], sql_bond: DbBondDTO) -> MoexBondDTO:
        for moex_data in moex_data_list:
            soup = BeautifulSoup(moex_data, features="xml")
            rows = soup.find(name="data", attrs={"id": "securities"}).find_all("row")
            for row in rows:
                if row["SECID"] == sql_bond.isin:
                    redemption_date = row["MATDATE"] if row["BUYBACKDATE"] == "0000-00-00" else row["BUYBACKDATE"]
                    redemption_date = datetime.strptime(redemption_date, "%Y-%m-%d").date()
                    coupon_date = datetime.strptime(row["NEXTCOUPON"], "%Y-%m-%d").date()
                    price = round(
                        float(row["PREVWAPRICE"]) * int(row["FACEVALUE"]) * sql_bond.amount / 100,
                        2,
                    )
                    nkd = round(float(row["ACCRUEDINT"]) * sql_bond.amount, 2)
                    return MoexBondDTO(
                        id=sql_bond.id,
                        amount=sql_bond.amount,
                        title=row["SECNAME"],
                        isin=sql_bond.isin,
                        coupon_date=coupon_date,
                        coupon_price=round(float(row["COUPONVALUE"]) * sql_bond.amount, 2),
                        nominal=int(row["FACEVALUE"]) * sql_bond.amount,
                        price=round(price + nkd, 2),
                        redemption_date=redemption_date,
                        cur_nominal=sql_bond.cur_nominal,
                    )

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
    async def get_one_bond_profile(cls, isin: str, amount: int) -> MoexBondDTO | None:
        ofz_moex_data = await cls.__get_request(section="TQOB")
        other_moex_data = await cls.__get_request(section="TQCB")
        fake_sql_bond = DbBondDTO(isin=isin, amount=amount, id=0)
        bond_data = await cls.__get_one_bond_data(
            moex_data_list=[other_moex_data, ofz_moex_data],
            sql_bond=fake_sql_bond,
        )
        print(bond_data)
        return bond_data


if __name__ == "__main__":
    asyncio.run(MoexAPI.get_one_bond_profile(isin="RU000A1033B9", amount=1))
