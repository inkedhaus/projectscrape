#!/usr/bin/env python3
"""
Test script for Facebook Ads scraping integration
Validates that the configuration is properly set up and ready to use
"""

import sys


def test_imports():
    """Test that all required imports work"""
    print("🧪 Testing imports...")

    try:
        from apps.firecrawl_tools.firecrawl_presets import (
            process_facebook_ad_results,
        )

        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test that the configuration is valid"""
    print("\n🧪 Testing configuration...")

    try:
        from apps.firecrawl_tools.firecrawl_presets import FACEBOOK_ADS_CONFIG

        # Check required keys
        required_keys = ["formats", "timeout", "actions"]
        for key in required_keys:
            if key not in FACEBOOK_ADS_CONFIG:
                print(f"❌ Missing required key: {key}")
                return False

        # Check actions are properly formatted
        actions = FACEBOOK_ADS_CONFIG["actions"]
        if not isinstance(actions, list) or len(actions) == 0:
            print("❌ Actions should be a non-empty list")
            return False

        print(f"✅ Configuration valid with {len(actions)} actions")
        print(f"   Timeout: {FACEBOOK_ADS_CONFIG['timeout']}ms")
        print(f"   Formats: {FACEBOOK_ADS_CONFIG['formats']}")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_url_generation():
    """Test URL generation functions"""
    print("\n🧪 Testing URL generation...")

    try:
        from apps.firecrawl_tools.firecrawl_presets import (
            POPULAR_FACEBOOK_PAGES,
            get_facebook_ads_url,
        )

        # Test with page ID
        nike_url = get_facebook_ads_url(page_id=POPULAR_FACEBOOK_PAGES["nike"])
        if "view_all_page_id=310947142968045" not in nike_url:
            print("❌ Nike page ID URL generation failed")
            return False

        # Test with search terms
        search_url = get_facebook_ads_url(search_terms="fitness equipment")
        if "search_terms=fitness%20equipment" not in search_url:
            print("❌ Search terms URL generation failed")
            return False

        print("✅ URL generation working")
        print(f"   Nike URL: {nike_url[:80]}...")
        print(f"   Search URL: {search_url[:80]}...")
        return True

    except Exception as e:
        print(f"❌ URL generation test failed: {e}")
        return False


def test_preset_examples():
    """Test preset examples"""
    print("\n🧪 Testing preset examples...")

    try:
        from apps.firecrawl_tools.firecrawl_presets import get_preset_examples

        examples = get_preset_examples()
        if len(examples) == 0:
            print("❌ No preset examples found")
            return False

        print(f"✅ Found {len(examples)} preset examples:")
        for brand in list(examples.keys())[:3]:  # Show first 3
            print(f"   - {brand.title()}")

        return True

    except Exception as e:
        print(f"❌ Preset examples test failed: {e}")
        return False


def test_text_processing():
    """Test text processing functions"""
    print("\n🧪 Testing text processing...")

    try:
        from apps.firecrawl_tools.firecrawl_presets import clean_ad_text, normalize_offer

        # Test offer normalization
        test_text = "Get 25% off your first order with code SAVE25"
        offer = normalize_offer(test_text)
        if "25% off" not in offer.lower():
            print(f"❌ Offer normalization failed: got '{offer}'")
            return False

        # Test text cleaning
        dirty_text = "  Shop Now   Sponsored  Amazing Deal  "
        clean_text = clean_ad_text(dirty_text)
        if "sponsored" in clean_text.lower():
            print(f"❌ Text cleaning failed: got '{clean_text}'")
            return False

        print("✅ Text processing working")
        print(f"   Extracted offer: '{offer}'")
        print(f"   Cleaned text: '{clean_text}'")
        return True

    except Exception as e:
        print(f"❌ Text processing test failed: {e}")
        return False


def test_firecrawl_integration():
    """Test integration with main firecrawl module"""
    print("\n🧪 Testing Firecrawl integration...")

    try:
        # Check if the module can be imported
        import apps.firecrawl_tools.main

        # Check if we can initialize (this will check for API key)
        print("   Note: This test requires a valid FIRECRAWL_API_KEY in .env")
        print("   If you see an API key error, that's normal if not configured yet")

        # We don't actually initialize to avoid API key requirement for testing
        print("✅ Firecrawl integration module loads successfully")
        return True

    except ImportError as e:
        print(f"❌ Firecrawl integration failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🎯 Facebook Ads Scraping Integration Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_configuration,
        test_url_generation,
        test_preset_examples,
        test_text_processing,
        test_firecrawl_integration,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Facebook Ads scraping is ready to use.")
        print("\n💡 To run the scraper:")
        print("   1. Set FIRECRAWL_API_KEY in your .env file")
        print("   2. Run: python -m apps.firecrawl_tools.main")
        print("   3. Select option 7 (Facebook Ads)")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
