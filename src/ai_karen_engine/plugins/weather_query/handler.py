"""Weather plugin handler."""

from __future__ import annotations

import json
from typing import Optional

import httpx

BASE_URL = "https://wttr.in"  # default simple weather service


async def run(params: dict) -> dict:
    """Return a simple weather summary and widget reference for the given location."""
    location: Optional[str] = params.get("location")
    if not location:
        return {"error": "I need a location to check the weather."}

    url = f"{BASE_URL}/{location}?format=j1"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover - network fail safe
            return {
                "error": f"Sorry, I couldn't fetch the weather for {location}: {exc}"
            }

    try:
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp_c = current["temp_C"]
        feels_c = current["FeelsLikeC"]
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
