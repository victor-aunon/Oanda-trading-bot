# Libraries
import argparse
import json
import os

# Packages
import backtrader as bt

# Locals
from oandatradingbot.backtester.summarizer import Summarizer
from oandatradingbot.strategies.macd_ema_atr_backtest import MacdEmaAtrBackTest
from oandatradingbot.types.config import ConfigType
from oandatradingbot.utils.config_checker import check_config
from oandatradingbot.utils.financial_feed import FinancialFeed

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
        default=os.path.join(
            current_dir, "..", "..", "..", "config", "config_backtest.json"
        ),
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

    config = check_config(config, "backtest")

    for instrument in list(config["instruments"]):
        cerebro = bt.Cerebro(stdstats=True)

        for i, tframe in enumerate(config["timeframes"]):
            print(
                f"Downloading {instrument} feed with interval "
                f"{tframe['interval']}..."
            )
            feed = FinancialFeed(instrument, tframe['interval']).get_feed()
            data = bt.feeds.PandasData(dataname=feed, name=instrument)
            if i == 0:
                data_name = instrument
            else:
                data_name = f"{instrument}t{tframe['compression']}"

            cerebro.resampledata(
                data, name=data_name,
                timeframe=eval(f"bt.TimeFrame.{tframe['timeframe']}"),
                compression=tframe['compression']
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
