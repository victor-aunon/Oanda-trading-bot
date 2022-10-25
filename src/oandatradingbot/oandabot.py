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
from oandatradingbot.utils.config_checker import check_config

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
        default=os.path.join(current_dir, "..", "..", "config", "config.json"),
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

    config["debug"] = args.debug

    config = check_config(config, "live")

    # Instantiate cerebro
    cerebro = bt.Cerebro()

    store = bto.stores.OandaV20Store(
        token=config["oanda_token"],
        account=config["oanda_account_id"],
        practice=config["practice"],
        stream_timeout=20,
        notif_transactions=True
    )

    for instrument in config["instruments"]:
        for i, tframe in enumerate(config["timeframes"]):
            data = store.getdata(
                dataname=instrument,
                timeframe=eval(f"bt.TimeFrame.{tframe['timeframe']}"),
                compression=tframe["compression"]
                # Increase qcheck (0.5 def) to ensure candles every next
                # qcheck=20,
            )
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
    cerebro.broker = store.getbroker()  # Assign Oanda broker

    kwargs = config
    kwargs["config"] = config  # type: ignore[typeddict-item]
    cerebro.addstrategy(MacdEmaAtrLive, **kwargs)

    # Sizes are going to be a percentage of the cash
    cerebro.addsizer(OandaV20RiskPercentSizer, percents=config["risk"] / 100)

    # Add a timer to notify on Fridays before session ends
    # cerebro.add_timer()
    cerebro.run()
