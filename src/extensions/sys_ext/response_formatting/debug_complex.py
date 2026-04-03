#!/usr/bin/env python3
"""
Debug complex product extraction.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from formatters.product_formatter import ProductResponseFormatter

def debug_complex():
    """Debug complex product info extraction."""
    formatter = ProductResponseFormatter()
    
    complex_content = """
        ASUS ROG Strix G15 - $1,299 (was $1,499)
        Brand: ASUS
        Model: ROG Strix G15 G513QM
        Rating: 4.3/5 stars (1,567 reviews)
        In stock - ships within 2 business days
        Shipping: Free standard shipping
        Warranty: 2-year manufacturer warranty
        Available at Best Buy and Amazon
        
        Specifications:
        Processor: AMD Ryzen 7 5800H
        Graphics: NVIDIA RTX 3060
        RAM: 16GB DDR4
        Storage: 512GB NVMe SSD
        Display: 15.6-inch 144Hz
        Weight: 5.07 lbs
        
        Features:
        - RGB backlit keyboard
        - Advanced cooling system
        - Dolby Atmos audio
        - Wi-Fi 6 connectivity
        - Multiple USB ports
        
        Description: High-performance gaming laptop designed for competitive gaming and content creation.
        """
    
    print("Content:")
    print(complex_content)
    print("\n" + "="*50)
    
    product_info = formatter._extract_product_info(complex_content)
    
    print("Extracted info:")
    print(f"Name: '{product_info.name}'")
    print(f"Brand: '{product_info.brand}'")
    print(f"Model: '{product_info.model}'")
    print(f"Price: '{product_info.price}'")
    print(f"Original Price: '{product_info.original_price}'")
    print(f"Rating: '{product_info.rating}'")
    print(f"Review Count: '{product_info.review_count}'")
    print(f"Availability: '{product_info.availability}'")
    print(f"Shipping: '{product_info.shipping}'")
    print(f"Warranty: '{product_info.warranty}'")
    print(f"Store: '{product_info.store}'")
    print(f"Description: '{product_info.description}'")
    print(f"Specifications ({len(product_info.specifications)}):")
    for spec in product_info.specifications:
        print(f"  - {spec['name']}: {spec['value']}")
    print(f"Features ({len(product_info.features)}):")
    for feature in product_info.features:
        print(f"  - {feature}")

if __name__ == "__main__":
    debug_complex()