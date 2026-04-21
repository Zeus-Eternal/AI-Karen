"""
Weather tool for Karen AI's tool integration system.

This module provides a weather tool that integrates the weather-query plugin
with Karen's tool system, making it available for chat conversations and agent workflows.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from ai_karen_engine.services.tool_service import (
    BaseTool,
    ToolMetadata,
    ToolParameter,
    ParameterType,
    ToolExecutionContext,
    ToolExecutionResult,
)

logger = logging.getLogger(__name__)


class WeatherTool(BaseTool):
    """Weather query tool for Karen AI's tool integration system."""

    def __init__(self):
        # Define tool metadata
        weather_metadata = ToolMetadata(
            name="weather",
            display_name="Weather Query",
            description="Get current weather information for a location",
            version="1.0.0",
            author="Karen AI Team",
            category="weather",
            tags=["weather", "forecast", "location", "meteorology"],
            documentation_url="https://github.com/KIRO/AI-Karen/blob/main/src/extensions/plugins/weather-query/README.md",
        )

        # Define tool parameters
        weather_params = [
            ToolParameter(
                name="location",
                type=ParameterType.STRING,
                description="Location to get weather for (e.g., 'London', 'New York', 'Tokyo')",
                required=True,
                examples=["London", "Paris, France", "New York, US", "Tokyo, Japan"],
            ),
            ToolParameter(
                name="units",
                type=ParameterType.STRING,
                description="Temperature units (metric or imperial)",
                required=False,
                default_value="metric",
                validation_rules={"allowed_values": ["metric", "imperial"]},
                examples=["metric", "imperial"],
            ),
        ]

        # Initialize the tool with its execution function
        super().__init__(weather_metadata, weather_params, self._execute_weather_query)

    async def _execute_weather_query(
        self, parameters: Dict[str, Any], context: ToolExecutionContext
    ) -> Dict[str, Any]:
        """Execute weather query using the weather-query plugin."""
        try:
            import asyncio

            location = parameters.get("location")
            if not location:
                return {
                    "error": "Location parameter is required",
                    "suggestion": "Please provide a location like 'London', 'New York', or 'Tokyo'",
                }

            # Import the weather plugin handler
            try:
                from src.extensions.plugins.weather_query.handler import (
                    WeatherExtension,
                )
            except ImportError:
                logger.error("Weather plugin not found. Falling back to mock data.")
                return self._get_mock_weather_data(location)

            # Create weather extension instance
            weather_extension = WeatherExtension()

            # Prepare parameters for the weather plugin
            weather_params = {"location": location}

            # Add units if specified
            units = parameters.get("units", "metric")
            if units != "metric":
                weather_params["units"] = "imperial"

            # Execute the weather query
            result = await weather_extension.get_weather(weather_params)

            # Format the result for the tool response
            if "error" in result:
                return {"error": result["error"], "location": location}

            # Add metadata to the result
            formatted_result = {
                "location": location,
                "weather_summary": result.get(
                    "summary", "Weather information unavailable"
                ),
                "reference_id": result.get(
                    "ref_id", f"{location.lower().replace(' ', '_')}_weather"
                ),
                "timestamp": context.timestamp.isoformat(),
                "units": units,
            }

            logger.info(f"Successfully retrieved weather for {location}")
            return formatted_result

        except Exception as e:
            logger.error(f"Weather tool execution failed: {e}", exc_info=True)
            return {
                "error": f"Failed to retrieve weather information: {str(e)}",
                "location": location or "unknown",
            }

    def _get_mock_weather_data(self, location: str) -> Dict[str, Any]:
        """Fallback mock weather data when plugin is not available."""
        return {
            "location": location,
            "weather_summary": f"Currently in {location}: Clear skies. The temperature is 20°C (feels like 20°C). Humidity is 60%. Wind speed 5 m/s.",
            "reference_id": f"{location.lower().replace(' ', '_')}_weather",
            "timestamp": "mock-data",
            "units": "metric",
            "note": "Using mock data - weather plugin not properly configured",
        }


# Global instance for easy registration
weather_tool = WeatherTool()


def register_weather_tool(tool_integration_service) -> bool:
    """Register the weather tool with the tool integration service."""
    try:
        success = tool_integration_service.register_tool(weather_tool)
        if success:
            logger.info("Weather tool registered successfully")
        else:
            logger.error("Failed to register weather tool")
        return success
    except Exception as e:
        logger.error(f"Error registering weather tool: {e}")
        return False


def get_weather_tool_info() -> Dict[str, Any]:
    """Get information about the weather tool."""
    return weather_tool.get_info()
