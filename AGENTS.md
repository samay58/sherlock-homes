# Repository Guidelines

## Project Structure & Module Organization
- `app/` is the FastAPI backend. Key areas include `app/models/`, `app/services/`, and `app/routes/`.
- `frontend/` contains the SvelteKit app; main code lives under `frontend/src/`.
- `tests/` holds pytest tests for backend behavior.
- `scripts/` has one-off data tools (e.g., `scripts/import_from_json.py`).
- `migrations/` and `alembic.ini` manage schema changes.
- Top-level helpers: `run_local.sh`, `run_frontend.sh`, `nuke_db.sh`, `Makefile`.

## Build, Test, and Development Commands
- `./run_local.sh`: start the API locally (sets up venv, uses SQLite).
- `./run_frontend.sh`: start the frontend dev server (yarn).
- `make up` / `make dev`: Docker workflow.
- `make test` or `pytest -q`: run backend tests.
- `make fmt`: format Python and frontend code.
- `python -m app.scripts.analyze_visual_scores`: run visual scoring batch job.
- `python scripts/import_from_json.py`: import data export.
- `./nuke_db.sh`: reset the local database.

## Coding Style & Naming Conventions
- Python formatting uses Black and isort (`make fmt`).
- Indentation: 4 spaces in Python; follow existing formatting in `frontend/`.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Place new backend logic in `app/services/` and keep models in `app/models/`.

## Testing Guidelines
- Framework: pytest in `tests/`.
- Naming: `tests/test_*.py` and `test_*` functions.
- Run: `make test` or `pytest -q`; optional coverage via `pytest --cov=app --cov-report=html`.
- No enforced coverage threshold, but add tests for scoring, ingestion, and API changes.

## Configuration & Secrets
- Local overrides live in `.env.local`; defaults in `.env`.
- Set `DATABASE_URL` explicitly for local SQLite (e.g., `sqlite:///./homehog.db`).
- Keep API keys (ZenRows, Anthropic) out of commits.

## Commit & Pull Request Guidelines
- Commit history uses short descriptive summaries; no strict convention observed.
- PRs should include a concise summary, test commands run, and screenshots for UI changes.
- Call out any data or migration changes (new columns, backfills, or re-ingestion).

## Issue Tracking

This project uses **bd (beads)** for issue tracking.
Run `bd prime` for workflow context, or install hooks (`bd hooks install`) for auto-injection.

**Quick reference:**
- `bd ready` - Find unblocked work
- `bd create "Title" --type task --priority 2` - Create issue
- `bd close <id>` - Complete work
- `bd sync` - Sync with git (run at session end)

For full workflow details: `bd prime`

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
