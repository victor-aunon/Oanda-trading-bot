# Libraries
from datetime import datetime
import os
from typing import Optional, Any

# Packages
import backtrader as bt
import xlsxwriter

# Local
from oandatradingbot.utils.instrument_units import PIP_UNITS
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.order_manager_backtest import OrderManagerBackTest


class BaseBackTestStrategy(bt.Strategy):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config = kwargs
        self.optimize = kwargs["optimize"]
        self.check_config()
        self.pairs = [p for p in kwargs["pairs"]] if self.optimize \
            else kwargs["pairs"]
        self.account_currency = kwargs["account_currency"]
        # Attributes that do not require dictionaries
        self.messages = Messages(
            self.config["language"], kwargs["account_currency"]
        )
        self.order_manager = OrderManagerBackTest(
            self.messages,
            self.pairs,
            self.p.profit_risk_ratio,
            self.broker
        )
        self.initialize_dicts()

    def check_config(self) -> None:
        # Check language
        if "language" not in self.config \
                or self.config["language"] not in ["EN-US", "ES-ES"]:
            print(
                "WARNING: Invalid language in config file. Switching to EN-US"
            )
            self.config["language"] = "EN-US"

    def initialize_dicts(self):
        pass

    @staticmethod
    def datetime_to_str(timestamp: datetime) -> str:
        return datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

    def log(self, text: str, dt: Optional[datetime] = None) -> None:
        # dt = dt or self.data[data_name].datetime.datetime(0)
        dtime = dt or self.datetime_to_str(datetime.now())
        print(f"{dtime} - {text}")

    def get_stop_loss(self, data_name: str):
        pass

    def get_take_profit(self, data_name: str):
        pass

    def enter_buy_signal(self, data_name: str):
        pass

    def near_buy_signal(self, data_name: str):
        pass

    def enter_sell_signal(self, data_name: str):
        pass

    def near_sell_signal(self, data_name: str):
        pass

    def notify_order(self, order: bt.Order) -> None:
        pair = order.data._name
        if self.order_manager.buyed[pair]:
            response = self.order_manager.manage_buy_order(
                order,
                self.datetime_to_str(self.data[pair].datetime.datetime(0)),
            )
            if response != "" and self.config["debug"]:
                self.log(response, self.data[pair].datetime.datetime(0))
        elif self.order_manager.selled[pair]:
            response = self.order_manager.manage_sell_order(
                order,
                self.datetime_to_str(self.data[pair].datetime.datetime(0)),
            )
            if response != "" and self.config["debug"]:
                self.log(response, self.data[pair].datetime.datetime(0))

    def notify_store(self, msg: Any, *args, **kwargs) -> None:
        if isinstance(msg, dict):
            if "errorCode" in msg:
                self.log(f"{msg.errorCode} - {msg.errorMsg}")  # type: ignore
        else:
            self.log(msg)

    def next(self) -> None:
        # Iterate over each currency pair since data is a list of feeds named
        # by each pair
        for pair in self.pairs:

            timestamp = self.data[pair].datetime.datetime(0)
            close = self.data[pair].close[0]

            # Check if today is Friday to close the order at the
            # end of the session
            valid = bt.Order.DAY if timestamp.weekday() == 4 else None

            # Check if a buy order could be opened
            if not self.order_manager.buyed[pair]:
                if self.enter_buy_signal(pair):
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = PIP_UNITS[pair.split("_")[1]]
                    stop_loss = self.get_stop_loss(pair)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(pair)

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=True,
                    )

                    # Calculate SL and TK
                    sl_price = close - stop_loss
                    tk_price = close + take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} - Close: {close:.4f} - "
                                f"ATR: {self.atr[pair].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f}"
                            ),
                            timestamp
                        )

                    # Create bracket order
                    self.buy_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
                        valid=valid,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager.buyed[pair] = True

            # Check if a sell order could be opened
            if not self.order_manager.selled[pair]:
                if self.enter_sell_signal(pair):
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = PIP_UNITS[pair.split("_")[1]]
                    stop_loss = self.get_stop_loss(pair)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(pair)

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=False,
                    )

                    # Calculate SL and TK
                    sl_price = close + stop_loss
                    tk_price = close - take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} - Close: {close:.4f} - "
                                f"ATR: {self.atr[pair].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f}"
                            ),
                            timestamp
                        )

                    # Create bracket order
                    self.sell_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
                        valid=valid,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager.selled[pair] = True

    def stop(self):
        # Skip the summary when optimizing
        if self.optimize:
            print(self.strat_name)
            return
        for pair in self.pairs:
            if len(self.order_manager.trades[pair]) == 0:
                continue

            # Create xlsxwriter workbook
            self.summary_file = os.path.join(
                self.config["results_path"],
                (
                    f"Backtest_{pair}_{self.strat_name}_"
                    f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')}"
                    ".xlsx"
                )
            )
            workbook = xlsxwriter.Workbook(self.summary_file)
            worksheet = workbook.add_worksheet("Trades")

            # Add a format for the successful operation
            successful = workbook.add_format({
                'border': 0,
                'bg_color': '#94eb9e',
                'align': 'center',
                'valign': 'vcenter',
            })

            # Add a format for the unsuccessful operation
            unsuccessful = workbook.add_format({
                'border': 0,
                'bg_color': '#fa7f7f',
                'align': 'center',
                'valign': 'vcenter',
            })

            # Create the trades table
            worksheet.add_table(
                0, 0,
                len(self.order_manager.trades[pair]),
                len(self.order_manager.trades[pair][0].keys()) - 1,
                {
                    "columns": [{"header": col} for col
                                in self.order_manager.trades[pair][0].keys()]
                }
            )
            for i, trade in enumerate(self.order_manager.trades[pair]):
                worksheet.write_row(
                    i + 1, 0, trade.values(),
                    cell_format=successful if trade["PL"] > 0
                    else unsuccessful
                )

            workbook.close()
