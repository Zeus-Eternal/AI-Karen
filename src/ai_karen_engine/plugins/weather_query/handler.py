"""Weather plugin handler using a client for network calls."""

from __future__ import annotations

import json
import os
from typing import Optional

from ai_karen_engine.plugins.weather_query.client import WeatherClient


async def run(params: dict) -> dict:
    """Return a simple weather summary and widget reference for the given location."""
    location: Optional[str] = params.get("location")
    if not location:
        return {"error": "I need a location to check the weather."}

    service = os.getenv("WEATHER_SERVICE", "wttr_in")
    client = WeatherClient(service=service)
    try:
        data = await client.get_weather(location)
    except Exception as exc:  # pragma: no cover - network fail safe
        return {"error": f"Sorry, I couldn't fetch the weather for {location}: {exc}"}

    try:
        if service == "openweather":
            desc = data["weather"][0]["description"].capitalize()
            temp_c = data["main"]["temp"]
            feels_c = data["main"].get("feels_like", temp_c)
            humidity = data["main"].get("humidity")
            wind = data.get("wind", {}).get("speed")
        else:
            current = data["current_condition"][0]
            desc = current["weatherDesc"][0]["value"]
            temp_c = float(current["temp_C"])
            feels_c = float(current["FeelsLikeC"])
            humidity = current.get("humidity")
            wind = current.get("windspeedKmph")
    except Exception as exc:  # pragma: no cover - data structure safety
        return {"error": f"Weather data parsing failed: {exc}"}

    summary = f"Currently in {location}: {desc}. The temperature is {temp_c}°C (feels like {feels_c}°C)."
    if humidity:
        summary += f" Humidity is {humidity}%."
    if wind:
        summary += f" Wind speed {wind} km/h."

    ref_id = f"{location.lower().replace(' ', '_')}_forecast"
    return {"summary": summary, "ref_id": ref_id}
