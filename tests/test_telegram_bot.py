# Libraries
from datetime import datetime, timedelta
import os

# Local
from oandatradingbot.repository.repository import Repository
from oandatradingbot.types.trade import TradeDbType
from oandatradingbot.utils.telegram_bot import TelegramBot

current_dir = os.path.dirname(os.path.abspath(__file__))
db_uri = f"sqlite:///{os.path.join(current_dir, 'test.db')}"

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

trade2: TradeDbType = {
    "id": 2,
    "instrument": "EUR_USD",
    "account": "Demo",
    "entry_time": datetime(2022, 10, 4, 17, 30),
    "exit_time": datetime(2022, 10, 4, 17, 30) + timedelta(minutes=25),
    "duration": 25 * 60,
    "operation": "BUY",
    "size": 5000.0,
    "entry_price": 1.15,
    "exit_price": 1.16,
    "trade_pips": (1.16 - 1.15) * 1e5,
    "stop_loss": 1.14,
    "take_profit": 1.16,
    "canceled": False,
    "profit": 28.50,
}

trade3: TradeDbType = {
    "id": 3,
    "instrument": "EUR_USD",
    "account": "Demo",
    "entry_time": datetime(2022, 10, 5, 11, 30),
    "exit_time": datetime(2022, 10, 5, 11, 30) + timedelta(minutes=45),
    "duration": 45 * 60,
    "operation": "SELL",
    "size": 5000.0,
    "entry_price": 1.15,
    "exit_price": 1.16,
    "trade_pips": (1.16 - 1.15) * 1e5,
    "stop_loss": 1.14,
    "take_profit": 1.16,
    "canceled": False,
    "profit": 22.50,
}

trade4: TradeDbType = {
    "id": 4,
    "instrument": "EUR_USD",
    "account": "Demo",
    "entry_time": datetime(2022, 10, 10, 11, 30),
    "exit_time": datetime(2022, 10, 10, 11, 30) + timedelta(hours=2),
    "duration": 2 * 60 * 60,
    "operation": "SELL",
    "size": 5000.0,
    "entry_price": 1.15,
    "exit_price": 1.16,
    "trade_pips": (1.16 - 1.15) * 1e5,
    "stop_loss": 1.14,
    "take_profit": 1.16,
    "canceled": False,
    "profit": 30.10,
}


def test_check_telegram_bot():
    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        db_uri
    )
    assert tb.check_bot().status_code == 200
    assert tb._notify("Testing").status_code == 200


def test_notify_trade():
    repository = Repository(db_uri)

    repository.save_trade(trade1)

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        db_uri,
        "GBP",
        "Trade"
    )

    assert tb.notify_trade(1).status_code == 200  # type: ignore [union-attr]


def test_daily_report():
    repository = Repository(db_uri)

    repository.save_trade(trade2)

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        db_uri,
        "EUR",
        "Daily"
    )

    assert tb.daily_report(
        datetime(2022, 10, 4)
    ).status_code == 200  # type: ignore [union-attr]


def test_weekly_report():
    repository = Repository(db_uri)

    repository.save_trade(trade3)
    repository.save_trade(trade4)

    tb = TelegramBot(
        os.environ["telegram_token"],
        os.environ["telegram_chat_id"],
        db_uri,
        "CHF"
    )

    assert tb.weekly_report(
        datetime(2022, 10, 7, 23, 59)
    ).status_code == 200  # type: ignore [union-attr]

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
