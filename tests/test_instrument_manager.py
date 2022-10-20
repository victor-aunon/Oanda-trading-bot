# Libraries
import os

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.instrument_manager import InstrumentManager

config: ConfigType = {
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "pairs": ["EUR_NZD"],
}


def test_instrument_manager():
    im = InstrumentManager(config)
    assert isinstance(im.get_units(config["pairs"][0]), float)
    assert isinstance(im.get_ask_price(config["pairs"][0]), float)
    assert isinstance(im.get_bid_price(config["pairs"][0]), float)
