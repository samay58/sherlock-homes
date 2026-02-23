# Sherlock Homes - Project Tracker

**Project Goal:** A real estate intelligence platform for matching users in San Francisco with listings based on quantitative (price, size, beds/baths) and qualitative (natural light, high ceilings, outdoor space, etc.) criteria.

**Core Technologies:** FastAPI (Python), Vite + React (TypeScript), PostgreSQL, Docker, ZenRows (for Zillow data).

**Frontend Migration:** SvelteKit → Vite + React (2026-01-27).

---

**Current Focus:** Polish the Vite + React UI and matching intelligence.

---

## Phase 1: Foundation & Data Ingestion (Largely Complete)

- [x] **Setup:** Project structure, FastAPI basics, frontend basics, Docker Compose.
- [x] **Database:** Initial Models (`User`, `Criteria`, `PropertyListing`), Alembic migrations setup.
- [x] **Data Pipeline:**
  - [x] Provider Abstraction (`app/providers/base.py`).
  - [x] Zillow Provider (`app/providers/zillow.py`) using ZenRows Discovery and Property Detail APIs.
  - [x] Ingestion Service (`app/services/ingestion.py`) orchestrating fetch, enrichment, throttling, and upsert.
  - [x] NLP Keyword Flag Extraction (`app/services/nlp.py`).
  - [x] Scheduled Execution via APScheduler.
  - [x] Admin controls (`/admin/ingestion/run`, `/admin/ingestion/last-run`).
  - [x] Basic data filtering.

## Phase 2: Core Matching Backend (Complete)

- [x] **Criteria Model & Schema Enhancements:** Added flags, user link, migration, updated schemas.
- [x] **Minimal Criteria API (for Testing):** Implemented `/criteria/test-user` (POST/GET).
- [x] **Matching Service:** Implemented `find_matches` in `app/services/matching.py`.
- [x] **Core API Routes:** Implemented `/listings` (GET), `/listings/{id}` (GET), `/matches/test-user` (GET).

## Phase 3: User Authentication & Full Criteria CRUD (Deferred)

- [ ] User Authentication & Authorization (JWT, Hashing, Endpoints, Dependencies)
- [ ] Full Criteria Management API (CRUD, Scoping, Active flag)

## Phase 4: Frontend User Interface (Vite + React) (Complete)

- [x] **Setup & Base Layout:**
  - [x] Vite + React project with navigation and global styling.
- [x] **API Client/Utility:**
  - [x] API utility in `src/lib/api.ts` for backend requests.
- [x] **Listing Display Components:**
  - [x] Listing card component and shared UI primitives.
- [x] **Browse Listings Page:**
  - [x] Listings page with pagination and filters.
- [x] **Listing Detail Page:**
  - [x] Listing detail page with full intel.
- [x] **Criteria Management UI (Minimal for Test User):**
  - [x] Criteria page tied to `GET/POST /criteria/test-user`.
- [x] **Matching Results UI:**
  - [x] Matches page with explainability and sorting.
- [ ] **(Deferred UI):** Placeholder/Non-functional Login/Register pages.

## Phase 5: Refinement & Deployment (Deferred)

- [ ] Testing
- [ ] Error Handling
- [ ] Configuration
- [ ] Deployment
- [ ] CI/CD (Optional)
