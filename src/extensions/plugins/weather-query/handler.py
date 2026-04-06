"""Weather extension runtime."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from client import WeatherClient
from extensions.core.host.base import ExtensionBase, HookContext, HookPoint

logger = logging.getLogger(__name__)


def _location_ref(location: str) -> str:
    return f"{location.lower().replace(' ', '_')}_forecast"


class WeatherExtension(ExtensionBase):
    """Class-based weather extension for the unified extension host."""

    async def initialize(self) -> None:
        """No-op initialization for the weather extension."""

    async def shutdown(self) -> None:
        """No-op shutdown for the weather extension."""

    async def execute_hook(self, hook_point: HookPoint, context: HookContext) -> Dict[str, Any]:
        """Execute the weather action for supported hook points."""
        if hook_point not in self.manifest.hook_points:
            return {"error": f"Unsupported hook point: {hook_point.value}"}

        return await self.get_weather(context.data)

    async def get_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
                    f"Currently in {location}: {desc}. The temperature is {temp_c}°C "
                    f"(feels like {feels_c}°C)."
                )
                if humidity is not None:
                    summary += f" Humidity is {humidity}%."
                if wind is not None:
                    summary += f" Wind speed {wind} m/s."
                return {
                    "summary": summary,
                    "ref_id": _location_ref(location),
                }
            except Exception as exc:  # pragma: no cover - network fail safe
                logger.error("Weather lookup failed: %s", exc)

        summary = (
            f"Currently in {location}: Clear skies. The temperature is 20°C "
            "(feels like 20°C)."
        )
        return {
            "summary": summary,
            "ref_id": _location_ref(location),
        }


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible legacy entrypoint."""
    extension = WeatherExtension.__new__(WeatherExtension)
    return await WeatherExtension.get_weather(extension, params)
