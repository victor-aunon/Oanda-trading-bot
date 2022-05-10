import json

import pytest

from utils.telegram_bot import TelegramBot


@pytest.mark.skip()
def test_telegram_bot():

    # Load config json file
    with open("src/tradingbot/config_dev.json", "r") as file:
        config = json.load(file)

    tb = TelegramBot(
        config["telegram_token"],
        config["telegram_chat_id"],
    )
    assert tb.check_bot().status_code == 200
    assert tb.notify("Testing").status_code == 200
