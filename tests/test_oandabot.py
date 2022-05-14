# Libraries
import os

# Packages
import backtrader
import pytest

# Local
from tradingbot.oandabot import main

# current_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "timeframe": "Minutes",
    "timeframe_num": 1,
    "pairs": ["EUR_NZD"],
    "risk": 0.0001,
    "account_currency": "EUR",
    "language": "EN-US",
    "tts": True,
    "strategy_params": {
        "interval": "1m",
        "macd_fast_ema": 5,
        "macd_slow_ema": 26,
        "macd_signal_ema": 8,
        "ema_period": 220,
        "atr_period": 14,
        "atr_distance": 1.1,
        "profit_risk_ratio": 1.5
    }
}


def test_oandabot():

    with pytest.raises(backtrader.errors.StrategySkipError):
        main(config, "sqlite://", True)
