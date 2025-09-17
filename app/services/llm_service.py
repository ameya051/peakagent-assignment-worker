from __future__ import annotations

import json
import os
from typing import List, Dict, Any


def analyze_with_gemini(
    data: List[Dict[str, Any]], model: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """Use Gemini to analyze N days of EOD objects and return a strict JSON recommendation.

    Input data is an array of objects like:
    {
      "change": 102.93,
      "changePercent": 0.08920874,
      "close": 115484,
      "date": "2025-09-16",
      "high": 116037.57,
      "low": 114951.5,
      "open": 115381.07,
      "symbol": "BTCUSD",
      "volume": 197138020,
      "vwap": 115491.02
    }
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "missing_gemini_api_key: set GOOGLE_API_KEY or GEMINI_API_KEY"
        )

    try:
        from google import genai  # type: ignore[import-not-found]
        from google.genai import types
    except Exception:
        raise RuntimeError("missing_dependency: install google-genai")

    client = genai.Client(api_key=api_key)

    system_prompt = (
        "Role: You are a concise markets analyst.\n\n"
        "Task: Given the last N days of EOD candles (one symbol), return ONLY a compact JSON with exactly these keys:\n"
        "- recommendation: one of [\"buy\",\"sell\",\"hold\"]\n"
        "- rationale: short, plain-English reason (<= 50 words), grounded ONLY in the provided data\n"
        "- change_percent: number (float) = ((last_close - first_close) / first_close)\n"
        "- window_days: integer = N\n\n"
        "Rules:\n"
        "- Use only the input array; no external data, no speculation, no disclaimers.\n"
        "- Consider trend (closes), momentum (delta close), volatility ((max_high - min_low)/last_close), and volume vs. average.\n"
        "- If N < 2 or key info is missing, return: recommendation=\"hold\", rationale=\"insufficient_data\", change_percent=0, window_days=N.\n"
        "- Output must be valid JSON, no extra keys, no markdown, no text around it.\n"
        "- Numbers must be JSON numbers (not strings). Round change_percent to 6 decimals.\n"
    )

    user_content = (
        "Analyze the following EOD data array and apply the system rules. Return ONLY the JSON object.\n\n"
        f"Data (oldest → newest), N = {len(data)}:\n"
        f"{json.dumps(data)}"
    )

    resp = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
        contents=user_content,
    )
    text = resp.text
    if not text:
        raise RuntimeError("invalid_llm_response: empty")
    try:
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(f"invalid_llm_response: expected JSON: {e}")
