from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta


Base: DeclarativeMeta = declarative_base()


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    pair = Column(String(30))
    account = Column(String(20))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    duration = Column(Integer)
    operation = Column(String(10))
    size = Column(Float)
    entry_price = Column(Float)
    exit_price = Column(Float)
    trade_pips = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    canceled = Column(Boolean)
    profit = Column(Float)

    def __repr__(self) -> str:
        return (
            f"Trade(id={self.id}, type={self.operation}, "
            f"entry={self.entry_time}, exit={self.exit_time}, "
            f"duration={self.duration // 60} minutes, size={self.size}, "
            f"{'profit' if self.profit >= 0 else 'loss'}={self.profit})"
        )
