"""
Weather Response Formatter - Production Grade
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..Base import SpecializedFormatter, ResponseContext
from ...Models import FormattedResponse
from ...Enums import ContentType, FormatType

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
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
    day: str
    high_temp: Optional[str] = None
    low_temp: Optional[str] = None
    condition: Optional[str] = None
    precipitation_chance: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class WeatherAlert:
    type: str
    severity: str
    description: str


@dataclass
class WeatherInfo:
    location: str
    current: Optional[WeatherCondition] = None
    forecast: Optional[List[WeatherForecast]] = None
    alerts: Optional[List[WeatherAlert]] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None

    def __post_init__(self):
        self.forecast = self.forecast or []
        self.alerts = self.alerts or []


class WeatherResponseFormatter(SpecializedFormatter):
    def __init__(self):
        super().__init__("weather", "2.0.0")

        self._condition_icons = {
            "sunny": "☀️",
            "clear": "☀️",
            "partly cloudy": "⛅",
            "cloudy": "☁️",
            "rain": "🌧️",
            "snow": "❄️",
            "thunderstorm": "⛈️",
            "fog": "🌫️",
            "windy": "💨",
            "hot": "🔥",
            "cold": "🥶",
        }

        self._alert_icons = {
            "minor": "⚠️",
            "moderate": "🟡",
            "severe": "🟠",
            "extreme": "🔴",
        }

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.WEATHER:
            return True

        keywords = ["weather", "temperature", "forecast", "humidity", "wind"]
        return sum(k in content.lower() for k in keywords) >= 2

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        info = self._extract_weather_info(content)

        if info.location == "Unknown Location" and not info.current:
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        html = self._generate_weather_card_html(info)

        return FormattedResponse(
            content=f"{html}\n\n{content}",
            format_type=FormatType.SEARCH_ANSWER,
            metadata={"formatter": self.name, "location": info.location},
            preferred_renderer="html",
        )

    def _extract_weather_info(self, content: str) -> WeatherInfo:
        info = WeatherInfo(location=self._extract_location(content))

        current = WeatherCondition(condition="Unknown")

        current.temperature = self._extract(r"(-?\d+)\s*(?:°|degrees)", content)
        current.feels_like = self._extract(r"feels like\s*(-?\d+)", content)
        current.humidity = self._extract(r"humidity\s*[:\-]?\s*(\d+)%", content)
        current.wind_speed = self._extract(r"wind.*?(\d+)\s*(?:mph|km/h)", content)
        current.pressure = self._extract(r"pressure\s*[:\-]?\s*(\d+)", content)
        current.uv_index = self._extract(r"uv\s*index\s*[:\-]?\s*(\d+)", content)
        current.visibility = self._extract(r"visibility\s*[:\-]?\s*(\d+)", content)

        for cond, icon in self._condition_icons.items():
            if cond in content.lower():
                current.condition = cond.title()
                current.icon = icon
                break

        if any(
            [
                current.temperature,
                current.humidity,
                current.wind_speed,
                current.condition != "Unknown",
            ]
        ):
            info.current = current

        info.sunrise = self._extract(
            r"sunrise\s*[:\-]?\s*([\d:]+\s*[APMapm]*)", content
        )
        info.sunset = self._extract(r"sunset\s*[:\-]?\s*([\d:]+\s*[APMapm]*)", content)

        info.forecast = self._extract_forecast(content)
        info.alerts = self._extract_alerts(content)

        return info

    def _extract_forecast(self, content: str) -> List[WeatherForecast]:
        forecasts = []
        matches = re.findall(
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).*?(\d+).*(\d+)",
            content,
            re.IGNORECASE,
        )

        for m in matches:
            forecasts.append(WeatherForecast(day=m[0], high_temp=m[1], low_temp=m[2]))

        return forecasts

    def _extract_alerts(self, content: str) -> List[WeatherAlert]:
        alerts = []
        matches = re.findall(
            r"(warning|alert|advisory).*?(severe|moderate|minor).*?([^.]+)",
            content,
            re.IGNORECASE,
        )

        for m in matches:
            alerts.append(WeatherAlert(type=m[0], severity=m[1], description=m[2]))

        return alerts

    def _extract_location(self, content: str) -> str:
        match = re.search(r"(?:in|for)\s+([A-Z][a-zA-Z\s,]+)", content)
        return match.group(1).strip() if match else "Unknown Location"

    def _extract(self, pattern: str, content: str) -> Optional[str]:
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1) if match else None

    def _generate_weather_card_html(self, info: WeatherInfo) -> str:
        html = f'<div class="weather-card p-4 rounded-xl border bg-card shadow-sm">'
        html += f'<h2 class="text-xl font-bold mb-2">🌍 {info.location}</h2>'

        if info.current:
            html += f'<div class="mb-3">'
            if info.current.icon:
                html += f'<span class="text-4xl">{info.current.icon}</span>'
            html += f'<div class="text-3xl font-bold">{info.current.temperature or "--"}°</div>'
            html += f"<div>{info.current.condition}</div>"
            html += "</div>"

            html += '<div class="grid grid-cols-2 gap-2 text-sm">'
            for label, value in {
                "Humidity": info.current.humidity,
                "Wind": info.current.wind_speed,
                "UV": info.current.uv_index,
                "Pressure": info.current.pressure,
            }.items():
                if value:
                    html += f"<div>{label}: {value}</div>"
            html += "</div>"

        if info.forecast:
            html += '<div class="mt-4"><h3 class="font-semibold">Forecast</h3>'
            for f in info.forecast:
                html += f"<div>{f.day}: {f.high_temp}° / {f.low_temp}°</div>"
            html += "</div>"

        if info.alerts:
            html += (
                '<div class="mt-4"><h3 class="font-semibold text-red-500">Alerts</h3>'
            )
            for a in info.alerts:
                html += f"<div>{a.severity.upper()}: {a.description}</div>"
            html += "</div>"

        html += "</div>"
        return html
