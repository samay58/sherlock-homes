# Codex Handoff: Sherlock Homes Deep Review

**Date**: 2026-01-27
**Handoff From**: Claude Opus 4.5
**Purpose**: Deep inspection, quality audit, and roadmap development

---

## Project Overview

Sherlock Homes is an SF real estate intelligence platform that matches users with property listings using NLP, geospatial analysis, and OpenAI Vision. It scores 17 weighted criteria per listing (natural light, outdoor space, character, tranquility, etc.) to surface what matters beyond basic inventory.

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, Pydantic, Python 3.11+ |
| Frontend | Vite, React 18, TypeScript, React Query |
| Database | SQLite (local), PostgreSQL (Docker) |
| AI | OpenAI Vision for visual scoring |
| Scraping | ZenRows API for listing data |

### Recent Changes

The frontend was just migrated from SvelteKit to Vite + React (2026-01-27). This enables React ecosystem tools like Agentation for development feedback.

---

## What Needs Review

### 1. Code Quality Audit

**Backend (`app/`)**
- `services/advanced_matching.py` - Core scoring engine (most complex, ~400 LOC)
- `services/nlp.py` - Text signal extraction
- `services/geospatial.py` - Tranquility scoring from SF noise data
- `services/ingestion.py` - Multi-source data pipeline
- `providers/` - Scraping providers (Zillow, Redfin, etc.)

**Frontend (`frontend/src/`)**
- `components/cards/DossierCard.tsx` - Most complex component (~300 LOC)
- `pages/MatchesPage.tsx` - Most complex page with filters, sorting, feedback
- `hooks/` - React Query data fetching hooks
- `lib/api.ts` - API client

### 2. AI Slop Detection

Look for these anti-patterns that indicate low-quality AI-generated code:

**Code smells:**
- Overly verbose comments explaining obvious code
- Unnecessary abstractions or premature optimization
- Copy-paste patterns that should be refactored
- Inconsistent error handling
- Magic numbers without constants
- Dead code or unused imports
- Over-engineered solutions for simple problems

**React-specific:**
- Unnecessary `useMemo`/`useCallback` without performance need
- Prop drilling that should use context
- Components doing too much (violating single responsibility)
- Inline styles that should be CSS
- Missing or incorrect dependency arrays in hooks

**Python-specific:**
- Type hints that don't match actual types
- Overly complex list comprehensions
- SQLAlchemy N+1 query patterns
- Async/await misuse
- Exception handling that swallows errors

### 3. Performance Review

**Backend:**
- Database query efficiency (check for N+1 patterns)
- API response times
- Ingestion pipeline throughput
- Memory usage during scoring

**Frontend:**
- Bundle size analysis
- Render performance (unnecessary re-renders)
- Network waterfall (API call patterns)
- Image loading strategy

### 4. Architecture Assessment

- Is the scoring engine maintainable and extensible?
- Is the provider abstraction clean?
- Are the React components properly decomposed?
- Is state management appropriate (React Query vs local state)?
- Are there circular dependencies?

---

## Key Files to Start With

```
# Backend core
app/services/advanced_matching.py    # Scoring engine
app/services/criteria_config.py      # Criteria loading
app/services/nlp.py                  # NLP extraction
app/services/ingestion.py            # Data pipeline
app/providers/registry.py            # Provider pattern

# Frontend core
frontend/src/components/cards/DossierCard.tsx
frontend/src/pages/MatchesPage.tsx
frontend/src/hooks/useMatches.ts
frontend/src/lib/api.ts

# Config
config/user_criteria.yaml            # Scoring weights and signals
```

---

## Commands for Exploration

```bash
# Start the app
./run_local.sh          # Backend at :8000
./run_frontend.sh       # Frontend at :5173

# Test endpoints
curl http://localhost:8000/ping
curl http://localhost:8000/matches/test-user
curl http://localhost:8000/listings?limit=10

# Run tests
pytest tests/ -v

# Check types
cd frontend && npx tsc --noEmit

# Build frontend
cd frontend && npm run build
```

---

## Roadmap Request

After the deep review, please propose a roadmap covering:

### Near-term (Polish)
- Bug fixes discovered during review
- Performance optimizations
- Code quality improvements
- Test coverage gaps

### Medium-term (Features)
- What features would make this significantly more useful?
- What's missing from a real estate search perspective?
- How can the matching/scoring be improved?

### Long-term (Scale)
- What architectural changes would be needed for scale?
- How should the data pipeline evolve?
- What would a production deployment look like?

---

## Context Files

- `CLAUDE.md` - Project documentation and commands
- `README.md` - Project overview
- `docs/ARCHITECTURE.md` - System architecture
- `docs/DEVELOPMENT.md` - Development guide
- `config/user_criteria.yaml` - Scoring configuration

---

## Success Criteria

A successful review will:
1. Identify concrete issues with severity ratings
2. Provide specific code examples of problems and fixes
3. Suggest refactoring opportunities with clear rationale
4. Propose a prioritized roadmap with dependencies
5. Ensure the codebase is production-ready, not just "demo-ready"

---

*This handoff was prepared by Claude Opus 4.5 after completing a SvelteKit → React migration and documentation cleanup.*
