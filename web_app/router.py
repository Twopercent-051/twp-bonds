from fastapi import APIRouter
from fastapi.requests import Request

from create_app import templates
from models.sql_dao import BondsDAO, MoneyBalanceDAO
from services.moex import MoexAPI

router = APIRouter()


@router.get("/")
async def get_bonds(request: Request):
    sql_bonds = await BondsDAO.get_many()
    bonds = await MoexAPI.get_bonds_profiles(sql_bonds=sql_bonds)
    total_amount = sum(bond.amount for bond in bonds)
    total_nominal = sum(bond.nominal for bond in bonds)
    total_price = round(number=sum(bond.price for bond in bonds), ndigits=2)
    balances = await MoneyBalanceDAO.get_many()
    total = sum(balance.amount for balance in balances)
    total_deposits = sum(balance.amount for balance in balances if balance.description == "deposit")
    difference = total + total_price - total_deposits
    return templates.TemplateResponse(
        "bonds_table.html",
        {
            "request": request,
            "bonds": bonds,
            "total_amount": total_amount,
            "total_price": total_price,
            "total_nominal": total_nominal,
            "current_balance": round(number=total / 100, ndigits=2),
            "difference": round(number=difference / 100, ndigits=2),
        },
    )
