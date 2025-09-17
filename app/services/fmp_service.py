import os
from datetime import date
import requests


def fetch_eod_for_date(symbol: str, target_date: date) -> dict:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        raise RuntimeError("missing_api_key: Set FMP_API_KEY in environment")

    url = (
        "https://financialmodelingprep.com/stable/historical-price-eod/full"
        f"?symbol={symbol}&from={target_date:%Y-%m-%d}&to={target_date:%Y-%m-%d}&apikey="
        + api_key
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 502
        raise RuntimeError(f"upstream_http_error:{status}:{e}")
    except requests.RequestException as e:
        raise RuntimeError(f"upstream_request_failed:{e}")

    try:
        payload = resp.json()
    except ValueError:
        raise RuntimeError("invalid_upstream_json")

    if not isinstance(payload, list) or not payload:
        raise RuntimeError("invalid_upstream_payload: expected a non-empty list")

    r = payload[0]
    ds = r.get("date")
    if not isinstance(ds, str):
        raise RuntimeError("invalid_upstream_date: missing or invalid date")

    try:
        date.fromisoformat(ds)
    except ValueError:
        raise RuntimeError("invalid_upstream_date: not ISO YYYY-MM-DD")

    return r
