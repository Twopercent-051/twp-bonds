from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from models.sql_dao import BondsDAO

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    text = "Введи ISIN и количество через пробел"
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
    sql_bond = await BondsDAO.get_one_or_none(isin=isin)
    if sql_bond:
        await BondsDAO.update_by_id(item_id=sql_bond.id, amount=sql_bond.amount + amount)
    else:
        await BondsDAO.create_with_return_id(isin=isin, amount=amount)
    text = "Сохранили"
    await message.answer(text=text)
