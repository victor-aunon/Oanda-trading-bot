# Libraries
from datetime import datetime
from typing import Dict, Literal, TypedDict

TradeRegistryValuesType = TypedDict(
    "TradeRegistryValuesType",
    {
        "instrument": str,
        "op_type": Literal["BUY", "SELL"]
    }
)

TradeRegistryType = Dict[str, TradeRegistryValuesType]

TradeDbType = TypedDict(
    "TradeDbType",
    {
        "id": int,
        "instrument": str,
        "account": Literal["Demo", "Brokerage"],
        "entry_time": datetime,
        "exit_time": datetime,
        "duration": int,
        "operation": Literal["SELL", "BUY"],
        "size": float,
        "entry_price": float,
        "exit_price": float,
        "trade_pips": float,
        "stop_loss": float,
        "take_profit": float,
        "canceled": bool,
        "profit": float,
    },
)

TradeType = TypedDict(
    "TradeType",
    {
        "Entry": str,
        "Exit": str,
        "Operation": str,
        "Entry price": float,
        "Exit price": float,  # type: ignore
        "SL": float,
        "SL (pips)": float,
        "TK": float,
        "TK (pips)": float,
        "Canceled": bool,
        "PL": float,
    },
)
