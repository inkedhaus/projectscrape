#!/usr/bin/env python
"""Unified CLI for AdSpy Marketing Suite."""
import subprocess
import sys
from pathlib import Path

import click


@click.group()
def cli():
    """AdSpy Marketing Intelligence Suite."""
    pass


@cli.command()
@click.option("--url", required=True, help="Facebook Ad Library URL")
@click.option("--scrolls", type=int, default=10, help="Number of scrolls")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
def scrape(url, scrolls, headless):
    """Scrape Facebook ads."""
    args = [sys.executable, "-m", "apps.ad_intel.main", "--url", url, "--max-scrolls", str(scrolls)]
    if headless:
        args.append("--headless")

    subprocess.run(args)


@cli.command()
@click.option("--limit", type=int, default=150, help="Number of ads to analyze")
@click.option("--brand", help="Filter by specific brand")
@click.option("--strategy/--no-strategy", default=False, help="Generate strategy")
@click.option("--budget", type=float, default=100, help="Daily budget")
@click.option("--objective", default="conversions", help="Campaign objective")
def analyze(limit, brand, strategy, budget, objective):
    """Analyze scraped ads."""
    args = [sys.executable, "-m", "apps.analysis.main", "--limit", str(limit)]

    if brand:
        args.extend(["--brand", brand])

    if strategy:
        args.extend(["--strategy", "--budget", str(budget), "--objective", objective])

    subprocess.run(args)


@cli.command()
@click.option("--budget", type=float, default=100, help="Daily budget")
@click.option("--name", default="Test Campaign", help="Campaign name")
@click.option("--objective", default="conversions", help="Campaign objective")
@click.option("--insights-file", help="Path to insights JSON file")
def strategize(budget, name, objective, insights_file):
    """Generate campaign strategy."""
    args = [
        sys.executable,
        "-m",
        "apps.strategist.main",
        "--budget",
        str(budget),
        "--campaign-name",
        name,
        "--objective",
        objective,
    ]

    if insights_file:
        args.extend(["--insights-file", insights_file])

    subprocess.run(args)


@cli.command()
@click.option(
    "--format", type=click.Choice(["csv", "json", "both"]), default="both", help="Export format"
)
def export(format):
    """Export ads to CSV/Excel."""
    subprocess.run([sys.executable, "-m", "apps.ad_intel.main", "--export"])


@cli.command()
@click.option("--niche", required=True, help="Product niche")
@click.option("--location", default="Houston, TX", help="Search location")
@click.option("--radius", type=int, default=100, help="Search radius in miles")
@click.option("--limit", type=int, default=50, help="Maximum suppliers to find")
def suppliers(niche, location, radius, limit):
    """Find suppliers in niche."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "apps.supplier_intel.main",
            "--niche",
            niche,
            "--location",
            location,
            "--radius",
            str(radius),
            "--limit",
            str(limit),
        ]
    )


@cli.command()
def firecrawl():
    """Launch interactive Firecrawl tools menu."""
    subprocess.run([sys.executable, "-m", "apps.firecrawl_tools.main"])


@cli.command()
def setup():
    """Setup the environment."""
    click.echo("Setting up AdSpy Marketing Suite...")

    # Create directories
    dirs = [
        "data/raw",
        "data/processed",
        "data/reports",
        "data/suppliers",
        "data/firecrawl_results",
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        click.echo(f"Created directory: {dir_path}")

    # Copy .env.example to .env if not exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil

            shutil.copy(".env.example", ".env")
            click.echo("Created .env file from .env.example")
            click.echo("Please edit .env with your API keys!")
        else:
            click.echo("Warning: .env.example not found")

    click.echo("Setup completed!")
    click.echo("\nNext steps:")
    click.echo("1. Edit .env file with your OpenAI API key and FIRECRAWL_API_KEY")
    click.echo("2. Install Playwright browsers: playwright install chromium")
    click.echo("3. Install Firecrawl: pip install firecrawl-py")
    click.echo("4. Start scraping: python run.py scrape --url <facebook-ad-library-url>")
    click.echo("5. Or use Firecrawl tools: python run.py firecrawl")


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the API server")
@click.option("--port", type=int, default=8000, help="Port to bind the API server")
@click.option("--reload/--no-reload", default=True, help="Enable auto-reload for development")
def api(host, port, reload):
    """Start the Marketing API server."""
    try:
        import uvicorn

        uvicorn.run("apps.marketing_api.main:app", host=host, port=port, reload=reload)
    except ImportError:
        click.echo("Error: uvicorn is required to run the API server")
        click.echo("Install it with: pip install uvicorn")


@cli.command()
def status():
    """Show project status and statistics."""
    from core.db import Database

    db = Database()
    stats = db.get_stats()

    click.echo("=== AdSpy Marketing Suite Status ===")
    click.echo(f"Total ads in database: {stats['total_ads']}")
    click.echo(f"Unique brands: {stats['unique_brands']}")
    click.echo(f"Total analysis results: {stats['total_analysis']}")

    # Check data directories
    data_dirs = {
        "Raw data": "data/raw",
        "Processed data": "data/processed",
        "Reports": "data/reports",
        "Suppliers": "data/suppliers",
    }

    click.echo("\n=== Data Directories ===")
    for name, path in data_dirs.items():
        dir_path = Path(path)
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            click.echo(f"{name}: {file_count} files")
        else:
            click.echo(f"{name}: Directory not found")


@cli.command()
@click.argument("workflow", type=click.Choice(["full", "scrape-analyze", "analyze-strategize"]))
@click.option("--url", help="Facebook Ad Library URL (for full/scrape-analyze)")
@click.option("--budget", type=float, default=100, help="Daily budget for strategy")
@click.option("--niche", help="Product niche for supplier search (full workflow only)")
def workflow(workflow, url, budget, niche):
    """Run predefined workflows."""
    click.echo(f"Starting {workflow} workflow...")

    if workflow == "full":
        if not url:
            click.echo("Error: --url is required for full workflow")
            return

        # Step 1: Scrape
        click.echo("Step 1/4: Scraping ads...")
        subprocess.run([sys.executable, "-m", "apps.ad_intel.main", "--url", url])

        # Step 2: Analyze
        click.echo("Step 2/4: Analyzing ads...")
        subprocess.run(
            [sys.executable, "-m", "apps.analysis.main", "--strategy", "--budget", str(budget)]
        )

        # Step 3: Strategy
        click.echo("Step 3/4: Generating strategy...")
        subprocess.run([sys.executable, "-m", "apps.strategist.main", "--budget", str(budget)])

        # Step 4: Suppliers (if niche provided)
        if niche:
            click.echo("Step 4/4: Finding suppliers...")
            subprocess.run([sys.executable, "-m", "apps.supplier_intel.main", "--niche", niche])

        click.echo("Full workflow completed!")

    elif workflow == "scrape-analyze":
        if not url:
            click.echo("Error: --url is required for scrape-analyze workflow")
            return

        click.echo("Step 1/2: Scraping ads...")
        subprocess.run([sys.executable, "-m", "apps.ad_intel.main", "--url", url])

        click.echo("Step 2/2: Analyzing ads...")
        subprocess.run([sys.executable, "-m", "apps.analysis.main", "--limit", "100"])

        click.echo("Scrape-analyze workflow completed!")

    elif workflow == "analyze-strategize":
        click.echo("Step 1/2: Analyzing ads...")
        subprocess.run(
            [sys.executable, "-m", "apps.analysis.main", "--strategy", "--budget", str(budget)]
        )

        click.echo("Step 2/2: Generating strategy...")
        subprocess.run([sys.executable, "-m", "apps.strategist.main", "--budget", str(budget)])

        click.echo("Analyze-strategize workflow completed!")


if __name__ == "__main__":
    cli()
