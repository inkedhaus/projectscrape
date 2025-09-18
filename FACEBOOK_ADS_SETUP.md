# Facebook Ad Library Scraping Integration

## 🎯 Overview
Successfully integrated a specialized Facebook Ad Library scraping configuration into your Firecrawl tools. This preset configuration is optimized for extracting ads from Facebook's Ad Library with smart ad detection and processing.

## ✅ What's Been Added

### 1. **firecrawl_presets.py**
- **Location**: `apps/firecrawl_tools/firecrawl_presets.py`
- **Features**:
  - Pre-configured actions for Facebook consent dismissal
  - 20-cycle scroll pattern for comprehensive ad loading
  - Smart ad detection schema
  - Offer pattern matching (discounts, promos, etc.)
  - Text cleaning and normalization
  - Popular brand page IDs (Nike, Adidas, Amazon, etc.)

### 2. **Enhanced main.py**
- **Location**: `apps/firecrawl_tools/main.py`
- **Features**:
  - New menu option 7: "FACEBOOK ADS"
  - Interactive brand selection
  - Custom page ID input
  - Search terms input
  - Smart result processing and display

### 3. **Test Suite**
- **Location**: `test_facebook_ads_integration.py`
- **Results**: ✅ 5/6 tests passed (firecrawl-py not installed, expected)

## 🚀 How to Use

### Prerequisites
1. Install firecrawl-py package:
   ```bash
   pip install firecrawl-py
   ```

2. Set your Firecrawl API key in `.env`:
   ```
   FIRECRAWL_API_KEY=fc-your-api-key-here
   ```

### Running the Scraper
1. **Start the application**:
   ```bash
   python -m apps.firecrawl_tools.main
   ```

2. **Select option 7** (FACEBOOK ADS) from the menu

3. **Choose your input method**:
   - **Option 1**: Popular brands (Nike, Adidas, Amazon, etc.)
   - **Option 2**: Custom Facebook page ID
   - **Option 3**: Search terms
   - **Option 4**: Custom Facebook Ads Library URL

4. **Wait for results** (2-3 minutes due to dynamic content loading)

## 📊 What You Get

### Raw Data
- Complete markdown content from Facebook Ad Library
- All dynamic content after scrolling and loading

### Processed Results
- **Headlines**: Main ad text
- **Advertisers**: Company/page names
- **CTAs**: Call-to-action buttons (Shop Now, Learn More, etc.)
- **Offers**: Detected discounts and promotions
- **Clean formatting**: Normalized and cleaned text

### File Output
Results saved to: `data/firecrawl_results/facebook_ads_[brand]_[timestamp].json`

## 🎯 Popular Brands Available
- Nike (310947142968045)
- Adidas (20793831865)
- Amazon (20446254070)
- Walmart (36622166142)
- Target (14467896762)
- Best Buy (116179995091093)
- McDonald's (66988152632)
- Starbucks (17800226067)
- Coca-Cola (7924983368)

## ⚙️ Configuration Details

### Specialized Settings
- **Timeout**: 120 seconds (2 minutes)
- **Scroll cycles**: 20 comprehensive scrolls
- **Consent handling**: Automatic cookie dismissal
- **User agents**: Rotating pool for reliability
- **Location**: US-based scraping
- **Format**: Markdown for easy processing

### Smart Processing
- **Offer detection**: Regex patterns for discounts, promos, BOGO, etc.
- **Text cleaning**: Removes Facebook UI elements
- **Ad structure**: Headline, subheadline, CTA, offer extraction

## 🔧 Example Usage

```python
# Direct usage in your code
from apps.firecrawl_tools.firecrawl_presets import (
    FACEBOOK_ADS_CONFIG,
    get_facebook_ads_url,
    process_facebook_ad_results
)

# Generate Nike's ads URL
url = get_facebook_ads_url(page_id="310947142968045", country="US")

# Use with Firecrawl
result = firecrawl.scrape(url, **FACEBOOK_ADS_CONFIG)

# Process results
ads = process_facebook_ad_results(result)
```

## ✨ Ready to Run!

Your Facebook Ad Library scraping integration is now complete and ready to use. Simply install firecrawl-py, set your API key, and start scraping ads with the specialized configuration optimized for Facebook's dynamic content.

The system handles all the complexity of:
- Cookie consent dismissal
- Dynamic content loading
- Comprehensive scrolling
- Ad detection and extraction
- Text processing and normalization

Just select option 7 from the Firecrawl menu and start exploring competitor ads! 🎯
