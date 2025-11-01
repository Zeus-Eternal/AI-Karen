"""
Search Plugin for AI-Karen
Integrated from neuro_recall search capabilities with SearxNG backend
"""

from typing import Any, Dict, List, Optional
import httpx
import logging
from ai_karen_engine.services.tools.contracts import (
    ToolContext,
    ToolResult,
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ExecutionMode
)

logger = logging.getLogger(__name__)

class SearchPlugin:
    """Privacy-respecting web search powered by SearxNG instances"""
    
    DEFAULT_HOST = "http://127.0.0.1:8080"
    DEFAULT_CATEGORY = "general"
    SAFE_SEARCH_LEVELS = {0, 1, 2}
    VALID_TIME_RANGES = {"day", "week", "month", "year"}
    
    def __init__(self, default_host: str = None):
        self.default_host = default_host or self.DEFAULT_HOST
    
    def _validate_safe_search(self, level: int) -> None:
        if level not in self.SAFE_SEARCH_LEVELS:
            raise ValueError(f"safe_search must be 0, 1 or 2 (got {level})")
    
    def _validate_time_range(self, time_range: Optional[str]) -> None:
        if time_range is not None and time_range not in self.VALID_TIME_RANGES:
            raise ValueError(f"time_range must be one of {sorted(self.VALID_TIME_RANGES)} (got {time_range})")
    
    async def search(
        self,
        context: ToolContext,
        query: str,
        num_results: int = 10,
        category: Optional[str] = None,
        language: str = "en",
        time_range: Optional[str] = None,
        safe_search: int = 1,
        host: Optional[str] = None
    ) -> ToolResult:
        """
        Run a web search via SearxNG instance
        
        Args:
            context: Tool execution context
            query: The search string
            num_results: Max results to return (default 10, max 20 recommended)
            category: SearxNG category (general, images, videos, news, etc.)
            language: Two-letter language code (default "en")
            time_range: Freshness filter: "day" | "week" | "month" | "year"
            safe_search: 0 = off, 1 = moderate, 2 = strict (default 1)
            host: Full base-URL of the SearxNG instance to query
            
        Returns:
            ToolResult with search results containing title, link, snippet
        """
        try:
            self._validate_safe_search(safe_search)
            self._validate_time_range(time_range)
            
            search_host = host or self.default_host
            
            params: Dict[str, Any] = {
                "q": query,
                "format": "json",
                "language": language,
                "categories": category or self.DEFAULT_CATEGORY,
                "pageno": 1,
                "safe": safe_search,
            }
            
            if time_range:
                params["time_range"] = time_range
            
            url = f"{search_host.rstrip('/')}/search"
            
            async with httpx.AsyncClient(
                timeout=20.0, 
                headers={"User-Agent": "ai-karen-search"}
            ) as client:
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    results = data.get("results", [])[:num_results]
                    
                    formatted_results = [
                        {
                            "title": result.get("title", ""),
                            "link": result.get("url", ""),
                            "snippet": result.get("content", ""),
                        }
                        for result in results
                    ]
                    
                    return ToolResult(
                        output=formatted_results,
                        success=True,
                        metadata={
                            "query": query,
                            "num_results": len(formatted_results),
                            "category": category or self.DEFAULT_CATEGORY,
                            "language": language,
                            "safe_search": safe_search
                        }
                    )
                    
                except Exception as exc:
                    logger.error(f"Search request failed: {exc}")
                    return ToolResult(
                        output=[{"title": "Search error", "link": "", "snippet": str(exc)}],
                        success=False,
                        error_message=f"Search failed: {str(exc)}"
                    )
                    
        except Exception as e:
            logger.error(f"Search validation failed: {e}")
            return ToolResult(
                output=[],
                success=False,
                error_message=f"Search validation failed: {str(e)}"
            )
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for registration"""
        return {
            "name": "web_search",
            "description": "Privacy-respecting web search powered by SearxNG",
            "scope": ToolScope.GLOBAL,
            "rbac_level": RBACLevel.DEVELOPER,
            "privacy_level": PrivacyLevel.PUBLIC,
            "parameters": {
                "query": {"type": "string", "required": True, "description": "Search query"},
                "num_results": {"type": "integer", "default": 10, "description": "Number of results"},
                "category": {"type": "string", "description": "Search category"},
                "language": {"type": "string", "default": "en", "description": "Language code"},
                "time_range": {"type": "string", "description": "Time range filter"},
                "safe_search": {"type": "integer", "default": 1, "description": "Safe search level"},
                "host": {"type": "string", "description": "SearxNG instance URL"}
            }
        }
