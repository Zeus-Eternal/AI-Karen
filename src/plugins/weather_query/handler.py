"""Weather plugin handler with optional real API integration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from ai_karen_engine.plugins.weather_query.client import WeatherClient

logger = logging.getLogger(__name__)


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return current weather summary for the given location."""
    location: Optional[str] = params.get("location")
    if not location:
        return {"error": "I need a location to check the weather."}

    api_key = os.getenv("OPENWEATHER_API_KEY")
    client: Optional[WeatherClient] = WeatherClient(api_key) if api_key else None

    if client:
        try:
            data = await client.get_current(location)
            weather = data.get("weather", [{}])[0]
            main = data.get("main", {})
            desc = weather.get("description", "").capitalize()
            temp_c = main.get("temp")
            feels_c = main.get("feels_like")
            humidity = main.get("humidity")
            wind = data.get("wind", {}).get("speed")
            summary = (
                f"Currently in {location}: {desc}. The temperature is {temp_c}°C ("
                f"feels like {feels_c}°C)."
            )
            if humidity is not None:
                summary += f" Humidity is {humidity}%."
            if wind is not None:
                summary += f" Wind speed {wind} m/s."
            return {
                "summary": summary,
                "ref_id": f"{location.lower().replace(' ', '_')}_forecast",
            }
        except Exception as exc:  # pragma: no cover - network fail safe
            logger.error("Weather lookup failed: %s", exc)

    # Fallback mocked response
    summary = (
        f"Currently in {location}: Clear skies. The temperature is 20°C "
        "(feels like 20°C)."
    )
    return {
        "summary": summary,
        "ref_id": f"{location.lower().replace(' ', '_')}_forecast",
    }
