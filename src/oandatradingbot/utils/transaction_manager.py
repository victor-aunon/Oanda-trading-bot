# Libraries
from datetime import datetime
from typing import Dict, Literal, Optional

# Locals
from oandatradingbot.repository.repository import Repository
from oandatradingbot.types.api_transaction \
    import ApiTransactionType, empty_transaction
from oandatradingbot.types.config import ConfigType
from oandatradingbot.types.order import OperationType, OrdersType
from oandatradingbot.types.trade import TradeRegistryType, TradeDbType
from oandatradingbot.utils.instrument_manager import InstrumentManager
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.telegram_bot import TelegramBot
from oandatradingbot.utils.tts import TTS

IsBuyedSelledType = Dict[OperationType, Dict[str, bool]]
ExitType = Literal["TK", "SL", "CANCEL"]


class TransactionManager:
    def __init__(
        self, config: ConfigType, telegram_bot: Optional[TelegramBot] = None
    ) -> None:
        self.instrument_manager = InstrumentManager(config)
        self.messages = Messages(
            config["language"], config["account_currency"]
        )
        self.repository = Repository(config["database_uri"])
        if "tts" in config and config["tts"]:
            self.tts = TTS(
                config["language_tts"] if "language_tts" in config else "EN-US"
            )
        if telegram_bot is not None:
            self.telegram_bot = telegram_bot
        self.account_type = config["account_type"]
        self.trades_registry: TradeRegistryType = {}
        self.is_buyed_selled: IsBuyedSelledType = {"BUY": {}, "SELL": {}}
        self.orders: OrdersType = {"BUY": {}, "SELL": {}}

    def _reset_instrument_order(
        self, type: OperationType, instrument: str
    ) -> None:
        self.orders[type][instrument] = {
            "MK": empty_transaction,
            "SL": empty_transaction,
            "TK": empty_transaction,
            "CANCEL": empty_transaction
        }

    def _save_trade_in_repository(
        self, op_type: OperationType, exit_type: ExitType, instrument: str
    ) -> None:
        main_order = self.orders[op_type][instrument]
        entry_time = datetime.utcfromtimestamp(float(main_order["MK"]["time"]))
        exit_time = datetime.utcfromtimestamp(
            float(main_order[exit_type]["time"])
        )
        trade_pips = (
            float(main_order[exit_type]["price"])
            - float(main_order["MK"]["price"])
            ) * self.instrument_manager.get_units(instrument)
        stop_loss = abs(
            float(main_order["MK"]["price"])
            - float(main_order["SL"]["price"])
        ) * self.instrument_manager.get_units(instrument)
        take_profit = abs(
            float(main_order["MK"]["price"])
            - float(main_order["TK"]["price"])
        ) * self.instrument_manager.get_units(instrument)

        trade: TradeDbType = {
            "id": int(main_order["MK"]["id"]),
            "instrument": instrument,
            "account": self.account_type,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "duration": (exit_time - entry_time).seconds,
            "operation": op_type,
            "size": float(main_order["MK"]["units"]),
            "entry_price": float(main_order["MK"]["price"]),
            "exit_price": float(main_order[exit_type]["price"]),
            "trade_pips": trade_pips,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "canceled": False if exit_type in ["SL", "TK"] else True,
            "profit": round(float(main_order[exit_type]["pl"]), 2)
        }
        self.repository.save_trade(trade)

        if hasattr(self, "telegram_bot"):
            self.telegram_bot.notify_trade(int(main_order["MK"]["id"]))

    def market_order_submitted(self, transaction: ApiTransactionType) -> str:
        instrument = transaction["instrument"]
        op_type: OperationType = "BUY" \
            if float(transaction["units"]) > 0 else "SELL"
        self.trades_registry[transaction["id"]] = {
            "instrument": instrument, "op_type": op_type
        }
        if op_type == "BUY":
            return self.messages.buy_order_submitted(
                int(float(transaction["units"])),
                f"{' '.join(instrument.split('_'))}",
                transaction["id"]
            )
        elif op_type == "SELL":
            return self.messages.sell_order_submitted(
                int(float(transaction["units"])),
                f"{' '.join(instrument.split('_'))}",
                transaction["id"]
            )

    def market_order_rejected(self, transaction: ApiTransactionType) -> str:
        if transaction["orderID"] not in self.trades_registry:
            return ""
        instrument = self.trades_registry[transaction["orderID"]]["instrument"]
        op_type = self.trades_registry[transaction["orderID"]]["op_type"]

        if op_type == "BUY":
            self.trades_registry.pop(transaction["orderID"], None)
            return self.messages.buy_order_rejected(
                f"{' '.join(instrument.split('_'))}",
                transaction["orderID"]
            )
        elif op_type == "SELL":
            self.trades_registry.pop(transaction["orderID"], None)
            return self.messages.sell_order_rejected(
                f"{' '.join(instrument.split('_'))}",
                transaction["orderID"]
            )

    def register_market_order(self, transaction: ApiTransactionType) -> str:
        instrument = transaction["instrument"]
        # Remove any canceled trade with this instrument
        for key, val in list(self.trades_registry.items()):
            if val["instrument"] == instrument:
                self.trades_registry.pop(key, None)
        op_type: OperationType = "BUY" if float(transaction["units"]) > 0 \
            else "SELL"

        self.orders[op_type][instrument]["MK"] = transaction
        self.is_buyed_selled[op_type][instrument] = True
        self.trades_registry[transaction["id"]] = {
            "instrument": instrument, "op_type": op_type
        }
        if op_type == "BUY":
            message = self.messages.buy_order_placed(
                int(float(transaction["units"])),
                f"{' '.join(instrument.split('_'))}",
                float(transaction["price"]),
                transaction["id"]
            )
        elif op_type == "SELL":
            message = self.messages.sell_order_placed(
                int(float(transaction["units"])),
                f"{' '.join(instrument.split('_'))}",
                float(transaction["price"]),
                transaction["id"]
            )
        if hasattr(self, "tts"):
            self.tts.say(message)
        return message

    def register_take_profit_order(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = self.trades_registry[transaction["tradeID"]]["instrument"]
        op_type = self.trades_registry[transaction["tradeID"]]["op_type"]

        self.orders[op_type][instrument]["TK"] = transaction
        return self.messages.limit_order_accepted(
            instrument, transaction["tradeID"]
        )

    def replace_take_profit_order(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = self.trades_registry[transaction["tradeID"]]["instrument"]
        op_type = self.trades_registry[transaction["tradeID"]]["op_type"]

        self.orders[op_type][instrument]["TK"]["price"] = transaction["price"]
        self.orders[op_type][instrument]["TK"]["time"] = transaction["time"]
        return self.messages.limit_order_replaced(
            instrument, transaction["tradeID"]
        )

    def register_stop_loss_order(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = self.trades_registry[transaction["tradeID"]]["instrument"]
        op_type = self.trades_registry[transaction["tradeID"]]["op_type"]

        self.orders[op_type][instrument]["SL"] = transaction
        return self.messages.stop_order_accepted(
            instrument, transaction["tradeID"]
        )

    def replace_stop_loss_order(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = self.trades_registry[transaction["tradeID"]]["instrument"]
        op_type = self.trades_registry[transaction["tradeID"]]["op_type"]

        self.orders[op_type][instrument]["SL"]["price"] = transaction["price"]
        self.orders[op_type][instrument]["SL"]["time"] = transaction["time"]
        return self.messages.stop_order_replaced(
            instrument, transaction["tradeID"]
        )

    def take_profit_order_completed(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = transaction["instrument"]
        this_trade_id = transaction["tradesClosed"][0]["tradeID"]

        # Units negative since closing a buy order means a sell order
        op_type: OperationType = "BUY" if float(transaction["units"]) < 0 \
            else "SELL"
        trade_id = self.orders[op_type][instrument]["MK"]["id"]
        if this_trade_id != trade_id:
            return ""

        self.orders[op_type][instrument]["TK"] = transaction
        self._save_trade_in_repository(op_type, "TK", instrument)
        profit = float(transaction["pl"])
        self._reset_instrument_order(op_type, instrument)
        # Remove this trade from trades_registry since it is completed
        self.trades_registry.pop(this_trade_id, None)
        self.is_buyed_selled[op_type][instrument] = False
        if op_type == "BUY":
            message = self.messages.limit_buy_order(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        elif op_type == "SELL":
            message = self.messages.limit_sell_order(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        if hasattr(self, "tts"):
            self.tts.say(message)
        return message

    def stop_loss_order_completed(
        self, transaction: ApiTransactionType
    ) -> str:
        instrument = transaction["instrument"]
        this_trade_id = transaction["tradesClosed"][0]["tradeID"]

        # Units negative since closing a buy order means a sell order
        op_type: OperationType = "BUY" if float(transaction["units"]) < 0 \
            else "SELL"
        trade_id = self.orders[op_type][instrument]["MK"]["id"]
        if this_trade_id != trade_id:
            return ""

        self.orders[op_type][instrument]["SL"] = transaction
        self._save_trade_in_repository(op_type, "SL", instrument)
        profit = float(transaction["pl"])
        self._reset_instrument_order(op_type, instrument)
        # Remove this trade from trades_registry since it is completed
        self.trades_registry.pop(this_trade_id, None)
        self.is_buyed_selled[op_type][instrument] = False
        if op_type == "BUY":
            message = self.messages.stop_buy_order(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        elif op_type == "SELL":
            message = self.messages.stop_sell_order(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        if hasattr(self, "tts"):
            self.tts.say(message)
        return message

    def market_order_canceled(self, transaction: ApiTransactionType) -> str:
        instrument = transaction["instrument"]
        this_trade_id = transaction["tradesClosed"][0]["tradeID"]

        # Units negative since closing a buy order means a sell order
        op_type: OperationType = "BUY" if float(transaction["units"]) < 0 \
            else "SELL"
        trade_id = self.orders[op_type][instrument]["MK"]["id"]
        if this_trade_id != trade_id:
            return ""

        self.orders[op_type][instrument]["CANCEL"] = transaction
        self._save_trade_in_repository(op_type, "CANCEL", instrument)
        profit = float(transaction["pl"])
        self._reset_instrument_order(op_type, instrument)
        # Remove this trade from trades_registry since it is completed
        self.trades_registry.pop(this_trade_id, None)
        self.is_buyed_selled[op_type][instrument] = False
        if op_type == "BUY":
            message = self.messages.buy_order_canceled(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        elif op_type == "SELL":
            message = self.messages.sell_order_canceled(
                f"{' '.join(instrument.split('_'))}", profit, this_trade_id
            )
        if hasattr(self, "tts"):
            self.tts.say(message)
        return message
