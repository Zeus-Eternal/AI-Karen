"""
Weather Response Formatter Plugin

This formatter provides intelligent formatting for weather-related responses,
including current conditions, extended forecasts, and weather alerts with icons.
Integrates with the existing theme manager for consistent styling.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    """Data structure for weather condition information."""
    condition: str
    temperature: Optional[str] = None
    feels_like: Optional[str] = None
    humidity: Optional[str] = None
    wind_speed: Optional[str] = None
    wind_direction: Optional[str] = None
    pressure: Optional[str] = None
    visibility: Optional[str] = None
    uv_index: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class WeatherForecast:
    """Data structure for weather forecast information."""
    day: str
    high_temp: Optional[str] = None
    low_temp: Optional[str] = None
    condition: Optional[str] = None
    precipitation_chance: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class WeatherAlert:
    """Data structure for weather alert information."""
    type: str
    severity: str
    description: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class WeatherInfo:
    """Data structure for complete weather information."""
    location: str
    current: Optional[WeatherCondition] = None
    forecast: List[WeatherForecast] = None
    alerts: List[WeatherAlert] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    last_updated: Optional[str] = None
    
    def __post_init__(self):
        if self.forecast is None:
            self.forecast = []
        if self.alerts is None:
            self.alerts = []


class WeatherResponseFormatter(ResponseFormatter):
    """
    Formatter for weather-related responses.
    
    This formatter detects weather information in responses and formats them
    as attractive weather cards with current conditions, forecasts, and alerts.
    """
    
    def __init__(self):
        super().__init__("weather", "1.0.0")
        
        # Weather detection patterns
        self._weather_patterns = [
            r'(?i)\b(?:weather|forecast|temperature)\s*(?:in|for|at)?\s*([^,\n]+)',
            r'(?i)(?:current|today\'?s?)\s*(?:weather|temperature|conditions?)',
            r'(?i)\b(\d+)\s*(?:degrees?|°[CF]?)\b',
            r'(?i)(?:humidity|pressure|wind)\s*[:\-]?\s*([\d.]+)',
            r'(?i)(?:rain|snow|sunny|cloudy|overcast|clear|partly cloudy|thunderstorm)',
            r'(?i)(?:high|low|max|min)\s*(?:temperature|temp)?\s*[:\-]?\s*(\d+)',
            r'(?i)(?:sunrise|sunset)\s*[:\-]?\s*([\d:]+\s*(?:AM|PM)?)',
            r'(?i)(?:wind speed|wind)\s*[:\-]?\s*([\d.]+)\s*(?:mph|km/h|m/s)',
            r'(?i)(?:precipitation|chance of rain)\s*[:\-]?\s*(\d+)%',
            r'(?i)(?:uv index|uv)\s*[:\-]?\s*(\d+)',
        ]
        
        # Weather condition mappings to icons
        self._condition_icons = {
            'sunny': '☀️',
            'clear': '☀️',
            'partly cloudy': '⛅',
            'cloudy': '☁️',
            'overcast': '☁️',
            'rain': '🌧️',
            'light rain': '🌦️',
            'heavy rain': '🌧️',
            'drizzle': '🌦️',
            'snow': '❄️',
            'light snow': '🌨️',
            'heavy snow': '❄️',
            'sleet': '🌨️',
            'thunderstorm': '⛈️',
            'storm': '⛈️',
            'fog': '🌫️',
            'mist': '🌫️',
            'haze': '🌫️',
            'windy': '💨',
            'hot': '🔥',
            'cold': '🥶',
        }
        
        # Alert severity mappings
        self._alert_icons = {
            'minor': '⚠️',
            'moderate': '🟡',
            'severe': '🟠',
            'extreme': '🔴',
            'warning': '⚠️',
            'watch': '👀',
            'advisory': 'ℹ️',
        }
  
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle weather-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be weather-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as weather
        if context.detected_content_type == ContentType.WEATHER:
            return True
        
        # Look for weather-related keywords and patterns
        content_lower = content.lower()
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny', 'cloudy',
            'wind', 'humidity', 'pressure', 'storm', 'thunder', 'lightning', 'tornado',
            'hurricane', 'celsius', 'fahrenheit', 'degrees', 'hot', 'cold', 'warm', 'cool',
            'precipitation', 'visibility', 'uv index', 'sunrise', 'sunset', 'overcast',
            'partly cloudy', 'clear', 'drizzle', 'thunderstorm', 'fog', 'mist', 'haze'
        ]
        
        keyword_count = sum(1 for keyword in weather_keywords if keyword in content_lower)
        
        # Check for weather-specific patterns
        pattern_matches = sum(1 for pattern in self._weather_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        
        # Check for temperature patterns (strong indicator)
        temp_patterns = [
            r'\b\d+\s*(?:degrees?|°[CF]?)\b',
            r'\b(?:high|low|max|min)\s*(?:temperature|temp)?\s*[:\-]?\s*\d+',
            r'\b\d+\s*(?:celsius|fahrenheit|°C|°F)\b'
        ]
        temp_matches = sum(1 for pattern in temp_patterns
                          if re.search(pattern, content, re.IGNORECASE))
        
        # Require at least 2 keywords or 1 pattern match, with temperature being a strong indicator
        if keyword_count >= 3 or pattern_matches >= 2 or temp_matches >= 1:
            return True
        elif keyword_count >= 2 or pattern_matches >= 1:
            # Additional check for non-weather content
            non_weather_keywords = ['movie', 'recipe', 'cooking', 'news', 'product', 'travel', 'code']
            non_weather_count = sum(1 for keyword in non_weather_keywords if keyword in content_lower)
            return non_weather_count == 0
        elif keyword_count >= 1 and any(kw in content_lower for kw in ['uv index', 'pressure', 'barometric']):
            # Special case for specific weather terms
            return True
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format weather-related content as an attractive weather card.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with weather card formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not weather-related", self.name)
            
            # Extract weather information from content
            weather_info = self._extract_weather_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_weather_card_html(weather_info, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.WEATHER,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "location": weather_info.location,
                    "has_current": bool(weather_info.current),
                    "has_forecast": len(weather_info.forecast) > 0,
                    "has_alerts": len(weather_info.alerts) > 0,
                    "current_temp": weather_info.current.temperature if weather_info.current else None,
                    "current_condition": weather_info.current.condition if weather_info.current else None
                },
                css_classes=css_classes,
                has_images=True,  # Weather icons count as images
                has_interactive_elements=len(weather_info.forecast) > 0  # Forecast tabs/toggles
            )
            
        except Exception as e:
            self.logger.error(f"Weather formatting failed: {e}")
            raise FormattingError(f"Failed to format weather content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for weather formatting.
        
        Returns:
            List of required theme components
        """
        return [
            "typography",
            "spacing", 
            "colors",
            "cards",
            "icons",
            "badges",
            "alerts",
            "gradients"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing WEATHER content type
        """
        return [ContentType.WEATHER] 
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for weather content formatting.
        
        Args:
            content: The response content
            context: Additional context information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not self.can_format(content, context):
            return 0.0
        
        score = 0.0
        content_lower = content.lower()
        
        # High confidence indicators
        if context.detected_content_type == ContentType.WEATHER:
            score += 0.4
        
        # Weather-specific patterns
        pattern_matches = sum(1 for pattern in self._weather_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        
        # Temperature patterns (very strong indicator)
        temp_patterns = [
            r'\b\d+\s*(?:degrees?|°[CF]?)\b',
            r'\b\d+\s*(?:celsius|fahrenheit|°C|°F)\b'
        ]
        temp_matches = sum(1 for pattern in temp_patterns
                          if re.search(pattern, content, re.IGNORECASE))
        score += min(temp_matches * 0.2, 0.4)
        
        # Weather keywords
        weather_keywords = ['weather', 'forecast', 'temperature', 'rain', 'sunny', 'cloudy', 'warm', 'hot', 'cold']
        keyword_matches = sum(1 for keyword in weather_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.15, 0.4)
        
        return min(score, 1.0)
    
    def _extract_weather_info(self, content: str) -> WeatherInfo:
        """
        Extract weather information from response content.
        
        Args:
            content: The response content
            
        Returns:
            WeatherInfo object with extracted data
        """
        weather_info = WeatherInfo(location="Unknown Location")
        
        # Extract location
        location_patterns = [
            r'(?i)(?:weather|forecast|temperature)\s+(?:in|for|at)\s+([^,\n\(:]+?)(?:\s*[:\-]|\s*is|\s*:|$)',
            r'(?i)(?:weather\s+forecast\s+for\s+)([A-Z][a-zA-Z\s,]+?)(?:\s*[:\-]|$)',
            r'(?i)(?:forecast\s+for\s+)([A-Z][a-zA-Z\s,]+?)(?:\s*[:\-]|$)',
            r'(?i)(?:in|for|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\s*(?:today|tomorrow|this week|:))',
            r'(?i)^([A-Z][a-zA-Z\s,]+?)\s*(?:weather|forecast)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                location = match.group(1).strip()
                # Clean up common words and punctuation
                location = re.sub(r'\s*(?:weather|forecast|temperature|today|tomorrow|:)\s*$', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\s+(?:is|are)\s+\d+.*$', '', location)  # Remove "is 22°C" type endings
                location = re.sub(r'[:\-]\s*\d+.*$', '', location)  # Remove temperature info
                if len(location) > 2 and not location.lower() in ['temperature', 'weather', 'forecast']:
                    weather_info.location = location
                    break
        
        # Extract current conditions
        current_condition = WeatherCondition(condition="Unknown")
        
        # Extract temperature
        temp_patterns = [
            r'(?i)(?:temperature|temp|currently)\s*[:\-]?\s*(\d+)\s*(?:degrees?|°[CF]?)',
            r'(?i)\b(\d+)\s*(?:degrees?|°[CF]?)\b',
            r'(?i)(?:it\'s|currently)\s*(\d+)\s*(?:degrees?|°[CF]?)',
        ]
        
        for pattern in temp_patterns:
            match = re.search(pattern, content)
            if match:
                temp = match.group(1)
                # Determine unit from context
                if '°F' in match.group(0) or 'fahrenheit' in match.group(0).lower():
                    current_condition.temperature = f"{temp}°F"
                elif '°C' in match.group(0) or 'celsius' in match.group(0).lower():
                    current_condition.temperature = f"{temp}°C"
                else:
                    current_condition.temperature = f"{temp}°"
                break
        
        # Extract feels like temperature
        feels_like_match = re.search(r'(?i)feels like\s*[:\-]?\s*(\d+)\s*(?:degrees?|°[CF]?)', content)
        if feels_like_match:
            feels_temp = feels_like_match.group(1)
            current_condition.feels_like = f"{feels_temp}°"
        
        # Extract weather condition
        condition_patterns = [
            r'(?i)(?:currently|today|it\'s)\s*(?:is\s*)?([a-z\s]+?)(?:\s*(?:with|and|,|\.|$))',
            r'(?i)(sunny|clear|cloudy|overcast|rain|snow|storm|fog|mist|haze|windy|partly cloudy)',
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                condition = match.strip().lower() if isinstance(match, str) else match
                # Handle multi-word conditions
                if 'partly cloudy' in condition or condition == 'partly cloudy':
                    current_condition.condition = "Partly Cloudy"
                    current_condition.icon = self._condition_icons['partly cloudy']
                    break
                elif condition in self._condition_icons:
                    current_condition.condition = condition.title()
                    current_condition.icon = self._condition_icons[condition]
                    break
            if current_condition.condition != "Unknown":
                break
        
        # If no specific condition found, try to infer from keywords
        if current_condition.condition == "Unknown":
            # Check for multi-word conditions first
            if 'partly cloudy' in content.lower():
                current_condition.condition = "Partly Cloudy"
                current_condition.icon = self._condition_icons['partly cloudy']
            else:
                for condition, icon in self._condition_icons.items():
                    if condition in content.lower():
                        current_condition.condition = condition.title()
                        current_condition.icon = icon
                        break
        
        # Extract humidity
        humidity_match = re.search(r'(?i)humidity\s*[:\-]?\s*(\d+)%?', content)
        if humidity_match:
            current_condition.humidity = f"{humidity_match.group(1)}%"
        
        # Extract wind information
        wind_speed_match = re.search(r'(?i)wind\s*(?:speed)?\s*[:\-]?\s*([\d.]+)\s*(?:mph|km/h|m/s)', content)
        if wind_speed_match:
            current_condition.wind_speed = wind_speed_match.group(0)
        
        wind_dir_patterns = [
            r'(?i)wind\s*(?:direction)?\s*[:\-]?\s*(north|south|east|west|ne|nw|se|sw|n|s|e|w)\b',
            r'(?i)\b(north|south|east|west|ne|nw|se|sw|n|s|e|w)\s*(?:wind|winds)',
            r'(?i)(?:from\s+the\s+)?(north|south|east|west|northeast|northwest|southeast|southwest|nw|ne|sw|se)\b'
        ]
        
        for pattern in wind_dir_patterns:
            wind_dir_match = re.search(pattern, content)
            if wind_dir_match:
                direction = wind_dir_match.group(1).upper()
                # Normalize direction names
                direction_map = {
                    'NORTHEAST': 'NE', 'NORTHWEST': 'NW', 
                    'SOUTHEAST': 'SE', 'SOUTHWEST': 'SW',
                    'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W'
                }
                current_condition.wind_direction = direction_map.get(direction, direction)
                break
        
        # Extract pressure
        pressure_match = re.search(r'(?i)(?:pressure|barometric)\s*[:\-]?\s*([\d.]+)\s*(?:mb|hPa|inHg)', content)
        if pressure_match:
            current_condition.pressure = pressure_match.group(0)
        
        # Extract visibility
        visibility_match = re.search(r'(?i)visibility\s*[:\-]?\s*([\d.]+)\s*(?:miles?|km|m)', content)
        if visibility_match:
            current_condition.visibility = visibility_match.group(0)
        
        # Extract UV index
        uv_match = re.search(r'(?i)(?:uv index|uv)\s*[:\-]?\s*(\d+)', content)
        if uv_match:
            current_condition.uv_index = uv_match.group(1)
        
        # Only add current condition if we have meaningful data
        if (current_condition.temperature or 
            current_condition.condition != "Unknown" or 
            current_condition.humidity or 
            current_condition.wind_speed):
            weather_info.current = current_condition
        
        # Extract forecast information
        forecast_patterns = [
            r'(?i)(tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*[:\-]?\s*(?:high|low|temp)?\s*(\d+)(?:°[CF]?)?',
            r'(?i)(today|tonight)\s*[:\-]?\s*(?:high|low|temp)?\s*(\d+)(?:°[CF]?)?',
        ]
        
        for pattern in forecast_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for day, temp in matches:
                forecast = WeatherForecast(day=day.title(), high_temp=f"{temp}°")
                
                # Try to find condition for this day
                day_section = self._extract_day_section(content, day)
                if day_section:
                    for condition, icon in self._condition_icons.items():
                        if condition in day_section.lower():
                            forecast.condition = condition.title()
                            forecast.icon = icon
                            break
                
                weather_info.forecast.append(forecast)
        
        # Extract sunrise/sunset
        sunrise_match = re.search(r'(?i)sunrise\s*[:\-]?\s*([\d:]+\s*(?:AM|PM)?)', content)
        if sunrise_match:
            weather_info.sunrise = sunrise_match.group(1)
        
        sunset_match = re.search(r'(?i)sunset\s*[:\-]?\s*([\d:]+\s*(?:AM|PM)?)', content)
        if sunset_match:
            weather_info.sunset = sunset_match.group(1)
        
        # Extract weather alerts
        alert_patterns = [
            r'(?i)(warning|watch|advisory|alert)\s*[:\-]?\s*([^.]+)',
            r'(?i)(severe|extreme|dangerous)\s*([^.]+)',
        ]
        
        for pattern in alert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for alert_type, description in matches:
                severity = "moderate"
                if any(word in description.lower() for word in ['severe', 'extreme', 'dangerous']):
                    severity = "severe"
                elif any(word in description.lower() for word in ['minor', 'light']):
                    severity = "minor"
                
                alert = WeatherAlert(
                    type=alert_type.title(),
                    severity=severity,
                    description=description.strip()
                )
                weather_info.alerts.append(alert)
        
        return weather_info
    
    def _extract_day_section(self, content: str, day: str) -> Optional[str]:
        """
        Extract the section of content related to a specific day.
        
        Args:
            content: Full content
            day: Day name to extract
            
        Returns:
            Section content or None
        """
        # Find the day mention and extract surrounding context
        day_pattern = rf'(?i){re.escape(day)}\s*[:\-]?[^.]*\.'
        match = re.search(day_pattern, content)
        if match:
            return match.group(0)
        return None
    
    def _generate_weather_card_html(self, weather_info: WeatherInfo, context: ResponseContext) -> str:
        """
        Generate HTML for weather card display.
        
        Args:
            weather_info: Extracted weather information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build weather card HTML
        html_parts = []
        
        # Card container
        html_parts.append('<div class="weather-card response-card">')
        
        # Header with location
        html_parts.append('<div class="weather-header">')
        html_parts.append(f'<h2 class="weather-location">🌍 {self._escape_html(weather_info.location)}</h2>')
        if weather_info.last_updated:
            html_parts.append(f'<span class="last-updated">Updated: {self._escape_html(weather_info.last_updated)}</span>')
        html_parts.append('</div>')
        
        # Current conditions section
        if weather_info.current:
            html_parts.append(self._generate_current_conditions_html(weather_info.current))
        
        # Alerts section
        if weather_info.alerts:
            html_parts.append(self._generate_alerts_html(weather_info.alerts))
        
        # Forecast section
        if weather_info.forecast:
            html_parts.append(self._generate_forecast_html(weather_info.forecast))
        
        # Sun times section
        if weather_info.sunrise or weather_info.sunset:
            html_parts.append('<div class="sun-times">')
            html_parts.append('<h3 class="section-title">🌅 Sun Times</h3>')
            html_parts.append('<div class="sun-times-grid">')
            
            if weather_info.sunrise:
                html_parts.append(f'<div class="sun-time"><span class="sun-icon">🌅</span><span class="time-label">Sunrise</span><span class="time-value">{self._escape_html(weather_info.sunrise)}</span></div>')
            
            if weather_info.sunset:
                html_parts.append(f'<div class="sun-time"><span class="sun-icon">🌇</span><span class="time-label">Sunset</span><span class="time-value">{self._escape_html(weather_info.sunset)}</span></div>')
            
            html_parts.append('</div>')
            html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        html_parts.append('</div>')  # Close weather-card
        
        return '\n'.join(html_parts)
    
    def _generate_current_conditions_html(self, current: WeatherCondition) -> str:
        """
        Generate HTML for current weather conditions.
        
        Args:
            current: Current weather condition data
            
        Returns:
            HTML string for current conditions
        """
        html_parts = []
        
        html_parts.append('<div class="current-conditions">')
        html_parts.append('<h3 class="section-title">🌤️ Current Conditions</h3>')
        
        # Main temperature and condition
        html_parts.append('<div class="current-main">')
        
        if current.icon:
            html_parts.append(f'<div class="weather-icon">{current.icon}</div>')
        
        html_parts.append('<div class="current-info">')
        
        if current.temperature:
            html_parts.append(f'<div class="current-temp">{self._escape_html(current.temperature)}</div>')
        
        if current.condition and current.condition != "Unknown":
            html_parts.append(f'<div class="current-condition">{self._escape_html(current.condition)}</div>')
        
        if current.feels_like:
            html_parts.append(f'<div class="feels-like">Feels like {self._escape_html(current.feels_like)}</div>')
        
        html_parts.append('</div>')  # Close current-info
        html_parts.append('</div>')  # Close current-main
        
        # Additional details
        details = []
        if current.humidity:
            details.append(f'<div class="detail-item"><span class="detail-icon">💧</span><span class="detail-label">Humidity</span><span class="detail-value">{self._escape_html(current.humidity)}</span></div>')
        
        if current.wind_speed:
            wind_text = current.wind_speed
            if current.wind_direction:
                wind_text += f" {current.wind_direction}"
            details.append(f'<div class="detail-item"><span class="detail-icon">💨</span><span class="detail-label">Wind</span><span class="detail-value">{self._escape_html(wind_text)}</span></div>')
        
        if current.pressure:
            details.append(f'<div class="detail-item"><span class="detail-icon">📊</span><span class="detail-label">Pressure</span><span class="detail-value">{self._escape_html(current.pressure)}</span></div>')
        
        if current.visibility:
            details.append(f'<div class="detail-item"><span class="detail-icon">👁️</span><span class="detail-label">Visibility</span><span class="detail-value">{self._escape_html(current.visibility)}</span></div>')
        
        if current.uv_index:
            uv_level = self._get_uv_level(current.uv_index)
            details.append(f'<div class="detail-item"><span class="detail-icon">☀️</span><span class="detail-label">UV Index</span><span class="detail-value">{self._escape_html(current.uv_index)} ({uv_level})</span></div>')
        
        if details:
            html_parts.append('<div class="current-details">')
            html_parts.extend(details)
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close current-conditions
        
        return '\n'.join(html_parts)
    
    def _generate_alerts_html(self, alerts: List[WeatherAlert]) -> str:
        """
        Generate HTML for weather alerts.
        
        Args:
            alerts: List of weather alerts
            
        Returns:
            HTML string for alerts
        """
        html_parts = []
        
        html_parts.append('<div class="weather-alerts">')
        html_parts.append('<h3 class="section-title">⚠️ Weather Alerts</h3>')
        
        for alert in alerts:
            severity_class = f"alert-{alert.severity}"
            icon = self._alert_icons.get(alert.severity.lower(), '⚠️')
            
            html_parts.append(f'<div class="weather-alert {severity_class}">')
            html_parts.append(f'<div class="alert-header">')
            html_parts.append(f'<span class="alert-icon">{icon}</span>')
            html_parts.append(f'<span class="alert-type">{self._escape_html(alert.type)}</span>')
            html_parts.append(f'<span class="alert-severity">{self._escape_html(alert.severity.title())}</span>')
            html_parts.append('</div>')
            
            html_parts.append(f'<div class="alert-description">{self._escape_html(alert.description)}</div>')
            
            if alert.start_time or alert.end_time:
                html_parts.append('<div class="alert-times">')
                if alert.start_time:
                    html_parts.append(f'<span class="alert-time">From: {self._escape_html(alert.start_time)}</span>')
                if alert.end_time:
                    html_parts.append(f'<span class="alert-time">Until: {self._escape_html(alert.end_time)}</span>')
                html_parts.append('</div>')
            
            html_parts.append('</div>')  # Close weather-alert
        
        html_parts.append('</div>')  # Close weather-alerts
        
        return '\n'.join(html_parts)
    
    def _generate_forecast_html(self, forecast: List[WeatherForecast]) -> str:
        """
        Generate HTML for weather forecast.
        
        Args:
            forecast: List of forecast data
            
        Returns:
            HTML string for forecast
        """
        html_parts = []
        
        html_parts.append('<div class="weather-forecast">')
        html_parts.append('<h3 class="section-title">📅 Forecast</h3>')
        html_parts.append('<div class="forecast-grid">')
        
        for day_forecast in forecast:
            html_parts.append('<div class="forecast-day">')
            
            html_parts.append(f'<div class="forecast-day-name">{self._escape_html(day_forecast.day)}</div>')
            
            if day_forecast.icon:
                html_parts.append(f'<div class="forecast-icon">{day_forecast.icon}</div>')
            
            if day_forecast.condition:
                html_parts.append(f'<div class="forecast-condition">{self._escape_html(day_forecast.condition)}</div>')
            
            if day_forecast.high_temp or day_forecast.low_temp:
                html_parts.append('<div class="forecast-temps">')
                if day_forecast.high_temp:
                    html_parts.append(f'<span class="temp-high">{self._escape_html(day_forecast.high_temp)}</span>')
                if day_forecast.low_temp:
                    html_parts.append(f'<span class="temp-low">{self._escape_html(day_forecast.low_temp)}</span>')
                html_parts.append('</div>')
            
            if day_forecast.precipitation_chance:
                html_parts.append(f'<div class="forecast-precip">💧 {self._escape_html(day_forecast.precipitation_chance)}</div>')
            
            html_parts.append('</div>')  # Close forecast-day
        
        html_parts.append('</div>')  # Close forecast-grid
        html_parts.append('</div>')  # Close weather-forecast
        
        return '\n'.join(html_parts)
    
    def _get_uv_level(self, uv_index: str) -> str:
        """
        Get UV level description from UV index.
        
        Args:
            uv_index: UV index value
            
        Returns:
            UV level description
        """
        try:
            uv_value = int(uv_index)
            if uv_value <= 2:
                return "Low"
            elif uv_value <= 5:
                return "Moderate"
            elif uv_value <= 7:
                return "High"
            elif uv_value <= 10:
                return "Very High"
            else:
                return "Extreme"
        except (ValueError, TypeError):
            return "Unknown"
    
    def _get_css_classes(self, context: ResponseContext) -> List[str]:
        """
        Get CSS classes based on theme context.
        
        Args:
            context: Response context
            
        Returns:
            List of CSS classes
        """
        base_classes = [
            "response-formatted",
            "weather-response",
            "themed-content"
        ]
        
        # Add theme-specific classes
        theme_name = context.theme_context.get('current_theme', 'light')
        base_classes.append(f"theme-{theme_name}")
        
        return base_classes
    
    def _generate_theme_styles(self, theme_name: str) -> str:
        """
        Generate theme-specific CSS styles.
        
        Args:
            theme_name: Name of the current theme
            
        Returns:
            CSS style block
        """
        # Import design tokens
        try:
            from ui_logic.themes.design_tokens import COLORS, SPACING, FONTS
            
            colors = COLORS.get(theme_name, COLORS['light'])
            
            css = f"""
            <style>
            .weather-card {{
                background: linear-gradient(135deg, {colors['surface']} 0%, {colors.get('background', '#f8f9fa')} 100%);
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 20px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
                max-width: 800px;
                overflow: hidden;
            }}
            
            .weather-header {{
                text-align: center;
                margin-bottom: {SPACING['lg']};
                padding-bottom: {SPACING['md']};
                border-bottom: 2px solid {colors['accent']};
            }}
            
            .weather-location {{
                color: {colors.get('text', '#333')};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.8em;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: {SPACING['sm']};
            }}
            
            .last-updated {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 0.9em;
                font-style: italic;
            }}
            
            .current-conditions {{
                background: rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                backdrop-filter: blur(10px);
            }}
            
            .section-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['md']} 0;
                font-size: 1.3em;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .current-main {{
                display: flex;
                align-items: center;
                gap: {SPACING['lg']};
                margin-bottom: {SPACING['md']};
            }}
            
            .weather-icon {{
                font-size: 4em;
                text-align: center;
                min-width: 100px;
            }}
            
            .current-info {{
                flex: 1;
            }}
            
            .current-temp {{
                font-size: 3em;
                font-weight: 700;
                color: {colors['accent']};
                line-height: 1;
                margin-bottom: {SPACING['sm']};
            }}
            
            .current-condition {{
                font-size: 1.3em;
                font-weight: 500;
                color: {colors.get('text', '#333')};
                margin-bottom: {SPACING['xs']};
            }}
            
            .feels-like {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 1em;
                font-style: italic;
            }}
            
            .current-details {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: {SPACING['sm']};
                margin-top: {SPACING['md']};
            }}
            
            .detail-item {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
                background: rgba(255,255,255,0.1);
                padding: {SPACING['sm']};
                border-radius: 8px;
            }}
            
            .detail-icon {{
                font-size: 1.2em;
                min-width: 24px;
                text-align: center;
            }}
            
            .detail-label {{
                font-weight: 500;
                color: {colors.get('text_secondary', '#666')};
                min-width: 80px;
            }}
            
            .detail-value {{
                font-weight: 600;
                color: {colors.get('text', '#333')};
                flex: 1;
            }}
            
            .weather-alerts {{
                margin: {SPACING['lg']} 0;
            }}
            
            .weather-alert {{
                border-radius: 12px;
                padding: {SPACING['md']};
                margin: {SPACING['sm']} 0;
                border-left: 4px solid;
            }}
            
            .alert-minor {{
                background: #fff3cd;
                border-color: #ffc107;
                color: #856404;
            }}
            
            .alert-moderate {{
                background: #fff3cd;
                border-color: #fd7e14;
                color: #842029;
            }}
            
            .alert-severe {{
                background: #f8d7da;
                border-color: #dc3545;
                color: #721c24;
            }}
            
            .alert-extreme {{
                background: #f5c2c7;
                border-color: #b02a37;
                color: #2c0b0e;
            }}
            
            .alert-header {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
                margin-bottom: {SPACING['sm']};
                font-weight: 600;
            }}
            
            .alert-icon {{
                font-size: 1.3em;
            }}
            
            .alert-type {{
                flex: 1;
                font-size: 1.1em;
            }}
            
            .alert-severity {{
                background: rgba(0,0,0,0.1);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                text-transform: uppercase;
            }}
            
            .alert-description {{
                line-height: 1.5;
                margin-bottom: {SPACING['sm']};
            }}
            
            .alert-times {{
                display: flex;
                gap: {SPACING['md']};
                font-size: 0.9em;
                font-style: italic;
            }}
            
            .weather-forecast {{
                margin: {SPACING['lg']} 0;
            }}
            
            .forecast-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: {SPACING['md']};
            }}
            
            .forecast-day {{
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: {SPACING['md']};
                text-align: center;
                backdrop-filter: blur(5px);
                transition: transform 0.2s ease;
            }}
            
            .forecast-day:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            .forecast-day-name {{
                font-weight: 600;
                color: {colors['accent']};
                margin-bottom: {SPACING['sm']};
                font-size: 1.1em;
            }}
            
            .forecast-icon {{
                font-size: 2.5em;
                margin: {SPACING['sm']} 0;
            }}
            
            .forecast-condition {{
                color: {colors.get('text', '#333')};
                font-size: 0.9em;
                margin-bottom: {SPACING['sm']};
            }}
            
            .forecast-temps {{
                display: flex;
                justify-content: center;
                gap: {SPACING['sm']};
                margin-bottom: {SPACING['sm']};
            }}
            
            .temp-high {{
                font-weight: 700;
                color: {colors.get('text', '#333')};
            }}
            
            .temp-low {{
                color: {colors.get('text_secondary', '#666')};
            }}
            
            .forecast-precip {{
                font-size: 0.8em;
                color: {colors.get('text_secondary', '#666')};
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }}
            
            .sun-times {{
                background: linear-gradient(45deg, #ffd54f, #ffb74d);
                border-radius: 16px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                color: #333;
            }}
            
            .sun-times .section-title {{
                color: #333;
            }}
            
            .sun-times-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: {SPACING['md']};
            }}
            
            .sun-time {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: {SPACING['xs']};
                background: rgba(255,255,255,0.2);
                padding: {SPACING['md']};
                border-radius: 12px;
            }}
            
            .sun-icon {{
                font-size: 2em;
            }}
            
            .time-label {{
                font-weight: 500;
                font-size: 0.9em;
            }}
            
            .time-value {{
                font-weight: 700;
                font-size: 1.1em;
            }}
            
            .theme-dark .weather-card {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            }}
            
            .theme-dark .current-conditions,
            .theme-dark .forecast-day {{
                background: rgba(255,255,255,0.05);
            }}
            
            .theme-enterprise .weather-card {{
                border-color: {colors.get('border', '#d0d0d0')};
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            }}
            
            @media (max-width: 768px) {{
                .weather-card {{
                    padding: {SPACING['md']};
                    margin: {SPACING['sm']} 0;
                }}
                
                .current-main {{
                    flex-direction: column;
                    text-align: center;
                    gap: {SPACING['md']};
                }}
                
                .current-temp {{
                    font-size: 2.5em;
                }}
                
                .current-details {{
                    grid-template-columns: 1fr;
                }}
                
                .forecast-grid {{
                    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                }}
            }}
            </style>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .weather-card {
                background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
                border: 1px solid #e0e0e0;
                border-radius: 20px;
                padding: 24px;
                margin: 16px 0;
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
                max-width: 800px;
            }
            .weather-location { color: #333; font-size: 1.8em; font-weight: 700; }
            .current-temp { font-size: 3em; font-weight: 700; color: #1e88e5; }
            .weather-icon { font-size: 4em; }
            .section-title { color: #1e88e5; font-weight: 600; }
            .forecast-day { background: rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; }
            
            @media (max-width: 768px) {
                .weather-card {
                    padding: 16px;
                    margin: 8px 0;
                }
                .current-temp {
                    font-size: 2.5em;
                }
            }
            </style>
            """
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        if not text:
            return ""
        
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))