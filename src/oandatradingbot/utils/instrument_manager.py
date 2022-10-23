# Libraries
from typing import Dict, List

# Packages
import requests

# Locals
from oandatradingbot.types.config import ConfigType

practice_url = "https://api-fxpractice.oanda.com"
prod_url = "https://api-fxtrade.oanda.com"


class InstrumentManager:

    def __init__(self, config: ConfigType) -> None:
        self.account_type = config["practice"]
        self.token = config["oanda_token"]
        self.account_id = config["oanda_account_id"]
        self.url = practice_url if self.account_type else prod_url
        self._get_instrument_units(config["instruments"])

    def _get_instrument_units(self, instruments: List[str]) -> None:
        units: Dict[str, float] = {}

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
                units[instrument["name"]] = eval(
                    f"1e{int(instrument['pipLocation']) * -1}"
                )
        self.units = units

    def get_units(self, instrument: str) -> float:
        return self.units[instrument]

    def get_bid_price(self, instrument: str) -> float:
        response = requests.get(
            f"{self.url}/v3/accounts/{self.account_id}/pricing",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {self.token}"
            },
            params={"instruments": instrument}
        )

        return float(response.json()["prices"][0]["closeoutBid"])

    def get_ask_price(self, instrument: str) -> float:
        response = requests.get(
            f"{self.url}/v3/accounts/{self.account_id}/pricing",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {self.token}"
            },
            params={"instruments": instrument}
        )

        return float(response.json()["prices"][0]["closeoutAsk"])
