import json
import os
from typing import Any, Dict, Optional

import httpx


class WeatherClient:
    """Client for fetching weather data from wttr.in or OpenWeatherMap."""

    def __init__(self, service: str = "wttr_in", api_key: Optional[str] = None) -> None:
        self.service = service
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://wttr.in"

    async def get_weather(self, location: str) -> Dict[str, Any]:
        if self.service == "openweather" and self.api_key:
            return await self._get_weather_openweather(location)
        return await self._get_weather_wttr(location)

    async def _get_weather_wttr(self, location: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{location}?format=j1"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()

    async def _get_weather_openweather(self, location: str) -> Dict[str, Any]:
        geo_url = (
            f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.api_key}"
        )
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(geo_url, timeout=10)
            geo_resp.raise_for_status()
            geo = geo_resp.json()
            if not geo:
                raise ValueError(f"Location '{location}' not found")
            lat = geo[0]["lat"]
            lon = geo[0]["lon"]

            weather_url = (
                f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
            )
            w_resp = await client.get(weather_url, timeout=10)
            w_resp.raise_for_status()
            return w_resp.json()

