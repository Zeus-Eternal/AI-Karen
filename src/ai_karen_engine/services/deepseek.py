"""
DeepSeekClient: Enterprise-Grade Client for DeepSeek API
- Complete sync/async interfaces with streaming support
- Advanced error handling and automatic retries
- Comprehensive observability with metrics and logging
- Connection pooling and resource management
- Configurable via environment or explicit settings
"""

import os
import logging
import time
from typing import Any, Dict, Optional, List, Generator, AsyncGenerator
import httpx
from pydantic import BaseModel, Field, validator, HttpUrl, AnyUrl
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from functools import wraps
import json

# === Structured Logging Configuration ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deepseek_client")
logger.setLevel(logging.INFO if os.getenv("ENV") == "production" else logging.DEBUG)

# === Observability Integration ===
class Metrics:
    """Metrics facade with Prometheus or dummy fallback"""
    def __init__(self):
        self.enabled = False
        self._init_metrics()
    
    def _init_metrics(self):
        try:
            from prometheus_client import Counter, Histogram, Gauge
            self.requests = Counter(
                "deepseek_requests_total",
                "Total DeepSeek API requests",
                ["model", "endpoint", "status"]
            )
            self.latency = Histogram(
                "deepseek_latency_seconds",
                "DeepSeek API request latency",
                ["model", "endpoint"]
            )
            self.errors = Counter(
                "deepseek_errors_total",
                "Total DeepSeek API errors",
                ["error_type", "endpoint"]
            )
            self.in_flight = Gauge(
                "deepseek_in_flight_requests",
                "Current in-flight requests to DeepSeek",
                ["endpoint"]
            )
            self.enabled = True
        except ImportError:
            logger.warning("Prometheus client not available - metrics disabled")
            self.requests = self.latency = self.errors = self.in_flight = self._dummy_metric()
    
    class _dummy_metric:
        def inc(self, n=1): pass
        def labels(self, **kwargs): return self
        def time(self): 
            class Ctx: 
                def __enter__(self): return self
                def __exit__(self, *a): pass
            return Ctx()
        def dec(self): pass

metrics = Metrics()

# === Configuration Model ===
class DeepSeekConfig(BaseModel):
    """Validated configuration for DeepSeekClient"""
    api_url: HttpUrl = Field(
        default="https://api.deepseek.com/v1/chat/completions",
        description="Base URL for chat completions"
    )
    models_url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional separate URL for model listing"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    timeout: int = Field(
        default=30,
        gt=0,
        le=300,
        description="Request timeout in seconds (1-300)"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum retry attempts (0-5)"
    )
    retry_base_delay: float = Field(
        default=1.0,
        gt=0,
        le=5,
        description="Base delay for exponential backoff in seconds"
    )
    max_retry_delay: float = Field(
        default=10.0,
        gt=0,
        le=30,
        description="Maximum retry delay in seconds"
    )
    default_model: str = Field(
        default="deepseek-chat",
        min_length=1,
        description="Default model name"
    )
    keepalive: int = Field(
        default=60,
        description="HTTP keepalive timeout in seconds"
    )
    max_connections: int = Field(
        default=100,
        description="Maximum HTTP connection pool size"
    )

    @validator('models_url', pre=True, always=True)
    def set_models_url(cls, v, values):
        if v is None and 'api_url' in values:
            return AnyUrl(f"{str(values['api_url']).replace('/chat/completions', '/models')}")
        return v

# === Retryable Exceptions ===
RETRYABLE_EXCEPTIONS = (
    httpx.NetworkError,
    httpx.TimeoutException,
    httpx.RemoteProtocolError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
    json.JSONDecodeError
)

# === Decorators ===
def observe_request(endpoint: str):
    """Decorator to add metrics and logging to API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            model = kwargs.get('model', args[0].config.default_model)
            metrics.in_flight.labels(endpoint=endpoint).inc()
            metrics.requests.labels(model=model, endpoint=endpoint, status="started").inc()
            start_time = time.monotonic()
            
            try:
                with metrics.latency.labels(model=model, endpoint=endpoint).time():
                    result = func(*args, **kwargs)
                metrics.requests.labels(model=model, endpoint=endpoint, status="success").inc()
                return result
            except Exception as e:
                error_type = "network" if isinstance(e, httpx.NetworkError) else "api"
                metrics.errors.labels(error_type=error_type, endpoint=endpoint).inc()
                metrics.requests.labels(model=model, endpoint=endpoint, status="failed").inc()
                logger.error(
                    "API request failed",
                    exc_info=True,
                    extra={
                        "endpoint": endpoint,
                        "model": model,
                        "duration_sec": time.monotonic() - start_time,
                        "error": str(e)
                    }
                )
                raise
            finally:
                metrics.in_flight.labels(endpoint=endpoint).dec()
        return wrapper
    return decorator

# === Main Client Implementation ===
class DeepSeekClient:
    """
    Production-grade client for DeepSeek API with:
    - Connection pooling and keepalive
    - Comprehensive observability
    - Automatic retries with backoff
    - Model management capabilities
    """
    
    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or self._load_config()
        self._client = None
        self._async_client = None
        logger.info(f"Initialized DeepSeekClient with config: {self.config}")

    @staticmethod
    def _load_config() -> DeepSeekConfig:
        """Load configuration with environment variable fallbacks"""
        return DeepSeekConfig(
            api_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"),
            models_url=os.getenv("DEEPSEEK_MODELS_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30")),
            max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3")),
            retry_base_delay=float(os.getenv("DEEPSEEK_RETRY_DELAY", "1.0")),
            max_retry_delay=float(os.getenv("DEEPSEEK_MAX_RETRY_DELAY", "10.0")),
            default_model=os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"),
            keepalive=int(os.getenv("DEEPSEEK_KEEPALIVE", "60")),
            max_connections=int(os.getenv("DEEPSEEK_MAX_CONNECTIONS", "100"))
        )

    @property
    def client(self) -> httpx.Client:
        """Lazy-loaded synchronous HTTP client with connection pooling"""
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_connections // 2
            )
            self._client = httpx.Client(
                timeout=self.config.timeout,
                limits=limits,
                transport=httpx.HTTPTransport(retries=self.config.max_retries)
            )
        return self._client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Lazy-loaded async HTTP client with connection pooling"""
        if self._async_client is None:
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_connections // 2
            )
            self._async_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                limits=limits,
                transport=httpx.AsyncHTTPTransport(retries=self.config.max_retries)
            )
        return self._async_client

    def _headers(self) -> Dict[str, str]:
        """Standard headers for all requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DeepSeekClient/1.0",
            "Accept": "application/json"
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def close(self):
        """Clean up client resources"""
        if self._client:
            self._client.close()
        if self._async_client:
            import asyncio
            asyncio.run(self._async_client.aclose())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # === Core Chat Methods ===
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    @observe_request("chat")
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous chat completion with automatic retries
        
        Args:
            messages: Conversation history as message dicts
            model: Model name (defaults to config)
            **kwargs: Additional API parameters
            
        Returns:
            Dict with completion response
            
        Raises:
            ValueError: For invalid input
            httpx.HTTPStatusError: For API errors
        """
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be non-empty list")
        
        model = model or self.config.default_model
        payload = {
            "model": model,
            "messages": messages,
            **{k: v for k, v in kwargs.items() if v is not None}
        }

        response = self.client.post(
            str(self.config.api_url),
            json=payload,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    @observe_request("chat")
    async def achat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of chat completion"""
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be non-empty list")
        
        model = model or self.config.default_model
        payload = {
            "model": model,
            "messages": messages,
            **{k: v for k, v in kwargs.items() if v is not None}
        }

        response = await self.async_client.post(
            str(self.config.api_url),
            json=payload,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    # === Streaming Methods ===
    @observe_request("stream_chat")
    def streaming_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream chat completion chunks
        
        Yields:
            JSON strings with completion chunks
            
        Raises:
            ValueError: For invalid input
            httpx.HTTPStatusError: For API errors
        """
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be non-empty list")
        
        model = model or self.config.default_model
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None}
        }

        with self.client.stream(
            "POST",
            str(self.config.api_url),
            json=payload,
            headers=self._headers()
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_text():
                if chunk.strip():
                    yield chunk

    @observe_request("stream_chat")
    async def astreaming_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Async version of streaming chat"""
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be non-empty list")
        
        model = model or self.config.default_model
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None}
        }

        async with self.async_client.stream(
            "POST",
            str(self.config.api_url),
            json=payload,
            headers=self._headers()
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk.strip():
                    yield chunk

    # === Model Management ===
    @observe_request("list_models")
    def available_models(self) -> List[str]:
        """List available models from DeepSeek API"""
        response = self.client.get(
            str(self.config.models_url),
            headers=self._headers()
        )
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "data" in data:
            return sorted([m["id"] for m in data["data"] if "id" in m])
        return []

    @observe_request("model_info")
    def model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        # Note: DeepSeek API may not have a model info endpoint
        # This is a placeholder for future compatibility
        return {"name": model_name, "status": "info_not_available"}

    # === Health Monitoring ===
    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check
        
        Returns:
            Dict with status and system information
        """
        start_time = time.monotonic()
        status = {
            "timestamp": time.time(),
            "status": "unknown",
            "components": {}
        }

        # Check API connectivity
        try:
            ping_response = self.chat(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            status["components"]["api"] = {
                "status": "healthy",
                "response_time": time.monotonic() - start_time,
                "model": ping_response.get("model")
            }
        except Exception as e:
            status["components"]["api"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # Check model availability
        try:
            models = self.available_models()
            status["components"]["models"] = {
                "status": "healthy",
                "available": len(models),
                "default_model_available": self.config.default_model in models
            }
        except Exception as e:
            status["components"]["models"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # Determine overall status
        if all(c["status"] == "healthy" for c in status["components"].values()):
            status["status"] = "healthy"
        else:
            status["status"] = "degraded" if any(
                c["status"] == "healthy" for c in status["components"].values()
            ) else "unhealthy"

        return status

# Global instance for simple usage
deepseek_client = DeepSeekClient()