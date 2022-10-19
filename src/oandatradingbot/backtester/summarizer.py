# Libraries
from datetime import datetime
import os
from typing import Any, Dict, List, Union

# Packages
from backtrader import plot
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import load_workbook
import pandas as pd

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.types.trade import TradeType

PlStatsType = Dict[str, Union[int, float, np.floating[Any]]]


class Summarizer:
    def __init__(
        self, results: Any, config: ConfigType,
        instrument: str,
        strategy: str
    ) -> None:
        self.instrument = instrument
        self.strategy = strategy
        self.trades_list: Dict[str, List[TradeType]] = \
            results.order_manager.trades
        self.drawdown: Dict[str, Any] = \
            results.analyzers.drawdown.get_analysis()
        self.summary_file: str = results.summary_file
        self.p_r_ratio: float = \
            config["profit_risk_ratio"]  # type: ignore[typeddict-item]
        self.initial_cash: float = config["cash"]
        self.currency: str = config["account_currency"]
        self.interval: int = config["timeframe_num"]
        self.testing: bool = config["testing"]
        self.results_path: str = config["results_path"]

    def _get_trades_pl_stats(self) -> PlStatsType:
        pl_stats: PlStatsType = {
            "Trades": 0,
            "Won": 0,
            "Lost": 0,
            "Long": 0,
            "Long won": 0,
            "Long lost": 0,
            "Short": 0,
            "Short won": 0,
            "Short lost": 0,
            "Total profit": 0.0,
            "Total loss": 0.0,
            "Mean profit": 0.0,
            "Mean loss": 0.0,
            "Longest winning streak": 0,
            "Longest losing streak": 0,
        }
        lost_counter: int = 0
        won_counter: int = 0
        for trade in self.trades_list[self.instrument]:
            if trade["PL"] > 0:
                pl_stats["Total profit"] += trade["PL"]
                pl_stats["Won"] += 1
                if trade["Operation"] == "BUY":
                    pl_stats["Long won"] += 1
                elif trade["Operation"] == "SELL":
                    pl_stats["Short won"] += 1
                won_counter += 1
                lost_counter = 0
                if won_counter > pl_stats["Longest winning streak"]:
                    pl_stats["Longest winning streak"] = won_counter
            else:
                pl_stats["Total loss"] += abs(trade["PL"])
                pl_stats["Lost"] += 1
                if trade["Operation"] == "BUY":
                    pl_stats["Long lost"] += 1
                elif trade["Operation"] == "SELL":
                    pl_stats["Short lost"] += 1
                lost_counter += 1
                won_counter = 0
                if lost_counter > pl_stats["Longest losing streak"]:
                    pl_stats["Longest losing streak"] = lost_counter
        pl_stats["Trades"] = pl_stats["Won"] + pl_stats["Lost"]
        pl_stats["Long"] = pl_stats["Long won"] + pl_stats["Long lost"]
        pl_stats["Short"] = pl_stats["Short won"] + pl_stats["Short lost"]
        pl_stats["Mean profit"] = np.mean(
            [t["PL"] for t in self.trades_list[self.instrument] if t["PL"] > 0]
        )
        pl_stats["Mean loss"] = abs(
            np.mean([t["PL"] for t in self.trades_list[self.instrument]
                     if t["PL"] < 0])
        )
        r_multiples_neg = np.array([-1] * pl_stats["Lost"])  # type: ignore
        r_multiples_pos = np.array(
            [self.p_r_ratio] * pl_stats["Won"]  # type: ignore
        )
        r_multiples = np.concatenate(
            (r_multiples_pos, r_multiples_neg),
            axis=None
        )
        pl_stats["SQN"] = (
            np.mean(r_multiples)
            / np.std(r_multiples)
            * np.sqrt(r_multiples.size)
        )
        return pl_stats

    def print_summary(self) -> None:
        tr_pl = self._get_trades_pl_stats()
        w_rate = tr_pl["Won"] / tr_pl["Trades"]
        w_l_ratio = tr_pl["Won"] / tr_pl["Lost"]
        m_d_t = self.drawdown["max"]["len"] * self.interval / 60 / 24
        report_name = self.instrument if self.instrument is not None \
            else self.strategy
        cash = tr_pl["Total profit"] - tr_pl["Total loss"]

        print("============================================")
        print("***** REPORT --", report_name, "*****")
        print("============================================")
        print(f"Final cash: {(cash + self.initial_cash):.2f} {self.currency}")
        print(
            f"Returns: {(cash):.2f} {self.currency} ",
            f"| {(cash / self.initial_cash * 100):.2f} %",
        )
        print("============================================")
        print(f"Total profit: {tr_pl['Total profit']:.2f} {self.currency}")
        print(f"Mean profit: {tr_pl['Mean profit']:.2f} {self.currency}")
        print(f"Longest wining streak: {tr_pl['Longest winning streak']}")
        print(f"Total loss: {tr_pl['Total loss']:.2f} {self.currency}")
        print(f"Mean loss: {tr_pl['Mean loss']:.2f} {self.currency}")
        print(f"Longest losing streak: {tr_pl['Longest losing streak']}")
        print("============================================")
        print("Trades:", tr_pl["Trades"])
        print("    Won:", tr_pl["Won"])
        print("    Lost:", tr_pl["Lost"])
        print(f"Win rate: {w_rate:.3f}")
        print(f"Win/loss ratio: {w_l_ratio:.3f}")
        print("Long:", tr_pl["Long"])
        print("    Won:", tr_pl["Long won"])
        print("    Lost:", tr_pl["Long lost"])
        print("Short:", tr_pl["Short"])
        print("    Won:", tr_pl["Short won"])
        print("    Lost:", tr_pl["Short lost"])
        print("============================================")
        print(f"Max drawdown time: {m_d_t:.2f} days")
        print(
            f"Max drawdown money: {self.drawdown['max']['moneydown']:.2f} "
            f"{self.currency} | {self.drawdown['max']['drawdown']:.2f} %"
        )
        print("============================================")
        print("SQN:", f"{tr_pl['SQN']:.3f}")
        print("============================================")

    def save_summary(self) -> None:
        tr_pl = self._get_trades_pl_stats()
        w_rate = tr_pl["Won"] / tr_pl["Trades"]
        w_l_ratio = tr_pl["Won"] / tr_pl["Lost"]
        m_d_t = self.drawdown["max"]["len"] * self.interval / 60 / 24
        report_name = self.instrument if self.instrument is not None \
            else self.strategy
        cash = tr_pl["Total profit"] - tr_pl["Total loss"]

        summary = pd.DataFrame(
            [
                {
                    "Name": report_name,
                    "Trades": tr_pl["Trades"],
                    "Won": tr_pl["Won"],
                    "Lost": tr_pl["Lost"],
                    "Long total": tr_pl["Long"],
                    "Long won": tr_pl["Long won"],
                    "Long lost": tr_pl["Long lost"],
                    "Short total": tr_pl["Short"],
                    "Short won": tr_pl["Short won"],
                    "Short lost": tr_pl["Short lost"],
                    "Total profit": tr_pl["Total profit"],
                    "Total loss": tr_pl["Total loss"],
                    "Max drawdown time days": m_d_t,
                    "Max drawdown money %": self.drawdown["max"]["drawdown"],
                    "Win rate": w_rate,
                    "Win/loss ratio": w_l_ratio,
                    "SQN": tr_pl["SQN"],
                    "Returns": cash,
                    "Returns %": cash / self.initial_cash * 100,
                }
            ]
        )

        if os.path.exists(self.summary_file):
            book = load_workbook(self.summary_file)
            writer = pd.ExcelWriter(self.summary_file, engine="openpyxl")
            writer.book = book
            writer.sheets = {ws.title: ws for ws in book.worksheets}
        else:
            writer = pd.ExcelWriter(self.summary_file, engine="openpyxl")
        summary.to_excel(writer, "Summary", index=False)
        writer.save()

    def save_plots(
        self, cerebro, numfigs=1, iplot=False, start=None, end=None, dpi=300,
        tight=True, use=None, **kwargs
    ):

        plt.rcParams["figure.figsize"] = (15, 10)
        file_name = (
            f"{self.strategy}_{self.instrument}_"
            f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')}.png"
        )

        # Only show the figure if not running a test
        if self.testing:
            if cerebro.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

            for stratlist in cerebro.runstrats:
                for si, strategy in enumerate(stratlist):
                    figure: Figure = plotter.plot(
                        strategy, figid=si * 100,
                        numfigs=numfigs, iplot=iplot,
                        start=start, end=end, use=use,
                        style="candle", barup="green", bardown="red"
                    )[0]
        else:
            figure = cerebro.plot(
                style="candle", barup="green", bardown="red"
            )[0][0]

        figure.savefig(os.path.join(self.results_path, file_name))
        plt.close("all")
