# Scoring Implementation Guide

## Overview
This document describes the scoring and data freshness implementation for Sherlock Homes.

## Features Implemented

### 1. Advanced Matching with Scoring
- **Location**: `app/services/advanced_matching.py`
- **Algorithm**: Multi-factor scoring system (0-100 scale)
- **Factors Considered**:
  - Essential features (natural light, outdoor space, etc.)
  - Price value within range
  - Neighborhood preferences
  - Walk scores
  - Deal quality indicators
  - Text quality from descriptions

### 2. Data Freshness Tracking
- **Ingestion Status Endpoint**: `GET /ingestion/status`
- **Response Includes**:
  - Last update time
  - Hours since update
  - Status (up_to_date, stale, outdated)
  - Counts of listings processed

### 3. Automatic Data Ingestion
- **Scheduler**: APScheduler running every 6 hours (configurable)
- **Configuration**:
  - `INGESTION_INTERVAL_HOURS`: Hours between runs (default: 6)
  - `ENABLE_AUTO_INGESTION`: Toggle automatic ingestion (default: true)
- **Manual Trigger**: `POST /admin/ingestion/run`

### 4. Frontend Score Display
- **Match Score Badge**: Visual indicator showing percentage match
- **Color Coding**:
  - 80-100%: Excellent (green)
  - 60-79%: Good (blue)
  - 40-59%: Fair (yellow)
  - 0-39%: Low (gray)
- **Score Labels**: "Top Match", "Great Match", "Good Match", "Fair Match"

### 5. Sorting and Filtering
- **Sort Options**:
  - Match Score (default, best first)
  - Price (low to high / high to low)
  - Size (largest first)
- **Filter Options**:
  - Minimum match score slider (0-90%)
- **Results Counter**: Shows filtered vs total matches

## API Changes

### Updated Endpoints
- `GET /matches/test-user` - Now returns listings with `match_score` and `feature_scores`
- `GET /ingestion/status` - New endpoint for data freshness info

### Schema Updates
- `PropertyListing` schema includes:
  ```python
  match_score: Optional[float]  # 0-100 percentage
  feature_scores: Optional[Dict[str, Any]]  # Feature breakdown
  ```

## Configuration

### Environment Variables
```env
# Ingestion Settings
INGESTION_INTERVAL_HOURS=6  # How often to run (in hours)
ENABLE_AUTO_INGESTION=true  # Enable/disable automatic ingestion
ZENROWS_API_KEY=your_key_here  # Required for data scraping
```

## Usage

### Check Data Freshness
```bash
curl http://localhost:8000/ingestion/status
```

### Trigger Manual Ingestion
```bash
curl -X POST http://localhost:8000/admin/ingestion/run
```

### View Matches with Scores
Visit `http://localhost:5173/matches` to see:
- Listings ranked by match score
- Visual score badges on each card
- Sorting and filtering controls
- Data freshness indicator

## Testing

1. Start the application:
   ```bash
   docker compose up --build
   ```

2. Trigger data ingestion:
   ```bash
   curl -X POST http://localhost:8000/admin/ingestion/run
   ```

3. View matches with scores:
   ```bash
   curl http://localhost:8000/matches/test-user | python3 -m json.tool
   ```

4. Check frontend at `http://localhost:5173/matches`

## Notes

- Scores are calculated based on user criteria weights
- Default weights can be customized per user
- Ingestion runs automatically every 6 hours when ZENROWS_API_KEY is set
- Feature scores breakdown shows which features contributed to the match