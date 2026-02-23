# API Documentation

Base URL: `http://localhost:8000`

FastAPI interactive docs:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Authentication
Currently uses a test user. Authentication is planned.

## Endpoints

### Health

```http
GET /ping
```

Response:
```json
{"status": "ok"}
```

### Listings

```http
GET /listings?skip=0&limit=100
```

Response: list of `PropertyListing` objects.

```http
GET /listings/{id}
```

Response: a single `PropertyListing`.

```http
GET /listings/{id}/history
```

Response: list of listing change events (price drops, status changes, etc.).

```http
GET /changes?since=2025-12-01T00:00:00Z&event_types=price_drop,status_change
```

Response: recent events across listings.

### Matches

```http
GET /matches/test-user
```

Response: list of `PropertyListing` objects with match fields:
- `match_score`
- `match_narrative`
- `match_reasons`
- `match_tradeoff`
- `feature_scores`

Notes:
- Scoring runs at request time (read-time scoring).
- If text intelligence is enabled (`OPENAI_TEXT_MAX_LISTINGS>0`) this endpoint may make best-effort external LLM calls to improve explainability fields (`top_positives`, `key_tradeoff`, `why_now`). OpenAI is used when configured; DeepInfra can be configured as a fallback.

### Criteria

```http
GET /criteria/test-user
POST /criteria/test-user
```

Fields include:
- `price_soft_max` (preferred cap)
- `price_max` (hard cap)
- `preferred_neighborhoods`
- `avoid_neighborhoods`
- `neighborhood_mode` (`strict` or `boost`)
- `recency_mode` (`fresh`, `balanced`, `hidden_gems`)

### Ingestion

```http
POST /admin/ingestion/run
GET /ingestion/status
```

### Admin Utilities

```http
POST /admin/migrate
POST /admin/migrate/stamp/{revision}

POST /admin/scraper/run
GET  /admin/scraper/status

GET  /admin/ingestion/last-run
```

### Scouts

```http
POST /scouts/
POST /scouts/{id}/run
GET /scouts/
GET /scouts/{id}/matches
```

### Users (Weight Learning)

```http
GET    /users/{id}/weights
GET    /users/{id}/weights/summary
POST   /users/{id}/weights/recalculate
DELETE /users/{id}/weights
```
