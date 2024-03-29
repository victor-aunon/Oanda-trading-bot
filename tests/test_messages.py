# Packages
import pytest

# Locals
from oandatradingbot.utils.messages import Messages


@pytest.mark.parametrize("language", ["EN-US", "ES-ES"])
def test_messages(language):
    messages = Messages(language, "EUR")
    size = 10000
    inst = "EUR_CAD"
    price = 1.05
    amount = 10.50
    assert isinstance(messages.near_buy_signal(inst), str)
    assert isinstance(messages.near_sell_signal(inst), str)
    assert isinstance(messages.buy_order_submitted(size, inst, "1"), str)
    assert isinstance(messages.sell_order_submitted(size, inst, "1"), str)
    assert isinstance(messages.buy_order_rejected(inst, "1"), str)
    assert isinstance(messages.sell_order_rejected(inst, "1"), str)
    assert isinstance(messages.buy_order_placed(size, inst, price, "1"), str)
    assert isinstance(messages.sell_order_placed(size, inst, price, "1"), str)
    assert isinstance(messages.limit_buy_order(inst, amount, "1"), str)
    assert isinstance(messages.limit_sell_order(inst, amount, "1"), str)
    assert isinstance(messages.stop_buy_order(inst, amount, "1"), str)
    assert isinstance(messages.stop_sell_order(inst, amount, "1"), str)
    assert isinstance(messages.stop_order_accepted(inst, "1"), str)
    assert isinstance(messages.stop_order_replaced(inst, "1"), str)
    assert isinstance(messages.limit_order_accepted(inst, "1"), str)
    assert isinstance(messages.limit_order_replaced(inst, "1"), str)
    assert isinstance(messages.buy_order_canceled(inst, amount, "1"), str)
    assert isinstance(messages.sell_order_canceled(inst, amount, "1"), str)
