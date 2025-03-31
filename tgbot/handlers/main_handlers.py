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
        value = int(message.text.split(" ")[1])
    except (IndexError, ValueError):
        text = "Неправильно"
        return await message.answer(text=text)
    current_value = await MoneyBalanceDAO.get_one_or_none()
    if value < 0:
        if current_value.balance + value < 0:
            text = "Баланс не может быть отрицательным"
            return await message.answer(text=text)
    await MoneyBalanceDAO.update_by_id(item_id=current_value.id, balance=current_value.balance + value * 100)
    text = "Сохранили"
    await message.answer(text=text)


from decimal import Decimal, ROUND_DOWN


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
    # price = Decimal(str(moex_bond.price))  # Цена облигации
    # # Получение текущего баланса
    # current_balance = await MoneyBalanceDAO.get_one_or_none()
    # if not current_balance:
    #     text = "Ошибка: баланс пользователя не найден."
    #     return await message.answer(text=text)
    # balance = Decimal(str(current_balance.balance))  # Текущий баланс
    # # Проверка, достаточно ли средств
    # if balance < price:
    #     text = (
    #         f"Баланс не может быть отрицательным\n"
    #         f"Balance: {balance.quantize(Decimal('0.01'))}\n"
    #         f"Price: {price.quantize(Decimal('0.01'))}"
    #     )
    #     return await message.answer(text=text)
    # # Обновление баланса
    # new_balance = balance - price
    # await MoneyBalanceDAO.update_by_id(
    #     item_id=current_balance.id,
    #     balance=new_balance.quantize(Decimal("0.01"), rounding=ROUND_DOWN),  # Округляем до копеек
    # )
    # # Работа с записями об облигациях
    sql_bond = await BondsDAO.get_one_or_none(isin=isin)
    if sql_bond:
        await BondsDAO.update_by_id(item_id=sql_bond.id, amount=sql_bond.amount + amount)
    else:
        result = await TransactionsDAO.create_bond(
            isin=isin, amount=amount, nominal=moex_bond.nominal, price=int(moex_bond.price * 100)
        )
        # await BondsDAO.create_with_return_id(isin=isin, amount=amount, nominal=moex_bond.nominal)
    if not result:
        text = "Баланс не может быть отрицательным"
        await message.answer(text=text)
        return
    text = "Сохранили"
    await message.answer(text=text)
