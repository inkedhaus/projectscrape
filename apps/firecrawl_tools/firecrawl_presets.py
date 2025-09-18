#!/usr/bin/env python3
"""
Facebook Ad Library Scraping Configuration
Preset configurations for specialized Firecrawl scraping operations
"""

import os
import random
import re
from typing import Any

# 🔑 API Key (falls back to config)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# 🎭 User-Agent Pool (desktop browsers)
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/123.0.0.0 Safari/537.36",
]


# 🎲 Random jitter helper
def jitter(ms: int = 1500, spread: int = 400) -> int:
    """Generate random wait time with jitter"""
    return max(500, int(random.uniform(ms - spread, ms + spread)))


# ⏳ Pre-actions (settle + consent dismissal)
PRE_ACTIONS = [
    {"type": "wait", "milliseconds": jitter(1800, 600)},
    {"type": "click", "selector": "button:has-text('Allow all')", "optional": True},
    {"type": "click", "selector": "button:has-text('Accept all')", "optional": True},
    {"type": "click", "selector": "button:has-text('Only allow essential')", "optional": True},
    {"type": "click", "selector": "[aria-label='Close']", "optional": True},
    {"type": "click", "selector": "button:has-text('Not Now')", "optional": True},
]

# 📜 Scroll pattern (20 cycles for comprehensive coverage)
SCROLL_ACTIONS = []
for _ in range(20):
    SCROLL_ACTIONS.extend(
        [
            {"type": "wait", "milliseconds": jitter(1500, 500)},
            {"type": "scroll", "direction": "down", "pixels": int(random.uniform(1100, 1700))},
        ]
    )

# 🎯 Extraction schema for Facebook ad cards
AD_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": "Main bold text or primary message of the ad",
            },
            "subheadline": {
                "type": "string",
                "description": "Secondary descriptive text or body copy",
            },
            "cta": {
                "type": "string",
                "description": "Call-to-action button text (Shop Now, Learn More, etc.)",
            },
            "offer": {
                "type": "string",
                "description": "Any discount, promo code, or special offer mentioned",
            },
            "advertiser": {"type": "string", "description": "Company or page name running the ad"},
            "image_alt": {"type": "string", "description": "Alt text or description of ad images"},
        },
        "required": ["headline"],
    },
}

# 🔎 Offer detection patterns
OFFER_PATTERNS = re.compile(
    r"(\b\d{1,2}%\s*off\b|\b\d{1,3}\s*%\s*off\b|free\s+ship|free\s+shipping|bogo|buy\s+one\s+get\s+one|"
    r"coupon|promo\s*code|use\s+code|save\s+\$?\d+|discount|deal|sale|\$\d+\s+off)",
    flags=re.IGNORECASE,
)


def normalize_offer(text: str) -> str:
    """Extract and normalize offer text from ad content"""
    if not text:
        return ""

    match = OFFER_PATTERNS.search(text)
    return match.group(0).strip() if match else ""


def clean_ad_text(text: str) -> str:
    """Clean and normalize ad text"""
    if not text:
        return ""

    # Remove extra whitespace and normalize
    cleaned = " ".join(text.strip().split())
    # Remove common Facebook UI elements
    cleaned = re.sub(r"\b(Sponsored|Ad|Learn More)\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# ⚙️ Complete Facebook Ads Library configuration
FACEBOOK_ADS_CONFIG = {
    "formats": ["markdown"],
    "only_main_content": False,  # Need full page for ad detection
    "timeout": 120000,  # 2 minutes for complex page loading
    "wait_for": 5000,  # Wait for dynamic content
    "actions": PRE_ACTIONS + SCROLL_ACTIONS,
    "mobile": False,  # Desktop view for better ad visibility
    "remove_base64_images": True,  # Reduce response size
    "location": {"country": "US", "languages": ["en"]},
}


def get_facebook_ads_url(page_id: str = None, country: str = "US", search_terms: str = None) -> str:
    """Generate Facebook Ads Library URL with parameters"""
    base_url = "https://www.facebook.com/ads/library/"
    params = ["active_status=active", "ad_type=all", f"country={country}", "media_type=all"]

    if page_id:
        params.append(f"view_all_page_id={page_id}")

    if search_terms:
        params.append(f"search_terms={search_terms.replace(' ', '%20')}")

    return f"{base_url}?{'&'.join(params)}"


def process_facebook_ad_results(raw_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Process and clean Facebook ad scraping results"""
    if not raw_result or "markdown" not in raw_result:
        return []

    content = raw_result["markdown"]

    # Extract ad-like content patterns

    ads = []
    lines = content.split("\n")

    current_ad = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current_ad:
                ads.append(current_ad)
                current_ad = {}
            continue

        # Detect headlines
        if line.startswith("###") or line.startswith("**"):
            current_ad["headline"] = clean_ad_text(line.replace("#", "").replace("*", ""))

        # Detect sponsored content
        elif "sponsored" in line.lower():
            current_ad["advertiser"] = clean_ad_text(line.replace("Sponsored", ""))

        # Detect CTAs
        elif any(
            cta.lower() in line.lower() for cta in ["shop now", "learn more", "sign up", "download"]
        ):
            current_ad["cta"] = clean_ad_text(line)

        # Check for offers
        elif OFFER_PATTERNS.search(line):
            current_ad["offer"] = normalize_offer(line)

        # Other content as subheadline
        elif "headline" in current_ad and "subheadline" not in current_ad:
            current_ad["subheadline"] = clean_ad_text(line)

    # Add last ad if exists
    if current_ad:
        ads.append(current_ad)

    return ads


# 📊 Popular Facebook Pages for testing
POPULAR_FACEBOOK_PAGES = {
    "nike": "310947142968045",
    "adidas": "20793831865",
    "amazon": "20446254070",
    "walmart": "36622166142",
    "target": "14467896762",
    "bestbuy": "116179995091093",
    "mcdonalds": "66988152632",
    "starbucks": "17800226067",
    "coca_cola": "7924983368",
}


def get_preset_examples() -> dict[str, str]:
    """Get example URLs for popular brands"""
    examples = {}
    for brand, page_id in POPULAR_FACEBOOK_PAGES.items():
        examples[brand] = get_facebook_ads_url(page_id)
    return examples
