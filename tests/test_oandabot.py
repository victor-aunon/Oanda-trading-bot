# Libraries
import os

# Packages
import backtrader
import pytest

# Local
from tradingbot.oandabot import main

current_dir = os.path.dirname(os.path.abspath(__file__))


def test_oandabot():

    with pytest.raises(backtrader.errors.StrategySkipError):
        main(
            "config_dev.json",
            f"sqlite:///{os.path.join(current_dir, 'test.db')}",
            True
        )

    # Delete db
    os.remove(os.path.join(current_dir, 'test.db'))
