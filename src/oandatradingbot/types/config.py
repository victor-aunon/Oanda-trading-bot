from typing import List, Literal, Union
from typing_extensions import TypedDict

MacdFastEmaType = TypedDict(
    "MacdFastEmaType", {"start": int, "end": int, "step": int}
)


StrategyParamsType = TypedDict(
    "StrategyParamsType",
    {
        "macd_fast_ema": Union[MacdFastEmaType, int],
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
        "language": Union[Literal["ES-ES"], Literal["EN-US"]],
        "timeframe_num": int,
        "timeframe": str,
        "interval": str,
        "strategy_params": StrategyParamsType,
        "debug": bool,
        "testing": bool,
        "optimize": bool,
        "opt_name": str,
        "database_uri": str,
        "account_type": Literal["Demo", "Brokerage"],
        "practice": bool,
        "oanda_token": str,
        "oanda_account_id": str,
        "language_tts": Union[Literal["ES-ES"], Literal["EN-US"]],
        "telegram_token": str,
        "telegram_chat_id": str,
        "tts": bool
    },
    total=False,
)
