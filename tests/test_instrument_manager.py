# Libraries
import os

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.instrument_manager import InstrumentManager

config: ConfigType = {
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "instruments": ["EUR_NZD"],
}


def test_instrument_manager():
    im = InstrumentManager(config)
    assert isinstance(im.get_units(config["instruments"][0]), float)
    assert isinstance(im.get_ask_price(config["instruments"][0]), float)
    assert isinstance(im.get_bid_price(config["instruments"][0]), float)
