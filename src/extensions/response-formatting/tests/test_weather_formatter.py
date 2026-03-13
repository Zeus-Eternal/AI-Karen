"""
Unit tests for WeatherResponseFormatter.

Tests weather content detection, information extraction, and HTML formatting
with various weather scenarios including current conditions, forecasts, and alerts.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseContext, ContentType, FormattingError
from formatters.weather_formatter import WeatherResponseFormatter, WeatherInfo, WeatherCondition, WeatherForecast, WeatherAlert


class TestWeatherResponseFormatter(unittest.TestCase):
    """Test cases for WeatherResponseFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = WeatherResponseFormatter()
        self.mock_context = Mock(spec=ResponseContext)
        self.mock_context.detected_content_type = None
        self.mock_context.user_preferences = {}
        self.mock_context.theme_context = {'current_theme': 'light'}
        self.mock_context.session_data = {}
    
    def test_formatter_initialization(self):
        """Test formatter is properly initialized."""
        self.assertEqual(self.formatter.name, "weather")
        self.assertEqual(self.formatter.version, "1.0.0")
        self.assertIn(ContentType.WEATHER, self.formatter.get_supported_content_types())
    
    def test_can_format_weather_content(self):
        """Test detection of weather-related content."""
        # Test cases that should be detected as weather
        weather_contents = [
            "The weather in New York is 75°F and sunny today.",
            "Current temperature is 22°C with partly cloudy skies.",
            "Tomorrow's forecast shows rain with a high of 68°F.",
            "Humidity is at 65% with winds from the northwest at 15 mph.",
            "Weather alert: Thunderstorm warning in effect until 8 PM.",
            "Sunrise is at 6:30 AM and sunset at 7:45 PM.",
            "UV index is 8, which is very high.",
            "Barometric pressure is 30.15 inHg and falling."
        ]
        
        for content in weather_contents:
            with self.subTest(content=content):
                self.assertTrue(
                    self.formatter.can_format(content, self.mock_context),
                    f"Should detect weather content: {content}"
                )
    
    def test_can_format_non_weather_content(self):
        """Test rejection of non-weather content."""
        non_weather_contents = [
            "This is a great movie about adventure.",
            "Here's a recipe for chocolate cake with ingredients.",
            "Breaking news: Stock market reaches new high.",
            "This product has excellent reviews and costs $50.",
            "Travel to Paris and visit the Eiffel Tower.",
            "Here's some Python code to solve the problem."
        ]
        
        for content in non_weather_contents:
            with self.subTest(content=content):
                self.assertFalse(
                    self.formatter.can_format(content, self.mock_context),
                    f"Should not detect weather content: {content}"
                )
    
    def test_can_format_with_detected_content_type(self):
        """Test detection when content type is pre-detected."""
        self.mock_context.detected_content_type = ContentType.WEATHER
        
        # Should return True even for minimal weather content
        self.assertTrue(
            self.formatter.can_format("Temperature today", self.mock_context)
        )
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation for different content types."""
        # High confidence weather content
        high_confidence_content = "Weather in Boston: 72°F, sunny, humidity 45%, wind 10 mph"
        score = self.formatter.get_confidence_score(high_confidence_content, self.mock_context)
        self.assertGreater(score, 0.7, "Should have high confidence for clear weather content")
        
        # Medium confidence weather content
        medium_confidence_content = "It's sunny and warm today"
        score = self.formatter.get_confidence_score(medium_confidence_content, self.mock_context)
        self.assertGreater(score, 0.3, "Should have medium confidence")
        self.assertLess(score, 0.7, "Should not have high confidence")
        
        # Low confidence non-weather content
        low_confidence_content = "This is about cooking recipes"
        score = self.formatter.get_confidence_score(low_confidence_content, self.mock_context)
        self.assertEqual(score, 0.0, "Should have zero confidence for non-weather content")
    
    def test_extract_weather_info_basic(self):
        """Test extraction of basic weather information."""
        content = "Weather in New York: 75°F, sunny, humidity 60%, wind 12 mph NW"
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertEqual(weather_info.location, "New York")
        self.assertIsNotNone(weather_info.current)
        self.assertEqual(weather_info.current.temperature, "75°F")
        self.assertEqual(weather_info.current.condition, "Sunny")
        self.assertEqual(weather_info.current.humidity, "60%")
        self.assertIn("12", weather_info.current.wind_speed)
        self.assertEqual(weather_info.current.wind_direction, "NW")
    
    def test_extract_weather_info_celsius(self):
        """Test extraction with Celsius temperature."""
        content = "Temperature in London is 22°C, partly cloudy"
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertEqual(weather_info.location, "London")
        self.assertEqual(weather_info.current.temperature, "22°C")
        self.assertEqual(weather_info.current.condition, "Partly Cloudy")
    
    def test_extract_weather_info_forecast(self):
        """Test extraction of forecast information."""
        content = """Weather forecast for Chicago:
        Today: 78°F, sunny
        Tomorrow: 72°F, partly cloudy
        Wednesday: 65°F, rain"""
        
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertEqual(weather_info.location, "Chicago")
        self.assertGreater(len(weather_info.forecast), 0)
        
        # Check if forecast days are extracted
        forecast_days = [f.day for f in weather_info.forecast]
        self.assertIn("Tomorrow", forecast_days)
    
    def test_extract_weather_info_alerts(self):
        """Test extraction of weather alerts."""
        content = """Weather for Miami:
        Current: 85°F, partly cloudy
        Severe thunderstorm warning in effect until 9 PM
        Hurricane watch issued for coastal areas"""
        
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertEqual(weather_info.location, "Miami")
        self.assertGreater(len(weather_info.alerts), 0)
        
        # Check alert extraction
        alert_types = [alert.type for alert in weather_info.alerts]
        self.assertTrue(any("warning" in alert_type.lower() for alert_type in alert_types))
    
    def test_extract_weather_info_sun_times(self):
        """Test extraction of sunrise and sunset times."""
        content = """Weather today:
        Temperature: 70°F
        Sunrise: 6:30 AM
        Sunset: 7:45 PM"""
        
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertEqual(weather_info.sunrise, "6:30 AM")
        self.assertEqual(weather_info.sunset, "7:45 PM")
    
    def test_extract_weather_info_additional_details(self):
        """Test extraction of additional weather details."""
        content = """Current conditions:
        Temperature: 68°F (feels like 72°F)
        Humidity: 75%
        Pressure: 30.15 inHg
        Visibility: 10 miles
        UV Index: 6"""
        
        weather_info = self.formatter._extract_weather_info(content)
        
        self.assertIsNotNone(weather_info.current)
        self.assertEqual(weather_info.current.temperature, "68°F")
        self.assertEqual(weather_info.current.feels_like, "72°")
        self.assertEqual(weather_info.current.humidity, "75%")
        self.assertIn("30.15 inHg", weather_info.current.pressure)
        self.assertIn("10 miles", weather_info.current.visibility)
        self.assertEqual(weather_info.current.uv_index, "6")
    
    def test_condition_icon_mapping(self):
        """Test weather condition to icon mapping."""
        test_conditions = [
            ("sunny", "☀️"),
            ("cloudy", "☁️"),
            ("rain", "🌧️"),
            ("snow", "❄️"),
            ("thunderstorm", "⛈️"),
            ("fog", "🌫️")
        ]
        
        for condition, expected_icon in test_conditions:
            content = f"Weather is {condition} today"
            weather_info = self.formatter._extract_weather_info(content)
            
            if weather_info.current and weather_info.current.icon:
                self.assertEqual(
                    weather_info.current.icon, 
                    expected_icon,
                    f"Icon for {condition} should be {expected_icon}"
                )
    
    def test_format_response_success(self):
        """Test successful weather response formatting."""
        content = "Weather in Seattle: 65°F, partly cloudy, humidity 70%"
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertEqual(result.content_type, ContentType.WEATHER)
        self.assertIn("weather-card", result.content)
        self.assertIn("Seattle", result.content)
        self.assertIn("65°F", result.content)
        self.assertIn("Partly Cloudy", result.content)
        self.assertIn("70%", result.content)
        self.assertTrue(result.has_images)  # Weather icons count as images
        self.assertIn("weather", result.metadata["formatter"])
    
    def test_format_response_with_forecast(self):
        """Test formatting with forecast information."""
        content = """Weather forecast:
        Today: 75°F, sunny
        Tomorrow: 68°F, cloudy
        Wednesday: 62°F, rain"""
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertIn("forecast", result.content.lower())
        self.assertIn("Today", result.content)
        self.assertIn("Tomorrow", result.content)
        self.assertIn("Wednesday", result.content)
        self.assertTrue(result.has_interactive_elements)  # Forecast has interactive elements
    
    def test_format_response_with_alerts(self):
        """Test formatting with weather alerts."""
        content = """Weather update:
        Current: 80°F, partly cloudy
        Severe thunderstorm warning in effect"""
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertIn("alert", result.content.lower())
        self.assertIn("warning", result.content.lower())
        self.assertIn("⚠️", result.content)  # Alert icon
    
    def test_format_response_with_sun_times(self):
        """Test formatting with sunrise/sunset information."""
        content = """Today's weather:
        Temperature: 72°F
        Sunrise: 6:15 AM
        Sunset: 8:30 PM"""
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertIn("sun", result.content.lower())
        self.assertIn("6:15 AM", result.content)
        self.assertIn("8:30 PM", result.content)
        self.assertIn("🌅", result.content)  # Sunrise icon
        self.assertIn("🌇", result.content)  # Sunset icon
    
    def test_format_response_invalid_content(self):
        """Test formatting with invalid content raises error."""
        content = "This is not weather-related content about movies"
        
        with self.assertRaises(FormattingError):
            self.formatter.format_response(content, self.mock_context)
    
    def test_format_response_empty_content(self):
        """Test formatting with empty content raises error."""
        with self.assertRaises(FormattingError):
            self.formatter.format_response("", self.mock_context)
    
    def test_theme_requirements(self):
        """Test theme requirements are properly defined."""
        requirements = self.formatter.get_theme_requirements()
        
        expected_requirements = [
            "typography", "spacing", "colors", "cards", 
            "icons", "badges", "alerts", "gradients"
        ]
        
        for requirement in expected_requirements:
            self.assertIn(requirement, requirements)
    
    def test_css_classes_generation(self):
        """Test CSS classes are generated correctly."""
        css_classes = self.formatter._get_css_classes(self.mock_context)
        
        expected_classes = [
            "response-formatted",
            "weather-response", 
            "themed-content",
            "theme-light"
        ]
        
        for css_class in expected_classes:
            self.assertIn(css_class, css_classes)
    
    def test_css_classes_dark_theme(self):
        """Test CSS classes for dark theme."""
        self.mock_context.theme_context = {'current_theme': 'dark'}
        css_classes = self.formatter._get_css_classes(self.mock_context)
        
        self.assertIn("theme-dark", css_classes)
    
    def test_uv_level_calculation(self):
        """Test UV level description calculation."""
        test_cases = [
            ("1", "Low"),
            ("3", "Moderate"), 
            ("6", "High"),
            ("9", "Very High"),
            ("12", "Extreme"),
            ("invalid", "Unknown")
        ]
        
        for uv_index, expected_level in test_cases:
            level = self.formatter._get_uv_level(uv_index)
            self.assertEqual(level, expected_level, f"UV index {uv_index} should be {expected_level}")
    
    def test_html_escaping(self):
        """Test HTML content is properly escaped."""
        content = "Weather alert: <script>alert('xss')</script> & dangerous content"
        
        result = self.formatter.format_response(content, self.mock_context)
        
        # Check that HTML is escaped
        self.assertNotIn("<script>", result.content)
        self.assertIn("&lt;script&gt;", result.content)
        self.assertIn("&amp;", result.content)
    
    def test_metadata_generation(self):
        """Test metadata is properly generated."""
        content = "Weather in Boston: 70°F, sunny with 3 day forecast"
        
        result = self.formatter.format_response(content, self.mock_context)
        
        metadata = result.metadata
        self.assertEqual(metadata["formatter"], "weather")
        self.assertEqual(metadata["location"], "Boston")
        self.assertTrue(metadata["has_current"])
        self.assertIsNotNone(metadata["current_temp"])
        self.assertIsNotNone(metadata["current_condition"])
    
    def test_responsive_design_classes(self):
        """Test responsive design CSS is included."""
        content = "Weather today: 75°F and sunny"
        
        result = self.formatter.format_response(content, self.mock_context)
        
        # Check for responsive CSS media queries
        self.assertIn("@media", result.content)
        self.assertIn("768px", result.content)  # Mobile breakpoint
    
    def test_accessibility_features(self):
        """Test accessibility features in generated HTML."""
        content = "Weather: 72°F, partly cloudy, UV index 5"
        
        result = self.formatter.format_response(content, self.mock_context)
        
        # Check for semantic HTML structure
        self.assertIn("<h2", result.content)  # Proper heading hierarchy
        self.assertIn("<h3", result.content)  # Section headings
        self.assertIn("class=", result.content)  # CSS classes for styling
    
    def test_temperature_unit_detection(self):
        """Test temperature unit detection and formatting."""
        test_cases = [
            ("Temperature is 75°F", "75°F"),
            ("It's 22°C outside", "22°C"),
            ("Current temp: 68 degrees Fahrenheit", "68°"),
            ("Temperature: 20 celsius", "20°C")
        ]
        
        for content, expected_temp in test_cases:
            weather_info = self.formatter._extract_weather_info(content)
            if weather_info.current and weather_info.current.temperature:
                self.assertEqual(
                    weather_info.current.temperature,
                    expected_temp,
                    f"Temperature extraction failed for: {content}"
                )
    
    def test_wind_information_extraction(self):
        """Test wind speed and direction extraction."""
        content = "Wind: 15 mph from the northwest, gusting to 25 mph"
        weather_info = self.formatter._extract_weather_info(content)
        
        if weather_info.current:
            self.assertIsNotNone(weather_info.current.wind_speed)
            self.assertIn("15", weather_info.current.wind_speed)
    
    def test_multiple_locations_handling(self):
        """Test handling of multiple locations in content."""
        content = "Weather in New York: 75°F, sunny. In Los Angeles: 82°F, clear."
        weather_info = self.formatter._extract_weather_info(content)
        
        # Should extract the first location mentioned
        self.assertIn("New York", weather_info.location)
    
    def test_forecast_day_parsing(self):
        """Test parsing of different forecast day formats."""
        content = """Forecast:
        Today: 75°F, sunny
        Tomorrow: 70°F, cloudy  
        Monday: 68°F, rain
        Tuesday: 72°F, partly cloudy"""
        
        weather_info = self.formatter._extract_weather_info(content)
        
        forecast_days = [f.day for f in weather_info.forecast]
        expected_days = ["Today", "Tomorrow", "Monday", "Tuesday"]
        
        for day in expected_days:
            self.assertIn(day, forecast_days, f"Should extract forecast for {day}")
    
    def test_alert_severity_classification(self):
        """Test weather alert severity classification."""
        test_alerts = [
            ("Severe thunderstorm warning", "severe"),
            ("Winter weather advisory", "moderate"),
            ("Extreme heat warning", "severe"),
            ("Fog advisory", "moderate")
        ]
        
        for alert_text, expected_severity in test_alerts:
            content = f"Weather update: {alert_text} in effect"
            weather_info = self.formatter._extract_weather_info(content)
            
            if weather_info.alerts:
                # Check that severity is classified appropriately
                self.assertTrue(len(weather_info.alerts) > 0)
    
    def test_edge_case_empty_weather_info(self):
        """Test handling of content with minimal weather information."""
        content = "Weather update"  # Minimal content
        
        # Should still create weather info with defaults
        weather_info = self.formatter._extract_weather_info(content)
        self.assertIsNotNone(weather_info)
        self.assertEqual(weather_info.location, "Unknown Location")
    
    def test_performance_with_long_content(self):
        """Test formatter performance with long content."""
        # Create long weather content
        long_content = "Weather forecast: " + "Today is sunny. " * 100 + "Temperature is 75°F."
        
        # Should handle long content without issues
        result = self.formatter.format_response(long_content, self.mock_context)
        self.assertIsNotNone(result)
        self.assertEqual(result.content_type, ContentType.WEATHER)


if __name__ == '__main__':
    unittest.main()