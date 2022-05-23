# Libraries
import os
from typing import Any, Dict, Optional, Union

# Packages
import numpy as np
from openpyxl import load_workbook
import pandas as pd


class Summarizer:
    def __init__(
        self, results: Any, config: Dict[str, Any],
        cash: float, instrument: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> None:
        self.instrument = instrument
        self.strategy = strategy
        self.trades_list = results.order_manager.trades
        self.trades = results.analyzers.trades.get_analysis()
        self.drawdown = results.analyzers.drawdown.get_analysis()
        self.sharpe_ratio = results.analyzers.sharperatio.get_analysis()
        self.sqn = results.analyzers.sqn.get_analysis()
        self.summary_file = results.summary_file
        self.initial_cash = config["cash"]
        self.cash = cash
        self.currency = config["account_currency"]
        self.interval = config["timeframe_num"]

    def _get_pl_stats(self) -> Dict[str, Union[int, float]]:
        pl_dict = {
            "Total profit": 0.,
            "Total loss": 0.,
            "Mean profit": 0.,
            "Mean loss": 0.,
            "Longest winning streak": 0,
            "Longest losing streak": 0
        }
        lost_counter = 0
        won_counter = 0
        for trade in self.trades_list[self.instrument]:
            if trade["PL"] > 0:
                pl_dict["Total profit"] += trade["PL"]
                won_counter += 1
                lost_counter = 0
                if won_counter > pl_dict["Longest winning streak"]:
                    pl_dict["Longest winning streak"] = won_counter
            else:
                pl_dict["Total loss"] += abs(trade["PL"])
                lost_counter += 1
                won_counter = 0
                if lost_counter > pl_dict["Longest losing streak"]:
                    pl_dict["Longest losing streak"] = lost_counter
        pl_dict["Mean profit"] = np.mean(
            [t["PL"] for t in self.trades_list[self.instrument] if t["PL"] > 0]
        )
        pl_dict["Mean loss"] = abs(np.mean(
            [t["PL"] for t in self.trades_list[self.instrument] if t["PL"] < 0]
        ))
        return pl_dict

    def print_summary(self) -> None:
        w_ratio = self.trades['won']['total'] / self.trades['total']['closed']
        w_l_ratio = self.trades['won']['total'] / self.trades['lost']['total']
        m_d_t = self.drawdown['max']['len'] * self.interval / 60 / 24
        report_name = self.instrument if self.instrument is not None \
            else self.strategy
        pl = self._get_pl_stats()

        print("============================================")
        print("***** REPORT --", report_name, "*****")
        print("============================================")
        print(f"Final cash: {self.cash:.2f} {self.currency}")
        print(
            f"Returns: {(self.cash - self.initial_cash):.2f} {self.currency} ",
            f"| {((self.cash - self.initial_cash) / self.cash * 100):.2f} %"
        )
        print("============================================")
        print(f"Total profit: {pl['Total profit']:.2f} {self.currency}")
        print(f"Mean profit: {pl['Mean profit']:.2f} {self.currency}")
        print(f"Longest wining streak: {pl['Longest winning streak']}")
        print(f"Total loss: {pl['Total loss']:.2f} {self.currency}")
        print(f"Mean loss: {pl['Mean loss']:.2f} {self.currency}")
        print(f"Longest losing streak: {pl['Longest losing streak']}")
        print("============================================")
        print("Trades:", self.trades["total"]["closed"])
        print("    Won:", self.trades["won"]["total"])
        print("    Lost:", self.trades["lost"]["total"])
        print(f"Win ratio: {w_ratio:.3f}")
        print(f"Win/loss ratio: {w_l_ratio:.3f}")
        print("Long:", self.trades["long"]["total"])
        print("    Won:", self.trades["long"]["won"])
        print("    Lost:", self.trades["long"]["lost"])
        print("Short:", self.trades["short"]["total"])
        print("    Won:", self.trades["short"]["won"])
        print("    Lost:", self.trades["short"]["lost"])
        print("============================================")
        print(f"Max drawdown time: {m_d_t:.2f} days")
        print(
            f"Max drawdown money: {self.drawdown['max']['moneydown']:.2f} "
            f"{self.currency} | {self.drawdown['max']['drawdown']:.2f} %"
        )
        print("============================================")
        print("Sharpe ratio:", f"{self.sharpe_ratio['sharperatio']:.3f}")
        print("============================================")
        print("SQN:", f"{self.sqn['sqn']:.3f}")
        print("============================================")

    def save_summary(self) -> None:
        w_ratio = self.trades['won']['total'] / self.trades['total']['closed']
        w_l_ratio = self.trades['won']['total'] / self.trades['lost']['total']
        m_d_t = self.drawdown['max']['len'] * self.interval / 60 / 24
        report_name = self.instrument if self.instrument is not None \
            else self.strategy
        pl = self._get_pl_stats()

        summary = pd.DataFrame([{
            "Name": report_name,
            "Trades": self.trades["total"]["closed"],
            "Won": self.trades["won"]["total"],
            "Lost": self.trades["lost"]["total"],
            "Long total": self.trades["long"]["total"],
            "Long won": self.trades["long"]["won"],
            "Long lost": self.trades["long"]["lost"],
            "Short total": self.trades["short"]["total"],
            "Short won": self.trades["short"]["won"],
            "Short lost": self.trades["short"]["lost"],
            "Total profit": pl["Total profit"],
            "Total loss": pl["Total loss"],
            "Max drawdown time": m_d_t,
            "Max drawdown money %": self.drawdown['max']['moneydown'],
            "Win ratio": w_ratio,
            "Win/loss ratio": w_l_ratio,
            "Sharpe ratio": self.sharpe_ratio['sharperatio'],
            "SQN": self.sqn['sqn'],
            "Returns": self.cash - self.initial_cash,
            "Returns %": (self.cash - self.initial_cash) / self.cash * 100
        }])

        if os.path.exists(self.summary_file):
            book = load_workbook(self.summary_file)
            writer = pd.ExcelWriter(self.summary_file, engine="openpyxl")
            writer.book = book
            writer.sheets = {ws.title: ws for ws in book.worksheets}
        else:
            writer = pd.ExcelWriter(self.summary_file, engine="openpyxl")
        summary.to_excel(writer, "Summary", index=False)
        writer.save()
