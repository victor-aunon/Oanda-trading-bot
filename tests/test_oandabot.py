# Libraries
import os
from datetime import datetime, timedelta


# Packages
import backtrader
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from oandatradingbot.dbmodels.trade import Trade, Base
from oandatradingbot.oandabot import main

current_dir = os.path.dirname(os.path.abspath(__file__))

trade1 = Trade(
    id=1,
    pair="EUR_USD",
    account="Demo",
    entry_time=datetime.utcnow(),
    exit_time=datetime.utcnow() + timedelta(minutes=15),
    duration=15*60,
    operation="BUY",
    size=5000.0,
    entry_price=1.15,
    exit_price=1.16,
    trade_pips=(1.16 - 1.15) * 1e5,
    stop_loss=1.14,
    take_profit=1.16,
    canceled=False,
    profit=25.50,
)

trade2 = Trade(
    id=2,
    pair="EUR_GBP",
    account="Demo",
    entry_time=datetime.utcnow() + timedelta(minutes=30),
    exit_time=datetime.utcnow() + timedelta(minutes=45),
    duration=15*60,
    operation="SELL",
    size=3000.0,
    entry_price=0.84,
    exit_price=0.83,
    trade_pips=(0.84 - 0.83) * 1e5,
    stop_loss=0.841,
    take_profit=0.83,
    canceled=False,
    profit=20.30,
)

trade3 = Trade(
    id=3,
    pair="EUR_CHF",
    account="Demo",
    entry_time=datetime.utcnow() - timedelta(days=1, minutes=45),
    exit_time=datetime.utcnow() - timedelta(days=1),
    duration=15*60,
    operation="BUY",
    size=3000.0,
    entry_price=1.15,
    exit_price=1.16,
    trade_pips=(1.16 - 1.15) * 1e5,
    stop_loss=1.14,
    take_profit=1.16,
    canceled=False,
    profit=27.55,
)

trade4 = Trade(
    id=4,
    pair="EUR_GBP",
    account="Demo",
    entry_time=datetime.utcnow() - timedelta(days=2, minutes=45),
    exit_time=datetime.utcnow() - timedelta(days=2),
    duration=15*60,
    operation="SELL",
    size=3000.0,
    entry_price=0.84,
    exit_price=0.842,
    trade_pips=(0.84 - 0.842) * 1e5,
    stop_loss=0.842,
    take_profit=0.83,
    canceled=False,
    profit=-25.30,
)

config = {
    "database_uri": f"sqlite:///{os.path.join(current_dir, 'test_oanda.db')}",
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
    "language_tts": "EN-US",
    "telegram_token": os.environ["telegram_token"],
    "telegram_chat_id": os.environ["telegram_chat_id"],
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


def create_session():
    engine = create_engine(
        config["database_uri"], echo=True
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def test_oandabot():

    session = create_session()
    session.add(trade1)
    session.add(trade2)
    session.add(trade3)
    session.add(trade4)
    session.commit()
    session.close()

    with pytest.raises(backtrader.errors.StrategySkipError):
        print(config["database_uri"])
        main(
            config,
            True
        )

    # Delete db
    os.remove(os.path.join(current_dir, 'test_oanda.db'))
