# Development Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
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