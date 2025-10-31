#!/usr/bin/env python3
"""
Debug ProductResponseFormatter extraction.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from formatters.product_formatter import ProductResponseFormatter

def debug_extraction():
    """Debug product info extraction."""
    formatter = ProductResponseFormatter()
    
    product_content = """
        MacBook Air M2 - $999
        Brand: Apple
        Model: MacBook Air 13-inch
        Rating: 4.5/5 stars (1,234 reviews)
        Available at Apple Store
        Specifications: 8GB RAM, 256GB SSD
        Features: Retina display, Touch ID, All-day battery
        """
    
    print("Content:")
    print(product_content)
    print("\n" + "="*50)
    
    product_info = formatter._extract_product_info(product_content)
    
    print("Extracted info:")
    print(f"Name: '{product_info.name}'")
    print(f"Brand: '{product_info.brand}'")
    print(f"Model: '{product_info.model}'")
    print(f"Price: '{product_info.price}'")
    print(f"Rating: '{product_info.rating}'")
    print(f"Store: '{product_info.store}'")
    print(f"Specifications: {product_info.specifications}")
    print(f"Features: {product_info.features}")

if __name__ == "__main__":
    debug_extraction()