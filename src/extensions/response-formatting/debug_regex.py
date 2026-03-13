#!/usr/bin/env python3
"""
Debug regex patterns.
"""

import re

def debug_regex():
    """Debug regex patterns."""
    content = 'iPhone 15 Pro - $999, Brand: Apple, Rating: 4.8/5 stars, Available at Apple Store with free shipping and warranty'
    
    patterns = [
        r'^([a-zA-Z][a-zA-Z0-9\s]*(?:Air|Pro|Max|Ultra|Plus|Mini)?)',
        r'^([a-zA-Z]+[a-zA-Z0-9\s]*)',
        r'^([^\-]+)',
        r'^(iPhone[^-]*)',
        r'^([^,\-]+)',
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, content)
        if match:
            print(f"Pattern {i+1}: '{pattern}' -> '{match.group(1).strip()}'")
        else:
            print(f"Pattern {i+1}: '{pattern}' -> No match")

if __name__ == "__main__":
    debug_regex()