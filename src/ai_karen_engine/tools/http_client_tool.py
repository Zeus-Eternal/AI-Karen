"""
HTTP Client Tool for AI-Karen
Production-ready HTTP client for making API calls and web requests.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class HTTPClientTool:
    """
    Production-grade HTTP client tool for API interactions.

    Features:
    - Support for all HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
    - Custom headers and authentication
    - Request/response logging
    - Timeout and retry logic
    - JSON, form data, and multipart support
    - Response parsing (JSON, text, binary)
    - Error handling and status code validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_backoff = self.config.get('retry_backoff', 2)
        self.verify_ssl = self.config.get('verify_ssl', True)
        self.user_agent = self.config.get('user_agent', 'AI-Karen-Agent/1.0')
        self.default_headers = self.config.get('default_headers', {})

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        auth: Optional[tuple] = None,
        timeout: Optional[int] = None,
        follow_redirects: bool = True
    ) -> Dict[str, Any]:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.)
            url: Target URL
            headers: Request headers
            params: URL query parameters
            data: Form data or raw body
            json_data: JSON body data
            auth: Basic auth tuple (username, password)
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow redirects

        Returns:
            Dictionary with response data:
                - status_code: HTTP status code
                - headers: Response headers
                - body: Response body
                - json: Parsed JSON (if applicable)
                - text: Response text
                - elapsed: Request duration
        """
        method = method.upper()
        timeout_val = timeout or self.timeout

        # Prepare headers
        request_headers = {
            'User-Agent': self.user_agent,
            **self.default_headers
        }
        if headers:
            request_headers.update(headers)

        # Handle authentication
        auth_header = None
        if auth:
            import base64
            credentials = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
            auth_header = f"Basic {credentials}"
            request_headers['Authorization'] = auth_header

        # Prepare kwargs
        kwargs = {
            'headers': request_headers,
            'params': params,
            'timeout': aiohttp.ClientTimeout(total=timeout_val),
            'allow_redirects': follow_redirects,
            'ssl': self.verify_ssl
        }

        # Add body
        if json_data is not None:
            kwargs['json'] = json_data
        elif data is not None:
            kwargs['data'] = data

        # Make request with retry
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start_time = datetime.utcnow()

                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        elapsed = (datetime.utcnow() - start_time).total_seconds()

                        # Read response body
                        body_bytes = await response.read()
                        body_text = body_bytes.decode('utf-8', errors='ignore')

                        # Try to parse JSON
                        response_json = None
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            try:
                                response_json = json.loads(body_text)
                            except json.JSONDecodeError:
                                pass

                        result = {
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'body': body_bytes,
                            'text': body_text,
                            'json': response_json,
                            'elapsed': elapsed,
                            'url': str(response.url),
                            'method': method,
                            'ok': 200 <= response.status < 300
                        }

                        logger.info(
                            f"HTTP {method} {url} -> {response.status} "
                            f"({elapsed:.2f}s)"
                        )

                        return result

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    f"HTTP {method} {url} timeout (attempt {attempt + 1}/{self.max_retries})"
                )
            except Exception as e:
                last_error = e
                logger.error(
                    f"HTTP {method} {url} failed: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_backoff ** attempt)

        # All retries failed
        raise Exception(f"HTTP request failed after {self.max_retries} attempts: {last_error}")

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request('POST', url, **kwargs)

    async def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request('PUT', url, **kwargs)

    async def patch(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make PATCH request."""
        return await self.request('PATCH', url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request('DELETE', url, **kwargs)

    async def head(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make HEAD request."""
        return await self.request('HEAD', url, **kwargs)

    async def options(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make OPTIONS request."""
        return await self.request('OPTIONS', url, **kwargs)

    async def download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Download a file from URL.

        Args:
            url: Source URL
            output_path: Destination file path
            chunk_size: Download chunk size
            **kwargs: Additional request parameters

        Returns:
            Dictionary with download info
        """
        import aiofiles

        start_time = datetime.utcnow()
        total_bytes = 0

        # Remove data/json from kwargs as we're streaming
        kwargs.pop('data', None)
        kwargs.pop('json_data', None)

        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': self.user_agent,
            **self.default_headers
        })
        kwargs['headers'] = headers

        timeout_val = kwargs.pop('timeout', self.timeout)
        kwargs['timeout'] = aiohttp.ClientTimeout(total=timeout_val)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as response:
                response.raise_for_status()

                async with aiofiles.open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        total_bytes += len(chunk)

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        return {
            'status': 'success',
            'output_path': output_path,
            'total_bytes': total_bytes,
            'elapsed': elapsed,
            'url': url
        }


# Singleton instance
_http_client_instance = None


def get_http_client_tool(config: Optional[Dict[str, Any]] = None) -> HTTPClientTool:
    """Get or create singleton HTTP client tool instance."""
    global _http_client_instance
    if _http_client_instance is None:
        _http_client_instance = HTTPClientTool(config)
    return _http_client_instance
