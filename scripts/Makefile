# DriftTracker Development Makefile
# Enterprise-grade development workflow

.PHONY: help install test test-unit test-integration test-e2e test-performance lint format clean coverage docs

# Default target
help:
	@echo "DriftTracker Development Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install          Install all dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e         Run end-to-end tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run all linting tools"
	@echo "  format           Format code with black"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security-check   Run security checks with bandit"
	@echo ""
	@echo "Development:"
	@echo "  clean            Clean up generated files"
	@echo "  docs             Generate documentation"
	@echo "  run              Run the development server"
	@echo "  docker-build     Build production Docker image"
	@echo "  docker-run       Run production container"
	@echo "  docker-dev       Build and run development container"
	@echo "  docker-compose-prod   Run production with docker-compose"
	@echo "  docker-compose-dev    Run development with docker-compose"
	@echo "  docker-compose-test   Run tests with docker-compose"
	@echo "  docker-stop      Stop all containers"

# Installation
install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-test.txt

# Testing
test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test-e2e:
	pytest tests/e2e/ -v --tb=short

test-performance:
	pytest tests/performance/ -v --benchmark-only

test-coverage:
	pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Code Quality
lint:
	flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 backend/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	pylint backend/ --output-format=json > pylint-report.json || true

format:
	black backend/ --line-length=127
	isort backend/

type-check:
	mypy backend/ --ignore-missing-imports

security-check:
	bandit -r backend/ -f json -o bandit-report.json || true

# Development
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -f *.log
	rm -f test-results.xml
	rm -f coverage.xml
	rm -f bandit-report.json
	rm -f pylint-report.json

docs:
	pydoc-markdown --render-toc --output-dir docs/api

run:
	cd backend && python -m cli

# Docker commands
docker-build:
	docker build -f docker/Dockerfile -t drifttracker:latest .

docker-run:
	docker run -p 8000:8000 drifttracker:latest

docker-dev:
	docker build -f docker/Dockerfile.dev -t drifttracker-dev:latest .
	docker run -p 8001:8000 -v $(PWD)/backend:/app/backend drifttracker-dev:latest

docker-compose-prod:
	docker-compose -f docker/docker-compose.yml up drifttracker

docker-compose-dev:
	docker-compose -f docker/docker-compose.yml --profile dev up drifttracker-dev

docker-compose-test:
	docker-compose -f docker/docker-compose.yml --profile test up drifttracker-test

docker-stop:
	docker-compose -f docker/docker-compose.yml down

# CI/CD helpers
ci-test:
	pytest tests/ --junitxml=test-results.xml --cov=backend --cov-report=xml --cov-report=html

ci-lint:
	flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check backend/
	mypy backend/ --ignore-missing-imports

# Performance testing
benchmark:
	pytest tests/performance/ -v --benchmark-only --benchmark-sort=mean

# Database operations (for future use)
db-migrate:
	@echo "Database migration commands will be added here"

db-seed:
	@echo "Database seeding commands will be added here"

# Deployment helpers
deploy-staging:
	@echo "Staging deployment commands will be added here"

deploy-production:
	@echo "Production deployment commands will be added here"

# Monitoring and health checks
health-check:
	curl -f http://localhost:8001/health || echo "Service not responding"

# Development server with auto-reload
dev:
	cd backend && uvicorn cli:app --reload --host 0.0.0.0 --port 8001

# Quick development setup
setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

# Pre-commit hooks (if using pre-commit)
pre-commit-install:
	pip install pre-commit
	pre-commit install

# Generate requirements from current environment
freeze:
	pip freeze > requirements-frozen.txt

# Update dependencies
update-deps:
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-test.txt
	pip freeze > requirements-frozen.txt 