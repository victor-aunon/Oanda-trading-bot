import pytest

from utils.messages import Messages


@pytest.mark.parametrize("language", ["EN-US", "ES-ES"])
def test_messages(language):
    messages = Messages(language, "EUR")
    size = 10000
    pair = "EURCAD"
    price = 1.05
    amount = 10.50
    assert isinstance(messages.near_buy_signal(pair), str)
    assert isinstance(messages.near_sell_signal(pair), str)
    assert isinstance(messages.buy_order_placed(size, pair, price), str)
    assert isinstance(messages.sell_order_placed(size, pair, price), str)
    assert isinstance(messages.limit_buy_order(pair, amount), str)
    assert isinstance(messages.limit_sell_order(pair, amount), str)
    assert isinstance(messages.stop_buy_order(pair, amount), str)
    assert isinstance(messages.stop_sell_order(pair, amount), str)
    assert isinstance(messages.buy_order_canceled(pair), str)
    assert isinstance(messages.sell_order_canceled(pair), str)
    assert isinstance(messages.stop_order_accepted(pair), str)
    assert isinstance(messages.limit_order_accepted(pair), str)
