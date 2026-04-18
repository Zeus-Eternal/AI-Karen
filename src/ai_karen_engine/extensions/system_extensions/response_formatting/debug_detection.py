#!/usr/bin/env python3
"""
Debug content detection for product content.
"""

import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def debug_detection():
    """Debug product content detection."""
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
    
    print("Query:", user_query)
    print("Content:", response_content)
    print("\n" + "="*50)
    
    result = await detector.detect_content_type(user_query, response_content)
    
    print(f"Detected type: {result.content_type}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Keywords: {result.keywords}")
    print(f"Entities: {result.detected_entities}")

if __name__ == "__main__":
    asyncio.run(debug_detection())