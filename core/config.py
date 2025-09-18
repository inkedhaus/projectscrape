"""Configuration management for AdSpy Marketing Suite."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Application configuration."""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    firecrawl_api_key: str | None = None
    google_api_key: str | None = None

    # Scraping settings
    max_scrolls: int = 10
    headless: bool = True
    scroll_delay: float = 2.0

    # Database settings
    db_path: str = "data/ads.db"

    # Output settings
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    reports_dir: Path = Path("data/reports")


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_scrolls=int(os.getenv("MAX_SCROLLS", "10")),
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        scroll_delay=float(os.getenv("SCROLL_DELAY", "2.0")),
        db_path=os.getenv("DB_PATH", "data/ads.db"),
    )
