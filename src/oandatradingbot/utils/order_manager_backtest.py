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
        instruments: List[str],
        profit_risk_ratio: float,
        broker: BackBroker
    ) -> None:
        self.messages = messages_engine
        self.p_r_ratio = profit_risk_ratio
        self.broker = broker
        self.is_buy_or_sell: IsBuyOrSellType = {}
        self.orders: OrdersBTType = {"BUY": {}, "SELL": {}}
        self.trades: Dict[str, List[TradeType]] = {}
        for instrument in instruments:
            self._reset_instrument_order("BUY", instrument)
            self._reset_instrument_order("SELL", instrument)
            self.trades[instrument] = []

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

    def has_buyed(self, instrument: str) -> bool:
        if instrument not in self.is_buy_or_sell:
            return False
        return True if self.is_buy_or_sell[instrument] == "BUY" else False

    def has_selled(self, instrument: str) -> bool:
        if instrument not in self.is_buy_or_sell:
            return False
        return True if self.is_buy_or_sell[instrument] == "SELL" else False

    def manage_order(
        self, order: Order, size: float, timestamp: str, last_close: float
    ) -> str:
        instrument: str = order.data._name
        status = order.getstatusname()
        type_name = order.getordername()
        if instrument not in self.is_buy_or_sell:
            return ""
        op_type: OperationType = self.is_buy_or_sell[instrument]

        # Register market (main) order. Wait till status is completed instead
        # of accepted in order to get the execution price
        if status in ["Completed"] and type_name == "Market":
            self.orders[op_type][instrument]["MK"] = order
            self.orders[op_type][instrument]["entry_time"] = timestamp
            self.is_buy_or_sell[instrument] = op_type
            if op_type == "BUY":
                return self.messages.buy_order_placed(
                    round(size, 2), instrument, order.executed.price
                )
            elif op_type == "SELL":
                return self.messages.sell_order_placed(
                    round(size, 2), instrument, order.executed.price
                )

        # Register stop order
        elif status in ["Accepted"] and type_name == "Stop":
            self.orders[op_type][instrument]["SL"] = order
            return ""

        # Register limit order
        elif status in ["Accepted"] and type_name == "Limit":
            self.orders[op_type][instrument]["TK"] = order
            return ""

        # Stop order completed
        elif status in ["Completed"] and type_name == "Stop":
            self.orders[op_type][instrument]["SL"] = order
            loss = size * -1
            self.broker.set_cash(self.broker.get_cash() + loss)
            self.orders[op_type][instrument]["exit_time"] = timestamp
            self._store_trade(op_type, "SL", instrument, loss)
            self._reset_instrument_order(op_type, instrument)
            self.is_buy_or_sell.pop(instrument, None)
            if op_type == "BUY":
                return self.messages.stop_buy_order(instrument, abs(loss))
            elif op_type == "SELL":
                return self.messages.stop_sell_order(instrument, abs(loss))

        # Limit order completed
        elif status in ["Completed"] and type_name == "Limit":
            self.orders[op_type][instrument]["TK"] = order
            profit = size * self.p_r_ratio
            self.broker.set_cash(self.broker.get_cash() + profit)
            self.orders[op_type][instrument]["exit_time"] = timestamp
            self._store_trade(op_type, "TK", instrument, profit)
            self._reset_instrument_order(op_type, instrument)
            self.is_buy_or_sell.pop(instrument, None)
            if op_type == "BUY":
                return self.messages.limit_buy_order(instrument, profit)
            elif op_type == "SELL":
                return self.messages.limit_sell_order(instrument, profit)

        # Order expired
        elif status == "Expired":
            if self.orders[op_type][instrument]["MK"].size == 0:
                return ""
            open = self.orders[op_type][instrument]["MK"].executed.price
            if last_close >= open:
                tk = self.orders[op_type][instrument]["TK"].price
                if op_type == "BUY":
                    pl = (last_close - open) / (tk - open) \
                        * size * self.p_r_ratio
                elif op_type == "SELL":
                    pl = (open - last_close) / (open - tk) \
                        * size * self.p_r_ratio
            else:
                sl = self.orders[op_type][instrument]["SL"].price
                if op_type == "BUY":
                    pl = (open - last_close) / (open - sl) * (size * -1)
                elif op_type == "SELL":
                    pl = (last_close - open) / (sl - open) * size * -1
            self.broker.set_cash(self.broker.get_cash() + pl)
            self.orders[op_type][instrument]["exit_time"] = timestamp
            self._store_trade(op_type, "CANCEL", instrument, pl, last_close)
            self._reset_instrument_order(op_type, instrument)
            self.is_buy_or_sell.pop(instrument, None)
            if op_type == "BUY":
                return self.messages.buy_order_canceled(instrument, pl)
            elif op_type == "SELL":
                return self.messages.sell_order_canceled(instrument, pl)
        return ""

    def _store_trade(
        self, op_type: OperationType,
        order_type: Literal["TK", "SL", "CANCEL"],
        instrument: str,
        pl: float,
        exit_price: Optional[float] = None
    ) -> None:
        main_order = self.orders[op_type][instrument]

        if exit_price is None:
            exit_price = main_order[order_type].executed.price  # type: ignore
        try:
            entry_price = main_order["MK"].executed.price
        except Exception:
            entry_price = exit_price
        sl_price = main_order["SL"].created.price
        tk_price = main_order["TK"].created.price
        units = PIP_UNITS[instrument.split("_")[1]]
        tk_pips = (tk_price - entry_price) * units if op_type == "BUY" \
            else (entry_price - tk_price) * units
        sl_pips = (entry_price - sl_price) * units if op_type == "BUY" \
            else (sl_price - entry_price) * units

        self.trades[instrument].append({
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
