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
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
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
└── .env              # Environment variables
```

## Workflow Example

### Complete Campaign Research Flow

```bash
# 1. Scrape competitor ads
python -m apps.ad_intel.main --url "https://facebook.com/ads/library/..."

# 2. Analyze patterns and extract insights
python -m apps.analysis.main --strategy --budget 500

# 3. Build campaign structure
python -m apps.strategist.main --insights-file data/reports/insights_*.json

# 4. Find suppliers (if physical product)
python -m apps.supplier_intel.main --niche "your niche"

# 5. Export everything
python -m apps.ad_intel.main --export
```

## Output Files

The suite generates various outputs:

- **Raw Data**: `data/raw/fb/*.json` - GraphQL intercepts
- **Processed Data**: `data/processed/*.csv|xlsx|parquet` - Structured datasets
- **Reports**: `data/reports/*.md|json` - Analysis and strategies
- **Insights**: Pattern analysis, angles, hooks, opportunities
- **Campaign Structures**: Ready-to-import campaign JSON
- **Creative Matrix**: Test variations in Excel format

## Advanced Features

### Custom Analysis Prompts

Edit `apps/analysis/prompts.py` to customize LLM prompts for your specific needs.

### Database Queries

Access the SQLite database directly:

```python
import sqlite3
con = sqlite3.connect("data/ads.db")
df = pd.read_sql_query("SELECT * FROM ads WHERE brand LIKE '%example%'", con)
```

### Batch Processing

Process multiple competitor pages:

```bash
for url in $(cat competitor_urls.txt); do
    python -m apps.ad_intel.main --url "$url"
done
```

## Performance Tips

1. **Scrolling**: Adjust `MAX_SCROLLS` based on page size (10-20 usually sufficient)
2. **Headless Mode**: Set `HEADLESS=true` in `.env` for faster scraping
3. **Rate Limiting**: Add delays between requests to avoid detection
4. **Database**: Periodically vacuum SQLite database for performance

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

## Data Privacy & Compliance

- Respect website ToS and robots.txt
- Use appropriate delays between requests
- Store data securely and don't share personal information
- This tool is for research and competitive analysis only

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open Pull Request

## License

This project is for educational and research purposes. Ensure compliance with all applicable laws and terms of service when using web scraping features.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with detailed information

---

## CLI Runner Script

Save this as `run.py` in the root directory for a unified CLI interface:

```python
#!/usr/bin/env python
"""Unified CLI for AdSpy Marketing Suite."""
import click
import subprocess
import sys
from pathlib import Path

@click.group()
def cli():
    """AdSpy Marketing Intelligence Suite."""
    pass

@cli.command()
@click.option('--url', required=True, help='Facebook Ad Library URL')
@click.option('--scrolls', type=int, default=10, help='Number of scrolls')
def scrape(url, scrolls):
    """Scrape Facebook ads."""
    subprocess.run([
        sys.executable, '-m', 'apps.ad_intel.main',
        '--url', url,
        '--max-scrolls', str(scrolls)
    ])

@cli.command()
@click.option('--limit', type=int, default=150, help='Number of ads to analyze')
@click.option('--strategy/--no-strategy', default=False, help='Generate strategy')
@click.option('--budget', type=float, default=100, help='Daily budget')
def analyze(limit, strategy, budget):
    """Analyze scraped ads."""
    args = [
        sys.executable, '-m', 'apps.analysis.main',
        '--limit', str(limit)
    ]
    if strategy:
        args.extend(['--strategy', '--budget', str(budget)])
    subprocess.run(args)

@cli.command()
@click.option('--budget', type=float, default=100, help='Daily budget')
@click.option('--name', default='Test Campaign', help='Campaign name')
def strategize(budget, name):
    """Generate campaign strategy."""
    subprocess.run([
        sys.executable, '-m', 'apps.strategist.main',
        '--budget', str(budget),
        '--campaign-name', name
    ])

@cli.command()
def export():
    """Export ads to CSV/Excel."""
    subprocess.run([sys.executable, '-m', 'apps.ad_intel.main', '--export'])

@cli.command()
@click.option('--niche', required=True, help='Product niche')
@click.option('--location', default='Houston, TX', help='Search location')
def suppliers(niche, location):
    """Find suppliers in niche."""
    subprocess.run([
        sys.executable, '-m', 'apps.supplier_intel.main',
        '--niche', niche,
        '--location', location
    ])

@cli.command()
def setup():
    """Setup the environment."""
    subprocess.run(['make', 'setup'])

if __name__ == '__main__':
    cli()
```

Usage with the runner:

```bash
python run.py scrape --url "https://..." --scrolls 15
python run.py analyze --strategy --budget 500
python run.py strategize --budget 1000 --name "Q1 Campaign"
python run.py suppliers --niche "organic soap"
python run.py export
```
