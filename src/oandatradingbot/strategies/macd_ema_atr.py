# Packages
from backtrader.indicators.atr import AverageTrueRange as ATR
from backtrader.indicators.ema import ExponentialMovingAverage as EMA
from backtrader.indicators.macd import MACD
from backtrader import Strategy

# Locals
from oandatradingbot.strategies.base_backtest_strategy \
    import BaseBackTestStrategy


class MACDEMAATRCreator:

    def creator(baseclass: Strategy):

        class MACDEMAATR(baseclass):  # type: ignore

            params = {
                "macd_fast_ema": 12,
                "macd_slow_ema": 26,
                "macd_signal_ema": 9,
                "ema_period": 200,
                "atr_period": 14,
                "atr_distance": 1.2,
                "profit_risk_ratio": 1.5
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
                    f"-{self.config['interval']}" if "interval"
                    in self.config else ""
                )
                print(f"Strategy: {self.strat_name}")

            def initialize_dicts(self):
                # Dictionaries whose keys are the fx pairs
                self.data = {}
                self.macd = {}
                self.ema = {}
                self.atr = {}
                self.data_ready = {}
                # Fill the previous dictionaries
                for pair in self.pairs:
                    # Indicators
                    data = [d for d in self.datas if d._name == pair][0]
                    self.data[pair] = data
                    self.macd[pair] = MACD(
                        data.close,
                        period_me1=self.p.macd_fast_ema,
                        period_me2=self.p.macd_slow_ema,
                        period_signal=self.p.macd_signal_ema,
                    )
                    self.ema[pair] = EMA(data.close, period=self.p.ema_period)
                    self.atr[pair] = ATR(data, period=self.p.atr_period)
                    self.data_ready[pair] = False

            def get_stop_loss(self, pair):
                return self.atr[pair].atr[0] * self.p.atr_distance

            def get_take_profit(self, pair):
                return (
                    self.atr[pair].atr[0] * self.p.atr_distance
                    * self.p.profit_risk_ratio
                )

            def near_buy_signal(self, data_name):
                macd = self.macd[data_name].macd
                signal = self.macd[data_name].signal
                ema = self.ema[data_name].ema
                close = self.data[data_name].close

                # Look for previous positive MACD signal values
                prev_positives = [
                    True if x > 0 else False for x in macd.get(size=5)
                ]

                # Look for previous prices above the EMA
                prices_above = [
                    True if x > y else False
                    for x, y in zip(close.get(size=20), ema.get(size=20))
                ]

                return (
                    signal[0] < 0
                    and macd[-5] < signal[-5]
                    and True not in prev_positives
                    and False not in prices_above
                    and ema[-1] > ema[-10]
                )

            def enter_buy_signal(self, data_name):
                macd = self.macd[data_name].macd
                signal = self.macd[data_name].signal
                ema = self.ema[data_name].ema
                close = self.data[data_name].close

                # Look for previous positive MACD signal values
                prev_positives = [
                    True if x > 0 else False for x in macd.get(size=5)
                ]

                # Look for previous prices above the EMA
                prices_above = [
                    True if x > y else False
                    for x, y in zip(close.get(size=20), ema.get(size=20))
                ]

                return (
                    macd[0] > signal[0]
                    and signal[0] < 0
                    and macd[-5] < signal[-5]
                    and True not in prev_positives
                    and False not in prices_above
                    and ema[-1] > ema[-10]
                )

            def near_sell_signal(self, data_name):
                macd = self.macd[data_name].macd
                signal = self.macd[data_name].signal
                ema = self.ema[data_name].ema
                close = self.data[data_name].close

                # Look for previous negatives MACD signal values
                prev_negatives = [
                    True if x < 0 else False for x in macd.get(size=5)
                ]

                prices_below = [
                    True if x < y else False
                    for x, y in zip(close.get(size=20), ema.get(size=20))
                ]

                return (
                    signal[0] > 0
                    and macd[-5] > signal[-5]
                    and True not in prev_negatives
                    and False not in prices_below
                    and ema[-1] < ema[-10]
                )

            def enter_sell_signal(self, data_name):
                macd = self.macd[data_name].macd
                signal = self.macd[data_name].signal
                ema = self.ema[data_name].ema
                close = self.data[data_name].close

                # Look for previous negatives MACD signal values
                prev_negatives = [
                    True if x < 0 else False for x in macd.get(size=5)
                ]

                prices_below = [
                    True if x < y else False
                    for x, y in zip(close.get(size=20), ema.get(size=20))
                ]

                return (
                    macd[0] < signal[0]
                    and signal[0] > 0
                    and macd[-5] > signal[-5]
                    and True not in prev_negatives
                    and False not in prices_below
                    and ema[-1] < ema[-10]
                )

        return MACDEMAATR


class MACDEMAATRBT(BaseBackTestStrategy):  # type: ignore

    params = {
        "macd_fast_ema": 12,
        "macd_slow_ema": 26,
        "macd_signal_ema": 9,
        "ema_period": 200,
        "atr_period": 14,
        "atr_distance": 1.2,
        "profit_risk_ratio": 1.5
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
            f"-{self.config['interval']}" if "interval"
            in self.config else ""
        )

    def initialize_dicts(self):
        # Dictionaries whose keys are the fx pairs
        self.data = {}
        self.macd = {}
        self.ema = {}
        self.atr = {}
        self.data_ready = {}
        # Fill the previous dictionaries
        for pair in self.pairs:
            # Indicators
            data = [d for d in self.datas if d._name == pair][0]
            self.data[pair] = data
            self.macd[pair] = MACD(
                data.close,
                period_me1=self.p.macd_fast_ema,
                period_me2=self.p.macd_slow_ema,
                period_signal=self.p.macd_signal_ema,
            )
            self.ema[pair] = EMA(data.close, period=self.p.ema_period)
            self.atr[pair] = ATR(data, period=self.p.atr_period)
            self.data_ready[pair] = False

    def get_stop_loss(self, pair):
        return self.atr[pair].atr[0] * self.p.atr_distance

    def get_take_profit(self, pair):
        return (
            self.atr[pair].atr[0] * self.p.atr_distance
            * self.p.profit_risk_ratio
        )

    def enter_buy_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous positive MACD signal values
        prev_positives = [
            True if x > 0 else False for x in macd.get(size=5)
        ]

        # Look for previous prices above the EMA
        prices_above = [
            True if x > y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            macd[0] > signal[0]
            and signal[0] < 0
            and macd[-5] < signal[-5]
            and True not in prev_positives
            and False not in prices_above
            and ema[-1] > ema[-10]
        )

    def enter_sell_signal(self, data_name):
        macd = self.macd[data_name].macd
        signal = self.macd[data_name].signal
        ema = self.ema[data_name].ema
        close = self.data[data_name].close

        # Look for previous negatives MACD signal values
        prev_negatives = [
            True if x < 0 else False for x in macd.get(size=5)
        ]

        prices_below = [
            True if x < y else False
            for x, y in zip(close.get(size=20), ema.get(size=20))
        ]

        return (
            macd[0] < signal[0]
            and signal[0] > 0
            and macd[-5] > signal[-5]
            and True not in prev_negatives
            and False not in prices_below
            and ema[-1] < ema[-10]
        )
