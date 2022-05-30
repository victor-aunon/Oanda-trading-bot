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
        instrument: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> None:
        self.instrument = instrument
        self.strategy = strategy
        self.trades_list = results.order_manager.trades
        self.drawdown = results.analyzers.drawdown.get_analysis()
        self.summary_file = results.summary_file
        self.p_r_ratio = config["profit_risk_ratio"]
        self.initial_cash = config["cash"]
        self.currency = config["account_currency"]
        self.interval = config["timeframe_num"]

    def _get_trades_pl_stats(self) -> Dict[str, Union[int, float]]:
        pl_dict = {
            "Trades": 0,
            "Won": 0,
            "Lost": 0,
            "Long": 0,
            "Long won": 0,
            "Long lost": 0,
            "Short": 0,
            "Short won": 0,
            "Short lost": 0,
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
                pl_dict["Won"] += 1
                if trade["Operation"] == "BUY":
                    pl_dict["Long won"] += 1
                elif trade["Operation"] == "SELL":
                    pl_dict["Short won"] += 1
                won_counter += 1
                lost_counter = 0
                if won_counter > pl_dict["Longest winning streak"]:
                    pl_dict["Longest winning streak"] = won_counter
            else:
                pl_dict["Total loss"] += abs(trade["PL"])
                pl_dict["Lost"] += 1
                if trade["Operation"] == "BUY":
                    pl_dict["Long lost"] += 1
                elif trade["Operation"] == "SELL":
                    pl_dict["Short lost"] += 1
                lost_counter += 1
                won_counter = 0
                if lost_counter > pl_dict["Longest losing streak"]:
                    pl_dict["Longest losing streak"] = lost_counter
        pl_dict["Trades"] = pl_dict["Won"] + pl_dict["Lost"]
        pl_dict["Long"] = pl_dict["Long won"] + pl_dict["Long lost"]
        pl_dict["Short"] = pl_dict["Short won"] + pl_dict["Short lost"]
        pl_dict["Mean profit"] = np.mean(
            [t["PL"] for t in self.trades_list[self.instrument] if t["PL"] > 0]
        )
        pl_dict["Mean loss"] = abs(np.mean(
            [t["PL"] for t in self.trades_list[self.instrument] if t["PL"] < 0]
        ))
        r_multiples_neg = np.array([-1] * pl_dict["Lost"])  # type: ignore
        r_multiples_pos = np.array(
            [self.p_r_ratio] * pl_dict["Won"]  # type: ignore
        )
        r_multiples = np.concatenate(
            (r_multiples_pos, r_multiples_neg), axis=None
        )
        pl_dict["SQN"] = np.mean(r_multiples) / np.std(r_multiples) \
            * np.sqrt(r_multiples.size)
        return pl_dict

    def print_summary(self) -> None:
        tr_pl = self._get_trades_pl_stats()
        w_rate = tr_pl["Won"] / tr_pl["Trades"]
        w_l_ratio = tr_pl["Won"] / tr_pl["Lost"]
        m_d_t = self.drawdown['max']['len'] * self.interval / 60 / 24
        report_name = self.instrument if self.instrument is not None \
            else self.strategy
        cash = tr_pl['Total profit'] - tr_pl['Total loss']

        print("============================================")
        print("***** REPORT --", report_name, "*****")
        print("============================================")
        print(f"Final cash: {(cash + self.initial_cash):.2f} {self.currency}")
        print(
            f"Returns: {(cash):.2f} {self.currency} ",
            f"| {(cash / self.initial_cash * 100):.2f} %"
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

        summary = pd.DataFrame([{
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
            "Returns %":cash / self.initial_cash * 100
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
