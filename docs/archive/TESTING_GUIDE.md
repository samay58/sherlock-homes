# Sherlock Homes - Testing Guide
**Clean, simple instructions to test the system from scratch**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Start the System
```bash
cd ~/sherlock-homes
docker compose up -d --build
```

**Wait 10 seconds for services to start**, then verify:
```bash
docker compose ps
```

You should see 3 services running:
- `sherlock-api` (port 8000)
- `sherlock-frontend` (port 5173)
- `sherlock-db` (port 5432)

---

### Step 2: Initialize Test Data
```bash
docker compose exec -T api python app/db/init_test_data.py
```

**Expected output**:
```
✓ Created test user (id=1, email=test@sherlock.app)
✓ Created search criteria for test user
  Name: SF Luxury Properties
  Required features: natural_light
  Feature weights: 13 categories

✅ Test data initialization complete!
```

---

### Step 3: Run Data Ingestion
```bash
curl -X POST http://localhost:8000/admin/ingestion/run
```

**What happens**:
- Searches Dolores Heights for properties
- Filters: $800k+, 2+ beds, 1.5+ baths
- Fetches up to 25 pages (~1,000 listings)
- Enriches up to 200 with full descriptions
- Extracts features (natural light, outdoor space, etc.)
- **Takes 3-5 minutes** ☕

---

### Step 4: Check Results

#### Option A: View in Browser (Recommended)
```bash
open http://localhost:5173/matches
```

**What to look for**:
- ✅ Green checkmarks next to features (NOT red X's)
- Properties sorted by match score
- Price range $800k-$2M+
- 2-3 bedroom units
- Dolores Heights and surrounding areas

#### Option B: View via API
```bash
curl http://localhost:8000/matches/test-user | python3 -m json.tool | head -100
```

**What to verify**:
```json
{
  "address": "...",
  "price": 1500000,
  "natural_light": true,        // ✅ Should be TRUE (not false!)
  "outdoor_space": true,         // ✅ Should be TRUE for properties that have it
  "match_score": 83.3,          // Score 0-100
  "feature_scores": {
    "natural_light": 10,        // Feature detected!
    "outdoor_space": 8,
    ...
  }
}
```

---

## ✅ Success Criteria

Your system is working correctly if:

1. **Green checkmarks appear** ✅
   - Properties with "natural light" in description show `natural_light: true`
   - Properties with "backyard" or "deck" show `outdoor_space: true`

2. **Dolores Heights properties** appear
   - Look for addresses in Dolores Heights, Castro, Noe Valley

3. **Match scores are reasonable**
   - Top matches: 80-100
   - Good matches: 60-79
   - Fair matches: 40-59

4. **Variety in listings**
   - Mix of 2br and 3br properties
   - Price range $800k-$2M+
   - Different property types (single-family, condo, townhouse)

---

## 🔧 Troubleshooting

### Problem: No listings after ingestion

**Check ingestion status**:
```bash
curl http://localhost:8000/ingestion/status | python3 -m json.tool
```

**Expected**:
```json
{
  "last_run_summary_count": 1000+,    // Properties found
  "last_run_detail_calls": 200,       // Details fetched
  "last_run_upsert_count": 200+,      // Saved to DB
  "last_run_error": null              // No errors
}
```

**If error is not null**: Check logs
```bash
docker compose logs api --tail=100
```

---

### Problem: All features show red X's (false)

**This means the Pydantic fix didn't apply**. Rebuild:
```bash
docker compose build api
docker compose up -d api
sleep 5
curl http://localhost:8000/listings/1 | python3 -m json.tool | grep "natural_light\|outdoor_space"
```

Should show `true` for properties that have these features.

---

### Problem: No Dolores Heights listings

**Check what location is being searched**:
```bash
docker compose logs api | grep "initialized for location"
```

**Expected**:
```
ZillowProvider initialized for location='dolores-heights-san-francisco-ca'
```

**If it shows generic 'san-francisco-ca'**:
```bash
# Verify .env file has the location
cat .env | grep SEARCH_LOCATION

# Should show:
SEARCH_LOCATION=dolores-heights-san-francisco-ca
```

If missing, add it and rebuild:
```bash
echo "SEARCH_LOCATION=dolores-heights-san-francisco-ca" >> .env
docker compose build api
docker compose up -d api
```

---

### Problem: Services won't start

**Check if ports are in use**:
```bash
lsof -i :8000   # API
lsof -i :5173   # Frontend
lsof -i :5432   # Database
```

**Kill conflicting processes** or **stop and restart**:
```bash
docker compose down
docker compose up -d --build
```

---

## 🎯 Advanced Testing

### Test 1: Verify Feature Detection

Pick a property with obvious features:
```bash
# Get a property with "natural light" in description
curl http://localhost:8000/listings/2 | python3 -c "
import sys, json
p = json.load(sys.stdin)
print(f'Address: {p[\"address\"]}')
print(f'Description snippet: {p[\"description\"][:200]}...')
print()
print(f'natural_light flag: {p.get(\"natural_light\", \"MISSING\")}')
print(f'outdoor_space flag: {p.get(\"outdoor_space\", \"MISSING\")}')
"
```

**Expected**: If description mentions "abundance of natural light" → `natural_light: true`

---

### Test 2: Verify Scoring System

```bash
curl http://localhost:8000/matches/test-user | python3 -c "
import sys, json
matches = json.load(sys.stdin)
print(f'Total Matches: {len(matches)}')
print()
print('Top 3 Matches:')
for i, m in enumerate(matches[:3], 1):
    print(f'{i}. {m[\"address\"]}')
    print(f'   Score: {m[\"match_score\"]:.1f}/100')
    print(f'   Price: \${m[\"price\"]:,.0f}')
    nl = '✅' if m.get('natural_light') else '❌'
    os = '✅' if m.get('outdoor_space') else '❌'
    print(f'   Natural Light: {nl} | Outdoor Space: {os}')
    print()
"
```

**Expected**:
- Top matches should be 80-100 score
- High-scoring properties should have ✅ for key features

---

### Test 3: Check Database Directly

```bash
docker compose exec -T db psql -U postgres -d sherlock -c "
SELECT
  listing_id,
  address,
  price,
  has_natural_light_keywords,
  has_outdoor_space_keywords
FROM property_listings
WHERE has_natural_light_keywords = true
LIMIT 5;
"
```

**Expected**: See properties with `t` (true) in the boolean columns

---

## 📝 Configuration Reference

### Current Setup (.env)

```env
# ZenRows API (Required)
ZENROWS_API_KEY=your_zenrows_key_here

# Location - Your Priority Neighborhood
SEARCH_LOCATION=dolores-heights-san-francisco-ca

# Search Filters - Relaxed to capture quality inventory
SEARCH_PRICE_MIN=800000      # $800k minimum
SEARCH_BEDS_MIN=2            # 2+ bedrooms
SEARCH_BATHS_MIN=1.5         # 1.5+ bathrooms
SEARCH_SQFT_MIN=1000         # 1000+ sqft

# Data Collection Limits
MAX_PAGES=25                 # Up to 1,000 listings
MAX_DETAIL_CALLS=200         # Enrich 200 with full details

# Auto-Refresh
INGESTION_INTERVAL_HOURS=6   # Re-run every 6 hours
ENABLE_AUTO_INGESTION=true   # Background updates
```

### To Change Neighborhoods

Edit `.env`:
```bash
# For different SF neighborhoods:
SEARCH_LOCATION=noe-valley-san-francisco-ca
SEARCH_LOCATION=castro-san-francisco-ca
SEARCH_LOCATION=mission-san-francisco-ca
SEARCH_LOCATION=pacific-heights-san-francisco-ca
```

Then rebuild and re-ingest:
```bash
docker compose build api && docker compose up -d api
curl -X POST http://localhost:8000/admin/ingestion/run
```

### To Adjust Filters

More selective (luxury only):
```env
SEARCH_PRICE_MIN=1500000
SEARCH_BEDS_MIN=3
SEARCH_BATHS_MIN=2.0
```

More inclusive (capture everything):
```env
SEARCH_PRICE_MIN=500000
SEARCH_BEDS_MIN=1
SEARCH_BATHS_MIN=1.0
```

---

## 🔄 Fresh Start (Reset Everything)

If you want to completely reset and start over:

```bash
# Stop all services
docker compose down

# Remove database volume (deletes all listings!)
docker volume rm sherlock-homes_db_data

# Rebuild from scratch
docker compose up -d --build

# Wait 10 seconds, then initialize
sleep 10
docker compose exec -T api python app/db/init_test_data.py

# Run fresh ingestion
curl -X POST http://localhost:8000/admin/ingestion/run

# Wait 5 minutes, then check results
sleep 300
open http://localhost:5173/matches
```

---

## 📊 Monitoring

### Check Ingestion Status
```bash
curl http://localhost:8000/ingestion/status | python3 -m json.tool
```

### View Logs
```bash
# API logs
docker compose logs api --tail=100 --follow

# Database logs
docker compose logs db --tail=50

# All services
docker compose logs --tail=50 --follow
```

### Database Stats
```bash
docker compose exec -T db psql -U postgres -d sherlock -c "
SELECT
  COUNT(*) as total_listings,
  COUNT(*) FILTER (WHERE has_natural_light_keywords) as with_natural_light,
  COUNT(*) FILTER (WHERE has_outdoor_space_keywords) as with_outdoor_space,
  COUNT(*) FILTER (WHERE price >= 1000000) as luxury_market
FROM property_listings;
"
```

---

## 🎯 What Success Looks Like

### Frontend (http://localhost:5173/matches)
![Expected UI]
- Clean, modern design
- Properties sorted by match score
- **Green checkmarks** ✅ next to detected features
- Score badges: "Top Match" (90+), "Great Match" (70+), "Good Match" (50+)
- Filter controls: sort by score/price/size, minimum score slider

### API Response
```json
[
  {
    "id": 19,
    "address": "506 11th Ave, San Francisco, CA 94118",
    "price": 1995000,
    "beds": 3,
    "baths": 4,
    "sqft": 2032,
    "natural_light": true,      // ✅ GREEN CHECKMARK
    "outdoor_space": true,       // ✅ GREEN CHECKMARK
    "high_ceilings": true,       // ✅ GREEN CHECKMARK
    "match_score": 83.3,        // High score
    "feature_scores": {
      "natural_light": 10,      // Detected!
      "outdoor_space": 8,       // Detected!
      "high_ceilings": 7        // Detected!
    }
  }
]
```

---

## 📞 Quick Commands Reference

```bash
# Start system
docker compose up -d --build

# Initialize test data
docker compose exec -T api python app/db/init_test_data.py

# Run ingestion
curl -X POST http://localhost:8000/admin/ingestion/run

# Check status
curl http://localhost:8000/ingestion/status | python3 -m json.tool

# View matches (browser)
open http://localhost:5173/matches

# View matches (API)
curl http://localhost:8000/matches/test-user | python3 -m json.tool

# Check logs
docker compose logs api --tail=100

# Stop system
docker compose down

# Full reset
docker compose down && docker volume rm sherlock-homes_db_data
```

---

## ✅ Final Checklist

Before considering the system "working":

- [ ] Services start without errors (`docker compose ps` shows all running)
- [ ] Test user initialized (no 500 errors on `/matches/test-user`)
- [ ] Ingestion completes successfully (check `/ingestion/status`)
- [ ] Listings have green checkmarks (`natural_light: true` not `false`)
- [ ] Match scores appear (not `null`)
- [ ] Frontend loads at http://localhost:5173/matches
- [ ] Can sort and filter matches
- [ ] Properties from Dolores Heights area appear
- [ ] 2 bedroom units are included (not just 3+)
- [ ] Price range shows variety ($800k-$2M+)

---

**System is working when**: You see properties with ✅ green checkmarks, accurate match scores, and your target neighborhood (Dolores Heights) represented in the results!

🎉 **Enjoy your clean, modern, elegant property search!** 🏠
