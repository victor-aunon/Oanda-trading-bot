# Libraries
import argparse
import json
import os

# Packages
import backtrader as bt
import btoandav20 as bto
from btoandav20.sizers.oandav20sizer import OandaV20RiskPercentSizer

# Local
from oandatradingbot.strategies.macd_ema_atr_live import MacdEmaAtrLive
from oandatradingbot.types.config import ConfigType

current_dir = os.path.dirname(os.path.abspath(__file__))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Oanda trading bot'
        )
    )

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


def main(config_obj=None) -> None:
    print("====== Starting backtrader ======")
    args = parse_args()

    if config_obj is None:
        # Load config json file
        with open(args.config_file, "r") as file:
            config: ConfigType = json.load(file)
    else:
        config = config_obj

    # Default database
    if "database_uri" not in config:
        config["database_uri"] = \
            f"sqlite:///{os.path.join(current_dir, 'trades.db')}"

    config["account_type"] = "Demo" if config["practice"] else "Brokerage"
    config["debug"] = args.debug
    if "testing" not in config:
        config["testing"] = False
    # Check there are no repeated instruments
    config["instruments"] = list(set(config["instruments"]))

    # Instantiate cerebro
    cerebro = bt.Cerebro()

    store = bto.stores.OandaV20Store(
        token=config["oanda_token"],
        account=config["oanda_account_id"],
        practice=config["practice"],
        stream_timeout=20,
        notif_transactions=True
    )

    # Transform config dictionary
    for param in config["strategy_params"]:
        p = config["strategy_params"][param]  # type: ignore[literal-required]
        config[param] = p  # type: ignore[literal-required]
    config.pop("strategy_params", None)

    for instrument in config["instruments"]:
        data = store.getdata(
            dataname=instrument,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"]
            # qcheck=20,  # Increase qcheck (0.5 def) to ensure candles every
            # next
        )
        cerebro.resampledata(
            data,
            name=instrument,
            timeframe=eval(f"bt.TimeFrame.{config['timeframe']}"),
            compression=config["timeframe_num"],
        )
    cerebro.broker = store.getbroker()  # Assign Oanda broker

    kwargs = config
    kwargs["config"] = config  # type: ignore[typeddict-item]
    cerebro.addstrategy(MacdEmaAtrLive, **kwargs)

    # Sizes are going to be a percentage of the cash
    cerebro.addsizer(OandaV20RiskPercentSizer, percents=config["risk"] / 100)

    # Add a timer to notify on Fridays before session ends
    # cerebro.add_timer()
    cerebro.run()
