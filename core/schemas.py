"""Data models and schemas for AdSpy Marketing Suite."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Ad:
    """Facebook ad data model."""

    id: str
    brand: str
    page_name: str
    headline: str
    body: str
    call_to_action: str
    media_type: str
    media_urls: list[str] = field(default_factory=list)
    target_audience: dict[str, Any] = field(default_factory=dict)
    created_date: str = ""
    scraped_at: datetime | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdAnalysis:
    """Ad analysis results."""

    ad_id: str
    hook_analysis: str
    angle: str
    pain_points: list[str]
    benefits: list[str]
    emotion: str
    target_audience: str
    effectiveness_score: float
    improvements: list[str]
    created_at: datetime | None = None


@dataclass
class CampaignStrategy:
    """Campaign strategy model."""

    name: str
    budget: float
    objective: str
    campaign_structure: list[dict[str, Any]]
    creative_angles: list[str]
    audience_segments: list[dict[str, Any]]
    budget_allocation: dict[str, float]
    testing_plan: list[dict[str, Any]]
    scaling_strategy: dict[str, Any]
    expected_metrics: dict[str, float]
    created_at: datetime | None = None


@dataclass
class Supplier:
    """Supplier information model."""

    name: str
    location: str
    contact: str
    products: list[str]
    rating: float
    reviews_count: int
    website: str
    notes: str = ""


@dataclass
class ScrapingSession:
    """Scraping session metadata."""

    url: str
    start_time: datetime
    end_time: datetime | None = None
    ads_scraped: int = 0
    max_scrolls: int = 10
    success: bool = False
    error_message: str = ""


@dataclass
class PatternAnalysis:
    """Pattern analysis results."""

    common_hooks: list[str]
    power_words: list[str]
    emotional_triggers: list[str]
    structure_patterns: list[str]
    cta_patterns: list[str]
    length_analysis: dict[str, Any]
    sample_size: int
    created_at: datetime | None = None
