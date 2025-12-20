# Development Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11 or 3.12 (spaCy wheels)
- Node.js 18+
- PostgreSQL client (optional)

## Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sherlock-homes
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start services**
   ```bash
   make up
   # Or with rebuilding:
   make dev
   ```

4. **Run migrations**
   ```bash
   make migrate
   ```

## Development Workflow

### Backend Development

```bash
# Start API with hot reload
make dev-api

# Run tests
make test

# Run with coverage
make test-coverage

# Format code
black app/
isort app/

# Create new migration
make migrate-create
```

### Faster local installs (optional)
If `uv` is installed, `./run_local.sh` will use it automatically for venv creation and dependency installs (default venv: `.venv`). Set `VENV_DIR` to override.
If `requirements.txt` changes, `./run_local.sh` will reinstall dependencies automatically.

### Alerts (optional)
Set these in `.env.local` if you want notifications:

```env
# iMessage (macOS relay)
IMESSAGE_ENABLED=false
IMESSAGE_TARGET=

# Email (SMTP)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=

# SMS fallback (Twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
TWILIO_TO_NUMBER=
```

Notes:
- iMessage requires a logged-in macOS session with Messages access.
- Email requires valid SMTP credentials.

### Troubleshooting
- **bcrypt error on startup**: rebuild the venv after installing `bcrypt==3.2.2`.
  ```bash
  rm -rf .venv
  ./run_local.sh
  ```

### Local Smoke Test (End-to-End)
```bash
# 1) Start API (Terminal 1)
./run_local.sh

# 2) Health check (Terminal 2)
curl http://localhost:8000/ping

# 3) Ingest fresh listings
curl -X POST http://localhost:8000/admin/ingestion/run

# 4) Verify ingestion status
curl http://localhost:8000/ingestion/status

# 5) Set criteria (budget + neighborhoods + recency)
curl -X POST http://localhost:8000/criteria/test-user \\
  -H \"Content-Type: application/json\" \\
  -d '{\"name\":\"Focused\",\"price_soft_max\":3000000,\"price_max\":3500000,\"preferred_neighborhoods\":[\"Dolores Heights\",\"Potrero Hill\",\"Cole Valley\",\"Haight-Ashbury\",\"NoPa\"],\"avoid_neighborhoods\":[\"Pacific Heights\"],\"neighborhood_mode\":\"strict\",\"recency_mode\":\"balanced\",\"require_natural_light\":true,\"require_outdoor_space\":true,\"avoid_busy_streets\":true}'

# 6) Fetch matches (includes why-this-matched fields)
curl http://localhost:8000/matches/test-user

# 7) Create scout
curl -X POST http://localhost:8000/scouts/ \\
  -H \"Content-Type: application/json\" \\
  -d '{\"name\":\"Daily Scout\",\"description\":\"Bright 2-3 bed, quiet, outdoor space\",\"alert_frequency\":\"instant\",\"alert_sms\":true,\"alert_email\":false,\"max_results_per_alert\":5}'

# 8) Run scout (replace ID)
curl -X POST http://localhost:8000/scouts/1/run

# 9) Recent changes feed
curl http://localhost:8000/changes?limit=5
```

### Frontend Development

```bash
# Start dev server
cd frontend
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Format code
npm run format
```

### Database Management

```bash
# Access PostgreSQL shell
make shell-db

# Reset database
make db-reset

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Code Style

### Python
- Black for formatting
- isort for imports
- Type hints for all functions
- Docstrings for public APIs

### JavaScript/Svelte
- Prettier for formatting
- ESLint for linting
- JSDoc comments for utilities

## Testing

### Backend Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test
pytest tests/test_matching.py::test_find_matches
```

### Frontend Tests
```bash
# Component tests
npm run test:unit

# E2E tests
npm run test:e2e
```

## API Development

### Adding New Endpoints

1. Create router in `app/routers/`
2. Add service logic in `app/services/`
3. Update models if needed in `app/models/`
4. Add tests in `tests/`
5. Update API documentation

### Example Router
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/")
async def list_examples(db: Session = Depends(get_db)):
    return {"examples": []}
```

## Frontend Development

### Component Structure
```svelte
<script>
  import { onMount } from 'svelte';
  
  export let prop;
  
  // Component logic
</script>

<!-- Template -->
<div class="component">
  <!-- Content -->
</div>

<style>
  /* Scoped styles */
</style>
```

### Adding Routes
1. Create folder in `src/routes/`
2. Add `+page.svelte` for the page
3. Add `+page.js` for data loading
4. Update navigation if needed

## Debugging

### Backend
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugger
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Frontend
- Use browser DevTools
- Add `console.log()` statements
- Use Svelte DevTools extension

### Docker Logs
```bash
# All services
make logs

# Specific service
docker compose logs -f api
docker compose logs -f frontend
```

## Common Issues

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
docker compose ps
# Restart database
docker compose restart postgres
```

### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install
```

### Migration Conflicts
```bash
# Check current version
alembic current
# Stamp to head if needed
alembic stamp head
```

## Performance Tips

1. **Use database indexes** for frequently queried columns
2. **Implement caching** for expensive operations
3. **Lazy load images** in frontend
4. **Use pagination** for large datasets
5. **Profile slow queries** with EXPLAIN ANALYZE

## Security Checklist

- [ ] Never commit `.env` files
- [ ] Validate all user inputs
- [ ] Use parameterized queries
- [ ] Implement rate limiting
- [ ] Keep dependencies updated
- [ ] Use HTTPS in production
- [ ] Sanitize error messages

## Deployment Preparation

1. **Build production images**
   ```bash
   make build-prod
   ```

2. **Run production checks**
   ```bash
   # Security scan
   pip-audit
   
   # Dependency check
   npm audit
   ```

3. **Environment variables**
   - Set `DEBUG=false`
   - Use strong database password
   - Configure proper CORS origins

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
