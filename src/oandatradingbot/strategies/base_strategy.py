# Libraries
import ast
from datetime import datetime, time
from pprint import pprint
from typing import Dict, List, Optional, Union

# Packages
import backtrader as bt

# Local
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.instrument_manager import InstrumentManager
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.order_manager import OrderManager
from oandatradingbot.utils.telegram_bot import TelegramBot
from oandatradingbot.utils.tts import TTS

LANGUAGES = ["ES-ES", "EN-US"]


class BaseStrategy(bt.Strategy):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config: ConfigType = kwargs["config"]
        self._check_config()
        self.instruments: List[str] = self.config["instruments"]
        self.account_type: str = self.config["account_type"]
        self.account_currency: str = self.config["account_currency"]
        self.testing: bool = self.config["testing"]
        self.messages = Messages(
            self.config["language"], self.config["account_currency"]
        )
        if self.config["tts"]:
            self.tts = TTS(
                self.config["language_tts"] if "language_tts" in self.config
                else "EN-US",
                120
            )
        self.instrument_manager = InstrumentManager(self.config)
        # Create TelegramBot instance if the bot is reachable
        if "telegram_token" in self.config:
            self._check_telegram_bot()
            # Add a timer to send notifications at a certain hour
            if hasattr(self, "telegram_bot"):
                self.add_timer(
                    when=self.config["testing_date"].time() if self.testing
                    else time(self.config["telegram_report_hour"] or 20, 0),
                    weekdays=[] if self.testing else [1, 2, 3, 4, 5],
                    timername="telegram_timer",
                )
        # Add a timer to close pending orders on Fridays at session close
        self.add_timer(
            when=self.config["testing_date"].time() if self.testing
            else time(20, 30),
            weekdays=[] if self.testing else [5],
            timername="session_close"
        )
        self.order_manager = OrderManager(
            self.config,
            self.telegram_bot if hasattr(self, "telegram_bot") else None,
        )
        self.initialize_dicts()

    @staticmethod
    def datetime_to_str(timestamp: datetime) -> str:
        return datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

    def _check_config(self) -> None:
        # Check oanda tokens and account id
        if self.broker.o.get_currency() is None:
            print(
                "ERROR: Invalid config file. Make sure you have passed",
                "a valid config JSON file and a valid OANDA access token",
                "and account id.",
            )
            raise bt.StrategySkipError
        # Check language
        if "language" not in self.config \
                or self.config["language"] not in LANGUAGES:
            print(
                "WARNING: Invalid language in config file. Switching to EN-US"
            )
            self.config["language"] = "EN-US"

    def _check_telegram_bot(self) -> None:
        telegram_bot = TelegramBot(self.config)
        if telegram_bot.check_bot().status_code != 200:
            print(
                "WARNING: Invalid Telegram bot token access. Check the config",
                "JSON file.",
            )
            return
        self.telegram_bot = telegram_bot

    def initialize_dicts(self) -> None:
        """Implemented in child class"""
        pass

    def log(self, text: str, dt: Optional[datetime] = None):
        # dt = dt or self.data[data_name].datetime.datetime(0)
        dtime = dt or self.datetime_to_str(datetime.now())
        print(f"{dtime} - {text}")

    def notify_data(self, data: bt.DataBase, status: str) -> None:
        self.log(f"Data status: {data._name} -> {data._getstatusname(status)}")
        for instrument in self.instruments:
            if data._name == instrument and status == data.LIVE:
                self.data_ready[instrument] = True
            elif data._name == instrument and status != data.LIVE:
                self.data_ready[instrument] = False

    def notify_store(
        self,
        msg: Union[Dict[str, str], str],
        *args,
        **kwargs
    ) -> None:
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

    def notify_timer(self, timer, when, timername, *args, **kwargs):
        if timername == "telegram_timer":
            self.telegram_bot.manage_notifications(
                self.config["testing_date"] if self.testing
                else datetime.utcnow()
            )
        if timername == "session_close":
            self.order_manager.cancel_pending_trades()

    def next(self) -> None:
        # Iterate over each currency instrument since data
        # is a list of feeds named by each instrument
        for instrument in self.instruments:
            # Only do operations if the data is ready (LIVE)
            if not self.data_ready[instrument]:
                return

            # Log the closing price
            # timestamp = self.data[instrument].datetime.datetime(0)
            close: float = self.data[instrument].close[0]
            text = f"{instrument} - {close}"
            if self.config["debug"]:
                self.log(text)

            # Check if a buy order could be opened
            if not self.order_manager.has_buyed(instrument):
                if self.near_buy_signal(instrument):
                    self.log(self.messages.near_buy_signal(instrument))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_buy_signal(
                                f"{' '.join(instrument.split('_'))}"
                            )
                        )
                if self.enter_buy_signal(instrument) and not self.testing:
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(instrument)
                    stop_loss = self.get_stop_loss(instrument)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(instrument)

                    # Calculate lot size
                    size: float = self.getsizer().getsizing(
                        self.data[instrument],
                        isbuy=True,
                        pips=s_l_pips / self.broker.o.get_leverage(),
                    )

                    # Get the current ask price and calculate SL and TK
                    ask_price = self.instrument_manager.get_ask_price(
                        instrument
                    )
                    diff = ask_price - close
                    sl_price = ask_price - diff - stop_loss
                    tk_price = ask_price - diff + take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Instrument: {instrument} - Close: {close} - "
                                f"Ask: {(ask_price):.5f} - "
                                f"ATR: {self.atr[instrument].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f} - "
                                f"Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.buy_bracket(
                        data=self.data[instrument],
                        size=size,
                        exectype=bt.Order.Market,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )

            # Check if a sell order could be opened
            if not self.order_manager.has_selled(instrument):
                if self.near_sell_signal(instrument):
                    self.log(self.messages.near_sell_signal(instrument))
                    if self.config["tts"]:
                        self.tts.say(
                            self.messages.near_sell_signal(
                                f"{' '.join(instrument.split('_'))}"
                            )
                        )
                if self.enter_sell_signal(instrument) and not self.testing:
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(instrument)
                    stop_loss = self.get_stop_loss(instrument)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(instrument)

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[instrument],
                        isbuy=False,
                        pips=s_l_pips / self.broker.o.get_leverage(),
                    )

                    # Get the current bid price and calculate SL and TK
                    bid_price = self.instrument_manager.get_bid_price(
                        instrument
                    )
                    diff = close - bid_price
                    sl_price = bid_price + diff + stop_loss
                    tk_price = bid_price + diff - take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Instrument: {instrument} - Close: {close} - "
                                f"Bid: {bid_price:.5f} - "
                                f"ATR: {self.atr[instrument].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f} - "
                                f"Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.sell_bracket(
                        data=self.data[instrument],
                        size=size,
                        exectype=bt.Order.Market,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )

            # Stop the execution when running a test
            if self.testing:
                raise bt.StrategySkipError
