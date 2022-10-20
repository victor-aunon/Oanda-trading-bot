# Libraries
from datetime import datetime
import os

# Local
from oandatradingbot.repository.repository import Repository
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.telegram_bot import TelegramBot
from tests.trades import trade1, trade2, trade3, trade4

current_dir = os.path.dirname(os.path.abspath(__file__))
db_uri = f"sqlite:///{os.path.join(current_dir, 'test.db')}"

config: ConfigType = {
    "telegram_token": os.environ["telegram_token"],
    "telegram_chat_id": os.environ["telegram_chat_id"],
    "database_uri": db_uri,
    "account_currency": "EUR"
}


def test_check_telegram_bot():
    tb = TelegramBot(config)
    assert tb.check_bot().status_code == 200
    assert tb._notify("Testing").status_code == 200


def test_notify_trade():
    repository = Repository(db_uri)

    repository.save_trade(trade1)

    config["telegram_report_frequency"] = "Trade"
    tb = TelegramBot(config)

    assert tb.notify_trade(1).status_code == 200  # type: ignore [union-attr]


def test_daily_report():
    repository = Repository(db_uri)

    repository.save_trade(trade2)

    tb = TelegramBot(config)

    assert tb.daily_report(
        datetime(2022, 10, 4)
    ).status_code == 200  # type: ignore [union-attr]


def test_weekly_report():
    repository = Repository(db_uri)

    repository.save_trade(trade3)
    repository.save_trade(trade4)

    tb = TelegramBot(config)

    assert tb.weekly_report(
        datetime(2022, 10, 7, 23, 59)
    ).status_code == 200  # type: ignore [union-attr]


def test_manage_notifications_should_not_send_reports():
    tb = TelegramBot(config)

    assert tb.manage_notifications(datetime(2022, 10, 5, 22, 0)) == 0


def test_manage_notifications_daily():
    config["telegram_report_frequency"] = "Daily"
    tb = TelegramBot(config)

    assert tb.manage_notifications(datetime(2022, 10, 5, 22, 0)) == 1


def test_manage_notifications_on_week_close():
    tb = TelegramBot(config)

    assert tb.manage_notifications(datetime(2022, 10, 7, 22, 0)) == 2

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
