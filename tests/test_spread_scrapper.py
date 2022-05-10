from utils.spread_scrapper import SpreadScrapper


def test_spread_scrapper():
    spread_scrapper = SpreadScrapper()
    assert isinstance(spread_scrapper.get_spread("AUDCAD"), float)
    assert isinstance(spread_scrapper.get_spread("BTCUSD"), float)
