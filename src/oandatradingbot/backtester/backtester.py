# Libraries
import argparse
from datetime import datetime
import json
import os
import sys

# Packages
import backtrader as bt
import matplotlib.pyplot as plt

# Locals
from oandatradingbot.backtester.summarizer import Summarizer
from oandatradingbot.strategies.macd_ema_atr import MACDEMAATRCreator
from oandatradingbot.strategies.base_backtest_strategy \
    import BaseBackTestStrategy
from oandatradingbot.utils.financial_feed import FinancialFeed

CRYPTOS = ["BTC", "BCH", "ETH", "LTC"]
plt.rcParams["figure.figsize"] = (15, 10)
current_dir = os.path.dirname(os.path.abspath(__file__))


def saveplots(
    cerebro, numfigs=1, iplot=False, start=None, end=None,
    dpi=300, tight=True, use=None, **kwargs
):

    from backtrader import plot
    if cerebro.p.oldsync:
        plotter = plot.Plot_OldSync(**kwargs)
    else:
        plotter = plot.Plot(**kwargs)

    for stratlist in cerebro.runstrats:
        for si, strategy in enumerate(stratlist):
            fig = plotter.plot(
                strategy, figid=si * 100,
                numfigs=numfigs, iplot=iplot,
                start=start, end=end, use=use
            )
    return fig


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


def main(config_obj=None, testing=False):
    print("====== Starting backtrader ======")
    args = parse_args()

    if config_obj is None:
        # Load config json file
        with open(args.config_file, "r") as file:
            config = json.load(file)
    else:
        config = config_obj

    config["debug"] = args.debug
    config["optimize"] = False

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
        config[param] = config["strategy_params"][param]
    config.pop("strategy_params", None)

    for pair in list(config["pairs"]):  # type: ignore
        cerebro = bt.Cerebro(stdstats=True)

        market = "fx" if pair.split("_")[0] not in CRYPTOS else "crypto"
        print(f"Downloading {pair} feed...")
        feed = FinancialFeed(pair, market, config['interval']).get_feed()
        data = bt.feeds.PandasData(dataname=feed, name=pair)

        cerebro.resampledata(
            data, name=pair,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config['timeframe_num']
        )

        cerebro.broker = bt.brokers.BackBroker(cash=config["cash"])
        # Allow cheat con close, otherwise order will match next open price
        # and SL and TK calculation are messed up
        cerebro.broker.set_coc(True)

        config["pairs"] = [pair]
        strategy = MACDEMAATRCreator.creator(BaseBackTestStrategy)
        cerebro.addstrategy(strategy, **config)

        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

        print("Running backtest...")
        results = cerebro.run()

        summarizer = Summarizer(
            results[0], config, pair
        )

        # Print and save summary in the results Excel file
        summarizer.print_summary()
        summarizer.save_summary()

        # Only show the figure if not running a test
        if testing:
            figure = saveplots(
                cerebro, style="candle", barup="green", bardown="red"
            )[0]
        else:
            figure = cerebro.plot(
                style="candle", barup="green", bardown="red"
            )[0][0]

        file_name = (
            f"{results[0].strat_name}_{pair}_"
            f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')}.png"
        )
        figure.savefig(os.path.join(config["results_path"], file_name))
        plt.close("all")
