from typing import Annotated

from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column, as_declarative

intpk = Annotated[int, mapped_column(primary_key=True)]
str_200 = Annotated[str, 200]


@as_declarative()
class BaseDB:
    metadata = MetaData()


class BondDB(BaseDB):
    __tablename__ = "tickets"

    id: Mapped[intpk]
    isin: Mapped[str_200]
    amount: Mapped[int]
    cur_nominal: Mapped[int]


class MoneyBalanceDB(BaseDB):
    __tablename__ = "money_balances"

    id: Mapped[intpk]
    balance: Mapped[int] = mapped_column(server_default="0")
    currency: Mapped[str_200] = mapped_column(server_default="RUB")
