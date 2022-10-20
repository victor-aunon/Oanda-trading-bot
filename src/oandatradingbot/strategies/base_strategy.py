# Libraries
import ast
from datetime import datetime
from pprint import pprint
from typing import List, Optional, Union

# Packages
import backtrader as bt

# Local
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.instrument_manager import InstrumentManager
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.order_manager import OrderManager
from oandatradingbot.utils.telegram_bot import TelegramBot
from oandatradingbot.utils.tts import TTS


class BaseStrategy(bt.Strategy):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config: ConfigType = kwargs
        self.check_config()
        self.pairs: List[str] = kwargs["pairs"]
        self.account_type: str = kwargs["account_type"]
        self.account_currency: str = kwargs["account_currency"]
        self.testing: bool = kwargs["testing"]
        # Attributes that do not require dictionaries
        self.messages = Messages(
            self.config["language"], kwargs["account_currency"]
        )
        if kwargs["tts"]:
            self.tts = TTS(self.config["language_tts"], 120)
        self.instrument_manager = InstrumentManager(self.config)
        if "telegram_token" in self.config:
            self.telegram_bot = TelegramBot(
                kwargs["telegram_token"],
                kwargs["telegram_chat_id"],
                self.config["database_uri"],
                self.account_currency,
                kwargs["telegram_report_frequency"]
                if "telegram_report_frequency" in kwargs
                else "Daily",
                kwargs["telegram_report_hour"]
                if "telegram_report_hour" in kwargs
                else 22,
            )
            self.check_telegram_bot()
        self.order_manager = OrderManager(
            self.messages,
            self.config["database_uri"],
            self.instrument_manager,
            self.account_type,
            self.pairs,
            self.tts if self.config["tts"] else None,
            self.telegram_bot if "telegram_token" in self.config else None,
        )
        self.initialize_dicts()

    @staticmethod
    def datetime_to_str(timestamp: datetime) -> str:
        return datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

    def check_config(self) -> None:
        # Check oanda tokens and account id
        if self.broker.o.get_currency() is None:
            print(
                "ERROR: Invalid config file. Make sure you have passed",
                "a valid config JSON file and a valid OANDA access token",
                "and account id.",
            )
            raise bt.StrategySkipError
        # Check language
        if "language" not in self.config or self.config["language"] not in [
            "EN-US",
            "ES-ES",
        ]:
            print(
                "WARNING: Invalid language in config file. Switching to EN-US"
            )
            self.config["language"] = "EN-US"

    def check_telegram_bot(self) -> None:
        if self.telegram_bot.check_bot().status_code != 200:
            print(
                "WARNING: Invalid Telegram bot token access. Check the config",
                "JSON file.",
            )
            self.telegram_bot = None  # type: ignore

    def initialize_dicts(self) -> None:
        pass

    def log(self, text: str, dt: Optional[datetime] = None):
        # dt = dt or self.data[data_name].datetime.datetime(0)
        dtime = dt or self.datetime_to_str(datetime.now())
        print(f"{dtime} - {text}")

    def get_stop_loss(self, data_name: str) -> float:
        pass

    def get_take_profit(self, data_name: str) -> float:
        pass

    def enter_buy_signal(self, data_name: str) -> bool:
        pass

    def near_buy_signal(self, data_name: str) -> bool:
        pass

    def enter_sell_signal(self, data_name: str) -> bool:
        pass

    def near_sell_signal(self, data_name: str) -> bool:
        pass

    def notify_data(self, data: bt.DataBase, status: str) -> None:
        self.log(f"Data status: {data._name} -> {data._getstatusname(status)}")
        for pair in self.pairs:
            if data._name == pair and status == data.LIVE:
                self.data_ready[pair] = True
            elif data._name == pair and status != data.LIVE:
                self.data_ready[pair] = False

    def notify_order(self, order: bt.Order) -> None:
        pass

    def notify_trade(self, trade: bt.Trade) -> None:
        pass

    def notify_store(
        self,
        msg: Union[dict[str, str], str],
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

    def manage_telegram_notifications(self) -> None:  # TODO: move to TB
        if not hasattr(self, "telegram_bot"):
            return
        now = datetime.now()
        notify_hour = now.hour if self.testing \
            else self.telegram_bot.report_hour
        notify_week_day = now.weekday() if self.testing else 4

        # Reset daily notification
        if now.hour == 0:
            self.telegram_bot.daily_notification = True
        # Reset weekly notification
        if now.hour == 0 and now.weekday() == 4:
            self.telegram_bot.weekly_notification = True

        # Send daily notification
        if self.telegram_bot.daily_notification and now.hour == notify_hour:
            response = self.telegram_bot.daily_report(now)
            if response is None:
                return
            if response.status_code == 200:
                self.telegram_bot.daily_notification = False
                self.log("Daily report sent via Telegram")
        # Send weekly notification
        if (
            self.telegram_bot.weekly_notification
            and now.hour == notify_hour
            and now.weekday() == notify_week_day
        ):  # Weekly rep. on Friday
            response = self.telegram_bot.weekly_report(now)
            if response is None:
                return
            if response.status_code == 200:
                self.telegram_bot.weekly_notification = False
                self.log("Weekly report sent via Telegram")

    def next(self) -> None:
        # Iterate over each currency pair since data is a list of feeds named
        # by each pair
        for pair in self.pairs:
            # Only do operations if the data is ready (LIVE)
            if not self.data_ready[pair]:
                return

            # Log the closing price
            # timestamp = self.data[pair].datetime.datetime(0)
            close: float = self.data[pair].close[0]
            text = f"{pair} - {close}"
            if self.config["debug"]:
                self.log(text)

            # Manage daily and weekly Telegram notifications
            self.manage_telegram_notifications()

            # Stop the execution when running a test
            if self.testing:
                self.order_manager.cancel_pending_trades()
                raise bt.StrategySkipError

            # Check if today is Friday to close pending trades at the
            # end of the session
            now = datetime.utcnow()
            if (
                now.weekday() == 4
                and now.hour == 20
                and now.minute == 60 - self.config["timeframe_num"]
            ):
                self.order_manager.cancel_pending_trades()
                return

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
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(pair)
                    stop_loss = self.get_stop_loss(pair)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(pair)

                    # Calculate lot size
                    size: float = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=True,
                        pips=s_l_pips / self.broker.o.get_leverage(),
                    )

                    # Get the current ask price and calculate SL and TK
                    ask_price = self.instrument_manager.get_ask_price(pair)
                    diff = ask_price - close
                    sl_price = ask_price - diff - stop_loss
                    tk_price = ask_price - diff + take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} - Close: {close} - "
                                f"Ask: {(ask_price):.5f} - "
                                f"ATR: {self.atr[pair].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f} - "
                                f"Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.buy_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
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
                    # Calculate SL and TK based on ATR and Profit/Risk ratio
                    units = self.instrument_manager.get_units(pair)
                    stop_loss = self.get_stop_loss(pair)
                    s_l_pips = stop_loss * units
                    take_profit = self.get_take_profit(pair)

                    # Calculate lot size
                    size = self.getsizer().getsizing(
                        self.data[pair],
                        isbuy=False,
                        pips=s_l_pips / self.broker.o.get_leverage(),
                    )

                    # Get the current bid price and calculate SL and TK
                    bid_price = self.instrument_manager.get_bid_price(pair)
                    diff = close - bid_price
                    sl_price = bid_price + diff + stop_loss
                    tk_price = bid_price + diff - take_profit

                    if self.config["debug"]:
                        self.log(
                            (
                                f"Pair: {pair} - Close: {close} - "
                                f"Bid: {bid_price:.5f} - "
                                f"ATR: {self.atr[pair].atr[0]:.4f} - "
                                f"SL (pips): {s_l_pips:.2f} - TK (pips): "
                                f"{(take_profit * units):.2f} - "
                                f"SL price: {sl_price:.5f} - "
                                f"TK price: {tk_price:.5f} - "
                                f"Size: {size}"
                            )
                        )

                    # Create bracket order
                    self.sell_bracket(
                        data=self.data[pair],
                        size=size,
                        exectype=bt.Order.Market,
                        stopprice=sl_price,
                        stopexec=bt.Order.Stop,
                        limitprice=tk_price,
                        limitexec=bt.Order.Limit,
                    )
