# Primalabs OA

FastAPI app for the Primalabs take-home: spin up model deployments, fake completions with token metering, and a usage endpoint for billing.

## Run it

Python 3.11+. From the repo root:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use `python -m uvicorn` so you actually hit the venv. If you get `ModuleNotFoundError: pydantic_settings`, you're probably running a global uvicorn — activate the venv and try again.

API docs (FastAPI auto-generates these):

- Swagger: http://localhost:8000/docs
- Raw schema: http://localhost:8000/openapi.json

Tests:

```bash
pytest -v
```

Optional env vars:

- `APP_DATABASE_URL` — default `sqlite:///./primalabs.db`
- `APP_PROVISIONING_DELAY_SECONDS` — fixed delay; tests set `0.2`
- `APP_PROVISIONING_DELAY_MIN` / `APP_PROVISIONING_DELAY_MAX` — default 9–10s random wait before ready
- `APP_RATE_LIMIT_PER_MINUTE` — default 100 per API key

Unless you override with `PROVISIONING_DELAY_SECONDS`, provisioning sleeps a random time between 9 and 10 seconds.

## Data model

Two tables.

**deployments** — one row per deployment. `model` is `model-a` or `model-b`. Status goes `provisioning` → `ready` → `terminated`. `api_key` and `endpoint_url` only show up on GET once status is `ready`.

**usage_events** — append-only log, one row per completion. Stores `api_key`, `deployment_id`, `model`, token counts, and `timestamp`. I denormalized `model` onto each event so usage queries don't have to join deployments every time.

Each deployment gets its own API key (1:1). Keys are unique.

## Scaling metering to ~10k req/s

Right now every completion writes to SQLite on the request path. That won't hold at 10k RPS.

What I'd do in production:

- After auth + rate limit, push a small event to Kafka (or similar) and return the mock response. Don't block on the DB write.
- Consumers batch into ClickHouse / BigQuery (or rollups in Redis/Postgres). Partition by `api_key` so workers scale out.
- Rate limiting moves to Redis (sliding window per key). The in-memory limiter here is fine for a single process.
- `/usage` reads from pre-aggregated daily/hourly tables, not a full scan of raw events. Keep raw events around for disputes, with a TTL.
- Watch queue lag, use idempotent event IDs for at-least-once delivery.

Billing can be a few seconds behind; that's normal for usage-based products.

## If I had more time

- Redis for rate limits (and maybe provisioning locks across workers)
- Idempotency keys on completions
- Alembic migrations instead of `create_all`
- Request logging with `deployment_id`, basic metrics
- Paginated `/usage`, validate the api_key exists before returning empty totals
- A real analytics store for heavy usage queries

## Trade-offs and assumptions

I kept it simple on purpose:

- SQLite + sync SQLAlchemy — easy to run and grade, not built for horizontal scale
- `BackgroundTasks` for provisioning — good enough to fake the 9–10s delay without Celery
- In-memory rate limiter — works for one worker; multiple uvicorn workers would need Redis
- Append-only usage log — correct and easy to reason about; you'd roll up in prod
- 409 when deployment isn't ready — same handling for provisioning and terminated
- Random `output_tokens` per spec; tests patch `random` so billing assertions are stable

Assumptions I made where the spec was silent:

- Missing deployment → 404
- Usage `from` / `to` are inclusive on `timestamp`
- Timestamps stored as timezone-aware UTC
- Wrong key for another deployment → 403; unknown key → 401

## AI assistance

Most of this I wrote myself. I used Cursor on some parts (early file layout, boilerplate, README edits). The tests are mine too I wrote them, with AI helping here and there (e.g. fixture setup, assertion ideas). Design, error codes, and rate limiting are my calls. I ran `pytest` locally before submitting.

## Layout

```
app/
  main.py, config.py, database.py
  models/, schemas/, routers/, services/
tests/
  test_deployment_lifecycle.py
  test_metering_and_usage.py
```

## Time spent

~100 minutes
