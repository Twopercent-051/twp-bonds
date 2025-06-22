from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from models.sql_dao import BondsDAO, MoneyBalanceDAO, TransactionsDAO
from services.moex import MoexAPI

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    text = "Введи ISIN и количество через пробел"
    await message.answer(text=text)


@router.message(F.text.startswith("RUB"))
async def get_balance_handler(message: Message):
    try:
        value = int(message.text.split(" ")[1]) * 100
    except (IndexError, ValueError):
        text = "Неправильно"
        return await message.answer(text=text)
    current_value = await MoneyBalanceDAO.get_total()
    if value < 0:
        if current_value + value < 0:
            text = "Баланс не может быть отрицательным"
            return await message.answer(text=text)
    await MoneyBalanceDAO.create_with_return_id(amount=value, description="deposit")
    text = "Сохранили"
    await message.answer(text=text)
    return None


@router.message(F.text)
async def get_bond_handler(message: Message):
    if message.from_user.id not in config.admin_ids:
        text = "🔧 В данный момент бот недоступен. Обратитесь к администратору."
        return await message.answer(text=text)
    try:
        parts = message.text.split(" ")
        isin = parts[0]
        amount = int(parts[1])
    except (IndexError, ValueError):
        text = "Неправильный формат сообщения. Используйте: ISIN количество."
        return await message.answer(text=text)
    moex_bond = await MoexAPI.get_one_bond_profile(isin=isin, amount=amount)
    if not moex_bond:
        text = "Облигация не найдена по указанному ISIN."
        return await message.answer(text=text)
    sql_bond = await BondsDAO.get_one_or_none(isin=isin)
    if sql_bond:
        result = await TransactionsDAO.update_bond(
            isin=isin,
            amount=amount,
            price=int(moex_bond.price * 100),
            nominal=moex_bond.nominal,
            coupon=moex_bond.coupon_price,
        )
    else:
        result = await TransactionsDAO.create_bond(
            isin=isin,
            amount=amount,
            nominal=moex_bond.nominal,
            price=int(moex_bond.price * 100),
            coupon=moex_bond.coupon_price,
        )
    if not result:
        text = "Баланс не может быть отрицательным"
        await message.answer(text=text)
        return None
    text = "Сохранили"
    await message.answer(text=text)
    return None
