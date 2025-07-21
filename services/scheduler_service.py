import asyncio
from datetime import datetime, timedelta
from operator import itemgetter
from typing import Literal

from config import config
from create_app import bot, logger, scheduler
from models.schemas import MoexBondDTO
from models.sql_dao import MoneyBalanceDAO, BondsDAO
from services.moex import MoexAPI


class SchedulerService:

    @staticmethod
    async def __send_message(text: str):
        for chat in config.admin_ids:
            try:
                await bot.send_message(chat_id=chat, text=text)
            except Exception as ex:
                logger.warning(ex)

    @staticmethod
    async def __get_bond_profile(isin: str) -> MoexBondDTO | None:
        sql_bond = await BondsDAO.get_one_or_none(isin=isin)
        if not sql_bond:
            return None
        moex_bond = await MoexAPI.get_one_bond_profile(db_bond=sql_bond)
        if not moex_bond:
            return None
        return moex_bond

    @classmethod
    async def _coupon_payment(cls, isin: str):
        bond = await cls.__get_bond_profile(isin=isin)
        if not bond:
            return None
        text = f"💡 Выплачено <i>{round(bond.coupon_price/100, 2)}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
        await cls.__send_message(text=text)
        await MoneyBalanceDAO.create_with_return_id(
            amount=bond.coupon_price, description=f"coupon_payment {bond.title}"
        )
        await cls.__set_task(task="part", isin=isin, date=datetime.today() + timedelta(days=3))
        return None

    @classmethod
    async def _part_redemption(cls, isin: str):
        bond = await cls.__get_bond_profile(isin=isin)
        if not bond:
            return None
        diff = bond.nominal - bond.cur_nominal
        if diff == 0:
            return None
        text = f"💡 Частичное погашение <i>{diff * bond.amount}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
        await cls.__send_message(text=text)
        await BondsDAO.update_by_id(item_id=bond.id, cur_nominal=bond.nominal, cur_coupon=bond.coupon_price)
        await MoneyBalanceDAO.create_with_return_id(
            amount=int(diff * bond.amount * 100), description=f"part_redemption {bond.title}"
        )
        return None

    @classmethod
    async def _bond_redemption(cls, isin: str) -> bool:
        bond = await cls.__get_bond_profile(isin=isin)
        if not bond:
            return None
        if bond.redemption_date.date() != datetime.today():
            return False
        text = f"💡 Полное погашение <i>{bond.price}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
        await cls.__send_message(text=text)
        await MoneyBalanceDAO.create_with_return_id(amount=bond.price, description=f"bond_redemption {bond.title}")
        await BondsDAO.delete(isin=isin)
        return True

    @classmethod
    async def __set_task(cls, task: Literal["coupon", "part", "redemption"], isin: str, date: datetime):
        methods = {"coupon": cls._coupon_payment, "redemption": cls._bond_redemption, "part": cls._part_redemption}
        scheduler.add_job(
            func=methods[task],
            trigger="date",
            run_date=date.replace(hour=5, minute=0),
            kwargs={"isin": isin},
            misfire_grace_time=None,
        )

    @classmethod
    async def set_bond(cls, isin: str, coupon_date: datetime, redemption_date: datetime):
        await cls.__set_task(task="coupon", isin=isin, date=coupon_date)
        await cls.__set_task(task="redemption", isin=isin, date=redemption_date)

    @classmethod
    async def start(cls):
        scheduler.remove_all_jobs()
        sql_bonds = await BondsDAO.get_many()
        moex_bonds = await MoexAPI.get_bonds_profiles(sql_bonds=sql_bonds)
        for moex_bond in moex_bonds:
            await cls.set_bond(
                isin=moex_bond.isin, coupon_date=moex_bond.coupon_date, redemption_date=moex_bond.redemption_date
            )
        scheduler.start()

    @classmethod
    def get_scheduled_tasks(cls):
        jobs = scheduler.get_jobs()
        result = []
        for job in jobs:
            params = job.kwargs or {}
            isin = params.get("isin")
            func_name = job.func.__name__
            if func_name == "_coupon_payment":
                task = "coupon"
            elif func_name == "_bond_redemption":
                task = "redemption"
            elif func_name == "_part_redemption":
                task = "part"
            else:
                task = None
            if task and isin:
                result.append({"isin": isin, "task": task, "time": job.next_run_time})  # Время запуска
        result.sort(key=itemgetter("time"))
        return result
