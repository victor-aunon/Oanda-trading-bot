# Libraries
import os
import shutil

# Packages
import pandas as pd

# Locals
from oandatradingbot.optimizer.optimizer import main

current_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    "results_path": os.path.join(current_dir, "results"),
    "instruments": ["EUR_USD", "EUR_GBP"],
    "cash": 10000,
    "risk": 1,
    "account_currency": "EUR",
    "language": "ES-ES",
    "timeframes": [
        {"timeframe": "Minutes", "compression": 5, "interval": "5m"},
        {"timeframe": "Minutes", "compression": 60, "interval": "60m"}
    ],
    "strategy_params": {
        "macd_fast_ema": [5, 6],
        "macd_slow_ema": 25,
        "macd_signal_ema": 5,
        "ema_period": {"start": 100, "end": 121, "step": 20},
        "atr_period": 14,
        "atr_distance": 3.0,
        "profit_risk_ratio": 1.0
    }
}


def test_optimizer():

    main(config)
    strategies = []
    opt_name = ""
    for root, folders, files in os.walk(os.path.join(current_dir, "results")):
        for file in files:
            print(file)
            # Check optimization excel file
            if "Optimization" in file:
                opt_name = root
                df_strats = pd.read_excel(
                    os.path.join(current_dir, "results", root, file),
                    "Summary"
                )
                strategies = df_strats["Name"]
                # Check that there are several strategies
                assert df_strats.shape[1] > 1
                # Check that there are values
                print(df_strats.columns)
                for col in df_strats.columns:
                    assert any(pd.isna(df_strats[col]).values) is False

    # Check figures
    for strat in strategies:
        assert os.path.exists(
            os.path.join(
                current_dir, "results", opt_name,
                f"Cumulative_returns_{strat}.png"
            )
        )
        assert os.path.exists(
            os.path.join(
                current_dir, "results", opt_name, f"Trades_{strat}.png"
            )
        )
        assert os.path.exists(
            os.path.join(
                current_dir, "results", opt_name, f"Win_rate_{strat}.png"
            )
        )

    # Check parameter figures
    assert os.path.exists(
        os.path.join(
            current_dir, "results", opt_name, "Profit_Risk_Ratio_Trades.png"
        )
    )
    assert os.path.exists(
        os.path.join(
            current_dir, "results", opt_name, "Profit_Risk_Ratio_Win_rate.png"
        )
    )

    # Remove the results folder within the tests folder
    shutil.rmtree(os.path.join(current_dir, "results"), ignore_errors=True)
