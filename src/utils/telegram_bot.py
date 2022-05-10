import requests


class TelegramBot:
    base_url = "https://api.telegram.org/bot"

    def __init__(
        self,
        token: str,
        chat_id: str,
        report_freq="Daily",
        report_hour=22
    ) -> None:

        self.token = token
        self.chat_id = chat_id
        self.frequency = report_freq
        self.report_hour = report_hour

    def check_bot(self) -> requests.Response:
        response = requests.post(f"{self.base_url}{self.token}/getMe")
        return response

    def notify(self, text: str) -> requests.Response:
        params = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        response = requests.post(
            f"{self.base_url}{self.token}/sendMessage", params=params
        )
        return response
