#!/usr/bin/env python3
"""
Simple test of Firecrawl functionality
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from firecrawl import FirecrawlApp
    print("✅ Firecrawl imported successfully!")
except ImportError as e:
    print(f"❌ Firecrawl import failed: {e}")
    sys.exit(1)

try:
    from core.config import load_config
    print("✅ Core config imported successfully!")
except ImportError as e:
    print(f"❌ Core config import failed: {e}")
    sys.exit(1)

try:
    # Load config and get API key
    config = load_config()
    api_key = getattr(config, "firecrawl_api_key", None)
    
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in .env file")
        sys.exit(1)
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Initialize Firecrawl
    firecrawl = FirecrawlApp(api_key=api_key)
    print("✅ Firecrawl initialized successfully!")
    
    # Test simple scrape
    print("\n🔥 Testing simple scrape of example.com...")
    result = firecrawl.scrape("https://example.com", formats=["markdown"])
    
    if result and 'markdown' in result:
        content_length = len(result['markdown'])
        print(f"✅ Successfully scraped {content_length} characters!")
        print(f"📄 First 100 characters: {result['markdown'][:100]}...")
        
        # Save result
        import json
        from datetime import datetime
        
        os.makedirs("data/firecrawl_results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/firecrawl_results/test_scrape_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
    else:
        print("❌ No content received")
        
except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
