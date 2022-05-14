import pytest

from utils.messages import Messages


@pytest.mark.parametrize("language", ["EN-US", "ES-ES"])
def test_messages(language):
    messages = Messages(language, "EUR")
    size = 10000
    pair = "EUR_CAD"
    price = 1.05
    amount = 10.50
    assert isinstance(messages.near_buy_signal(pair), str)
    assert isinstance(messages.near_sell_signal(pair), str)
    assert isinstance(messages.buy_order_submitted(size, pair, 1), str)
    assert isinstance(messages.sell_order_submitted(size, pair, 1), str)
    assert isinstance(messages.buy_order_rejected(pair, 1), str)
    assert isinstance(messages.sell_order_rejected(pair, 1), str)
    assert isinstance(messages.buy_order_placed(size, pair, price, 1), str)
    assert isinstance(messages.sell_order_placed(size, pair, price, 1), str)
    assert isinstance(messages.limit_buy_order(pair, amount, 1), str)
    assert isinstance(messages.limit_sell_order(pair, amount, 1), str)
    assert isinstance(messages.stop_buy_order(pair, amount, 1), str)
    assert isinstance(messages.stop_sell_order(pair, amount, 1), str)
    assert isinstance(messages.stop_order_accepted(pair, 1), str)
    assert isinstance(messages.stop_order_replaced(pair, 1), str)
    assert isinstance(messages.limit_order_accepted(pair, 1), str)
    assert isinstance(messages.limit_order_replaced(pair, 1), str)
    assert isinstance(messages.buy_order_canceled(pair, amount, 1), str)
    assert isinstance(messages.sell_order_canceled(pair, amount, 1), str)
