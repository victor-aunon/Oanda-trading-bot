# Libraries
import os
from datetime import datetime

# Local
from oandatradingbot.types.api_transaction import ApiTransactionType
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.order_manager import OrderManager
from oandatradingbot.utils.telegram_bot import TelegramBot

current_dir = os.path.dirname(os.path.abspath(__file__))

config: ConfigType = {
    "database_uri": f"sqlite:///{os.path.join(current_dir, 'test.db')}",
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "language": "EN-US",
    "instruments": ["EUR_NZD"],
    "account_currency": "EUR",
    "account_type": "Demo",
    "tts": True,
    "telegram_token": os.environ["telegram_token"],
    "telegram_chat_id": os.environ["telegram_chat_id"],
    "telegram_report_frequency": "Trade"
}


# Simulating the structure of the transaction object returned by the API
class Transaction:
    def __init__(
        self, type: str, reason: str, trade_id: str, units: str
    ) -> None:
        self.type = type
        self.reason = reason
        self.trade_id = trade_id
        self.units = units

    @property
    def dict(self) -> ApiTransactionType:
        return {
            "type": self.type,
            "reason": self.reason,
            "tradeID": self.trade_id,
            "orderID": self.trade_id,
            "id": self.trade_id,
            "tradesClosed": [{"tradeID": self.trade_id}],
            "units": self.units,
            "price": "1.1515",
            "instrument": config["instruments"][0],
            "pl": "-20.50" if self.reason == "STOP_LOSS_ORDER" else "20.50",
            "time": str(datetime.now().timestamp())
        }


def test_recover_orders():
    om = OrderManager(config)

    assert om.recover_orders() == 0


def test_buy_order_rejected():
    om = OrderManager(config)

    # Testing order submitted and rejected: stop loss on fill loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "1", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction(
        "ORDER_CANCEL", "TAKE_PROFIT_ON_FILL_LOSS", "1", "4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)


def test_buy_order_stop_loss():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing exiting by stop loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "2", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "3", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "3", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "3", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Replacing stop loss order
    trans = Transaction("STOP_LOSS_ORDER", "REPLACEMENT", "3", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip stop loss order with another tradeID
    trans = Transaction("ORDER_FILL", "STOP_LOSS_ORDER", "99", "-4000").dict
    assert om.manage_transaction(trans) == ""
    # Complete stop loss order
    trans = Transaction("ORDER_FILL", "STOP_LOSS_ORDER", "3", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is False


def test_buy_order_take_profit():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing exiting by take profit
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "4", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "5", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "5", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "5", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Replacing take profit order
    trans = Transaction("TAKE_PROFIT_ORDER", "REPLACEMENT", "5", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip take profit order with another tradeID
    trans = Transaction("ORDER_FILL", "TAKE_PROFIT_ORDER", "99", "-4000").dict
    assert om.manage_transaction(trans) == ""
    # Complete take profit order
    trans = Transaction("ORDER_FILL", "TAKE_PROFIT_ORDER", "5", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is False


def test_cancel_buy_order():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing market order canceled
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "6", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "7", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "7", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "7", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip market order with another tradeID
    trans = Transaction(
        "ORDER_FILL", "MARKET_ORDER_TRADE_CLOSE", "99", "-4000"
    ).dict
    assert om.manage_transaction(trans) == ""
    # Cancel market order
    trans = Transaction(
        "ORDER_FILL", "MARKET_ORDER_TRADE_CLOSE", "7", "-4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_buyed(trans["instrument"]) is False


def test_sell_order_rejected():
    om = OrderManager(config)

    # Testing order submitted and rejected: stop loss on fill loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "8", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction(
        "ORDER_CANCEL", "INSUFFICIENT_LIQUIDITY", "8", "-4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)


def test_sell_order_stop_loss():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing exiting by stop loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "9", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "10", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "10", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "10", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Replacing stop loss order
    trans = Transaction("STOP_LOSS_ORDER", "REPLACEMENT", "10", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip stop loss order with another tradeID
    trans = Transaction("ORDER_FILL", "STOP_LOSS_ORDER", "99", "4000").dict
    assert om.manage_transaction(trans) == ""
    # Complete stop loss order
    trans = Transaction("ORDER_FILL", "STOP_LOSS_ORDER", "10", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is False


def test_sell_order_take_profit():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing exiting by take profit
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "11", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "12", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "12", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "12", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Replacing take profit order
    trans = Transaction("TAKE_PROFIT_ORDER", "REPLACEMENT", "12", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip take profit order with another tradeID
    trans = Transaction("ORDER_FILL", "TAKE_PROFIT_ORDER", "99", "4000").dict
    assert om.manage_transaction(trans) == ""
    # Complete take profit order
    trans = Transaction("ORDER_FILL", "TAKE_PROFIT_ORDER", "12", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is False


def test_cancel_sell_order():
    tb = TelegramBot(config)
    om = OrderManager(config, tb)

    # Testing market order canceled
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "13", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("ORDER_FILL", "MARKET_ORDER", "14", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is True
    trans = Transaction("TAKE_PROFIT_ORDER", "ON_FILL", "14", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction("STOP_LOSS_ORDER", "ON_FILL", "14", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    # Skip market order with another tradeID
    trans = Transaction(
        "ORDER_FILL", "MARKET_ORDER_TRADE_CLOSE", "99", "4000"
    ).dict
    assert om.manage_transaction(trans) == ""
    # Cancel market order
    trans = Transaction(
        "ORDER_FILL", "MARKET_ORDER_POSITION_CLOSEOUT", "14", "4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is False


def test_other_order():
    om = OrderManager(config)

    # Skipping some other type/reason
    trans = Transaction("OTHER_TYPE", "OTHER_REASON", "99", "4000").dict
    assert om.manage_transaction(trans) == ""

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
