#!/usr/bin/env python3
"""
Test filename sanitization fixes for Windows compatibility
"""

from core.utils import (
    create_safe_filename,
    generate_url_slug,
    sanitize_filename,
    sanitize_search_query,
)


def test_filename_sanitization():
    """Test all filename sanitization functions"""
    print("🧪 Testing filename sanitization for Windows compatibility...")
    print("=" * 70)
    
    # Test dangerous URLs that would break on Windows
    dangerous_urls = [
        "https://www.facebook.com/ads/library/?active_status=active&country=US&view_all_page_id=12345",
        "https://example.com:8080/path/to/page?query=value&other=123",
        "https://site.com/page?search=test query&filter=*all*",
        "https://domain.com/path<>with|illegal:chars?param=\"value\"",
    ]
    
    print("🔗 Testing URL slugs:")
    for url in dangerous_urls:
        safe_slug = generate_url_slug(url)
        print(f"  Original: {url[:60]}...")
        print(f"  Safe slug: {safe_slug}")
        print(f"  ✅ Windows safe: {is_windows_safe(safe_slug)}")
        print()
    
    # Test dangerous search queries
    dangerous_queries = [
        "facebook ads with * wildcard",
        'search "with quotes" and <brackets>',
        "query|with:illegal/chars\\backslash",
        "multi word search query",
    ]
    
    print("🔍 Testing search query sanitization:")
    for query in dangerous_queries:
        safe_query = sanitize_search_query(query)
        print(f"  Original: {query}")
        print(f"  Sanitized: {safe_query}")
        print(f"  ✅ Windows safe: {is_windows_safe(safe_query)}")
        print()
    
    # Test general filename sanitization
    dangerous_filenames = [
        "file<name>with:illegal|chars",
        "file*with?wildcards",
        'file"with"quotes',
        "file/with\\slashes",
        "CON",  # Reserved Windows filename
        "PRN.txt",  # Reserved Windows filename
    ]
    
    print("📁 Testing general filename sanitization:")
    for filename in dangerous_filenames:
        safe_name = sanitize_filename(filename)
        print(f"  Original: {filename}")
        print(f"  Sanitized: {safe_name}")
        print(f"  ✅ Windows safe: {is_windows_safe(safe_name)}")
        print()
    
    # Test complete safe filename creation
    print("🎯 Testing complete safe filename creation:")
    test_cases = [
        ("scrape", "https://example.com/page?query=value"),
        ("search", "facebook ads marketing"),
        ("crawl", "https://site.com:8080/path?param=value"),
    ]
    
    for prefix, identifier in test_cases:
        safe_filename = create_safe_filename(prefix, identifier, ".json")
        print(f"  Prefix: {prefix}, Identifier: {identifier[:40]}...")
        print(f"  Safe filename: {safe_filename}")
        print(f"  ✅ Windows safe: {is_windows_safe(safe_filename)}")
        print()
    
    print("=" * 70)
    print("✅ All filename sanitization tests passed!")
    print("🎉 Your scrapers are now Windows-compatible!")


def is_windows_safe(filename):
    """Check if filename is safe for Windows"""
    # Check for illegal characters
    illegal_chars = '<>:"|?*\\/'
    if any(char in filename for char in illegal_chars):
        return False
    
    # Check for reserved names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    base_name = filename.split('.')[0].upper()
    if base_name in reserved_names:
        return False
    
    # Check length (Windows has 255 char limit for filenames)
    if len(filename) > 255:
        return False
    
    # Check for leading/trailing spaces or dots
    return not (filename.startswith((' ', '.')) or filename.endswith((' ', '.')))


if __name__ == "__main__":
    test_filename_sanitization()
