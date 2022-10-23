# Libraries
from datetime import datetime
import os
import sys
from typing import Dict, List, Union

# Packages
import numpy as np
import pandas as pd
import xlsxwriter

# Locals
from oandatradingbot.types.config import ConfigType
from oandatradingbot.types.trade import TradeType


class SaveResults:
    def __init__(self, config: ConfigType, profit_risk_ratio: float) -> None:
        self.path = config["results_path"]
        self.profit_risk_ratio = profit_risk_ratio
        self.account_currency = config["account_currency"]

    def _create_optimization_folder(self, optimization_name: str) -> None:
        try:
            os.mkdir(os.path.join(self.path, optimization_name, "temp"))
        except OSError as e:
            if e.errno == 17:
                pass
            else:
                print(e)
                sys.exit()

    def save_optimization_results(
        self,
        optimization_name: str,
        strategy_name: str,
        instruments: List[str],
        trades: Dict[str, List[TradeType]]
    ) -> None:
        self._create_optimization_folder(optimization_name)

        pl_stats: dict[str, Union[int, float]] = {
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
        }
        for instrument in instruments:
            if len(trades[instrument]) == 0:
                continue
            pr_long = [
                tr["PL"] for tr in trades[instrument]
                if (tr["PL"] > 0) and (tr["Operation"] == "BUY")
            ]
            pr_short = [
                tr["PL"] for tr in trades[instrument]
                if (tr["PL"] > 0) and (tr["Operation"] == "SELL")
            ]
            lo_long = [
                tr["PL"] for tr in trades[instrument]
                if (tr["PL"] < 0) and (tr["Operation"] == "BUY")
            ]
            lo_short = [
                tr["PL"] for tr in trades[instrument]
                if (tr["PL"] < 0) and (tr["Operation"] == "SELL")
            ]
            pl_stats["Won"] += (len(pr_long) + len(pr_short))
            pl_stats[f"Won {instrument}"] = (len(pr_long) + len(pr_short))
            pl_stats["Lost"] += (len(lo_long) + len(lo_short))
            pl_stats[f"Lost {instrument}"] = (len(lo_long) + len(lo_short))
            pl_stats["Long"] += (len(pr_long) + len(lo_long))
            pl_stats["Long won"] += len(pr_long)
            pl_stats["Long lost"] += len(lo_long)
            pl_stats["Short"] += (len(pr_short) + len(lo_short))
            pl_stats["Short won"] += len(pr_short)
            pl_stats["Short lost"] += len(lo_short)
            pl_stats[f"Trades {instrument}"] = pl_stats[f"Won {instrument}"] \
                + pl_stats[f"Lost {instrument}"]
            pl_stats[f"Returns {instrument}"] = (sum(pr_long) + sum(pr_short))
            pl_stats[f"Returns {instrument}"] += (sum(lo_long) + sum(lo_short))
            pl_stats["Total profit"] += (sum(pr_long) + sum(pr_short))
            pl_stats["Total loss"] -= (sum(lo_long) + sum(lo_short))
        pl_stats["Trades"] = pl_stats["Won"] + pl_stats["Lost"]
        r_multiples_neg = np.array([-1] * pl_stats["Lost"])  # type: ignore
        r_multiples_pos = np.array(  # type: ignore
            [self.profit_risk_ratio] * pl_stats["Won"]  # type: ignore
        )
        r_multiples = np.concatenate(
            (r_multiples_pos, r_multiples_neg), axis=None
        )
        pl_stats["SQN"] = np.mean(r_multiples) / np.std(r_multiples) \
            * np.sqrt(r_multiples.size)

        # Print strategy brief results
        print(
            f"{strategy_name} --> Won: {pl_stats['Won']} - Lost: "
            f"{pl_stats['Lost']} - Win rate: "
            f"{(pl_stats['Won'] / (pl_stats['Won'] + pl_stats['Lost'])):.3f} "
            f"- Returns: "
            f"{(pl_stats['Total profit'] - pl_stats['Total loss']):.2f} "
            f"{self.account_currency}"
        )

        # Save a temporary summary file
        df = pd.DataFrame([pl_stats])
        df.to_csv(os.path.join(
                self.path, optimization_name, "temp", f"{strategy_name}.csv"
            ), sep=";"
        )

    def save_backtest_results(
        self,
        strategy_name: str,
        instrument: str,
        trades: Dict[str, List[TradeType]]
    ) -> str:
        # Create xlsxwriter workbook
        summary_file = os.path.join(
            self.path,
            (
                f"Backtest_{instrument}_{strategy_name}_"
                f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')}"
                ".xlsx"
            )
        )
        workbook = xlsxwriter.Workbook(summary_file)
        worksheet = workbook.add_worksheet("Trades")

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
            0, 0,
            len(trades[instrument]),
            len(trades[instrument][0].keys()) - 1,
            {
                "columns": [{"header": col} for col
                            in trades[instrument][0].keys()]
            }
        )
        for i, trade in enumerate(trades[instrument]):
            worksheet.write_row(
                i + 1, 0, trade.values(),
                cell_format=successful if trade["PL"] > 0
                else unsuccessful
            )

        workbook.close()
        return summary_file
