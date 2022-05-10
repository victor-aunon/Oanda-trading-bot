# Libraries
import argparse
from datetime import datetime
import json
import math
import os

# Packages
import backtrader as bt
import btoandav20 as bto
from btoandav20.sizers.oandav20sizer import OandaV20RiskPercentSizer
from backtrader.indicators.atr import AverageTrueRange as ATR
from backtrader.indicators.ema import ExponentialMovingAverage as EMA
from backtrader.indicators.macd import MACD
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from dbmodels.trade import Base
from utils.cash_manager import CashManager
from utils.messages import Messages
from utils.order_manager import OrderManager
from utils.spread_scrapper import SpreadScrapper
from utils.tts import TTS

# PAIRS = [
#     "EURNZD",
#     "EURUSD",
#     "GBPAUD",
#     "EURCAD",
#     "EURAUD",
#     "USDAUD",
#     "EURGBP",
#     "GBPCAD",
#     "USDJPY",
#     "EURCHF",
# ]


class MACDEMAATRStrategy(bt.Strategy):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config = kwargs
        self.pairs = kwargs["pairs"]
        self.risk = kwargs["risk"]
        self.p = kwargs["strategy_params"]
        self.account_type = kwargs["account_type"]
        self.account_currency = kwargs["account_currency"]
        self.testing = kwargs["testing"]
        # Attributes that do not require dictionaries
        self.atr_dist = self.p["atr_distance"]
        self.p_r_ratio = self.p["profit_risk_ratio"]
        self.interval = self.p["interval"]
        self.messages = Messages(
            kwargs["language"], kwargs["account_currency"]
        )
        if kwargs["tts"]:
            self.tts = TTS(kwargs["language"], 120)
        engine = create_engine(kwargs["db_connection"])
        Base.metadata.create_all(engine)
        self.db_session = Session(bind=engine)
        self.initialize_dicts()

    def initialize_dicts(self):
        # Dictionaries whose keys are the fx pairs
        self.data = {}
        self.macd = {}
        self.ema = {}
        self.atr = {}
        self.cash_manager = {}
        self.order_manager = {}
        self.data_ready = {}
        self.units = {}
        # Fill the previous dictionaries
        for pair in self.pairs:
            # Indicators
            data = [d for d in self.datas if d._name == pair][0]
            self.data[pair] = data
            self.macd[pair] = MACD(
                data.close,
                period_me1=self.p["macd_fast_ema"],
                period_me2=self.p["macd_slow_ema"],
                period_signal=self.p["macd_signal_ema"],
            )
            self.ema[pair] = EMA(data.close, period=self.p["ema_period"])
            self.atr[pair] = ATR(data, period=self.p["atr_period"])
            # Other dictionaries
            self.cash_manager[pair] = CashManager(
                self.risk,
                pair[0:3],
                pair[3:],
                self.account_currency,
                self.interval,
            )  # TODO cashmanager autodetects forex or crypto
            self.order_manager[pair] = OrderManager(
                self.messages,
                self.db_session,
                self.account_type,
                self.tts if self.tts else None
            )
            self.data_ready[pair] = False
            self.units[pair] = (
                1e2 if pair[3:] == "JPY" else 1e4
            )  # TODO set in the cash manager and allow cryptocoins

    @staticmethod
    def datetime_to_str(timestamp):
        return datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

    def log(self, text, dt=None):
        # dt = dt or self.data[data_name].datetime.datetime(0)
        dt = dt or self.datetime_to_str(datetime.now())
        print(f"{dt} - {text}")

    def enter_buy_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous positive MACD signal values
        prev_positives = [True if x > 0 else False for x in macd.get(size=5)]

        # Look for previous prices above the EMA
        prices_above = [
            True if x > y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            macd[0] > signal[0]
            and signal[0] < 0
            and macd[-5] < signal[-5]
            and True not in prev_positives
            and False not in prices_above
            and ema[-1] > ema[-10]
        )

    def near_buy_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous positive MACD signal values
        prev_positives = [True if x > 0 else False for x in macd.get(size=5)]

        # Look for previous prices above the EMA
        prices_above = [
            True if x > y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            signal[0] < 0
            and macd[-5] < signal[-5]
            and True not in prev_positives
            and False not in prices_above
            and ema[-1] > ema[-10]
        )

    def enter_sell_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous negatives MACD signal values
        prev_negatives = [True if x < 0 else False for x in macd.get(size=5)]

        prices_below = [
            True if x < y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            macd[0] < signal[0]
            and signal[0] > 0
            and macd[-5] > signal[-5]
            and True not in prev_negatives
            and False not in prices_below
            and ema[-1] < ema[-10]
        )

    def near_sell_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous negatives MACD signal values
        prev_negatives = [True if x < 0 else False for x in macd.get(size=5)]

        prices_below = [
            True if x < y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            signal[0] > 0
            and macd[-5] > signal[-5]
            and True not in prev_negatives
            and False not in prices_below
            and ema[-1] < ema[-10]
        )

    def notify_data(self, data, status):
        self.log(f"Data status: {data._name} -> {data._getstatusname(status)}")
        for pair in self.pairs:
            if data._name == pair and status == data.LIVE:
                self.data_ready[pair] = True
            elif data._name == pair and status != data.LIVE:
                self.data_ready[pair] = False

    def notify_order(self, order):
        pair = order.data._name
        if self.order_manager[pair].has_buyed:
            self.log(
                self.order_manager[pair].manage_buy_order(
                    order,
                    self.cash_manager[pair],
                    self.datetime_to_str(self.data[pair].datetime.datetime(0)),
                )
            )
        elif self.order_manager[pair].has_selled:
            self.log(
                self.order_manager[pair].manage_sell_order(
                    order,
                    self.cash_manager[pair],
                    self.datetime_to_str(self.data[pair].datetime.datetime(0)),
                )
            )
        if self.config["debug"]:
            print(
                order.data._name,
                order.ref,
                order.created.size,
                order.created.price,
                order.price,
                order.size,
                order.ordtypename(),
                order.getordername(),
                order.getstatusname(),
                order.executed.value,
                order.executed.price,
                order.executed.dt
            )

    def notify_trade(self, trade):
        pass

    def notify_store(self, msg, *args, **kwargs):
        if isinstance(msg, dict):
            if "errorCode" in msg:
                self.log(f"{msg.errorCode} - {msg.errorMsg}")  # type: ignore
        elif "id" in msg:
            pass
        else:
            self.log(msg)

    def next(self):
        # Iterate over each forex pair since data is a list of feeds named
        # by each pair
        for pair in self.pairs:
            # Only do operations if the data is ready (LIVE)
            if not self.data_ready[pair]:
                return

            # Log the closing price
            timestamp = self.data[pair].datetime.datetime(0)
            close = self.data[pair].close[0]
            text = f"{pair} - {close}"
            if self.config["debug"]:
                self.log(text)

            # Stop the execution when running a test
            if self.testing:
                raise bt.StrategySkipError

            # Check if a buy order could be opened
            if not self.order_manager[pair].has_buyed:
                if self.near_buy_signal(pair):
                    self.log(self.messages.near_buy_signal(pair))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_buy_signal(
                                f"{pair[0:3]} {pair[3:]}"
                            )
                        )
                if self.enter_buy_signal(pair):
                    # Check if today is Friday to close the order at the
                    # end of the session
                    # date = datetime.strptime(
                    #     self.datetime_to_str(timestamp), "%Y-%m-%d %H:%M:%S"
                    # )
                    # valid = 0 if date.weekday() == 4 else None

                    # Get the current spread
                    spread_pips = SpreadScrapper.get_spread(pair)
                    spread = spread_pips / self.units[pair]

                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    stop_loss = self.atr[pair].atr[0] * self.atr_dist
                    s_l_pips = stop_loss * self.units[pair]
                    take_profit = stop_loss * self.p_r_ratio

                    # Calculate lot size
                    quantity = self.cash_manager[pair].get_quantity(
                        self.broker.getcash(),
                        s_l_pips,
                        self.datetime_to_str(timestamp)
                    )
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=True,
                        pips=s_l_pips / self.broker.o.get_leverage()
                    )

                    # Conform to the minimum price variation
                    # Multiplied and divided by 10 to round the pip/10
                    sl_price = math.floor(
                        (close + spread - stop_loss) * self.units[pair] * 10
                    ) / (self.units[pair] * 10)
                    tk_price = math.ceil(
                        (close + spread + take_profit) * self.units[pair] * 10
                    ) / (self.units[pair] * 10)

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} Close: {close} "
                                f"Close (w/spread): {(close + spread):.5f} "
                                f"Spread: {spread:.2f} "
                                f"ATR: {self.atr[pair].atr[0]:.4f} "
                                f"SL (pips): {s_l_pips:.2f} TK (pips): "
                                f"{(take_profit * self.units[pair]):.2f} "
                                f"SL price: {sl_price:.5f} "
                                f"TK price: {tk_price:.5f} "
                                f"Quantity: {quantity} Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.buy_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
                        valid=0,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager[pair].has_buyed = True

            # Check if a sell order could be opened
            if not self.order_manager[pair].has_selled:
                if self.near_sell_signal(pair):
                    self.log(self.messages.near_sell_signal(pair))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_sell_signal(
                                f"{pair[0:3]} {pair[3:]}"
                            )
                        )
                if self.enter_sell_signal(pair):
                    # Check if today is Friday to close the order at the
                    # end of the session
                    # date = datetime.strptime(
                    #     self.datetime_to_str(timestamp), "%Y-%m-%d %H:%M:%S"
                    # )
                    # valid = 0 if date.weekday() == 4 else None

                    # Get the current spread
                    spread_pips = SpreadScrapper.get_spread(pair)
                    spread = spread_pips / self.units[pair]

                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    stop_loss = self.atr[pair].atr[0] * self.atr_dist
                    s_l_pips = stop_loss * self.units[pair]
                    take_profit = stop_loss * self.p_r_ratio

                    # Calculate lot size
                    quantity = self.cash_manager[pair].get_quantity(
                        self.broker.getcash(),
                        s_l_pips,
                        self.datetime_to_str(timestamp)
                    )
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=False,
                        pips=s_l_pips / self.broker.o.get_leverage()
                    )

                    # Conform to the minimum price variation
                    # Multiplied and divided by 10 to round the pip/10
                    sl_price = math.ceil(
                        (close - spread + stop_loss) * self.units[pair] * 10
                    ) / (self.units[pair] * 10)
                    tk_price = math.floor(
                        (close - spread - take_profit) * self.units[pair] * 10
                    ) / (self.units[pair] * 10)

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} Close: {close} "
                                f"Close (w/spread): {(close + spread):.5f} "
                                f"Spread: {spread:.2f} "
                                f"ATR: {self.atr[pair].atr[0]:.4f} "
                                f"SL (pips): {s_l_pips:.2f} TK (pips): "
                                f"{(take_profit * self.units[pair]):.2f} "
                                f"SL price: {sl_price:.5f} "
                                f"TK price: {tk_price:.5f} "
                                f"Quantity: {quantity} Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.sell_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
                        valid=0,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
                    self.order_manager[pair].has_selled = True


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Oanda trading bot'
        )
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))

    parser.add_argument(
        '--config-file',
        default=os.path.join(current_dir, "config.json"),
        required=False, help="Configuration json file required to run the bot")

    parser.add_argument(
        '--db-connection',
        default=f"sqlite:///{os.path.join(current_dir, 'trades.db')}",
        required=False, help="Database URI where trades are stored")

    parser.add_argument(
        '--debug',
        action="store_true", default=False,
        required=False, help="Show runtime information")

    parser.add_argument(
        '--basetemp',
        required=False, help=argparse.SUPPRESS)

    return parser.parse_args(pargs)


def main(config_file=None, db_connection=None, testing=False):
    print("====== Starting backtrader ======")
    args = parse_args()

    config = config_file if config_file is not None else args.config_file

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Load config json file
    with open(os.path.join(current_dir, config), "r") as file:
        config = json.load(file)

    config["db_connection"] = db_connection if db_connection is not None \
        else args.db_connection

    config["account_type"] = "Demo" if config["practice"] else "Brokerage"
    config["testing"] = testing
    config["debug"] = args.debug
    # Check there are no repeated pairs
    config["pairs"] = list(set(config["pairs"]))

    # Instantiate cerebro
    cerebro = bt.Cerebro()

    store = bto.stores.OandaV20Store(
        token=config["oanda_token"],
        account=config["oanda_account_id"],
        practice=config["practice"],
        stream_timeout=20,
        notif_transactions=True
    )

    for pair in config["pairs"]:
        data = store.getdata(
            dataname=f"{pair[0:3]}_{pair[3:]}",
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"]
            # qcheck=20,  # Increase qcheck (0.5 def) to ensure candles every
            # next
        )
        cerebro.resampledata(
            data,
            name=pair,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"],
        )
    cerebro.broker = store.getbroker()  # Assign Oanda broker

    cerebro.addstrategy(MACDEMAATRStrategy, **config)

    # Sizes are going to be a percentage of the cash
    cerebro.addsizer(
        OandaV20RiskPercentSizer, percents=config["risk"]
    )
    cerebro.run()


if __name__ == "__main__":
    main()
