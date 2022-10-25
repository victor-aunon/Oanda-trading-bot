from datetime import datetime
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

TimeFrameType = TypedDict(
    "TimeFrameType",
    {
        "timeframe": str,
        "compression": int,
        "interval": str
    }
)


ConfigType = TypedDict(
    "ConfigType",
    {
        "results_path": str,
        "instruments": List[str],
        "cash": float,
        "risk": float,
        "account_currency": str,
        "language": Union[Literal["ES-ES"], Literal["EN-US"]],
        "timeframes": List[TimeFrameType],
        "strategy_params": StrategyParamsType,
        "profit_risk_ratio": float,
        "debug": bool,
        "testing": bool,
        "testing_date": datetime,
        "testing_directory": str,
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
        "telegram_report_frequency": Literal["Trade", "Daily", "Weekly"],
        "telegram_report_hour": int,
        "tts": bool
    },
    total=False,
)
