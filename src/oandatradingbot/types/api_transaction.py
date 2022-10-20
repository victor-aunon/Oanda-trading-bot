from typing import List
from typing_extensions import TypedDict


ApiTransactionType = TypedDict(
    "ApiTransactionType",
    {
        "type": str,
        "reason": str,
        "tradeID": str,
        "orderID": str,
        "id": str,
        "tradesClosed": List[dict[str, str]],
        "units": str,
        "price": str,
        "instrument": str,
        "pl": str,
        "time": str,
    },
)
