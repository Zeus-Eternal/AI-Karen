# Weather Query Plugin

This plugin retrieves current weather information. It relies on
`WeatherClient` to make network requests, keeping the handler simple and easy
to test.

By default the free **wttr.in** service is used.  If the environment variable
`WEATHER_SERVICE` is set to `openweather` and a valid `OPENWEATHER_API_KEY` is
available, the plugin fetches data from OpenWeatherMap instead.
