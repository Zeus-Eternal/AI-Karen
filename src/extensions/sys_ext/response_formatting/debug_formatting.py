#!/usr/bin/env python3
"""
Debug response formatting output.
"""

import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def debug_formatting():
    """Debug response formatting."""
    from integration import get_response_formatting_integration
    
    integration = get_response_formatting_integration()
    
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
    
    formatted_response = await integration.format_response(
        user_query=user_query,
        response_content=response_content,
        user_preferences={'theme': 'light'},
        theme_context={'current_theme': 'light'},
        session_data={}
    )
    
    print("Content type:", formatted_response.content_type)
    print("Metadata:", formatted_response.metadata)
    print("\nFormatted content:")
    print(formatted_response.content)

if __name__ == "__main__":
    asyncio.run(debug_formatting())