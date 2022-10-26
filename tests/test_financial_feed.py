# Packages
import pytest

# Locals
from oandatradingbot.utils.financial_feed import FinancialFeed, INTERVALS


# def test_invalid_instrument():
#     with pytest.raises(SystemExit):
#         FinancialFeed("gold")


def test_invalid_interval():
    with pytest.raises(SystemExit):
        FinancialFeed("EUR_USD", "1s")


@pytest.mark.parametrize("interval", INTERVALS)
def test_valid_instrument_and_interval(interval):
    feed = FinancialFeed("EUR_USD", interval).get_feed()
    assert feed.size > 0
    feed = FinancialFeed("BTC_USD", interval).get_feed()
    assert feed.size > 0
