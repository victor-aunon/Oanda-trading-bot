# Libraries
from datetime import datetime
from typing import Any, List, Dict, Optional

# Packages
from sqlalchemy import Boolean
from sqlalchemy.orm import Session

# Local
from oandatradingbot.utils.instrument_manager import InstrumentManager
from oandatradingbot.utils.messages import Messages
from oandatradingbot.utils.telegram_bot import TelegramBot
from oandatradingbot.utils.tts import TTS
from oandatradingbot.dbmodels.trade import Trade


REJECTED_REASONS = [
    "STOP_LOSS_ON_FILL_LOSS",
    "TAKE_PROFIT_ON_FILL_LOSS",
    "INSUFFICIENT_LIQUIDITY"
]

CANCEL_REASONS = ["MARKET_ORDER_POSITION_CLOSEOUT", "MARKET_ORDER_TRADE_CLOSE"]


class OrderManager:
    def __init__(
        self, messages_engine: Messages,
        db_session: Session,
        instrument_manager: InstrumentManager,
        account_type: str,
        pairs: List[str],
        tts_engine: Optional[TTS] = None,
        telegram_bot: Optional[TelegramBot] = None
    ) -> None:
        self.messages = messages_engine
        self.db_session = db_session
        self.instrument_manager = instrument_manager
        self.account_type = account_type
        self.tts = tts_engine
        self.telegram_bot = telegram_bot
        self.selled, self.buyed = {}, {}
        self.sell_order, self.buy_order = {}, {}
        self.trade_dict = {}  # type: ignore
        for pair in pairs:
            self.buyed[pair] = False
            self.selled[pair] = False
            self.buy_order[pair] = {
                "MK": None, "SL": None, "TK": None, "CANCEL": None
            }
            self.sell_order[pair] = {
                "MK": None, "SL": None, "TK": None, "CANCEL": None
            }

    def has_buyed(self, pair: str) -> Boolean:
        return self.buyed[pair]

    def has_selled(self, pair: str) -> Boolean:
        return self.selled[pair]

    def manage_transaction(self, transaction: Dict[str, Any]) -> str:
        # Submit market order
        if transaction["type"] == "MARKET_ORDER" \
                and transaction["reason"] == "CLIENT_ORDER":
            pair = transaction["instrument"]
            # Buy order
            if float(transaction["units"]) > 0:
                self.trade_dict[transaction["id"]] = {
                    "pair": pair, "op_type": "BUY"
                }
                response = self.messages.buy_order_submitted(
                    int(float(transaction["units"])),
                    f"{' '.join(pair.split('_'))}",
                    transaction["id"]
                )
            # Sell order
            else:
                self.trade_dict[transaction["id"]] = {
                    "pair": pair, "op_type": "SELL"
                }
                response = self.messages.sell_order_submitted(
                    int(float(transaction["units"])),
                    f"{' '.join(pair.split('_'))}",
                    transaction["id"]
                )

        # Market order rejected (stop loss on fill loss)
        elif transaction["type"] == "ORDER_CANCEL" \
                and transaction["reason"] in REJECTED_REASONS:
            if transaction["orderID"] not in self.trade_dict:
                return ""
            pair = self.trade_dict[transaction["orderID"]]["pair"]
            op_type = self.trade_dict[transaction["orderID"]]["op_type"]

            if op_type == "BUY":
                self.trade_dict.pop(transaction["orderID"], None)
                response = self.messages.buy_order_rejected(
                    f"{' '.join(pair.split('_'))}",
                    transaction["orderID"]
                )
            elif op_type == "SELL":
                self.trade_dict.pop(transaction["orderID"], None)
                response = self.messages.sell_order_rejected(
                    f"{' '.join(pair.split('_'))}",
                    transaction["orderID"]
                )

        # Register market order
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "MARKET_ORDER":
            pair = transaction["instrument"]
            # Remove any canceled trade with this pair
            for key, val in list(self.trade_dict.items()):
                if val["pair"] == pair:
                    self.trade_dict.pop(key, None)
            # Buy order
            if float(transaction["units"]) > 0:
                self.buy_order[pair]["MK"] = transaction  # type: ignore
                self.buyed[pair] = True
                self.trade_dict[transaction["id"]] = {
                    "pair": pair, "op_type": "BUY"
                }
                if self.tts is not None:
                    self.tts.say(
                        self.messages.buy_order_placed(
                            int(float(transaction["units"])),
                            f"{' '.join(pair.split('_'))}",
                            float(transaction["price"])
                        )
                    )
                response = self.messages.buy_order_placed(
                    int(float(transaction["units"])),
                    f"{' '.join(pair.split('_'))}",
                    float(transaction["price"]),
                    transaction["id"]
                )
            # Sell order
            else:
                self.sell_order[pair]["MK"] = transaction  # type: ignore
                self.selled[pair] = True
                self.trade_dict[transaction["id"]] = {
                    "pair": pair, "op_type": "SELL"
                }
                if self.tts is not None:
                    self.tts.say(
                        self.messages.sell_order_placed(
                            int(float(transaction["units"])),
                            f"{' '.join(pair.split('_'))}",
                            float(transaction["price"])
                        )
                    )
                response = self.messages.sell_order_placed(
                    int(float(transaction["units"])),
                    f"{' '.join(pair.split('_'))}",
                    float(transaction["price"]),
                    transaction["id"]
                )

        # Register take profit order
        elif transaction["type"] == "TAKE_PROFIT_ORDER" \
                and transaction["reason"] == "ON_FILL":
            pair = self.trade_dict[transaction["tradeID"]]["pair"]
            op_type = self.trade_dict[transaction["tradeID"]]["op_type"]
            if op_type == "BUY":
                self.buy_order[pair]["TK"] = transaction  # type: ignore
            elif op_type == "SELL":
                self.sell_order[pair]["TK"] = transaction  # type: ignore
            response = self.messages.limit_order_accepted(
                pair, transaction["tradeID"]
            )

        # Replace take profit order
        elif transaction["type"] == "TAKE_PROFIT_ORDER" \
                and transaction["reason"] == "REPLACEMENT":
            pair = self.trade_dict[transaction["tradeID"]]["pair"]
            op_type = self.trade_dict[transaction["tradeID"]]["op_type"]
            if op_type == "BUY":
                self.buy_order[pair][  # type: ignore
                    "TK"]["price"] = transaction["price"]  # type: ignore
                self.buy_order[pair][  # type: ignore
                    "TK"]["time"] = transaction["time"]  # type: ignore
            elif op_type == "SELL":
                self.sell_order[pair][  # type: ignore
                    "TK"]["price"] = transaction["price"]  # type: ignore
                self.sell_order[pair][  # type: ignore
                    "TK"]["time"] = transaction["time"]  # type: ignore
            response = self.messages.limit_order_replaced(
                pair, transaction["tradeID"]
            )

        # Register stop loss order
        elif transaction["type"] == "STOP_LOSS_ORDER" \
                and transaction["reason"] == "ON_FILL":
            pair = self.trade_dict[transaction["tradeID"]]["pair"]
            op_type = self.trade_dict[transaction["tradeID"]]["op_type"]
            if op_type == "BUY":
                self.buy_order[pair]["SL"] = transaction  # type: ignore
            elif op_type == "SELL":
                self.sell_order[pair]["SL"] = transaction  # type: ignore
            response = self.messages.stop_order_accepted(
                pair, transaction["tradeID"]
            )

        # Replace stop loss order
        elif transaction["type"] == "STOP_LOSS_ORDER" \
                and transaction["reason"] == "REPLACEMENT":
            pair = self.trade_dict[transaction["tradeID"]]["pair"]
            op_type = self.trade_dict[transaction["tradeID"]]["op_type"]
            if op_type == "BUY":
                self.buy_order[pair][  # type: ignore
                    "SL"]["price"] = transaction["price"]  # type: ignore
                self.buy_order[pair][  # type: ignore
                    "SL"]["time"] = transaction["time"]  # type: ignore
            elif op_type == "SELL":
                self.sell_order[pair][  # type: ignore
                    "SL"]["price"] = transaction["price"]  # type: ignore
                self.sell_order[pair][  # type: ignore
                    "SL"]["time"] = transaction["time"]  # type: ignore
            response = self.messages.stop_order_replaced(
                pair, transaction["tradeID"]
            )

        # Limit order completed
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "TAKE_PROFIT_ORDER":
            pair = transaction["instrument"]
            this_trade_id = transaction["tradesClosed"][0]["tradeID"]
            # Buy order
            # Units negative since closing a buy order means a sell order
            if float(transaction["units"]) < 0:
                trade_id = \
                    self.buy_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.buy_order[pair]["TK"] = transaction  # type: ignore
                self._store_trade_in_db("BUY", "TK", pair)
                profit = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.limit_buy_order(
                            f"{' '.join(pair.split('_'))}", profit
                        )
                    )
                self.buy_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.buyed[pair] = False
                response = self.messages.limit_buy_order(
                    pair, profit, this_trade_id
                )
            # Sell order
            else:
                trade_id = \
                    self.sell_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.sell_order[pair]["TK"] = transaction  # type: ignore
                self._store_trade_in_db("SELL", "TK", pair)
                profit = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.limit_sell_order(
                            f"{' '.join(pair.split('_'))}", profit
                        )
                    )
                self.sell_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.selled[pair] = False
                response = self.messages.limit_sell_order(
                    pair, profit, this_trade_id
                )

        # Stop order completed
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "STOP_LOSS_ORDER":
            pair = transaction["instrument"]
            this_trade_id = transaction["tradesClosed"][0]["tradeID"]
            # Buy order
            # Units negative since closing a buy order means a sell order
            if float(transaction["units"]) < 0:
                trade_id = \
                    self.buy_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.buy_order[pair]["SL"] = transaction  # type: ignore
                self._store_trade_in_db("BUY", "SL", pair)
                loss = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.stop_buy_order(
                            f"{' '.join(pair.split('_'))}", abs(loss)
                        )
                    )
                self.buy_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.buyed[pair] = False
                response = self.messages.stop_buy_order(
                    pair, abs(loss), this_trade_id
                )
            # Sell order
            else:
                trade_id = \
                    self.sell_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.sell_order[pair]["SL"] = transaction  # type: ignore
                self._store_trade_in_db("SELL", "SL", pair)
                loss = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.stop_sell_order(
                            f"{' '.join(pair.split('_'))}", abs(loss)
                        )
                    )
                self.sell_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.selled[pair] = False
                response = self.messages.stop_sell_order(
                    pair, abs(loss), this_trade_id
                )

        # Market order canceled
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] in CANCEL_REASONS:
            pair = transaction["instrument"]
            this_trade_id = transaction["tradesClosed"][0]["tradeID"]
            # Buy order
            # Units negative since closing a buy order means a sell order
            if float(transaction["units"]) < 0:
                trade_id = \
                    self.buy_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.buy_order[pair]["CANCEL"] = transaction  # type:ignore
                self._store_trade_in_db("BUY", "CANCEL", pair)
                pl = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.buy_order_canceled(
                            f"{' '.join(pair.split('_'))}", pl
                        )
                    )
                self.buy_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.buyed[pair] = False
                response = self.messages.buy_order_canceled(
                    pair, pl, this_trade_id
                )
            # Sell order
            else:
                trade_id = \
                    self.sell_order[pair]["MK"]["id"]  # type: ignore
                if this_trade_id != trade_id:
                    return ""
                self.sell_order[pair]["CANCEL"] = \
                    transaction  # type: ignore
                self._store_trade_in_db("SELL", "CANCEL", pair)
                pl = float(transaction["pl"])
                if self.tts is not None:
                    self.tts.say(
                        self.messages.sell_order_canceled(
                            f"{' '.join(pair.split('_'))}", pl
                        )
                    )
                self.sell_order[pair] = {
                    "MK": None, "SL": None, "TK": None, "CANCEL": None
                }
                self.trade_dict.pop(this_trade_id, None)
                self.selled[pair] = False
                response = self.messages.sell_order_canceled(
                    pair, pl, this_trade_id
                )
        else:
            response = ""
        return response

    def _store_trade_in_db(self, type: str, exit_type: str, pair: str) -> None:
        main_order = self.buy_order[pair] if type == "BUY" \
            else self.sell_order[pair]
        entry_time = datetime.utcfromtimestamp(
            float(main_order["MK"]["time"])  # type: ignore
        )
        exit_time = datetime.utcfromtimestamp(
            float(main_order[exit_type]["time"])  # type: ignore
        )
        duration = exit_time - entry_time
        entry_price = float(main_order["MK"]["price"])  # type: ignore
        exit_price = float(main_order[exit_type]["price"])  # type: ignore
        units = self.instrument_manager.get_units(pair)
        trade_pips = (
            float(main_order[exit_type]["price"])  # type: ignore
            - float(main_order["MK"]["price"])  # type: ignore
            ) * units
        stop_loss = abs(
            float(main_order["MK"]["price"])  # type: ignore
            - float(main_order["SL"]["price"])  # type: ignore
        ) * units
        take_profit = abs(
            float(main_order["MK"]["price"])  # type: ignore
            - float(main_order["TK"]["price"])  # type: ignore
        ) * units
        profit = round(float(main_order[exit_type]["pl"]), 2)  # type:ignore

        with self.db_session as session:
            trade_db = Trade(
                id=int(main_order["MK"]["id"]),  # type: ignore
                pair=pair,
                account=self.account_type,
                entry_time=entry_time,
                exit_time=exit_time,
                duration=duration.seconds,
                operation=type,
                size=float(main_order["MK"]["units"]),  # type: ignore
                entry_price=entry_price,
                exit_price=exit_price,
                trade_pips=trade_pips,
                stop_loss=stop_loss,
                take_profit=take_profit,
                canceled=False if exit_type in ["SL", "TK"] else True,
                profit=profit,
            )
            session.add(trade_db)
            session.commit()

        # Send Telegram notification if required
        if self.telegram_bot is not None:
            if self.telegram_bot.report_freq == "Trade":
                self.telegram_bot.notify_trade(
                    int(main_order["MK"]["id"])  # type: ignore
                )
        return
