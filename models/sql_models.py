from datetime import datetime
from typing import Annotated

from sqlalchemy import MetaData, text
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
