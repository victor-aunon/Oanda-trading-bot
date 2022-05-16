# Libraries
from datetime import datetime, timedelta
import os

# Packages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from oandatradingbot.dbmodels.trade import Trade, Base
from oandatradingbot.utils.telegram_bot import TelegramBot

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
    entry_time=datetime.utcnow() + timedelta(days=1),
    exit_time=datetime.utcnow() + timedelta(days=1, minutes=45),
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
    entry_time=datetime.utcnow() + timedelta(days=1),
    exit_time=datetime.utcnow() + timedelta(days=1, minutes=45),
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


def create_session():
    engine = create_engine(
        f"sqlite:///{os.path.join(current_dir, 'test.db')}", echo=True
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def test_check_telegram_bot():

    session = create_session()

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        session
    )
    assert tb.check_bot().status_code == 200
    assert tb._notify("Testing").status_code == 200


def test_notify_trade():

    session = create_session()

    session.add(trade1)
    session.commit()

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        session,
        "GBP",
        "Trade"
    )

    assert tb.notify_trade(trade1.id).status_code == 200

    session.close()

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))


def test_daily_report():

    session = create_session()

    session.add(trade1)
    session.add(trade2)
    session.commit()

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        session,
        "EUR",
        "Daily"
    )

    assert tb.daily_report().status_code == 200

    session.close()

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))


def test_weekly_report():

    session = create_session()

    session.add(trade1)
    session.add(trade2)
    session.add(trade3)
    session.add(trade4)
    session.commit()

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        session,
        "CHF"
    )

    assert tb.weekly_report().status_code == 200

    session.close()

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
