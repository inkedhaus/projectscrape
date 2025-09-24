# Enhanced Facebook Ads Scraper

## Overview

The Enhanced Facebook Ads Scraper provides advanced features for scraping Facebook Ad Library data, including image scraping, date range filtering, and intelligent deduplication to ensure you only collect original, unique content.

## New Features

### 🖼️ Image Scraping
- **Image URLs**: Automatically extracts image URLs from scraped content
- **Base64 Images**: Preserves embedded images in base64 format for offline viewing
- **Image Deduplication**: Identifies and removes duplicate images based on URLs and content hashes

### 📅 Date Range Filtering
- **Preset Ranges**: Choose from common date ranges (7 days, 30 days, 90 days, 6 months, 1 year)
- **Custom Ranges**: Specify any number of days back from today
- **URL Parameters**: Automatically adds Facebook's date filtering parameters to URLs
- **Content Filtering**: Extracts and validates dates from ad content

### 🔄 Content Deduplication
- **Headline Detection**: Identifies duplicate ads with identical or similar headlines
- **Image Matching**: Prevents scraping the same visual content multiple times
- **Video Detection**: Identifies duplicate video content (YouTube, Facebook videos)
- **Smart Signatures**: Creates unique fingerprints combining headlines, images, and videos

## Usage

### Quick Start
```bash
python -m apps.firecrawl_tools.main
# Select option 7 (Facebook Ads)
```

### Configuration Options

#### 1. Enhanced Configuration
- **Best for**: Complete data collection with images
- **Features**: Extended scrolling, HTML + Markdown formats, image preservation
- **Speed**: Slower but more comprehensive
- **Use when**: You need maximum content coverage and images

#### 2. Simple Configuration  
- **Best for**: Fast basic scraping
- **Features**: Basic scrolling, Markdown format only
- **Speed**: Faster execution
- **Use when**: You need quick results without images

#### 3. EU Configuration
- **Best for**: European users dealing with consent pages
- **Features**: Extended consent waiting, optimized for GDPR
- **Speed**: Medium
- **Use when**: Scraping from European locations

### Date Range Options

1. **No Filter**: Scrapes all available ads regardless of date
2. **Last 7 days**: Recent ads from the past week
3. **Last 30 days**: Ads from the past month
4. **Last 90 days**: Ads from the past quarter
5. **Last 6 months**: Medium-term ad history
6. **Last year**: Long-term ad analysis
7. **Custom**: Specify exact number of days back

### Example Workflow

```python
# 1. Start the scraper
python -m apps.firecrawl_tools.main

# 2. Select Facebook Ads (option 7)

# 3. Enter Facebook Ads Library URL
# Example: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&media_type=all&q=nike

# 4. Choose configuration
# Enhanced (1) - for complete data with images
# Simple (2) - for fast basic scraping  
# EU (3) - for European users

# 5. Select date range
# Last 30 days (3) - good balance of recency and volume

# 6. Enable deduplication (default: Yes)
# This prevents duplicate ads in results

# Results saved to: data/firecrawl_results/facebook_ads_enhanced_nike_20241217_210324.json
```

## Output Format

### Enhanced Results Structure
```json
{
  "raw_result": {
    "markdown": "...",
    "html": "..."
  },
  "url": "https://facebook.com/ads/library/...",
  "brand": "nike",
  "config_used": "Enhanced",
  "timestamp": "2024-12-17T21:03:24",
  "features": {
    "images_included": true,
    "date_filtered": true,
    "deduplicated": true
  },
  "date_filter": {
    "start_date": "2024-11-17T21:03:24",
    "end_date": "2024-12-17T21:03:24"
  },
  "extracted_ads": [
    {
      "content": "Ad content with images...",
      "extracted_at": "2024-12-17T21:03:24",
      "extracted_date": "2024-12-15T10:30:00"
    }
  ],
  "deduplication_stats": {
    "unique_headlines": 25,
    "unique_images": 18,
    "unique_videos": 3,
    "total_combinations": 42
  }
}
```

## Technical Details

### Date Range URL Parameters
The scraper automatically adds Facebook's date filtering parameters:
- `creation_date_min`: Unix timestamp for start date
- `creation_date_max`: Unix timestamp for end date

### Deduplication Algorithm
1. **Extract Components**: Headlines, image URLs, video URLs from each ad
2. **Create Signature**: Unique fingerprint combining all components
3. **Check Duplicates**: Compare against previously seen content
4. **Filter Results**: Only include truly unique ads

### Image Processing
- **URL Detection**: Regex patterns for common image formats (jpg, png, gif, webp)
- **Base64 Extraction**: Identifies embedded images with data URIs
- **Hash Signatures**: Creates content-based hashes for duplicate detection

## Best Practices

### For Maximum Coverage
1. Use **Enhanced Configuration**
2. Set **No Date Filter** or **Last 6 months**
3. Enable **Deduplication** to avoid redundancy
4. Allow **2-3 minutes** for complete processing

### For Quick Analysis
1. Use **Simple Configuration** 
2. Set **Last 30 days** date filter
3. Enable **Deduplication** 
4. Expect **30-60 seconds** processing time

### For Large Brands
1. Use **Enhanced Configuration** with **deduplication**
2. Consider **multiple smaller date ranges** to avoid timeouts
3. Monitor **output file sizes** (can be several MB)

## Troubleshooting

### Common Issues

#### "No ads found"
- Check if URL is accessible without login
- Try different date ranges (Facebook may filter old ads)
- Verify brand/company name spelling in URL

#### "Timeout errors"
- Switch to **Simple Configuration**
- Reduce date range to **Last 30 days**
- Check internet connection stability

#### "Duplicate content still appearing"
- Ensure deduplication is enabled
- Note that slight variations in headlines may pass through
- Check deduplication stats in output for effectiveness

### Performance Tips
- **Enhanced mode**: 2-5 minutes for comprehensive results
- **Simple mode**: 30-60 seconds for basic content
- **Large brands**: May generate 5-20MB result files
- **Memory usage**: Monitor for very large scraping sessions

## File Locations

- **Results**: `data/firecrawl_results/`
- **Configuration**: `apps/firecrawl_tools/facebook_simple_config.py`
- **Main Script**: `apps/firecrawl_tools/main.py`

## API Requirements

Requires valid Firecrawl API key in `.env` file:
```
FIRECRAWL_API_KEY=your_api_key_here
```

## Changelog

### v2.0 - Enhanced Features
- ✅ Added image scraping support
- ✅ Implemented date range filtering with presets
- ✅ Built intelligent deduplication system
- ✅ Enhanced HTML content extraction
- ✅ Added comprehensive ad analysis
- ✅ Improved error handling and user feedback
- ✅ Added configuration selection options
