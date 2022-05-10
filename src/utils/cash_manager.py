# Libraries
from datetime import datetime, timedelta
import time

# Packages
import yfinance as yf


class CashManager:
    """A forex calculator to obtain pip value, lot size and profit.

    Attributes:
        risk (float): The percentage of the capital to risk (0.01 = 1%).
        from_currency (str): The symbol of the first currency of the
            pair. Defaults to None.
        to_currency (str): The symbol of the second currency of the
            pair. Defaults to None.
        interval (str): The time interval of each candle. See
            yfinance library intervals. Defaults to "5m".
        capital_currency (str): The symbol of the capital currency.
           Defaults to "EUR".
    """

    def __init__(
        self,
        risk: float,
        from_currency: str,
        to_currency: str,
        capital_currency: str = "EUR",
        interval: str = "5m",
    ) -> None:
        self.risk = risk
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.capital_currency = capital_currency
        self.interval = interval
        self.units = 1e2 if self.to_currency == "JPY" else 1e4

    def get_exchange_rate(
        self, from_currency: str, to_currency: str, timestamp: str
    ) -> float:
        """Returns the exchange rate between currencies at a given timestamp.

        Args:
            from_currency (string): Symbol of the currency.
            to_currency (string): Symbol of the converted currency.
            timestamp (string): Date in the "%Y-%m-%d %H:%M:%S" format.

        Returns:
            float: The exchange rate.
        """
        date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        pair = f"{from_currency}{to_currency}=X"  # TODO
        data = yf.download(
            pair,
            date,
            date + timedelta(hours=2),
            interval=self.interval,
            progress=False,
        )
        try:
            data = data.tz_localize("UTC")
        except Exception:
            pass
        try:
            return float(data.Close[timestamp])
        except Exception as e:
            print(e)
            try:
                return float(data.Close[-1])
            except Exception as e:
                print(f"{e}. Re-trying to fetch price data")
                # print(date, pair, data.head(5))
                time.sleep(1)
                return self.get_exchange_rate(
                    from_currency, to_currency, timestamp
                )

    def get_quantity(self, cash: float, pips: float, timestamp: str) -> int:
        """_summary_

        Parameters
        ----------
        cash : float
            The amount of cash to risk
        timestamp : string
            The proper datetime to calculate the exchange rate

        Returns
        -------
        int
            The quantity of the trade
        """
        return int(
            cash
            * self.risk
            * self.get_exchange_rate(
                self.to_currency, self.capital_currency, timestamp
            )
            / pips
            * self.units
        )

    def profit(self, open, close, quantity, type, timestamp) -> float:
        """Calculates the profit of an operation.

        Args:
            open (float): The opening price of the operation.
            close (float): The closing price of the operation.
            lot (float): The lot size.
            timestamp (str): The proper timestamp to calculate pip value.

        Returns:
            float: The profit in self.to_currency units.
        """
        difference = (close - open) if type == "BUY" else (open - close)
        return float(
            difference
            * quantity
            * self.get_exchange_rate(
                self.to_currency, self.capital_currency, timestamp
            )
        )
