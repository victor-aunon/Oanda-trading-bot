# Libraries
from typing import Dict, Any, List

# Packages
import requests

practice_url = "https://api-fxpractice.oanda.com"
prod_url = "https://api-fxtrade.oanda.com"


class InstrumentManager:

    def __init__(self, config: Dict[str, Any]) -> None:
        self.account_type = config["practice"]
        self.token = config["oanda_token"]
        self.account_id = config["oanda_account_id"]
        self.url = practice_url if self.account_type else prod_url
        self._get_instrument_units(config["pairs"])

    def _get_instrument_units(self, instruments: List[str]) -> None:
        self.units: Dict[str, float] = {}

        response = requests.get(
            f"{self.url}/v3/accounts/{self.account_id}/instruments",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {self.token}"
            },
            params={"instruments": ",".join(instruments)}
        )

        for instrument in response.json()["instruments"]:
            if instrument["tags"][0]["name"] in ["CURRENCY", "CRYPTO"]:
                self.units[instrument["name"]] = eval(
                    f"1e{int(instrument['pipLocation']) * -1}"
                )

    def get_units(self, pair: str) -> float:
        return self.units[pair]

    def get_bid_price(self, pair: str) -> float:
        response = requests.get(
            f"{self.url}/v3/accounts/{self.account_id}/pricing",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {self.token}"
            },
            params={"instruments": pair}
        )

        return float(response.json()["prices"][0]["closeoutBid"])

    def get_ask_price(self, pair: str) -> float:
        response = requests.get(
            f"{self.url}/v3/accounts/{self.account_id}/pricing",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {self.token}"
            },
            params={"instruments": pair}
        )

        return float(response.json()["prices"][0]["closeoutAsk"])
