# Libraries
from datetime import datetime, timedelta
import os

# Packages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from oandatradingbot.dbmodels.trade import Trade, Base

current_dir = os.path.dirname(os.path.abspath(__file__))


def create_session():
    engine = create_engine(
        f"sqlite:///{os.path.join(current_dir, 'test.db')}", echo=True
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def test_create_trade():
    session = create_session()

    trade = Trade(
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

    session.add(trade)
    session.commit()

    trade_db = session.query(Trade).filter(Trade.pair == "EUR_USD").first()
    assert "Trade(id=1, type=BUY" in trade_db.__repr__()
    assert "size=5000.0, profit=25.5)" in trade_db.__repr__()
    assert trade_db.pair == "EUR_USD"

    session.close()


def test_delete_trade():
    session = create_session()

    # Remove the trade created previously
    trade_db = session.query(Trade).filter(Trade.pair == "EUR_USD").first()
    session.delete(trade_db)
    session.commit()

    # Get the deleted trade, it will return None
    trade_db = session.query(Trade).filter(Trade.pair == "EUR_USD").first()
    assert trade_db is None
    session.close()

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
