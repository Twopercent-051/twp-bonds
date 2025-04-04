import asyncio
from datetime import datetime

from config import config
from create_app import bot, logger, scheduler
from models.schemas import MoexBondDTO
from models.sql_dao import MoneyBalanceDAO, BondsDAO
from services.moex import MoexAPI


async def __send_message(text: str):
    for chat in config.admin_ids:
        try:
            await bot.send_message(chat_id=chat, text=text)
        except Exception as ex:
            logger.warning(ex)


async def __coupon_payment(bond: MoexBondDTO):
    if bond.coupon_date != datetime.today():
        return
    text = f"💡 Выплачено <i>{bond.coupon_price}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
    await __send_message(text=text)
    await MoneyBalanceDAO.create_with_return_id(count=int(bond.coupon_price * 100), description="coupon payment")


async def __part_redemption(bond: MoexBondDTO):
    diff = bond.nominal - bond.cur_nominal
    if diff == 0:
        return
    text = (
        f"💡 Частичное погашение <i>{diff * bond.amount}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
    )
    await __send_message(text=text)
    await MoneyBalanceDAO.create_with_return_id(count=int(diff * bond.amount * 100), description="part redemption")
    # current_balance = await MoneyBalanceDAO.get_one_or_none()
    # await BondsDAO.update_by_id(item_id=bond.id, cur_nominal=bond.nominal)
    # await MoneyBalanceDAO.update_by_id(item_id=current_balance.id, balance=current_balance.balance + diff * bond.amount)


async def __bond_redemption(bond: MoexBondDTO) -> bool:
    if bond.redemption_date != datetime.today():
        return False
    text = f"💡 Полное погашение <i>{bond.price}₽</i> по облигации <i>{bond.title}</i> <i>({bond.amount}шт)</i>"
    await __send_message(text=text)
    text = f"💡 Выплачено <i>{bond.coupon_price}₽ по облигации <i>{bond.title}</i> ({bond.amount}шт)</i>"
    await __send_message(text=text)
    await MoneyBalanceDAO.create_with_return_id(
        count=bond.price + int(bond.coupon_price * 100), description="bond redemption"
    )
    # current_balance = await MoneyBalanceDAO.get_one_or_none()
    # await BondsDAO.delete(id=bond.id)
    # await MoneyBalanceDAO.update_by_id(
    #     item_id=current_balance.id, balance=current_balance.balance + bond.price + int(bond.coupon_price * 100)
    # )
    return True


async def __scheduler_dispatcher():
    sql_bonds = await BondsDAO.get_many()
    bonds = await MoexAPI.get_bonds_profiles(sql_bonds=sql_bonds)
    for bond in bonds:
        full_redemption = await __bond_redemption(bond=bond)
        if full_redemption:
            continue
        await __coupon_payment(bond=bond)
        await __part_redemption(bond=bond)


async def create_task():
    scheduler.add_job(
        func=__scheduler_dispatcher,
        trigger="cron",
        hour=5,
        minute=0,
        misfire_grace_time=None,
    )


if __name__ == "__main__":
    asyncio.run(__scheduler_dispatcher())
