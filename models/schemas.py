from datetime import datetime

from pydantic import BaseModel


class DbBondDTO(BaseModel):
    id: int
    isin: str
    amount: int
    cur_nominal: int


class MoexBondDTO(DbBondDTO):
    title: str
    coupon_date: datetime
    coupon_price: float
    nominal: int
    price: float
    redemption_date: datetime


class MoneyBalanceDTO(BaseModel):
    id: int
    balance: float
    currency: str
