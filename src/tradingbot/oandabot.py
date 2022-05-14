# Libraries
import argparse
import ast
from datetime import datetime
import json
import os
from pprint import pprint

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
from utils.instrument_manager import InstrumentManager
from utils.messages import Messages
from utils.order_manager import OrderManager
from utils.tts import TTS


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
        self.instrument_manager = InstrumentManager(self.config)
        self.order_manager = OrderManager(
            self.messages,
            self.db_session,
            self.instrument_manager,
            self.account_type,
            self.pairs,
            self.tts if self.config["tts"] else None
        )
        self.initialize_dicts()

    def initialize_dicts(self):
        # Dictionaries whose keys are the fx pairs
        self.data = {}
        self.macd = {}
        self.ema = {}
        self.atr = {}
        self.data_ready = {}
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
            self.data_ready[pair] = False

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
        pass

    def notify_trade(self, trade):
        pass

    def notify_store(self, msg, *args, **kwargs):
        if isinstance(msg, dict):
            if "errorCode" in msg:
                self.log(f"{msg.errorCode} - {msg.errorMsg}")  # type: ignore
        elif "batchID" in msg:
            res_dict = ast.literal_eval(msg)
            if self.config["debug"]:
                pprint(res_dict)
            response = self.order_manager.manage_transaction(res_dict)
            if response != "":
                self.log(response)
        else:
            self.log(msg)

    def next(self):
        # Iterate over each currency pair since data is a list of feeds named
        # by each pair
        for pair in self.pairs:
            # Only do operations if the data is ready (LIVE)
            if not self.data_ready[pair]:
                return

            # Log the closing price
            # timestamp = self.data[pair].datetime.datetime(0)
            close = self.data[pair].close[0]
            text = f"{pair} - {close}"
            if self.config["debug"]:
                self.log(text)

            # Stop the execution when running a test
            if self.testing:
                raise bt.StrategySkipError

            # Check if a buy order could be opened
            if not self.order_manager.has_buyed(pair):
                if self.near_buy_signal(pair):
                    self.log(self.messages.near_buy_signal(pair))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_buy_signal(
                                f"{' '.join(pair.split('_'))}"
                            )
                        )
                if self.enter_buy_signal(pair):
                    # Check if today is Friday to close the order at the
                    # end of the session
                    # date = datetime.strptime(
                    #     self.datetime_to_str(timestamp), "%Y-%m-%d %H:%M:%S"
                    # )
                    # valid = 0 if date.weekday() == 4 else None

                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(pair)
                    stop_loss = self.atr[pair].atr[0] * self.atr_dist
                    s_l_pips = stop_loss * units
                    take_profit = stop_loss * self.p_r_ratio

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=True,
                        pips=s_l_pips / self.broker.o.get_leverage()
                    )

                    # Get the current ask price and calculate SL and TK
                    ask_price = self.instrument_manager.get_ask_price(pair)
                    sl_price = ask_price - stop_loss
                    tk_price = ask_price + take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} Close: {close} "
                                f"Ask: {(ask_price):.5f} "
                                f"ATR: {self.atr[pair].atr[0]:.4f} "
                                f"SL (pips): {s_l_pips:.2f} TK (pips): "
                                f"{(take_profit * units):.2f} "
                                f"SL price: {sl_price:.5f} "
                                f"TK price: {tk_price:.5f} "
                                f"Size: {size}"
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

            # Check if a sell order could be opened
            if not self.order_manager.has_selled(pair):
                if self.near_sell_signal(pair):
                    self.log(self.messages.near_sell_signal(pair))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_sell_signal(
                                f"{' '.join(pair.split('_'))}"
                            )
                        )
                if self.enter_sell_signal(pair):
                    # Check if today is Friday to close the order at the
                    # end of the session
                    # date = datetime.strptime(
                    #     self.datetime_to_str(timestamp), "%Y-%m-%d %H:%M:%S"
                    # )
                    # valid = 0 if date.weekday() == 4 else None

                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(pair)
                    stop_loss = self.atr[pair].atr[0] * self.atr_dist
                    s_l_pips = stop_loss * units
                    take_profit = stop_loss * self.p_r_ratio

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=False,
                        pips=s_l_pips / self.broker.o.get_leverage()
                    )

                    # Get the current bid price and calculate SL and TK
                    bid_price = self.instrument_manager.get_bid_price(pair)
                    sl_price = bid_price + stop_loss
                    tk_price = bid_price - take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} Close: {close} "
                                f"Bid: {bid_price:.5f} "
                                f"ATR: {self.atr[pair].atr[0]:.4f} "
                                f"SL (pips): {s_l_pips:.2f} TK (pips): "
                                f"{(take_profit * units):.2f} "
                                f"SL price: {sl_price:.5f} "
                                f"TK price: {tk_price:.5f} "
                                f"Size: {size}"
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


def main(config_obj=None, db_connection=None, testing=False):
    print("====== Starting backtrader ======")
    args = parse_args()

    config = config_obj if config_obj is not None else args.config_file

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Load config json file
    if config_obj is None:
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
            dataname=pair,
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
