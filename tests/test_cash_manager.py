import pytest

from utils.cash_manager import CashManager


@pytest.mark.parametrize(
    "operation_type, to_currency", [("BUY", "EUR"), ("SELL", "JPY")]
)
def test_cash_manager(operation_type, to_currency):
    cm = CashManager(0.01, "CAD", to_currency, "EUR", "1m")
    cash = 50000.0
    pips = 6.5
    timestamp = "2022-05-05 13:47:00"
    open = 1.12
    close = 1.13
    quantity = cm.get_quantity(cash, pips, timestamp)
    assert isinstance(cm.get_quantity(cash, pips, timestamp), int)
    assert isinstance(
        cm.profit(open, close, quantity, operation_type, timestamp), float
    )
    assert isinstance(cm.get_exchange_rate("EUR", "USD", timestamp), float)
