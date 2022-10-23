# Libraries
import os
from datetime import datetime

# Packages
import backtrader
import pytest

# Local
from oandatradingbot.repository.repository import Repository
from oandatradingbot.types.config import ConfigType
from oandatradingbot.oandabot import main
from tests.trades import trade1, trade2, trade3, trade4

current_dir = os.path.dirname(os.path.abspath(__file__))

config: ConfigType = {
    "database_uri": f"sqlite:///{os.path.join(current_dir, 'test_oanda.db')}",
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "timeframe": "Minutes",
    "timeframe_num": 1,
    "interval": "1m",
    "instruments": ["EUR_NZD"],
    "risk": 0.0001,
    "account_currency": "EUR",
    "language": "EN-US",
    "tts": True,
    "language_tts": "EN-US",
    "testing": True,
    # testing_date is a Friday so the bot send weekly report and closes
    # pending trades. Time is 00:00 so the test can be run at any hour ->
    # timers will always fire
    "testing_date": datetime(2022, 10, 7, 0, 0, 0),
    "telegram_token": os.environ["telegram_token"],
    "telegram_chat_id": os.environ["telegram_chat_id"],
    "strategy_params": {
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
    repository = Repository(config["database_uri"])

    repository.save_trade(trade1)
    repository.save_trade(trade2)
    repository.save_trade(trade3)
    repository.save_trade(trade4)

    with pytest.raises(backtrader.errors.StrategySkipError):
        main(config)

    # Delete db
    os.remove(os.path.join(current_dir, 'test_oanda.db'))
