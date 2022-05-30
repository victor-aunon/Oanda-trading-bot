from datetime import datetime, timedelta
import time
import yfinance as yf


class FinancialFeed:
    def __init__(self, ticker, market, interval="5m") -> None:
        self.interval = interval
        self.set_ticker(ticker, market)
        self.get_start_end()
        self.retrieve_feed()

    def set_ticker(self, ticker, market):
        ticker = ticker.replace("_", "")
        ticker = ticker.replace("/", "")
        ticker = ticker.replace("-", "")
        if market == "fx":
            self.ticker = f"{ticker}=X"
        elif market == "crypto":
            self.ticker = f"{ticker[0:3]}-{ticker[3:]}"

    def get_start_end(self):
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

    def retrieve_feed(self):
        feed = yf.download(
            tickers=self.ticker,
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

    def get_feed(self):
        return self.feed

    def print_feed(self):
        print(self.feed)
