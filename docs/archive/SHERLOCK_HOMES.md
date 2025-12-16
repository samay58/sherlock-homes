# Sherlock Homes

> **Insight over inventory.**

Zillow shows you what's for sale. Sherlock Homes shows you what's worth your time.

---

## Project Status

| Component | Status | Last Updated |
|-----------|--------|--------------|
| Design System | ✅ Complete | 2025-12-04 |
| Frontend Components | ✅ Complete | 2025-12-05 |
| Geospatial Intelligence | ✅ Complete | 2025-12-05 |
| Light Potential Scoring | ✅ Complete | 2025-12-05 |
| Vibe Presets | ✅ Complete | 2025-12-04 |
| Match Narratives | ✅ Complete | 2025-12-04 |
| Data Freshness | ✅ Complete | 2025-12-05 |
| ZenRows Integration | ✅ Working | 2025-12-05 |
| Computer Vision (CV) | ⏸️ Deferred to Phase 2 | — |

---

## Session Log: 2025-12-05

### Issues Identified & Fixed

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Intel tags not showing | DossierCard used `listing.natural_light` instead of `listing.has_natural_light_keywords` | Fixed property names in DossierCard.svelte:38-45 |
| API returning wrong field names | Schema used `serialization_alias` renaming fields | Removed aliases from app/schemas/property.py |
| No tranquility scores | ZenRows provider not extracting lat/lon | Added lat/lon extraction to zillow.py:200-208 |
| Listings scattered across SF | Old cached data from previous searches | Cleaned DB, kept only Dolores Heights area |
| Can't tell fresh from stale | Missing days_on_market extraction | Added `listing_days` extraction to provider |
| Fresh listings filtered out | Criteria too restrictive (3bd/$1M+) | Relaxed to 2bd/$600k+ |
| No freshness visibility | UI didn't show listing age | Added badges + "Newest First" sort |

### Files Changed

```
app/providers/zillow.py        # +lat/lon, +days_on_market, +neighborhood extraction
app/schemas/property.py        # Removed serialization_alias, added all boolean fields
frontend/src/lib/components/DossierCard.svelte  # Fixed intel property names, added freshness badges
frontend/src/routes/matches/+page.svelte        # Added "Newest First" sort option
```

### Key Metrics After Fixes

- **Listings**: 16 in Dolores Heights area (94110, 94114)
- **With full intelligence**: 11 (lat/lon + tranquility + days_on_market)
- **Fresh (≤7 days)**: 1 listing (465 Liberty St)
- **Stale (>90 days)**: 4 listings

---

## Learnings

### What Worked
1. **Keyword-based light detection** is surprisingly effective—listing agents reliably mention "south-facing" and "skylights" when present
2. **Haversine distance to polylines** provides accurate noise proximity without external APIs
3. **Vibe presets** simplify complex multi-factor preferences into one click
4. **Serif for prices** creates instant authority/premium feel
5. **ZenRows property detail API** provides lat/lon + days_on_market not in discovery endpoint

### What We Learned (2025-12-05)
1. **Database pollution is real** — Old searches accumulate, mixing irrelevant listings with fresh target data
2. **Criteria filtering is invisible** — Restrictive criteria silently hides good matches; need visibility
3. **Freshness matters** — `days_on_market` is critical for surfacing "underrated" listings vs stale inventory
4. **ZenRows discovery vs details** — Discovery gives list, details gives lat/lon/days/description
5. **Schema aliases break frontend** — `serialization_alias` renamed fields, breaking type expectations

### What We Avoided
1. **True solar orientation from lat/lon alone is infeasible**—requires building footprint + unit position data we don't have
2. **CV claims verification deferred**—$100/month API cost, complex integration, uncertain ROI
3. **Tailwind migration rejected**—3-5 day effort with no feature benefit

---

## Technical Debt

### Resolved
- [x] ~~API route return format change~~ FIXED
- [x] ~~DossierCard intel property names~~ FIXED 2025-12-05
- [x] ~~Schema serialization_alias~~ FIXED 2025-12-05
- [x] ~~ZenRows lat/lon extraction~~ FIXED 2025-12-05
- [x] ~~Days on market extraction~~ FIXED 2025-12-05
- [x] ~~Freshness badges in UI~~ FIXED 2025-12-05

### Remaining
- [ ] Vibe selection doesn't re-fetch from server (client-side only)
- [ ] No persistence of user's selected vibe
- [ ] API endpoint doesn't expose vibe_preset query param
- [ ] Ingestion status endpoint returns 500 (minor)
- [ ] Some listings missing days_on_market (older cached data)

---

## Roadmap

### Phase 1: Visual Engine ✅ COMPLETE
- [x] Design system (tokens, typography)
- [x] DossierCard, ToggleChip, VibeSelector components
- [x] Homepage and matches page rebrand
- [x] Geospatial intelligence (Tranquility Score)
- [x] NLP intelligence (Light Potential)
- [x] Vibe presets with weighted scoring
- [x] Match narrative generation
- [x] Freshness badges + "Newest First" sort

### Phase 1.5: Data Quality (Next)
- [ ] Auto-cleanup of stale/off-target listings on ingestion
- [ ] Neighborhood filtering in API (not just DB cleanup)
- [ ] Criteria editor UI (let user adjust filters)
- [ ] "Why filtered" explanation for hidden listings

### Phase 2: CV Claims Verification (Future)
- [ ] Photo analysis for natural light validation
- [ ] Kitchen/bathroom quality scoring
- [ ] "Looks like photos" confidence indicator
- [ ] Budget: ~$100/month for API calls

### Phase 3: Leanness & Performance (Future)
- [ ] Server-side vibe preset application
- [ ] Cached intelligence scores in API response
- [ ] Infinite scroll / virtualized list
- [ ] Email digest of high-scoring matches

### Phase 4: Expansion (Future)
- [ ] Multi-city support (beyond SF)
- [ ] User accounts with saved vibes
- [ ] Comparison mode (side-by-side dossiers)
- [ ] Historical price tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  SvelteKit + Sherlock Design System                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ DossierCard │ │ VibeSelector│ │ ToggleChip  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      DEDUCTION ENGINE                       │
│  FastAPI + Intelligence Services                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PropertyMatcher                                      │   │
│  │  • Vibe-weighted scoring                            │   │
│  │  • Tranquility Score (geospatial)                   │   │
│  │  • Light Potential (NLP)                            │   │
│  │  • Match Narrative generation                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                            │
│  PostgreSQL + ZenRows Ingestion                            │
│  • 100+ keyword signals per listing                        │
│  • Cached intelligence scores                              │
│  • SF busy street/freeway coordinates                      │
│  • days_on_market for freshness                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Test Commands
```bash
# Start services
docker compose up -d

# Run ingestion
curl -X POST http://localhost:8000/admin/ingestion/run

# View matches
open http://localhost:5173/matches

# Check API response
curl -s http://localhost:8000/matches/test-user | python3 -c "
import sys,json; d=json.load(sys.stdin)
for l in d[:5]: print(f\"{l['address'][:35]}: {l.get('days_on_market','?')}d, {l.get('match_score',0):.0f}%\")"
```

### Verification Checklist
- [ ] Fresh listings show green "XD NEW" badge
- [ ] Stale listings (>90d) show gray "XXXD" badge
- [ ] Intel tags appear (Natural Light, View, etc.)
- [ ] Match scores display (0-100%)
- [ ] "Newest First" sort works
- [ ] All listings in target area (94110, 94114)

### Key Files to Edit
| Change | File |
|--------|------|
| Add keyword | `app/services/nlp.py` → KEYWORDS dict |
| Add busy street | `app/services/geospatial.py` → SF_BUSY_STREETS |
| Modify vibe | `app/services/vibe_presets.py` → VIBE_PRESETS |
| Update card layout | `frontend/src/lib/components/DossierCard.svelte` |
| Change colors | `frontend/src/lib/design-system/sherlock-tokens.css` |
| Adjust criteria | DB: `UPDATE criteria SET beds_min=X WHERE user_id=1` |

---

## Current Test User Criteria

```sql
-- Dolores Heights Explorer (user_id=1)
price_min: $600,000
price_max: $10,000,000
beds_min: 2
baths_min: 1
sqft_min: 800
require_natural_light: false
```

To modify: `docker exec -i sherlock-db psql -U postgres -d sherlock -c "UPDATE criteria SET beds_min=3 WHERE user_id=1;"`

---

*Last updated: 2025-12-05*
