from datetime import datetime

from pydantic import BaseModel


class DbBondDTO(BaseModel):
    id: int
    isin: str
    amount: int
    cur_coupon: int
    cur_nominal: int


class MoexBondDTO(DbBondDTO):
    title: str
    coupon_date: datetime
    coupon_price: int
    nominal: int
    price: int
    redemption_date: datetime


class MoneyBalanceDTO(BaseModel):
    id: int
    amount: int
    currency: str
    created_at: datetime
    description: str
