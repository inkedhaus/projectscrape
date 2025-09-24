#!/usr/bin/env python3
"""
Test script for the new Facebook Ads Playwright scraper
"""

import asyncio
import sys
from facebook_ads_playwright_scraper import FacebookAdsPlaywrightScraper, AdRecord


async def test_scraper():
    """Test the scraper with a simple run"""
    print("🧪 Testing Facebook Ads Playwright Scraper")
    print("=" * 50)

    # Test AdRecord creation
    test_ad = AdRecord(
        library_id="12345", page_name="Test Page", headline="Test Headline", caption="Test Caption"
    )
    print(f"✅ AdRecord test: {test_ad.library_id}")

    # Test scraper initialization
    scraper = FacebookAdsPlaywrightScraper(out_dir="data/test_results")
    print("✅ Scraper initialized successfully")

    # Test selectors loading
    print(f"✅ Selectors loaded: {len(scraper.selectors)} categories")

    # Test short scrape (5 scrolls max for quick test)
    print("\n🚀 Starting short test scrape...")
    test_url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&search_type=keyword_unordered&q=test"

    try:
        results = await scraper.run_scrape(
            url=test_url,
            max_scrolls=5,  # Very short test
            brand_name="TestRun",
        )

        if results["success"]:
            print("🎉 TEST SUCCESSFUL!")
            print(f"   📱 Ads extracted: {results['metrics']['total_ads']}")
            print(f"   🖼️  Media URLs: {results['metrics']['media_urls']}")
            print(f"   📜 Scrolls: {results['metrics']['scrolls_performed']}")
            return True
        else:
            print(f"❌ Test failed: {results.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Test exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)
