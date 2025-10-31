#!/usr/bin/env python3
"""
Debug section extraction.
"""

import re

def debug_sections():
    """Debug section extraction."""
    content = """
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
    print(content)
    print("\n" + "="*50)
    
    # Test specifications section
    spec_section_start = re.search(r'(?i)specifications?\s*[:\-]?\s*$', content, re.MULTILINE)
    if spec_section_start:
        print("Found specifications section at position:", spec_section_start.start(), "to", spec_section_start.end())
        print("Match:", repr(spec_section_start.group()))
        
        # Extract lines after "Specifications:" until next section or empty line
        lines = content[spec_section_start.end():].split('\n')
        print("Lines after specifications:")
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"  {i}: '{line}'")
            if not line or line.lower().startswith(('features', 'description')):
                print(f"    -> Breaking at line {i}")
                break
            if ':' in line:
                key, value = line.split(':', 1)
                print(f"    -> Spec: '{key.strip()}' = '{value.strip()}'")
    else:
        print("No specifications section found")
    
    print("\n" + "-"*30)
    
    # Test features section
    feature_section_start = re.search(r'(?i)features?\s*[:\-]?\s*$', content, re.MULTILINE)
    if feature_section_start:
        print("Found features section at position:", feature_section_start.start(), "to", feature_section_start.end())
        print("Match:", repr(feature_section_start.group()))
        
        # Extract lines after "Features:" until next section or empty line
        lines = content[feature_section_start.end():].split('\n')
        print("Lines after features:")
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"  {i}: '{line}'")
            if not line or line.lower().startswith(('description', 'specifications')):
                print(f"    -> Breaking at line {i}")
                break
            # Remove bullet point markers
            clean_line = re.sub(r'^\s*[-•]\s*', '', line)
            print(f"    -> Clean: '{clean_line}'")
    else:
        print("No features section found")

if __name__ == "__main__":
    debug_sections()