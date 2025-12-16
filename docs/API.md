# API Documentation

Base URL: `http://localhost:8000`

## Authentication

Currently using test user. Authentication system planned for future release.

## Endpoints

### Health Check

```http
GET /ping
```

**Response**
```json
{
  "status": "ok"
}
```

### Listings

#### Get All Listings

```http
GET /listings
```

**Query Parameters**
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Maximum records to return (default: 20)
- `min_price` (number): Minimum price filter
- `max_price` (number): Maximum price filter
- `min_beds` (integer): Minimum bedrooms
- `min_baths` (number): Minimum bathrooms
- `min_sqft` (integer): Minimum square footage

**Response**
```json
{
  "listings": [
    {
      "id": "uuid",
      "address": "123 Main St, San Francisco, CA",
      "price": 1500000,
      "beds": 3,
      "baths": 2,
      "sqft": 1800,
      "photos": ["url1", "url2"],
      "natural_light_flag": true,
      "high_ceilings_flag": false,
      "outdoor_space_flag": true,
      "modern_kitchen_flag": true
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 20
}
```

#### Get Listing Details

```http
GET /listings/{listing_id}
```

**Response**
```json
{
  "id": "uuid",
  "zillow_id": "123456",
  "address": "123 Main St, San Francisco, CA",
  "price": 1500000,
  "beds": 3,
  "baths": 2,
  "sqft": 1800,
  "year_built": 1950,
  "lot_size": 3000,
  "property_type": "Single Family",
  "description": "Beautiful home with...",
  "photos": ["url1", "url2"],
  "natural_light_flag": true,
  "high_ceilings_flag": false,
  "outdoor_space_flag": true,
  "modern_kitchen_flag": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Criteria

#### Get User Criteria

```http
GET /criteria/test-user
```

**Response**
```json
{
  "id": "uuid",
  "user_id": "test-user",
  "min_price": 500000,
  "max_price": 2000000,
  "min_beds": 2,
  "min_baths": 1.5,
  "min_sqft": 1200,
  "natural_light_priority": true,
  "high_ceilings_priority": false,
  "outdoor_space_priority": true,
  "modern_kitchen_priority": true,
  "active": true
}
```

#### Update User Criteria

```http
POST /criteria/test-user
```

**Request Body**
```json
{
  "min_price": 500000,
  "max_price": 2000000,
  "min_beds": 2,
  "min_baths": 1.5,
  "min_sqft": 1200,
  "natural_light_priority": true,
  "high_ceilings_priority": false,
  "outdoor_space_priority": true,
  "modern_kitchen_priority": true
}
```

**Response**
```json
{
  "id": "uuid",
  "user_id": "test-user",
  "min_price": 500000,
  "max_price": 2000000,
  "min_beds": 2,
  "min_baths": 1.5,
  "min_sqft": 1200,
  "natural_light_priority": true,
  "high_ceilings_priority": false,
  "outdoor_space_priority": true,
  "modern_kitchen_priority": true,
  "active": true,
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Matches

#### Get Matched Listings

```http
GET /matches/test-user
```

**Query Parameters**
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Maximum records to return (default: 20)

**Response**
```json
{
  "matches": [
    {
      "listing": {
        "id": "uuid",
        "address": "123 Main St, San Francisco, CA",
        "price": 1500000,
        "beds": 3,
        "baths": 2,
        "sqft": 1800,
        "photos": ["url1", "url2"],
        "natural_light_flag": true,
        "high_ceilings_flag": false,
        "outdoor_space_flag": true,
        "modern_kitchen_flag": true
      },
      "score": 0.95,
      "matched_features": [
        "natural_light",
        "outdoor_space",
        "modern_kitchen"
      ]
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 20
}
```

### Admin Endpoints

#### Trigger Data Ingestion

```http
POST /admin/ingestion/run
```

**Headers**
- `X-Admin-Token`: Admin authentication token

**Response**
```json
{
  "status": "started",
  "job_id": "uuid",
  "estimated_duration_seconds": 300
}
```

#### Get Last Ingestion Run

```http
GET /admin/ingestion/last-run
```

**Headers**
- `X-Admin-Token`: Admin authentication token

**Response**
```json
{
  "id": "uuid",
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:05:00Z",
  "status": "completed",
  "listings_processed": 150,
  "listings_created": 10,
  "listings_updated": 140,
  "errors": []
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "errors": [
    {
      "field": "min_price",
      "message": "Must be a positive number"
    }
  ]
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "min_price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_id": "uuid"
}
```

## Rate Limiting

Currently no rate limiting. Planned for production:
- 100 requests per minute for listing endpoints
- 10 requests per minute for criteria updates
- 1 request per minute for admin endpoints

## Pagination

All list endpoints support pagination:
- Default page size: 20
- Maximum page size: 100
- Use `skip` and `limit` parameters

## Filtering

Listing endpoints support filtering by:
- Price range (`min_price`, `max_price`)
- Bedrooms (`min_beds`)
- Bathrooms (`min_baths`)
- Square footage (`min_sqft`)
- Feature flags (planned)

## Webhooks (Planned)

Future support for webhooks on:
- New listings matching criteria
- Price drops on matched listings
- Listing status changes