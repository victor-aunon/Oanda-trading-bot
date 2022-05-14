# Libraries
import os
from datetime import datetime

# Packages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from dbmodels.trade import Base
from utils.instrument_manager import InstrumentManager
from utils.messages import Messages
from utils.order_manager import OrderManager
from utils.tts import TTS

current_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    "oanda_token": os.environ["oanda_token"],
    "oanda_account_id": os.environ["oanda_account_id"],
    "practice": True,
    "pairs": ["EUR_NZD"],
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
    def dict(self) -> dict:
        return {
            "type": self.type,
            "reason": self.reason,
            "tradeID": self.trade_id,
            "orderID": self.trade_id,
            "id": self.trade_id,
            "tradesClosed": [{"tradeID": self.trade_id}],
            "units": self.units,
            "price": "1.1515",
            "instrument": config["pairs"][0],
            "pl": "20.50",
            "time": str(datetime.now().timestamp())
        }


def create_session():
    engine = create_engine(
        f"sqlite:///{os.path.join(current_dir, 'test.db')}", echo=True
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def test_buy_order_rejected():
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

    # Testing order submitted and rejected: stop loss on fill loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "1", "4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction(
        "STOP_LOSS_ON_FILL_LOSS", "ORDER_CANCEL", "1", "4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)


def test_buy_order_stop_loss():
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))


def test_sell_order_rejected():
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

    # Testing order submitted and rejected: stop loss on fill loss
    trans = Transaction("MARKET_ORDER", "CLIENT_ORDER", "8", "-4000").dict
    assert isinstance(om.manage_transaction(trans), str)
    trans = Transaction(
        "STOP_LOSS_ON_FILL_LOSS", "ORDER_CANCEL", "8", "-4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)


def test_sell_order_stop_loss():
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

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
        "ORDER_FILL", "MARKET_ORDER_TRADE_CLOSE", "14", "4000"
    ).dict
    assert isinstance(om.manage_transaction(trans), str)
    assert om.has_selled(trans["instrument"]) is False


def test_other_order():
    messages = Messages("EN-US", "EUR")
    tts = TTS("EN-US")
    session = create_session()
    im = InstrumentManager(config)
    om = OrderManager(messages, session, im, "Demo", config["pairs"], tts)

    # Skipping some other type/reason
    trans = Transaction("OTHER_TYPE", "OTHER_REASON", "99", "4000").dict
    assert om.manage_transaction(trans) == ""

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
