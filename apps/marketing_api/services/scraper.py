import logging
from datetime import datetime

import httpx
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class CompetitorAdsScraper:
    def __init__(self, firecrawl_api_key: str = None, openai_api_key: str = None):
        self.fb_library_url = "https://www.facebook.com/ads/library"
        self.tiktok_library_url = "https://library.ads.tiktok.com"
        self.firecrawl_api_key = firecrawl_api_key
        self.openai_api_key = openai_api_key

    async def scrape_facebook_ads_with_firecrawl(
        self, brand: str, country: str = "US", active_only: bool = True, max_pages: int = 3
    ) -> list[dict]:
        """Scrape Facebook Ad Library using Firecrawl with AI extraction"""

        if not self.firecrawl_api_key:
            logger.error("Firecrawl API key not provided")
            return []

        try:
            # Build search URL
            search_url = f"{self.fb_library_url}/?active_status={'active' if active_only else 'all'}&ad_type=all&country={country}&q={brand}"
            logger.info(f"Scraping Facebook ads for {brand} from: {search_url}")

            # Use Firecrawl to scrape with AI extraction
            async with httpx.AsyncClient(timeout=60.0) as client:
                scrape_response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {self.firecrawl_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "url": search_url,
                        "formats": ["extract"],
                        "extract": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "ads": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ad_text": {
                                                    "type": "string",
                                                    "description": "The main ad copy/text content",
                                                },
                                                "headline": {
                                                    "type": "string",
                                                    "description": "Ad headline if visible",
                                                },
                                                "cta_button": {
                                                    "type": "string",
                                                    "description": "Call-to-action button text",
                                                },
                                                "page_name": {
                                                    "type": "string",
                                                    "description": "Advertiser page name",
                                                },
                                                "ad_status": {
                                                    "type": "string",
                                                    "description": "Ad status (active, inactive, etc.)",
                                                },
                                                "media_type": {
                                                    "type": "string",
                                                    "description": "Type of media (image, video, carousel)",
                                                },
                                                "engagement": {
                                                    "type": "object",
                                                    "properties": {
                                                        "likes": {"type": "number"},
                                                        "comments": {"type": "number"},
                                                        "shares": {"type": "number"},
                                                    },
                                                },
                                            },
                                            "required": ["ad_text", "page_name"],
                                        },
                                    }
                                },
                                "required": ["ads"],
                            },
                            "prompt": f"Extract all Facebook ads for the brand '{brand}' from this Facebook Ad Library page. Focus on getting the ad copy text, headlines, CTA buttons, advertiser names, and any engagement metrics visible. Look for ads in article elements or ad containers.",
                        },
                        "waitFor": 3000,
                        "actions": [
                            {"type": "wait", "milliseconds": 2000},
                            {"type": "scroll", "direction": "down", "amount": 3},
                        ],
                    },
                )

                if scrape_response.status_code != 200:
                    logger.error(
                        f"Firecrawl scraping failed: {scrape_response.status_code} - {scrape_response.text}"
                    )
                    return []

                scrape_data = scrape_response.json()

                if not scrape_data.get("success") or not scrape_data.get("data", {}).get("extract"):
                    logger.error(f"Firecrawl extraction failed: {scrape_data}")
                    return []

                extracted_data = scrape_data["data"]["extract"]
                ads_data = extracted_data.get("ads", [])

                if not ads_data:
                    logger.warning(f"No ads found for brand: {brand}")
                    return []

                # Process and structure the extracted ads
                structured_ads = []
                for i, ad in enumerate(ads_data):
                    if not ad.get("ad_text"):  # Skip ads without text content
                        continue

                    structured_ad = {
                        "platform": "facebook",
                        "brand": brand,
                        "ad_id": f"fb_{brand}_{i}_{int(datetime.now().timestamp())}",
                        "copy": ad.get("ad_text", ""),
                        "headline": ad.get("headline", ""),
                        "cta": ad.get("cta_button", ""),
                        "page_name": ad.get("page_name", ""),
                        "status": ad.get("ad_status", "active"),
                        "media_type": ad.get("media_type", "unknown"),
                        "likes": ad.get("engagement", {}).get("likes", 0),
                        "comments": ad.get("engagement", {}).get("comments", 0),
                        "shares": ad.get("engagement", {}).get("shares", 0),
                        "scraped_at": datetime.now().isoformat(),
                        "source_url": search_url,
                    }
                    structured_ads.append(structured_ad)

                logger.info(f"Successfully extracted {len(structured_ads)} ads for {brand}")
                return structured_ads

        except Exception as e:
            logger.error(f"Error scraping Facebook ads for {brand} with Firecrawl: {e}")
            return []

    # Keep the old method as fallback
    async def scrape_facebook_ads(
        self, brand: str, country: str = "US", active_only: bool = True
    ) -> list[dict]:
        """Main Facebook scraping method - uses Firecrawl if available, fallback to mock data"""

        if self.firecrawl_api_key:
            return await self.scrape_facebook_ads_with_firecrawl(brand, country, active_only)
        logger.warning("No Firecrawl API key provided, returning mock data")
        # Return mock data for testing
        return [
            {
                "platform": "facebook",
                "brand": brand,
                "ad_id": f"fb_mock_{brand}_001",
                "copy": f"Sample Facebook ad copy for {brand}",
                "headline": f"Amazing {brand} Products",
                "cta": "Shop Now",
                "page_name": f"{brand} Official",
                "status": "active",
                "media_type": "image",
                "likes": 150,
                "comments": 25,
                "shares": 10,
                "scraped_at": datetime.now().isoformat(),
                "source_url": f"https://facebook.com/ads/library/?q={brand}",
            }
        ]

    async def scrape_tiktok_ads(self, brand: str, country: str = "US") -> list[dict]:
        """Scrape TikTok Ad Library"""

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Navigate to TikTok Ad Library
                search_url = f"{self.tiktok_library_url}/search?q={brand}&country={country}"
                await page.goto(search_url)

                # Wait for ads to load
                await page.wait_for_selector(".ad-item", timeout=10000)

                # Extract ad data
                ads = await page.evaluate(
                    """
                    () => {
                        const adElements = document.querySelectorAll('.ad-item');
                        return Array.from(adElements).map(ad => {
                            const getText = (selector) => {
                                const el = ad.querySelector(selector);
                                return el ? el.textContent.trim() : null;
                            };

                            return {
                                id: ad.getAttribute('data-ad-id') || Date.now().toString(),
                                text: getText('.ad-text'),
                                cta: getText('.ad-cta'),
                                brand_name: getText('.brand-name'),
                                video_url: ad.querySelector('video source') ? ad.querySelector('video source').src : null,
                                thumbnail: ad.querySelector('.ad-thumbnail img') ? ad.querySelector('.ad-thumbnail img').src : null
                            };
                        });
                    }
                """
                )

                await browser.close()

                # Process and return structured data
                return [
                    {
                        "platform": "tiktok",
                        "brand": brand,
                        "ad_id": ad["id"],
                        "copy": ad["text"],
                        "cta": ad["cta"],
                        "brand_name": ad["brand_name"],
                        "media_type": "video" if ad["video_url"] else "image",
                        "media_urls": [ad["video_url"] or ad["thumbnail"]],
                        "thumbnail_url": ad["thumbnail"],
                        "scraped_at": datetime.now().isoformat(),
                    }
                    for ad in ads
                    if ad["text"]
                ]

        except Exception as e:
            logger.error(f"Error scraping TikTok ads for {brand}: {e}")
            return []

    async def scrape_multiple_platforms(
        self, brands: list[str], platforms: list[str] = None
    ) -> list[dict]:
        """Scrape ads from multiple platforms and brands"""

        if platforms is None:
            platforms = ["facebook", "tiktok"]
        all_ads = []

        for brand in brands:
            if "facebook" in platforms:
                fb_ads = await self.scrape_facebook_ads(brand)
                all_ads.extend(fb_ads)

            if "tiktok" in platforms:
                tiktok_ads = await self.scrape_tiktok_ads(brand)
                all_ads.extend(tiktok_ads)

        return all_ads
