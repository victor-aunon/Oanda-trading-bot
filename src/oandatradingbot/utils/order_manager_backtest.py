# Libraries
from typing import Any, Dict, List, Optional

# Packages
from backtrader import Order, BackBroker

# Local
from oandatradingbot.utils.instrument_units import PIP_UNITS
from oandatradingbot.utils.messages import Messages


class OrderManagerBackTest:
    def __init__(
        self, messages_engine: Messages,
        pairs: List[str],
        profit_risk_ratio: float,
        broker: BackBroker
    ) -> None:
        self.messages = messages_engine
        self.p_r_ratio = profit_risk_ratio
        self.broker = broker
        self.selled, self.buyed = {}, {}
        self.sell_order, self.buy_order = {}, {}
        self.trades: Dict[str, List[Dict[str, Any]]] = {}
        for pair in pairs:
            self.buyed[pair] = False
            self.selled[pair] = False
            self.buy_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.sell_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.trades[pair] = []

    def manage_buy_order(
        self, order: Order, size: float, timestamp: str, last_close: float
    ) -> str:
        pair = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.buy_order[pair]["MK"] = order
            self.buy_order[pair]["entry_time"] = timestamp  # type: ignore
            response = self.messages.buy_order_placed(
                round(size, 2), pair, order.executed.price
            )
        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.buy_order[pair]["SL"] = order
            response = ""
        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.buy_order[pair]["TK"] = order
            response = ""
        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            self.buy_order[pair]["SL"] = order
            loss = size * -1
            self.broker.set_cash(self.broker.get_cash() + loss)
            self.buy_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("BUY", "SL", pair, loss)
            self.buy_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.buyed[pair] = False
            response = self.messages.stop_buy_order(pair, abs(loss))
        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            self.buy_order[pair]["TK"] = order
            profit = size * self.p_r_ratio
            self.broker.set_cash(self.broker.get_cash() + profit)
            self.buy_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("BUY", "TK", pair, profit)
            self.buy_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.buyed[pair] = False
            response = self.messages.limit_buy_order(pair, profit)
        elif status == "Expired":
            if self.buy_order[pair]["MK"] is None:
                return ""
            open = self.buy_order[pair]["MK"].executed.price  # type: ignore
            if last_close >= open:
                tk = self.buy_order[pair]["TK"].price  # type: ignore
                pl = (last_close - open) / (tk - open) \
                    * size * self.p_r_ratio
            else:
                sl = self.buy_order[pair]["SL"].price  # type: ignore
                pl = (open - last_close) / (open - sl) \
                    * (size * -1)
            self.broker.set_cash(self.broker.get_cash() + pl)
            self.buy_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("BUY", "CANCEL", pair, pl, last_close)
            self.buy_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.buyed[pair] = False
            response = self.messages.buy_order_canceled(pair, pl)
        else:
            response = ""
        return response

    def manage_sell_order(
        self, order: Order, size: float, timestamp: str, last_close: float
    ) -> str:
        pair = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.sell_order[pair]["MK"] = order
            self.sell_order[pair]["entry_time"] = timestamp  # type: ignore
            response = self.messages.sell_order_placed(
                round(size, 2), pair, order.executed.price
            )
        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.sell_order[pair]["SL"] = order
            response = ""
        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.sell_order[pair]["TK"] = order
            response = ""
        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            self.sell_order[pair]["SL"] = order
            loss = size * -1
            self.broker.set_cash(self.broker.get_cash() + loss)
            self.sell_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("SELL", "SL", pair, loss)
            self.sell_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.selled[pair] = False
            response = self.messages.stop_sell_order(pair, abs(loss))
        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            self.sell_order[pair]["TK"] = order
            profit = size * self.p_r_ratio
            self.broker.set_cash(self.broker.get_cash() + profit)
            self.sell_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("SELL", "TK", pair, profit)
            self.sell_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.selled[pair] = False
            response = self.messages.limit_sell_order(pair, profit)
        elif status == "Expired":
            if self.sell_order[pair]["MK"] is None:
                return ""
            open = self.sell_order[pair]["MK"].executed.price  # type: ignore
            if last_close <= open:
                tk = self.sell_order[pair]["TK"].price  # type: ignore
                pl = (open - last_close) / (open - tk) \
                    * size * self.p_r_ratio
            else:
                sl = self.sell_order[pair]["SL"].price  # type: ignore
                pl = (last_close - open) / (sl - open) \
                    * size * -1
            self.broker.set_cash(self.broker.get_cash() + pl)
            self.sell_order[pair]["exit_time"] = timestamp  # type: ignore
            self._store_trade("SELL", "CANCEL", pair, pl, last_close)
            self.sell_order[pair] = {
                "MK": None,
                "SL": None,
                "TK": None,
                "entry_time": None,
                "exit_time": None
            }
            self.selled[pair] = False
            response = self.messages.sell_order_canceled(pair, pl)
        else:
            response = ""
        return response

    def _store_trade(
        self, op_type: str, order_type: str, pair: str, pl: float,
        exit_price: Optional[float] = None
    ) -> None:
        if op_type == "BUY":
            main_order = self.buy_order[pair]
        elif op_type == "SELL":
            main_order = self.sell_order[pair]

        if exit_price is None:
            exit_price = main_order[order_type].executed.price  # type: ignore
        try:
            entry_price = main_order["MK"].executed.price  # type: ignore
        except Exception:
            entry_price = exit_price
        sl_price = main_order["SL"].created.price  # type: ignore
        tk_price = main_order["TK"].created.price  # type: ignore
        units = PIP_UNITS[pair.split("_")[1]]
        tk_pips = (tk_price - entry_price) * units if op_type == "BUY" \
            else (entry_price - tk_price) * units
        sl_pips = (entry_price - sl_price) * units if op_type == "BUY" \
            else (sl_price - entry_price) * units

        self.trades[pair].append({
            "Entry": main_order["entry_time"],
            "Exit": main_order["exit_time"],
            "Operation": op_type,
            "Entry price": round(entry_price, 5),
            "Exit price": round(exit_price, 5),  # type: ignore
            "SL": round(sl_price, 5),
            "SL (pips)": round(sl_pips, 2),
            "TK": round(tk_price, 5),
            "TK (pips)": round(tk_pips, 2),
            "PL": round(pl, 2)
        })
