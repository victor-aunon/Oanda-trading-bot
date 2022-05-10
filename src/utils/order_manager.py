# Libraries
from datetime import datetime

# Packages
from backtrader import Order
from sqlalchemy.orm import Session

# Local
from utils.cash_manager import CashManager
from utils.messages import Messages
from dbmodels.trade import Trade


class OrderManager:
    def __init__(
        self, messages_engine: Messages,
        db_session: Session,
        account_type: str,
        tts_engine=None
    ) -> None:
        self.messages = messages_engine
        self.db_session = db_session
        self.account_type = account_type
        self.tts = tts_engine
        self.has_buyed = False
        self.has_selled = False
        self.buy_order = {
            "MK": None, "SL": None, "TK": None, "entry_time": None
        }
        self.sell_order = {
            "MK": None, "SL": None, "TK": None,  "entry_time": None
        }

    def manage_buy_order(
        self, order, cash_manager: CashManager, timestamp: str
    ) -> str:
        pair = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.buy_order["MK"] = order
            self.buy_order["entry_time"] = datetime.utcnow()  # type: ignore
            if self.tts is not None:
                self.tts.say(
                    self.messages.buy_order_placed(
                        order.size, f"{pair[0:3]} {pair[3:]}",
                        order.executed.price
                    )
                )
            response = self.messages.buy_order_placed(
                order.size, pair, order.executed.price
            )
        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.buy_order["SL"] = order
            response = self.messages.stop_order_accepted(pair)
        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.buy_order["TK"] = order
            response = self.messages.limit_order_accepted(pair)
        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            loss = round(
                cash_manager.profit(
                    self.buy_order["MK"].executed.price,  # type: ignore
                    order.executed.price,
                    abs(order.size),
                    "BUY",
                    timestamp,
                ),
                2,
            )
            self._store_trade_in_db("BUY", "SL", cash_manager.units, loss)
            if self.tts is not None:
                self.tts.say(
                    self.messages.stop_buy_order(
                        f"{pair[0:3]} {pair[3:]}", abs(loss)
                    )
                )
            self.buy_order = {"MK": None, "SL": None, "TK": None}
            self.has_buyed = False
            response = self.messages.stop_buy_order(pair, loss)
        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            profit = round(
                cash_manager.profit(
                    self.buy_order["MK"].executed.price,  # type: ignore
                    order.executed.price,
                    abs(order.size),
                    "BUY",
                    timestamp,
                ),
                2,
            )
            self._store_trade_in_db("BUY", "TK", cash_manager.units, profit)
            if self.tts is not None:
                self.tts.say(
                    self.messages.limit_buy_order(
                        f"{pair[0:3]} {pair[3:]}", profit
                    )
                )
            self.buy_order = {"MK": None, "SL": None, "TK": None}
            self.has_buyed = False
            response = self.messages.limit_buy_order(pair, profit)
        # Main order canceled
        elif status in ["Canceled", "Margin"]:
            if self.tts is not None:
                self.tts.say(
                    self.messages.buy_order_canceled(f"{pair[0:3]} {pair[3:]}")
                )
            self.buy_order = {"MK": None, "SL": None, "TK": None}
            self.has_buyed = False
            response = self.messages.buy_order_canceled(pair)
        else:
            response = ""
        return response

    def manage_sell_order(
        self, order: Order, cash_manager: CashManager, timestamp: str
    ) -> str:
        pair = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.sell_order["MK"] = order
            self.sell_order["entry_time"] = datetime.utcnow()  # type: ignore
            if self.tts is not None:
                self.tts.say(
                    self.messages.sell_order_placed(
                        order.size, f"{pair[0:3]} {pair[3:]}",
                        order.executed.price
                    )
                )
            response = self.messages.sell_order_placed(
                order.size, pair, order.executed.price
            )
        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.sell_order["SL"] = order
            response = self.messages.stop_order_accepted(pair)
        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.sell_order["TK"] = order
            response = self.messages.limit_order_accepted(pair)
        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            loss = round(
                cash_manager.profit(
                    self.sell_order["MK"].executed.price,  # type: ignore
                    order.executed.price,
                    abs(order.size),
                    "SELL",
                    timestamp,
                ),
                2,
            )
            self._store_trade_in_db("SELL", "SL", cash_manager.units, loss)
            if self.tts is not None:
                self.tts.say(
                    self.messages.stop_sell_order(
                        f"{pair[0:3]} {pair[3:]}", abs(loss)
                    )
                )
            self.sell_order = {"MK": None, "SL": None, "TK": None}
            self.has_selled = False
            response = self.messages.stop_sell_order(pair, loss)
        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            profit = round(
                cash_manager.profit(
                    self.sell_order["MK"].executed.price,  # type: ignore
                    order.executed.price,
                    abs(order.size),
                    "SELL",
                    timestamp,
                ),
                2,
            )
            self._store_trade_in_db("SELL", "TK", cash_manager.units, profit)
            if self.tts is not None:
                self.tts.say(
                    self.messages.limit_sell_order(
                        f"{pair[0:3]} {pair[3:]}", profit
                    )
                )
            self.sell_order = {"MK": None, "SL": None, "TK": None}
            self.has_selled = False
            response = self.messages.limit_sell_order(pair, profit)
        # Main order canceled
        elif status in ["Canceled", "Margin"]:
            if self.tts is not None:
                self.tts.say(
                    self.messages.sell_order_canceled(
                        f"{pair[0:3]} {pair[3:]}"
                    )
                )
            self.sell_order = {"MK": None, "SL": None, "TK": None}
            self.has_selled = False
            response = self.messages.sell_order_canceled(pair)
        else:
            response = ""
        return response

    def _store_trade_in_db(
        self, type: str, exit_type: str, units: float, profit: float
    ) -> None:
        main_order = self.buy_order if type == "BUY" else self.sell_order
        # if exit_type == "Canceled":
        exit_price = main_order[exit_type].executed.price  # type: ignore

        duration = datetime.utcnow() - main_order["entry_time"]  # type: ignore
        spread = abs(
            main_order["MK"].executed.price  # type: ignore
            - main_order["MK"].created.price  # type: ignore
        )
        pips = (exit_price
                - main_order["MK"].executed.price) / units  # type: ignore
        stop_loss = abs(
            main_order["MK"].executed.price  # type: ignore
            - main_order["SL"].executed.price  # type: ignore
        ) / units
        take_profit = abs(
            main_order["MK"].executed.price  # type: ignore
            - main_order["TK"].executed.price  # type: ignore
        ) / units

        with self.db_session as session:
            trade_db = Trade(
                pair=main_order["MK"].data._name,  # type: ignore
                account=self.account_type,
                entry_time=main_order["entry_time"],
                exit_time=datetime.utcnow(),
                duration=duration.seconds,
                operation=type,
                open_price=main_order["MK"].executed.price,  # type: ignore
                exit_price=exit_price,
                spread=spread,
                trade_pips=pips,
                stop_loss=stop_loss,
                take_profit=take_profit,
                canceled=False if exit_type in ["SL", "TK"] else True,
                profit=profit,
            )
            session.add(trade_db)
            session.commit()
        pass
