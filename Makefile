.PHONY: help setup install clean scrape-fb analyze export test lint format

help: ## Show available commands
	@echo "AdSpy Marketing Intelligence Suite"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and setup environment
	@echo "Setting up AdSpy Marketing Suite..."
	pip install -r requirements.txt
	playwright install chromium
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please edit with your API keys!"; fi
	@mkdir -p data/raw data/processed data/reports data/suppliers
	@echo "Setup completed!"

install: ## Install package in development mode
	pip install -e .

clean: ## Clean temporary files and directories
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup completed!"

scrape-fb: ## Scrape Facebook ads (URL=<facebook-ad-library-url>)
	@if [ -z "$(URL)" ]; then echo "Usage: make scrape-fb URL=<facebook-ad-library-url>"; exit 1; fi
	python -m apps.ad_intel.main --url "$(URL)" --max-scrolls 10

analyze: ## Run ad analysis on scraped data
	python -m apps.analysis.main --limit 150 --strategy --budget 100

strategize: ## Generate campaign strategy (BUDGET=100)
	python -m apps.strategist.main --budget $(or $(BUDGET),100) --campaign-name "Generated Campaign"

export: ## Export ads to CSV/Excel
	python -m apps.ad_intel.main --export

suppliers: ## Find suppliers (NICHE=<product-niche>)
	@if [ -z "$(NICHE)" ]; then echo "Usage: make suppliers NICHE=<product-niche>"; exit 1; fi
	python -m apps.supplier_intel.main --niche "$(NICHE)" --location "Houston, TX"

workflow-full: ## Run full workflow (URL=<url> NICHE=<niche>)
	@if [ -z "$(URL)" ]; then echo "Usage: make workflow-full URL=<facebook-url> NICHE=<niche>"; exit 1; fi
	python run.py workflow full --url "$(URL)" --niche "$(NICHE)" --budget $(or $(BUDGET),100)

test: ## Run tests
	@if [ -d tests ]; then \
		echo "Running tests..."; \
		python -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Create tests first."; \
	fi

lint: ## Run linting
	@echo "Running linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 apps/ core/ run.py --max-line-length=120 --ignore=E501,W503; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

format: ## Format code with black
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black apps/ core/ run.py --line-length 120; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

status: ## Show project status
	python run.py status

# Example usage targets
example-scrape: ## Example: Scrape sample Facebook page
	@echo "This would scrape a sample page (replace with real URL)"
	@echo "make scrape-fb URL='https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&view_all_page_id=123456'"

example-workflow: ## Example: Run complete workflow
	@echo "Example full workflow:"
	@echo "make workflow-full URL='https://facebook.com/ads/library/...' NICHE='fitness equipment'"

dev-setup: ## Setup development environment
	pip install -e .
	pip install pytest flake8 black
	@echo "Development environment ready!"

docker-build: ## Build Docker image (if Dockerfile exists)
	@if [ -f Dockerfile ]; then \
		docker build -t adspy-suite .; \
	else \
		echo "Dockerfile not found. Create one to use Docker."; \
	fi

docker-run: ## Run in Docker container
	@if [ -f Dockerfile ]; then \
		docker run -it --rm -v $(PWD)/data:/app/data adspy-suite; \
	else \
		echo "Docker image not built. Run 'make docker-build' first."; \
	fi