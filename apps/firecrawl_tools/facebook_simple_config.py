"""
Simplified Facebook Ads scraping configuration
More reliable with fewer actions that could fail
"""

# Simple configuration with minimal actions
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
    "remove_base64_images": True,
    "location": {"country": "US", "languages": ["en"]},
}

# Alternative for EU users
FACEBOOK_ADS_EU_CONFIG = {
    "formats": ["markdown"], 
    "only_main_content": False,
    "timeout": 60000,
    "wait_for": 5000,
    "actions": [
        {"type": "wait", "milliseconds": 5000},  # Longer wait for consent
        {"type": "scroll", "direction": "down", "pixels": 800},
    ],
    "mobile": False,
    "location": {"country": "DE", "languages": ["en"]},
}
