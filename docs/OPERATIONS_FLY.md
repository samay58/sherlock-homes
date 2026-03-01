# Fly.io Operations Runbook

Canonical production runbook for `sherlock-homes-nyc`.

## Current Known Good State (March 1, 2026)

- StreetEasy low-count incident is resolved in production.
- Verified production DB counts after a production-path StreetEasy run:
  - `streeteasy: 774`
  - `zillow: 459`
  - `total: 1233`
- If you need to re-validate, run the count query in "Verify listing counts by source" plus the StreetEasy-only diagnostic below.

## App Facts

- App: `sherlock-homes-nyc`
- Hostname: `https://sherlock-homes-nyc.fly.dev`
- Region: `ewr`
- Runtime: FastAPI + static frontend served by `app/main.py`
- Migrations: release command (`alembic upgrade head`)

## Standard Release Flow

```bash
# 1) Sync branch state
git pull --rebase

# 2) Validate locally
make test

# 3) Deploy
fly deploy -a sherlock-homes-nyc

# 4) Verify platform state
fly status -a sherlock-homes-nyc
fly releases -a sherlock-homes-nyc --image
```

## Ingestion Operations

### Trigger ingestion now

```bash
curl -X POST https://sherlock-homes-nyc.fly.dev/admin/ingestion/run
```

### Trigger StreetEasy-only ingestion diagnostics

Use this when Zillow runtime obscures StreetEasy debugging.

```bash
fly ssh console -a sherlock-homes-nyc -C "python - <<'PY'
import asyncio, time
from collections import Counter
from app.providers.streeteasy import StreetEasyProvider

async def main():
    p = StreetEasyProvider()
    t0 = time.time()
    items = await p.search_all_locations()
    counts = Counter(item.get('neighborhood') or 'Unknown' for item in items)
    print('street_easy_total', len(items))
    print('elapsed_seconds', round(time.time() - t0, 2))
    for hood, count in counts.most_common():
        print(f'{hood}: {count}')
    await p.close()

asyncio.run(main())
PY"
```

### Check ingestion status endpoint

```bash
curl https://sherlock-homes-nyc.fly.dev/ingestion/status
```

Important:
- `ingestion/status` and `admin/ingestion/last-run` come from in-memory app state.
- A machine restart can reset those fields.
- Running ingestion from a one-off external Python process (for debugging) does not update API process in-memory status.
- For source-of-truth verification, check logs and actual listing counts by source.

### Verify listing counts by source

```bash
fly ssh console -a sherlock-homes-nyc -C "python - <<'PY'
from app.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as db:
    total = db.execute(text('select count(*) from property_listings')).scalar()
    rows = db.execute(text('select source, count(*) from property_listings group by source order by source')).fetchall()
print('total', total)
for source, count in rows:
    print(source, count)
PY
"
```

## StreetEasy Low-Count Incident Playbook

Use this when StreetEasy drops to suspiciously low counts (for example ~12).

1. Confirm deployed release and image.
2. Trigger one manual ingestion.
3. Inspect logs for StreetEasy per-neighborhood page counts.
4. Compare source counts before vs after ingestion.
5. Verify gate: StreetEasy count is at least 3x baseline and at least 50 unique listings.

Useful log filter:

```bash
fly logs -a sherlock-homes-nyc --no-tail \
  | rg "StreetEasy|Starting ingestion|upserted|summary|detail call"
```

## StreetEasy Runtime Tunables

StreetEasy now has provider-specific bounds to prevent long-tail hangs from blocking upserts:

- `STREETEASY_REQUEST_TIMEOUT_SECONDS` (default `45`)
- `STREETEASY_REQUEST_RETRIES` (default `1`)
- `STREETEASY_MAX_DETAIL_CALLS` (default `80`)
- `STREETEASY_LOCATION_CONCURRENCY` (default `4`)
- `STREETEASY_MAX_PAGES` (default `5`)

These work alongside global ingestion controls:

- `INGESTION_PROVIDER_TIMEOUT_SECONDS`
- `INGESTION_DETAIL_CONCURRENCY`
- `INGESTION_DETAIL_REQUEST_TIMEOUT_SECONDS`

## Scheduler Reliability

`fly.toml` uses:
- `auto_stop_machines = 'stop'`
- `min_machines_running = 1`

This keeps one machine warm so APScheduler can run periodic ingestion.

## Rollback

1. Find previous successful release image.
2. Redeploy the prior image or revert commit and redeploy.
3. Re-run one ingestion and re-check source counts.

```bash
fly releases -a sherlock-homes-nyc --image
```
