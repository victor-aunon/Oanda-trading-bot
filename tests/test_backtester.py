# Libraries
import os

# Packages
import pandas as pd

# Locals
from oandatradingbot.backtester.backtester import main
from oandatradingbot.types.config import ConfigType

current_dir = os.path.dirname(os.path.abspath(__file__))

config: ConfigType = {
    "results_path": os.path.join(current_dir, "results"),
    "pairs": ["EUR_USD"],
    "cash": 10000,
    "risk": 1,
    "account_currency": "EUR",
    "language": "EN-US",
    "timeframe_num": 5,
    "timeframe": "Minutes",
    "interval": "5m",
    "strategy_params": {
        "macd_fast_ema": 5,
        "macd_slow_ema": 26,
        "macd_signal_ema": 8,
        "ema_period": 200,
        "atr_period": 14,
        "atr_distance": 1.5,
        "profit_risk_ratio": 1.5
    }
}


def test_backtester():

    main(config, testing=True)
    for file in os.listdir(os.path.join(current_dir, "results")):
        if file.endswith(".png"):
            # Check that there is a png file (the backtest figure)
            assert True
            # Remove the file
            os.remove(os.path.join(current_dir, "results", file))
        elif file.endswith(".xlsx"):
            df_trades = pd.read_excel(
                os.path.join(current_dir, "results", file),
                "Trades"
            )
            df_summary = pd.read_excel(
                os.path.join(current_dir, "results", file),
                "Summary"
            )
            # Check that there are several trades
            assert df_trades.shape[1] > 1
            # Check that there are values
            for col in df_summary.columns:
                assert not pd.isna(df_summary[col][0])
            # Remove the file
            os.remove(os.path.join(current_dir, "results", file))

    # Remove the results folder within the tests folder
    os.rmdir(os.path.join(current_dir, "results"))
