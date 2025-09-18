"""Facebook Ad Library scraper using Playwright."""

import logging
import time
from datetime import datetime
from typing import Any

from playwright.sync_api import Browser, Page, sync_playwright

logger = logging.getLogger(__name__)


class FacebookAdScraper:
    """Facebook Ad Library scraper with GraphQL interception."""

    def __init__(self, headless: bool = True, max_scrolls: int = 10):
        self.headless = headless
        self.max_scrolls = max_scrolls
        self.intercepted_data: list[dict[str, Any]] = []
        self.browser: Browser | None = None
        self.page: Page | None = None

    def _setup_browser(self):
        """Initialize browser and page."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()

        # Set up request interception for GraphQL
        self.page.on("response", self._intercept_graphql_response)

    def _intercept_graphql_response(self, response):
        """Intercept GraphQL responses containing ad data."""
        if "graphql" in response.url and response.status == 200:
            try:
                data = response.json()
                if self._is_ad_library_response(data):
                    ads = self._extract_ads_from_response(data)
                    self.intercepted_data.extend(ads)
                    logger.info(f"Intercepted {len(ads)} ads from GraphQL response")
            except Exception as e:
                logger.debug(f"Error processing GraphQL response: {e}")

    def _is_ad_library_response(self, data: dict[str, Any]) -> bool:
        """Check if response contains Facebook Ad Library data."""
        try:
            # Look for typical Ad Library GraphQL structure
            if isinstance(data, dict) and "data" in data:
                data_content = data["data"]
                if isinstance(data_content, dict):
                    # Check for ad library specific fields
                    for key in data_content:
                        if key and isinstance(data_content[key], dict):
                            edges = data_content[key].get("edges", [])
                            if edges and isinstance(edges, list):
                                # Check if edges contain ad-like data
                                for edge in edges[:3]:  # Check first few edges
                                    node = edge.get("node", {})
                                    if self._looks_like_ad_data(node):
                                        return True
            return False
        except Exception:
            return False

    def _looks_like_ad_data(self, node: dict[str, Any]) -> bool:
        """Check if node looks like ad data."""
        ad_indicators = [
            "snapshot",
            "creative",
            "page_name",
            "page_id",
            "ad_snapshot_metadata",
            "cards",
            "title",
            "body",
        ]
        return any(indicator in node for indicator in ad_indicators)

    def _extract_ads_from_response(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract ad data from GraphQL response."""
        ads = []

        try:
            data_content = data.get("data", {})
            for key in data_content:
                if isinstance(data_content[key], dict):
                    edges = data_content[key].get("edges", [])
                    for edge in edges:
                        node = edge.get("node", {})
                        if self._looks_like_ad_data(node):
                            ad = self._parse_ad_node(node)
                            if ad:
                                ads.append(ad)

        except Exception as e:
            logger.error(f"Error extracting ads from response: {e}")

        return ads

    def _parse_ad_node(self, node: dict[str, Any]) -> dict[str, Any] | None:
        """Parse individual ad node into structured data."""
        try:
            ad = {
                "id": "",
                "brand": "",
                "page_name": "",
                "headline": "",
                "body": "",
                "call_to_action": "",
                "media_type": "",
                "media_urls": [],
                "target_audience": {},
                "created_date": "",
                "scraped_at": datetime.now().isoformat(),
                "raw_data": node,
            }

            # Extract page info
            if "page_name" in node:
                ad["page_name"] = node["page_name"]
                ad["brand"] = node["page_name"]

            # Extract snapshot data
            snapshot = node.get("snapshot", {})
            if snapshot:
                # Extract cards/creative content
                cards = snapshot.get("cards", [])
                if cards:
                    card = cards[0]  # First card usually has main content
                    ad["headline"] = card.get("title", "")
                    ad["body"] = card.get("body", "")

                    # Extract media
                    if "snapshot" in card:
                        card_snapshot = card["snapshot"]
                        if "images" in card_snapshot:
                            ad["media_type"] = "image"
                            ad["media_urls"] = [
                                img.get("original_image_url", "") for img in card_snapshot["images"]
                            ]
                        elif "videos" in card_snapshot:
                            ad["media_type"] = "video"
                            ad["media_urls"] = [
                                vid.get("video_preview_image_url", "")
                                for vid in card_snapshot["videos"]
                            ]

                # Extract CTA
                cta = snapshot.get("cta_text", "") or snapshot.get("link_url", "")
                ad["call_to_action"] = cta

            # Generate ID from available data
            ad["id"] = self._generate_ad_id(node)

            # Only return if we have meaningful data
            if ad["page_name"] or ad["headline"] or ad["body"]:
                return ad

        except Exception as e:
            logger.error(f"Error parsing ad node: {e}")

        return None

    def _generate_ad_id(self, node: dict[str, Any]) -> str:
        """Generate unique ID for ad."""
        page_name = node.get("page_name", "")
        snapshot = node.get("snapshot", {})
        cards = snapshot.get("cards", [])
        title = cards[0].get("title", "") if cards else ""

        # Use hash of key fields
        import hashlib

        data_str = f"{page_name}_{title}_{snapshot.get('cta_text', '')}"
        return hashlib.md5(data_str.encode()).hexdigest()[:12]

    def scrape_ads(self, url: str) -> list[dict[str, Any]]:
        """Scrape ads from Facebook Ad Library URL."""
        if not self.browser:
            self._setup_browser()

        try:
            print(f"Navigating to: {url}")
            self.page.goto(url, wait_until="networkidle")

            # Wait for initial load
            time.sleep(3)

            print("Starting to scroll and capture data...")
            scroll_count = 0

            while scroll_count < self.max_scrolls:
                # Scroll down
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                # Wait for new content to load
                time.sleep(2)

                scroll_count += 1
                print(
                    f"Scroll {scroll_count}/{self.max_scrolls} - Total ads captured: {len(self.intercepted_data)}"
                )

                # Check if we've reached the end
                if scroll_count > 5:  # Give some scrolls to check
                    current_height = self.page.evaluate("document.body.scrollHeight")
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    new_height = self.page.evaluate("document.body.scrollHeight")

                    if current_height == new_height:
                        print("Reached end of page")
                        break

            print(f"Scraping completed. Total ads intercepted: {len(self.intercepted_data)}")
            return self.intercepted_data

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise

    def close(self):
        """Close browser and cleanup."""
        if self.browser:
            self.browser.close()
        if hasattr(self, "playwright"):
            self.playwright.stop()
