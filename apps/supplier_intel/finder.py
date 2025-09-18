"""Supplier finder using web search and scraping."""

import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SupplierFinder:
    """Find suppliers using web search and scraping."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def find_suppliers(
        self, niche: str, location: str = "Houston, TX", radius: int = 100, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Find suppliers for given niche and location."""
        suppliers = []

        try:
            # Search different sources
            print("Searching business directories...")
            suppliers.extend(self._search_business_directories(niche, location, limit // 3))

            print("Searching Google Business...")
            suppliers.extend(self._search_google_business(niche, location, limit // 3))

            print("Searching industry directories...")
            suppliers.extend(self._search_industry_directories(niche, location, limit // 3))

            # Remove duplicates based on name and location
            suppliers = self._deduplicate_suppliers(suppliers)

            # Sort by rating
            suppliers.sort(key=lambda x: x.get("rating", 0), reverse=True)

            return suppliers[:limit]

        except Exception as e:
            logger.error(f"Error finding suppliers: {e}")
            return []

    def _search_business_directories(
        self, niche: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        """Search business directories for suppliers."""
        suppliers = []

        # Mock implementation - would use actual APIs like Yelp, YellowPages, etc.
        # For demo purposes, returning mock data
        mock_suppliers = [
            {
                "name": f"{niche.title()} Supply Co",
                "location": location,
                "contact": "(555) 123-4567",
                "website": "www.example-supply.com",
                "rating": 4.5,
                "reviews_count": 128,
                "products": [niche, f"{niche} accessories"],
                "notes": "Found via business directory search",
            },
            {
                "name": f"Premium {niche.title()} Distributors",
                "location": location,
                "contact": "info@premium-dist.com",
                "website": "www.premium-dist.com",
                "rating": 4.2,
                "reviews_count": 89,
                "products": [niche, f"wholesale {niche}"],
                "notes": "Wholesale supplier with good ratings",
            },
            {
                "name": f'{location.split(",")[0]} {niche.title()} Warehouse',
                "location": location,
                "contact": "(555) 987-6543",
                "website": "www.local-warehouse.com",
                "rating": 3.8,
                "reviews_count": 45,
                "products": [niche, f"{niche} bulk orders"],
                "notes": "Local warehouse supplier",
            },
        ]

        # Simulate API delay
        time.sleep(1)

        suppliers.extend(mock_suppliers[:limit])
        return suppliers

    def _search_google_business(
        self, niche: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        """Search Google Business for suppliers."""
        suppliers = []

        # Mock implementation - would use Google Places API
        mock_suppliers = [
            {
                "name": f"Elite {niche.title()} Solutions",
                "location": location,
                "contact": "sales@elite-solutions.com",
                "website": "www.elite-solutions.com",
                "rating": 4.7,
                "reviews_count": 203,
                "products": [niche, f"custom {niche}"],
                "notes": "High-rated on Google Business",
            },
            {
                "name": f"{niche.title()} Direct LLC",
                "location": location,
                "contact": "(555) 456-7890",
                "website": "www.direct-llc.com",
                "rating": 4.1,
                "reviews_count": 67,
                "products": [niche, f"{niche} wholesale"],
                "notes": "Direct manufacturer",
            },
        ]

        # Simulate API delay
        time.sleep(1)

        suppliers.extend(mock_suppliers[:limit])
        return suppliers

    def _search_industry_directories(
        self, niche: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        """Search industry-specific directories."""
        suppliers = []

        # Mock implementation - would search industry-specific sites
        mock_suppliers = [
            {
                "name": f"Industrial {niche.title()} Corp",
                "location": location,
                "contact": "procurement@industrial-corp.com",
                "website": "www.industrial-corp.com",
                "rating": 4.3,
                "reviews_count": 156,
                "products": [niche, f"industrial {niche}"],
                "notes": "Industry directory listing",
            },
            {
                "name": f"{niche.title()} Specialists Inc",
                "location": location,
                "contact": "(555) 321-0987",
                "website": "www.specialists-inc.com",
                "rating": 4.0,
                "reviews_count": 92,
                "products": [niche, f"specialty {niche}"],
                "notes": "Specialty supplier",
            },
        ]

        # Simulate API delay
        time.sleep(1)

        suppliers.extend(mock_suppliers[:limit])
        return suppliers

    def _deduplicate_suppliers(self, suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate suppliers based on name and location."""
        seen = set()
        unique_suppliers = []

        for supplier in suppliers:
            key = (supplier.get("name", "").lower(), supplier.get("location", "").lower())
            if key not in seen:
                seen.add(key)
                unique_suppliers.append(supplier)

        return unique_suppliers

    def verify_supplier(self, supplier: dict[str, Any]) -> dict[str, Any]:
        """Verify supplier information by checking website."""
        try:
            website = supplier.get("website", "")
            if not website:
                return supplier

            # Add protocol if missing
            if not website.startswith(("http://", "https://")):
                website = f"https://{website}"

            # Try to fetch website
            response = self.session.get(website, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Try to extract additional info
                title = soup.find("title")
                if title:
                    supplier["website_title"] = title.get_text().strip()

                # Look for contact info
                contact_patterns = ["contact", "email", "phone"]
                for pattern in contact_patterns:
                    # Capture pattern in closure to avoid late binding issue
                    def make_filter(p):
                        return lambda text: text and p in text.lower()
                    
                    elements = soup.find_all(text=make_filter(pattern))
                    if elements:
                        supplier[f"website_{pattern}"] = elements[0].strip()[:100]

                supplier["website_verified"] = True
            else:
                supplier["website_verified"] = False

        except Exception as e:
            logger.debug(f"Error verifying supplier website: {e}")
            supplier["website_verified"] = False

        return supplier
