"""
Utility functions for the AdSpy Marketing Intelligence Suite
"""

import hashlib
import re
from urllib.parse import parse_qs, urlparse


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Convert text to a safe filename for cross-platform compatibility.
    
    Args:
        text: Input text (URL, query, etc.)
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    if not text:
        return "unknown"
    
    # Remove/replace illegal characters for Windows/Unix
    # Illegal: < > : " | ? * \ / = (spaces for safety)
    text = re.sub(r'[<>:"|?*\\/= ]', '_', text)
    
    # Replace multiple underscores with single
    text = re.sub(r'_{2,}', '_', text)
    
    # Remove leading/trailing underscores and dots
    text = text.strip('_.')
    
    # Check for Windows reserved names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    base_name = text.split('.')[0].upper()
    if base_name in reserved_names:
        text = f"safe_{text}"
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Ensure it's not empty
    if not text:
        text = "sanitized"
    
    return text


def generate_url_slug(url: str) -> str:
    """
    Generate a short, safe slug from a URL for use in filenames.
    
    Args:
        url: Full URL
        
    Returns:
        Safe slug suitable for filenames
    """
    try:
        parsed = urlparse(url)
        
        # Start with domain
        domain = parsed.netloc.replace('www.', '')
        
        # Add path info if available
        path_parts = [p for p in parsed.path.split('/') if p and p != 'index.html']
        
        # Create base slug
        base_slug = f"{domain}_{path_parts[0]}" if path_parts else domain
        
        # Add query params info if present
        if parsed.query:
            query_params = parse_qs(parsed.query)
            # Add significant query params
            significant_params = []
            for key in ['q', 'search', 'query', 'page_id', 'brand']:
                if key in query_params:
                    param_value = str(query_params[key][0])[:10]  # First 10 chars
                    significant_params.append(f"{key}_{param_value}")
            
            if significant_params:
                base_slug += f"_{'_'.join(significant_params)}"
        
        # Sanitize the slug
        slug = sanitize_filename(base_slug, max_length=80)
        
        # Add hash for uniqueness if URL is complex
        if len(url) > 100 or '?' in url:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            slug += f"_{url_hash}"
        
        return slug
    
    except Exception:
        # Fallback: create hash-based slug
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"url_{url_hash}"


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query for safe filename usage.
    
    Args:
        query: Search query string
        
    Returns:
        Safe filename part
    """
    # Replace spaces and special chars
    sanitized = re.sub(r'[^\w\s-]', '', query)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    
    return sanitize_filename(sanitized, max_length=50)


def create_safe_filename(prefix: str, identifier: str, extension: str = ".json") -> str:
    """
    Create a safe filename with prefix, identifier, and extension.
    
    Args:
        prefix: File prefix (e.g., "scrape", "crawl")
        identifier: Main identifier (URL, query, etc.)
        extension: File extension
        
    Returns:
        Complete safe filename
    """
    from datetime import datetime
    
    # Sanitize components
    safe_prefix = sanitize_filename(prefix, max_length=20)
    safe_identifier = sanitize_filename(identifier, max_length=60)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine parts
    return f"{safe_prefix}_{safe_identifier}_{timestamp}{extension}"
    
