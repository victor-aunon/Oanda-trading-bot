# Libraries
from datetime import datetime
from typing import List, Union

# Packages
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

# Locals
from oandatradingbot.types.trade import TradeDbType
from oandatradingbot.repository.base import Base
from oandatradingbot.repository.trade import Trade


class Repository:
    def __init__(self, db_uri: str) -> None:
        self.db_uri = db_uri

    def start_session(self) -> Session:
        try:
            engine = create_engine(self.db_uri)
            Base.metadata.create_all(engine)
            return Session(bind=engine)
        except Exception as e:
            raise SystemExit(e)

    def save_trade(self, trade: TradeDbType) -> None:
        with self.start_session() as session:
            trade_db = Trade(**trade)
            session.add(trade_db)
            session.commit()

    def get_trade(self, id: int) -> Union[Trade, None]:
        session = self.start_session()
        trade = session.query(Trade).filter(Trade.id == id).first()
        session.close()
        return trade  # type: ignore[no-any-return]

    def remove_trade(self, id: int) -> None:
        trade = self.get_trade(id)

        if trade is None:
            return
        with self.start_session() as session:
            session.delete(trade)
            session.commit()

    def get_day_trades(self, day: datetime) -> List[Trade]:
        session = self.start_session()
        trades = session.query(Trade).filter(
                func.DATE(Trade.exit_time) == day.date()
            ).all()
        session.close()
        return trades  # type: ignore[no-any-return]

    def get_week_trades(
        self, monday: datetime, friday: datetime
    ) -> List[Trade]:
        session = self.start_session()
        trades = session.query(Trade).filter(
            Trade.exit_time >= monday,
            Trade.exit_time <= friday
        ).all()
        session.close()
        return trades  # type: ignore[no-any-return]
