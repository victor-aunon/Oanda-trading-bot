# Libraries
import argparse
import json
import os

# Packages
import backtrader as bt
import btoandav20 as bto
from btoandav20.sizers.oandav20sizer import OandaV20RiskPercentSizer

# Local
from oandatradingbot.strategies.macd_ema_atr import MACDEMAATRCreator
from oandatradingbot.strategies.base_strategy import BaseStrategy


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Oanda trading bot'
        )
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))

    parser.add_argument(
        '--config-file',
        default=os.path.join(current_dir, "config.json"),
        required=False, help="Configuration json file required to run the bot")

    parser.add_argument(
        '--debug',
        action="store_true", default=False,
        required=False, help="Show runtime information")

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

    current_dir = os.path.dirname(os.path.abspath(__file__))

    if "database_uri" not in config:
        config["database_uri"] = \
            f"sqlite:///{os.path.join(current_dir, 'trades.db')}"

    config["account_type"] = "Demo" if config["practice"] else "Brokerage"
    config["testing"] = testing
    config["debug"] = args.debug
    # Check there are no repeated pairs
    config["pairs"] = list(set(config["pairs"]))

    # Instantiate cerebro
    cerebro = bt.Cerebro()

    store = bto.stores.OandaV20Store(
        token=config["oanda_token"],
        account=config["oanda_account_id"],
        practice=config["practice"],
        stream_timeout=20,
        notif_transactions=True
    )

    for pair in config["pairs"]:
        data = store.getdata(
            dataname=pair,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"]
            # qcheck=20,  # Increase qcheck (0.5 def) to ensure candles every
            # next
        )
        cerebro.resampledata(
            data,
            name=pair,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"],
        )
    cerebro.broker = store.getbroker()  # Assign Oanda broker

    strategy = MACDEMAATRCreator.creator(BaseStrategy)
    cerebro.addstrategy(strategy, **config)

    # Sizes are going to be a percentage of the cash
    cerebro.addsizer(OandaV20RiskPercentSizer, percents=config["risk"] / 100)
    cerebro.run()
