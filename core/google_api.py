from __future__ import annotations

import os
import time
from typing import Any

import googlemaps


def _gmaps() -> googlemaps.Client:
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    return googlemaps.Client(key=key)


def text_search(
    query: str, location: str | None = None, radius_m: int = 50000, max_pages: int = 2
) -> list[dict[str, Any]]:
    """
    High-recall supplier lookup using Places Text Search.
    location: 'lat,lng' (optional). Example: '29.7604,-95.3698' for Houston.
    """
    gmaps = _gmaps()
    kwargs = {"query": query}
    if location:
        lat, lng = map(float, location.split(","))
        kwargs.update({"location": (lat, lng), "radius": radius_m})

    results: list[dict[str, Any]] = []
    page = gmaps.places(**kwargs)
    results.extend(page.get("results", []))
    pages = 1
    while "next_page_token" in page and pages < max_pages:
        time.sleep(2)  # Google requires short delay before next page token is valid
        page = gmaps.places(page_token=page["next_page_token"])
        results.extend(page.get("results", []))
        pages += 1
    return results


def place_details(place_id: str) -> dict[str, Any]:
    gmaps = _gmaps()
    fields = [
        "name",
        "rating",
        "user_ratings_total",
        "formatted_address",
        "international_phone_number",
        "website",
        "geometry/location",
        "opening_hours",
        "business_status",
        "types",
        "url",
    ]
    resp = gmaps.place(place_id=place_id, fields=fields)
    return resp.get("result", {})


def normalize_supplier(place: dict[str, Any]) -> dict[str, Any]:
    """Map Google result → your Supplier schema fields."""
    loc = place.get("geometry", {}).get("location") or {}
    return {
        "run_id": "",
        "name": place.get("name"),
        "domain": (place.get("website") or None),
        "locations": [place.get("formatted_address")] if place.get("formatted_address") else [],
        "product_types": [],  # fill later from Firecrawl site scrape
        "moq": None,
        "price_range": None,
        "ratings_avg": place.get("rating"),
        "ratings_count": place.get("user_ratings_total"),
        "source": "google",
        "extras": {
            "place_id": place.get("place_id"),
            "phone": place.get("international_phone_number"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "types": place.get("types"),
            "business_status": place.get("business_status"),
        },
    }
