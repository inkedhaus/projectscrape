#!/usr/bin/env python3
"""
Data cleanup script for Facebook Ads extracted data.
Fixes formatting issues and improves readability.
"""

import json
import re
from pathlib import Path
from typing import Any


def clean_markdown_text(text: str) -> str:
    """Clean up markdown text by removing unnecessary elements."""
    if not text:
        return ""

    # Remove multiple consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove empty links and broken markdown
    text = re.sub(r"\[​\].*?", "", text)
    text = re.sub(r"\[!\[\]\(.*?\)\]\(.*?\)", "", text)

    # Clean up excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Remove Facebook CDN URLs (they're not useful for analysis)
    text = re.sub(r"https://scontent-[a-zA-Z0-9-]+\.xx\.fbcdn\.net/[^\s\)]+", "[IMAGE]", text)

    return text.strip()


def extract_ad_data_from_markdown(markdown: str) -> list[dict[str, Any]]:
    """Extract structured ad data from Facebook Ads Library markdown."""
    ads = []

    # Pattern to match ad sections
    ad_pattern = r"!\[([^\]]+)\]\([^\)]+\)\s*\n\s*\[([^\]]+)\]\([^\)]+\)\s*\n\s*Sponsored\s*\n\s*([^\n]+)\s*\n.*?Library ID:\s*(\d+)\s*\n\s*Started running on\s*([^\n]+)"

    matches = re.findall(ad_pattern, markdown, re.DOTALL | re.MULTILINE)

    for match in matches:
        advertiser = match[1].strip()
        headline = match[2].strip()
        library_id = match[3].strip()
        date_started = match[4].strip()

        # Skip if we already have this ad (remove duplicates)
        if not any(ad["library_id"] == library_id for ad in ads):
            ad = {
                "advertiser": advertiser,
                "headline": headline,
                "library_id": library_id,
                "date_started": date_started,
                "cta": extract_cta_from_text(markdown, library_id),
            }
            ads.append(ad)

    return ads


def extract_cta_from_text(text: str, library_id: str) -> str | None:
    """Extract call-to-action text near a specific library ID."""
    # Look for common CTA patterns near the library ID
    cta_patterns = [
        r"Shop [Nn]ow",
        r"Learn [Mm]ore",
        r"Sign [Uu]p",
        r"Get [Ss]tarted",
        r"Download",
        r"Buy [Nn]ow",
        r"Visit [Ww]ebsite",
    ]

    # Find text around the library ID
    id_index = text.find(library_id)
    if id_index != -1:
        # Check 500 characters before and after the library ID
        context = text[max(0, id_index - 500) : id_index + 500]

        for pattern in cta_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)

    return None


def clean_processed_data(data: dict[str, Any]) -> dict[str, Any]:
    """Clean up processed ad data."""
    cleaned_data = {
        "brand": data.get("brand", ""),
        "url": data.get("url", ""),
        "timestamp": data.get("timestamp", ""),
        "scrape_summary": {
            "total_ads_found": 0,
            "unique_advertisers": set(),
            "date_range": {"earliest": None, "latest": None},
        },
    }

    # Extract ads from raw markdown if available
    raw_result = data.get("raw_result", {})
    markdown = raw_result.get("markdown", "")

    if markdown:
        # Extract structured ad data
        ads = extract_ad_data_from_markdown(markdown)
        cleaned_data["ads"] = ads
        cleaned_data["scrape_summary"]["total_ads_found"] = len(ads)

        # Get unique advertisers
        advertisers = set(ad["advertiser"] for ad in ads if ad["advertiser"])
        cleaned_data["scrape_summary"]["unique_advertisers"] = list(advertisers)

        # Find date range
        dates = [ad["date_started"] for ad in ads if ad["date_started"]]
        if dates:
            cleaned_data["scrape_summary"]["date_range"] = {
                "earliest": min(dates),
                "latest": max(dates),
            }
    else:
        # Use existing ads data but clean it
        existing_ads = data.get("ads", [])
        unique_ads = []
        seen_combinations = set()

        for ad in existing_ads:
            # Create a unique key for the ad
            key = (ad.get("advertiser", ""), ad.get("headline", ""))
            if key not in seen_combinations:
                seen_combinations.add(key)
                unique_ads.append(ad)

        cleaned_data["ads"] = unique_ads
        cleaned_data["scrape_summary"]["total_ads_found"] = len(unique_ads)
        cleaned_data["scrape_summary"]["unique_advertisers"] = list(
            set(ad["advertiser"] for ad in unique_ads if ad.get("advertiser"))
        )

    # Add cleaned raw data (much smaller)
    if raw_result:
        cleaned_raw = {
            "metadata": raw_result.get("metadata", {}),
            "markdown_summary": (
                clean_markdown_text(markdown[:1000]) + "..."
                if len(markdown) > 1000
                else clean_markdown_text(markdown)
            ),
        }
        cleaned_data["raw_summary"] = cleaned_raw

    return cleaned_data


def process_file(file_path: Path) -> bool:
    """Process a single JSON file."""
    try:
        print(f"Processing: {file_path.name}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Only process files that need cleaning
        if "ads" in data or "raw_result" in data:
            cleaned_data = clean_processed_data(data)

            # Create cleaned filename
            cleaned_filename = file_path.stem + "_cleaned" + file_path.suffix
            cleaned_path = file_path.parent / cleaned_filename

            # Write cleaned data
            with open(cleaned_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

            print(f"  SUCCESS: Created: {cleaned_filename}")

            # Print summary
            if "scrape_summary" in cleaned_data:
                summary = cleaned_data["scrape_summary"]
                print(f"  STATS: Found {summary['total_ads_found']} unique ads")
                print(
                    f"  ADVERTISERS: {len(summary['unique_advertisers'])} advertisers: {', '.join(summary['unique_advertisers'][:3])}{'...' if len(summary['unique_advertisers']) > 3 else ''}"
                )

            return True
        print("  SKIPPING: no ad data found")
        return False

    except Exception as e:
        print(f"  ERROR: Error processing {file_path.name}: {e}")
        return False


def main():
    """Main function to clean up all data files."""
    print("Starting data cleanup process...")

    # Find all JSON files in the firecrawl_results directory
    results_dir = Path("data/firecrawl_results")
    if not results_dir.exists():
        print(f"ERROR: Directory not found: {results_dir}")
        return

    json_files = list(results_dir.glob("*.json"))
    if not json_files:
        print(f"ERROR: No JSON files found in {results_dir}")
        return

    print(f"Found {len(json_files)} JSON files")

    processed_count = 0
    for file_path in sorted(json_files):
        # Skip already cleaned files
        if "_cleaned" in file_path.name:
            continue

        if process_file(file_path):
            processed_count += 1
        print()

    print("Data cleanup completed!")
    print(f"Processed {processed_count} files")
    print("Cleaned files are saved with '_cleaned' suffix")


if __name__ == "__main__":
    main()
