# Weather Query Plugin

This core plugin returns basic weather information. When the environment
variable `OPENWEATHER_API_KEY` is provided with a valid OpenWeatherMap API key,
the plugin calls the OpenWeatherMap REST API to fetch current conditions.
If the key is absent or an error occurs, the plugin falls back to mocked
responses so tests remain deterministic.

Supported parameter:

* `location` – the city or region to look up.
