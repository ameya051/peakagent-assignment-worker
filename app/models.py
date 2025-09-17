from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class EodPrice(Base):
    __tablename__ = "eod_prices"

    # Surrogate primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Natural keys and data
    symbol = Column(String, nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(Numeric(20, 8), nullable=False)
    high = Column(Numeric(20, 8), nullable=False)
    low = Column(Numeric(20, 8), nullable=False)
    close = Column(Numeric(20, 8), nullable=False)
    vwap = Column(Numeric(20, 8))
    volume = Column(BigInteger)
    change_abs = Column(Numeric(20, 8))
    change_percent = Column(Numeric(14, 12))
    ingested_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class DailyRecommendation(Base):
    __tablename__ = "daily_recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    trade_date = Column(Date, nullable=False)
    model_name = Column(String, nullable=False)
    # Flattened LLM output fields
    recommendation = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    change_percent = Column(Numeric(14, 12), nullable=False)
    window_days = Column(BigInteger, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "symbol", "trade_date", "model_name", name="uq_daily_rec_symbol_date_model"
        ),
    )
