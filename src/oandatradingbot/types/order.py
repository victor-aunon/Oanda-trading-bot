# Libraries
from typing import Dict, Literal, TypedDict, Union

# Packages
from backtrader import Order

# Locals
from oandatradingbot.types.api_transaction import ApiTransactionType

OperationType = Literal["BUY", "SELL"]

OrderType = TypedDict(
    "OrderType",
    {
        "MK": ApiTransactionType,
        "TK": ApiTransactionType,
        "SL": ApiTransactionType,
        "CANCEL": ApiTransactionType
    }
)

OrdersType = TypedDict(
    "OrdersType",
    {
        "BUY": Dict[str, OrderType],
        "SELL": Dict[str, OrderType]
    }
)


class EmptyBTExecuted:
    price = 0.0


class EmptyBTCreated:
    price = 0.0


class EmptyBTOrder:
    size = 0.0
    price = 0.0
    executed = EmptyBTExecuted()
    created = EmptyBTCreated()


OrderBTType = TypedDict(
    "OrderBTType",
    {
        "MK": Union[Order, EmptyBTOrder],
        "TK": Union[Order, EmptyBTOrder],
        "SL": Union[Order, EmptyBTOrder],
        "entry_time": str,
        "exit_time": str
    }
)

OrdersBTType = TypedDict(
    "OrdersBTType",
    {
        "BUY": Dict[str, OrderBTType],
        "SELL": Dict[str, OrderBTType]
    }
)
