from datetime import datetime
from typing import Annotated

from sqlalchemy import MetaData, text
from sqlalchemy.orm import Mapped, mapped_column, as_declarative

intpk = Annotated[int, mapped_column(primary_key=True)]
str_200 = Annotated[str, 200]
created_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


@as_declarative()
class BaseDB:
    metadata = MetaData()


class BondDB(BaseDB):
    __tablename__ = "bonds"

    id: Mapped[intpk]
    isin: Mapped[str_200]
    amount: Mapped[int]
    cur_coupon: Mapped[int] = mapped_column(server_default="0")
    cur_nominal: Mapped[int]


class MoneyBalanceDB(BaseDB):
    __tablename__ = "money_balances"

    id: Mapped[intpk]
    created_at: Mapped[created_at]
    description: Mapped[str_200]
    amount: Mapped[int] = mapped_column(server_default="0")
    currency: Mapped[str_200] = mapped_column(server_default="RUB")
