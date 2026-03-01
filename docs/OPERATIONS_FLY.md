# Fly.io Operations Runbook

Canonical production runbook for `sherlock-homes-nyc`.

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

### Check ingestion status endpoint

```bash
curl https://sherlock-homes-nyc.fly.dev/ingestion/status
```

Important:
- `ingestion/status` and `admin/ingestion/last-run` come from in-memory app state.
- A machine restart can reset those fields.
- For source-of-truth verification, check logs and actual listing counts by source.

### Verify listing counts by source

```bash
curl -sS 'https://sherlock-homes-nyc.fly.dev/listings?limit=500' \
  | python3 - <<'PY'
import json,sys
from collections import Counter
arr=json.load(sys.stdin)
print("total", len(arr))
print("by_source", dict(sorted(Counter((x.get("source") or "unknown") for x in arr).items())))
PY
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
