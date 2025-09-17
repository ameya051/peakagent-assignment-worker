from datetime import date
from typing import List

from sqlalchemy import select, desc

from app.db import SessionLocal
from app.models import EodPrice, DailyRecommendation


def get_last_n_days(symbol: str, n: int) -> List[EodPrice]:
    with SessionLocal() as session:
        q = (
            select(EodPrice)
            .where(EodPrice.symbol == symbol)
            .order_by(desc(EodPrice.trade_date))
            .limit(n)
        )
    return list(session.scalars(q).all())


def upsert_eod_from_payload(symbol: str, payload: dict) -> bool:
    """Insert EOD row if not already present for date. Returns True if inserted, False if existed."""
    trade_date = date.fromisoformat(payload["date"])  # may raise ValueError
    with SessionLocal() as session:
        existing = session.execute(
            select(EodPrice.id).where(EodPrice.trade_date == trade_date)
        ).first()
        if existing:
            return False
        row = EodPrice(
            symbol=symbol,
            trade_date=trade_date,
            open=payload.get("open"),
            high=payload.get("high"),
            low=payload.get("low"),
            close=payload.get("close"),
            vwap=payload.get("adjClose") or payload.get("vwap"),
            volume=payload.get("volume"),
            change_abs=payload.get("change") or payload.get("changeOverTime"),
            change_percent=payload.get("changePercent"),
        )
        session.add(row)
        session.commit()
        return True


def save_daily_recommendation(symbol: str, trade_date: date, model_name: str, content: dict) -> bool:
    """Insert a daily recommendation with flattened fields. Returns True if inserted, False if duplicate."""
    with SessionLocal() as session:
        exists = session.execute(
            select(DailyRecommendation.id).where(
                (DailyRecommendation.symbol == symbol)
                & (DailyRecommendation.trade_date == trade_date)
                & (DailyRecommendation.model_name == model_name)
            )
        ).first()
        if exists:
            return False
        rec = DailyRecommendation(
            symbol=symbol,
            trade_date=trade_date,
            model_name=model_name,
            recommendation=content.get("recommendation"),
            rationale=content.get("rationale"),
            change_percent=content.get("change_percent"),
            window_days=content.get("window_days"),
        )
        session.add(rec)
        session.commit()
        return True
