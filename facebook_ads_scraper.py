#!/usr/bin/env python3
"""
Facebook Ads Scraper - Extract Headlines, Subheadlines, CTAs, and Important Text
Specifically designed to extract key ad elements from Facebook Ad Library
"""

import json
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from firecrawl import FirecrawlApp

    from apps.firecrawl_tools.firecrawl_presets import (
        POPULAR_FACEBOOK_PAGES,
        get_facebook_ads_url,
        get_preset_examples,
    )
    from core.config import load_config
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

class FacebookAdsExtractor:
    """Extract specific elements from Facebook ads"""
    
    def __init__(self):
        config = load_config()
        api_key = getattr(config, "firecrawl_api_key", None)
        if not api_key:
            print("❌ FIRECRAWL_API_KEY not found in .env file")
            sys.exit(1)
        
        self.firecrawl = FirecrawlApp(api_key=api_key)
        print(f"✅ Firecrawl initialized with API key: {api_key[:10]}...")
    
    def scrape_facebook_ads(self, brand_name="nike"):
        """Scrape Facebook ads and extract key elements"""
        
        # Get the URL for the brand
        examples = get_preset_examples()
        if brand_name in examples:
            url = examples[brand_name]
        else:
            url = get_facebook_ads_url(POPULAR_FACEBOOK_PAGES.get(brand_name, POPULAR_FACEBOOK_PAGES["nike"]))
        
        print(f"\n🎯 Scraping Facebook ads for: {brand_name}")
        print(f"🔗 URL: {url}")
        
        # Configuration optimized for faster, more reliable ad extraction
        scrape_config = {
            "formats": ["markdown"],  # Start with just markdown for speed
            "only_main_content": True,
            "timeout": 45000,  # Reduced timeout
            "wait_for": 3000   # Reduced wait time
        }
        
        try:
            print("⏳ Scraping ads (this may take 60-90 seconds)...")
            result = self.firecrawl.scrape(url, **scrape_config)
            
            if not result:
                print("❌ No result returned from Firecrawl")
                return None
            
            # Save raw result
            self._save_result("raw", result, brand_name)
            
            # Handle Document object - extract attributes safely
            markdown_content = ""
            json_content = None
            
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown or ""
            elif hasattr(result, 'content'):
                markdown_content = result.content or ""
            elif isinstance(result, dict) and 'markdown' in result:
                markdown_content = result['markdown'] or ""
            
            if hasattr(result, 'json'):
                json_content = result.json
            elif isinstance(result, dict) and 'json' in result:
                json_content = result['json']
            
            # Extract ads from JSON format
            ads = []
            if json_content:
                try:
                    ads = json.loads(json_content) if isinstance(json_content, str) else json_content
                    if not isinstance(ads, list):
                        ads = [ads] if ads else []
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"⚠️ Could not parse JSON ads: {e}")
                    ads = []
            
            # Also try to extract from markdown using simple patterns
            if not ads and markdown_content:
                ads = self._extract_ads_from_markdown(markdown_content)
            
            print("\n📊 Results:")
            print(f"   📄 Content length: {len(markdown_content):,} characters")
            print(f"   🎯 Ads found: {len(ads)}")
            
            if ads:
                print(f"\n✅ Successfully extracted {len(ads)} ads!")
                self._display_ads(ads[:5])  # Show first 5 ads
                
                # Save processed ads
                processed_result = {
                    "brand": brand_name,
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "ads": ads,
                    "raw_result": result
                }
                self._save_result("processed", processed_result, brand_name)
                
                return processed_result
            print("⚠️ No ads were extracted. Possible causes:")
            print("   - Facebook changed their ad display format")
            print("   - No active ads for this brand currently")
            print("   - Geographic restrictions")
            print("   - Rate limiting or access restrictions")

            return {
                "brand": brand_name,
                "url": url,
                "ads": [],
                "raw_result": result,
                "error": "No ads extracted"
            }
        
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return None
    
    def _extract_ads_from_markdown(self, markdown_content):
        """Extract ads from Facebook Ad Library markdown content"""
        ads = []
        lines = markdown_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for sponsored content pattern
            if 'Sponsored' in line:
                current_ad = {'advertiser': None, 'headline': None, 'cta': None, 'library_id': None, 'date_started': None}
                
                # Look backward for advertiser (usually appears before "Sponsored")
                for j in range(max(0, i-5), i):
                    prev_line = lines[j].strip()
                    if prev_line.startswith('[') and ']' in prev_line and 'facebook.com' in prev_line:
                        # Extract advertiser name from [Advertiser Name](url) format
                        advertiser = prev_line[1:prev_line.find(']')]
                        current_ad['advertiser'] = advertiser
                        break
                
                # Look forward for headline and CTA
                for j in range(i+1, min(len(lines), i+10)):
                    next_line = lines[j].strip()
                    
                    # Skip empty lines
                    if not next_line:
                        continue
                    
                    # Look for headline (usually the first substantial text after "Sponsored")
                    if not current_ad['headline'] and len(next_line) > 10 and not next_line.startswith('![') and '➡️' not in next_line:
                        current_ad['headline'] = next_line
                    
                    # Look for CTA patterns
                    if any(cta in next_line.lower() for cta in ['shop now', 'learn more', 'get started', 'buy now', 'sign up', 'download']):
                        # Clean up CTA - remove markdown links
                        cta = next_line
                        if '](http' in cta:
                            cta = cta[:cta.find('](http')]
                        current_ad['cta'] = cta
                    
                    # Look for Library ID
                    if 'Library ID:' in next_line:
                        current_ad['library_id'] = next_line.replace('Library ID:', '').strip()
                    
                    # Look for start date
                    if 'Started running on' in next_line:
                        current_ad['date_started'] = next_line.replace('Started running on', '').strip()
                    
                    # Stop when we hit another ad or significant break
                    if 'Active' in next_line and 'Library ID:' in lines[j+1] if j+1 < len(lines) else False:
                        break
                
                # Only add if we found meaningful content
                if current_ad['advertiser'] or current_ad['headline']:
                    ads.append(current_ad)
            
            i += 1
        
        return ads
    
    def _display_ads(self, ads):
        """Display extracted ads in a nice format"""
        print("\n" + "="*60)
        print("🎯 EXTRACTED FACEBOOK ADS")
        print("="*60)
        
        for i, ad in enumerate(ads, 1):
            print(f"\n📱 AD #{i}")
            print("-" * 40)
            
            if ad.get('headline'):
                print(f"📢 Headline: {ad['headline']}")
            if ad.get('subheadline'):
                print(f"📝 Subheadline: {ad['subheadline']}")
            if ad.get('advertiser'):
                print(f"👤 Advertiser: {ad['advertiser']}")
            if ad.get('cta'):
                print(f"🎯 CTA: {ad['cta']}")
            if ad.get('important_text'):
                print(f"💡 Important Text: {ad['important_text']}")
            if ad.get('offer'):
                print(f"💰 Offer: {ad['offer']}")
    
    def _save_result(self, result_type, data, brand_name):
        """Save results to file with proper serialization handling"""
        os.makedirs("data/firecrawl_results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/firecrawl_results/facebook_ads_{result_type}_{brand_name}_{timestamp}.json"
        
        # Convert data to JSON-serializable format
        serializable_data = self._make_serializable(data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 {result_type.title()} results saved to: {filename}")
    
    def _make_serializable(self, obj):
        """Convert objects to JSON-serializable format"""
        if hasattr(obj, '__dict__'):
            # Convert objects with __dict__ to dictionaries
            return {k: self._make_serializable(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        # For any other type, convert to string
        return str(obj)

def main():
    """Main function"""
    extractor = FacebookAdsExtractor()
    
    print("🔥 Facebook Ads Scraper")
    print("=" * 50)
    
    # Show available brands
    examples = get_preset_examples()
    print("\n📊 Available brands:")
    for i, brand in enumerate(examples.keys(), 1):
        print(f"  {i}. {brand.title()}")
    
    # Get user choice
    try:
        choice = input(f"\nSelect brand (1-{len(examples)}) or press Enter for Nike [1]: ").strip()
        if not choice:
            choice = "1"
        
        brand_idx = int(choice) - 1
        brands = list(examples.keys())
        
        if 0 <= brand_idx < len(brands):
            brand_name = brands[brand_idx]
        else:
            print("Invalid choice, using Nike")
            brand_name = "nike"
        
        print(f"✅ Selected: {brand_name.title()}")
        
        # Scrape ads
        result = extractor.scrape_facebook_ads(brand_name)
        
        if result and result.get('ads'):
            print(f"\n🎉 SUCCESS! Extracted {len(result['ads'])} ads with:")
            print("   📢 Headlines")  
            print("   📝 Subheadlines")
            print("   👤 Advertisers")
            print("   🎯 Call-to-Actions")
            print("   💡 Important Text")
            print("   💰 Offers")
            print("\n💾 All data saved to data/firecrawl_results/")
        else:
            print("\n⚠️ No ads extracted. Check the saved raw data for debugging.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
