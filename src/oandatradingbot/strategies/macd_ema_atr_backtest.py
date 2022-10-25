# Libraries
from typing import Dict, List

# Packages
from backtrader.indicators.atr import AverageTrueRange as ATR
from backtrader.indicators.ema import ExponentialMovingAverage as EMA
from backtrader.indicators.macd import MACD
from backtrader.lineseries import LineSeries
from backtrader.lineiterator import LineIterator
from backtrader.indicator import Indicator
import numpy as np

# Locals
from oandatradingbot.strategies.base_backtest_strategy \
    import BaseBackTestStrategy
from oandatradingbot.types.config import StrategyParamsType


class MacdEmaAtrBackTest(BaseBackTestStrategy):

    params: StrategyParamsType = {
        "macd_fast_ema": 12,
        "macd_slow_ema": 26,
        "macd_signal_ema": 9,
        "ema_period": 200,
        "atr_period": 14,
        "atr_distance": 1.2,
        "profit_risk_ratio": 1.5,
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.strat_name = "MACDEMAATR_({}-{}-{}-{}-{})-{}{}".format(
            self.p.macd_fast_ema,
            self.p.macd_slow_ema,
            self.p.macd_signal_ema,
            self.p.ema_period,
            f"{self.p.atr_distance:.1f}",
            f"{self.p.profit_risk_ratio:.1f}",
            f"-{self.timeframes[0]['interval']}"
        )
        print(f"Strategy: {self.strat_name}")

    def initialize_dicts(self) -> None:
        ""
        # Dictionaries whose keys are the fx instruments
        self.data: Dict[str, LineIterator] = {}
        self.macd: Dict[str, Indicator] = {}
        self.ema: Dict[str, List[Indicator]] = {}
        self.atr: Dict[str, Indicator] = {}
        self.data_ready: Dict[str, bool] = {}
        # Fill the previous dictionaries
        for instrument in self.instruments:
            # Indicators
            datas: List[LineIterator] = [d for d in self.datas
                                         if instrument in d._name]
            data = datas[0]
            self.data[instrument] = data
            self.macd[instrument] = MACD(
                data.close,
                period_me1=self.p.macd_fast_ema,
                period_me2=self.p.macd_slow_ema,
                period_signal=self.p.macd_signal_ema,
            )
            self.ema[instrument] = []
            for data, period in zip(self.datas, [self.p.ema_period, 100]):
                self.ema[instrument].append(EMA(data.close, period=period))
            self.atr[instrument] = ATR(data, period=self.p.atr_period)
            self.data_ready[instrument] = False

    def get_stop_loss(self, instrument: str) -> float:
        return (  # type: ignore
            self.atr[instrument].atr[0] * self.p.atr_distance
        )

    def get_take_profit(self, instrument: str) -> float:
        return (  # type: ignore
            self.atr[instrument].atr[0]
            * self.p.atr_distance
            * self.p.profit_risk_ratio
        )

    def enter_buy_signal(self, instrument: str) -> bool:
        """Returns True if the following conditions are met:
            - MACD line above signal line
            - MACD line and signal line are below 0
            - MACD line was below signal line 5 bars ago
            - MACD line has not crossed zero line during the last 5 bars
            - The price has been above the EMA line for 20 bars
            - The current EMA value is higher or equal to the one of
              10 bars ago
            - Trend is bullish: slope of EMA is positive
            - Trend in a higher timeframe is bullish (optional)

        Parameters
        ----------
        instrument : str
            The instrument to be traded, e.g. a pair of currencies

        -------
        bool
            True if the conditions are met, otherwise False
        """
        macd: LineSeries = self.macd[instrument].macd
        signal: LineSeries = self.macd[instrument].signal
        ema: LineSeries = self.ema[instrument][0].ema
        if len(self.ema[instrument]) > 1:
            ema_higher_frame: LineSeries = self.ema[instrument][1].ema
        close: LineSeries = self.data[instrument].close

        # Look for previous positive MACD signal values
        prev_positives = [True if x > 0 else False for x in macd.get(size=5)]

        # Look for previous prices above the EMA
        prices_above = [
            True if x > y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        # Check price trend in both time frames
        x_ema = np.arange(len(close.get(size=10)))
        slope_ema, _ = np.polyfit(x_ema, ema.get(size=10), 1)
        if len(self.ema[instrument]) < 2:
            # To always be True if there is only one timeframe
            slope_ema_higher_frame = 1
        else:
            x_ema_higher_frame = np.arange(len(close.get(size=5)))
            slope_ema_higher_frame, _ = np.polyfit(
                x_ema_higher_frame, ema_higher_frame.get(size=5), 1
            )

        return (
            macd[0] > signal[0]
            and signal[0] < 0
            and macd[-5] < signal[-5]
            and True not in prev_positives
            and False not in prices_above
            and ema[-1] >= ema[-10]
            and slope_ema > 0
            and slope_ema_higher_frame > 0
        )

    def enter_sell_signal(self, instrument: str) -> bool:
        """Returns True if the following conditions are met:
            - MACD line below signal line
            - MACD line and signal line are above 0
            - MACD line was above signal line 5 bars ago
            - MACD line has not crossed zero line during the last 5 bars
            - The price has been below the EMA line for 20 bars
            - The current EMA value is lower or equal to the one of
              10 bars ago
            - Trend is bearish: slope of EMA is negative
            - Trend in a higher timeframe is bearish (optional)

        Parameters
        ----------
        instrument : str
            The instrument to be traded, e.g. a pair of currencies

        -------
        bool
            True if the conditions are met, otherwise False
        """
        macd: LineSeries = self.macd[instrument].macd
        signal: LineSeries = self.macd[instrument].signal
        ema: LineSeries = self.ema[instrument][0].ema
        if len(self.ema[instrument]) > 1:
            ema_higher_frame: LineSeries = self.ema[instrument][1].ema
        close: LineSeries = self.data[instrument].close

        # Look for previous negatives MACD signal values
        prev_negatives = [True if x < 0 else False for x in macd.get(size=5)]

        # Look for previous prices below the EMA
        prices_below = [
            True if x < y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        # Check price trend in both time frames
        x_ema = np.arange(len(close.get(size=10)))
        slope_ema, _ = np.polyfit(x_ema, ema.get(size=10), 1)
        if len(self.ema[instrument]) < 2:
            # To always be True if there is only one timeframe
            slope_ema_higher_frame = -1
        else:
            x_ema_higher_frame = np.arange(len(close.get(size=5)))
            slope_ema_higher_frame, _ = np.polyfit(
                x_ema_higher_frame, ema_higher_frame.get(size=5), 1
            )

        return (
            macd[0] < signal[0]
            and signal[0] > 0
            and macd[-5] > signal[-5]
            and True not in prev_negatives
            and False not in prices_below
            and ema[-1] <= ema[-10]
            and slope_ema < 0
            and slope_ema_higher_frame < 0
        )
