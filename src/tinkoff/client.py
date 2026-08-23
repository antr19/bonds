import asyncio
import os
import httpx
import json
from typing import List

TINKOFF_TOKEN=os.getenv("TINKOFF_TOKEN")


def money_to_float(money_dict: dict) -> float:
    """Конвертирует MoneyValue из REST API в float."""
    if not money_dict:
        return 0.0
    units = float(money_dict.get("units", 0))
    nano = money_dict.get("nano", 0)
    return units + nano / 1e9


class TBankPortfolioREST:
    """REST-клиент для получения портфеля из Т-Инвестиций."""

    def __init__(self, token: str = TINKOFF_TOKEN):
        self.token = token or os.environ.get("TBANK_TOKEN") or os.environ.get("TINKOFF_TOKEN")
        if not self.token:
            raise ValueError("Не передан токен")
        self.base_url = "https://invest-public-api.tinkoff.ru/rest"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_accounts(self) -> List[dict]:
        async with httpx.AsyncClient(verify=False) as client:  # verify=False отключает SSL-проверку
            resp = await client.post(
                f"{self.base_url}/tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts",
                headers=self.headers,
                json={},
            )
            resp.raise_for_status()
            return resp.json().get("accounts", [])

    async def get_portfolio(self, account_id: str) -> dict:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.post(
                f"{self.base_url}/tinkoff.public.invest.api.contract.v1.OperationsService/GetPortfolio",
                headers=self.headers,
                json={"accountId": account_id, "currency": "rub"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_portfolio_for_ai(self, allowed_types: List[str] = None) -> dict:
        """
        Возвращает портфель в виде JSON-строки, оптимизированной для ИИ.

        :param allowed_types: Список допустимых типов инструментов.
                              Примеры: ["share"] (только акции), ["bond", "etf"] (облигации и фонды).
                              Если None, возвращаются все инструменты.
        """
        accounts = await self.get_accounts()
        if not accounts:
            return json.dumps({"error": "Счета не найдены"}, ensure_ascii=False, indent=2)

        account_id = accounts[0]["id"]
        portfolio_data = await self.get_portfolio(account_id)
        raw_positions = portfolio_data.get("positions", [])

        positions_for_ai = []
        total_portfolio_value = 0.0
        total_expected_yield = 0.0

        for p in raw_positions:
            # Получаем тип инструмента (share, bond, etf, currency и т.д.)
            inst_type = p.get("instrumentType", "unknown")

            # ФИЛЬТРАЦИЯ: если список разрешённых типов задан и текущего типа в нём нет — пропускаем
            if allowed_types and inst_type not in allowed_types:
                continue

            quantity = money_to_float(p.get("quantity", {}))
            avg_price = money_to_float(p.get("averagePositionPrice", {}))
            cur_price = money_to_float(p.get("currentPrice", {}))
            expected_yield = money_to_float(p.get("expectedYield", {}))

            # Предвычисляем метрики
            current_value = round(quantity * cur_price, 2)
            profit_loss = round(expected_yield, 2)

            total_portfolio_value += current_value
            total_expected_yield += profit_loss

            positions_for_ai.append({
                "ticker": p.get("ticker", "UNKNOWN"),
                "instrument_type": inst_type,
                "quantity": round(quantity, 4),
                "average_price_rub": round(avg_price, 2),
                "current_price_rub": round(cur_price, 2),
                "current_value_rub": current_value,
                "profit_loss_rub": profit_loss
            })

        ai_ready_data = {
            "portfolio_summary": {
                "currency": "RUB",
                "filtered_by_types": allowed_types if allowed_types else "all",
                "total_positions_count": len(positions_for_ai),
                "total_current_value_rub": round(total_portfolio_value, 2),
                "total_profit_loss_rub": round(total_expected_yield, 2),
                "is_profitable": total_expected_yield > 0
            },
            "positions": positions_for_ai
        }

        return ai_ready_data


async def main():
    client = TBankPortfolioREST()
    print(await client.get_portfolio_for_ai(allowed_types=["bond"]))


if __name__ == "__main__":
    # Подавляем предупреждения httpx о verify=False
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    asyncio.run(main())