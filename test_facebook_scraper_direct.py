#!/usr/bin/env python3
"""
Direct test of Facebook Ad Library scraping for MadRabbit
Testing the exact URL provided to understand what works
"""

import json
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from firecrawl import FirecrawlApp

    from core.config import load_config

    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


def test_madrabbit_scraping():
    """Test scraping the specific MadRabbit URL"""

    # Load config and initialize Firecrawl
    config = load_config()
    api_key = getattr(config, "firecrawl_api_key", None)
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in .env file")
        return None

    firecrawl = FirecrawlApp(api_key=api_key)
    print(f"✅ Firecrawl initialized with API key: {api_key[:10]}...")

    # The exact URL provided by user
    url = "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=310947142968045"

    print("\n🎯 Testing MadRabbit Facebook Ads URL:")
    print(f"🔗 {url}")

    # Try different configurations to see what works
    configs_to_test = [
        {
            "name": "Simple Markdown Only",
            "config": {
                "formats": ["markdown"],
                "only_main_content": True,
                "timeout": 30000,
            },
        },
        {
            "name": "Enhanced with HTML",
            "config": {
                "formats": ["markdown", "html"],
                "only_main_content": True,
                "timeout": 45000,
                "wait_for": 3000,
            },
        },
        {
            "name": "With Images (no base64 removal)",
            "config": {
                "formats": ["markdown", "html"],
                "only_main_content": True,
                "timeout": 60000,
                "wait_for": 5000,
                "remove_base64_images": False,
            },
        },
    ]

    results = {}

    for i, test_config in enumerate(configs_to_test, 1):
        print(f"\n{'=' * 60}")
        print(f"🧪 TEST {i}: {test_config['name']}")
        print(f"{'=' * 60}")

        try:
            print("⏳ Scraping (this may take 30-90 seconds)...")
            result = firecrawl.scrape(url, **test_config["config"])

            print(f"🔍 Result type: {type(result)}")

            # Handle different response formats
            markdown_content = ""
            html_content = ""

            if hasattr(result, "markdown"):
                markdown_content = result.markdown or ""
            elif hasattr(result, "content"):
                markdown_content = result.content or ""
            elif isinstance(result, dict):
                markdown_content = result.get("markdown", result.get("content", ""))

            if hasattr(result, "html"):
                html_content = result.html or ""
            elif isinstance(result, dict):
                html_content = result.get("html", "")

            # Basic analysis
            markdown_len = len(markdown_content)
            html_len = len(html_content)

            print("✅ SUCCESS!")
            print(f"   📄 Markdown: {markdown_len:,} characters")
            if html_len:
                print(f"   🌐 HTML: {html_len:,} characters")

            # Look for ad indicators in the content
            ad_indicators = [
                "Mad Rabbit",
                "Sponsored",
                "Library ID",
                "Shop Now",
                "Shop now",
                "Fresh Ink",
                "Started running on",
            ]

            found_indicators = []
            content_to_check = markdown_content + html_content
            for indicator in ad_indicators:
                if indicator.lower() in content_to_check.lower():
                    found_indicators.append(indicator)

            print(f"   🎯 Ad indicators found: {found_indicators}")

            # Try basic ad extraction
            ads_found = extract_basic_ads(markdown_content)
            if ads_found:
                print(f"   📱 Extracted ads: {len(ads_found)}")
                for j, ad in enumerate(ads_found[:3], 1):  # Show first 3
                    print(f"      Ad {j}: {ad.get('headline', 'No headline')[:50]}...")

            # Save successful result
            if markdown_len > 1000:  # If we got substantial content
                save_result(result, test_config["name"], f"test_{i}")
                results[test_config["name"]] = {
                    "success": True,
                    "markdown_length": markdown_len,
                    "html_length": html_len,
                    "ads_found": len(ads_found),
                    "indicators": found_indicators,
                }
            else:
                print("⚠️  Content too short, might not be complete")
                results[test_config["name"]] = {"success": False, "error": "Content too short"}

        except Exception as e:
            print(f"❌ FAILED: {str(e)[:100]}...")
            results[test_config["name"]] = {"success": False, "error": str(e)[:200]}

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY OF TESTS")
    print(f"{'=' * 60}")

    for name, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{status}: {name}")
        if result["success"]:
            print(f"   📄 Markdown: {result['markdown_length']:,} chars")
            print(f"   🎯 Ads found: {result['ads_found']}")
        else:
            print(f"   ❌ Error: {result['error']}")

    return results


def extract_basic_ads(markdown_content):
    """Basic ad extraction from markdown content"""
    if not markdown_content:
        return []

    ads = []
    lines = markdown_content.split("\n")

    current_ad = {}

    for _i, line in enumerate(lines):
        line = line.strip()

        # Look for Mad Rabbit mentions
        if "mad rabbit" in line.lower() and not current_ad.get("advertiser"):
            current_ad["advertiser"] = "Mad Rabbit Tattoo"

        # Look for headlines
        if "fresh ink" in line.lower() or (
            "vibrant" in line.lower() and "protected" in line.lower()
        ):
            current_ad["headline"] = line

        # Look for CTAs
        if "shop now" in line.lower():
            current_ad["cta"] = "Shop Now"

        # Look for Library IDs
        if "library id" in line.lower():
            try:
                library_id = line.split(":")[-1].strip()
                current_ad["library_id"] = library_id
            except:
                pass

        # Look for dates
        if "started running" in line.lower():
            try:
                date = line.replace("started running on", "").strip()
                current_ad["date_started"] = date
            except:
                pass

        # If we have enough info for an ad, save it
        if len(current_ad) >= 2:
            ads.append(current_ad.copy())
            current_ad = {}

    return ads[:20]  # Limit results


def save_result(result, config_name, test_num):
    """Save result to file with proper serialization"""
    os.makedirs("data/firecrawl_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/firecrawl_results/madrabbit_{test_num}_{config_name.lower().replace(' ', '_')}_{timestamp}.json"

    # Convert to serializable format
    serializable_result = {}
    if hasattr(result, "__dict__"):
        for key, value in result.__dict__.items():
            if not key.startswith("_"):
                try:
                    json.dumps(value)  # Test if serializable
                    serializable_result[key] = value
                except:
                    serializable_result[key] = str(value)
    else:
        serializable_result = result

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {"config_used": config_name, "timestamp": timestamp, "result": serializable_result},
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        print(f"💾 Results saved to: {filename}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")


if __name__ == "__main__":
    print("🔥 Direct Facebook Ad Library Test for MadRabbit")
    print("=" * 60)

    results = test_madrabbit_scraping()

    if results:
        successful_configs = [name for name, result in results.items() if result["success"]]
        if successful_configs:
            print("\n🎉 SUCCESS! Working configurations:")
            for config in successful_configs:
                print(f"   ✅ {config}")
            print("\n💡 Use the working configuration for reliable scraping!")
        else:
            print("\n⚠️  No configurations worked. Check network/API issues.")

    print("\n👋 Test complete!")
