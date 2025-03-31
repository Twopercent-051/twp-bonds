from typing import List

from sqlalchemy import insert, update, delete, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from create_app import database_url
from models.schemas import DbBondDTO, MoneyBalanceDTO
from models.sql_models import BondDB, MoneyBalanceDB

engine = create_async_engine(url=database_url)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


class BaseDAO:
    model = None

    @classmethod
    async def create_with_return_id(cls, **data) -> int:
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(**data).returning(cls.model.id)
            result = await session.execute(stmt)
            created_id = result.scalar()
            await session.commit()
            return created_id

    @classmethod
    async def create_many(cls, data: List[dict]):
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def update_by_id(cls, item_id: int, **data):
        async with async_session_maker() as session:
            stmt = update(cls.model).values(**data).filter_by(id=item_id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def delete(cls, **data):
        async with async_session_maker() as session:
            stmt = delete(cls.model).filter_by(**data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def delete_many_by_ids(cls, ids: list[int]):
        async with async_session_maker() as session:
            stmt = delete(cls.model).where(cls.model.id.in_(ids))
            await session.execute(stmt)
            await session.commit()


class BondsDAO(BaseDAO):
    model = BondDB

    @classmethod
    async def get_one_or_none(cls, **filter_by) -> DbBondDTO | None:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by).limit(1)
            result = await session.execute(query)
            row = result.scalars().one_or_none()
            if row:
                return DbBondDTO.model_validate(obj=row, from_attributes=True)

    @classmethod
    async def get_many(cls, **filter_by) -> list[DbBondDTO]:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            data = await session.execute(query)
            return [DbBondDTO.model_validate(obj=row, from_attributes=True) for row in data.scalars().all()]


class MoneyBalanceDAO(BaseDAO):
    model = MoneyBalanceDB

    @classmethod
    async def get_one_or_none(cls, currency: str = "RUB") -> MoneyBalanceDTO | None:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(currency=currency).limit(1)
            result = await session.execute(query)
            row = result.scalars().one_or_none()
            if row:
                return MoneyBalanceDTO.model_validate(obj=row, from_attributes=True)
