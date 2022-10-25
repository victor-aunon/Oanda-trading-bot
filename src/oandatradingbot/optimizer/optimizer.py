# Libraries
import argparse
import json
from multiprocessing import cpu_count
import os
from typing import List

# Packages
import backtrader as bt
import numpy as np

# Locals
from oandatradingbot.strategies.macd_ema_atr_backtest import MacdEmaAtrBackTest
from oandatradingbot.utils.financial_feed import FinancialFeed
from oandatradingbot.optimizer.summarizer_opt import Summarizer
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.config_checker import check_config

current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=("Backtester based on Yahoo finance instrument feed"),
    )

    parser.add_argument(
        "--config-file",
        default=os.path.join(
            current_dir, "..", "..", "..", "config", "config_optimize.json"
        ),
        required=False,
        help="Configuration json file required to run the bot",
    )

    parser.add_argument("--basetemp", required=False, help=argparse.SUPPRESS)

    parser.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(pargs)


def main(config_obj=None):
    print("====== Starting backtrader ======")
    args = parse_args()

    if config_obj is None:
        # Load config json file
        with open(args.config_file, "r") as file:
            config: ConfigType = json.load(file)
    else:
        config = config_obj

    config["debug"] = False

    config = check_config(config, "optimize")

    # Create ranges from strategy parameters
    variations: List[int] = []
    print("Parameters values:")
    for param in config["strategy_params"]:
        param_dict = config["strategy_params"][param]  # type: ignore
        if isinstance(param_dict, dict):
            config[param] = np.arange(  # type: ignore
                param_dict["start"], param_dict["end"], param_dict["step"]
            )
            print(f"    {param}: {config[param]}")  # type: ignore
            variations.append(len(config[param]))  # type: ignore
        elif isinstance(param_dict, list):
            config[param] = param_dict  # type: ignore
            print(f"    {param}: {config[param]}")  # type: ignore
            variations.append(len(config[param]))  # type: ignore
        else:
            config[param] = param_dict  # type: ignore
            print(f"    {param}: {config[param]}")  # type: ignore
    print(f"Simulations: {np.prod(variations)}")
    print(f"Batches: {int(np.ceil(np.prod(variations) / cpu_count()))}\n")
    config.pop("strategy_params", None)

    cerebro = bt.Cerebro(stdstats=False, optreturn=True)

    for instrument in config["instruments"]:
        for i, tframe in enumerate(config["timeframes"]):
            print(
                f"Downloading {instrument} feed with interval "
                f"{tframe['interval']}..."
            )
            feed = FinancialFeed(instrument, tframe["interval"]).get_feed()
            data = bt.feeds.PandasData(dataname=feed, name=instrument)
            if i == 0:
                data_name = instrument
            else:
                data_name = f"{instrument}t{tframe['compression']}"

            cerebro.resampledata(
                data,
                name=data_name,
                timeframe=eval(f"bt.TimeFrame.{tframe['timeframe']}"),
                compression=tframe["compression"],
            )

    cerebro.broker = bt.brokers.BackBroker(cash=config["cash"])
    # Allow cheat con close, otherwise order will match next open price
    # and SL and TK calculation are messed up
    cerebro.broker.set_coc(True)

    # Envolve instruments and timeframes in an array for multiprocessing
    config["instruments"] = [config["instruments"]]  # type: ignore
    config["timeframes"] = [config["timeframes"]]  # type: ignore
    cerebro.optstrategy(MacdEmaAtrBackTest, **config)

    print("Running backtests...")
    cerebro.run()

    summarizer = Summarizer(config)
    summarizer.save_optimization_results()
    summarizer.save_instruments_plots()
    summarizer.parameters_plots()
