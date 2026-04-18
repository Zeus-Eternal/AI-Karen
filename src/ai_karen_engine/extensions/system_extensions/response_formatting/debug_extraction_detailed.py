#!/usr/bin/env python3
"""
Debug detailed extraction logic.
"""

import sys
import re
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from formatters.product_formatter import ProductInfo

def debug_extraction():
    """Debug extraction step by step."""
    content = 'iPhone 15 Pro - $999, Brand: Apple, Rating: 4.8/5 stars, Available at Apple Store with free shipping and warranty'
    
    print("Content:", content)
    print("\n" + "="*50)
    
    product_info = ProductInfo(name="Product")
    
    # Extract product name
    lines = content.strip().split('\n')
    print("Lines:", lines)
    
    for line in lines:
        line = line.strip()
        print(f"\nProcessing line: '{line}'")
        
        if not line:
            print("  -> Empty line, skipping")
            continue
            
        # Skip lines that are clearly not product names
        skip_keywords = ['here are', 'these are', 'available', 'specifications', 'features']
        if any(skip in line.lower() for skip in skip_keywords):
            print(f"  -> Contains skip keywords, skipping")
            continue
            
        # Look for lines with product name and price pattern
        price_match = re.search(r'(.+?)\s*\-\s*\$\d+', line)
        if price_match:
            name = price_match.group(1).strip()
            print(f"  -> Found price pattern, name: '{name}'")
            if len(name) > 3:
                product_info.name = name
                print(f"  -> Set product name to: '{product_info.name}'")
                break
        
        # Look for lines that start with a product name (including iPhone, iPad, etc.)
        brand_match = re.search(r'^([a-zA-Z][a-zA-Z0-9\s]*(?:Air|Pro|Max|Ultra|Plus|Mini)?)', line)
        if brand_match and '$' in line:
            name = brand_match.group(1).strip()
            print(f"  -> Found brand pattern, name: '{name}'")
            # Remove trailing words that are not part of the product name
            name = re.sub(r'\s*\-.*$', '', name)
            print(f"  -> After cleanup, name: '{name}'")
            if len(name) > 3:
                product_info.name = name
                print(f"  -> Set product name to: '{product_info.name}'")
                break
    
    print(f"\nFinal product name: '{product_info.name}'")

if __name__ == "__main__":
    debug_extraction()