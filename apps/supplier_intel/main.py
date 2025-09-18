"""Supplier intelligence main module."""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import load_config

from .finder import SupplierFinder


def save_suppliers_csv(suppliers: list[dict[str, Any]], output_path: str):
    """Save suppliers to CSV file."""
    if not suppliers:
        print("No suppliers to save")
        return

    fieldnames = [
        "name",
        "location",
        "contact",
        "website",
        "rating",
        "reviews_count",
        "products",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for supplier in suppliers:
            # Convert lists to strings for CSV
            row = supplier.copy()
            if "products" in row and isinstance(row["products"], list):
                row["products"] = ", ".join(row["products"])

            writer.writerow({field: row.get(field, "") for field in fieldnames})

    print(f"Saved {len(suppliers)} suppliers to {output_path}")


def save_suppliers_json(suppliers: list[dict[str, Any]], output_path: str):
    """Save suppliers to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(suppliers, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(suppliers)} suppliers to {output_path}")


def main():
    """Main entry point for supplier intelligence."""
    parser = argparse.ArgumentParser(description="Supplier Intelligence Tool")
    parser.add_argument("--niche", required=True, help="Product niche to search for")
    parser.add_argument("--location", default="Houston, TX", help="Search location")
    parser.add_argument("--radius", type=int, default=100, help="Search radius in miles")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of suppliers to find")
    parser.add_argument("--output", default="data/suppliers", help="Output directory")

    args = parser.parse_args()
    load_config()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Searching for suppliers...")
    print(f"Niche: {args.niche}")
    print(f"Location: {args.location}")
    print(f"Radius: {args.radius} miles")
    print(f"Limit: {args.limit} suppliers")

    # Initialize supplier finder
    finder = SupplierFinder()

    try:
        # Search for suppliers
        suppliers = finder.find_suppliers(
            niche=args.niche, location=args.location, radius=args.radius, limit=args.limit
        )

        if suppliers:
            print(f"\nFound {len(suppliers)} suppliers!")

            # Generate timestamp for files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            niche_safe = args.niche.replace(" ", "_").replace("/", "_")

            # Save to CSV
            csv_path = output_dir / f"suppliers_{niche_safe}_{timestamp}.csv"
            save_suppliers_csv(suppliers, str(csv_path))

            # Save to JSON
            json_path = output_dir / f"suppliers_{niche_safe}_{timestamp}.json"
            save_suppliers_json(suppliers, str(json_path))

            # Print summary
            print("\n=== Supplier Summary ===")
            print(f"Total suppliers found: {len(suppliers)}")

            # Top rated suppliers
            rated_suppliers = [s for s in suppliers if s.get("rating", 0) > 0]
            if rated_suppliers:
                top_rated = max(rated_suppliers, key=lambda x: x.get("rating", 0))
                print(f"Top rated: {top_rated.get('name')} ({top_rated.get('rating'):.1f}★)")

            # Location distribution
            locations = {}
            for supplier in suppliers:
                loc = supplier.get("location", "Unknown")
                locations[loc] = locations.get(loc, 0) + 1

            if locations:
                print("Top locations:")
                sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)
                for location, count in sorted_locations[:3]:
                    print(f"  • {location}: {count} suppliers")

            # Show sample suppliers
            print("\nSample suppliers:")
            for i, supplier in enumerate(suppliers[:5], 1):
                name = supplier.get("name", "Unknown")
                location = supplier.get("location", "Unknown")
                rating = supplier.get("rating", 0)
                website = supplier.get("website", "N/A")
                print(f"  {i}. {name} - {location} ({rating}★) - {website}")

            print(f"\nAll supplier data saved to {output_dir}")

        else:
            print("No suppliers found. Try adjusting your search criteria.")

    except Exception as e:
        print(f"Error during supplier search: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
