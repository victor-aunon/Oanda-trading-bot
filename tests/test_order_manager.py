# Libraries
import os

# Packages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Local
from dbmodels.trade import Base
from utils.cash_manager import CashManager
from utils.messages import Messages
from utils.order_manager import OrderManager
from utils.tts import TTS

current_dir = os.path.dirname(os.path.abspath(__file__))


# Simulating the structure of an order
class Data:
    def __init__(self) -> None:
        self._name = "EURUSD"


class Created:
    def __init__(self) -> None:
        self.price = 1.04


class Executed:
    def __init__(self) -> None:
        self.price = 1.05


class Order:
    def __init__(self, status, name) -> None:
        self.status = status
        self.name = name
        self.size = 10000
        self.data = Data()
        self.created = Created()
        self.executed = Executed()

    def getstatusname(self):
        return self.status

    def getordername(self):
        return self.name


def create_session():
    engine = create_engine(
        f"sqlite:///{os.path.join(current_dir, 'test.db')}", echo=True
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def test_order_manager_buy_order():
    messages = Messages("EN-US", "EUR")
    tts = TTS()
    session = create_session()
    om = OrderManager(messages, session, "Demo", tts)
    cm = CashManager(0.01, "USD", "EUR")
    datetime = "2022-05-05 13:47:00"

    # Testing exiting by stop loss
    order = Order("Completed", "Market")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Accepted", "Stop")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Accepted", "Limit")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Completed", "Stop")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)

    # Testing exiting by take profit
    order = Order("Completed", "Market")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Accepted", "Stop")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Accepted", "Limit")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Completed", "Limit")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)

    # Testing market order canceled
    order = Order("Completed", "Market")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)
    order = Order("Canceled", "Market")
    assert isinstance(om.manage_buy_order(order, cm, datetime), str)


def test_order_manager_sell_order():
    messages = Messages("EN-US", "EUR")
    tts = TTS()
    session = create_session()
    om = OrderManager(messages, session, "Demo", tts)
    cm = CashManager(0.01, "USD", "EUR")
    datetime = "2022-05-05 13:47:00"

    # Testing exiting by stop loss
    order = Order("Completed", "Market")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Accepted", "Stop")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Accepted", "Limit")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Completed", "Stop")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)

    # Testing exiting by take profit
    order = Order("Completed", "Market")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Accepted", "Stop")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Accepted", "Limit")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Completed", "Limit")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)

    # Testing market order canceled
    order = Order("Completed", "Market")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)
    order = Order("Canceled", "Market")
    assert isinstance(om.manage_sell_order(order, cm, datetime), str)

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
