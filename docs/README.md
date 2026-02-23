# Docs Index

This folder is the source of truth for Home Hog (Sherlock Homes) documentation.

## Start Here

- `../README.md`: what the product is, how to run it
- `DEVELOPMENT.md`: local + Docker workflows, troubleshooting
- `API.md`: API endpoints (manual reference; FastAPI also serves `/docs`)

## Architecture And Scoring

- `ARCHITECTURE.md`: codebase map + data flow
- `SCORING_ENGINE_SPEC.md`: scoring rubric and explainability requirements
- `SCORING_DEEP_DIVE_2026-02-22.md`: runtime diagnostics snapshot (NYC rental)
- `../config/user_criteria.yaml` / `../config/nyc_rental_criteria.yaml`: scoring configuration (selected via `BUYER_CRITERIA_PATH`)

## History (Archive)

Historical documents live in `archive/` and are not guaranteed to reflect the current code.

- `archive/PROJECT_HISTORY.md`: phase tracker (archived, unmaintained)
- `archive/CHANGELOG.md`: changelog (archived, unmaintained)
- `archive/SESSION_PROGRESS.md`: prior session log (archived)
- `archive/ai/`: historical agent prompts and reviews (archived)
