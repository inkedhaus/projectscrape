#!/usr/bin/env python3
"""
🧩 Facebook Ads Library Scraper - Clean Playwright Implementation
Following the clean instructions for optimal Facebook ad extraction

✅ FEATURES:
- Smart scrolling with verification
- Network capture with retry queue
- DOM extraction after each scroll
- Progress checkpointing every 50 ads
- Selector caching for reliability
- Rate limiting and error handling
- URL-based deduplication
"""

import asyncio
import json
import os
import random
import re
import sys
import aiohttp
import aiofiles
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse, unquote

from playwright.async_api import Page, async_playwright


@dataclass
class MediaItem:
    """Media item structure"""

    type: str  # "image" or "video"
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    poster: Optional[str] = None  # for videos
    local_path: Optional[str] = None  # downloaded file path


@dataclass
class AdRecord:
    """Structured ad data record following the required schema"""

    ad_id: Optional[str] = None  # Prefer post_id/adid from network
    placement: str = "feed"  # feed|stories|reels|unknown
    page_name: Optional[str] = None
    page_id: Optional[str] = None
    headline: Optional[str] = None
    primary_text: Optional[str] = None
    cta_label: Optional[str] = None
    sponsored_label: Optional[str] = None
    destination_url: Optional[str] = None
    media: List[MediaItem] = None
    created_time: Optional[str] = None
    captured_at: str = ""
    source: Dict[str, str] = None

    # Legacy fields for compatibility
    library_id: Optional[str] = None
    caption: Optional[str] = None
    cta_text: Optional[str] = None
    media_urls: List[str] = None
    date_started: Optional[str] = None
    ad_url: Optional[str] = None
    extracted_at: Optional[str] = None

    def __post_init__(self):
        if self.media is None:
            self.media = []
        if self.media_urls is None:
            self.media_urls = []
        if self.source is None:
            self.source = {"path": "dom", "details": "default_selectors"}
        if not self.captured_at:
            self.captured_at = datetime.now().isoformat()
        if not self.extracted_at:
            self.extracted_at = self.captured_at
        # Map legacy fields to new schema
        if self.caption and not self.primary_text:
            self.primary_text = self.caption
        if self.cta_text and not self.cta_label:
            self.cta_label = self.cta_text


class FacebookAdsPlaywrightScraper:
    """
    Clean Facebook Ads scraper using Playwright following optimized instructions
    """

    def __init__(self, out_dir: str = "data/playwright_results"):
        """Initialize scraper with output directory"""
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Create media subdirectory for downloaded files
        self.media_dir = self.out_dir / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Core data structures
        self.media_urls: Set[str] = set()  # Successfully captured media
        self.retry_queue: List[str] = []  # Failed downloads to retry
        self.seen_ads: Set[str] = set()  # Deduplication based on URL
        self.extracted_ads: List[AdRecord] = []
        self.downloaded_files: Set[str] = set()  # Track downloaded file paths

        # Load cached selectors for speed
        self.selectors = self._load_selectors()

        print("🧩 Facebook Ads Playwright Scraper initialized")
        print(f"📁 Output directory: {self.out_dir}")
        print(f"🖼️  Media directory: {self.media_dir}")

    def _load_selectors(self) -> Dict[str, List[str]]:
        """Load cached working selectors from selectors.json"""
        selectors_file = Path("selectors.json")

        # Default selectors with multiple fallbacks
        default_selectors = {
            "ad_cards": [
                "[data-testid='ad-card']",
                "[role='article']",
                "div[style*='border']:has(img)",
                ".x1n2onr6 > div > div",
            ],
            "media_images": [
                "img[src*='fbcdn']",
                "img[src*='safe_image.php']",
                "div[style*='background-image'][style*='fbcdn']",
                "[role='img']",
            ],
            "ad_text": ["[data-testid='ad-text']", "div[dir='auto']", "span[dir='auto']"],
            "cta_buttons": [
                "[data-testid='cta-button']",
                "a[role='button']",
                "button",
                "a[href*='facebook.com/tr']",
            ],
        }

        try:
            if selectors_file.exists():
                with open(selectors_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                print(f"✅ Loaded cached selectors from {selectors_file}")
                return {**default_selectors, **cached}
        except Exception as e:
            print(f"⚠️  Failed to load selectors: {e}")

        return default_selectors

    def _save_selectors(self):
        """Save working selectors to cache"""
        try:
            with open("selectors.json", "w", encoding="utf-8") as f:
                json.dump(self.selectors, f, indent=2)
            print("💾 Selectors cached for future runs")
        except Exception as e:
            print(f"⚠️  Failed to cache selectors: {e}")

    async def smart_scroll(self, page: Page) -> bool:
        """
        Smart scrolling with verification - returns True if new content appeared
        """
        last_height = await page.evaluate("document.body.scrollHeight")

        # Scroll in chunks, not all at once
        await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")

        # More reliable than networkidle
        await page.wait_for_timeout(1500)

        new_height = await page.evaluate("document.body.scrollHeight")
        return new_height > last_height  # True if new content appeared

    async def capture_media_responses(self, page: Page) -> Dict[str, Any]:
        """
        Capture media URLs from network responses
        """
        media_metadata = {}

        def handle_response(response):
            """Handle network responses for media capture"""
            try:
                url = response.url
                content_type = response.headers.get("content-type", "")

                # Capture if URL contains fbcdn.net or safe_image.php OR content-type is image/video
                if (
                    "fbcdn.net" in url
                    or "safe_image.php" in url
                    or content_type.startswith(("image/", "video/"))
                ):
                    if response.ok:
                        self.media_urls.add(url)
                        media_metadata[url] = {
                            "content_type": content_type,
                            "status": response.status,
                            "captured_at": datetime.now().isoformat(),
                        }
                    else:
                        # Add to retry queue for failed downloads
                        self.retry_queue.append(url)

            except Exception as e:
                print(f"⚠️  Response handler error: {e}")

        # Attach response handler
        page.on("response", handle_response)
        return media_metadata

    async def _scrape_text_from_cards(self, page: Page) -> List[AdRecord]:
        """
        FIXED: Better targeting of actual sponsored ad content
        """
        new_ads = []

        # Wait for content to stabilize
        print("⏳ Waiting for ad content to load...")
        try:
            await page.wait_for_selector("div", timeout=10000)
            await page.wait_for_timeout(3000)  # Let dynamic content settle
        except:
            print("⚠️  Timeout waiting for content")

        # FIXED: More robust ad container detection
        try:
            # Try multiple selectors to find ad containers
            validated_sponsored_cards = []
            facebook_interface_keywords = [
                "Meta Ad Library",
                "Ad Library Report",
                "Ad Library API",
                "Select country",
                "United States",
                "All ads",
                "Active status",
                "Platforms",
                "Filter",
                "results",
                "Subscribe to email",
                "System status",
                "FAQ",
                "About ads and data use",
                "Privacy",
                "Terms",
                "Cookies",
                "Launched",
                "Open Dropdown",
                "See ad details",
                "See summary details",
                "See more",
                "This ad has multiple versions",
                "use this creative and text",
                "Issues, elections or politics",
            ]

            # IMPROVED: More precise ad container detection
            container_selectors = [
                # Target actual ad containers with "Library ID" - this indicates real ads
                'div:has-text("Library ID:")',  # Most reliable indicator of real ads
                # Target containers with both "Sponsored" and meaningful content
                'div:has-text("Sponsored"):has(img)',  # Ads should have images
                # Fallback to broader selectors
                'div:has-text("Sponsored")',  # Most direct
                'div[role="main"] div',  # Broader container search
            ]

            print(f"🔍 Trying {len(container_selectors)} improved container selectors...")

            for i, selector in enumerate(container_selectors):
                try:
                    print(f"🔍 Trying selector {i + 1}: {selector}")
                    ad_containers = await page.query_selector_all(selector)
                    print(f"   Found {len(ad_containers)} potential containers")

                    candidate_containers = []

                    for container in ad_containers[
                        :50
                    ]:  # Process fewer but more relevant containers
                        try:
                            card_text = await container.inner_text()

                            # STRICT VALIDATION: Must be actual ad content
                            if self._is_valid_ad_container(card_text):
                                candidate_containers.append(container)
                                lines = [
                                    line.strip() for line in card_text.split("\n") if line.strip()
                                ]
                                preview_text = next(
                                    (
                                        line
                                        for line in lines
                                        if len(line) > 10 and "Library ID" not in line
                                    ),
                                    "No preview",
                                )
                                print(f"✅ Valid ad found: {preview_text[:50]}...")

                                # Take first few good candidates from each selector
                                if (
                                    len(candidate_containers) >= 5
                                ):  # Reduced limit for better quality
                                    break

                        except Exception as e:
                            continue

                    # If we found good candidates, use them
                    if candidate_containers:
                        validated_sponsored_cards.extend(candidate_containers)
                        print(f"✅ Selector {i + 1} found {len(candidate_containers)} valid ads")
                        break  # Stop trying other selectors if we found real ads

                except Exception as e:
                    print(f"⚠️  Selector {i + 1} failed: {e}")
                    continue

            print(f"🎯 Processing {len(validated_sponsored_cards)} validated sponsored ads")

            for card in validated_sponsored_cards:
                try:
                    ad = AdRecord()

                    # Extract all text from the card
                    card_text = await card.inner_text()
                    lines = [line.strip() for line in card_text.split("\n") if line.strip()]

                    # Better text extraction
                    ad.library_id = await self._extract_library_id_fixed(card, lines)
                    ad.page_name = await self._extract_page_name_fixed(card, lines)
                    ad.primary_text = await self._extract_primary_text_fixed(card, lines)
                    ad.headline = await self._extract_headline_fixed(card, lines)
                    ad.cta_label = await self._extract_cta_fixed(card, lines)
                    ad.date_started = await self._extract_date_fixed(card, lines)

                    # Legacy compatibility
                    ad.caption = ad.primary_text
                    ad.cta_text = ad.cta_label

                    # Media extraction
                    ad.media_urls = await self._extract_media_urls_fixed(card)

                    # Create source info
                    ad.source = {
                        "path": "fixed_dom_extraction",
                        "details": f"extracted_{len([x for x in [ad.primary_text, ad.headline, ad.cta_label] if x])}_text_fields",
                        "method": "line_parsing",
                    }

                    # Validation - must have some meaningful content
                    if any(
                        [ad.primary_text, ad.headline, ad.cta_label, ad.library_id, ad.media_urls]
                    ):
                        ad.ad_url = f"library_id:{ad.library_id}" if ad.library_id else None

                        # Deduplication
                        if ad.ad_url and ad.ad_url in self.seen_ads:
                            continue
                        if ad.ad_url:
                            self.seen_ads.add(ad.ad_url)

                        new_ads.append(ad)
                        print(
                            f"✅ Extracted ad: {ad.primary_text[:50] if ad.primary_text else 'No text'}..."
                        )

                except Exception as e:
                    print(f"⚠️  Error extracting ad: {e}")
                    continue

        except Exception as e:
            print(f"❌ Failed to find ad containers: {e}")

        print(f"✅ Fixed extraction completed: {len(new_ads)} ads found")
        return new_ads

    def _is_valid_ad_container(self, card_text: str) -> bool:
        """
        Validate if a container contains a real ad vs Facebook interface elements
        """
        if not card_text or len(card_text.strip()) < 20:
            return False

        # MUST contain "Sponsored" - this is the key indicator of ads
        if "Sponsored" not in card_text:
            return False

        # MUST contain "Library ID" - this confirms it's a real ad from the Ad Library
        if "Library ID:" not in card_text:
            return False

        # Check for reasonable length - real ads have substantial content
        if len(card_text) < 100 or len(card_text) > 5000:
            return False

        # Skip pure interface elements by checking for interface-heavy patterns
        interface_indicators = [
            "Meta Ad Library",
            "Ad Library Report",
            "Select country",
            "Filter results",
            "System status",
            "Subscribe to email",
            "About ads and data use",
        ]

        # Count interface indicators - if too many, it's likely interface
        interface_count = sum(1 for indicator in interface_indicators if indicator in card_text)
        if interface_count > 2:  # More than 2 interface indicators = likely interface
            return False

        # Look for positive ad indicators
        ad_indicators = [
            "Started running on",  # Date when ad started
            "Platforms",  # Where ad runs (Facebook, Instagram, etc.)
            "Shop now",  # Common CTA
            "Learn more",  # Common CTA
            "Sign up",  # Common CTA
            "Get started",  # Common CTA
        ]

        ad_indicator_count = sum(1 for indicator in ad_indicators if indicator in card_text)

        # Must have at least one positive ad indicator
        if ad_indicator_count < 1:
            return False

        # Additional validation: look for brand/company names after "Sponsored"
        lines = [line.strip() for line in card_text.split("\n") if line.strip()]
        sponsored_index = -1

        for i, line in enumerate(lines):
            if line == "Sponsored":
                sponsored_index = i
                break

        if sponsored_index >= 0 and sponsored_index + 1 < len(lines):
            next_line = lines[sponsored_index + 1]
            # The line after "Sponsored" should be a brand/company name
            if len(next_line) > 2 and len(next_line) < 100:  # Reasonable brand name length
                return True

        return False

    async def extract_cards_from_dom(self, page: Page) -> List[AdRecord]:
        """
        Extract ad card data from DOM after each scroll step - delegates to text scraper
        """
        return await self._scrape_text_from_cards(page)

    async def _extract_ad_url(self, card) -> Optional[str]:
        """Extract unique ad URL for deduplication"""
        try:
            # Look for data attributes or href that could be unique
            ad_id = await card.get_attribute("data-ad-id")
            if ad_id:
                return f"ad_id:{ad_id}"

            # Look for library ID in the card
            library_id_element = await card.query_selector("text=Library ID")
            if library_id_element:
                parent = await library_id_element.query_selector("xpath=..")
                if parent:
                    text = await parent.inner_text()
                    if "Library ID:" in text:
                        lib_id = text.split("Library ID:")[-1].strip().split()[0]
                        return f"library_id:{lib_id}"

            return None
        except:
            return None

    async def _extract_library_id(self, card) -> Optional[str]:
        """Extract Library ID from ad card"""
        try:
            # Look for "Library ID:" text
            element = await card.query_selector("text=Library ID")
            if element:
                parent = await element.query_selector("xpath=..")
                if parent:
                    text = await parent.inner_text()
                    if "Library ID:" in text:
                        return text.split("Library ID:")[-1].strip().split()[0]
        except:
            pass
        return None

    async def _extract_page_name(self, card) -> Optional[str]:
        """Extract page name/advertiser from ad card"""
        try:
            # Look for page name in various locations
            selectors = ["[role='link'][href*='/']", "a[href*='facebook.com']", "strong", "b"]
            for selector in selectors:
                element = await card.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) < 100:  # Reasonable page name length
                        return text.strip()
        except:
            pass
        return None

    def _classify_text_content(self, text: str) -> dict:
        """Classify extracted text into different ad components"""
        if not text:
            return {}

        text_lower = text.lower()
        classifications = {
            "is_hook": bool(
                re.search(
                    r"[🔥💥⚡️✨🎯]|sale|limited|ending|now|alert|urgent|breaking",
                    text,
                    re.IGNORECASE,
                )
            ),
            "is_offer": bool(
                re.search(r"\d+%\s*off|save|discount|free|deal|special|promo", text, re.IGNORECASE)
            ),
            "is_cta": len(text) < 20
            and any(
                word in text_lower
                for word in [
                    "shop",
                    "buy",
                    "get",
                    "learn",
                    "discover",
                    "try",
                    "start",
                    "join",
                    "book",
                    "call",
                ]
            ),
            "is_hashtag": "#" in text,
            "is_headline": 20 < len(text) < 150
            and not any(word in text_lower for word in ["shop", "buy", "get"]),
            "is_description": len(text) > 150,
            "has_urgency": bool(
                re.search(
                    r"limited|ending|hurry|last chance|while supplies last|act now",
                    text,
                    re.IGNORECASE,
                )
            ),
            "has_number": bool(re.search(r"\d+", text)),
        }
        return classifications

    async def _wait_for_text_content(self, page: Page, timeout: int = 5000) -> bool:
        """Wait for ad text content to fully load"""
        try:
            # Wait for text containers to appear with non-empty content
            await page.wait_for_selector("div[dir='auto']:not(:empty)", timeout=timeout)
            # Additional wait for dynamic content to stabilize
            await page.wait_for_timeout(1500)
            return True
        except:
            print("⚠️  Timeout waiting for text content to load")
            return False

    async def _extract_all_text_from_card(self, card) -> List[str]:
        """Extract all text content from ad card for classification"""
        all_texts = []
        try:
            # Get all text from various selectors
            text_selector_groups = ["ad_text_primary", "ad_text_fallback", "text_containers"]

            for group in text_selector_groups:
                if group in self.selectors:
                    for selector in self.selectors[group]:
                        try:
                            elements = await card.query_selector_all(selector)
                            for element in elements:
                                text = await element.inner_text()
                                if text and len(text.strip()) > 3:
                                    cleaned_text = text.strip()
                                    if cleaned_text not in all_texts:  # Avoid duplicates
                                        all_texts.append(cleaned_text)
                        except:
                            continue

            # Also try to get text from the entire card as fallback
            if not all_texts:
                try:
                    card_text = await card.inner_text()
                    if card_text:
                        # Split by lines and filter meaningful text
                        lines = [
                            line.strip()
                            for line in card_text.split("\n")
                            if line.strip() and len(line.strip()) > 3
                        ]
                        all_texts.extend(lines[:10])  # Limit to first 10 lines
                except:
                    pass

        except Exception as e:
            print(f"⚠️  Error extracting all text: {e}")

        return all_texts

    async def _extract_text_content(self, card, content_type: str) -> Optional[str]:
        """Enhanced text content extraction with classification"""
        try:
            # First extract all text from the card
            all_texts = await self._extract_all_text_from_card(card)

            if not all_texts:
                return None

            # Classify and select appropriate text based on content_type
            for text in all_texts:
                classification = self._classify_text_content(text)

                if content_type == "caption" or content_type == "primary_text":
                    # Look for longer descriptive text
                    if classification.get("is_description") or classification.get("is_headline"):
                        return text[:500]  # Limit length

                elif content_type == "headline":
                    # Look for medium-length headline text
                    if classification.get("is_headline") or (50 < len(text) < 200):
                        return text[:300]

                elif content_type == "hook":
                    # Look for attention-grabbing text with emojis or urgency
                    if classification.get("is_hook") or classification.get("has_urgency"):
                        return text[:200]

            # Fallback: return the longest meaningful text
            meaningful_texts = [t for t in all_texts if len(t) > 10]
            if meaningful_texts:
                return max(meaningful_texts, key=len)[:500]

        except Exception as e:
            print(f"⚠️  Error in enhanced text extraction: {e}")

        return None

    async def _extract_cta_text(self, card) -> Optional[str]:
        """Enhanced CTA button text extraction"""
        try:
            # Try enhanced CTA button selectors first
            cta_selectors = ["cta_buttons_enhanced", "cta_buttons"]

            for selector_group in cta_selectors:
                if selector_group in self.selectors:
                    for selector in self.selectors[selector_group]:
                        try:
                            elements = await card.query_selector_all(selector)
                            for element in elements:
                                text = await element.inner_text()
                                if text and len(text.strip()) < 50:  # CTA text is usually short
                                    cleaned_text = text.strip()
                                    classification = self._classify_text_content(cleaned_text)
                                    if classification.get("is_cta"):
                                        return cleaned_text
                        except:
                            continue

            # Fallback: look for CTA-like text in all extracted text
            all_texts = await self._extract_all_text_from_card(card)
            for text in all_texts:
                if len(text) < 30:  # Short text that might be a CTA
                    classification = self._classify_text_content(text)
                    if classification.get("is_cta"):
                        return text

        except Exception as e:
            print(f"⚠️  Error in enhanced CTA extraction: {e}")

        return None

    async def _extract_hooks_and_offers(self, card) -> tuple:
        """Extract hooks and offers separately"""
        hooks = []
        offers = []

        try:
            all_texts = await self._extract_all_text_from_card(card)

            for text in all_texts:
                classification = self._classify_text_content(text)

                if classification.get("is_hook") or classification.get("has_urgency"):
                    hooks.append(text)

                if classification.get("is_offer"):
                    offers.append(text)

        except Exception as e:
            print(f"⚠️  Error extracting hooks and offers: {e}")

        return (hooks[0] if hooks else None, offers[0] if offers else None)

    async def _extract_hashtags(self, card) -> List[str]:
        """Extract hashtags from ad card"""
        hashtags = []
        try:
            all_texts = await self._extract_all_text_from_card(card)

            for text in all_texts:
                # Find hashtags using regex
                found_hashtags = re.findall(r"#\w+", text)
                hashtags.extend(found_hashtags)

        except Exception as e:
            print(f"⚠️  Error extracting hashtags: {e}")

        return list(set(hashtags))  # Remove duplicates

    async def _extract_destination_url(self, card) -> Optional[str]:
        """Extract destination URL from ad card"""
        try:
            # Look for links within the card
            links = await card.query_selector_all("a[href]")
            for link in links:
                href = await link.get_attribute("href")
                if href and not href.startswith("javascript:"):
                    # Clean URL
                    if "?" in href:
                        href = href.split("?")[0]
                    return href
        except:
            pass
        return None

    async def _extract_media_urls(self, card) -> List[str]:
        """Extract media URLs from ad card"""
        media_urls = []
        try:
            # Extract from img src
            for selector in self.selectors["media_images"]:
                elements = await card.query_selector_all(selector)
                for element in elements:
                    src = await element.get_attribute("src")
                    if src and ("fbcdn" in src or "safe_image.php" in src):
                        media_urls.append(src)

                    # Check background-image style
                    style = await element.get_attribute("style") or ""
                    if "background-image" in style and "fbcdn" in style:
                        # Extract URL from background-image
                        start = style.find("url(") + 4
                        end = style.find(")", start)
                        if start > 3 and end > start:
                            bg_url = style[start:end].strip("\"'")
                            if "fbcdn" in bg_url:
                                media_urls.append(bg_url)
        except:
            pass

        return list(set(media_urls))  # Remove duplicates

    async def _extract_date_started(self, card) -> Optional[str]:
        """Extract date started from ad card"""
        try:
            # Look for date text patterns
            text = await card.inner_text()
            if "Started running on" in text:
                lines = text.split("\n")
                for line in lines:
                    if "Started running on" in line:
                        date_part = line.replace("Started running on", "").strip()
                        if "·" in date_part:
                            date_part = date_part.split("·")[0].strip()
                        return date_part
        except:
            pass
        return None

    # FIXED: New extraction methods for line-based parsing
    async def _extract_library_id_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract Library ID from parsed lines"""
        try:
            for line in lines:
                if "Library ID:" in line:
                    lib_id = line.split("Library ID:")[-1].strip().split()[0]
                    return lib_id
        except:
            pass
        return None

    async def _extract_page_name_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract page name from parsed lines"""
        try:
            # Look for "American Vintage" or similar brand names
            # Usually appears after "Sponsored" and before main ad text
            sponsored_index = -1
            for i, line in enumerate(lines):
                if line == "Sponsored":
                    sponsored_index = i
                    break

            if sponsored_index >= 0 and sponsored_index + 1 < len(lines):
                next_line = lines[sponsored_index + 1]
                # Filter out common interface elements
                if len(next_line) < 50 and not any(
                    skip in next_line
                    for skip in [
                        "Library ID",
                        "Started running",
                        "Platforms",
                        "See ad details",
                        "This ad has multiple",
                        "Open Dropdown",
                        "Learn more",
                    ]
                ):
                    return next_line
        except:
            pass
        return None

    async def _extract_primary_text_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract primary ad text from parsed lines"""
        try:
            # Skip interface lines and find actual ad content
            skip_patterns = [
                "Active",
                "Library ID",
                "Started running",
                "Platforms",
                "Sponsored",
                "See ad details",
                "See summary details",
                "This ad has multiple",
                "Open Dropdown",
                "Learn more",
                "Shop now",
                "Shop Now",
            ]

            meaningful_lines = []
            for line in lines:
                # Skip short lines and interface elements
                if (
                    len(line) > 20
                    and not any(skip in line for skip in skip_patterns)
                    and not line.isupper()
                ):  # Skip all caps lines (usually interface)
                    meaningful_lines.append(line)

            # Return the longest meaningful line as primary text
            if meaningful_lines:
                primary = max(meaningful_lines, key=len)
                return primary[:500]  # Limit length

        except Exception as e:
            print(f"⚠️  Error extracting primary text: {e}")
        return None

    async def _extract_headline_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract headline from parsed lines"""
        try:
            # Look for medium-length lines that could be headlines
            for line in lines:
                if (
                    30 < len(line) < 150
                    and "Sponsored" not in line
                    and "Library ID" not in line
                    and not line.endswith("...")
                ):  # Avoid truncated text
                    return line
        except:
            pass
        return None

    async def _extract_cta_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract CTA from parsed lines"""
        try:
            # Look for common CTA patterns
            cta_patterns = [
                "Shop now",
                "Shop Now",
                "Learn more",
                "Get started",
                "Sign up",
                "Buy now",
            ]
            for line in lines:
                if line in cta_patterns or any(pattern in line for pattern in cta_patterns):
                    return line
        except:
            pass
        return None

    async def _extract_date_fixed(self, card, lines: List[str]) -> Optional[str]:
        """Extract start date from parsed lines"""
        try:
            for line in lines:
                if "Started running on" in line:
                    date_part = line.replace("Started running on", "").strip()
                    return date_part
        except:
            pass
        return None

    async def _extract_media_urls_fixed(self, card) -> List[str]:
        """Extract media URLs with improved targeting"""
        media_urls = []
        try:
            # Look for images with fbcdn URLs
            images = await card.query_selector_all("img[src*='fbcdn']")
            for img in images:
                src = await img.get_attribute("src")
                if src and "fbcdn" in src:
                    # Skip tiny images (likely profile pics or icons)
                    width = await img.get_attribute("width")
                    height = await img.get_attribute("height")
                    if (not width or int(width) > 100) and (not height or int(height) > 100):
                        media_urls.append(src)

            # Also look for video elements
            videos = await card.query_selector_all("video[src*='fbcdn']")
            for video in videos:
                src = await video.get_attribute("src")
                if src:
                    media_urls.append(src)

        except Exception as e:
            print(f"⚠️  Error extracting media URLs: {e}")

        return list(set(media_urls))  # Remove duplicates

    async def _handle_errors(self, page: Page):
        """Handle common errors during scraping"""
        try:
            # Handle "No results found"
            no_results = await page.query_selector("text=No results found")
            if no_results:
                print("ℹ️  No results found - exiting gracefully")
                return "no_results"

            # Handle cookie banner
            cookie_accept = await page.query_selector(
                "button:has-text('Accept'), button:has-text('Allow')"
            )
            if cookie_accept:
                print("🍪 Accepting cookies...")
                await cookie_accept.click()
                await page.wait_for_timeout(1000)

        except Exception as e:
            print(f"⚠️  Error handling: {e}")

        return None

    async def _save_checkpoint(self):
        """Save progress checkpoint every 50 ads"""
        if len(self.extracted_ads) % 50 == 0 and len(self.extracted_ads) > 0:
            checkpoint_file = self.out_dir / "checkpoint.json"
            checkpoint_data = {
                "ads_count": len(self.extracted_ads),
                "timestamp": datetime.now().isoformat(),
                "seen_ads_count": len(self.seen_ads),
                "media_urls_count": len(self.media_urls),
            }

            try:
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(checkpoint_data, f, indent=2)
                print(f"💾 Checkpoint saved: {len(self.extracted_ads)} ads")
            except Exception as e:
                print(f"⚠️  Failed to save checkpoint: {e}")

    def _sanitize_filename(self, url: str, ad_id: Optional[str] = None) -> str:
        """Generate a safe filename from URL"""
        # Extract file extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = ""

        if "." in path:
            ext = path.split(".")[-1]
            # Limit extension length and only allow common formats
            if ext.lower() in ["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi"]:
                ext = f".{ext.lower()}"
            else:
                ext = ".jpg"  # Default to jpg
        else:
            ext = ".jpg"  # Default extension

        # Create filename based on ad_id or timestamp
        if ad_id:
            filename = f"{ad_id}_{datetime.now().strftime('%H%M%S')}{ext}"
        else:
            # Use part of URL hash for uniqueness
            url_hash = str(hash(url))[-8:]  # Last 8 chars of hash
            filename = f"media_{url_hash}{ext}"

        # Remove any unsafe characters
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        return filename

    async def _download_media_file(self, url: str, ad_id: Optional[str] = None) -> Optional[str]:
        """Download a media file and return the local path"""
        try:
            filename = self._sanitize_filename(url, ad_id)
            local_path = self.media_dir / filename

            # Skip if already downloaded
            if str(local_path) in self.downloaded_files:
                return str(local_path)

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                ) as response:
                    if response.status == 200:
                        async with aiofiles.open(local_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)

                        self.downloaded_files.add(str(local_path))
                        print(f"📥 Downloaded: {filename}")
                        return str(local_path)
                    else:
                        print(f"⚠️  Failed to download {url}: HTTP {response.status}")
                        self.retry_queue.append(url)
                        return None

        except Exception as e:
            print(f"⚠️  Download error for {url}: {e}")
            self.retry_queue.append(url)
            return None

    async def _scrape_media_from_ads(self, ads: List[AdRecord]) -> List[AdRecord]:
        """Separate function to scrape media from extracted ads"""
        print(f"🖼️  Processing media for {len(ads)} ads...")

        media_download_count = 0
        max_media_downloads = 10  # Limit for testing

        for ad in ads:
            if media_download_count >= max_media_downloads:
                print(f"📊 Reached media download limit: {max_media_downloads}")
                break

            if ad.media_urls:
                print(
                    f"🔍 Processing {len(ad.media_urls)} media URLs for ad {ad.library_id or 'unknown'}"
                )

                # Convert URLs to MediaItem objects with downloads
                media_items = []
                for url in ad.media_urls[:3]:  # Max 3 media per ad
                    if media_download_count >= max_media_downloads:
                        break

                    # Determine media type
                    media_type = "image"
                    if any(ext in url.lower() for ext in [".mp4", ".mov", ".avi", "video"]):
                        media_type = "video"

                    # Download the file
                    local_path = await self._download_media_file(url, ad.library_id)

                    if local_path:
                        media_download_count += 1

                    media_item = MediaItem(type=media_type, url=url, local_path=local_path)

                    media_items.append(media_item)

                # Update ad with new media structure
                ad.media = media_items

        print(f"✅ Downloaded {media_download_count} media files")
        return ads

    async def _retry_failed_media(self):
        """Retry failed media downloads with direct fetch"""
        if not self.retry_queue:
            return

        print(f"🔄 Retrying {len(self.retry_queue)} failed media URLs...")

        # Actual retry with file download
        retried = 0
        failed_urls = self.retry_queue.copy()
        self.retry_queue.clear()

        for url in failed_urls[:5]:  # Limit retries per batch
            try:
                local_path = await self._download_media_file(url)
                if local_path:
                    self.media_urls.add(url)
                    retried += 1
                else:
                    # Still failed, keep in retry queue
                    self.retry_queue.append(url)
            except Exception as e:
                print(f"⚠️  Retry failed for {url}: {e}")
                self.retry_queue.append(url)

        print(f"✅ Successfully retried {retried} media downloads")
        if self.retry_queue:
            print(f"   🔄 {len(self.retry_queue)} URLs still in retry queue")

    async def run_scrape(
        self, url: str, max_scrolls: int = 50, brand_name: str = "FacebookAds"
    ) -> Dict[str, Any]:
        """
        Main scraping coordinator - runs the complete scrape process

        Args:
            url: Facebook Ads Library URL
            max_scrolls: Maximum number of scroll attempts
            brand_name: Brand name for output files

        Returns:
            Dictionary with scraping results and metadata
        """
        start_time = datetime.now()

        # Generate unique identifier for this test
        unique_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        unique_brand = f"{brand_name}_Test_{unique_timestamp}"

        print(f"🚀 Starting Facebook Ads scrape - UNIQUE TEST")
        print(f"🔗 URL: {url}")
        print(f"📊 Max scrolls: {max_scrolls}")
        print(f"🏷️  Brand: {unique_brand}")
        print(f"🆔 Test ID: {unique_timestamp}")

        async with async_playwright() as p:
            # Browser setup following clean instructions
            browser = await p.chromium.launch(
                headless=False,  # headless=False for detection avoidance
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Standard desktop viewport
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},  # Standard size
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            page = await context.new_page()

            try:
                # Set up network capture
                media_metadata = await self.capture_media_responses(page)

                print("🌐 Navigating to Facebook Ads Library...")
                await page.goto(url, timeout=60000)

                # Handle initial errors
                error_status = await self._handle_errors(page)
                if error_status == "no_results":
                    return {"success": False, "error": "No results found"}

                # Smart scrolling loop
                consecutive_no_content = 0
                scroll_count = 0

                print("📜 Starting smart scroll loop...")

                while scroll_count < max_scrolls:
                    print(f"📜 Scroll {scroll_count + 1}/{max_scrolls}")

                    # Extract ads from current DOM state
                    new_ads = await self.extract_cards_from_dom(page)
                    self.extracted_ads.extend(new_ads)

                    # Save checkpoint every 50 ads
                    await self._save_checkpoint()

                    # Smart scroll with verification
                    has_new_content = await self.smart_scroll(page)

                    if has_new_content:
                        consecutive_no_content = 0
                        print("✅ New content loaded")
                    else:
                        consecutive_no_content += 1
                        print(f"⏸️  No new content ({consecutive_no_content}/2)")

                    # Stop if no new content appears twice in a row
                    if consecutive_no_content >= 2:
                        print("🏁 No more content - stopping")
                        break

                    scroll_count += 1

                    # Rate limiting: 800-1500ms between scrolls
                    delay = random.randint(800, 1500)
                    await page.wait_for_timeout(delay)

                # Final extraction after scrolling completes
                print("🔍 Final DOM extraction...")
                final_ads = await self.extract_cards_from_dom(page)
                self.extracted_ads.extend(final_ads)

                # Separate media scraping phase - download actual files
                print("🖼️  Starting media downloading phase...")
                self.extracted_ads = await self._scrape_media_from_ads(self.extracted_ads)

                # Retry failed media downloads
                await self._retry_failed_media()

                print(f"✅ Scraping completed!")
                print(f"   📱 Total ads extracted: {len(self.extracted_ads)}")
                print(f"   🖼️  Media URLs captured: {len(self.media_urls)}")
                print(f"   📜 Scrolls performed: {scroll_count}")

                # Create results
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                results = {
                    "success": True,
                    "timestamp": start_time.isoformat(),
                    "duration_seconds": duration,
                    "brand": brand_name,
                    "url": url,
                    "scrape_method": "Playwright - Clean Implementation",
                    "metrics": {
                        "total_ads": len(self.extracted_ads),
                        "unique_ads": len(self.seen_ads),
                        "media_urls": len(self.media_urls),
                        "scrolls_performed": scroll_count,
                        "retry_queue_remaining": len(self.retry_queue),
                    },
                    "ads": [asdict(ad) for ad in self.extracted_ads],
                    "media_urls": list(self.media_urls),
                    "config": {
                        "headless": False,
                        "viewport": "1920x1080",
                        "max_scrolls": max_scrolls,
                        "rate_limit": "800-1500ms",
                    },
                }

                # Save results
                await self._save_results(results, brand_name)

                # Save working selectors
                self._save_selectors()

                return results

            except Exception as e:
                print(f"❌ Scraping failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": start_time.isoformat(),
                    "ads_extracted": len(self.extracted_ads),
                }

            finally:
                await browser.close()

    async def _save_results(self, results: Dict[str, Any], brand_name: str):
        """Save scraping results to timestamped files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = self.out_dir / f"facebook_ads_playwright_{brand_name}_{timestamp}.json"
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Results saved to: {json_file}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")

        # Save CSV summary
        csv_file = self.out_dir / f"facebook_ads_playwright_{brand_name}_{timestamp}.csv"
        try:
            import csv

            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                if results["ads"]:
                    writer = csv.DictWriter(f, fieldnames=results["ads"][0].keys())
                    writer.writeheader()
                    writer.writerows(results["ads"])
            print(f"📊 CSV saved to: {csv_file}")
        except Exception as e:
            print(f"⚠️  Failed to save CSV: {e}")


async def main():
    """Main execution function"""
    print("🧩 Facebook Ads Library Scraper - Clean Playwright Implementation")
    print("=" * 70)
    print("✅ FEATURES: Smart scrolling, network capture, checkpointing")
    print("✅ APPROACH: Direct browser automation with Playwright")
    print("=" * 70)

    scraper = FacebookAdsPlaywrightScraper()

    # User-provided specific Facebook ads library URL for testing enhanced text extraction
    test_url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=109406860675"

    # Run the scraper with limited settings for testing
    results = await scraper.run_scrape(
        url=test_url,
        max_scrolls=5,  # Moderate scrolls to test text extraction thoroughly
        brand_name="HustleButterDeluxe_Enhanced",
    )

    if results["success"]:
        print("\n🎉 SCRAPING SUCCESS!")
        print(f"   📱 Total ads: {results['metrics']['total_ads']}")
        print(f"   🖼️  Media URLs: {results['metrics']['media_urls']}")
        print(f"   📜 Scrolls: {results['metrics']['scrolls_performed']}")
        print(f"   ⏱️  Duration: {results['duration_seconds']:.1f}s")
        print("\n💡 Clean Playwright implementation working!")
    else:
        print(f"\n❌ SCRAPING FAILED: {results.get('error', 'Unknown error')}")

    return results


if __name__ == "__main__":
    # Install playwright if needed
    print("🔧 Checking Playwright installation...")
    try:
        import playwright

        print("✅ Playwright is installed")
    except ImportError:
        print("❌ Installing playwright...")
        os.system("pip install playwright")
        os.system("playwright install chromium")

    # Run the scraper
    results = asyncio.run(main())
    print("\n👋 Scraping complete!")
