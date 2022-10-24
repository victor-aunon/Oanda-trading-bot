# Libraries
from datetime import datetime
import os

# Packages
import pytest

# Local
from oandatradingbot.repository.repository import Repository
from tests.trades import trade1, trade2, trade3, trade4

current_dir = os.path.dirname(os.path.abspath(__file__))
db_uri = f"sqlite:///{os.path.join(current_dir, 'test.db')}"


def test_raise_exception_when_db_uri_is_invalid():
    with pytest.raises(SystemExit):
        _ = Repository("")


def test_create_trade():
    repository = Repository(db_uri)

    repository.save_trade(trade1)

    trade_db = repository.get_trade(1)

    assert trade_db is not None
    assert trade_db.operation == "BUY"
    assert trade_db.size == 5000.0
    assert trade_db.profit == 25.5
    assert trade_db.instrument == "EUR_USD"


def test_delete_trade():
    repository = Repository(db_uri)

    repository.remove_trade(1)
    # Get the deleted trade, it will return None
    trade_db = repository.get_trade(1)

    assert trade_db is None


def test_delete_trade_no_exists():
    repository = Repository(db_uri)

    repository.remove_trade(4)
    # Get the deleted trade, it will return None
    trade_db = repository.get_trade(4)

    assert trade_db is None


def test_get_day_trades():
    repository = Repository(db_uri)

    repository.save_trade(trade1)
    repository.save_trade(trade2)
    repository.save_trade(trade3)
    repository.save_trade(trade4)

    trades = repository.get_day_trades(datetime(2022, 10, 4, 22, 00))

    # Should return 2 trades
    assert len(trades) == 2


def test_get_week_trades():
    repository = Repository(db_uri)

    trades = repository.get_week_trades(
        datetime(2022, 10, 3), datetime(2022, 10, 7, 23, 59)
    )

    # Should return 3 trades
    assert len(trades) == 3
    # Delete db
    os.remove(os.path.join(current_dir, "test.db"))
