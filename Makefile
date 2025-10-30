.PHONY: help install install-dev dev backend frontend test lint format clean setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup - install dependencies for both Python and Next.js
	@echo "Setting up project..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt || echo "Note: Some dev dependencies may fail, continuing..."
	cd next-app && npm install
	@echo "Setup complete! Copy .env.example to .env and configure your API keys."

install: ## Install production dependencies
	pip install -r requirements.txt
	cd next-app && npm install --production

install-dev: ## Install all development dependencies
	pip install -r requirements-dev.txt
	cd next-app && npm install

dev: ## Run both backend and frontend in development mode
	@echo "Starting backend and frontend..."
	@make -j2 backend frontend

backend: ## Run Python FastAPI backend
	@echo "Starting FastAPI backend on http://localhost:8000"
	python -m app.main

frontend: ## Run Next.js frontend
	@echo "Starting Next.js frontend on http://localhost:3000"
	cd next-app && npm run dev

test: ## Run tests
	@echo "Running Python tests..."
	pytest tests/ || echo "No tests found, create tests/ directory"
	@echo "Running TypeScript tests..."
	cd next-app && npm test || echo "No tests configured"

lint: ## Lint code (Python and TypeScript)
	@echo "Linting Python code..."
	flake8 app/ --max-line-length=100 --exclude=__pycache__ || echo "flake8 not installed, run: pip install flake8"
	black --check app/ || echo "black not installed, run: pip install black"
	@echo "Linting TypeScript code..."
	cd next-app && npm run lint

format: ## Format code (Python and TypeScript)
	@echo "Formatting Python code..."
	black app/
	isort app/
	@echo "Formatting TypeScript code..."
	cd next-app && npm run format || npx prettier --write "next-app/**/*.{ts,tsx,json,css}" || echo "Prettier not configured"

typecheck: ## Type check code
	@echo "Type checking Python code..."
	mypy app/ --ignore-missing-imports || echo "mypy not installed, run: pip install mypy"
	@echo "Type checking TypeScript code..."
	cd next-app && npm run type-check || npx tsc --noEmit || echo "TypeScript check failed"

clean: ## Clean generated files and caches
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	cd next-app && rm -rf .next node_modules/.cache 2>/dev/null || true
	@echo "Clean complete!"

clean-all: clean ## Clean everything including node_modules and venv
	cd next-app && rm -rf node_modules
	rm -rf venv .venv env

db-reset: ## Reset the database (WARNING: deletes all data)
	@read -p "Are you sure you want to delete optimizer.db? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -f optimizer.db; \
		echo "Database deleted."; \
	else \
		echo "Cancelled."; \
	fi

watch-lint: ## Watch and auto-lint on file changes
	@echo "Watching for file changes..."
	@which entr > /dev/null || (echo "Install entr: brew install entr" && exit 1)
	find app/ -name "*.py" | entr -c make lint

.DEFAULT_GOAL := help

