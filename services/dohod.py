import httpx
import json

from pydantic import BaseModel

from models.schemas import MoexBondDTO
from models.sql_dao import BondsDAO
from services.moex import MoexAPI


class DohodItem(BaseModel):
    isin: str
    price: int
    price_return: int
    amount: int = 0


class BuyRecommendation:
    def __init__(self, dohod_bonds: list[DohodItem]):
        self.dohod_bonds = dohod_bonds

    @staticmethod
    async def parse_dohod() -> list[DohodItem]:
        payload = {"customFilters[strategy][]": ["strategy1", "strategy1"]}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url="https://www.dohod.ru/assets/components/dohodbonds/connectorweb.php?action=info", data=payload
            )
        data = json.loads(response.text)
        sorted_data = sorted(data, key=lambda x: float(x["price_return"]), reverse=True)
        top_5 = sorted_data[:5]
        result = []
        for item in top_5:
            result.append(
                DohodItem(
                    isin=item["xml_isin"],
                    price=int(item["nominal"]) * float(item["price"])
                    + float(item["nkd"]) * 100,  # предполагается, что price есть в item (или скорректируйте)
                    price_return=int(float(item["price_return"]) * 100),
                )
            )
        return result

    @classmethod
    async def create(cls, bonds: list[MoexBondDTO]) -> "BuyRecommendation":
        result = await cls.parse_dohod()
        cur_bonds_amount = {bond.isin: bond.amount for bond in bonds}
        for bond in result:
            amount = cur_bonds_amount.get(bond.isin, 0)
            bond.amount = amount
        return cls(dohod_bonds=result)

    def get(self, budget: int) -> dict[str, int]:
        """
        Генерирует рекомендации по покупке облигаций из топ-5 по доходности,
        чтобы распределение бумаг в портфеле стремилось к равномерному.
        """
        # Предварительно сортируем по доходности для приоритета при равенстве количества
        self.dohod_bonds.sort(key=lambda x: -x.price_return)
        result = {}
        while True:
            print(f"Budget: {budget}")
            # Сортировка: сначала по amount, затем по убыванию доходности
            sorted_bonds = sorted(self.dohod_bonds, key=lambda x: (x.amount * x.price, -x.price_return))
            # Находим бумагу с наименьшим количеством в портфеле, чтобы не "перекачивать" бюджет в одну бумагу
            candidate = sorted_bonds[0]
            if budget < candidate.price:
                break
            candidate.amount += 1
            budget -= candidate.price
            result[candidate.isin] = result.get(candidate.isin, 0) + 1
            print(f"Result: {result}")
        return result


async def test():
    sql_bonds = await BondsDAO.get_many()
    bonds = await MoexAPI.get_bonds_profiles(sql_bonds=sql_bonds)
    service = await BuyRecommendation.create(bonds=bonds)
    result = service.get(budget=672829)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
