# Architecture Documentation

## System Overview

Sherlock Homes is a real estate intelligence platform that matches users with SF listings based on quantitative and qualitative criteria. The system follows a modular architecture with clear separation of concerns.

## Core Components

### Backend (FastAPI)

The backend is built with FastAPI for high performance and automatic API documentation.

```
app/
├── core/
│   ├── config.py       # Environment configuration
│   └── database.py     # Database connection and session management
├── models/
│   ├── user.py         # User model
│   ├── listing.py      # Property listing model
│   └── criteria.py     # User criteria model
├── routers/
│   ├── listings.py     # Listing endpoints
│   ├── matches.py      # Matching endpoints
│   └── criteria.py     # Criteria management
├── services/
│   ├── ingestion.py    # Data ingestion from external sources
│   ├── matching.py     # Matching algorithm
│   └── nlp.py          # Natural language processing
└── providers/
    ├── base.py         # Provider abstraction
    └── zillow.py       # Zillow data provider
```

#### Key Design Decisions

1. **Service Layer Pattern**: Business logic is encapsulated in services, keeping routers thin
2. **Provider Abstraction**: External data sources are abstracted for easy swapping
3. **Async Operations**: Leverages Python's async/await for efficient I/O operations
4. **Type Safety**: Uses Pydantic models for request/response validation

### Frontend (Vite + React)

The frontend uses Vite + React 18 with TypeScript for fast development and optimal performance.

```
frontend/src/
├── components/
│   ├── cards/          # DossierCard, ListingCard
│   ├── filters/        # ToggleChip, VibeSelector
│   ├── gallery/        # ImageGallery
│   ├── layout/         # RootLayout
│   └── loading/        # SkeletonLoader
├── hooks/              # React Query hooks
├── lib/
│   ├── api.ts          # API client
│   └── types.ts        # TypeScript interfaces
├── pages/              # Route components
│   ├── HomePage.tsx
│   ├── ListingsPage.tsx
│   ├── ListingDetailPage.tsx
│   ├── MatchesPage.tsx
│   └── CriteriaPage.tsx
├── styles/
│   ├── app.css         # Global styles
│   └── design-system/  # Design tokens
├── App.tsx             # Router setup
└── main.tsx            # Entry point
```

#### Design System

- **Tokens-Based**: CSS custom properties for consistent theming
- **Component-First**: Atomic design principles with reusable components
- **Motion Design**: Micro-interactions under 200ms for instant feedback
- **Responsive**: Mobile-first approach with progressive enhancement

### Database (PostgreSQL)

#### Schema Design

```sql
users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

property_listings
├── id (UUID, PK)
├── zillow_id (VARCHAR, UNIQUE)
├── address (VARCHAR)
├── price (DECIMAL)
├── beds (INTEGER)
├── baths (DECIMAL)
├── sqft (INTEGER)
├── photos (JSON)
├── natural_light_flag (BOOLEAN)
├── high_ceilings_flag (BOOLEAN)
├── outdoor_space_flag (BOOLEAN)
├── modern_kitchen_flag (BOOLEAN)
└── timestamps

user_criteria
├── id (UUID, PK)
├── user_id (UUID, FK)
├── min_price (DECIMAL)
├── max_price (DECIMAL)
├── min_beds (INTEGER)
├── min_baths (DECIMAL)
├── min_sqft (INTEGER)
├── [quality flags...]
└── timestamps
```

## Data Flow

### Ingestion Pipeline

```
ZenRows API → Zillow Provider → Ingestion Service → NLP Processing → Database
```

1. **Scheduled Fetch**: APScheduler triggers periodic data fetches
2. **Rate Limiting**: Throttled requests to respect API limits
3. **Enrichment**: NLP extracts qualitative features from descriptions
4. **Upsert**: Conflict resolution on zillow_id for updates

### Matching Algorithm

```
User Criteria → Matching Service → Filtered Listings → Ranked Results
```

1. **Hard Filters**: Price, beds, baths, sqft constraints
2. **Soft Scoring**: Qualitative feature preferences
3. **Ranking**: Combined score with configurable weights

## Deployment Architecture

### Docker Composition

```yaml
services:
  api:
    - FastAPI application
    - Auto-reload in development
    - Health checks
  
  frontend:
    - Vite + React application
    - Hot module replacement
    - Static asset serving
  
  postgres:
    - PostgreSQL 15
    - Persistent volume
    - Automated migrations
```

### Environment Configuration

- **Development**: Hot reload, debug logging, local database
- **Staging**: Production build, remote database, error tracking
- **Production**: Optimized build, CDN assets, monitoring

## Security Considerations

1. **API Keys**: Environment variables, never in code
2. **CORS**: Configured for frontend origin
3. **Input Validation**: Pydantic models for all inputs
4. **SQL Injection**: SQLAlchemy ORM prevents injection
5. **Rate Limiting**: Per-endpoint throttling (planned)

## Performance Optimizations

1. **Database Indexing**: On frequently queried columns
2. **Lazy Loading**: Images load on scroll
3. **Caching**: Redis for frequently accessed data (planned)
4. **CDN**: Static assets served from edge (production)
5. **Connection Pooling**: Database connection reuse

## Monitoring & Observability

### Logging
- Structured JSON logging
- Request/response correlation IDs
- Error tracking with stack traces

### Metrics (Planned)
- Request latency percentiles
- Database query performance
- External API response times
- Business metrics (matches, conversions)

## Future Considerations

1. **Authentication**: JWT-based auth system
2. **Real-time Updates**: WebSocket for live listings
3. **ML Ranking**: Machine learning for personalized ranking
4. **Mobile Apps**: React Native or Flutter
5. **Multi-region**: Geographic distribution for scale