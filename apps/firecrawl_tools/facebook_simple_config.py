"""
Enhanced Facebook Ads scraping configuration
Includes image scraping, date filtering, and deduplication features
"""

from datetime import datetime, timedelta
from typing import Any

# Enhanced configuration with image support and better scrolling
FACEBOOK_ADS_ENHANCED_CONFIG = {
    "formats": ["markdown", "html"],  # Include HTML for better parsing
    "only_main_content": False,
    "timeout": 120000,  # 2 minutes for more content
    "wait_for": 3000,  # 3 seconds initial wait
    "actions": [
        # Initial wait for page load
        {"type": "wait", "milliseconds": 3000},
        # More extensive scrolling to load more ads
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        # Final wait to ensure all content is loaded
        {"type": "wait", "milliseconds": 3000},
    ],
    "mobile": False,
    "remove_base64_images": False,  # Keep images for analysis
    "location": {"country": "US", "languages": ["en"]},
}

# Simple configuration with minimal actions (fallback)
FACEBOOK_ADS_SIMPLE_CONFIG = {
    "formats": ["markdown"],
    "only_main_content": False,
    "timeout": 90000,  # 1.5 minutes
    "wait_for": 3000,  # 3 seconds initial wait
    "actions": [
        # Just wait and scroll - no risky click actions
        {"type": "wait", "milliseconds": 3000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 1000},
    ],
    "mobile": False,
    "remove_base64_images": False,  # Changed to keep images
    "location": {"country": "US", "languages": ["en"]},
}

# Alternative for EU users
FACEBOOK_ADS_EU_CONFIG = {
    "formats": ["markdown", "html"],
    "only_main_content": False,
    "timeout": 60000,
    "wait_for": 5000,
    "actions": [
        {"type": "wait", "milliseconds": 5000},  # Longer wait for consent
        {"type": "scroll", "direction": "down", "pixels": 800},
        {"type": "wait", "milliseconds": 2000},
        {"type": "scroll", "direction": "down", "pixels": 800},
    ],
    "mobile": False,
    "remove_base64_images": False,  # Changed to keep images
    "location": {"country": "DE", "languages": ["en"]},
}

# Date range presets for filtering
DATE_RANGE_PRESETS = {
    "last_7_days": {"start_date": datetime.now() - timedelta(days=7), "end_date": datetime.now()},
    "last_30_days": {"start_date": datetime.now() - timedelta(days=30), "end_date": datetime.now()},
    "last_90_days": {"start_date": datetime.now() - timedelta(days=90), "end_date": datetime.now()},
    "last_6_months": {
        "start_date": datetime.now() - timedelta(days=180),
        "end_date": datetime.now(),
    },
    "last_year": {"start_date": datetime.now() - timedelta(days=365), "end_date": datetime.now()},
}


class AdDeduplicator:
    """Handle deduplication of Facebook ads based on headlines, images, and videos"""

    def __init__(self):
        self.seen_headlines: set = set()
        self.seen_images: set = set()
        self.seen_videos: set = set()
        self.seen_combinations: set = set()

    def is_duplicate(self, ad_data: dict[str, Any]) -> bool:
        """Check if an ad is a duplicate based on content"""
        headline = self._extract_headline(ad_data)
        images = self._extract_images(ad_data)
        videos = self._extract_videos(ad_data)

        # Create a unique signature for this ad
        signature = self._create_signature(headline, images, videos)

        if signature in self.seen_combinations:
            return True

        # Check individual components
        if headline and headline in self.seen_headlines:
            return True

        for image in images:
            if image in self.seen_images:
                return True

        for video in videos:
            if video in self.seen_videos:
                return True

        # If not duplicate, record all components
        if headline:
            self.seen_headlines.add(headline)
        self.seen_images.update(images)
        self.seen_videos.update(videos)
        self.seen_combinations.add(signature)

        return False

    def _extract_headline(self, ad_data: dict[str, Any]) -> str | None:
        """Extract headline from ad data"""
        # Look for common headline patterns in the content
        content = str(ad_data.get("content", ""))

        # Simple headline extraction (can be enhanced with regex)
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # Skip if too short or looks like metadata
            if len(line) > 10 and not line.startswith(("http", "www", "@", "#")):
                return line.lower()  # Normalize for comparison

        return None

    def _extract_images(self, ad_data: dict[str, Any]) -> list[str]:
        """Extract image URLs or hashes from ad data"""
        images = []
        content = str(ad_data.get("content", ""))

        # Look for image patterns (URLs, base64, etc.)
        import re

        # Find image URLs
        img_urls = re.findall(r"https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)", content, re.IGNORECASE)
        images.extend(img_urls)

        # Find base64 images (first 50 chars as signature)
        base64_images = re.findall(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]{50})", content)
        images.extend(base64_images)

        return images

    def _extract_videos(self, ad_data: dict[str, Any]) -> list[str]:
        """Extract video URLs or identifiers from ad data"""
        videos = []
        content = str(ad_data.get("content", ""))

        import re

        # Find video URLs
        video_urls = re.findall(r"https?://[^\s]+\.(?:mp4|avi|mov|webm)", content, re.IGNORECASE)
        videos.extend(video_urls)

        # Find YouTube/Facebook video IDs
        youtube_ids = re.findall(r"youtube\.com/watch\?v=([A-Za-z0-9_-]+)", content)
        facebook_video_ids = re.findall(r"facebook\.com/[^/]+/videos/(\d+)", content)

        videos.extend(youtube_ids)
        videos.extend(facebook_video_ids)

        return videos

    def _create_signature(self, headline: str | None, images: list[str], videos: list[str]) -> str:
        """Create unique signature for an ad"""
        components = []

        if headline:
            components.append(f"h:{headline[:50]}")  # First 50 chars of headline

        if images:
            components.append(f"i:{len(images)}:{hash(tuple(images))}")

        if videos:
            components.append(f"v:{len(videos)}:{hash(tuple(videos))}")

        return "|".join(components) if components else "empty"

    def get_stats(self) -> dict[str, int]:
        """Get deduplication statistics"""
        return {
            "unique_headlines": len(self.seen_headlines),
            "unique_images": len(self.seen_images),
            "unique_videos": len(self.seen_videos),
            "total_combinations": len(self.seen_combinations),
        }


class DateRangeFilter:
    """Handle date range filtering for Facebook ads"""

    def __init__(self, start_date: datetime | None = None, end_date: datetime | None = None):
        self.start_date = start_date
        self.end_date = end_date

    @classmethod
    def from_preset(cls, preset_name: str) -> "DateRangeFilter":
        """Create filter from preset name"""
        if preset_name not in DATE_RANGE_PRESETS:
            raise ValueError(
                f"Unknown preset: {preset_name}. Available: {list(DATE_RANGE_PRESETS.keys())}"
            )

        preset = DATE_RANGE_PRESETS[preset_name]
        return cls(preset["start_date"], preset["end_date"])

    @classmethod
    def custom_range(cls, days_back: int) -> "DateRangeFilter":
        """Create filter for custom number of days back"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return cls(start_date, end_date)

    def is_in_range(self, ad_date: datetime) -> bool:
        """Check if ad date is within range"""
        if self.start_date and ad_date < self.start_date:
            return False
        return not (self.end_date and ad_date > self.end_date)

    def extract_ad_date(self, ad_data: dict[str, Any]) -> datetime | None:
        """Extract date from ad data (to be implemented based on actual data structure)"""
        # This would need to be customized based on how dates appear in the scraped data
        content = str(ad_data.get("content", ""))

        import re

        # Look for various date patterns
        date_patterns = [
            r"(\d{1,2}/\d{1,2}/\d{4})",  # MM/DD/YYYY
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\w+ \d{1,2}, \d{4})",  # Month DD, YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                try:
                    # Try to parse the first match
                    date_str = matches[0]
                    # Simple parsing - could be enhanced
                    if "/" in date_str:
                        return datetime.strptime(date_str, "%m/%d/%Y")
                    if "-" in date_str:
                        return datetime.strptime(date_str, "%Y-%m-%d")
                    # Add more parsing logic as needed
                except ValueError:
                    continue

        return None


def build_url_with_date_filter(base_url: str, date_filter: DateRangeFilter) -> str:
    """Build Facebook Ads Library URL with date parameters"""
    if not date_filter.start_date or not date_filter.end_date:
        return base_url

    # Facebook Ads Library URL parameters for date filtering
    start_timestamp = int(date_filter.start_date.timestamp())
    end_timestamp = int(date_filter.end_date.timestamp())

    separator = "&" if "?" in base_url else "?"
    date_params = f"creation_date_min={start_timestamp}&creation_date_max={end_timestamp}"

    return f"{base_url}{separator}{date_params}"
