# PeakAgent Worker

A lightweight daily worker that:

1. Fetches the symbol's end-of-day (EOD) price from Financial Modeling Prep (FMP)
2. Upserts it into Postgres via SQLAlchemy models
3. Loads the last 7 days of prices
4. Calls Gemini to produce a buy/sell/hold recommendation with rationale
5. Saves the recommendation for the day

The worker is designed to run once per day (via a scheduler or platform cron) and is Railway-ready.

## Folder structure

```
.
├── Procfile                 # Declares the `worker` process (python -m app.worker)
├── requirements.txt         # Python dependencies for the worker runtime
├── app/
│   ├── __init__.py          # Package init
│   ├── db.py                # SQLAlchemy engine/session setup
│   ├── models.py            # SQLAlchemy models (EodPrice, DailyRecommendation)
│   ├── worker.py            # Entry point; orchestrates fetch -> persist -> analyze -> save
│   └── services/
│       ├── __init__.py
│       ├── fmp_service.py   # Fetch EOD data from FMP API
│       ├── llm_service.py   # Analyze recent prices using Gemini, return strict JSON
│       └── repository.py    # DB helpers for CRUD operations
```

## How it works

- `app/worker.py` is the entrypoint. It:
  - Reads environment variables and defaults (e.g., `SYMBOL=BTCUSD`)
  - Fetches the current day's EOD candle using `fmp_service.fetch_eod_for_date()`
  - Upserts the row using `repository.upsert_eod_from_payload()`
  - Loads the last 7 days using `repository.get_last_n_days()`
  - Sends the series to `llm_service.analyze_with_gemini()` which returns JSON like:
    ```json
    {
      "recommendation": "buy|sell|hold",
      "rationale": "short reason",
      "change_percent": 0.012345,
      "window_days": 7
    }
    ```
  - Persists it using `repository.save_daily_recommendation()`

## Environment variables

Required:
- DATABASE_URL: Postgres URL. Examples:
  - postgresql+psycopg://user:pass@host:5432/db
  - postgres://user:pass@host:5432/db (auto-rewritten to psycopg driver)
- FMP_API_KEY: API key for Financial Modeling Prep
- GOOGLE_API_KEY or GEMINI_API_KEY: API key for Gemini (google-genai)

Optional:
- SYMBOL: trading pair or ticker to track (default: BTCUSD)
- GEMINI_MODEL: Gemini model name to use (default: gemini-2.5-flash)
- MODEL_NAME: legacy/alt env for model name; only used if GEMINI_MODEL is unset

A local `.env` file is supported via `python-dotenv`.

## Setup (local)

1. Create a virtual environment and install deps
2. Set environment variables (or create a `.env`)
3. Ensure your Postgres is reachable and has appropriate privileges

Run locally from the `worker` directory:

```bash
python -m app.worker
```

Return codes:
- 0: success
- 2: EOD fetch failure
- 3: DB upsert failure
- 4: no price data to analyze
- 5: saving recommendation failed
- 6: LLM analysis failed

## Deployment (Railway)

- The `Procfile` declares a `worker` process that runs: `python -m app.worker`
- Add environment variables in Railway → Variables
- Attach a Postgres database (Railway plugin) and expose its `DATABASE_URL`
- Configure a Railway Cron (or an external scheduler) to invoke the worker once per day

Notes:
- If using Railway Cron, set it to hit an endpoint or use a scheduled run process depending on your setup. Alternatively, run the worker continuously under an external scheduler.

## Models

- `EodPrice`: stores daily OHLCV and derived fields
- `DailyRecommendation`: stores one recommendation per (symbol, date, model). Uniqueness is enforced

## Dependencies

- requests, SQLAlchemy, psycopg, python-dotenv
- google-genai for Gemini client

If you prefer google-generativeai, adjust the code and requirements accordingly.

## Troubleshooting

- "missing_gemini_api_key": set `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- "missing_api_key": set `FMP_API_KEY`
- Connection issues: verify `DATABASE_URL` (driver prefix is auto-normalized)
- Invalid upstream payloads: FMP may occasionally return empty or malformed data for a date
