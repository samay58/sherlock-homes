# API Documentation

Base URL: `http://localhost:8000`

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

### Scouts

```http
POST /scouts/
POST /scouts/{id}/run
GET /scouts/
GET /scouts/{id}/matches
```
