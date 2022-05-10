
class Messages:
    def __init__(self, language: str, account_currency: str) -> None:
        self.lang = language
        self.currency = account_currency

    def near_buy_signal(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"{pair} cerca de señal de COMPRA"
        elif self.lang == "EN-US":
            response = f"{pair} near BUY signal"
        return response

    def buy_order_placed(self, size: int, pair: str, price: float) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de COMPRA {size} {pair} a {price:.4f}"
        elif self.lang == "EN-US":
            response = f"BUY order {size} {pair} at {price:.4f}"
        return response

    def buy_order_canceled(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de COMPRA {pair} cancelada"
        elif self.lang == "EN-US":
            response = f"BUY order {pair} canceled"
        return response

    def stop_buy_order(self, pair: str, amount: float) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {pair} completada por LÍMITE de PÉRDIDAS. "
                f"{amount} {self.currency} perdidos"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {pair} completed by STOP LOSS. "
                f"{amount} {self.currency} lost"
            )
        return response

    def limit_buy_order(self, pair: str, amount: float) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {pair} completada por RECOGIDA de "
                f"BENEFICIOS. {amount} {self.currency} ganados"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {pair} completed by TAKE PROFIT. "
                f"{amount} {self.currency} earned"
            )
        return response

    def near_sell_signal(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"{pair} cerca de señal de VENTA"
        elif self.lang == "EN-US":
            response = f"{pair} near SELL signal"
        return response

    def sell_order_placed(self, size: int, pair: str, price: float) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de VENTA {abs(size)} {pair} a {price:.4f}"
        elif self.lang == "EN-US":
            response = f"SELL order {abs(size)} {pair} at {price:.4f}"
        return response

    def sell_order_canceled(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de VENTA {pair} cancelada"
        elif self.lang == "EN-US":
            response = f"SELL order {pair} canceled"
        return response

    def stop_sell_order(self, pair: str, amount: float) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {pair} completada por LÍMITE de PÉRDIDAS. "
                f"{amount} {self.currency} perdidos"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {pair} completed by STOP LOSS. "
                f"{amount} {self.currency} lost"
            )
        return response

    def limit_sell_order(self, pair: str, amount: float) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {pair} completada por RECOGIDA de "
                f"BENEFICIOS. {amount} {self.currency} ganados"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {pair} completed by TAKE PROFIT. "
                f"{amount} {self.currency} earned"
            )
        return response

    def stop_order_accepted(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de STOP {pair} aceptada"
        elif self.lang == "EN-US":
            response = f"STOP order{pair} accepted"
        return response

    def limit_order_accepted(self, pair: str) -> str:
        if self.lang == "ES-ES":
            response = f"Orden de LÍMITE {pair} aceptada"
        elif self.lang == "EN-US":
            response = f"LIMIT order{pair} accepted"
        return response
