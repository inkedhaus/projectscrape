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

from .facebook_simple_config import FACEBOOK_ADS_SIMPLE_CONFIG
from .firecrawl_presets import (
    POPULAR_FACEBOOK_PAGES,
    get_facebook_ads_url,
    get_preset_examples,
    process_facebook_ad_results,
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
            choice = input(f"\nEnter the method number (1–{len(MENU_OPTIONS)}) you want to run: ").strip()
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
        progress_message: str | None = None
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
            f"Scraping {url}"
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
            f"Crawling {url} (limit: {limit}, depth: {depth})"
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
            f"Mapping {url}"
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
            f"Searching for '{query}'"
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
                f"Extracting from {url}"
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
        actions = [
            {"type": "wait", "milliseconds": 2000}, 
            {"type": "screenshot", "fullPage": True}
        ]

        self._execute_firecrawl_operation(
            "actions",
            lambda: self.firecrawl.scrape(url, formats=["markdown"], actions=actions),
            f"actions_{generate_url_slug(url)}",
            f"Scraping {url} with actions"
        )

    def run_facebook_ads(self) -> None:
        """Execute Facebook Ads Library scraping - Simplified version for testing"""
        print("\n🎯 Running Facebook Ads Library scraping (Simple Mode)...")
        
        # Simplified: Only use popular brands for easier testing
        print("\n📊 Popular brands available:")
        examples = get_preset_examples()
        for i, brand in enumerate(examples.keys(), 1):
            print(f"{i:2d}. {brand.title()}")

        try:
            brand_choice = input(f"\nSelect brand (1-{len(examples)}) [1]: ").strip() or "1"
            brand_idx = int(brand_choice) - 1
            brands = list(examples.keys())

            if 0 <= brand_idx < len(brands):
                brand_name = brands[brand_idx]
                url = examples[brand_name]
                print(f"✅ Selected: {brand_name.title()}")
            else:
                print("❌ Invalid selection, using Nike as default")
                brand_name = "nike"
                url = examples["nike"]

        except (ValueError, KeyError):
            print("❌ Invalid selection, using Nike as default")
            brand_name = "nike"
            url = get_facebook_ads_url(POPULAR_FACEBOOK_PAGES["nike"])

        print(f"\n🔗 Target URL: {url}")
        print("⚙️  Using Simple configuration for testing...")
        print("⏳ This should take about 30-60 seconds...")

        # Use only the simple configuration for testing
        self._execute_firecrawl_operation(
            "facebook_ads",
            lambda: self._scrape_facebook_ads_simple(url, brand_name),
            brand_name,
            f"Scraping Facebook ads for {brand_name}"
        )

    def _scrape_facebook_ads_simple(self, url: str, brand_name: str) -> dict:
        """Simplified Facebook ads scraping using only simple config"""
        try:
            # Use simple configuration only
            result = self.firecrawl.scrape(url=url, **FACEBOOK_ADS_SIMPLE_CONFIG)
            
            # Process the results
            processed_ads = process_facebook_ad_results(result)

            # Enhanced result with processed ads
            enhanced_result = {
                "raw_result": result,
                "processed_ads": processed_ads,
                "url": url,
                "brand": brand_name,
                "config_used": "Simple",
            }

            # Show quick summary
            if processed_ads:
                print(f"✅ Successfully found {len(processed_ads)} ads!")
                # Show first 3 ads
                for i, ad in enumerate(processed_ads[:3], 1):
                    headline = ad.get("headline", "No headline")[:40]
                    advertiser = ad.get("advertiser", "Unknown")[:25]
                    print(f"  {i}. {headline} (by {advertiser})")
            else:
                content_length = len(result.get('markdown', '')) if result else 0
                print(f"⚠️  No ads found. Scraped {content_length:,} characters of content.")
                
            return enhanced_result
            
        except Exception as e:
            print(f"❌ Simple config failed: {str(e)[:100]}...")
            # Return minimal result for debugging
            return {
                "raw_result": {"error": str(e)},
                "processed_ads": [],
                "url": url,
                "brand": brand_name,
                "config_used": "Simple (Failed)",
                "error": str(e)
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

            # Handle Facebook ads specific results
            if "processed_ads" in result and isinstance(result["processed_ads"], list):
                print(f"🎯 Ads processed: {len(result['processed_ads'])}")

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
