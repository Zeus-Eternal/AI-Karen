import logging
from typing import Any, Dict

import httpx


logger = logging.getLogger(__name__)


class WeatherClient:
    """Minimal OpenWeatherMap API client."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def get_current(self, location: str) -> Dict[str, Any]:
        """Return current weather for the given location."""
        params = {"q": location, "appid": self.api_key, "units": "metric"}
        url = f"{self.base_url}/weather"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()

