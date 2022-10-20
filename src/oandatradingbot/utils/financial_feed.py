# Libraries
from datetime import datetime, timedelta
import time

# Packages
import yfinance as yf
from pandas import DataFrame

CRYPTOS = ["BTC", "BCH", "ETH", "LTC"]
INTERVALS = [
    "1m", "2m", "5m", "15m", "30m", "60m", "90m",
    "1h", "1d", "5d", "1wk", "1mo", "3mo"
]


class FinancialFeed:
    def __init__(self, instrument: str, interval="5m") -> None:
        if interval not in INTERVALS:
            raise SystemExit(
                f"Invalid interval. Valid intervals are {INTERVALS}"
            )
        self.interval = interval
        self.set_instrument(instrument)
        self.get_start_end()
        self.retrieve_feed()
        if self.feed.size == 0:
            raise SystemExit("Invalid instrument, not found in Yahoo Finance")

    def set_instrument(self, instrument: str) -> None:
        market = "fx" if instrument.split("_")[0] not in CRYPTOS else "crypto"
        instrument = instrument.replace("_", "")
        instrument = instrument.replace("/", "")
        instrument = instrument.replace("-", "")
        if market == "fx":
            self.instrument = f"{instrument}=X"
        elif market == "crypto":
            self.instrument = f"{instrument[0:3]}-{instrument[3:]}"

    def get_start_end(self) -> None:
        if self.interval == "1m":
            self.start = (datetime.now() - timedelta(days=6)).date()
            self.end = (datetime.now() + timedelta(days=1)).date()
        elif self.interval in ["5m", "2m", "15m", "30m", "90m"]:
            self.start = (datetime.now() - timedelta(days=59)).date()
            self.end = (datetime.now() + timedelta(days=1)).date()
        elif self.interval in ["60m", "1h"]:
            self.start = (datetime.now() - timedelta(days=729)).date()
            self.end = (datetime.now() + timedelta(days=1)).date()
        else:
            self.start = (datetime.now() - timedelta(days=30 * 365)).date()
            self.end = (datetime.now() + timedelta(days=1)).date()

    def retrieve_feed(self) -> None:
        feed: DataFrame = yf.download(
            tickers=self.instrument,
            start=self.start,
            end=self.end,
            interval=self.interval
        )
        # Remove time zone localization
        try:
            feed = feed.tz_localize('UTC')
        except Exception:
            print("Cannot determine feed timezone. Assuming UTC.")
            if feed.shape[0] == 0:
                time.sleep(1)
                self.retrieve_feed()
            pass
        self.feed = feed

    def get_feed(self) -> DataFrame:
        return self.feed

    def print_feed(self) -> None:
        print(self.feed)
