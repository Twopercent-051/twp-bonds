from pydantic import BaseModel


class DbBondDTO(BaseModel):
    id: int
    isin: str
    amount: int


class MoexBondDTO(DbBondDTO):
    title: str
    coupon_date: str
    coupon_price: float
    nominal: int
    price: float
    nkd: float
    redemption_date: str
