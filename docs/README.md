# Docs Index

This folder is the source of truth for Home Hog (Sherlock Homes) documentation.

## Start Here

- `../README.md`: what the product is, how to run it
- `DEVELOPMENT.md`: local + Docker workflows, troubleshooting
- `API.md`: API endpoints (manual reference; FastAPI also serves `/docs`)
- `OPERATIONS_FLY.md`: production deploy/ingestion runbook (canonical)
- `ARCHITECTURE.md`: current codebase map + ingestion/scoring flow

## Architecture And Scoring

- `SCORING_ENGINE_SPEC.md`: scoring rubric/explainability design doc (may lag live config)
- `SCORING_DEEP_DIVE_2026-02-22.md`: point-in-time diagnostics snapshot (historical)
- `../config/user_criteria.yaml` / `../config/nyc_rental_criteria.yaml`: scoring configuration (selected via `BUYER_CRITERIA_PATH`)

Current production scoring source of truth:
- `../config/nyc_rental_criteria.yaml` (NYC rental profile)

## History (Archive)

Historical documents live in `archive/` and are not guaranteed to reflect the current code.

- `archive/PROJECT_HISTORY.md`: phase tracker (archived, unmaintained)
- `archive/CHANGELOG.md`: changelog (archived, unmaintained)
- `archive/SESSION_PROGRESS.md`: prior session log (archived)
- `archive/ai/`: historical agent prompts and reviews (archived)
