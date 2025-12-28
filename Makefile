# MagOneAI Makefile
# Common commands for development and deployment

.PHONY: help build push dev up down logs clean

# Default registry and tag
REGISTRY ?= magoneai
TAG ?= latest

# Platform for deployment (amd64 for Google Cloud, arm64 for ARM servers)
PLATFORM ?= linux/amd64

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Docker Build Commands (Cross-Platform)
# ============================================

build: build-api build-worker build-web ## Build all Docker images for deployment platform

build-api: ## Build API image for deployment
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-api:$(TAG) -f Dockerfile --load .

build-worker: ## Build Worker image for deployment
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-worker:$(TAG) -f Dockerfile.worker --load .

build-web: ## Build Web image for deployment
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-web:$(TAG) -f web/Dockerfile --load web/

# Build and push in one step (recommended for CI/CD)
build-push: build-push-api build-push-worker build-push-web ## Build and push all images

build-push-api: ## Build and push API image
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-api:$(TAG) -f Dockerfile --push .

build-push-worker: ## Build and push Worker image
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-worker:$(TAG) -f Dockerfile.worker --push .

build-push-web: ## Build and push Web image
	docker buildx build --platform $(PLATFORM) -t $(REGISTRY)/magoneai-web:$(TAG) -f web/Dockerfile --push web/

# Build multi-arch images (amd64 + arm64)
build-multiarch: ## Build multi-architecture images and push
	docker buildx build --platform linux/amd64,linux/arm64 -t $(REGISTRY)/magoneai-api:$(TAG) -f Dockerfile --push .
	docker buildx build --platform linux/amd64,linux/arm64 -t $(REGISTRY)/magoneai-worker:$(TAG) -f Dockerfile.worker --push .
	docker buildx build --platform linux/amd64,linux/arm64 -t $(REGISTRY)/magoneai-web:$(TAG) -f web/Dockerfile --push web/

push: push-api push-worker push-web ## Push all images to registry

push-api: ## Push API image
	docker push $(REGISTRY)/magoneai-api:$(TAG)

push-worker: ## Push Worker image
	docker push $(REGISTRY)/magoneai-worker:$(TAG)

push-web: ## Push Web image
	docker push $(REGISTRY)/magoneai-web:$(TAG)

# ============================================
# Buildx Setup (run once)
# ============================================

buildx-setup: ## Setup Docker Buildx for multi-platform builds
	docker buildx create --name magone-builder --use --bootstrap
	docker buildx inspect --bootstrap

# ============================================
# Local Development
# ============================================

dev: ## Start local development environment (infrastructure only)
	cd docker && docker-compose up -d

dev-down: ## Stop local development environment
	cd docker && docker-compose down

dev-logs: ## View local development logs
	cd docker && docker-compose logs -f

# ============================================
# Production Deployment
# ============================================

up: ## Start production deployment
	cd deploy && docker-compose up -d

down: ## Stop production deployment
	cd deploy && docker-compose down

logs: ## View production logs
	cd deploy && docker-compose logs -f

restart: ## Restart all production services
	cd deploy && docker-compose restart

pull: ## Pull latest images
	cd deploy && docker-compose pull

update: pull up ## Pull and restart with latest images

# ============================================
# Local Deployment (no SSL)
# ============================================

local-up: ## Start local deployment (no SSL)
	cd deploy && docker-compose -f docker-compose.local.yml up -d

local-down: ## Stop local deployment
	cd deploy && docker-compose -f docker-compose.local.yml down

local-logs: ## View local deployment logs
	cd deploy && docker-compose -f docker-compose.local.yml logs -f

# ============================================
# Utilities
# ============================================

clean: ## Remove all containers and volumes (DESTRUCTIVE)
	cd deploy && docker-compose down -v
	docker system prune -f

status: ## Show status of all services
	cd deploy && docker-compose ps

shell-api: ## Open shell in API container
	cd deploy && docker-compose exec api /bin/bash

shell-worker: ## Open shell in Worker container
	cd deploy && docker-compose exec worker /bin/bash

db-shell: ## Open PostgreSQL shell
	cd deploy && docker-compose exec postgres psql -U magone magone_db

redis-shell: ## Open Redis shell
	cd deploy && docker-compose exec redis redis-cli

# ============================================
# Testing
# ============================================

test: ## Run all tests with coverage
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit -v --cov=src --cov-report=term-missing

test-integration: ## Run integration tests only
	pytest tests/integration -v --cov=src --cov-append

test-cov: ## Run tests and open HTML coverage report
	pytest tests/ --cov=src --cov-report=html && open htmlcov/index.html

test-fast: ## Run tests quickly (stop on first failure)
	pytest tests/unit -v -x --tb=short

test-parallel: ## Run tests in parallel
	pytest tests/ -v -n auto --cov=src --cov-report=term-missing

test-api: ## Run API router tests only
	pytest tests/unit/api -v --cov=src/api --cov-report=term-missing

test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw -- -v tests/unit

# ============================================
# Linting & Formatting
# ============================================

lint: ## Run linter
	ruff check src/ workers/ tests/

lint-fix: ## Run linter with auto-fix
	ruff check --fix src/ workers/ tests/

format: ## Format code
	ruff format src/ workers/ tests/

format-check: ## Check code formatting
	ruff format --check src/ workers/ tests/

typecheck: ## Run type checker
	mypy src/ --ignore-missing-imports

# ============================================
# CI/CD Commands
# ============================================

ci: lint-fix format test ## Run full CI pipeline locally
	@echo "All CI checks passed!"

ci-check: format-check lint test ## Run CI checks without fixing
	@echo "All CI checks passed!"
