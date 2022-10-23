# Libraries
from typing import Literal, TypedDict


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
      "BUY": dict[str, OrderType],
      "SELL": dict[str, OrderType]
   }
)
