# Libraries
import os

# Packages
import pytest

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.config_checker import check_config

current_dir = os.path.dirname(os.path.abspath(__file__))


def test_results_path():
    # No results path and mode is not live
    config: ConfigType = {}
    with pytest.raises(SystemExit):
        check_config(config, "backtest")

    # results path does not exists and mode is not live
    config = {"results_path": "invented/path"}
    with pytest.raises(SystemExit):
        check_config(config, "optimize")


def test_instruments():
    # Instruments not provided
    config: ConfigType = {}
    with pytest.raises(SystemExit):
        check_config(config, "live")


def test_account_currency():
    # account_currency not provided
    config: ConfigType = {
        "instruments": ["EUR_USD"],
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"},
        ]
    }
    with pytest.raises(SystemExit):
        check_config(config, "live")


def test_timeframes():
    # time_frames not provided
    config: ConfigType = {"instruments": ["EUR_USD"]}
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # more than 2 time_frames objects
    config["timeframes"] = [
        {"timeframe": "Days", "compression": 1, },  # type: ignore
        {"timeframe": "Days", "compression": 2, },  # type: ignore
        {"timeframe": "Days", "compression": 3, }  # type: ignore
    ]
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # interval not provided in time_frames and mode is not live
    config["timeframes"] = [
        {"timeframe": "Days", "compression": 1, },  # type: ignore
        {"timeframe": "Days", "compression": 2, },  # type: ignore
    ]
    with pytest.raises(SystemExit):
        check_config(config, "backtest")


def test_database():
    # database uri not provided should create a new sqlite one
    config: ConfigType = {
        "results_path": ".",
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "strategy_params": {
            "macd_fast_ema": 26,
            "macd_slow_ema": 12,
            "macd_signal_ema": 9,
            "ema_period": 200,
            "atr_period": 14,
            "atr_distance": 1.0,
            "profit_risk_ratio": 1.0,
        },
        "oanda_token": os.environ["oanda_token"],
        "oanda_account_id": os.environ["oanda_account_id"],
        "testing": True,
        "testing_directory": current_dir
    }
    path = os.path.abspath(os.path.join(current_dir, "trades.db"))
    db_path = f"sqlite:///{path}"
    db_path_checked = check_config(config, "live")["database_uri"]
    assert db_path_checked.lower() == db_path.lower()
    os.remove(path)

    # database uri provided but wrong
    config["database_uri"] = "fake"
    with pytest.raises(SystemExit):
        check_config(config, "live")


def test_telegram_token_and_chat_id():
    # telegram_chat_id not provided
    config: ConfigType = {
        "results_path": ".",
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "telegram_token": "token"
    }
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # telegram_token not provided
    config.pop("telegram_token")
    config["telegram_chat_id"] = "chat_id"
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # telegram_token not valid
    config["telegram_token"] = "token"
    with pytest.raises(SystemExit):
        check_config(config, "live")


def test_language():
    # Setting language to EN-US if language is not provided
    config: ConfigType = {
        "results_path": ".",
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "strategy_params": {
            "macd_fast_ema": 26,
            "macd_slow_ema": 12,
            "macd_signal_ema": 9,
            "ema_period": 200,
            "atr_period": 14,
            "atr_distance": 1.0,
            "profit_risk_ratio": 1.0,
        },
        "oanda_token": os.environ["oanda_token"],
        "oanda_account_id": os.environ["oanda_account_id"],
        "testing": True,
        "testing_directory": current_dir
    }
    assert check_config(config, "backtest")["language"] == "EN-US"

    # Setting language to EN-US if language is not valid
    config["language"] = "CAT"  # type: ignore
    print(config)
    assert check_config(config, "live")["language"] == "EN-US"

    # Language is valid
    config["language"] = "ES-ES"
    assert check_config(config, "backtest")["language"] == "ES-ES"


def test_language_tts():
    # Setting language to EN-US if language_tts is not provided
    config: ConfigType = {
        "results_path": ".",
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "strategy_params": {
            "macd_fast_ema": 26,
            "macd_slow_ema": 12,
            "macd_signal_ema": 9,
            "ema_period": 200,
            "atr_period": 14,
            "atr_distance": 1.0,
            "profit_risk_ratio": 1.0,
        },
        "tts": True,
        "testing": True,
        "testing_directory": current_dir,
        "oanda_token": os.environ["oanda_token"],
        "oanda_account_id": os.environ["oanda_account_id"],
    }
    assert check_config(config, "live")["language_tts"] == "EN-US"

    # Setting language to EN-US if language_tts is not valid
    config["language_tts"] = "CAT"  # type: ignore
    assert check_config(config, "live")["language_tts"] == "EN-US"

    # Language is valid
    config["language_tts"] = "ES-ES"
    assert check_config(config, "live")["language_tts"] == "ES-ES"


def test_oanda_tokens():
    config: ConfigType = {
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "strategy_params": {
            "macd_fast_ema": 26,
            "macd_slow_ema": 12,
            "macd_signal_ema": 9,
            "ema_period": 200,
            "atr_period": 14,
            "atr_distance": 1.0,
            "profit_risk_ratio": 1.0,
        },
        "language": "ES-ES",
        "telegram_token": os.environ["telegram_token"],
        "telegram_chat_id": os.environ["telegram_chat_id"],
        "testing": True,
        "testing_directory": current_dir
    }

    # Test oanda_token and oanda_account_id not provided
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # Test oanda_token not provided
    config["oanda_account_id"] = os.environ["oanda_account_id"]
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # Test oanda_account_id not provided
    config.pop("oanda_account_id")
    config["oanda_token"] = os.environ["oanda_token"]
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # Test invalid oanda_token
    config["oanda_account_id"] = os.environ["oanda_account_id"]
    config["oanda_token"] = "invalid_token"
    with pytest.raises(SystemExit):
        check_config(config, "live")

    # Test invalid oanda_account_id
    config["oanda_account_id"] = "invalid_account_id"
    config["oanda_token"] = os.environ["oanda_token"]
    with pytest.raises(SystemExit):
        check_config(config, "live")


def test_complete_config():
    config: ConfigType = {
        "instruments": ["EUR_USD"],
        "account_currency": "EUR",
        "timeframes": [
            {"timeframe": "Days", "compression": 1, "interval": "1d"},
            {"timeframe": "Days", "compression": 2, "interval": "1d"}
        ],
        "strategy_params": {
            "macd_fast_ema": 26,
            "macd_slow_ema": 12,
            "macd_signal_ema": 9,
            "ema_period": 200,
            "atr_period": 14,
            "atr_distance": 1.0,
            "profit_risk_ratio": 1.0,
        },
        "tts": True,
        "language": "ES-ES",
        "language_tts": "ES-ES",
        "telegram_token": os.environ["telegram_token"],
        "telegram_chat_id": os.environ["telegram_chat_id"],
        "oanda_token": os.environ["oanda_token"],
        "oanda_account_id": os.environ["oanda_account_id"],
        "testing": True,
        "testing_directory": current_dir
    }

    assert type(check_config(config, "live")) == dict
    path = os.path.abspath(os.path.join(current_dir, "trades.db"))
    os.remove(path)
