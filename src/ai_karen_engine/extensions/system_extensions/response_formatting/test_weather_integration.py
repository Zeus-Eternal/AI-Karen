#!/usr/bin/env python3
"""
Simple integration test for weather formatter.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from integration import get_response_formatting_integration
from base import ContentType


async def test_weather_integration():
    """Test weather formatter integration."""
    print("🌤️ Testing Weather Formatter Integration")
    print("=" * 50)
    
    # Get integration instance
    integration = get_response_formatting_integration()
    
    # Test weather content
    weather_queries = [
        ("What's the weather like?", "The weather in New York is 75°F and sunny today with humidity at 60%."),
        ("Weather forecast", "Weather forecast for Chicago: Today 78°F sunny, Tomorrow 72°F partly cloudy."),
        ("Temperature today", "Current temperature is 22°C with light rain and winds from the northwest."),
        ("Weather alert", "Severe thunderstorm warning in effect for Miami until 9 PM tonight.")
    ]
    
    for query, response in weather_queries:
        print(f"\n🔍 Testing: {query}")
        print(f"📝 Response: {response[:60]}...")
        
        try:
            # Format the response
            result = await integration.format_response(
                user_query=query,
                response_content=response,
                theme_context={'current_theme': 'light'}
            )
            
            # Check results
            if result.content_type == ContentType.WEATHER:
                print("✅ Correctly detected as weather content")
                print(f"📊 Confidence: {result.metadata.get('content_detection', {}).get('confidence', 0):.2f}")
                print(f"🎨 Formatter: {result.metadata.get('formatter', 'unknown')}")
                
                # Check for weather-specific elements
                weather_elements = ['weather-card', 'current-temp', 'weather-icon', '°']
                found_elements = [elem for elem in weather_elements if elem in result.content]
                print(f"🏷️ Weather elements found: {len(found_elements)}/{len(weather_elements)}")
                
                if result.has_images:
                    print("🖼️ Contains weather icons")
                
            else:
                print(f"⚠️ Detected as: {result.content_type.value}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test non-weather content (should not be detected as weather)
    print(f"\n🚫 Testing non-weather content")
    non_weather_query = "Tell me about movies"
    non_weather_response = "Here are some great movies to watch this weekend."
    
    try:
        result = await integration.format_response(
            user_query=non_weather_query,
            response_content=non_weather_response,
            theme_context={'current_theme': 'light'}
        )
        
        if result.content_type != ContentType.WEATHER:
            print("✅ Correctly rejected non-weather content")
        else:
            print("❌ Incorrectly detected non-weather as weather")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Get integration stats
    print(f"\n📈 Integration Statistics")
    stats = integration.get_integration_metrics()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Successful formats: {stats['successful_formats']}")
    print(f"Failed formats: {stats['failed_formats']}")
    
    # List available formatters
    formatters = integration.get_available_formatters()
    weather_formatters = [f for f in formatters if 'weather' in f['name'].lower()]
    print(f"\n🔧 Weather formatters available: {len(weather_formatters)}")
    for formatter in weather_formatters:
        print(f"  - {formatter['name']} v{formatter['version']}")
    
    print(f"\n🎉 Weather formatter integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_weather_integration())