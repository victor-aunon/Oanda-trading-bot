# Libraries
import os
from typing import Any, Dict, List

# Packages
import numpy as np
import pandas as pd
import pylab as plt
import warnings
import xlsxwriter

from oandatradingbot.types.config import ConfigType

warnings.filterwarnings("ignore")


class Summarizer:
    def __init__(self, config: ConfigType) -> None:
        self.strat_files = []
        self.instruments = config["instruments"][0]
        self.results_path = config["results_path"]
        self.initial_cash = config["cash"]
        self.currency = config["account_currency"]
        self.opt_name = config["opt_name"]
        for file in os.listdir(
            os.path.join(self.results_path, self.opt_name, "temp")
        ):
            if file.endswith(".csv"):
                self.strat_files.append(file)

    def _get_strategy_summary(self) -> List[Dict[str, Any]]:

        results_list = []

        for strategy in self.strat_files:
            df_strat = pd.read_csv(
                os.path.join(
                    self.results_path, self.opt_name, "temp", strategy
                ),
                sep=";"
            )
            cash = df_strat["Total profit"][0] - df_strat["Total loss"][0]

            res = {
                "Name": strategy.split(".csv")[0],
                "Trades": df_strat["Trades"][0],
                "Won": df_strat["Won"][0],
                "Lost": df_strat["Lost"][0],
                "Long total": df_strat["Long"][0],
                "Long won": df_strat["Long won"][0],
                "Long lost": df_strat["Long lost"][0],
                "Short total": df_strat["Short"][0],
                "Short won": df_strat["Short won"][0],
                "Short lost": df_strat["Short lost"][0],
                "Win rate": df_strat["Won"][0] / df_strat["Trades"][0],
                "Win/loss ratio": df_strat["Won"][0] / df_strat["Lost"][0],
                "SQN": df_strat['SQN'][0],
                "Returns": cash,
                "Returns %": cash / self.initial_cash * 100
            }

            for inst in self.instruments:
                try:
                    res[f"Trades {inst}"] = df_strat[f"Trades {inst}"][0]
                    res[f"Won {inst}"] = df_strat[f"Won {inst}"][0]
                    res[f"Lost {inst}"] = df_strat[f"Lost {inst}"][0]
                    res[f"Returns {inst}"] = df_strat[f"Returns {inst}"][0]
                except KeyError:
                    res[f"Trades {inst}"] = 0.0
                    res[f"Won {inst}"] = 0.0
                    res[f"Lost {inst}"] = 0
                    res[f"Returns {inst}"] = 0.0

            results_list.append(res)

        return results_list

    def _remove_temp_files(self):
        for file in self.strat_files:
            os.remove(
                os.path.join(self.results_path, self.opt_name, "temp", file)
            )

        os.rmdir(os.path.join(self.results_path, self.opt_name, "temp"))

    def save_optimization_results(self) -> None:

        results_list = self._get_strategy_summary()

        summary_file = os.path.join(
            self.results_path,
            self.opt_name,
            f"{self.opt_name}.xlsx"
        )

        # Create xlsxwriter workbook
        workbook = xlsxwriter.Workbook(summary_file)
        worksheet = workbook.add_worksheet("Summary")

        # Add a format for the successful operation
        successful = workbook.add_format({
            'border': 0,
            'bg_color': '#94eb9e',
            'align': 'center',
            'valign': 'vcenter',
        })

        # Add a format for the unsuccessful operation
        unsuccessful = workbook.add_format({
            'border': 0,
            'bg_color': '#fa7f7f',
            'align': 'center',
            'valign': 'vcenter',
        })

        # Create the trades table
        worksheet.add_table(
            0, 0, len(results_list), len(results_list[0].keys()) - 1,
            {"columns": [{"header": col} for col in results_list[0].keys()]}
        )

        for i, trade in enumerate(results_list):
            worksheet.write_row(
                i + 1, 0, trade.values(),
                cell_format=successful if trade["Win rate"] >= 0.5
                else unsuccessful
            )

        workbook.close()

        results_list.sort(
            key=lambda r: r["Win rate"], reverse=True  # type: ignore
        )

        print("============================================")
        print("************* BEST STRATEGIES **************")
        print(
            f"{results_list[0]['Name']} --> Win rate: "
            f"{results_list[0]['Win rate']:.3f}"
        )
        if len(results_list) > 1:
            print(
                f"{results_list[1]['Name']} --> Win rate: "
                f"{results_list[1]['Win rate']:.3f}"
            )
        if len(results_list) > 2:
            print(
                f"{results_list[2]['Name']} --> Win rate: "
                f"{results_list[2]['Win rate']:.3f}"
            )

    def save_instruments_plots(self):

        # Do not create figure if there is only one instrument
        if len(self.instruments) == 1:
            self._remove_temp_files()
            return

        df_strats = pd.read_excel(
            os.path.join(
                self.results_path, self.opt_name, f"{self.opt_name}.xlsx"
            ),
        ).sort_values(by=["SQN"], ascending=False).head(30)
        for strategy in df_strats["Name"]:
            res_dict: Dict[str, Dict[str, float]] = {}
            res_dict["Trades"] = {}
            res_dict["Returns"] = {}
            res_dict["Win rate"] = {}
            for inst in self.instruments:
                res_dict["Trades"][inst] = \
                    df_strats.loc[
                        df_strats["Name"] == strategy, f"Trades {inst}"
                    ].item()
                res_dict["Returns"][inst] = \
                    df_strats.loc[
                        df_strats["Name"] == strategy, f"Returns {inst}"
                    ].item() / self.initial_cash * 100
                res_dict["Win rate"][inst] = \
                    df_strats.loc[
                        df_strats["Name"] == strategy, f"Won {inst}"
                    ].item() / res_dict["Trades"][inst] * 100
            trades_keys = sorted(
                res_dict["Trades"],
                key=res_dict["Trades"].get,  # type: ignore
                reverse=True
            )
            trades_values = [res_dict["Trades"][k] for k in trades_keys]
            returns_keys = sorted(
                res_dict["Returns"],
                key=res_dict["Returns"].get,  # type: ignore
                reverse=True
            )
            returns_values = [res_dict["Returns"][k] for k in returns_keys]
            win_rate_keys = sorted(
                res_dict["Win rate"],
                key=res_dict["Win rate"].get,  # type: ignore
                reverse=True
            )
            win_rate_values = [res_dict["Win rate"][k] for k in win_rate_keys]

            # Returns figure
            fig = plt.figure(figsize=(10, 4.2))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(bottom=0.17, left=0.08, right=0.95)

            colors = ["g" if x > 0 else "r" for x in returns_values]

            ax.bar(range(len(returns_keys)), returns_values, color=colors)
            ax.set_axisbelow(True)
            ax.grid(which='major', axis='y', color='0.5')
            ax.grid(which='minor', axis='y', ls='--')
            ax.set_xticks(range(len(returns_keys)))
            # plt.minorticks_on()
            ax.set_xticklabels(
                returns_keys, fontsize=9, rotation=60, ha="right"
            )
            ax.set_ylim(
                [np.floor(min(returns_values) / 10) * 10,
                 np.ceil(max(returns_values) / 10) * 10]
            )
            plt.title("Cumulative returns (%)", fontsize=14, fontweight="bold")
            fig.savefig(
                os.path.join(
                    self.results_path,
                    self.opt_name,
                    f"Cumulative_returns_{strategy}.png"
                ),
                dpi=300
            )
            plt.close(fig)

            # Win rate figure
            fig = plt.figure(figsize=(10, 4.2))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(bottom=0.17, left=0.08, right=0.95)

            colors = ["g" if x >= 50 else "r" for x in win_rate_values]

            ax.bar(range(len(win_rate_keys)), win_rate_values, color=colors)
            ax.set_axisbelow(True)
            ax.grid(which='major', axis='y', color='0.5')
            ax.grid(which='minor', axis='y', ls='--')
            ax.set_xticks(range(len(win_rate_keys)))
            # plt.minorticks_on()
            ax.set_xticklabels(
                win_rate_keys, fontsize=9, rotation=60, ha="right"
            )
            ax.set_ylim(
                [np.floor(min(win_rate_values) / 10) * 10,
                 np.ceil(max(win_rate_values) / 10) * 10]
            )
            plt.title("Win rate (%)", fontsize=14, fontweight="bold")
            fig.savefig(
                os.path.join(
                    self.results_path,
                    self.opt_name,
                    f"Win_rate_{strategy}.png"
                ),
                dpi=300
            )
            plt.close(fig)

            # Trades figure
            fig = plt.figure(figsize=(10, 4.2))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(bottom=0.17, left=0.08, right=0.95)

            ax.bar(range(len(trades_keys)), trades_values)
            ax.set_axisbelow(True)
            ax.grid(which='major', axis='y', color='0.5')
            ax.grid(which='minor', axis='y', ls='--')
            ax.set_xticks(range(len(trades_keys)))
            # plt.minorticks_on()
            ax.set_xticklabels(
                trades_keys, fontsize=9, rotation=60, ha="right"
            )
            ax.set_ylim(
                [np.floor(min(trades_values) / 10) * 10,
                 np.ceil(max(trades_values) / 10) * 10]
            )
            plt.title("Trades", fontsize=14, fontweight="bold")
            fig.savefig(
                os.path.join(
                    self.results_path,
                    self.opt_name,
                    f"Trades_{strategy}.png"
                ),
                dpi=300
            )
            plt.close(fig)

        self._remove_temp_files()

    def parameters_plots(self):
        optimization_file = None
        for file in os.listdir(
            os.path.join(self.results_path, self.opt_name)
        ):
            if file.endswith(".xlsx"):
                optimization_file = file

        if optimization_file is None:
            return

        df = pd.read_excel(
            os.path.join(self.results_path, self.opt_name, optimization_file)
        )
        # Extract parameters values from strategy name
        macd_fast_ema = [
            float(p.split("(")[1].split("-")[0]) for p in df["Name"]
        ]
        macd_slow_ema = [
            float(p.split("(")[1].split("-")[1]) for p in df["Name"]
        ]
        macd_signal_ema = [
            float(p.split("(")[1].split("-")[2]) for p in df["Name"]
        ]
        ema = [
            float(p.split("(")[1].split("-")[3]) for p in df["Name"]
        ]
        atr_distance = [
            float(p.split("(")[1].split("-")[4].split(")")[0])
            for p in df["Name"]
        ]
        p_r_ratio = [
            float(p.split(")")[1].split("-")[1]) for p in df["Name"]
        ]

        param_dict = {
            "MACD Fast EMA": macd_fast_ema,
            "MACD Slow EMA": macd_slow_ema,
            "MACD Signal EMA": macd_signal_ema,
            "EMA": ema,
            "ATR Distance": atr_distance,
            "Profit Risk Ratio": p_r_ratio
        }
        colors = ["g", "r", "orange", "dodgerblue", "darkorchid", "teal"]

        # Trades figures
        for color, (param, values) in zip(colors, param_dict.items()):
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(bottom=0.1, left=0.08, right=0.95, top=0.95)

            ax.set_axisbelow(True)
            ax.grid(which='major', axis='y', color='0.5')
            ax.grid(which='minor', axis='y', ls='--')
            ax.scatter(values, df["Trades"], c=color, s=8)
            ax.set_xlabel(param)
            ax.set_ylabel("Trades")

            fig.savefig(
                os.path.join(
                    self.results_path,
                    self.opt_name,
                    f"{param.replace(' ', '_')}_Trades.png"
                ),
                dpi=300
            )
            plt.close(fig)

        # Win rate figures
        for color, (param, values) in zip(colors, param_dict.items()):
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111)
            plt.subplots_adjust(bottom=0.1, left=0.08, right=0.95, top=0.95)

            ax.set_axisbelow(True)
            ax.grid(which='major', axis='y', color='0.5')
            ax.grid(which='minor', axis='y', ls='--')
            ax.scatter(values, df["Win rate"], c=color, s=8)
            ax.set_xlabel(param)
            ax.set_ylabel("Win rate")

            fig.savefig(
                os.path.join(
                    self.results_path,
                    self.opt_name,
                    f"{param.replace(' ', '_')}_Win_rate.png"
                ),
                dpi=300
            )
            plt.close(fig)
