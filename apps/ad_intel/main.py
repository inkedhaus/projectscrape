"""Facebook Ad Library scraper main module."""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import load_config
from core.db import Database

from .scraper import FacebookAdScraper


def export_ads_to_csv(ads: list[dict[str, Any]], output_path: str):
    """Export ads to CSV format."""
    if not ads:
        print("No ads to export")
        return

    fieldnames = [
        "id",
        "brand",
        "page_name",
        "headline",
        "body",
        "call_to_action",
        "media_type",
        "created_date",
        "scraped_at",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ad in ads:
            row = {field: ad.get(field, "") for field in fieldnames}
            writer.writerow(row)

    print(f"Exported {len(ads)} ads to {output_path}")


def export_ads_to_json(ads: list[dict[str, Any]], output_path: str):
    """Export ads to JSON format."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ads, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(ads)} ads to {output_path}")


def main():
    """Main entry point for ad intelligence scraper."""
    parser = argparse.ArgumentParser(description="Facebook Ad Library Intelligence Scraper")
    parser.add_argument("--url", help="Facebook Ad Library URL to scrape")
    parser.add_argument("--max-scrolls", type=int, default=10, help="Maximum number of scrolls")
    parser.add_argument("--export", action="store_true", help="Export existing ads from database")
    parser.add_argument(
        "--output-dir", default="data/processed", help="Output directory for exports"
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    args = parser.parse_args()
    config = load_config()
    db = Database()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.export:
        # Export existing ads from database
        print("Exporting ads from database...")
        ads = db.get_ads()

        if ads:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Export to CSV
            csv_path = output_dir / f"ads_export_{timestamp}.csv"
            export_ads_to_csv(ads, str(csv_path))

            # Export to JSON
            json_path = output_dir / f"ads_export_{timestamp}.json"
            export_ads_to_json(ads, str(json_path))

            # Print statistics
            stats = db.get_stats()
            print("\nDatabase Statistics:")
            print(f"Total ads: {stats['total_ads']}")
            print(f"Unique brands: {stats['unique_brands']}")
            print(f"Total analysis: {stats['total_analysis']}")
        else:
            print("No ads found in database")

        return

    if not args.url:
        print("Error: --url is required for scraping. Use --export to export existing data.")
        return

    print("Starting Facebook Ad Library scraping...")
    print(f"URL: {args.url}")
    print(f"Max scrolls: {args.max_scrolls}")
    print(f"Headless: {args.headless or config.headless}")

    # Initialize scraper
    scraper = FacebookAdScraper(
        headless=args.headless or config.headless, max_scrolls=args.max_scrolls
    )

    try:
        # Scrape ads
        ads = scraper.scrape_ads(args.url)

        if ads:
            print(f"\nScraped {len(ads)} ads successfully!")

            # Save to database
            saved_count = db.save_ads(ads)
            print(f"Saved {saved_count} ads to database")

            # Save raw data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = Path(config.raw_dir) / f"fb_ads_{timestamp}.json"
            raw_file.parent.mkdir(parents=True, exist_ok=True)

            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(ads, f, indent=2, ensure_ascii=False)

            print(f"Raw data saved to: {raw_file}")

            # Auto-export to CSV
            csv_path = output_dir / f"ads_scraped_{timestamp}.csv"
            export_ads_to_csv(ads, str(csv_path))

        else:
            print("No ads were scraped. Check the URL and try again.")

    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback

        traceback.print_exc()

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
