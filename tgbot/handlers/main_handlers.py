from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from models.sql_dao import BondsDAO, MoneyBalanceDAO, TransactionsDAO
from services.dohod import BuyRecommendation
from services.moex import MoexAPI
from services.scheduler_service import SchedulerService

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    text = "Введи ISIN и количество через пробел"
    await message.answer(text=text)


@router.message(Command("recommendations"))
async def get_recommendations_handler(message: Message):
    text = "Список рекомендаций:\n"
    sql_bonds = await BondsDAO.get_many()
    bonds = await MoexAPI.get_bonds_profiles(sql_bonds=sql_bonds)
    service = await BuyRecommendation.create(bonds=bonds)
    balances = await MoneyBalanceDAO.get_many()
    balance = sum(balance.amount for balance in balances)
    result = service.get(budget=balance)
    if len(result) == 0:
        await message.answer(text="Нет рекомендаций")
        return None
    for isin, amount in result.items():
        text += f"<code>{isin}</code> - {amount} шт.\n"
    await message.answer(text=text)
    return None


@router.message(Command("tasks"))
async def get_tasks_handler(message: Message):
    text = "Список задач:\n"
    tasks = SchedulerService.get_scheduled_tasks()
    if len(tasks) == 0:
        await message.answer(text="Нет задач")
        return None
    for task in tasks:
        text += f"<code>{task['isin']}</code> - {task['task']} - {task['time']}\n"
    await message.answer(text=text)
    return None


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
            price=moex_bond.price,
            nominal=moex_bond.nominal,
            coupon=moex_bond.coupon_price,
        )
    else:
        result = await TransactionsDAO.create_bond(
            isin=isin,
            amount=amount,
            nominal=moex_bond.nominal,
            price=moex_bond.price,
            coupon=moex_bond.coupon_price,
        )
        await SchedulerService.set_bond(
            isin=isin, coupon_date=moex_bond.coupon_date, redemption_date=moex_bond.redemption_date
        )
    if not result:
        text = "Баланс не может быть отрицательным"
        await message.answer(text=text)
        return None
    text = "Сохранили"
    await message.answer(text=text)
    return None
