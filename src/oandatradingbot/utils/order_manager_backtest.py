# Libraries
from typing import Dict, List, Literal, Optional

# Packages
from backtrader import Order, BackBroker

# Local
from oandatradingbot.types.order import OperationType, OrdersBTType, \
    EmptyBTOrder
from oandatradingbot.types.trade import TradeType
from oandatradingbot.utils.instrument_units import PIP_UNITS
from oandatradingbot.utils.messages import Messages

IsBuyOrSellType = dict[str, Literal["BUY", "SELL"]]


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
        self.is_buy_or_sell: IsBuyOrSellType = {}
        self.orders: OrdersBTType = {"BUY": {}, "SELL": {}}
        self.trades: Dict[str, List[TradeType]] = {}
        for pair in pairs:
            self._reset_instrument_order("BUY", pair)
            self._reset_instrument_order("SELL", pair)
            self.trades[pair] = []

    def _reset_instrument_order(
        self, type: OperationType, instrument: str
    ) -> None:
        self.orders[type][instrument] = {
            "MK": EmptyBTOrder(),
            "SL": EmptyBTOrder(),
            "TK": EmptyBTOrder(),
            "entry_time": "",
            "exit_time": ""
        }

    def has_buyed(self, pair: str) -> bool:
        if pair not in self.is_buy_or_sell:
            return False
        return True if self.is_buy_or_sell[pair] == "BUY" else False

    def has_selled(self, pair: str) -> bool:
        if pair not in self.is_buy_or_sell:
            return False
        return True if self.is_buy_or_sell[pair] == "SELL" else False

    def manage_order(
        self, order: Order, size: float, timestamp: str, last_close: float
    ) -> str:
        pair: str = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        if pair not in self.is_buy_or_sell:
            return ""
        op_type: OperationType = self.is_buy_or_sell[pair]

        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.orders[op_type][pair]["MK"] = order
            self.orders[op_type][pair]["entry_time"] = timestamp
            self.is_buy_or_sell[pair] = op_type
            if op_type == "BUY":
                return self.messages.buy_order_placed(
                    round(size, 2), pair, order.executed.price
                )
            elif op_type == "SELL":
                return self.messages.sell_order_placed(
                    round(size, 2), pair, order.executed.price
                )

        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.orders[op_type][pair]["SL"] = order
            return ""

        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.orders[op_type][pair]["TK"] = order
            return ""

        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            self.orders[op_type][pair]["SL"] = order
            loss = size * -1
            self.broker.set_cash(self.broker.get_cash() + loss)
            self.orders[op_type][pair]["exit_time"] = timestamp
            self._store_trade(op_type, "SL", pair, loss)
            self._reset_instrument_order(op_type, pair)
            self.is_buy_or_sell.pop(pair, None)
            if op_type == "BUY":
                return self.messages.stop_buy_order(pair, abs(loss))
            elif op_type == "SELL":
                return self.messages.stop_sell_order(pair, abs(loss))

        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            self.orders[op_type][pair]["TK"] = order
            profit = size * self.p_r_ratio
            self.broker.set_cash(self.broker.get_cash() + profit)
            self.orders[op_type][pair]["exit_time"] = timestamp
            self._store_trade(op_type, "TK", pair, profit)
            self._reset_instrument_order(op_type, pair)
            self.is_buy_or_sell.pop(pair, None)
            if op_type == "BUY":
                return self.messages.limit_buy_order(pair, profit)
            elif op_type == "SELL":
                return self.messages.limit_sell_order(pair, profit)

        # Order expired
        elif status == "Expired":
            if self.orders[op_type][pair]["MK"].size == 0:
                return ""
            open = self.orders[op_type][pair]["MK"].executed.price
            if last_close >= open:
                tk = self.orders[op_type][pair]["TK"].price
                if op_type == "BUY":
                    pl = (last_close - open) / (tk - open) \
                        * size * self.p_r_ratio
                elif op_type == "SELL":
                    pl = (open - last_close) / (open - tk) \
                        * size * self.p_r_ratio
            else:
                sl = self.orders[op_type][pair]["SL"].price
                if op_type == "BUY":
                    pl = (open - last_close) / (open - sl) * (size * -1)
                elif op_type == "SELL":
                    pl = (last_close - open) / (sl - open) * size * -1
            self.broker.set_cash(self.broker.get_cash() + pl)
            self.orders[op_type][pair]["exit_time"] = timestamp
            self._store_trade(op_type, "CANCEL", pair, pl, last_close)
            self._reset_instrument_order(op_type, pair)
            self.is_buy_or_sell.pop(pair, None)
            if op_type == "BUY":
                return self.messages.buy_order_canceled(pair, pl)
            elif op_type == "SELL":
                return self.messages.sell_order_canceled(pair, pl)
        return ""

    def _store_trade(
        self, op_type: OperationType,
        order_type: Literal["TK", "SL", "CANCEL"],
        pair: str,
        pl: float,
        exit_price: Optional[float] = None
    ) -> None:
        main_order = self.orders[op_type][pair]

        if exit_price is None:
            exit_price = main_order[order_type].executed.price  # type: ignore
        try:
            entry_price = main_order["MK"].executed.price
        except Exception:
            entry_price = exit_price
        sl_price = main_order["SL"].created.price
        tk_price = main_order["TK"].created.price
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
            "Exit price": round(exit_price, 5),
            "SL": round(sl_price, 5),
            "SL (pips)": round(sl_pips, 2),
            "TK": round(tk_price, 5),
            "TK (pips)": round(tk_pips, 2),
            "Canceled": True if order_type == "CANCEL" else False,
            "PL": round(pl, 2)
        })
