#!/usr/bin/env python3
"""
Firecrawl Integration for AdSpy Marketing Intelligence Suite
Interactive menu for choosing Firecrawl scraping methods
"""

import json
import os
import sys
from datetime import datetime
from typing import Any

try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("❌ Firecrawl not installed. Install with: pip install firecrawl-py")
    sys.exit(1)

from core.config import load_config
from core.utils import generate_url_slug, sanitize_search_query

from .facebook_simple_config import (
    FACEBOOK_ADS_ENHANCED_CONFIG,
    FACEBOOK_ADS_EU_CONFIG,
    FACEBOOK_ADS_SIMPLE_CONFIG,
    AdDeduplicator,
    DateRangeFilter,
    build_url_with_date_filter,
)

# Constants
DEFAULT_TIMEOUT = 60000
DEFAULT_CRAWL_LIMIT = 20
DEFAULT_CRAWL_DEPTH = 2
DEFAULT_SEARCH_LIMIT = 5
OUTPUT_DIR = "data/firecrawl_results"
MAX_ADS_DISPLAY = 10

# Menu configuration
MENU_OPTIONS = [
    {
        "num": "1",
        "name": "SCRAPE",
        "desc": "Scrape a single URL into clean formats (markdown, HTML, JSON, screenshot).",
        "example": """doc = firecrawl.scrape(
    "https://example.com",
    formats=["markdown","html","screenshot"],
    only_main_content=True,
    timeout=60000
)""",
    },
    {
        "num": "2",
        "name": "CRAWL",
        "desc": "Discover and scrape all accessible subpages of a site.",
        "example": """docs = firecrawl.crawl(
    url="https://example.com",
    limit=20,         # max pages
    depth=2           # crawl depth
)""",
    },
    {
        "num": "3",
        "name": "MAP",
        "desc": "Get all URLs of a site extremely fast (no content, just structure).",
        "example": """urls = firecrawl.map("https://example.com")""",
    },
    {
        "num": "4",
        "name": "SEARCH",
        "desc": "Perform a web/news/image search with full content results.",
        "example": """results = firecrawl.search(
    query="firecrawl AI",
    limit=5,
    sources=["web","news","images"]
)""",
    },
    {
        "num": "5",
        "name": "EXTRACT",
        "desc": "Use AI to extract structured data.",
        "example": """# With schema:
from pydantic import BaseModel
class Schema(BaseModel):
    mission: str
    is_open_source: bool
result = firecrawl.scrape(
    "https://example.com",
    formats=[{"type":"json","schema":Schema}]
)

# With prompt:
result = firecrawl.scrape(
    "https://example.com", 
    formats=[{"type":"json","prompt":"Extract company mission"}]
)""",
    },
    {
        "num": "6",
        "name": "ACTIONS",
        "desc": "Interact with dynamic content before scraping.",
        "example": """doc = firecrawl.scrape(
    "https://example.com/login",
    formats=["markdown"],
    actions=[
        { "type": "write", "text": "john@example.com" },
        { "type": "press", "key": "Tab" },
        { "type": "write", "text": "mypassword" },
        { "type": "click", "selector": "button[type='submit']" },
        { "type": "wait", "milliseconds": 2000 },
        { "type": "screenshot", "fullPage": True }
    ]
)""",
    },
    {
        "num": "7",
        "name": "FACEBOOK ADS",
        "desc": "🎯 Specialized scraping for Facebook Ad Library with smart ad detection.",
        "example": """# Scrape Nike's Facebook ads
result = firecrawl.scrape(
    facebook_ads_url,
    **FACEBOOK_ADS_CONFIG
)

# Popular brands: nike, adidas, amazon, walmart, target
# Or provide custom page ID or search terms""",
    },
]


class FirecrawlManager:
    """Manages Firecrawl operations with interactive menu"""

    def __init__(self):
        """Initialize Firecrawl with API key from config"""
        config = load_config()
        api_key = getattr(config, "firecrawl_api_key", None)
        if not api_key:
            print("❌ FIRECRAWL_API_KEY not found in .env file")
            sys.exit(1)

        self.firecrawl = FirecrawlApp(api_key=api_key)

    def show_menu(self) -> None:
        """Display the main Firecrawl menu"""
        print("\n" + "=" * 80)
        print("🔥 Welcome to Firecrawl — Choose a method to run:")
        print("=" * 80)

        for option in MENU_OPTIONS:
            print(f"\n{option['num']}. {option['name']} → {option['desc']}")
            print("   Example:")
            for line in option["example"].split("\n"):
                print(f"   {line}")

        self._print_menu_footer()

    def _print_menu_footer(self) -> None:
        """Print menu tips and footer"""
        print("\n" + "-" * 80)
        print("💡 TIP: You can combine options.")
        print('- Add multiple formats: ["markdown","html","json"]')
        print("- Increase crawl depth for larger sites")
        print("- Use actions to scroll or click before scraping")
        print("-" * 80)

    def get_user_choice(self) -> str:
        """Get user's menu choice with validation"""
        valid_choices = [option["num"] for option in MENU_OPTIONS]
        while True:
            choice = input(
                f"\nEnter the method number (1–{len(MENU_OPTIONS)}) you want to run: "
            ).strip()
            if choice in valid_choices:
                return choice
            print(f"❌ Invalid choice. Please enter a number from 1-{len(MENU_OPTIONS)}.")

    def _get_url_input(self, prompt: str) -> str | None:
        """Get URL input from user with validation"""
        url = input(prompt).strip()
        if not url:
            print("❌ URL is required")
            return None
        return url

    def _get_integer_input(self, prompt: str, default: int) -> int | None:
        """Get integer input from user with validation"""
        try:
            value = input(f"{prompt} [{default}]: ").strip() or str(default)
            return int(value)
        except ValueError:
            print("❌ Invalid number")
            return None

    def _get_list_input(self, prompt: str, default: str, separator: str = ",") -> list[str]:
        """Get comma-separated list input from user"""
        input_value = input(f"{prompt} [{default}]: ").strip() or default
        return [item.strip() for item in input_value.split(separator)]

    def _execute_firecrawl_operation(
        self,
        operation_name: str,
        operation_func,
        filename_base: str,
        progress_message: str | None = None,
    ) -> None:
        """Execute a Firecrawl operation with error handling"""
        try:
            if progress_message:
                print(f"\n🚀 {progress_message}...")
            else:
                print(f"\n🚀 Running {operation_name} operation...")

            result = operation_func()
            self._save_and_display_result(operation_name, result, filename_base)
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_scrape(self) -> None:
        """Execute SCRAPE method"""
        print("\n🔥 Running SCRAPE method...")

        url = self._get_url_input("Enter URL to scrape: ")
        if not url:
            return

        print("\nSelect formats (comma-separated):")
        print("Options: markdown, html, json, screenshot, links")
        formats = self._get_list_input("Formats", "markdown")

        only_main = input("Extract only main content? (y/N): ").strip().lower() == "y"

        self._execute_firecrawl_operation(
            "scrape",
            lambda: self.firecrawl.scrape(
                url, formats=formats, only_main_content=only_main, timeout=DEFAULT_TIMEOUT
            ),
            generate_url_slug(url),
            f"Scraping {url}",
        )

    def run_crawl(self) -> None:
        """Execute CRAWL method"""
        print("\n🔥 Running CRAWL method...")

        url = self._get_url_input("Enter base URL to crawl: ")
        if not url:
            return

        limit = self._get_integer_input("Max pages to crawl", DEFAULT_CRAWL_LIMIT)
        depth = self._get_integer_input("Crawl depth", DEFAULT_CRAWL_DEPTH)

        if limit is None or depth is None:
            return

        self._execute_firecrawl_operation(
            "crawl",
            lambda: self.firecrawl.crawl(url=url, limit=limit, depth=depth),
            f"crawl_{generate_url_slug(url)}",
            f"Crawling {url} (limit: {limit}, depth: {depth})",
        )

    def run_map(self) -> None:
        """Execute MAP method"""
        print("\n🔥 Running MAP method...")

        url = self._get_url_input("Enter URL to map: ")
        if not url:
            return

        self._execute_firecrawl_operation(
            "map",
            lambda: self.firecrawl.map(url),
            f"map_{generate_url_slug(url)}",
            f"Mapping {url}",
        )

    def run_search(self) -> None:
        """Execute SEARCH method"""
        print("\n🔥 Running SEARCH method...")

        query = input("Enter search query: ").strip()
        if not query:
            print("❌ Query is required")
            return

        limit = self._get_integer_input("Number of results", DEFAULT_SEARCH_LIMIT)
        if limit is None:
            return

        print("\nSelect sources (comma-separated):")
        print("Options: web, news, images")
        sources = self._get_list_input("Sources", "web")

        self._execute_firecrawl_operation(
            "search",
            lambda: self.firecrawl.search(query=query, limit=limit, sources=sources),
            f"search_{sanitize_search_query(query)}",
            f"Searching for '{query}'",
        )

    def run_extract(self) -> None:
        """Execute EXTRACT method"""
        print("\n🔥 Running EXTRACT method...")

        url = self._get_url_input("Enter URL to extract from: ")
        if not url:
            return

        print("\nExtraction method:")
        print("1. Custom prompt (flexible)")
        print("2. Schema-based (structured)")

        method = input("Choose method (1/2) [1]: ").strip() or "1"

        if method == "1":
            prompt = input("Enter extraction prompt: ").strip()
            if not prompt:
                print("❌ Prompt is required")
                return

            formats = [{"type": "json", "prompt": prompt}]

            self._execute_firecrawl_operation(
                "extract",
                lambda: self.firecrawl.scrape(url, formats=formats, only_main_content=True),
                f"extract_{generate_url_slug(url)}",
                f"Extracting from {url}",
            )
        else:
            print("❌ Schema-based extraction not implemented in this demo")

    def run_actions(self) -> None:
        """Execute ACTIONS method"""
        print("\n🔥 Running ACTIONS method...")
        print("⚠️  This is a complex feature. Using basic example...")

        url = self._get_url_input("Enter URL: ")
        if not url:
            return

        # Basic example with screenshot
        actions = [{"type": "wait", "milliseconds": 2000}, {"type": "screenshot", "fullPage": True}]

        self._execute_firecrawl_operation(
            "actions",
            lambda: self.firecrawl.scrape(url, formats=["markdown"], actions=actions),
            f"actions_{generate_url_slug(url)}",
            f"Scraping {url} with actions",
        )

    def run_facebook_ads(self) -> None:
        """Execute Facebook Ads Library scraping with enhanced features"""
        print("\n🎯 Running Enhanced Facebook Ads Library scraping...")
        print("✨ Features: Image scraping, Date filtering, Deduplication")

        url = self._get_url_input("Enter Facebook Ads Library URL: ")
        if not url:
            return

        brand_name = input("Enter brand/company name for filename: ").strip() or "facebook_ads"

        # Configuration selection
        print("\nSelect scraping configuration:")
        print("1. Enhanced (images + extended scrolling, slower but more complete)")
        print("2. Simple (faster, basic content)")
        print("3. EU (optimized for European users)")
        config_choice = input("Choose configuration (1/2/3) [1]: ").strip() or "1"

        # Date range selection
        print("\nSelect date range:")
        print("1. No date filter (all ads)")
        print("2. Last 7 days")
        print("3. Last 30 days")
        print("4. Last 90 days")
        print("5. Last 6 months")
        print("6. Last year")
        print("7. Custom range (days back)")
        date_choice = input("Choose date range (1-7) [1]: ").strip() or "1"

        # Deduplication option
        enable_dedup = input("Enable deduplication? (Y/n): ").strip().lower() != "n"

        # Process choices
        config = self._get_config_by_choice(config_choice)
        date_filter = self._get_date_filter_by_choice(date_choice)

        # Apply date filter to URL if needed
        if date_filter and date_filter.start_date and date_filter.end_date:
            url = build_url_with_date_filter(url, date_filter)
            print(
                f"🗓️  Applied date filter: {date_filter.start_date.date()} to {date_filter.end_date.date()}"
            )

        print(f"\n🔗 Target URL: {url}")
        print(f"⚙️  Configuration: {config['name']}")
        print(f"🔄 Deduplication: {'Enabled' if enable_dedup else 'Disabled'}")
        print("⏳ Processing...")

        self._execute_firecrawl_operation(
            "facebook_ads_enhanced",
            lambda: self._scrape_facebook_ads_enhanced(
                url, brand_name, config, date_filter, enable_dedup
            ),
            brand_name,
            f"Scraping Facebook ads for {brand_name}",
        )

    def _get_config_by_choice(self, choice: str) -> dict:
        """Get configuration based on user choice"""
        configs = {
            "1": {"config": FACEBOOK_ADS_ENHANCED_CONFIG, "name": "Enhanced"},
            "2": {"config": FACEBOOK_ADS_SIMPLE_CONFIG, "name": "Simple"},
            "3": {"config": FACEBOOK_ADS_EU_CONFIG, "name": "EU Optimized"},
        }
        return configs.get(choice, configs["1"])

    def _get_date_filter_by_choice(self, choice: str) -> DateRangeFilter | None:
        """Get date filter based on user choice"""
        if choice == "1":
            return None
        if choice in ["2", "3", "4", "5", "6"]:
            preset_map = {
                "2": "last_7_days",
                "3": "last_30_days",
                "4": "last_90_days",
                "5": "last_6_months",
                "6": "last_year",
            }
            return DateRangeFilter.from_preset(preset_map[choice])
        if choice == "7":
            try:
                days = int(input("Enter number of days back: ").strip())
                return DateRangeFilter.custom_range(days)
            except ValueError:
                print("❌ Invalid number, using no date filter")
                return None
        return None

    def _scrape_facebook_ads_enhanced(
        self,
        url: str,
        brand_name: str,
        config: dict,
        date_filter: DateRangeFilter | None,
        enable_dedup: bool,
    ) -> dict:
        """Enhanced Facebook ads scraping with all features"""
        deduplicator = AdDeduplicator() if enable_dedup else None

        try:
            # Scrape using selected configuration
            result = self.firecrawl.scrape(url=url, **config["config"])

            # Process results
            processed_result = {
                "raw_result": result,
                "url": url,
                "brand": brand_name,
                "config_used": config["name"],
                "timestamp": datetime.now().isoformat(),
                "features": {
                    "images_included": not config["config"].get("remove_base64_images", True),
                    "date_filtered": date_filter is not None,
                    "deduplicated": enable_dedup,
                },
            }

            # Add date filter info
            if date_filter:
                processed_result["date_filter"] = {
                    "start_date": (
                        date_filter.start_date.isoformat() if date_filter.start_date else None
                    ),
                    "end_date": date_filter.end_date.isoformat() if date_filter.end_date else None,
                }

            # Extract and analyze ads if HTML content is available
            if "html" in result:
                processed_result["extracted_ads"] = self._extract_ads_from_html(
                    result["html"], deduplicator, date_filter
                )

            # Add deduplication stats
            if deduplicator:
                processed_result["deduplication_stats"] = deduplicator.get_stats()

            # Show enhanced summary
            content_length = len(result.get("markdown", "")) if result else 0
            html_length = len(result.get("html", "")) if result else 0

            print("✅ Successfully scraped:")
            print(f"   📄 Markdown: {content_length:,} characters")
            if html_length:
                print(f"   🌐 HTML: {html_length:,} characters")

            if "extracted_ads" in processed_result:
                print(f"   🎯 Extracted ads: {len(processed_result['extracted_ads'])}")

            if deduplicator:
                stats = deduplicator.get_stats()
                print(f"   🔄 Unique content: {stats['total_combinations']} combinations")

            return processed_result

        except Exception as e:
            print(f"❌ Enhanced scraping failed: {str(e)[:100]}...")
            # Return minimal result for debugging
            return {
                "raw_result": {"error": str(e)},
                "url": url,
                "brand": brand_name,
                "config_used": f"{config['name']} (Failed)",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _extract_ads_from_html(
        self,
        html_content: str,
        deduplicator: AdDeduplicator | None,
        date_filter: DateRangeFilter | None,
    ) -> list:
        """Extract individual ads from HTML content"""
        import re
        from html import unescape

        ads = []

        # Simple ad extraction logic (can be enhanced)
        # Look for common ad containers in Facebook Ads Library
        ad_patterns = [
            r'<div[^>]*data-testid="[^"]*ad[^"]*"[^>]*>(.*?)</div>',
            r"<article[^>]*>(.*?)</article>",
            r'<div[^>]*class="[^"]*ad[^"]*"[^>]*>(.*?)</div>',
        ]

        for pattern in ad_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                # Clean up the HTML content
                clean_content = unescape(match).strip()

                if len(clean_content) > 100:  # Filter out very short matches
                    ad_data = {
                        "content": clean_content[:1000],  # Limit content length
                        "extracted_at": datetime.now().isoformat(),
                    }

                    # Apply deduplication if enabled
                    if deduplicator and deduplicator.is_duplicate(ad_data):
                        continue

                    # Apply date filtering if enabled
                    if date_filter:
                        ad_date = date_filter.extract_ad_date(ad_data)
                        if ad_date and not date_filter.is_in_range(ad_date):
                            continue
                        if ad_date:
                            ad_data["extracted_date"] = ad_date.isoformat()

                    ads.append(ad_data)

        return ads[:50]  # Limit to first 50 ads to avoid huge files

    def _scrape_facebook_ads_simple(self, url: str, brand_name: str) -> dict:
        """Simplified Facebook ads scraping using only simple config"""
        try:
            # Use simple configuration only
            result = self.firecrawl.scrape(url=url, **FACEBOOK_ADS_SIMPLE_CONFIG)

            # Enhanced result without complex processing
            enhanced_result = {
                "raw_result": result,
                "url": url,
                "brand": brand_name,
                "config_used": "Simple",
            }

            # Show quick summary
            content_length = len(result.get("markdown", "")) if result else 0
            print(f"✅ Successfully scraped {content_length:,} characters of content.")

            return enhanced_result

        except Exception as e:
            print(f"❌ Simple config failed: {str(e)[:100]}...")
            # Return minimal result for debugging
            return {
                "raw_result": {"error": str(e)},
                "url": url,
                "brand": brand_name,
                "config_used": "Simple (Failed)",
                "error": str(e),
            }

    def _save_and_display_result(self, method: str, result: Any, filename_base: str) -> None:
        """Save result to file and display summary"""
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{OUTPUT_DIR}/{method}_{filename_base}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Results saved to: {filename}")

        self._display_result_summary(result)
        print("💾 Full results saved to JSON file")

    def _display_result_summary(self, result: Any) -> None:
        """Display summary of scraping results"""
        if isinstance(result, dict):
            if "markdown" in result:
                content_length = len(result.get("markdown", ""))
                print(f"📄 Content length: {content_length:,} characters")

            if "screenshot" in result:
                print("📸 Screenshot captured")

            if "data" in result and isinstance(result["data"], list):
                print(f"📊 Pages found: {len(result['data'])}")

        elif isinstance(result, list):
            print(f"📋 Items found: {len(result)}")
            if result and isinstance(result[0], dict):
                print(f"🔗 First item keys: {list(result[0].keys())}")


def main():
    """Main entry point"""
    try:
        manager = FirecrawlManager()

        while True:
            manager.show_menu()
            choice = manager.get_user_choice()

            # Execute chosen method
            if choice == "1":
                manager.run_scrape()
            elif choice == "2":
                manager.run_crawl()
            elif choice == "3":
                manager.run_map()
            elif choice == "4":
                manager.run_search()
            elif choice == "5":
                manager.run_extract()
            elif choice == "6":
                manager.run_actions()
            elif choice == "7":
                manager.run_facebook_ads()

            # Ask if user wants to continue
            if input("\nRun another method? (y/N): ").strip().lower() != "y":
                break

        print("\n👋 Thanks for using Firecrawl integration!")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
