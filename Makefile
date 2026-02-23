.PHONY: help up down build dev test clean migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  make up        - Start all services with Docker"
	@echo "  make down      - Stop all services"
	@echo "  make build     - Rebuild Docker images"
	@echo "  make dev       - Start development environment"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Clean temporary files and caches"
	@echo "  make migrate   - Run database migrations"
	@echo "  make shell-api - Open shell in API container"
	@echo "  make shell-db  - Open PostgreSQL shell"
	@echo "  make logs      - Follow all container logs"
	@echo "  make fmt       - Format code"

# Docker commands
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# Development
dev:
	docker compose up --build

dev-api:
	cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Testing
test:
	pytest -q

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=app --cov-report=html

# Database
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-down:
	alembic downgrade -1

# Shell access
shell-api:
	docker compose exec api /bin/bash

shell-db:
	docker compose exec db psql -U postgres -d sherlock

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf htmlcov/
	rm -rf .venv/

# Code formatting
fmt:
	@if [ -x .venv/bin/black ]; then .venv/bin/black app/; else black app/; fi
	@if [ -x .venv/bin/isort ]; then .venv/bin/isort app/; else isort app/; fi
	cd frontend && npm run format

# Linting
lint:
	@if [ -x .venv/bin/pylint ]; then PYLINTHOME=.pylint-cache .venv/bin/pylint app/; else PYLINTHOME=.pylint-cache pylint app/; fi
	cd frontend && npm run lint

# Install dependencies
install:
	pip install -r requirements.txt
	cd frontend && npm install

# Database utilities
db-reset:
	docker compose down -v
	docker compose up -d db
	sleep 5
	make migrate

db-seed:
	python -m app.scripts.seed_data

# Production build
build-prod:
	docker build -f Dockerfile -t sherlock-api:latest .
	cd frontend && npm run build
