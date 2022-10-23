# Libraries
import argparse
import json
import os
import sys

# Packages
import backtrader as bt

# Locals
from oandatradingbot.backtester.summarizer import Summarizer
from oandatradingbot.strategies.macd_ema_atr_backtest import MacdEmaAtrBackTest
from oandatradingbot.utils.financial_feed import FinancialFeed
from oandatradingbot.types.config import ConfigType

current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Backtester based on Yahoo finance instrument feed'
        )
    )

    parser.add_argument(
        '--config-file',
        default=os.path.join(current_dir, "..", "config_backtest.json"),
        required=False, help="Configuration json file required to run the bot")

    parser.add_argument(
        '--debug',
        action="store_true", default=False,
        required=False, help="Show extended information")

    parser.add_argument(
        '--basetemp',
        required=False, help=argparse.SUPPRESS)

    parser.add_argument('args', nargs=argparse.REMAINDER)

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

    config["debug"] = args.debug
    config["optimize"] = False
    if "testing" not in config:
        config["testing"] = False

    if config["results_path"] == "the path where results will be saved":
        print("ERROR: Change the name of the results_path before backtesting")
        sys.exit()

    try:
        os.mkdir(config["results_path"])
    except OSError as e:
        if e.errno == 17:
            pass
        else:
            print(e)
            sys.exit()

    # Transform config dictionary
    for param in config["strategy_params"]:
        config[param] = config["strategy_params"][param]  # type: ignore
    config.pop("strategy_params", None)

    for instrument in list(config["instruments"]):
        cerebro = bt.Cerebro(stdstats=True)

        print(f"Downloading {instrument} feed...")
        feed = FinancialFeed(instrument, config['interval']).get_feed()
        data = bt.feeds.PandasData(dataname=feed, name=instrument)

        cerebro.resampledata(
            data, name=instrument,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config['timeframe_num']
        )

        cerebro.broker = bt.brokers.BackBroker(cash=config["cash"])
        # Allow cheat con close, otherwise order will match next open price
        # and SL and TK calculation are messed up
        cerebro.broker.set_coc(True)

        config["instruments"] = [instrument]
        kwargs = config
        kwargs["config"] = config  # type: ignore[typeddict-item]
        cerebro.addstrategy(MacdEmaAtrBackTest, **kwargs)

        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

        print("Running backtest...")
        results = cerebro.run()

        summarizer = Summarizer(
            results[0], config, instrument, results[0].strat_name
        )

        # Print and save summary in the results Excel file
        summarizer.print_summary()
        summarizer.save_summary()

        # Save strategy performance figure
        summarizer.save_plots(cerebro)
