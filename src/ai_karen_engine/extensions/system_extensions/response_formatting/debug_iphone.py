#!/usr/bin/env python3
"""
Debug iPhone extraction.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from formatters.product_formatter import ProductResponseFormatter

def debug_iphone():
    """Debug iPhone info extraction."""
    formatter = ProductResponseFormatter()
    
    content = 'iPhone 15 Pro - $999, Brand: Apple, Rating: 4.8/5 stars, Available at Apple Store with free shipping and warranty'
    
    print("Content:")
    print(content)
    print("\n" + "="*50)
    
    product_info = formatter._extract_product_info(content)
    
    print("Extracted info:")
    print(f"Name: '{product_info.name}'")
    print(f"Brand: '{product_info.brand}'")
    print(f"Price: '{product_info.price}'")
    print(f"Rating: '{product_info.rating}'")

if __name__ == "__main__":
    debug_iphone()