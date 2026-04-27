"""
Web search client with support for multiple search providers.

Supported providers:
- duckduckgo: Free, no API key needed
- tavily: AI-focused search with free tier
- google_custom_search: Google Custom Search JSON API (paid)
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result"""
    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    published_date: Optional[str] = None
    source: Optional[str] = None


@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    results: List[SearchResult]
    total_results: Optional[int] = None
    search_time: Optional[float] = None
    provider: str = "unknown"
    error: Optional[str] = None


class WebSearchClient:
    """
    Multi-provider web search client.

    Automatically falls back to DuckDuckGo if configured providers fail.
    """

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Initialize search client.

        Args:
            settings: Configuration dict with provider settings
        """
        self.settings = settings or {}
        self.session: Optional[aiohttp.ClientSession] = None

        # Provider configurations
        self.providers = {
            "duckduckgo": {
                "enabled": True,
                "priority": 100,  # Highest priority free provider
            },
            "tavily": {
                "enabled": bool(self.settings.get("tavily_api_key")),
                "api_key": self.settings.get("tavily_api_key"),
                "api_url": "https://api.tavily.com/search",
                "priority": 90,
            },
            "google_custom_search": {
                "enabled": bool(
                    self.settings.get("google_api_key")
                    and self.settings.get("google_cx_id")
                ),
                "api_key": self.settings.get("google_api_key"),
                "cx_id": self.settings.get("google_cx_id"),
                "api_url": "https://www.googleapis.com/customsearch/v1",
                "priority": 80,
            },
        }

        # Sort providers by priority
        self._sorted_providers = sorted(
            [
                (name, config)
                for name, config in self.providers.items()
                if config.get("enabled", False)
            ],
            key=lambda x: x[1].get("priority", 0),
            reverse=True,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None

    async def search(
        self,
        query: str,
        max_results: int = 5,
        time_range: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> SearchResponse:
        """
        Perform web search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            time_range: Time filter (e.g., "d" for day, "w" for week, "m" for month, "y" for year)
            provider: Force specific provider (falls back to others if fails)
            **kwargs: Additional provider-specific parameters

        Returns:
            SearchResponse with results or error
        """
        if not query or not query.strip():
            return SearchResponse(
                query=query,
                results=[],
                provider="none",
                error="Empty query",
            )

        # Use specific provider if requested, otherwise try all by priority
        if provider:
            if provider in self.providers and self.providers[provider]["enabled"]:
                result = await self._search_with_provider(
                    provider,
                    query,
                    max_results,
                    time_range,
                    **kwargs,
                )
                return result
            else:
                # Fallback to highest priority provider
                logger.warning(
                    f"Requested provider '{provider}' not available, falling back",
                )

        # Try providers in priority order
        last_error = None
        for provider_name, config in self._sorted_providers:
            try:
                logger.debug(
                    f"Attempting search with provider: {provider_name}",
                    extra={"provider": provider_name, "query": query},
                )
                result = await self._search_with_provider(
                    provider_name,
                    query,
                    max_results,
                    time_range,
                    **kwargs,
                )

                if not result.error and result.results:
                    return result

                last_error = result.error or "No results"
                logger.debug(
                    f"Provider {provider_name} returned no results",
                    extra={"provider": provider_name, "error": last_error},
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Provider {provider_name} failed: {e}",
                    extra={"provider": provider_name, "error": str(e)},
                )
                continue

        # All providers failed
        return SearchResponse(
            query=query,
            results=[],
            provider="none",
            error=f"All providers failed. Last error: {last_error}",
        )

    async def _search_with_provider(
        self,
        provider_name: str,
        query: str,
        max_results: int,
        time_range: Optional[str] = None,
        **kwargs,
    ) -> SearchResponse:
        """Search with specific provider."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        if provider_name == "duckduckgo":
            return await self._search_duckduckgo(query, max_results, **kwargs)
        elif provider_name == "tavily":
            return await self._search_tavily(query, max_results, time_range, **kwargs)
        elif provider_name == "google_custom_search":
            return await self._search_google(query, max_results, time_range, **kwargs)
        else:
            return SearchResponse(
                query=query,
                results=[],
                provider="none",
                error=f"Unknown provider: {provider_name}",
            )

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        **kwargs,
    ) -> SearchResponse:
        """
        Search using DuckDuckGo HTML parsing (no API key required).

        Note: This is a scraping approach and may be less reliable than official APIs.
        """
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {
                "q": query,
                "kl": "us-en",
            }

            # Add headers to avoid bot detection
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            async with self.session.get(url, params=params, headers=headers) as response:
                # Accept 200 and 202 (DuckDuckGo sometimes returns 202)
                if response.status not in (200, 202):
                    return SearchResponse(
                        query=query,
                        results=[],
                        provider="duckduckgo",
                        error=f"HTTP {response.status}",
                    )

                html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find all result divs - try multiple selectors
            result_divs = soup.find_all("div", class_="result")

            if not result_divs:
                # Try alternative selectors
                result_divs = soup.find_all("div", class_="web-result")

            for i, div in enumerate(result_divs[:max_results]):
                try:
                    # Try multiple selectors for title
                    title_elem = (
                        div.find("a", class_="result__a")
                        or div.find("a", class_="result__url")
                        or div.find("a")
                    )
                    snippet_elem = div.find("a", class_="result__snippet")

                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and url:
                        results.append(
                            SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                source="duckduckgo",
                            )
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to parse DuckDuckGo result {i}: {e}",
                    )
                    continue

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                provider="duckduckgo",
            )

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}", exc_info=True)
            return SearchResponse(
                query=query,
                results=[],
                provider="duckduckgo",
                error=str(e),
            )

    async def _search_tavily(
        self,
        query: str,
        max_results: int,
        time_range: Optional[str] = None,
        **kwargs,
    ) -> SearchResponse:
        """Search using Tavily API."""
        api_key = self.providers["tavily"]["api_key"]
        api_url = self.providers["tavily"]["api_url"]

        try:
            # Convert time_range to days for Tavily
            days = None
            if time_range:
                time_map = {"d": 1, "w": 7, "m": 30, "y": 365}
                days = time_map.get(time_range.lower(), None)

            payload = {
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
            }

            if days:
                payload["days"] = days

            async with self.session.post(api_url, json=payload) as response:
                data = await response.json()

            if response.status != 200:
                error_msg = data.get("message", f"HTTP {response.status}")
                return SearchResponse(
                    query=query,
                    results=[],
                    provider="tavily",
                    error=error_msg,
                )

            results = []
            for item in data.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        published_date=item.get("published_date"),
                        source="tavily",
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get("num_results"),
                search_time=data.get("answer_time_seconds"),
                provider="tavily",
            )

        except Exception as e:
            logger.error(f"Tavily search error: {e}", exc_info=True)
            return SearchResponse(
                query=query,
                results=[],
                provider="tavily",
                error=str(e),
            )

    async def _search_google(
        self,
        query: str,
        max_results: int,
        time_range: Optional[str] = None,
        **kwargs,
    ) -> SearchResponse:
        """Search using Google Custom Search API."""
        api_key = self.providers["google_custom_search"]["api_key"]
        cx_id = self.providers["google_custom_search"]["cx_id"]
        api_url = self.providers["google_custom_search"]["api_url"]

        try:
            params = {
                "key": api_key,
                "cx": cx_id,
                "q": query,
                "num": max_results,
            }

            if time_range:
                params["dateRestrict"] = time_range

            async with self.session.get(api_url, params=params) as response:
                data = await response.json()

            if response.status != 200:
                error_msg = data.get("error", {}).get("message", f"HTTP {response.status}")
                return SearchResponse(
                    query=query,
                    results=[],
                    provider="google_custom_search",
                    error=error_msg,
                )

            results = []
            for item in data.get("items", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="google_custom_search",
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get("searchInformation", {}).get("totalResults"),
                search_time=data.get("searchInformation", {}).get("searchTime"),
                provider="google_custom_search",
            )

        except Exception as e:
            logger.error(f"Google Custom Search error: {e}", exc_info=True)
            return SearchResponse(
                query=query,
                results=[],
                provider="google_custom_search",
                error=str(e),
            )

    def is_configured(self) -> bool:
        """Check if any provider is configured."""
        return any(config.get("enabled", False) for config in self.providers.values())

    def get_available_providers(self) -> List[str]:
        """Get list of enabled providers."""
        return [
            name
            for name, config in self.providers.items()
            if config.get("enabled", False)
        ]
