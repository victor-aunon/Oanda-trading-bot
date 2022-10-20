# Libraries
from datetime import datetime, timedelta

# Locals
from oandatradingbot.types.trade import TradeDbType

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
