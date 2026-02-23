# Development

## Prerequisites

- Python 3.11 or 3.12 (spaCy wheels)
- Node.js 18+
- Docker + Docker Compose (optional)

## Local Development (No Docker)

Fastest feedback loop: SQLite + hot reload.

```bash
# Terminal 1 (API)
./run_local.sh

# Terminal 2 (frontend)
./run_frontend.sh
```

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### Local Data Conventions

- Local SQLite defaults to `sqlite:///./.local/sherlock.db`.
- If legacy DB files exist at `./sherlock.db` or `./homehog.db`, the backend will keep using them automatically.
- JSON export tooling writes to `.local/data_export.json`.

## Docker Development

Docker runs the API + Postgres + the frontend dev server.

```bash
cp .env.docker .env   # never commit real keys
make up
make migrate
```

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Common Commands

```bash
# Tests
make test   # uses .venv when present
# or: .venv/bin/python -m pytest -q

# Format + lint
make fmt
make lint

# Clean caches + local build outputs
make clean

# Reset local SQLite DB
./nuke_db.sh

# Export/import snapshot JSON (writes to .local/)
docker compose exec api python scripts/export_to_json.py
python scripts/import_from_json.py
```

## Local Smoke Test (End-to-End)

```bash
# Health
curl http://localhost:8000/ping

# Trigger ingestion
curl -X POST http://localhost:8000/admin/ingestion/run

# Check ingestion status
curl http://localhost:8000/ingestion/status

# Get matches for the test user
curl http://localhost:8000/matches/test-user
```

## Alerts (Optional)

Set these in `.env.local` if you want notifications:

```env
# iMessage (macOS relay)
IMESSAGE_ENABLED=false
IMESSAGE_TARGET=

# Email (SMTP)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=

# SMS fallback (Twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_TO_NUMBER=
```

Notes:
- iMessage requires a logged-in macOS session with Messages access.
- Email requires valid SMTP credentials.

## Troubleshooting

- **OpenAI 429s in `/matches`**: set `OPENAI_TEXT_MAX_LISTINGS=0` to disable text intelligence, or configure `DEEPINFRA_API_KEY` + `DEEPINFRA_TEXT_MODEL` to enable fallback.

- **Verify DeepInfra fallback is working**:
  1. Set `DEEPINFRA_API_KEY` in `.env.local`.
  2. Temporarily unset `OPENAI_API_KEY` (or leave it blank) and keep `OPENAI_TEXT_MAX_LISTINGS>0`.
  3. Restart `./run_local.sh` and call `GET /matches/test-user`.
  4. Confirm the API logs contain `Falling back to DeepInfra for text intelligence`.

- **SQLite `database is locked` during ingestion**: this usually means another process is holding a write transaction against the same SQLite file. Restart the API and re-run ingestion. The ingestion upsert path retries transient lock errors, but long-running requests that write (e.g. criteria creation) should commit promptly before making external calls.

- **bcrypt error on startup**: rebuild the venv (pins `bcrypt==3.2.2`).
  ```bash
  rm -rf .venv
  ./run_local.sh
  ```

### Frontend
- Use browser DevTools
- Add `console.log()` statements
- Use React Developer Tools extension

### Docker Logs
```bash
# All services
make logs

# Specific service
docker compose logs -f api
docker compose logs -f frontend
```

## Common Issues

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
docker compose ps
# Restart database
docker compose restart postgres
```

### Module Import Errors
```bash
# Recreate the backend venv + reinstall deps
rm -rf .venv
./run_local.sh

# Reinstall frontend deps
cd frontend && npm install
```

### Migration Conflicts
```bash
# Check current version
alembic current
# Stamp to head if needed
alembic stamp head
```
