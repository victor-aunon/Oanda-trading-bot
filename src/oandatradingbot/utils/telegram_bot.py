# Libraries
from datetime import datetime, timedelta
from typing import Union

# Packages
import requests

# Local
from oandatradingbot.repository.repository import Repository


currency_emoji = {
    "EUR": "💶",
    "GBP": "💷",
    "JPY": "💴"
}


class TelegramBot:
    base_url = "https://api.telegram.org/bot"

    def __init__(
        self,
        token: str,
        chat_id: str,
        db_uri: str,
        account_currency: str = "EUR",
        report_freq: str = "Daily",
        report_hour: int = 22
    ) -> None:

        self.token = token
        self.chat_id = chat_id
        self.repository = Repository(db_uri)
        self.currency = account_currency
        self.report_freq = report_freq
        self.report_hour = report_hour
        self.daily_notification = True
        self.weekly_notification = True

    def check_bot(self) -> requests.Response:
        response = requests.post(f"{self.base_url}{self.token}/getMe")
        return response

    def _format_trade(self, trade_id: int) -> str:
        trade = self.repository.get_trade(trade_id)

        if trade is None:
            return ""

        pl = "Profit" if trade.profit > 0 else "Loss"
        curr_emoji = currency_emoji[self.currency] \
            if self.currency in currency_emoji else "💵"

        msg = (
            f"🔔<b>Trade {trade.id}: {trade.operation} "
            f"{trade.instrument}</b>\n\n"
            f"   Entry: {datetime.strftime(trade.entry_time, '%H:%M:%S')}\n"
            f"   Exit: {datetime.strftime(trade.exit_time, '%H:%M:%S')}\n"
            f"   Size: {trade.size}\n\n"
            f"{curr_emoji} <b>{pl}: {trade.profit} {self.currency}</b>"
        )
        return msg

    def _format_daily_report(self, day: datetime) -> str:
        trades = self.repository.get_day_trades(day)

        if len(trades) == 0:
            return ""
        wins = len([tr for tr in trades if tr.profit >= 0])
        losses = len([tr for tr in trades if tr.profit < 0])
        win_ratio = wins / len(trades)
        total_pl = sum([tr.profit for tr in trades])

        trades_summary = ""
        for trade in trades:
            trades_summary += (
                f"•{trade.instrument} -> {trade.operation}: "
                f"<b>{trade.profit:.2f} {self.currency}</b>\n"
            )
        curr_emoji = currency_emoji[self.currency] \
            if self.currency in currency_emoji else "💵"

        msg = (
            f"📰 <b>Trades {day.date()}</b>\n\n"
            f"{trades_summary}"
            f"\n🎯Wins: {wins}, Losses: {losses}, WR: {win_ratio:.3f}\n"
            f"{curr_emoji} <b>Total profit: {total_pl:.2f} {self.currency}</b>"
        )
        return msg

    def _format_weekly_report(self, friday: datetime) -> str:
        monday = friday - timedelta(days=5)
        monday_start = datetime(monday.year, monday.month, monday.day, 0, 0)

        trades = self.repository.get_week_trades(monday_start, friday)

        if len(trades) == 0:
            return ""

        wins = len([tr for tr in trades if tr.profit >= 0])
        losses = len([tr for tr in trades if tr.profit < 0])
        win_ratio = wins / len(trades)
        total_pl = sum([tr.profit for tr in trades])

        instruments = {}
        for trade in trades:
            if trade.instrument not in instruments:
                instruments[trade.instrument] = {"Trades": 0, "Profit": 0}
            instruments[trade.instrument]["Trades"] += 1
            instruments[trade.instrument]["Profit"] += trade.profit

        trades_summary = ""
        for key, val in instruments.items():
            trades_summary += (
                f"•{key} -> {val['Trades']} trades, "
                f"profit: <b>{val['Profit']:.2f}</b>\n"
            )
        curr_emoji = currency_emoji[self.currency] \
            if self.currency in currency_emoji else "💵"

        msg = (
            f"📅 <b>Trades week {monday_start.date()} - "
            f"{friday.date()}</b>\n\n"
            f"{trades_summary}"
            f"\n🎯 Wins: {wins}, Losses: {losses}, WR: {win_ratio:.3f}\n"
            f"{curr_emoji} <b>Total profit: {total_pl:.2f} {self.currency}</b>"
        )
        return msg

    def notify_trade(self, trade_id: int) -> Union[requests.Response, None]:

        if self.report_freq != "Trade":
            return None
        text = self._format_trade(trade_id)
        if text == "":
            return None
        return self._notify(text)

    def daily_report(self, day: datetime) -> Union[requests.Response, None]:
        if self.report_freq == "Weekly":
            return None
        text = self._format_daily_report(day)
        if text == "":
            return None
        return self._notify(text)

    def weekly_report(self, day: datetime) -> Union[requests.Response, None]:
        text = self._format_weekly_report(day)
        if text == "":
            return None
        return self._notify(text)

    def _notify(self, text: str) -> requests.Response:
        params = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        response = requests.post(
            f"{self.base_url}{self.token}/sendMessage", params=params
        )
        return response
