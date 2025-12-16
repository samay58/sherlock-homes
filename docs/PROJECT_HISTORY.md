# Sherlock Homes - Project Tracker

**Project Goal:** A real estate intelligence platform for matching users in San Francisco with listings based on quantitative (price, size, beds/baths) and qualitative (natural light, high ceilings, outdoor space, etc.) criteria.

**Core Technologies:** FastAPI (Python), SvelteKit (JS/TS), PostgreSQL, Docker, ZenRows (for Zillow data).

---

**Current Focus:** Build the SvelteKit Frontend UI to interact with the core matching backend.

---

## Phase 1: Foundation & Data Ingestion (Largely Complete)

- [x] **Setup:** Project structure, FastAPI basics, SvelteKit basics, Docker Compose.
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

## Phase 4: Frontend User Interface (SvelteKit) (Complete)

- [x] **Setup & Base Layout:**
  - [x] Review/Create basic global layout (`src/routes/+layout.svelte`) with navigation.
  - [x] Basic global styling setup (CSS or Tailwind).
- [x] **API Client/Utility:**
  - [x] Create utility (`src/lib/api.js` or similar) for backend requests.
- [x] **Listing Display Components:**
  - [x] Create `ListingCard.svelte` component (`src/lib/components/`).
- [x] **Browse Listings Page:**
  - [x] Create `/listings/+page.svelte`.
  - [x] Fetch and display paginated listings using `ListingCard`.
- [x] **Listing Detail Page:**
  - [x] Create Listing Detail page (`src/routes/listings/[id]/+page.svelte`) and load function.
- [x] **Criteria Management UI (Minimal for Test User):**
  - [x] Create `/criteria/+page.svelte`.
  - [x] Fetch criteria from `GET /criteria/test-user`.
  - [x] Implement form to display and update criteria via `POST /criteria/test-user`.
- [x] **Matching Results UI:**
  - [x] Create `/matches/+page.svelte`.
  - [x] Fetch results from `GET /matches/test-user`.
  - [x] Display results using `ListingCard`.
- [ ] **(Deferred UI):** Placeholder/Non-functional Login/Register pages.

## Phase 5: Refinement & Deployment (Deferred)

- [ ] Testing
- [ ] Error Handling
- [ ] Configuration
- [ ] Deployment
- [ ] CI/CD (Optional)