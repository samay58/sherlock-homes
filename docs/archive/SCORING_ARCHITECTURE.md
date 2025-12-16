# Sherlock Homes Scoring & AI Services Architecture

**Prepared for**: Visual property assessment integration  
**Current Status**: Comprehensive keyword-based NLP + geospatial + vibe presets  
**No existing LLM integrations yet**

---

## 1. CURRENT SCORING ARCHITECTURE

### Overview: "Sherlock Homes Deduction Engine"
The system uses a **multi-layer scoring approach** with NO external AI/LLM dependencies:

```
Listing Input
    ↓
1. Hard Filters (SQLAlchemy query layer)
    ↓
2. Feature Extraction (NLP keyword matching)
    ↓
3. Match Score Calculation (weighted features)
    ↓
4. Intelligence Analysis (geospatial + light potential)
    ↓
5. Vibe Adjustments (preset-based boost/penalize)
    ↓
6. Human-Readable Narrative Generation
    ↓
Results with scores, feature breakdown, and explanations
```

---

## 2. LAYER 1: HARD FILTERS (advanced_matching.py)

**Location**: `app/services/advanced_matching.py::PropertyMatcher::_build_base_query()`

Applies strict database-level filters that EXCLUDE listings:

```python
Filters Applied:
├── Price Range (price_min, price_max)
├── Bed/Bath Count (beds_min, beds_max, baths_min)
├── Square Footage (sqft_min, sqft_max)
├── Property Type (condo, house, townhouse, etc.)
├── Neighborhood Avoidance (avoid_neighborhoods list)
├── Red Flag Exclusions:
│   ├── avoid_busy_streets → has_busy_street_keywords == False
│   ├── avoid_north_facing_only → is_north_facing_only == False
│   ├── avoid_basement_units → is_basement_unit == False
├── Excluded Streets (ilike pattern matching)
└── Days on Market (max_days_on_market)
```

**Key Pattern**: Hard filters are applied FIRST, reducing candidate pool before scoring

---

## 3. LAYER 2: FEATURE EXTRACTION (nlp.py)

### 3A. NLP Keyword Lists
**Location**: `app/services/nlp.py::KEYWORDS` dict

Feature detection using keyword matching across listing descriptions:

```python
KEYWORDS = {
    # Essential Features (13 types)
    "natural_light": 29 keywords
    "high_ceilings": 14 keywords  
    "outdoor_space": 19 keywords
    "parking": 11 keywords
    "view": 16 keywords
    "updated_systems": 12 keywords
    "home_office": 10 keywords
    "storage": 12 keywords
    "open_floor_plan": 9 keywords
    "architectural_details": 11 keywords
    
    # Quality Indicators
    "luxury": 13 keywords
    "designer": 10 keywords
    "tech_ready": 12 keywords
    
    # Deal Signals
    "motivated_seller": [various reduction/back-on-market signals]
}

RED_FLAGS = {
    "busy_street": 14 keywords (Van Ness, Geary, 19th Ave, etc.)
    "foundation_issues": 14 keywords
    "hoa_issues": 8 keywords
    "north_facing_only": 3 keywords
    "basement_unit": 5 keywords
    "tandem_parking": 2 keywords
    "street_parking_only": 2 keywords
}

POSITIVE_SIGNALS = {
    "rare", "coveted", "quiet", "walkable"
}
```

### 3B. Feature Flag Extraction
**Function**: `extract_flags(text) → dict[str, bool]`

Returns boolean for each feature found in description:
```python
{
    "has_natural_light_keywords": true,
    "has_view_keywords": true,
    "has_outdoor_space_keywords": false,
    "is_north_facing_only": false,
    "busy_street": false,
    ...
}
```

These flags are stored in the PropertyListing model as individual Boolean columns (15 feature flags + 7 red flags).

---

## 4. LAYER 3: MATCH SCORE CALCULATION

### 4A. Core Scoring Algorithm
**Location**: `advanced_matching.py::PropertyMatcher::_calculate_match_score()`

```python
def _calculate_match_score(listing) -> float (0-100):
    score = 0.0
    max_score = 0.0
    
    # 1. Essential Features (double weight if required by user)
    for feature in [natural_light, high_ceilings, outdoor_space, parking, view, ...]:
        weight = self.weights.get(feature, 5)
        if feature_is_required_by_user:
            max_score += weight * 2
            if listing_has_feature:
                score += weight * 2
        else:
            max_score += weight
            if listing_has_feature:
                score += weight
    
    # 2. Quality Indicators
    if has_luxury: score += weights["luxury"]
    if has_designer: score += weights["designer"]
    if has_tech_ready: score += weights["tech_ready"]
    
    # 3. Neighborhood Match
    if listing.neighborhood in preferred_neighborhoods:
        score += weights["neighborhood_match"]
    
    # 4. Walk Score
    if listing.walk_score >= criteria.min_walk_score:
        score += weights["walk_score"]
    else:
        partial_credit = weights["walk_score"] * (1 - (diff/20))
    
    # 5. Price Value
    price_position = (listing.price - price_min) / price_range
    price_score = (1 - price_position) * weights["price_match"]  # Lower = higher score
    
    # 6. Deal Quality
    if is_price_reduced: score += weights["deal_quality"]
    if is_back_on_market: score += weights["deal_quality"] * 0.5
    
    # 7. Text Quality Score
    if description:
        text_score = calculate_text_quality_score(description)  # Returns 0-100
        score += (text_score / 100) * 20
    
    # 8. Parking Type Match
    if listing.parking_type == criteria.parking_type:
        score += 5
    
    # 9. Red Flag Penalties
    if has_foundation_issues: score -= 10
    if has_hoa_issues: score -= 8
    
    # Final normalization
    if max_score > 0:
        final_score = (score / max_score) * 100
    else:
        final_score = 50
    
    return max(0, min(100, final_score))  # Clamp 0-100
```

### 4B. Text Quality Score
**Function**: `calculate_text_quality_score(text, criteria=None) -> float`

Produces weighted score based on feature keywords found:
```python
score = 0.0

# Default weights for features
default_weights = {
    "natural_light": 10,  # Highest
    "view": 9,
    "outdoor_space": 8,
    ...
    "storage": 4,  # Lowest
}

# For each keyword match, add its weight
for feature, keywords in KEYWORDS.items():
    if any keyword found in text:
        score += weights[feature]

# Add bonuses for positive signals
for signal in POSITIVE_SIGNALS:
    if found:
        score += 2

# Subtract for red flags
for flag in RED_FLAGS:
    if found:
        score -= 5

# Normalize to 0-100
max_possible = sum(weights) + (len(POSITIVE_SIGNALS) * 2)
normalized = (score / max_possible) * 100
return max(0, min(100, normalized))
```

---

## 5. LAYER 4: INTELLIGENCE ANALYSIS

### 5A. Tranquility Score (Geospatial)
**Location**: `app/services/geospatial.py::calculate_tranquility_score(lat, lon)`

Pure geospatial calculation using hardcoded SF noise source database:

```python
def calculate_tranquility_score(lat, lon) -> dict:
    """Returns 0-100 score based on proximity to noise sources"""
    
    score = 100.0  # Start perfect
    factors = {}
    warnings = []
    
    # BUSY STREETS (10 defined: Van Ness, Geary, 19th Ave, Mission St, etc.)
    for street in SF_BUSY_STREETS:
        dist = distance_to_polyline(lat, lon, street.coords)
        if dist < 30m:      score -= 35 * severity  # On street
        elif dist < 75m:    score -= 25 * severity  # Half block
        elif dist < 150m:   score -= 15 * severity  # One block
        elif dist < 300m:   score -= 8 * severity   # Two blocks
    
    # FREEWAYS (3 defined: US-101, I-280, I-80)
    for freeway in SF_FREEWAYS:
        dist = distance_to_polyline(lat, lon, freeway.coords)
        if dist < 100m:     score -= 40
        elif dist < 200m:   score -= 30
        elif dist < 300m:   score -= 20
        elif dist < 500m:   score -= 10
    
    # FIRE STATIONS (8 defined stations)
    for station in SF_FIRE_STATIONS:
        dist = haversine_meters(lat, lon, station_lat, station_lon)
        if dist < 150m:     score -= 10
        elif dist < 300m:   score -= 5
    
    return {
        "score": max(0, min(100, score)),
        "factors": {
            "nearest_busy_street": {"name": str, "distance_m": float},
            "nearest_freeway": {"name": str, "distance_m": float},
            "nearest_fire_station": {"name": str, "distance_m": float},
        },
        "warnings": [...],  # e.g., "On Van Ness Ave (high traffic)"
        "confidence": "high" | "medium" | "low"
    }
```

**Key Insight**: Uses Haversine formula for distance calculations. No API calls needed.

### 5B. Light Potential Score (NLP + Heuristics)
**Location**: `nlp.py::estimate_light_potential(description, is_north_facing_only, is_basement_unit, ...)`

```python
def estimate_light_potential(
    description: str,
    is_north_facing_only: bool,
    is_basement_unit: bool,
    has_natural_light_keywords: bool,
    photo_count: int,
) -> dict:
    """
    Returns:
    {
        "score": 0-100,
        "signals": ["mentions south-facing", "corner_unit", ...],
        "confidence": "high" | "medium" | "low",
        "note": "Light potential estimated from keywords. True orientation unknown."
    }
    """
    
    score = 50  # Start neutral
    
    # Positive keywords (+5 each, capped at +25)
    LIGHT_POSITIVE_KEYWORDS = [
        "south-facing", "southwest", "floor-to-ceiling", "sunny", "skylights", ...
    ]
    positive_count = count_matching_keywords(description)
    score += min(25, positive_count * 5)
    
    # Negative keywords (-10 each, capped at -30)
    LIGHT_NEGATIVE_KEYWORDS = [
        "north-facing", "basement", "garden level", "dark", "interior unit", ...
    ]
    negative_count = count_matching_keywords(description)
    score -= min(30, negative_count * 10)
    
    # Reliable Boolean Flags (heavy weight)
    if has_natural_light_keywords:  score += 15
    if is_north_facing_only:        score -= 25  (confidence = "high")
    if is_basement_unit:            score -= 30  (confidence = "high")
    
    # Heuristics
    if "top floor" or "penthouse":  score += 10
    if "corner unit":               score += 8
    if photo_count >= 15:           score += 5  (bright spaces = more photos)
    elif photo_count >= 10:         score += 3
    
    return {
        "score": max(0, min(100, score)),
        "signals": [...],
        "confidence": ...,
        "note": "..."
    }
```

---

## 6. LAYER 5: VIBE ADJUSTMENTS

### 6A. Vibe Presets System
**Location**: `app/services/vibe_presets.py`

Three personality-based presets that adjust scoring:

```python
VIBE_PRESETS = {
    "light_chaser": {
        name: "Light Chaser",
        weights: {
            "natural_light": 20,  # Highest priority
            "view": 15,
            "high_ceilings": 12,
            "architectural_details": 5,
            "tranquility": 3,  # Lower
        },
        filters: {
            "avoid_north_facing_only": True,
            "avoid_basement_units": True,
        },
        boost_keywords: ["south-facing", "floor-to-ceiling", "sunny", "corner unit", ...],
        penalize_keywords: ["north-facing", "basement", "dark", ...],
    },
    
    "urban_professional": {
        weights: {
            "walk_score": 15,
            "transit_score": 12,
            "updated_systems": 10,
            "tech_ready": 8,
            ...
        },
        filters: {"min_walk_score": 85, "property_types": ["condo", "loft"]},
        boost_keywords: ["walkable", "steps from", "modern", "smart home", ...],
        penalize_keywords: ["suburban", "cul-de-sac", ...],
    },
    
    "deal_hunter": {
        weights: {
            "deal_quality": 20,  # Highest
            "price_position": 15,
            "days_on_market_bonus": 10,
            ...
        },
        filters: {"include_price_reduced": True, "min_days_on_market": 14},
        boost_keywords: ["price reduced", "motivated", "must sell", "fixer", ...],
        penalize_keywords: ["multiple offers", "highest and best", ...],
    }
}
```

### 6B. Vibe Application
**In `PropertyMatcher.find_matches()`**:

```python
# Apply vibe-specific keyword adjustments
if listing.description:
    # Boost for matching vibe keywords
    boost_count = sum(1 for kw in self.boost_keywords if kw in desc_lower)
    score = min(100, score + boost_count * 1.5)
    
    # Penalize for anti-vibe keywords
    penalty_count = sum(1 for kw in self.penalize_keywords if kw in desc_lower)
    score = max(0, score - penalty_count * 2)
```

---

## 7. LAYER 6: HUMAN-READABLE NARRATIVES

### 7A. Narrative Generation
**Location**: `advanced_matching.py::generate_match_narrative()`

Produces explanatory text based on score and top features:

```python
def generate_match_narrative(listing, match_score, feature_scores, tranquility_data, light_data):
    """
    Returns a 1-2 sentence explanation.
    Examples:
    - "Excellent match — exceptional natural light and views."
    - "Strong match with notable outdoor space. Very quiet location."
    - "Good fit with home office potential."
    """
    
    # Score tiers
    if match_score >= 85:
        base = "Excellent match"
    elif match_score >= 70:
        base = "Strong match"
    elif match_score >= 55:
        base = "Good fit"
    elif match_score >= 40:
        base = "Worth considering"
    else:
        base = "Meets some requirements"
    
    # Add top 2-3 contributing features
    sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
    top_features = [FEATURE_DISPLAY_NAMES[f] for f, score in sorted_features[:3] if score > 0]
    
    # Add callouts for special signals
    callouts = []
    if tranquility_score >= 80:
        callouts.append("Very quiet location.")
    if light_score >= 75:
        callouts.append("Excellent light potential.")
    elif light_score <= 35:
        callouts.append("Limited natural light expected.")
    
    return base + " — " + ", ".join(top_features) + ". " + " ".join(callouts)
```

---

## 8. SCORE STORAGE & PIPELINE

### 8A. PropertyListing Model
**Location**: `app/models/listing.py`

Stores scores and intelligence in the database:

```python
class PropertyListing(Base):
    # Scoring columns
    match_score = Column(Float)  # 0-100, calculated per criteria
    feature_scores = Column(JSON)  # {feature: contribution_value, ...}
    
    # Cached intelligence
    tranquility_score = Column(Integer)  # 0-100, geospatial
    tranquility_factors = Column(JSON)  # {nearest_busy_street, nearest_freeway, ...}
    light_potential_score = Column(Integer)  # 0-100, NLP-based
    light_potential_signals = Column(JSON)  # what contributed to score
    
    # Feature flags (15 features + 7 red flags)
    has_natural_light_keywords = Column(Boolean)
    has_outdoor_space_keywords = Column(Boolean)
    ...
    is_north_facing_only = Column(Boolean)
    is_basement_unit = Column(Boolean)
    ...
```

### 8B. Match Pipeline
**Flow**: `listings.py::read_matches_for_user()`

```
1. GET /matches/user/{user_id}
   └─ get_or_create_user_criteria(user_id)
   
2. find_advanced_matches(criteria, db, limit=100, min_score=0.0, vibe_preset=None)
   ├─ PropertyMatcher(criteria, db, vibe_preset)
   │   └─ _initialize_weights()  (from defaults → vibe → user overrides)
   │
   └─ matcher.find_matches(limit=100, include_intelligence=True)
      ├─ _build_base_query()  (hard filters)
      ├─ For each listing:
      │  ├─ _calculate_match_score()
      │  ├─ if include_intelligence:
      │  │  ├─ calculate_tranquility_score(lat, lon)
      │  │  ├─ estimate_light_potential(description, flags, photos)
      │  │  └─ generate_match_narrative(listing, score, features, tranquility, light)
      │  └─ listing.match_score = score
      │     listing.feature_scores = breakdown
      │
      └─ Sort by score, apply limit, return [(listing, score, intelligence), ...]

3. Return results
   └─ Response includes: address, price, score, narrative, tranquility, light_potential
```

### 8C. Frontend Display
**What the API returns**:
```json
{
    "listing": {
        "address": "123 Main St",
        "price": 1500000,
        "match_score": 87.5,
        "feature_scores": {
            "natural_light": 10,
            "outdoor_space": 8,
            "view": 9,
        },
        "tranquility_score": 78,
        "light_potential_score": 82,
    },
    "narrative": "Excellent match — exceptional natural light and views. Very quiet location.",
    "tranquility": {
        "score": 78,
        "factors": {
            "nearest_busy_street": {"name": "Van Ness Ave", "distance_m": 245.3},
            "nearest_freeway": {"name": "None nearby", "distance_m": 1200.0},
        }
    },
    "light_potential": {
        "score": 82,
        "signals": ["mentions 'south-facing'", "corner_unit", "top_floor_unit"],
        "confidence": "medium"
    }
}
```

---

## 9. EXISTING PATTERNS FOR VISUAL SCORING

### 9A. Similar Score Types We Can Learn From

The system already implements 4 types of scores:

| Score Type | Source | Range | Confidence | API Call Required |
|-----------|--------|-------|-----------|------------------|
| Match Score | Feature weights + text | 0-100 | High (if well-defined criteria) | No |
| Tranquility | Geospatial distance | 0-100 | Medium/High | No (precomputed) |
| Light Potential | Keywords + heuristics | 0-100 | Medium/Low (depends on data) | No |
| Text Quality | Keyword density | 0-100 | Medium | No |

**Pattern**: All scores are:
- **0-100 normalized**
- **JSON-storable** (can be cached in DB)
- **Confidence-aware** (includes "high/medium/low" field)
- **Factor-based** (includes breakdown of what contributed)
- **Narrative-enabled** (generates human-readable explanation)

### 9B. Integration Points for Visual Scoring

To add visual property assessment, we could:

1. **Option A: Extend Existing NLP Pattern**
   - Add visual keywords from photo metadata or descriptions
   - E.g., "staged photos", "professional photography", "renovation showcase"
   - Follows existing extract_flags() + keyword matching pattern

2. **Option B: Add New Intelligence Layer** (like tranquility/light)
   - Call Claude Vision API on property photos
   - Store visual assessment score in DB (like light_potential_score)
   - Cache result per property
   - Include in narrative generation

3. **Option C: Photo Count Heuristics** (already partially implemented)
   - Photo count already used as signal in light_potential estimation
   - `photo_count >= 15: score += 5` (bright spaces have more photos)
   - Could expand to: photo diversity, staging indicators, etc.

---

## 10. CONFIGURATION & SETTINGS

### 10A. No LLM Configuration Yet
**Location**: `app/core/config.py`

```python
class Settings(BaseSettings):
    # API Keys (defined, no LLM keys yet)
    ZENROWS_API_KEY: Optional[str]  # Web scraping
    WALKSCORE_API_KEY: Optional[str]  # Walkability data
    
    # NOT defined:
    # OPENAI_API_KEY
    # CLAUDE_API_KEY
    # VISION_API_KEY
```

This is where visual scoring API keys would go if needed.

### 10B. Database Schema for Caching
Already has pattern for caching intelligent scores:
```python
tranquility_score = Column(Integer)  # Cache scores per property
tranquility_factors = Column(JSON)
light_potential_score = Column(Integer)
light_potential_signals = Column(JSON)
```

---

## 11. KEY ARCHITECTURAL DECISIONS

### 11A. Current Philosophy
1. **No external LLM APIs** - uses keyword matching + geometric computation
2. **Fast scoring** - can rate hundreds of properties in seconds
3. **Transparent logic** - every score includes "why" (signals, factors)
4. **Confidence-aware** - distinguishes "high confidence from data" vs "guessing"
5. **Cacheable** - scores stored in DB, can be reused
6. **Vibe-responsive** - same listing gets different scores for different users

### 11B. Scoring Validation Strategy
```python
match_score = _calculate_match_score(listing)  # 0-100

if match_score >= 85:  → "Excellent match"
elif match_score >= 70:  → "Strong match"
elif match_score >= 55:  → "Good fit"
elif match_score >= 40:  → "Worth considering"
else:                    → "Below threshold"
```

Thresholds are soft (not hard filters) — still included for user to see.

---

## 12. PATTERNS WE SHOULD FOLLOW FOR VISUAL SCORING

If adding vision API for photo assessment:

```python
# Pattern 1: Store in model
class PropertyListing(Base):
    visual_quality_score = Column(Integer)  # 0-100
    visual_assessment = Column(JSON)  # {aesthetic_appeal, staging_quality, ...}

# Pattern 2: Create service module
# app/services/visual_scoring.py
def assess_property_photos(listing, photos) -> dict:
    """
    Returns:
    {
        "score": 0-100,
        "dimensions": {
            "staging_quality": 0-100,
            "aesthetic_appeal": 0-100,
            "condition_indicators": 0-100,
        },
        "signals": ["professionally_staged", "modern_finishes", ...],
        "confidence": "high" | "medium" | "low",
        "note": "Assessment based on N photos"
    }
    """

# Pattern 3: Integrate into matcher
class PropertyMatcher:
    def find_matches(...):
        for listing in listings:
            ...
            if include_intelligence and listing.photos:
                visual_data = assess_property_photos(listing, listing.photos)
                intelligence["visual_assessment"] = visual_data
                
                # Factor into score
                visual_bonus = (visual_data["score"] / 100) * 5
                score = min(100, score + visual_bonus * 0.2)

# Pattern 4: Include in narratives
if visual_data and visual_data.get("score"):
    if visual_data["score"] >= 80:
        callouts.append("Professionally staged and well-maintained.")
    elif visual_data["score"] <= 40:
        callouts.append("May need cosmetic updates.")
```

---

## 13. SUMMARY TABLE

| Component | Location | Type | Purpose | API Calls |
|-----------|----------|------|---------|-----------|
| Hard Filters | advanced_matching.py | SQLAlchemy | Exclude unfitting properties | No |
| Feature Extraction | nlp.py | Keyword matching | Detect amenities from description | No |
| Match Scoring | advanced_matching.py | Weighted sum | Calculate property fit score | No |
| Text Quality | nlp.py | Keyword scoring | Rate description quality | No |
| Tranquility Score | geospatial.py | Distance calc | Assess noise pollution | No |
| Light Potential | nlp.py | Keywords + heuristics | Estimate natural light | No |
| Vibe Presets | vibe_presets.py | Weight adjustment | Personality-based filtering | No |
| Narratives | advanced_matching.py | Template + features | Explain match quality | No |

**Observation**: System is completely self-contained — no dependencies on external APIs except Zenrows (for scraping) and WalkScore (optional).

---

## READY FOR VISUAL INTEGRATION?

✅ **Database schema supports it** - has JSON columns for scores/factors  
✅ **Pipeline ready** - intelligence analysis layer can be extended  
✅ **Pattern established** - similar to tranquility/light scoring  
✅ **No architectural changes needed** - fits naturally into existing design  

**Next steps for vision integration**:
1. Define visual scoring dimensions (staging, aesthetics, condition)
2. Choose API (Claude Vision, GPT-4V, or image analysis library)
3. Create `app/services/visual_scoring.py`
4. Add columns to PropertyListing model
5. Integrate into `PropertyMatcher.find_matches()` intelligence layer
6. Include in narrative generation
