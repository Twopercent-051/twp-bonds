from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from models.sql_dao import BondsDAO, MoneyBalanceDAO
from services.moex import MoexAPI

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    text = "Введи ISIN и количество через пробел"
    await message.answer(text=text)


@router.message(F.text.startswith("RUB"))
async def get_balance_handler(message: Message):
    try:
        value = float(message.text.split(" ")[1])
    except (IndexError, ValueError):
        text = "Неправильно"
        return await message.answer(text=text)
    current_value = await MoneyBalanceDAO.get_one_or_none()
    if value < 0:
        if current_value.balance + value < 0:
            text = "Баланс не может быть отрицательным"
            return await message.answer(text=text)
    await MoneyBalanceDAO.update_by_id(item_id=current_value.id, balance=current_value.balance + value)
    text = "Сохранили"
    await message.answer(text=text)


@router.message(F.text)
async def get_bond_handler(message: Message):
    if message.from_user.id not in config.admin_ids:
        text = "🔧 В данный момент бот недоступен. Обратитесь к администратору."
        return await message.answer(text=text)
    try:
        isin = message.text.split(" ")[0]
        amount = int(message.text.split(" ")[1])
    except (IndexError, ValueError):
        text = "Неправильно"
        return await message.answer(text=text)
    moex_bond = await MoexAPI.get_one_bond_profile(isin=isin, amount=amount)
    if not moex_bond:
        text = "Not found"
        return await message.answer(text=text)
    current_balance = await MoneyBalanceDAO.get_one_or_none()
    if current_balance.balance < moex_bond.price:
        text = "Баланс не может быть отрицательным"
        return await message.answer(text=text)
    await MoneyBalanceDAO.update_by_id(item_id=current_balance.id, balance=current_balance.balance - moex_bond.price)
    sql_bond = await BondsDAO.get_one_or_none(isin=isin)
    if sql_bond:
        await BondsDAO.update_by_id(item_id=sql_bond.id, amount=sql_bond.amount + amount)
    else:
        await BondsDAO.create_with_return_id(isin=isin, amount=amount, nominal=moex_bond.nominal)
    text = "Сохранили"
    await message.answer(text=text)
