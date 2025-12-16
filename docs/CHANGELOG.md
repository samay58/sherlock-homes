# Changelog

## [Unreleased]

### Added
- Rauno-inspired design system with CSS custom properties
- Sophisticated ListingCard component with micro-interactions
- Skeleton loading states for better UX
- Design tokens for consistent theming
- Architecture documentation
- Improved repository structure

### Changed
- Streamlined README for clarity
- Enhanced UI with modern design principles
- Updated global styles with typography scale
- Improved component animations and transitions

## [0.2.0] - 2024-05-07

### Phase 4: Frontend User Interface (Complete)
- Setup & Base Layout with navigation
- API Client utility for backend requests
- ListingCard component for property display
- Browse Listings page with pagination
- Listing Detail page with full information
- Criteria Management UI for test user
- Matching Results UI with filtered listings

### Phase 2: Core Matching Backend (Complete)
- Criteria Model & Schema enhancements
- Minimal Criteria API for testing
- Matching Service implementation
- Core API Routes for listings and matches

## [0.1.0] - 2024-05-06

### Phase 1: Foundation & Data Ingestion (Complete)
- Project structure with FastAPI, SvelteKit, Docker Compose
- Database Models (User, Criteria, PropertyListing)
- Alembic migrations setup
- Provider Abstraction pattern
- Zillow Provider using ZenRows APIs
- Ingestion Service with throttling and upsert
- NLP Keyword Flag Extraction
- Scheduled Execution via APScheduler
- Admin controls for ingestion
- Basic data filtering