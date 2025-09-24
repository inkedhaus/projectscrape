# 🧩 Facebook Ads Playwright Scraper - Clean Implementation

Complete Facebook Ads Library scraper following clean instructions for optimal ad extraction.

## 🎯 Overview

This is a **complete rewrite** of the Facebook ads scraper using **Playwright browser automation** instead of the Firecrawl API approach. It follows the clean instructions provided for maximum reliability and performance.

### Key Differences from Firecrawl Version:
- **Direct browser control** vs API calls
- **Progressive content loading** during scrolling 
- **Real-time network capture** of media URLs
- **Smart scrolling with verification** 
- **Progress checkpointing** every 50 ads
- **Selector caching** for reliability

## ✅ Features Implemented

### 1. Browser Setup (Clean Instructions)
- `headless=False` - Avoid detection 
- Fixed viewport `1920x1080` - Standard desktop size
- Normal Chrome User-Agent - No randomization
- **Selector caching** in `selectors.json`

### 2. Smart Scrolling with Verification
```python
async def smart_scroll(page):
    # Measures if new content loads after scrolling
    # Returns True/False if content appeared
    # More intelligent than infinite scroll
```

### 3. Network Capture with Retry Queue
- Intercepts `page.on("response")` events
- Captures media URLs from `fbcdn.net` and `safe_image.php` 
- **Retry queue** for failed downloads
- More reliable than DOM-based media detection

### 4. DOM Extraction (Enhanced)
- Extract after **each scroll step** (not just at end)
- **Multiple selector fallbacks**
- Structured `AdRecord` objects
- Better error handling

### 5. Progress Checkpointing
- Save progress every **50 ads** to `checkpoint.json`
- **Resume capability** on restart
- Prevents data loss on interruption

### 6. Error Handling (Realistic)
- "No results found" → graceful exit
- Stale element → re-query DOM
- Network timeout → skip, continue
- Cookie banner → auto-accept

### 7. Deduplication
- **URL-based** unique keys (simple & effective)
- No complex image hashing needed
- Maintains `seen_ads` set

### 8. Rate Limiting
- `800-1500ms` delays between scrolls
- ~1 scroll per second maximum
- Facebook-friendly pacing

## 📁 File Structure

```
facebook_ads_playwright_scraper.py    # Main scraper implementation
selectors.json                        # Cached working selectors  
test_playwright_scraper.py            # Test script
data/playwright_results/              # Output directory
  └── checkpoint.json                 # Progress resumption
  └── facebook_ads_playwright_*.json  # Results files
  └── facebook_ads_playwright_*.csv   # CSV exports
```

## 🚀 Usage

### Basic Usage
```python
from facebook_ads_playwright_scraper import FacebookAdsPlaywrightScraper

# Initialize scraper
scraper = FacebookAdsPlaywrightScraper()

# Run scraping
results = await scraper.run_scrape(
    url="https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&search_type=page&view_all_page_id=310947142968045",
    max_scrolls=50,
    brand_name="MadRabbit"
)
```

### Quick Test Run
```bash
python test_playwright_scraper.py
```

### Full Production Run  
```bash
python facebook_ads_playwright_scraper.py
```

## 📊 Output Data Structure

### AdRecord Fields
```python
@dataclass
class AdRecord:
    library_id: Optional[str] = None      # Facebook Library ID
    page_name: Optional[str] = None       # Advertiser/Page name
    caption: Optional[str] = None         # Ad caption text
    headline: Optional[str] = None        # Ad headline  
    cta_text: Optional[str] = None        # Call-to-action button text
    destination_url: Optional[str] = None # Landing page URL
    media_urls: List[str] = None          # Image/video URLs
    date_started: Optional[str] = None    # Ad start date
    ad_url: Optional[str] = None          # Unique ad identifier
    extracted_at: Optional[str] = None    # Extraction timestamp
```

### Results Structure
```python
{
    "success": true,
    "timestamp": "2025-09-18T17:00:00",
    "duration_seconds": 125.5,
    "brand": "MadRabbit", 
    "scrape_method": "Playwright - Clean Implementation",
    "metrics": {
        "total_ads": 47,
        "unique_ads": 45,
        "media_urls": 89,
        "scrolls_performed": 25,
        "retry_queue_remaining": 2
    },
    "ads": [...],           # Array of AdRecord objects
    "media_urls": [...],    # Captured media URLs
    "config": {...}         # Scraper configuration used
}
```

## 🔧 Configuration

### Selectors (selectors.json)
The scraper uses cached selectors with multiple fallbacks:

```json
{
    "ad_cards": [
        "[data-testid='ad-card']",
        "[role='article']", 
        "div[style*='border']:has(img)"
    ],
    "media_images": [
        "img[src*='fbcdn']",
        "img[src*='safe_image.php']"
    ],
    "ad_text": [
        "[data-testid='ad-text']",
        "div[dir='auto']"
    ]
}
```

### Browser Settings
```python
browser = await p.chromium.launch(
    headless=False,  # Detection avoidance
    args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox"
    ]
)

context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},  # Standard size
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
)
```

## 📈 Performance Characteristics

### Timing Expectations
- **Initialization**: 2-3 seconds
- **Navigation**: 5-10 seconds  
- **Per scroll**: 1.5-2 seconds + delay
- **50 ads**: ~2-3 minutes
- **100 ads**: ~5-8 minutes

### Memory Usage
- **Browser process**: ~200-400MB
- **Python process**: ~50-100MB
- **Data structures**: Minimal (streaming approach)

## 🛡️ Anti-Detection Features

### What's Included ✅
- Non-headless browsing (`headless=False`)
- Standard viewport size (`1920x1080`)
- Normal user agent string
- Human-like scroll timing (`800-1500ms`)
- Rate limiting (~1 scroll/second)

### What's NOT Included ❌ 
- Proxy rotation (not needed for public API)
- Mouse movement simulation (overkill)
- Cookie storage (public data)
- Image hashing (URL dedup sufficient)
- Multiple contexts (one works fine)

## 🔍 Troubleshooting

### Common Issues

**No ads found**
- Check URL format
- Verify page loads in regular browser
- Check selectors in `selectors.json`

**Browser launch fails**
- Run: `playwright install chromium`
- Check system requirements
- Try with `headless=True` for debugging

**Network errors**
- Check internet connection
- Increase timeouts in code
- Check for rate limiting

**Memory issues**  
- Reduce `max_scrolls` parameter
- Clear browser cache between runs
- Check system RAM availability

### Debug Mode
Add debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Implementation Notes

### Critical Success Factors
1. `headless=False` - Most important for detection avoidance
2. `viewport: 1920x1080` - Standard desktop size
3. `wait_for_timeout(1500)` - Proper pacing 
4. Multiple selector fallbacks - Prevents breakage
5. URL-based deduplication - Simple & effective

### Core Functions
- `smart_scroll()` → Returns True/False if content loaded
- `capture_media_responses()` → Network interception
- `extract_cards_from_dom()` → Live DOM parsing  
- `run_scrape()` → Main orchestrator

### Error Recovery
- Stale elements → Re-query selectors
- Network timeouts → Continue with next scroll
- No results → Graceful exit
- Interruption → Resume from checkpoint

## 🔄 Comparison with Firecrawl Version

| Feature | Firecrawl | Playwright |
|---------|-----------|------------|
| **Approach** | Cloud API | Direct browser |
| **Content** | Static snapshot | Dynamic loading |
| **Media** | DOM parsing | Network capture |
| **Control** | Limited | Full browser control |
| **Rate Limits** | API quotas | Self-managed |
| **Reliability** | API dependent | Self-contained |
| **Setup** | API key only | Browser + deps |

## 🏁 Ready for Production

This implementation is **production-ready** with:
- ✅ Robust error handling
- ✅ Progress checkpointing  
- ✅ Multiple selector fallbacks
- ✅ Rate limiting compliance
- ✅ Comprehensive logging
- ✅ Clean data structures
- ✅ CSV/JSON export formats

The scraper follows Facebook's robots.txt and uses publicly available ad library data with appropriate rate limiting.
