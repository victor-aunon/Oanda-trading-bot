# Libraries
import copy
from datetime import datetime
from typing import Literal
import os

# Packages
import requests

# Locals
from oandatradingbot.repository.repository import Repository
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.financial_feed import INTERVALS
from oandatradingbot.utils.instrument_manager import practice_url, prod_url
from oandatradingbot.utils.telegram_bot import TelegramBot

LANGUAGES = ["EN-US", "ES-ES"]
current_dir = os.path.dirname(os.path.abspath(__file__))


def check_config(
    config: ConfigType,
    mode: Literal["backtest", "optimize", "live"]
) -> ConfigType:

    # Make a deepcopy of config to not alter the original dictionary
    ch_config = copy.deepcopy(config)

    # Check mandatory fields
    if mode != "live" and "results_path" not in config:
        raise SystemExit(
            "ERROR: Change the name of the results_path before backtesting"
        )
    if "instruments" not in config:
        raise SystemExit(
            "ERROR: Define the instruments list in the config file"
        )
    if "timeframes" not in config:
        raise SystemExit("ERROR: Please define timeframes in the config file")
    if len(config["timeframes"]) > 2:
        raise SystemExit(
            "ERROR: timeframes can only contain up to two objects"
        )
    if mode != "live":
        for timeframe in ch_config["timeframes"]:
            if "interval" not in timeframe:
                raise SystemExit(
                    f"ERROR: Please define a timeframe interval in the "
                    f"config file. Valid values are {INTERVALS}"
                )
    if "strategy_params" not in config:
        raise SystemExit(
            "ERROR: Please define the strategy parameters in the config file"
        )
    if "account_currency" not in ch_config:
        raise SystemExit(
            "ERROR: Please define the account currency symbol: EUR, USD, ..."
        )

    # Default database if database_uri is not provided
    if mode == "live" and "database_uri" not in config:
        if "testing" not in config:
            ch_config["testing"] = False

        if ch_config["testing"]:
            db_path = os.path.abspath(
                os.path.join(ch_config["testing_directory"], 'trades.db')
            )
        else:
            db_path = os.path.abspath(
                os.path.join(
                    current_dir, '..', '..', '..', 'trades.db'
                )
            )
        print(
            f"WARNING: database_uri not defined. "
            f"Creating a sqlite database at {db_path}"
        )
        ch_config["database_uri"] = f"sqlite:///{db_path}"

    # Check database connection
    if mode == "live" and "database_uri" in ch_config:
        repository = Repository(ch_config["database_uri"])
        repository._check_session()

    # Check Telegram token and chat id
    if mode == "live":
        if "telegram_token" in config and "telegram_chat_id" not in config:
            raise SystemExit(
                "ERROR: Please define the telegram_chat_id in the config file"
            )
        if "telegram_chat_id" in config and "telegram_token" not in config:
            raise SystemExit(
                "ERROR: Please define the telegram_token in the config file"
            )
        if "telegram_token" in config and "telegram_chat_id" in config:
            telegram_bot = TelegramBot(ch_config)
            if telegram_bot.check_bot().status_code != 200:
                raise SystemExit(
                    "ERROR: Invalid Telegram bot token access. "
                    "Check the config JSON file.",
                )

    # Setting default language if not provided or invalid
    if "language" not in ch_config or ch_config["language"] not in LANGUAGES:
        print("WARNING: Invalid language in config file, switching to EN-US")
        ch_config["language"] = "EN-US"
    if "tts" in config and config["tts"]:
        if "language_tts" not in config \
                or config["language_tts"] not in LANGUAGES:
            print("WARNING: Invalid language_tts, switching to EN-US")
            ch_config["language_tts"] = "EN-US"

    # Manage optimize and testing (internal fields)
    ch_config["optimize"] = True if mode == "optimize" else False
    if "testing" not in config:
        ch_config["testing"] = False

    # Manage account_type (internal field) and check oanda token
    if mode == "live":
        if "practice" not in config:
            ch_config["practice"] = True
        ch_config["account_type"] = \
            "Demo" if ch_config["practice"] else "Brokerage"
        if "oanda_token" not in config and "oanda_account_id" not in config:
            raise SystemExit(
                "ERROR: Please define oanda_token and oanda_account_id "
                "in the config file"
            )
        if "oanda_token" in config and "oanda_account_id" not in config:
            raise SystemExit(
                "ERROR: Please define the oanda_account_id in the config file"
            )
        if "oanda_account_id" in config and "oanda_token" not in config:
            raise SystemExit(
                "ERROR: Please define the oanda_token in the config file"
            )

        # Make a request to Oanda to check token and account id
        check_oanda_account(
            ch_config["practice"],
            ch_config["oanda_token"],
            ch_config["oanda_account_id"]
        )

    # Create results path
    if mode != "live":
        try:
            os.mkdir(ch_config["results_path"])
        except OSError as e:
            if e.errno == 17:
                pass
            else:
                raise SystemExit(e)
    if mode == "optimize":
        ch_config["opt_name"] = (
            "Optimization_"
            f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M')}"
        )
        try:
            os.mkdir(
                os.path.join(config["results_path"], ch_config["opt_name"])
            )
        except OSError as e:
            if e.errno == 17:
                pass
            else:
                raise SystemExit(e)

    # Check there are no repeated instruments
    ch_config["instruments"] = list(set(ch_config["instruments"]))

    # Transform ch_config dictionary
    if mode != "optimize":
        for param in ch_config["strategy_params"]:
            p = ch_config["strategy_params"][param]  # type: ignore
            ch_config[param] = p  # type: ignore
        ch_config.pop("strategy_params", None)

    return ch_config


def check_oanda_account(practice: bool, token: str, account_id: str) -> None:
    url = practice_url if practice else prod_url
    response = requests.get(
        f"{url}/v3/accounts",
        headers={
            "content-type": "application/json",
            "Authorization": f"Bearer {token}"
        },
    )
    if response.status_code != 200:
        raise SystemExit("ERROR: invalid oanda_token")

    accounts = response.json()["accounts"]
    account_found = [
        True if acc["id"] == account_id else False for acc in accounts
    ]
    if True not in account_found:
        raise SystemExit("ERROR: invalid oanda_account_id")

    return
