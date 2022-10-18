from typing import List, Literal, Union
from typing_extensions import TypedDict

MacdFastEmaType = TypedDict(
    "MacdFastEmaType", {"start": int, "end": int, "step": int}
)


StrategyParamsType = TypedDict(
    "StrategyParamsType",
    {
        "macd_fast_ema": MacdFastEmaType,
        "macd_slow_ema": int,
        "macd_signal_ema": int,
        "ema_period": int,
        "atr_period": int,
        "atr_distance": float,
        "profit_risk_ratio": float,
    },
)


ConfigType = TypedDict(
    "ConfigType",
    {
        "results_path": str,
        "pairs": List[str],
        "cash": float,
        "risk": float,
        "account_currency": str,
        "language": Union[Literal["ES-ES"], Literal["EN-EN"]],
        "timeframe_num": int,
        "timeframe": str,
        "interval": str,
        "strategy_params": StrategyParamsType,
        "debug": bool,
        "optimize": bool,
        "opt_name": str
    },
    total=False,
)
