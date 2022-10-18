# Libraries
import argparse
from datetime import datetime
import json
from multiprocessing import cpu_count
import os
import sys
from typing import List

# Packages
import backtrader as bt
import numpy as np

# Locals
from oandatradingbot.strategies.macd_ema_atr_backtest import MacdEmaAtrBackTest
from oandatradingbot.utils.financial_feed import FinancialFeed
from oandatradingbot.optimizer.summarizer_opt import Summarizer
from oandatradingbot.types.config import ConfigType

CRYPTOS = ["BTC", "BCH", "ETH", "LTC"]
current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=("Backtester based on Yahoo finance instrument feed"),
    )

    parser.add_argument(
        "--config-file",
        default=os.path.join(current_dir, "..", "config_optimize.json"),
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
    config["optimize"] = True

    if config["results_path"] == "the path where results will be saved":
        print("ERROR: Change the name of the results_path before backtesting")
        sys.exit()

    # Create results folder
    opt_name: str = (
        "Optimization_"
        f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M')}"
    )

    config["opt_name"] = opt_name
    try:
        os.mkdir(os.path.join(config["results_path"]))
    except OSError as e:
        if e.errno == 17:
            pass
        else:
            print(e)
            sys.exit()
    try:
        os.mkdir(os.path.join(config["results_path"], opt_name))
    except OSError as e:
        if e.errno == 17:
            pass
        else:
            print(e)
            sys.exit()

    # Create ranges from strategy parameters
    variations: List[int] = []
    print("Parameters values:")
    for param in config["strategy_params"]:
        param_dict = config[
            "strategy_params"
        ][param]
        if isinstance(param_dict, dict):
            config[param] = np.arange(
                param_dict["start"], param_dict["end"], param_dict["step"]
            )
            print(f"    {param}: {config[param]}")
            variations.append(len(config[param]))
        elif isinstance(param_dict, list):
            config[param] = param_dict
            print(f"    {param}: {config[param]}")
            variations.append(len(config[param]))
        else:
            config[param] = param_dict
            print(f"    {param}: {config[param]}")
    print(f"Simulations: {np.prod(variations)}")
    print(f"Batches: {int(np.ceil(np.prod(variations) / cpu_count()))}\n")
    config.pop("strategy_params", None)

    cerebro = bt.Cerebro(stdstats=False, optreturn=True)

    config["pairs"] = list(set(config["pairs"]))
    for pair in config["pairs"]:  # type: ignore
        market = "fx" if pair.split("_")[0] not in CRYPTOS else "crypto"
        print(f"Downloading {pair} feed...")
        feed = FinancialFeed(pair, market, config["interval"]).get_feed()
        data = bt.feeds.PandasData(dataname=feed, name=pair)

        cerebro.resampledata(
            data,
            name=pair,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"],
        )

    cerebro.broker = bt.brokers.BackBroker(cash=config["cash"])
    # Allow cheat con close, otherwise order will match next open price
    # and SL and TK calculation are messed up
    cerebro.broker.set_coc(True)

    config["pairs"] = [config["pairs"]]  # type: ignore
    cerebro.optstrategy(MacdEmaAtrBackTest, **config)

    print("Running backtests...")
    cerebro.run()

    summarizer = Summarizer(config)
    summarizer.save_optimization_results()
    summarizer.save_instruments_plots()
    summarizer.parameters_plots()
