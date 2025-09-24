# AdSpy Marketing Intelligence Suite

A powerful, AI-driven marketing intelligence and execution toolkit that extracts competitor ad data, analyzes market trends, and generates actionable campaign strategies.

## Features

- **Ad Intelligence**: Scrape and analyze Facebook Ad Library with GraphQL interception
- **AI Analysis**: LLM-powered ad teardowns, angle mining, and pattern recognition
- **Campaign Strategy**: Generate data-driven campaign structures and scaling rules
- **Supplier Intelligence**: Find and analyze suppliers in any niche
- **Content Ideation**: Generate high-converting copy based on proven patterns
- **Export & Reporting**: CSV, Excel, and Markdown reports with insights

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo>
cd adspy-suite

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Initialize directories
make setup
```

### Configuration

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=..
OPENAI_MODEL=..
FIRECRAWL_API_KEY=...  # Optional
GOOGLE_API_KEY=...      # Optional
```

## Usage

### 1. Scrape Competitor Ads

```bash
# Scrape Facebook Ad Library
python -m apps.ad_intel.main --url "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&view_all_page_id=<PAGE_ID>"

# With custom settings
python -m apps.ad_intel.main --url "<URL>" --max-scrolls 20

# Export scraped ads
python -m apps.ad_intel.main --export
```

### 2. Analyze Ads

```bash
# Run analysis on scraped ads
python -m apps.analysis.main

# Generate campaign strategy
python -m apps.analysis.main --strategy --budget 500 --objective conversions

# Analyze specific number of ads
python -m apps.analysis.main --limit 200
```

### 3. Build Campaign Structure

```bash
# Generate campaign with insights
python -m apps.strategist.main --insights-file data/reports/insights_*.json --budget 300

# Custom campaign
python -m apps.strategist.main --campaign-name "Q1 Launch" --budget 1000 --objective conversions
```

### 4. Find Suppliers

```bash
# Search suppliers in niche
python -m apps.supplier_intel.main --niche "organic skincare" --location "Houston, TX" --radius 200

# With custom output
python -m apps.supplier_intel.main --niche "fitness equipment" --output data/suppliers
```

## CLI Runner

Use the unified CLI for easier command execution:

```bash
# Setup
python run.py setup

# Scrape ads
python run.py scrape --url "https://..." --scrolls 15

# Analyze with strategy
python run.py analyze --strategy --budget 500

# Generate strategy
python run.py strategize --budget 1000 --name "Q1 Campaign"

# Find suppliers
python run.py suppliers --niche "organic soap"

# Run workflows
python run.py workflow full --url "https://..." --niche "fitness"
```

## Makefile Commands

```bash
make help        # Show available commands
make setup       # Install dependencies and setup
make scrape-fb URL=<page_url>  # Scrape Facebook ads
make analyze     # Run ad analysis
make export      # Export ads to CSV/Excel
make clean       # Clean temporary files
```

## Project Structure

```
adspy-suite/
├── apps/               # Application modules
│   ├── ad_intel/      # Ad scraping and intelligence
│   ├── analysis/      # AI-powered analysis
│   ├── strategist/    # Campaign strategy generation
│   └── supplier_intel/# Supplier discovery
├── core/              # Core utilities
│   ├── config.py      # Configuration management
│   ├── db.py          # Database operations
│   ├── llm.py         # LLM integration
│   └── schemas.py     # Data models
├── data/              # Data storage
│   ├── raw/          # Raw scraped data
│   ├── processed/    # Processed datasets
│   └── reports/      # Generated reports
├── tests/             # Test files
└── .env              # Environment variables
```

## Testing

```bash
# Run tests
make test
# or
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_core.py -v
```

## Output Files

The suite generates various outputs:

- **Raw Data**: `data/raw/fb/*.json` - GraphQL intercepts
- **Processed Data**: `data/processed/*.csv|xlsx|parquet` - Structured datasets
- **Reports**: `data/reports/*.md|json` - Analysis and strategies
- **Insights**: Pattern analysis, angles, hooks, opportunities
- **Campaign Structures**: Ready-to-import campaign JSON
- **Creative Matrix**: Test variations in Excel format

## Development

```bash
# Development setup
make dev-setup

# Format code
make format

# Lint code
make lint

# Clean up
make clean
```

## Troubleshooting

### Common Issues

1. **No ads captured**:
   - Verify the URL is correct Facebook Ad Library URL
   - Increase scroll count
   - Check browser console for errors

2. **LLM errors**:
   - Verify OpenAI API key is valid
   - Check API quota/limits
   - Falls back to offline analysis if API fails

3. **Playwright issues**:
   - Run `playwright install chromium`
   - Update Playwright: `pip install -U playwright`

### Debug Mode

```bash
# Enable verbose logging
export DEBUG=1
python -m apps.ad_intel.main --url "..."
```

## License

This project is for educational and research purposes. Ensure compliance with all applicable laws and terms of service when using web scraping features.
