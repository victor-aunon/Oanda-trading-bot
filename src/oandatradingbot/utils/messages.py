from typing import Optional


class Messages:
    def __init__(self, language: str, account_currency: str) -> None:
        self.lang = language
        self.currency = account_currency

    def near_buy_signal(self, instrument: str) -> str:
        if self.lang == "ES-ES":
            response = f"{instrument} cerca de señal de COMPRA"
        elif self.lang == "EN-US":
            response = f"{instrument} near BUY signal"
        return response

    def buy_order_submitted(
        self, size: int, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {abs(size)} {instrument}"
                f"{f' con ID {id}' if id is not None else ''} enviada"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {abs(size)} {instrument}"
                f"{f' with ID {id}' if id is not None else ''} submitted"
            )
        return response

    def buy_order_rejected(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {instrument}"
                f"{f' con ID {id}' if id is not None else ''} rechazada"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} rejected"
            )
        return response

    def buy_order_placed(
        self,
        size: float,
        instrument: str,
        price: float,
        id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {abs(size)} {instrument} a {price:.5f}"
                f"{f' con ID {id}' if id is not None else ''} aceptada"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {abs(size)} {instrument} at {price:.5f}"
                f"{f' with ID {id}' if id is not None else ''} accepted"
            )
        return response

    def buy_order_canceled(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {instrument}"
                f"{f' con ID {id}' if id is not None else ''} cancelada. "
                f"{abs(amount):.2f} {self.currency} "
                f"{'ganados' if amount >= 0 else 'perdidos'}"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} canceled. "
                f"{abs(amount):.2f} {self.currency} "
                f"{'earned' if amount >= 0 else 'lost'}"
            )
        return response

    def stop_buy_order(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {instrument}"
                f"{f' con ID {id}' if id is not None else ''}"
                " completada por LÍMITE de PÉRDIDAS. "
                f"{amount:.2f} {self.currency} perdidos"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {instrument}"
                f"{f' with ID {id}' if id is not None else ''}"
                " completed by STOP LOSS. "
                f"{amount:.2f} {self.currency} lost"
            )
        return response

    def limit_buy_order(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de COMPRA {instrument}"
                f"{f' con ID {id}' if id is not None else ''}"
                " completada por RECOGIDA de BENEFICIOS. "
                f"{amount:.2f} {self.currency} ganados"
            )
        elif self.lang == "EN-US":
            response = (
                f"BUY order {instrument}"
                f"{f' with ID {id}' if id is not None else ''}"
                " completed by TAKE PROFIT. "
                f"{amount:.2f} {self.currency} earned"
            )
        return response

    def near_sell_signal(self, instrument: str) -> str:
        if self.lang == "ES-ES":
            response = f"{instrument} cerca de señal de VENTA"
        elif self.lang == "EN-US":
            response = f"{instrument} near SELL signal"
        return response

    def sell_order_submitted(
        self, size: int, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {abs(size)} {instrument}"
                f"{f' con ID {id}' if id is not None else ''} enviada"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {abs(size)} {instrument}"
                f"{f' with ID {id}' if id is not None else ''} submitted"
            )
        return response

    def sell_order_rejected(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {instrument}"
                f"{f' con ID {id}' if id is not None else ''} rechazada"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} rejected"
            )
        return response

    def sell_order_placed(
        self,
        size: float,
        instrument: str,
        price: float,
        id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {abs(size)} {instrument} a {price:.5f}"
                f"{f' con ID {id}' if id is not None else ''} aceptada"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {abs(size)} {instrument} at {price:.5f}"
                f"{f' with ID {id}' if id is not None else ''} accepted"
            )
        return response

    def sell_order_canceled(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {instrument}"
                f"{f' con ID {id} ' if id is not None else ''} cancelada. "
                f"{abs(amount):.2f} {self.currency} "
                f"{'ganados' if amount >= 0 else 'perdidos'}"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {instrument}"
                f"{f' with ID {id} ' if id is not None else ''} canceled. "
                f"{abs(amount):.2f} {self.currency} "
                f"{'earned' if amount >= 0 else 'lost'}"
            )
        return response

    def stop_sell_order(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {instrument}"
                f"{f' con ID {id}' if id is not None else ''}"
                " completada por LÍMITE de PÉRDIDAS. "
                f"{amount:.2f} {self.currency} perdidos"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {instrument}"
                f"{f' with ID {id}' if id is not None else ''}"
                " completed by STOP LOSS. "
                f"{amount:.2f} {self.currency} lost"
            )
        return response

    def limit_sell_order(
        self, instrument: str, amount: float, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de VENTA {instrument}"
                f"{f' con ID {id}' if id is not None else ''}"
                " completada por RECOGIDA de BENEFICIOS. "
                f"{amount:.2f} {self.currency} ganados"
            )
        elif self.lang == "EN-US":
            response = (
                f"SELL order {instrument}"
                f"{f' with ID {id}' if id is not None else ''}"
                " completed by TAKE PROFIT. "
                f"{amount:.2f} {self.currency} earned"
            )
        return response

    def stop_order_accepted(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de STOP {instrument}"
                f"{f' con ID {id}' if id is not None else ''} aceptada"
            )
        elif self.lang == "EN-US":
            response = (
                f"STOP order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} accepted"
            )
        return response

    def stop_order_replaced(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de STOP {instrument}"
                f"{f' con ID {id}' if id is not None else ''} reajustada"
            )
        elif self.lang == "EN-US":
            response = (
                f"STOP order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} replaced"
            )
        return response

    def limit_order_accepted(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de LÍMITE {instrument}"
                f"{f' con ID {id}' if id is not None else ''} aceptada"
            )
        elif self.lang == "EN-US":
            response = (
                f"LIMIT order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} accepted"
            )
        return response

    def limit_order_replaced(
        self, instrument: str, id: Optional[str] = None
    ) -> str:
        if self.lang == "ES-ES":
            response = (
                f"Orden de LÍMITE {instrument}"
                f"{f' con ID {id}' if id is not None else ''} reajustada"
            )
        elif self.lang == "EN-US":
            response = (
                f"LIMIT order {instrument}"
                f"{f' with ID {id}' if id is not None else ''} replaced"
            )
        return response
