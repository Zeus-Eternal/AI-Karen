#!/usr/bin/env python3
"""
Debug content scoring mechanism.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_scoring():
    """Debug content scoring."""
    from content_detector import ContentTypeDetector
    from base import ContentType
    
    detector = ContentTypeDetector()
    
    user_query = "Show me the best laptops under $1000"
    response_content = """
    Here are some excellent laptops under $1000:
    
    MacBook Air M2 - $999
    Brand: Apple
    Model: MacBook Air 13-inch
    Rating: 4.5/5 stars (1,234 reviews)
    Available at Apple Store
    Specifications: 8GB RAM, 256GB SSD, M2 chip
    Features: Retina display, Touch ID, All-day battery life
    Shipping: Free 2-day delivery
    Warranty: 1-year limited warranty
    """
    
    combined_text = f"{user_query} {response_content}"
    print("Combined text:", combined_text)
    print("\n" + "="*50)
    
    # Test each content type scoring
    for content_type, patterns in detector._content_patterns.items():
        score = detector._calculate_content_score(combined_text, patterns, [], [])
        print(f"{content_type.value}: {score:.3f}")
        
        # Show keyword matches
        text_lower = combined_text.lower()
        keyword_matches = [kw for kw in patterns['keywords'] if kw in text_lower]
        print(f"  Keywords matched: {keyword_matches}")
        
        # Show pattern matches
        import re
        pattern_matches = []
        for pattern in patterns['patterns']:
            if re.search(pattern, combined_text, re.IGNORECASE):
                pattern_matches.append(pattern)
        print(f"  Patterns matched: {len(pattern_matches)}")
        print()

if __name__ == "__main__":
    debug_scoring()