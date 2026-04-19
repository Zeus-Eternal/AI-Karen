import asyncio
import logging
from typing import List, Dict, Any, Optional

try:
    from crawl4ai import (
        AsyncWebCrawler,
        BrowserConfig,
        CrawlerRunConfig,
        CacheMode
    )
except ImportError:
    # Fallback for environments without crawl4ai installed yet
    AsyncWebCrawler = None
    BrowserConfig = None
    CrawlerRunConfig = None
    CacheMode = None

logger = logging.getLogger(__name__)

class Crawl4AIIntegration:
    """
    Production-grade Crawl4AI integration layer.
    Responsibilities: Content acquisition and normalization ONLY.
    """

    def __init__(self, headless: bool = True):
        if AsyncWebCrawler is None:
            logger.warning("Crawl4AI not installed. Integration will operate in mock/degraded mode.")
        
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=False
        ) if BrowserConfig else None

    async def fetch_url(self, url: str, bypass_cache: bool = False) -> Dict[str, Any]:
        """Fetch a single URL and return normalized content."""
        if AsyncWebCrawler is None:
            return self._mock_result(url)

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS if bypass_cache else CacheMode.ENABLED
                    )
                )
                return self._normalize(result)
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return {"url": url, "error": str(e), "success": False}

    async def fetch_many(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple URLs in parallel."""
        if not urls:
            return []
            
        if AsyncWebCrawler is None:
            return [self._mock_result(url) for url in urls]

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                results = await crawler.arun_many(urls)
                return [self._normalize(r) for r in results if r]
        except Exception as e:
            logger.error(f"Parallel fetch failed: {e}")
            return [{"error": str(e), "success": False}]

    def _normalize(self, result) -> Dict[str, Any]:
        """Normalize Crawl4AI result into a consistent schema."""
        return {
            "url": getattr(result, "url", ""),
            "markdown": result.markdown.raw_markdown if hasattr(result, "markdown") and result.markdown else "",
            "links": getattr(result, "links", []),
            "metadata": getattr(result, "metadata", {}),
            "success": getattr(result, "success", True),
            "status_code": getattr(result, "status_code", 200)
        }

    def _mock_result(self, url: str) -> Dict[str, Any]:
        """Fallback mock result for testing/missing deps."""
        return {
            "url": url,
            "markdown": f"# Content from {url}\n\nThis is a placeholder as Crawl4AI is not active.",
            "links": [],
            "metadata": {"mock": True},
            "success": True,
            "status_code": 200
        }
