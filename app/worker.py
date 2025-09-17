#!/usr/bin/env python3
"""Daily job: fetch today's EOD, persist, analyze last 7 days, store recommendation."""
from __future__ import annotations

import os
import sys
from datetime import date
from typing import cast

from dotenv import load_dotenv

# Ensure env is loaded (DATABASE_URL, FMP_API_KEY)
load_dotenv()

from app.services.fmp_service import fetch_eod_for_date
from app.services.repository import (
    upsert_eod_from_payload,
    get_last_n_days,
    save_daily_recommendation,
)
from app.services.llm_service import analyze_with_gemini


def main():
    symbol = os.getenv("SYMBOL", "BTCUSD")
    # Prefer explicit GEMINI_MODEL, fall back to MODEL_NAME, default to gemini-1.5-flash
    model_name = os.getenv("GEMINI_MODEL", os.getenv("MODEL_NAME", "gemini-2.5-flash"))

    today = date.today()

    # 1) Fetch today's EOD from FMP and persist if new
    try:
        payload = fetch_eod_for_date(symbol, today)
        print(f"Fetched EOD for {symbol} on {today.isoformat()}: {payload}")
    except Exception as e:
        print(f"ERROR: fetching EOD failed: {e}")
        return 2

    try:
        inserted = upsert_eod_from_payload(symbol, payload)
        action = "inserted" if inserted else "exists"
        print(f"EOD for {today.isoformat()} {action}")
    except Exception as e:
        print(f"ERROR: upserting EOD failed: {e}")
        return 3

    # 2) Load last 7 days (including today if present)
    prices = get_last_n_days(symbol, 7)
    if not prices:
        print("WARN: No price data available for analysis")
        return 4

    # Build array of objects for LLM (oldest -> newest)
    def to_float(x):
        return float(x) if x is not None else None

    data = [
        {
            "change": to_float(p.change_abs),
            "changePercent": to_float(p.change_percent),
            "close": to_float(p.close),
            "date": p.trade_date.isoformat(),
            "high": to_float(p.high),
            "low": to_float(p.low),
            "open": to_float(p.open),
            "symbol": p.symbol,
            "volume": p.volume,
            "vwap": to_float(p.vwap),
        }
        for p in reversed(prices)
    ]
    print("Recent data retrieved from DB")

    # 3) Analyze with Gemini and save recommendation
    try:
        analysis = analyze_with_gemini(data, model=model_name)
    except Exception as e:
        print(f"ERROR: LLM analysis failed: {e}")
        return 6

    print(f"LLM analysis result: {analysis}")

    trade_date = cast(
        date, prices[0].trade_date
    )  # latest date is first due to desc ordering
    try:
        saved = save_daily_recommendation(symbol, trade_date, model_name, analysis)
        msg = "saved" if saved else "duplicate (skipped)"
        print(
            f"Recommendation for {symbol} {trade_date.isoformat()} {msg}: {analysis['recommendation']}"
        )
    except Exception as e:
        print(f"ERROR: saving recommendation failed: {e}")
        return 5

    return 0


if __name__ == "__main__":
    sys.exit(main())
