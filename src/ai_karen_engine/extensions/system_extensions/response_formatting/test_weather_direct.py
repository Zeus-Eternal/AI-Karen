#!/usr/bin/env python3
"""
Direct test of weather formatter functionality.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from formatters.weather_formatter import WeatherResponseFormatter
from base import ResponseContext, ContentType
from unittest.mock import Mock


def test_weather_formatter_direct():
    """Test weather formatter directly."""
    print("🌤️ Testing Weather Formatter Directly")
    print("=" * 50)
    
    # Create formatter
    formatter = WeatherResponseFormatter()
    
    # Create mock context
    mock_context = Mock(spec=ResponseContext)
    mock_context.detected_content_type = None
    mock_context.user_preferences = {}
    mock_context.theme_context = {'current_theme': 'light'}
    mock_context.session_data = {}
    
    # Test weather content
    weather_contents = [
        "The weather in New York is 75°F and sunny today with humidity at 60%.",
        "Weather forecast for Chicago: Today 78°F sunny, Tomorrow 72°F partly cloudy.",
        "Current temperature is 22°C with light rain and winds from the northwest.",
        "Severe thunderstorm warning in effect for Miami until 9 PM tonight.",
        "It's sunny and warm today with a high of 85°F.",
        "UV index is 8, which is very high.",
        "Barometric pressure is 30.15 inHg and falling."
    ]
    
    print(f"\n🔍 Testing weather content detection:")
    for i, content in enumerate(weather_contents, 1):
        can_format = formatter.can_format(content, mock_context)
        confidence = formatter.get_confidence_score(content, mock_context)
        print(f"{i}. {'✅' if can_format else '❌'} {confidence:.2f} - {content[:50]}...")
    
    # Test formatting
    print(f"\n🎨 Testing weather formatting:")
    test_content = "Weather in Seattle: 65°F, partly cloudy, humidity 70%, wind 12 mph NW"
    
    if formatter.can_format(test_content, mock_context):
        try:
            result = formatter.format_response(test_content, mock_context)
            print("✅ Formatting successful")
            print(f"📊 Content type: {result.content_type.value}")
            print(f"🏷️ CSS classes: {', '.join(result.css_classes)}")
            print(f"🎯 Theme requirements: {', '.join(result.theme_requirements)}")
            print(f"🖼️ Has images: {result.has_images}")
            print(f"⚡ Interactive: {result.has_interactive_elements}")
            
            # Check for key elements in HTML
            key_elements = ['weather-card', 'Seattle', '65°F', 'Partly Cloudy', '70%', 'NW']
            found = [elem for elem in key_elements if elem in result.content]
            print(f"🔍 Key elements found: {len(found)}/{len(key_elements)} - {found}")
            
        except Exception as e:
            print(f"❌ Formatting failed: {e}")
    else:
        print("❌ Cannot format test content")
    
    # Test non-weather content
    print(f"\n🚫 Testing non-weather content:")
    non_weather_contents = [
        "This is a great movie about adventure.",
        "Here's a recipe for chocolate cake.",
        "Breaking news: Stock market reaches new high.",
        "This product costs $50 and has great reviews."
    ]
    
    for content in non_weather_contents:
        can_format = formatter.can_format(content, mock_context)
        print(f"{'❌' if not can_format else '⚠️'} {content[:40]}...")
    
    print(f"\n🎉 Direct weather formatter test completed!")


if __name__ == "__main__":
    test_weather_formatter_direct()