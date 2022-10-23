from typing import Dict, List
from typing_extensions import TypedDict


ApiTransactionType = TypedDict(
    "ApiTransactionType",
    {
        "type": str,
        "reason": str,
        "tradeID": str,
        "orderID": str,
        "id": str,
        "tradesClosed": List[Dict[str, str]],
        "units": str,
        "price": str,
        "instrument": str,
        "pl": str,
        "time": str,
    },
)

empty_transaction: ApiTransactionType = {
    "type": "",
    "reason": "",
    "tradeID": "",
    "orderID": "",
    "id": "",
    "tradesClosed": [{"none": ""}],
    "units": "",
    "price": "",
    "instrument": "",
    "pl": "",
    "time": "",
}
