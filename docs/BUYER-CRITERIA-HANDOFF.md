# Buyer Criteria Handoff: Samay & Kamya

*Generated: 2026-01-19 from comprehensive Q&A session*
*Source: phoenix vault `02-personal/housing-search/`*

---

## Purpose

This document captures the complete qualitative criteria extracted through a structured interview session. It translates personal preferences into actionable scoring weights, NLP signals, and visual analysis guidance for the Sherlock Homes matching engine.

**Use this to:**
- Configure the PropertyMatcher scoring weights
- Build NLP keyword extraction rules
- Guide OpenAI Vision photo analysis
- Set up alert thresholds and triggers

---

## Buyer Profile

### The People
- **Samay & Kamya**, married 2025
- One cat (Resident), likely one dog in next 2-3 years (60%+ probability)
- No kids now, want optionality for 3-5 year horizon
- Both work from home some days

### Life Stage Context
- Career transition underway (target: March 2026)
- Want to settle for 5-7+ years, not flip in 3
- High standards for craft and intentionality
- Low tolerance for generic/commodity
- Active social life (friends over occasionally, not big parties)

### Core Identity (Relevant to Space)
- "Craftsperson/artist who builds products with taste" — home should reflect this
- Anti-trend sensibility: enduring > fashionable, curated > decorated
- "Stories are amenities" — provenance, history, intention matter
- Spatial exploration rewarded — layers, transitions, light reveals

---

## Hard Filters (Binary Pass/Fail)

These are dealbreakers. Fail ANY = don't show the listing.

```python
HARD_FILTERS = {
    "price_max": 3_500_000,
    "bedrooms_min": 3,
    "bathrooms_min": 2,
    "sqft_min": 1600,
    "neighborhoods": [
        "Dolores Heights",
        "Liberty Hill",
        "Mission District",
        "Valencia Corridor",
        "Cole Valley",
        "Haight-Ashbury",
        "Duboce Triangle",
    ],
}
```

### Additional Binary Checks (from showing protocol)
| Check | Pass Condition |
|-------|----------------|
| Not dark | Must feel bright on a cloudy day |
| Quiet street | No traffic roar, no bar noise |
| Layout flows | No choppy rooms, no dead ends |
| Street parking exists | Guests need to park |
| 1 bath has tub | Functionality requirement |

---

## Soft Caps (Penalty Above, Not Disqualification)

```python
SOFT_CAPS = {
    "price_ideal": 2_500_000,      # Above this: needs justification
    "hoa_monthly_max": 800,         # Above this: score penalty
}
```

**HOA scoring logic:**
- < $400/mo: Flag for deferred maintenance (yellow)
- $400-$800/mo: Normal, no adjustment
- $800-$1,000/mo: Needs justification (-5 points)
- > $1,000/mo: Better include doorman or pool (-10 points)

---

## Weighted Scoring Criteria

### Total: 126 points

### Tier 1: Make or Break (57 points)

These five criteria determine 45% of the score. A listing that nails these but misses Tier 2/3 items is still worth seeing.

| Criterion | Weight | What "10/10" Looks Like | What "2/10" Looks Like |
|-----------|--------|-------------------------|------------------------|
| **Natural Light** | 15 | Glows on cloudy day. Multiple exposures. Light changes through day. South-facing or corner. | Cave. Single north exposure. Trees/buildings blocking. All lights on in photos. |
| **Outdoor Space** | 12 | Private yard or large deck. Indoor-outdoor flow feels intentional. Room for dog. | Juliet balcony. Shared courtyard only. Afterthought patio off bedroom. |
| **Character / Soul** | 10 | Original details preserved. Architectural intention. Something unique you can't replicate. One-of-a-kind feature. | Generic. Could be anywhere. No story. Flipper gray-and-white. |
| **Kitchen Quality** | 10 | Modern, functional, place you want to hang out. Gas stove. Good light. Island or breakfast bar. | Galley with no room. Electric coil. Dark. Builder-grade everything. |
| **Location + Quiet** | 10 | Residential street. Walk to Dolores Park <10 min. Walk to food <10 min. Can sleep with windows open. | Busy thoroughfare. 15+ min walk to anything. Bar/club adjacent. Traffic roar. |

### Tier 2: Differentiate Good from Great (38 points)

| Criterion | Weight | Notes |
|-----------|--------|-------|
| **Office Space** | 8 | Dedicated room or substantial alcove with door/separation. Not a closet nook. |
| **Indoor-Outdoor Flow** | 8 | Does outdoor feel like extension of living? Or bolt-on afterthought? |
| **High Ceilings (9ft+)** | 6 | Psychological spaciousness. Light behavior. Victorian/Edwardian typically have this. |
| **Layout Intelligence** | 6 | Primary has en-suite? Rooms connect logically? Storage where needed? |
| **Move-In Ready** | 5 | Light reno okay. Major project only if bones are exceptional. |
| **Views** | 5 | Park/greenery preferred. City skyline nice. Not staring at wall or parking lot. |

### Tier 3: Practical (26 points)

| Criterion | Weight | Notes |
|-----------|--------|-------|
| **In-Unit Laundry** | 6 | Strongly prefer. Would stretch for exceptional place without. |
| **Parking** | 6 | Garage/deeded spot preferred. Flexible if everything else perfect. |
| **Central HVAC** | 4 | Not just wall units. SF summers getting warmer. |
| **Gas Stove** | 4 | Cook seriously. Need flame. (Redundant with kitchen but explicit check) |
| **Dishwasher** | 3 | Non-negotiable for lifestyle. |
| **Storage** | 3 | Moderate needs. Not gear-heavy people. |

### Scoring Implementation

```python
def calculate_score(listing, criteria_scores: dict[str, int]) -> int:
    """
    criteria_scores: dict mapping criterion name to 0-10 score
    Returns weighted total out of 126
    """
    WEIGHTS = {
        "natural_light": 15,
        "outdoor_space": 12,
        "character_soul": 10,
        "kitchen_quality": 10,
        "location_quiet": 10,
        "office_space": 8,
        "indoor_outdoor_flow": 8,
        "high_ceilings": 6,
        "layout_intelligence": 6,
        "move_in_ready": 5,
        "views": 5,
        "in_unit_laundry": 6,
        "parking": 6,
        "central_hvac": 4,
        "gas_stove": 4,
        "dishwasher": 3,
        "storage": 3,
    }

    total = 0
    for criterion, weight in WEIGHTS.items():
        score = criteria_scores.get(criterion, 5)  # default to neutral
        # Convert 0-10 to weighted contribution
        total += (score / 10) * weight

    return round(total)
```

---

## Score Thresholds

| Score | Percent | Action |
|-------|---------|--------|
| 100+ | 80%+ | **Exceptional** — Alert immediately, pursue aggressively |
| 88-99 | 70-79% | **Strong** — Include in daily digest, worth seeing |
| 76-87 | 60-69% | **Interesting** — Show if Top 5 criteria score well |
| <76 | <60% | **Pass** — Don't surface unless explicit search |

---

## NLP Keyword Signals

### Positive Signals (Boost Score)

#### Light Keywords (weight: 1.5x)
```python
LIGHT_POSITIVE = [
    "sun-filled", "natural light", "bright", "south-facing", "corner unit",
    "light-filled", "sunny", "morning light", "afternoon sun", "skylights",
    "bay windows", "oversized windows", "walls of windows", "light-drenched",
    "eastern exposure", "western exposure", "dual aspect"
]
```

#### Character Keywords (weight: 1.3x)
```python
CHARACTER_POSITIVE = [
    "original details", "period details", "restored", "preserved",
    "crown molding", "high ceilings", "built-ins", "hardwood floors",
    "Victorian", "Edwardian", "craftsman", "industrial", "loft",
    "one-of-a-kind", "unique", "character", "charm", "historic",
    "architectural", "artisan", "handcrafted", "millwork", "wainscoting"
]
```

#### Outdoor Keywords (weight: 1.4x)
```python
OUTDOOR_POSITIVE = [
    "private yard", "outdoor space", "deck", "patio", "garden",
    "indoor-outdoor", "entertaining", "al fresco", "backyard",
    "roof deck", "terrace", "outdoor kitchen", "landscaped"
]
```

#### Kitchen Keywords (weight: 1.2x)
```python
KITCHEN_POSITIVE = [
    "chef's kitchen", "gas range", "open kitchen", "renovated kitchen",
    "island", "breakfast bar", "eat-in kitchen", "Viking", "Wolf",
    "Sub-Zero", "marble counters", "quartz", "butler's pantry"
]
```

#### Quality Markers (weight: 1.3x)
```python
QUALITY_POSITIVE = [
    "architect-designed", "custom", "handmade", "artisan", "bespoke",
    "thoughtfully", "curated", "meticulously", "award-winning",
    "designer", "boutique"
]
```

### Negative Signals (Penalize Score)

#### Flipper Red Flags (weight: 0.7x)
```python
FLIPPER_NEGATIVE = [
    "completely renovated", "newly renovated", "total renovation",
    "brand new everything", "move-in ready"  # only negative if combined with generic description
]
# Additional check: ownership < 6 months + renovation keywords = strong flipper signal
```

#### Dark/Cave Signals (weight: 0.6x)
```python
DARK_NEGATIVE = [
    "cozy",      # negative UNLESS combined with light keywords
    "intimate",  # negative UNLESS combined with light keywords
    "charming",  # negative UNLESS combined with light keywords
    "snug", "tucked away"
]
# Logic: if description has "cozy" but NO light keywords, penalize
```

#### Condition Concerns (weight: 0.5x)
```python
CONDITION_NEGATIVE = [
    "bring your vision", "handyman special", "TLC needed",
    "needs work", "as-is", "investor special", "contractor special",
    "fixer", "estate sale"  # estate sale can be neutral, context-dependent
]
```

#### Noise/Location Concerns (weight: 0.7x)
```python
NOISE_NEGATIVE = [
    "steps from bars", "nightlife", "vibrant street", "bustling",
    "action", "heart of the city", "never a dull moment"
]
```

#### Weak Outdoor (weight: 0.8x)
```python
OUTDOOR_WEAK = [
    "shared yard", "common area", "balcony", "juliet balcony",
    "courtyard access"  # shared, not private
]
```

---

## Location Intelligence

### Street-Level Scoring

#### Boost Streets (+5 to location score)
```python
BOOST_STREETS = [
    "Liberty St",
    "Sanchez St",
    "Noe St",
    "Lexington St",
    "Hill St",
    "Hancock St",
    "Fair Oaks St",
]
```

#### Penalize Streets (-10 to location score)
```python
PENALIZE_STREETS = [
    "Valencia St",
    "Mission St",
    "Church St",
    "Market St",
    "Guerrero St",  # busy sections
    "16th St",
    "24th St",      # commercial corridors
]
```

#### Penalize Conditions
```python
LOCATION_PENALTIES = {
    "first_floor_busy_street": -15,
    "adjacent_to_bar": -10,
    "on_major_thoroughfare": -10,
    "near_freeway": -10,
    "near_muni_line": -5,  # minor, some people like transit access
}
```

### Neighborhood Micro-Targeting

**Dolores Heights / Liberty Hill (Primary)**
- Liberty Street itself: iconic, competitive, premium pricing
- Sanchez between 20th-22nd: quieter gold
- Triangle between Dolores, Church, 22nd: sweet spot

**Mission / Valencia Corridor (Secondary)**
- Guerrero Street: quieter parallel to Valencia
- Lexington between 20th-21st: hidden gem
- South of 24th: quieter but farther from action

**Cole Valley / Haight (Secondary)**
- Different vibe: more nature (GGP), less scene
- Strong Victorian stock
- Some Haight blocks tourist-heavy

**Duboce Triangle (Consider)**
- Between others geographically
- Church Street can be loud
- Some excellent housing stock

---

## Visual Scoring Guidance (OpenAI Vision)

### Positive Visual Signals
```python
VISUAL_BOOST = [
    "natural light visible in photos",
    "outdoor space with greenery visible",
    "open floor plan evident",
    "high ceilings visible (crown molding at height)",
    "original architectural details (moldings, built-ins, hardwood)",
    "warm materials visible (wood, brick, natural stone)",
    "multiple windows in main rooms",
    "view of trees or park",
    "well-proportioned rooms",
    "kitchen with island or gathering space",
]
```

### Negative Visual Signals
```python
VISUAL_PENALIZE = [
    "all lights on during day (hiding darkness)",
    "ultra-wide lens distortion (making rooms look bigger)",
    "heavily staged with rental furniture",
    "gray/beige color palette throughout (flipper signal)",
    "visible deferred maintenance (water stains, peeling)",
    "cramped room layouts",
    "small or no windows visible",
    "outdated fixtures without character (just old, not charming)",
    "LVP/laminate flooring",
    "builder-grade white shaker cabinets + gray walls",
    "photos only show best angles (suspicious)",
]
```

### Photo Analysis Checklist
For each listing, analyze photos for:
1. **Light quality**: Can you see natural light? Which direction? How many exposures?
2. **Outdoor space**: Private? Size? Usable? Intentional design or afterthought?
3. **Character markers**: Original details? Architectural intention? Unique features?
4. **Kitchen assessment**: Layout? Appliances? Light? Room to hang out?
5. **Red flags**: Signs of flipping? Deferred maintenance? Staging hiding problems?

---

## Alert Configuration

### Immediate Alerts
```python
IMMEDIATE_ALERTS = {
    "new_listing": {
        "score_threshold": 76,  # 60%+ gets immediate alert
        "notify": "immediate",
    },
    "price_drop": {
        "percent_threshold": 5,
        "notify": "immediate",
    },
    "back_on_market": {
        "notify": "immediate",
        "note": "Deal fell through = motivated seller",
    },
}
```

### Daily Digest
```python
DIGEST_ALERTS = {
    "dom_stale": {
        "days_threshold": 45,
        "note": "Negotiation opportunity",
    },
    "price_drop_small": {
        "percent_threshold": 3,
        "note": "Testing the market",
    },
}
```

---

## Explainability Template

For each match, generate:

```json
{
    "score": 94,
    "score_percent": "75%",
    "tier": "Strong",
    "top_positives": [
        "Exceptional natural light (south-facing corner, bay windows)",
        "Private backyard with mature landscaping",
        "Original Victorian details preserved (crown molding, built-ins)"
    ],
    "key_tradeoff": "No garage parking, street parking only",
    "signals": {
        "tranquility_score": 8.2,
        "light_potential": 9.1,
        "visual_quality": 7.8,
        "nlp_character_score": 8.5
    },
    "why_now": "Price dropped 6% yesterday after 52 DOM"
}
```

---

## Aesthetic Philosophy Reference

From buyer's lodging preferences (patterns that apply to home purchase):

### Historical Layering > Single-Era Purity
- Victorian/Edwardian lovingly updated > brand-new build OR museum piece
- Evidence of evolution: original bones + modern kitchen/bath + thoughtful additions
- "Design ahead of trends, follow heart not fashion"

### Warm Minimalism > Sterile Modern or Crusty Old
- Clean lines but not cold
- Wood, texture, warmth
- Think: converted industrial loft with soul, or Edwardian with restraint
- NOT: white box with no personality, or dark Victorian untouched since 1920

### Spatial Drama + Exploration
- Spaces that reveal themselves
- Light that changes through the day
- Views that surprise
- Indoor-outdoor transitions that feel intentional
- Ceiling height matters — psychological spaciousness

### Craft Over Generic Luxury
- Handmade tile > builder-grade subway tile
- Original millwork preserved > McMansion crown molding
- One beautiful detail > ten average ones
- "Secret places" energy — nooks, alcoves, light wells, roof access

---

## Files in Phoenix Vault

Source documents for this handoff:

| File | Purpose |
|------|---------|
| `02-personal/housing-search/HOUSE-HUNTING-CRITERIA.md` | Master criteria document (internal) |
| `02-personal/housing-search/REALTOR-BRIEF.md` | One-pager for agents (external) |
| `02-personal/housing-search/SHOWING-SCORECARD.md` | Printable field card |
| `02-personal/housing-search/sherlock-criteria.yaml` | Machine-readable config |
| `02-personal/housing-search/README.md` | Folder overview |

---

## Implementation Checklist

- [ ] Update `PropertyMatcher` with weighted scoring (126-point scale)
- [ ] Add hard filters to ingestion pipeline
- [ ] Implement NLP keyword extraction for positive/negative signals
- [ ] Add street-level scoring to geospatial service
- [ ] Configure OpenAI Vision prompts with visual signals
- [ ] Set up alert thresholds (76+ immediate, 45+ DOM digest)
- [ ] Build explainability payload with top 3 positives + 1 tradeoff
- [ ] Add soft cap penalties (price > $2.5M, HOA > $800)
- [ ] Implement "flipper detection" heuristic (ownership < 6mo + reno keywords)
- [ ] Add neighborhood micro-targeting (boost/penalize specific streets)

---

*This document should be updated if buyer preferences change. Last comprehensive interview: 2026-01-19.*
