"""
Core tools implementation converted from TypeScript.

This module contains Python implementations of the core tools that were
originally implemented in TypeScript in the web UI.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import aiohttp
import time

from ..tool_service import BaseTool, ToolMetadata, ToolCategory, ToolParameter, ToolStatus

logger = logging.getLogger(__name__)


class DateTool(BaseTool):
    """Tool for getting current date information."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_current_date",
            description="Get the current date in a human-readable format",
            category=ToolCategory.TIME,
            parameters=[],
            return_type=str,
            examples=[
                {
                    "input": {},
                    "output": "Monday, January 15, 2024"
                }
            ],
            tags=["date", "time", "current"],
            timeout=5
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get current date."""
        now = datetime.now()
        return now.strftime("%A, %B %d, %Y")


class TimeTool(BaseTool):
    """Tool for getting current time information, optionally for specific locations."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_current_time",
            description="Get the current time, optionally for a specific location",
            category=ToolCategory.TIME,
            parameters=[
                ToolParameter(
                    name="location",
                    type=str,
                    description="Location to get time for (optional)",
                    required=False,
                    validation_rules={"max_length": 100}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {},
                    "output": "The current time (for me) is 2:30 PM. If you'd like the time for a specific place, please tell me the location."
                },
                {
                    "input": {"location": "New York"},
                    "output": "The current time in America/New_York is 2:30 PM."
                }
            ],
            tags=["time", "timezone", "location"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get current time for location."""
        location = parameters.get("location", "").strip()
        
        if not location:
            # Return server time
            server_time = datetime.now().strftime("%I:%M %p")
            return f"The current time (for me) is {server_time}. If you'd like the time for a specific place, please tell me the location."
        
        # Try multiple time APIs
        return await self._get_time_for_location(location)
    
    async def _get_time_for_location(self, location: str) -> str:
        """Get time for specific location using multiple APIs."""
        logs = []
        logs.append(f"getCurrentTime called with location: \"{location}\"")
        
        # Attempt 1: timeapi.io (Primary Source)
        try:
            time_api_location = location.replace(", ", "/").replace(" ", "_")
            url = f"https://timeapi.io/api/Time/current/zone?timeZone={time_api_location}"
            logs.append(f"Attempt 1 (timeapi.io): {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_text = await response.text()
                    logs.append(f"timeapi.io response status: {response.status}")
                    
                    if response.status == 200:
                        data = json.loads(response_text)
                        if data and data.get("dateTime") and data.get("timeZone"):
                            time_in_location = datetime.fromisoformat(data["dateTime"].replace("Z", "+00:00"))
                            formatted_time = time_in_location.strftime("%I:%M %p")
                            success_msg = f"The current time in {data['timeZone'].replace('_', ' ')} is {formatted_time}."
                            logs.append(f"TimeAPI.io Success: {success_msg}")
                            return success_msg
                    
                    # Handle error response
                    if "not found" in response_text.lower() or "invalid timezone" in response_text.lower():
                        logs.append(f"Location \"{time_api_location}\" not recognized by timeapi.io")
                    
        except Exception as e:
            logs.append(f"TimeAPI.io Error: {str(e)}")
        
        # Attempt 2: WorldTimeAPI (Fallback Source)
        try:
            url = f"https://worldtimeapi.org/api/timezone/{location}"
            logs.append(f"Attempt 2 (WorldTimeAPI original): {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_text = await response.text()
                    logs.append(f"WorldTimeAPI status: {response.status}")
                    
                    if response.status == 200:
                        data = json.loads(response_text)
                        if data and data.get("datetime") and data.get("timezone"):
                            time_in_location = datetime.fromisoformat(data["datetime"])
                            formatted_time = time_in_location.strftime("%I:%M %p")
                            success_msg = f"The current time in {data['timezone'].replace('_', ' ')} is {formatted_time} (obtained via backup source WorldTimeAPI)."
                            logs.append(f"WorldTimeAPI Success: {success_msg}")
                            return success_msg
                    
        except Exception as e:
            logs.append(f"WorldTimeAPI Error: {str(e)}")
        
        # Attempt 3: Simplified location (city part) if original had comma
        if "," in location:
            try:
                city_part = location.split(",")[0].strip()
                if city_part and city_part.lower() != location.lower():
                    url = f"https://worldtimeapi.org/api/timezone/{city_part}"
                    logs.append(f"Attempt 3 (WorldTimeAPI simplified city \"{city_part}\"): {url}")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data and data.get("datetime") and data.get("timezone"):
                                    time_in_location = datetime.fromisoformat(data["datetime"])
                                    formatted_time = time_in_location.strftime("%I:%M %p")
                                    success_msg = f"The current time in {data['timezone'].replace('_', ' ')} is {formatted_time} (obtained using simplified location \"{city_part}\" with WorldTimeAPI)."
                                    logs.append(f"WorldTimeAPI Success for simplified city: {success_msg}")
                                    return success_msg
                            
            except Exception as e:
                logs.append(f"WorldTimeAPI (simplified city) Error: {str(e)}")
        
        # Attempt 4: Remove " City" suffix if present
        if location.lower().endswith(" city") and len(location) > 5:
            try:
                location_without_suffix = location[:-5].strip()
                url = f"https://worldtimeapi.org/api/timezone/{location_without_suffix}"
                logs.append(f"Attempt 4 (WorldTimeAPI suffix-removed \"{location_without_suffix}\"): {url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and data.get("datetime") and data.get("timezone"):
                                time_in_location = datetime.fromisoformat(data["datetime"])
                                formatted_time = time_in_location.strftime("%I:%M %p")
                                success_msg = f"The current time in {data['timezone'].replace('_', ' ')} is {formatted_time} (obtained using suffix-removed location \"{location_without_suffix}\" with WorldTimeAPI)."
                                logs.append(f"WorldTimeAPI Success for suffix-removed: {success_msg}")
                                return success_msg
                        
            except Exception as e:
                logs.append(f"WorldTimeAPI (suffix-removed) Error: {str(e)}")
        
        # All attempts failed
        error_message = f"I couldn't get the time for \"{location}\". All attempts failed. Please check the location name and format or try a nearby major city."
        logger.warning(" --- ".join(logs))
        return error_message


class WeatherTool(BaseTool):
    """Tool for getting weather information for locations."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_weather",
            description="Get current weather information for a location",
            category=ToolCategory.WEATHER,
            parameters=[
                ToolParameter(
                    name="location",
                    type=str,
                    description="Location to get weather for",
                    required=True,
                    validation_rules={"min_length": 1, "max_length": 100}
                ),
                ToolParameter(
                    name="temperature_unit",
                    type=str,
                    description="Temperature unit (C or F)",
                    required=False,
                    default="C",
                    validation_rules={"allowed_values": ["C", "F"]}
                ),
                ToolParameter(
                    name="service",
                    type=str,
                    description="Weather service to use",
                    required=False,
                    default="wttr_in",
                    validation_rules={"allowed_values": ["wttr_in", "custom_api"]}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {"location": "London"},
                    "output": "Currently in London: Partly cloudy. The temperature is 15°C (feels like 13°C). Humidity is at 65%. Wind speed is 12 km/h."
                }
            ],
            tags=["weather", "temperature", "location"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get weather for location."""
        location = parameters["location"].strip()
        temperature_unit = parameters.get("temperature_unit", "C")
        service = parameters.get("service", "wttr_in")
        
        if not location:
            return "Please specify a location for the weather. For example, you can ask 'what's the weather in London?'."
        
        if service == "custom_api":
            logger.info("Custom API service selected but not implemented, falling back to wttr.in")
        
        return await self._get_weather_from_wttr(location, temperature_unit)
    
    async def _get_weather_from_wttr(self, location: str, temperature_unit: str) -> str:
        """Get weather from wttr.in service."""
        url = f"https://wttr.in/{location}?format=j1"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        if "Unknown location" in response_text:
                            return f"Unknown location \"{location}\" according to wttr.in."
                        return f"Failed to fetch weather for \"{location}\". HTTP error {response.status}"
                    
                    data = json.loads(response_text)
                    
                    if not data or not data.get("current_condition"):
                        return f"Sorry, I received an unexpected response when fetching weather for \"{location}\"."
                    
                    current_condition = data["current_condition"][0]
                    
                    # Check for invalid data
                    if (data.get("weather") and data["weather"][0].get("maxtempC") == "0" and 
                        data["weather"][0].get("mintempC") == "0"):
                        return f"Sorry, I couldn't find reliable weather data for \"{location}\". Please check if the location is correct."
                    
                    # Extract weather information
                    description = "Not available"
                    if current_condition.get("weatherDesc") and current_condition["weatherDesc"]:
                        description = current_condition["weatherDesc"][0]["value"]
                    
                    temp_c = float(current_condition.get("temp_C", 0))
                    feels_like_c = float(current_condition.get("FeelsLikeC", temp_c))
                    
                    # Convert temperature if needed
                    if temperature_unit == "F":
                        temp = (temp_c * 9/5) + 32
                        feels_like = (feels_like_c * 9/5) + 32
                        unit_symbol = "°F"
                    else:
                        temp = temp_c
                        feels_like = feels_like_c
                        unit_symbol = "°C"
                    
                    # Build weather string
                    weather_parts = [
                        f"Currently in {location}: {description}.",
                        f"The temperature is {temp:.0f}{unit_symbol} (feels like {feels_like:.0f}{unit_symbol})."
                    ]
                    
                    humidity = current_condition.get("humidity")
                    if humidity:
                        weather_parts.append(f"Humidity is at {humidity}%.")
                    
                    wind_speed = current_condition.get("windspeedKmph")
                    if wind_speed:
                        weather_parts.append(f"Wind speed is {wind_speed} km/h.")
                    
                    return " ".join(weather_parts)
                    
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return f"Sorry, I encountered an error while trying to fetch the weather for \"{location}\". Please check your connection or try again."


class BookDatabaseTool(BaseTool):
    """Mock tool for querying book database."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="query_book_database",
            description="Query a mock book database for book information",
            category=ToolCategory.DATABASE,
            parameters=[
                ToolParameter(
                    name="book_title",
                    type=str,
                    description="Title of the book to look up",
                    required=True,
                    validation_rules={"min_length": 1, "max_length": 200}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {"book_title": "Dune"},
                    "output": "{\"title\": \"Dune\", \"author\": \"Frank Herbert\", \"genre\": \"Science Fiction\", \"summary\": \"...\", \"publishedYear\": 1965}"
                }
            ],
            tags=["books", "database", "mock"],
            timeout=5
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Query mock book database."""
        book_title = parameters["book_title"].strip()
        
        if not book_title:
            return json.dumps({
                "error": "Missing book title",
                "message": "I need a book title to look up details. Which book are you interested in?"
            })
        
        # Simulate database lookup delay
        await asyncio.sleep(0.5)
        
        # Mock database responses
        book_title_lower = book_title.lower()
        
        if "dune" in book_title_lower:
            return json.dumps({
                "title": book_title,
                "author": "Frank Herbert",
                "genre": "Science Fiction",
                "summary": "Dune is a 1965 science fiction novel by American author Frank Herbert, originally published as two separate serials in Analog magazine. It tied with Roger Zelazny's This Immortal for the Hugo Award in 1966 and it won the inaugural Nebula Award for Best Novel.",
                "publishedYear": 1965
            })
        elif "gatsby" in book_title_lower:
            return json.dumps({
                "title": book_title,
                "author": "F. Scott Fitzgerald",
                "genre": "Novel",
                "summary": "The Great Gatsby is a 1925 novel by American writer F. Scott Fitzgerald. Set in the Jazz Age on Long Island, near New York City, the novel depicts first-person narrator Nick Carraway's interactions with mysterious millionaire Jay Gatsby and Gatsby's obsession to reunite with his former lover, Daisy Buchanan.",
                "publishedYear": 1925
            })
        else:
            return json.dumps({
                "error": "Book not found",
                "title": book_title,
                "message": f"Sorry, I couldn't find detailed information for the item titled \"{book_title}\" in the database."
            })


class GmailUnreadTool(BaseTool):
    """Mock tool for checking Gmail unread emails."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="check_gmail_unread",
            description="Check unread Gmail emails (mock implementation)",
            category=ToolCategory.COMMUNICATION,
            parameters=[],
            return_type=str,
            examples=[
                {
                    "input": {},
                    "output": "{\"unreadCount\": 2, \"emails\": [{\"from\": \"Alice\", \"subject\": \"Meeting\", \"snippet\": \"...\"}]}"
                }
            ],
            tags=["gmail", "email", "mock"],
            timeout=5
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Check Gmail unread emails (mock)."""
        # Simulate API call delay
        await asyncio.sleep(0.7)
        
        return json.dumps({
            "unreadCount": 2,
            "emails": [
                {
                    "from": "Alice Wonderland",
                    "subject": "Tea Party Invitation",
                    "snippet": "You're invited to a mad tea party!"
                },
                {
                    "from": "Hacker News Digest",
                    "subject": "Top Stories for Today",
                    "snippet": "Check out the latest in tech..."
                }
            ]
        })


class GmailComposeTool(BaseTool):
    """Mock tool for composing Gmail emails."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="compose_gmail",
            description="Compose and send Gmail email (mock implementation)",
            category=ToolCategory.COMMUNICATION,
            parameters=[
                ToolParameter(
                    name="recipient",
                    type=str,
                    description="Email recipient",
                    required=True,
                    validation_rules={"min_length": 1}
                ),
                ToolParameter(
                    name="subject",
                    type=str,
                    description="Email subject",
                    required=True,
                    validation_rules={"min_length": 1}
                ),
                ToolParameter(
                    name="body",
                    type=str,
                    description="Email body",
                    required=True,
                    validation_rules={"min_length": 1}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {
                        "recipient": "alice@example.com",
                        "subject": "Hello",
                        "body": "Hi Alice, how are you?"
                    },
                    "output": "{\"success\": true, \"message\": \"Email sent to alice@example.com\"}"
                }
            ],
            tags=["gmail", "email", "compose", "mock"],
            timeout=5
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Compose Gmail email (mock)."""
        recipient = parameters.get("recipient", "").strip()
        subject = parameters.get("subject", "").strip()
        body = parameters.get("body", "").strip()
        
        # Check for missing fields
        missing = []
        if not recipient:
            missing.append("recipient")
        if not subject:
            missing.append("subject")
        if not body:
            missing.append("body")
        
        if missing:
            return json.dumps({
                "error": "Missing email details",
                "message": f"I'm missing some details to compose the email. I still need the {', '.join(missing)}. Could you provide them?"
            })
        
        # Simulate sending delay
        await asyncio.sleep(0.6)
        
        return json.dumps({
            "success": True,
            "message": f"Okay, I've \"sent\" an email to {recipient} with the subject \"{subject}\"."
        })


class KarenPluginTool(BaseTool):
    """Tool for executing Karen plugins."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="execute_karen_plugin",
            description="Execute a Karen plugin with specified parameters",
            category=ToolCategory.PLUGIN,
            parameters=[
                ToolParameter(
                    name="plugin_name",
                    type=str,
                    description="Name of the plugin to execute",
                    required=True,
                    validation_rules={"min_length": 1}
                ),
                ToolParameter(
                    name="parameters",
                    type=dict,
                    description="Plugin parameters",
                    required=False,
                    default={}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {
                        "plugin_name": "hello-world",
                        "parameters": {"name": "Alice"}
                    },
                    "output": "{\"success\": true, \"result\": \"Hello, Alice!\", \"plugin\": \"hello-world\"}"
                }
            ],
            tags=["plugin", "karen", "execution"],
            timeout=30
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Execute Karen plugin."""
        plugin_name = parameters["plugin_name"]
        plugin_params = parameters.get("parameters", {})
        user_id = context.get("user_id") if context else None
        
        try:
            # Import plugin service
            from ..plugin_service import get_plugin_service
            
            plugin_service = get_plugin_service()
            await plugin_service._ensure_initialized()
            
            # Execute plugin
            result = await plugin_service.execute_plugin(
                plugin_name=plugin_name,
                parameters=plugin_params,
                user_id=user_id
            )
            
            if result.success:
                return json.dumps({
                    "success": True,
                    "plugin": plugin_name,
                    "result": result.result,
                    "message": f"Successfully executed {plugin_name} plugin.",
                    "timestamp": result.started_at.isoformat()
                })
            else:
                return json.dumps({
                    "success": False,
                    "plugin": plugin_name,
                    "error": result.error,
                    "message": f"Failed to execute {plugin_name} plugin: {result.error}",
                    "timestamp": result.started_at.isoformat()
                })
                
        except Exception as e:
            logger.error(f"Plugin execution error: {e}")
            return json.dumps({
                "success": False,
                "plugin": plugin_name,
                "error": str(e),
                "message": f"I encountered an error while trying to execute the {plugin_name} plugin."
            })


class KarenMemoryQueryTool(BaseTool):
    """Tool for querying Karen memory system."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="query_karen_memory",
            description="Query the Karen memory system for relevant information",
            category=ToolCategory.MEMORY,
            parameters=[
                ToolParameter(
                    name="query_text",
                    type=str,
                    description="Text to search for in memory",
                    required=True,
                    validation_rules={"min_length": 1, "max_length": 500}
                ),
                ToolParameter(
                    name="top_k",
                    type=int,
                    description="Number of results to return",
                    required=False,
                    default=5,
                    validation_rules={"min_value": 1, "max_value": 20}
                ),
                ToolParameter(
                    name="similarity_threshold",
                    type=float,
                    description="Minimum similarity threshold",
                    required=False,
                    default=0.7,
                    validation_rules={"min_value": 0.0, "max_value": 1.0}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {"query_text": "coffee preferences"},
                    "output": "{\"success\": true, \"found\": 2, \"memories\": [...], \"message\": \"Found 2 relevant memories\"}"
                }
            ],
            tags=["memory", "search", "karen"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Query Karen memory."""
        query_text = parameters["query_text"]
        top_k = parameters.get("top_k", 5)
        similarity_threshold = parameters.get("similarity_threshold", 0.7)
        
        user_id = context.get("user_id") if context else None
        session_id = context.get("session_id") if context else None
        
        try:
            # Import memory service
            from ..memory_service import WebUIMemoryService
            
            memory_service = WebUIMemoryService()
            
            # Query memories
            memories = await memory_service.query_memories(
                text=query_text,
                user_id=user_id,
                session_id=session_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            if memories:
                formatted_memories = []
                for mem in memories:
                    formatted_memories.append({
                        "content": mem.get("content", ""),
                        "similarity": f"{mem.get('similarity_score', 0):.3f}",
                        "tags": mem.get("tags", []),
                        "timestamp": mem.get("timestamp", "")
                    })
                
                return json.dumps({
                    "success": True,
                    "query": query_text,
                    "found": len(memories),
                    "memories": formatted_memories,
                    "message": f"Found {len(memories)} relevant memories for your query."
                })
            else:
                return json.dumps({
                    "success": True,
                    "query": query_text,
                    "found": 0,
                    "memories": [],
                    "message": "I couldn't find any relevant memories for that query."
                })
                
        except Exception as e:
            logger.error(f"Memory query error: {e}")
            return json.dumps({
                "success": False,
                "query": query_text,
                "error": str(e),
                "message": "I had trouble searching through my memories right now."
            })


class KarenMemoryStoreTool(BaseTool):
    """Tool for storing information in Karen memory system."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="store_karen_memory",
            description="Store information in the Karen memory system",
            category=ToolCategory.MEMORY,
            parameters=[
                ToolParameter(
                    name="content",
                    type=str,
                    description="Content to store in memory",
                    required=True,
                    validation_rules={"min_length": 1, "max_length": 2000}
                ),
                ToolParameter(
                    name="tags",
                    type=list,
                    description="Tags for the memory entry",
                    required=False,
                    default=[]
                ),
                ToolParameter(
                    name="metadata",
                    type=dict,
                    description="Additional metadata",
                    required=False,
                    default={}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {
                        "content": "User likes coffee with milk",
                        "tags": ["preferences", "coffee"]
                    },
                    "output": "{\"success\": true, \"memoryId\": \"abc123\", \"message\": \"Information stored\"}"
                }
            ],
            tags=["memory", "store", "karen"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Store information in Karen memory."""
        content = parameters["content"]
        tags = parameters.get("tags", [])
        metadata = parameters.get("metadata", {})
        
        user_id = context.get("user_id") if context else None
        session_id = context.get("session_id") if context else None
        
        try:
            # Import memory service
            from ..memory_service import WebUIMemoryService
            
            memory_service = WebUIMemoryService()
            
            # Store memory
            memory_id = await memory_service.store_memory(
                content=content,
                metadata=metadata,
                tags=tags,
                user_id=user_id,
                session_id=session_id
            )
            
            if memory_id:
                return json.dumps({
                    "success": True,
                    "memoryId": memory_id,
                    "content": content[:100] + ("..." if len(content) > 100 else ""),
                    "tags": tags,
                    "message": "I've stored that information in my memory for future reference."
                })
            else:
                return json.dumps({
                    "success": False,
                    "message": "I had trouble storing that information in my memory."
                })
                
        except Exception as e:
            logger.error(f"Memory store error: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "I encountered an issue while trying to store that information."
            })


class KarenSystemStatusTool(BaseTool):
    """Tool for getting Karen system status."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_karen_system_status",
            description="Get current system status and health information",
            category=ToolCategory.SYSTEM,
            parameters=[],
            return_type=str,
            examples=[
                {
                    "input": {},
                    "output": "{\"success\": true, \"health\": {...}, \"metrics\": {...}, \"message\": \"System is healthy\"}"
                }
            ],
            tags=["system", "health", "status"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get system status."""
        try:
            # Mock system metrics (in real implementation, would query actual system)
            import psutil
            import os
            
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Calculate uptime (mock)
            uptime_hours = 24.5  # Mock value
            
            health_status = "healthy"
            if cpu_usage > 80 or memory_usage > 90:
                health_status = "degraded"
            
            return json.dumps({
                "success": True,
                "health": {
                    "status": health_status,
                    "services": 5,  # Mock service count
                    "timestamp": datetime.utcnow().isoformat()
                },
                "metrics": {
                    "cpu_usage": round(cpu_usage, 1),
                    "memory_usage": round(memory_usage, 1),
                    "active_sessions": 3,  # Mock value
                    "uptime_hours": uptime_hours,
                    "response_time_avg": 0.15  # Mock value
                },
                "message": f"System is {health_status}. CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%, Uptime: {uptime_hours}h"
            })
            
        except Exception as e:
            logger.error(f"System status error: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "I'm having trouble checking my system status right now."
            })


class KarenAnalyticsTool(BaseTool):
    """Tool for getting Karen analytics data."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_karen_analytics",
            description="Get usage analytics and statistics",
            category=ToolCategory.ANALYTICS,
            parameters=[
                ToolParameter(
                    name="time_range",
                    type=str,
                    description="Time range for analytics (e.g., '24h', '7d', '30d')",
                    required=False,
                    default="24h",
                    validation_rules={"allowed_values": ["1h", "24h", "7d", "30d"]}
                )
            ],
            return_type=str,
            examples=[
                {
                    "input": {"time_range": "24h"},
                    "output": "{\"success\": true, \"analytics\": {...}, \"message\": \"Analytics for last 24h\"}"
                }
            ],
            tags=["analytics", "statistics", "usage"],
            timeout=10
        )
    
    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get analytics data."""
        time_range = parameters.get("time_range", "24h")
        
        try:
            # Mock analytics data (in real implementation, would query analytics database)
            analytics_data = {
                "total_interactions": 150,
                "unique_users": 25,
                "user_satisfaction": 4.2,
                "popular_features": ["weather", "time", "memory"],
                "peak_hours": ["10:00", "14:00", "20:00"]
            }
            
            # Adjust numbers based on time range
            if time_range == "1h":
                analytics_data["total_interactions"] = 12
                analytics_data["unique_users"] = 5
            elif time_range == "7d":
                analytics_data["total_interactions"] = 1050
                analytics_data["unique_users"] = 180
            elif time_range == "30d":
                analytics_data["total_interactions"] = 4500
                analytics_data["unique_users"] = 750
            
            return json.dumps({
                "success": True,
                "timeRange": time_range,
                "analytics": analytics_data,
                "message": f"In the last {time_range}: {analytics_data['total_interactions']} interactions from {analytics_data['unique_users']} users. Satisfaction: {analytics_data['user_satisfaction']}/5.0"
            })
            
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return json.dumps({
                "success": False,
                "timeRange": time_range,
                "error": str(e),
                "message": "I couldn't retrieve analytics data right now."
            })