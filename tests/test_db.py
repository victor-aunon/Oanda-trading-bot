# Libraries
from datetime import datetime, timedelta
import os

# Packages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from dbmodels.trade import Trade, Base

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
        pair="EURUSD",
        account="Demo",
        entry_time=datetime.utcnow(),
        exit_time=datetime.utcnow() + timedelta(minutes=15),
        duration=15*60,
        operation="BUY",
        open_price=1.15,
        exit_price=1.16,
        spread=1.2,
        trade_pips=(1.16 - 1.15) * 1e5,
        stop_loss=1.14,
        take_profit=1.16,
        canceled=False,
        profit=25.50,
    )

    session.add(trade)
    session.commit()

    trade_db = session.query(Trade).filter(Trade.pair == "EURUSD").first()
    assert trade_db.pair == "EURUSD"
    session.close()


def test_delete_trade():
    session = create_session()

    # Remove the trade created previously
    trade_db = session.query(Trade).filter(Trade.pair == "EURUSD").first()
    session.delete(trade_db)
    session.commit()

    # Get the deleted trade, it will return None
    trade_db = session.query(Trade).filter(Trade.pair == "EURUSD").first()
    assert trade_db is None
    session.close()

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
