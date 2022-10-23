# Libraries
from datetime import datetime
import re
from typing import Optional

# Packages
import requests

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.types.order import OperationType
from oandatradingbot.types.api_transaction import ApiTransactionType
from oandatradingbot.utils.transaction_manager import TransactionManager
from oandatradingbot.utils.telegram_bot import TelegramBot


REJECTED_REASONS = [
    "STOP_LOSS_ON_FILL_LOSS",
    "TAKE_PROFIT_ON_FILL_LOSS",
    "INSUFFICIENT_LIQUIDITY"
]
CANCEL_REASONS = ["MARKET_ORDER_POSITION_CLOSEOUT", "MARKET_ORDER_TRADE_CLOSE"]


class OrderManager(TransactionManager):
    def __init__(
        self, config: ConfigType, telegram_bot: Optional[TelegramBot] = None
    ) -> None:
        super().__init__(config, telegram_bot)
        # Initialize dictionaries
        for pair in config["pairs"]:
            self.is_buyed_selled["BUY"][pair] = False
            self.is_buyed_selled["SELL"][pair] = False
            self._reset_instrument_order("BUY", pair)
            self._reset_instrument_order("SELL", pair)
        # Check for pending orders
        self.recover_orders()

    def _get_order(self, id: int) -> ApiTransactionType:
        url = self.instrument_manager.url
        account_id = self.instrument_manager.account_id
        token = self.instrument_manager.token

        response = requests.get(
            f"{url}/v3/accounts/{account_id}/transactions/{id}",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        transaction: ApiTransactionType = response.json()["transaction"]
        return transaction

    def has_buyed(self, pair: str) -> bool:
        return self.is_buyed_selled["BUY"][pair]

    def has_selled(self, pair: str) -> bool:
        return self.is_buyed_selled["SELL"][pair]

    def recover_orders(self) -> int:
        url = self.instrument_manager.url
        account_id = self.instrument_manager.account_id
        token = self.instrument_manager.token
        time_pattern = r"\d{4}-\d{2}-\d{2}[T]\d{2}:\d{2}:\d{2}[.]\d{6}"

        response = requests.get(
            f"{url}/v3/accounts/{account_id}/pendingOrders",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {token}"
            },
        )
        orders = response.json()["orders"]

        if len(orders) == 0:
            print("There is no pending orders")
            return 0

        for order in orders:
            # Get main market order
            main_order = self._get_order(order["tradeID"])
            entry_time = re.match(  # type: ignore
                time_pattern, main_order["time"]
            ).group()
            # Transform time string to timestamp
            main_order["time"] = str(datetime.strptime(
                entry_time, "%Y-%m-%dT%H:%M:%S.%f"
            ).timestamp())

            # Register market order
            if main_order["reason"] == "MARKET_ORDER" \
                and main_order["type"] == "ORDER_FILL" \
                    and main_order["id"] not in self.trades_registry:

                pair = main_order["instrument"]
                operation_type: OperationType = "BUY" \
                    if float(main_order["units"]) > 0 else "SELL"
                # Register buy or sell order
                self.trades_registry[main_order["id"]] = {
                    "pair": pair, "op_type": operation_type
                }
                if pair not in self.orders[operation_type]:
                    self._reset_instrument_order(operation_type, pair)
                self.orders[operation_type][pair]["MK"] = main_order
                self.is_buyed_selled[operation_type][pair] = True
                print(f"{operation_type} order {pair} recovered")

            # Register stop loss
            full_order = self._get_order(order["id"])
            if full_order["type"] == "STOP_LOSS_ORDER" \
                and full_order["reason"] == "ON_FILL" \
                    and full_order["tradeID"] == main_order["id"]:
                pair = self.trades_registry[full_order["tradeID"]]["pair"]
                op_type = self.trades_registry[
                    full_order["tradeID"]]["op_type"]
                self.orders[op_type][pair]["SL"] = full_order

            # Register take profit
            full_order = self._get_order(order["id"])
            if full_order["type"] == "TAKE_PROFIT_ORDER" \
                and full_order["reason"] == "ON_FILL" \
                    and full_order["tradeID"] == main_order["id"]:
                pair = self.trades_registry[full_order["tradeID"]]["pair"]
                op_type = self.trades_registry[
                    full_order["tradeID"]]["op_type"]
                self.orders[op_type][pair]["TK"] = full_order

        return len(orders)

    def cancel_pending_trades(self) -> None:
        url = self.instrument_manager.url
        account_id = self.instrument_manager.account_id
        token = self.instrument_manager.token

        response = requests.get(
            f"{url}/v3/accounts/{account_id}/trades",
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {token}"
            },
        )
        trades = response.json()["trades"]

        if len(trades) == 0:
            print("There is no pending trades")
            return

        for trade in trades:
            trade_id = trade["id"]
            instrument = trade["instrument"]
            response = requests.put(
                f"{url}/v3/accounts/{account_id}/trades/{trade_id}/close",
                headers={
                    "content-type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
            )
            if response.status_code == 200:
                print(f"Closing trade {instrument} with id {trade_id}")

    def manage_transaction(self, transaction: ApiTransactionType) -> str:
        # Submit market order
        if transaction["type"] == "MARKET_ORDER" \
                and transaction["reason"] == "CLIENT_ORDER":
            return self.market_order_submitted(transaction)

        # Market order rejected (stop loss on fill loss)
        elif transaction["type"] == "ORDER_CANCEL" \
                and transaction["reason"] in REJECTED_REASONS:
            return self.market_order_rejected(transaction)

        # Register market order
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "MARKET_ORDER":
            return self.register_market_order(transaction)

        # Register take profit order
        elif transaction["type"] == "TAKE_PROFIT_ORDER" \
                and transaction["reason"] == "ON_FILL":
            return self.register_take_profit_order(transaction)

        # Replace take profit order
        elif transaction["type"] == "TAKE_PROFIT_ORDER" \
                and transaction["reason"] == "REPLACEMENT":
            return self.replace_take_profit_order(transaction)

        # Register stop loss order
        elif transaction["type"] == "STOP_LOSS_ORDER" \
                and transaction["reason"] == "ON_FILL":
            return self.register_stop_loss_order(transaction)

        # Replace stop loss order
        elif transaction["type"] == "STOP_LOSS_ORDER" \
                and transaction["reason"] == "REPLACEMENT":
            return self.replace_stop_loss_order(transaction)

        # Limit order completed
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "TAKE_PROFIT_ORDER":
            return self.take_profit_order_completed(transaction)

        # Stop order completed
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] == "STOP_LOSS_ORDER":
            return self.stop_loss_order_completed(transaction)

        # Market order canceled
        elif transaction["type"] == "ORDER_FILL" \
                and transaction["reason"] in CANCEL_REASONS:
            return self.market_order_canceled(transaction)

        else:
            return ""
