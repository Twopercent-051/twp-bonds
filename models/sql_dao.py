import asyncio
from typing import List

from sqlalchemy import insert, update, delete, select, func
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import config
from create_app import database_url, logger, bot
from models.schemas import DbBondDTO, MoneyBalanceDTO
from models.sql_models import BondDB, MoneyBalanceDB

engine = create_async_engine(url=database_url)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


def retry_on_disconnect(max_retries=7, delay=1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except (InterfaceError, OperationalError) as e:
                    retries += 1
                    error_message = str(e)
                    short_message = error_message.split(":")[-1].strip()
                    error_text = f"Connection error: {short_message}. Retry {retries}/{max_retries}..."
                    logger.warning(msg=error_text)
                    if retries < max_retries:
                        await asyncio.sleep(delay)
                    else:
                        await bot.send_message(chat_id=config.admin_ids[0], text=error_text)

        return wrapper

    return decorator


class BaseDAO:
    model = None

    @classmethod
    @retry_on_disconnect()
    async def create_many(cls, data: List[dict]):
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    @retry_on_disconnect()
    async def create_with_return_id(cls, **data) -> int:
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(**data).returning(cls.model.id)
            result = await session.execute(stmt)
            created_id = result.scalar()
            await session.commit()
            return created_id

    @classmethod
    @retry_on_disconnect()
    async def update_by_id(cls, item_id: int, **data):
        async with async_session_maker() as session:
            stmt = update(cls.model).values(**data).filter_by(id=item_id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    @retry_on_disconnect()
    async def delete(cls, **data):
        async with async_session_maker() as session:
            stmt = delete(cls.model).filter_by(**data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    @retry_on_disconnect()
    async def delete_many_by_ids(cls, ids: list[int]):
        async with async_session_maker() as session:
            stmt = delete(cls.model).where(cls.model.id.in_(ids))
            await session.execute(stmt)
            await session.commit()


class BondsDAO(BaseDAO):
    model = BondDB

    @classmethod
    @retry_on_disconnect()
    async def get_one_or_none(cls, **filter_by) -> DbBondDTO | None:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by).limit(1)
            result = await session.execute(query)
            row = result.scalars().one_or_none()
            if row:
                return DbBondDTO.model_validate(obj=row, from_attributes=True)

    @classmethod
    @retry_on_disconnect()
    async def get_many(cls, **filter_by) -> list[DbBondDTO]:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            data = await session.execute(query)
            return [DbBondDTO.model_validate(obj=row, from_attributes=True) for row in data.scalars().all()]


class MoneyBalanceDAO(BaseDAO):
    model = MoneyBalanceDB

    @classmethod
    @retry_on_disconnect()
    async def get_one_or_none(cls, currency: str = "RUB") -> MoneyBalanceDTO | None:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(currency=currency).limit(1)
            result = await session.execute(query)
            row = result.scalars().one_or_none()
            if row:
                return MoneyBalanceDTO.model_validate(obj=row, from_attributes=True)

    @classmethod
    @retry_on_disconnect()
    async def get_many(cls, **filter_by) -> list[MoneyBalanceDTO]:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            data = await session.execute(query)
            return [MoneyBalanceDTO.model_validate(obj=row, from_attributes=True) for row in data.scalars().all()]

    @classmethod
    @retry_on_disconnect()
    async def get_total(cls, **filter_by) -> int:
        async with async_session_maker() as session:
            query = select(func.sum(cls.model.amount)).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar() or 0


class TransactionsDAO:

    @staticmethod
    @retry_on_disconnect()
    async def create_bond(isin: str, amount: int, nominal: int, price: int, coupon: int) -> bool:
        async with async_session_maker() as session:
            balance_query = select(func.sum(MoneyBalanceDB.amount)).where(MoneyBalanceDB.currency == "RUB")
            result = await session.execute(balance_query)
            total_balance = result.scalar() or 0
            if total_balance < price:
                return False
            balance_stmt = insert(MoneyBalanceDB).values(amount=-price, description="buy bond")
            await session.execute(balance_stmt)
            bond_stmt = insert(BondDB).values(isin=isin, amount=amount, cur_nominal=nominal, cur_coupon=coupon)
            await session.execute(bond_stmt)
            await session.commit()
            return True

    @staticmethod
    @retry_on_disconnect()
    async def update_bond(isin: str, amount: int, price: int, nominal: int, coupon: int) -> bool:
        async with async_session_maker() as session:
            balance_query = select(func.sum(MoneyBalanceDB.amount)).where(MoneyBalanceDB.currency == "RUB")
            result = await session.execute(balance_query)
            total_balance = result.scalar() or 0
            if total_balance < price:
                return False
            balance_stmt = insert(MoneyBalanceDB).values(amount=-price, description="buy bond")
            await session.execute(balance_stmt)
            bond_stmt = (
                update(BondDB)
                .values(
                    amount=amount + BondDB.amount,
                    cur_nominal=nominal + BondDB.cur_nominal,
                    cur_coupon=BondDB.cur_coupon + coupon,
                )
                .filter_by(isin=isin)
            )
            await session.execute(bond_stmt)
            await session.commit()
            return True
