# Worker Service

This folder contains a standalone worker for the daily EOD pipeline.
It can be deployed independently from the Flask web app.

## What it does
- Fetches today's EOD for `SYMBOL` from FMP
- Upserts into the shared Postgres database
- Loads the last 7 days
- Runs Gemini for a compact JSON recommendation
- Saves the recommendation into `daily_recommendations`

## Run locally

```bash
python -m worker.scripts.worker
```

Set these environment variables:
- DATABASE_URL (psycopg v3 style accepted or auto-normalized)
- FMP_API_KEY
- GOOGLE_API_KEY or GEMINI_API_KEY
- Optional: GEMINI_MODEL (default gemini-2.5-flash), SYMBOL (default BTCUSD)

## Deploy

- Use the `Procfile` in this folder: `worker: python -m worker.scripts.worker`
- On Railway/Heroku, create a new service using this folder as the root, or select the `worker` process type.
- Add a Schedule to run daily with command: `python -m worker.scripts.worker`

## Notes
- The worker uses its own `requirements.txt` and does not import from the main app package to keep isolation simple.
- It writes to the same database schema as the main app.
