# Libraries
import os
from datetime import datetime, timedelta

# Packages
import backtrader
import pytest

# Local
from oandatradingbot.types.config import ConfigType
from oandatradingbot.types.trade import TradeDbType
from oandatradingbot.oandabot import main

current_dir = os.path.dirname(os.path.abspath(__file__))

trade1: TradeDbType = {
    "id": 1,
    "instrument": "EUR_USD",
    "account": "Demo",
    "entry_time": datetime(2022, 10, 4, 11, 30),
    "exit_time": datetime(2022, 10, 4, 11, 30) + timedelta(minutes=15),
    "duration": 15 * 60,
    "operation": "BUY",
    "size": 5000.0,
    "entry_price": 1.15,
    "exit_price": 1.16,
    "trade_pips": (1.16 - 1.15) * 1e5,
    "stop_loss": 1.14,
    "take_profit": 1.16,
    "canceled": False,
    "profit": 25.50,
}

config: ConfigType = {
    "database_uri": f"sqlite:///{os.path.join(current_dir, 'test_oanda.db')}",
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "timeframe": "Minutes",
    "timeframe_num": 1,
    "interval": "1m",
    "pairs": ["EUR_NZD"],
    "risk": 0.0001,
    "account_currency": "EUR",
    "language": "EN-US",
    "tts": True,
    "language_tts": "EN-US",
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

    with pytest.raises(backtrader.errors.StrategySkipError):
        print(config["database_uri"])
        main(
            config,
            True
        )

    # Delete db
    os.remove(os.path.join(current_dir, 'test_oanda.db'))
