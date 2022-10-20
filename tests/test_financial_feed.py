# Packages
import pytest

# Locals
from oandatradingbot.utils.financial_feed import FinancialFeed, INTERVALS


def test_invalid_instrument_should_raise_system_exit():
    with pytest.raises(SystemExit):
        FinancialFeed("gold").get_feed()


def test_invalid_interval_should_raise_system_exit():
    with pytest.raises(SystemExit):
        FinancialFeed("EUR_USD", "1s").get_feed()


@pytest.mark.parametrize("interval", INTERVALS)
def test_valid_instrument_and_interval_should_return_complete_feed(interval):
    feed = FinancialFeed("EUR_USD", interval).get_feed()
    assert feed.size > 0
    feed = FinancialFeed("BTC_USD", interval).get_feed()
    assert feed.size > 0
