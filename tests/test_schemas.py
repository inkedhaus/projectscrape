from datetime import datetime
from typing import Literal

# Minimal pydantic stubs if you don't have them yet:
try:
    from core.schemas import AdCreative, Supplier
except Exception:
    from pydantic import BaseModel

    class Supplier(BaseModel):
        run_id: str
        name: str
        domain: str | None = None
        locations: list[str] = []
        product_types: list[str] = []
        moq: int | None = None
        price_range: tuple[float, float] | None = None
        ratings_avg: float | None = None
        ratings_count: int | None = None
        source: Literal["firecrawl", "google", "manual"] = "manual"

    class AdCreative(BaseModel):
        run_id: str
        platform: Literal["facebook", "tiktok"]
        advertiser: str
        ad_id: str
        status: Literal["active", "inactive", "unknown"] = "unknown"
        first_seen: datetime | None = None
        last_seen: datetime | None = None
        headline: str | None = None
        subheadline: str | None = None
        primary_text: str | None = None
        cta: str | None = None
        hooks: list[str] = []
        offer: str | None = None
        media_type: Literal["image", "video", "carousel", "unknown"] = "unknown"
        media_urls: list[str] = []


def test_supplier_minimal():
    s = Supplier(run_id="t1", name="Demo", domain="demo.com", source="manual")
    assert s.name and s.run_id


def test_adcreative_minimal():
    a = AdCreative(run_id="t1", platform="facebook", advertiser="Demo", ad_id="fb_1")
    assert a.platform in ("facebook", "tiktok")
