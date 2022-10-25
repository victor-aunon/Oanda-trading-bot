# Libraries
from datetime import datetime
from typing import Dict, List, Optional, Union

# Packages
import backtrader as bt

# Local
from oandatradingbot.strategies.backtest_save_results import SaveResults
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.instrument_units import PIP_UNITS
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.order_manager_backtest import OrderManagerBackTest


class BaseBackTestStrategy(bt.Strategy):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config: ConfigType = kwargs \
            if kwargs["optimize"] else kwargs["config"]
        self.timeframes = self.config["timeframes"]
        self.optimize = self.config["optimize"]
        self.instruments: List[str] = [p for p in self.config["instruments"]] \
            if self.optimize else self.config["instruments"]
        self.account_currency: str = self.config["account_currency"]
        # Attributes that do not require dictionaries
        self.messages = Messages(
            self.config["language"], self.config["account_currency"]
        )
        self.order_manager = OrderManagerBackTest(
            self.messages,
            self.instruments,
            self.p.profit_risk_ratio,
            self.broker
        )
        self.save_results = SaveResults(self.config, self.p.profit_risk_ratio)
        self.initialize_dicts()

    @staticmethod
    def datetime_to_str(timestamp: datetime) -> str:
        return datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

    def log(self, text: str, dt: Optional[datetime] = None) -> None:
        # dt = dt or self.data[data_name].datetime.datetime(0)
        dtime = dt or self.datetime_to_str(datetime.now())
        print(f"{dtime} - {text}")

    def notify_order(self, order: bt.Order) -> None:
        instrument = order.data._name
        close = self.data[instrument].close[0]
        response = self.order_manager.manage_order(
            order,
            self.broker.get_cash() * self.config["risk"] / 100,
            self.datetime_to_str(self.data[instrument].datetime.datetime(0)),
            close
        )
        if response != "" and self.config["debug"]:
            self.log(response, self.data[instrument].datetime.datetime(0))

    def notify_store(
        self,
        msg: Union[Dict[str, str], str],
        *args,
        **kwargs
    ) -> None:
        if isinstance(msg, dict):
            if "errorCode" in msg:
                self.log(f"{msg.errorCode} - {msg.errorMsg}")  # type: ignore
        else:
            self.log(msg)

    def next(self) -> None:
        # Iterate over each currency instrument since data is
        # a list of feeds named by each instrument
        for instrument in self.instruments:

            timestamp: datetime = self.data[instrument].datetime.datetime(0)
            close: float = self.data[instrument].close[0]

            # Check if today is Friday to close the order at the
            # end of the session
            valid = bt.Order.DAY if timestamp.weekday() == 4 else None

            # Check if a buy order could be opened
            if not self.order_manager.has_buyed(instrument):
                if self.enter_buy_signal(instrument):
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = PIP_UNITS[instrument.split("_")[1]]
                    stop_loss = self.get_stop_loss(instrument)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(instrument)

                    # Calculate SL and TK
                    sl_price = close - stop_loss
                    tk_price = close + take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Instrument: {instrument} - "
                                f"Close: {close:.4f} - "
                                f"ATR: {self.atr[instrument].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f}"
                            ),
                            timestamp
                        )

                    # Create bracket order
                    self.buy_bracket(
                        data=self.data[instrument],
                        size=None,
                        exectype=bt.Order.Market,
                        valid=valid,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager.is_buy_or_sell[instrument] = "BUY"

            # Check if a sell order could be opened
            if not self.order_manager.has_selled(instrument):
                if self.enter_sell_signal(instrument):
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = PIP_UNITS[instrument.split("_")[1]]
                    stop_loss = self.get_stop_loss(instrument)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(instrument)

                    # Calculate SL and TK
                    sl_price = close + stop_loss
                    tk_price = close - take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Instrument: {instrument} - "
                                f"Close: {close:.4f} - "
                                f"ATR: {self.atr[instrument].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f}"
                            ),
                            timestamp
                        )

                    # Create bracket order
                    self.sell_bracket(
                        data=self.data[instrument],
                        size=None,
                        exectype=bt.Order.Market,
                        valid=valid,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager.is_buy_or_sell[instrument] = "SELL"

    def stop(self) -> None:
        # Skip the trades summary when optimizing
        if self.optimize:
            self.save_results.save_optimization_results(
                self.config["opt_name"],
                self.strat_name,
                self.instruments,
                self.order_manager.trades
            )
            return

        # Not optimizing -> just backtest:
        # instruments only contains one instrument
        self.summary_file = self.save_results.save_backtest_results(
            self.strat_name, self.instruments[0], self.order_manager.trades
        )
