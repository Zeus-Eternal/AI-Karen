"""
Agent Echo Core Service

This service provides integration with the EchoCore platform for agents,
allowing them to leverage advanced memory and reasoning capabilities.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import requests
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class EchoCoreOperation(Enum):
    """Enumeration of EchoCore operations."""
    MEMORY_STORE = "memory_store"
    MEMORY_RETRIEVE = "memory_retrieve"
    MEMORY_SEARCH = "memory_search"
    MEMORY_DELETE = "memory_delete"
    REASONING_EXECUTE = "reasoning_execute"
    KNOWLEDGE_QUERY = "knowledge_query"
    EMBEDDING_GENERATE = "embedding_generate"
    SIMILARITY_CALCULATE = "similarity_calculate"
    CONCEPT_EXTRACT = "concept_extract"
    ENTITY_RECOGNIZE = "entity_recognize"


class EchoCoreResponseStatus(Enum):
    """Enumeration of EchoCore response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"


@dataclass
class EchoCoreRequest:
    """A request to EchoCore."""
    operation: EchoCoreOperation
    parameters: Dict[str, Any] = field(default_factory=dict)
    data: Any = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EchoCoreResponse:
    """A response from EchoCore."""
    request_id: str
    operation: EchoCoreOperation
    status: EchoCoreResponseStatus
    data: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0


@dataclass
class EchoCoreConfig:
    """Configuration for EchoCore integration."""
    api_endpoint: str = "https://api.echocore.example.com/v1"
    api_key: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_async: bool = True
    enable_caching: bool = True
    cache_ttl: float = 300.0  # 5 minutes
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: float = 60.0  # 1 minute
    enable_metrics: bool = True


class AgentEchoCore:
    """
    Provides integration with the EchoCore platform for agents.
    
    This class is responsible for:
    - Communicating with the EchoCore API
    - Handling EchoCore operations
    - Managing EchoCore authentication and rate limiting
    - Caching EchoCore responses
    - Providing metrics for EchoCore operations
    """
    
    def __init__(self, config: Optional[EchoCoreConfig] = None):
        self._config = config or EchoCoreConfig()
        self._session = None
        self._async_session = None
        self._cache: Dict[str, Tuple[datetime, EchoCoreResponse]] = {}
        self._rate_limit_timestamps: List[float] = []
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        
        # Callbacks for EchoCore events
        self._on_request: Optional[Callable[[EchoCoreRequest], None]] = None
        self._on_response: Optional[Callable[[EchoCoreResponse], None]] = None
        self._on_error: Optional[Callable[[EchoCoreRequest, str], None]] = None
    
    def initialize(self) -> None:
        """Initialize the EchoCore client."""
        # Create HTTP session
        self._session = requests.Session()
        
        # Set up authentication
        if self._config.api_key:
            self._session.headers.update({
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json"
            })
        
        # Create async HTTP session if async is enabled
        if self._config.enable_async:
            headers = {}
            if self._config.api_key:
                headers = {
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json"
                }
            self._async_session = aiohttp.ClientSession(headers=headers)
        
        logger.info("Initialized EchoCore client")
    
    def close(self) -> None:
        """Close the EchoCore client."""
        if self._session:
            self._session.close()
        
        if self._async_session:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_session.close())
        
        logger.info("Closed EchoCore client")
    
    def execute_operation(self, request: EchoCoreRequest) -> EchoCoreResponse:
        """
        Execute an EchoCore operation synchronously.
        
        Args:
            request: EchoCore request
            
        Returns:
            EchoCore response
        """
        if not self._session:
            self.initialize()
        
        # Check rate limit
        if self._config.enable_rate_limiting:
            self._check_rate_limit()
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if self._config.enable_caching and cache_key in self._cache:
            cached_time, cached_response = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._config.cache_ttl:
                logger.debug(f"Cache hit for operation: {request.operation.value}")
                return cached_response
        
        # Call request callback if set
        if self._on_request:
            self._on_request(request)
        
        # Record start time
        start_time = datetime.now()
        
        try:
            # Prepare request
            url = f"{self._config.api_endpoint}/{request.operation.value}"
            payload = {
                "request_id": request.request_id,
                "operation": request.operation.value,
                "parameters": request.parameters,
                "data": request.data,
                "timestamp": request.timestamp.isoformat()
            }
            
            # Execute request with retries
            response = None
            for attempt in range(self._config.max_retries + 1):
                try:
                    if self._session is not None:
                        response = self._session.post(
                            url,
                            json=payload,
                            timeout=self._config.timeout
                        )
                        break
                    else:
                        raise Exception("Session not initialized")
                except (requests.Timeout, requests.ConnectionError) as e:
                    if attempt < self._config.max_retries:
                        logger.warning(f"EchoCore request failed (attempt {attempt + 1}/{self._config.max_retries}): {str(e)}")
                        time.sleep(self._config.retry_delay)
                    else:
                        raise
            
            # Process response
            if response is None:
                raise Exception("No response from EchoCore")
            
            response_data = response.json()
            
            # Create EchoCore response
            echo_response = EchoCoreResponse(
                request_id=request.request_id,
                operation=request.operation,
                status=EchoCoreResponseStatus(response_data.get("status", "error")),
                data=response_data.get("data"),
                error=response_data.get("error"),
                timestamp=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache response if successful
            if self._config.enable_caching and echo_response.status == EchoCoreResponseStatus.SUCCESS:
                self._cache[cache_key] = (datetime.now(), echo_response)
            
            # Record metrics
            if self._config.enable_metrics:
                self._record_metrics(request, echo_response)
            
            # Call response callback if set
            if self._on_response:
                self._on_response(echo_response)
            
            return echo_response
            
        except Exception as e:
            # Create error response
            error_response = EchoCoreResponse(
                request_id=request.request_id,
                operation=request.operation,
                status=EchoCoreResponseStatus.ERROR,
                error=str(e),
                timestamp=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Call error callback if set
            if self._on_error:
                self._on_error(request, str(e))
            
            logger.error(f"EchoCore operation failed: {str(e)}")
            return error_response
    
    async def execute_operation_async(self, request: EchoCoreRequest) -> EchoCoreResponse:
        """
        Execute an EchoCore operation asynchronously.
        
        Args:
            request: EchoCore request
            
        Returns:
            EchoCore response
        """
        if not self._config.enable_async:
            raise ValueError("Async operations are not enabled")
        
        if not self._async_session:
            self.initialize()
        
        # Check rate limit
        if self._config.enable_rate_limiting:
            self._check_rate_limit()
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if self._config.enable_caching and cache_key in self._cache:
            cached_time, cached_response = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._config.cache_ttl:
                logger.debug(f"Cache hit for operation: {request.operation.value}")
                return cached_response
        
        # Call request callback if set
        if self._on_request:
            self._on_request(request)
        
        # Record start time
        start_time = datetime.now()
        
        try:
            # Prepare request
            url = f"{self._config.api_endpoint}/{request.operation.value}"
            payload = {
                "request_id": request.request_id,
                "operation": request.operation.value,
                "parameters": request.parameters,
                "data": request.data,
                "timestamp": request.timestamp.isoformat()
            }
            
            # Execute request with retries
            response = None
            for attempt in range(self._config.max_retries + 1):
                try:
                    if self._async_session is not None:
                        response = await self._async_session.post(
                            url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=self._config.timeout)
                        )
                        break
                    else:
                        raise Exception("Async session not initialized")
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    if attempt < self._config.max_retries:
                        logger.warning(f"EchoCore async request failed (attempt {attempt + 1}/{self._config.max_retries}): {str(e)}")
                        await asyncio.sleep(self._config.retry_delay)
                    else:
                        raise
            
            # Process response
            if response is None:
                raise Exception("No response from EchoCore")
            
            response_data = await response.json()
            
            # Create EchoCore response
            echo_response = EchoCoreResponse(
                request_id=request.request_id,
                operation=request.operation,
                status=EchoCoreResponseStatus(response_data.get("status", "error")),
                data=response_data.get("data"),
                error=response_data.get("error"),
                timestamp=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache response if successful
            if self._config.enable_caching and echo_response.status == EchoCoreResponseStatus.SUCCESS:
                self._cache[cache_key] = (datetime.now(), echo_response)
            
            # Record metrics
            if self._config.enable_metrics:
                self._record_metrics(request, echo_response)
            
            # Call response callback if set
            if self._on_response:
                self._on_response(echo_response)
            
            return echo_response
            
        except Exception as e:
            # Create error response
            error_response = EchoCoreResponse(
                request_id=request.request_id,
                operation=request.operation,
                status=EchoCoreResponseStatus.ERROR,
                error=str(e),
                timestamp=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Call error callback if set
            if self._on_error:
                self._on_error(request, str(e))
            
            logger.error(f"EchoCore async operation failed: {str(e)}")
            return error_response
    
    def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EchoCoreResponse:
        """
        Store a memory in EchoCore.
        
        Args:
            content: Content of the memory
            memory_type: Type of the memory
            tags: Tags for the memory
            metadata: Metadata for the memory
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.MEMORY_STORE,
            parameters={
                "memory_type": memory_type,
                "tags": tags or [],
                "metadata": metadata or {}
            },
            data=content
        )
        
        return self.execute_operation(request)
    
    def retrieve_memory(self, memory_id: str) -> EchoCoreResponse:
        """
        Retrieve a memory from EchoCore.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.MEMORY_RETRIEVE,
            parameters={
                "memory_id": memory_id
            }
        )
        
        return self.execute_operation(request)
    
    def search_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> EchoCoreResponse:
        """
        Search for memories in EchoCore.
        
        Args:
            query: Search query
            memory_type: Type of memories to search
            tags: Tags to filter by
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.MEMORY_SEARCH,
            parameters={
                "query": query,
                "memory_type": memory_type,
                "tags": tags or [],
                "limit": limit,
                "offset": offset
            }
        )
        
        return self.execute_operation(request)
    
    def delete_memory(self, memory_id: str) -> EchoCoreResponse:
        """
        Delete a memory from EchoCore.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.MEMORY_DELETE,
            parameters={
                "memory_id": memory_id
            }
        )
        
        return self.execute_operation(request)
    
    def execute_reasoning(
        self,
        reasoning_type: str,
        premises: List[str],
        context: Optional[str] = None
    ) -> EchoCoreResponse:
        """
        Execute reasoning in EchoCore.
        
        Args:
            reasoning_type: Type of reasoning
            premises: Premises for reasoning
            context: Context for reasoning
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.REASONING_EXECUTE,
            parameters={
                "reasoning_type": reasoning_type,
                "context": context
            },
            data=premises
        )
        
        return self.execute_operation(request)
    
    def query_knowledge(
        self,
        query: str,
        knowledge_base: Optional[str] = None,
        limit: int = 10
    ) -> EchoCoreResponse:
        """
        Query knowledge in EchoCore.
        
        Args:
            query: Knowledge query
            knowledge_base: Knowledge base to query
            limit: Maximum number of results
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.KNOWLEDGE_QUERY,
            parameters={
                "query": query,
                "knowledge_base": knowledge_base,
                "limit": limit
            }
        )
        
        return self.execute_operation(request)
    
    def generate_embedding(self, text: str, model: Optional[str] = None) -> EchoCoreResponse:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.EMBEDDING_GENERATE,
            parameters={
                "model": model
            },
            data=text
        )
        
        return self.execute_operation(request)
    
    def calculate_similarity(self, text1: str, text2: str, model: Optional[str] = None) -> EchoCoreResponse:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            model: Embedding model to use
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.SIMILARITY_CALCULATE,
            parameters={
                "model": model
            },
            data=[text1, text2]
        )
        
        return self.execute_operation(request)
    
    def extract_concepts(self, text: str, min_confidence: float = 0.5) -> EchoCoreResponse:
        """
        Extract concepts from text.
        
        Args:
            text: Text to extract concepts from
            min_confidence: Minimum confidence for concepts
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.CONCEPT_EXTRACT,
            parameters={
                "min_confidence": min_confidence
            },
            data=text
        )
        
        return self.execute_operation(request)
    
    def recognize_entities(self, text: str, entity_types: Optional[List[str]] = None) -> EchoCoreResponse:
        """
        Recognize entities in text.
        
        Args:
            text: Text to recognize entities in
            entity_types: Types of entities to recognize
            
        Returns:
            EchoCore response
        """
        request = EchoCoreRequest(
            operation=EchoCoreOperation.ENTITY_RECOGNIZE,
            parameters={
                "entity_types": entity_types or []
            },
            data=text
        )
        
        return self.execute_operation(request)
    
    def set_echo_core_callbacks(
        self,
        on_request: Optional[Callable[[EchoCoreRequest], None]] = None,
        on_response: Optional[Callable[[EchoCoreResponse], None]] = None,
        on_error: Optional[Callable[[EchoCoreRequest, str], None]] = None
    ) -> None:
        """Set callbacks for EchoCore events."""
        self._on_request = on_request
        self._on_response = on_response
        self._on_error = on_error
    
    def clear_cache(self) -> None:
        """Clear the EchoCore response cache."""
        self._cache.clear()
        logger.debug("Cleared EchoCore response cache")
    
    def get_metrics(self, operation: Optional[EchoCoreOperation] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get metrics for EchoCore operations.
        
        Args:
            operation: Operation to get metrics for
            limit: Maximum number of metrics to return
            
        Returns:
            List of metrics
        """
        if operation:
            metrics = self._metrics.get(operation.value, [])
        else:
            metrics = []
            for op_metrics in self._metrics.values():
                metrics.extend(op_metrics)
        
        # Sort by timestamp (newest first)
        metrics.sort(key=lambda m: m["timestamp"], reverse=True)
        
        # Apply limit
        return metrics[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about EchoCore operations.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_operations": sum(len(metrics) for metrics in self._metrics.values()),
            "operations_by_type": {},
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "cache_size": len(self._cache),
            "cache_hit_rate": 0.0,
            "rate_limit_status": "ok"
        }
        
        # Count operations by type
        for operation, metrics in self._metrics.items():
            stats["operations_by_type"][operation] = len(metrics)
        
        # Calculate success rate
        total_operations = stats["total_operations"]
        if total_operations > 0:
            successful_operations = 0
            total_response_time = 0.0
            
            for metrics in self._metrics.values():
                for metric in metrics:
                    if metric["status"] == EchoCoreResponseStatus.SUCCESS.value:
                        successful_operations += 1
                    
                    if "response_time" in metric:
                        total_response_time += metric["response_time"]
            
            stats["success_rate"] = successful_operations / total_operations
            stats["average_response_time"] = total_response_time / total_operations
        
        # Calculate cache hit rate
        # In a real implementation, this would track cache hits and misses
        stats["cache_hit_rate"] = 0.8  # Placeholder
        
        # Check rate limit status
        if self._config.enable_rate_limiting:
            now = time.time()
            recent_requests = [t for t in self._rate_limit_timestamps if now - t < self._config.rate_limit_period]
            if len(recent_requests) >= self._config.rate_limit_requests:
                stats["rate_limit_status"] = "limited"
        
        return stats
    
    def _get_cache_key(self, request: EchoCoreRequest) -> str:
        """Get a cache key for a request."""
        # Create a hash of the request
        import hashlib
        request_str = json.dumps({
            "operation": request.operation.value,
            "parameters": request.parameters,
            "data": request.data
        }, sort_keys=True)
        
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _check_rate_limit(self) -> None:
        """Check if the rate limit has been exceeded."""
        now = time.time()
        
        # Remove old timestamps
        self._rate_limit_timestamps = [
            t for t in self._rate_limit_timestamps
            if now - t < self._config.rate_limit_period
        ]
        
        # Check if rate limit exceeded
        if len(self._rate_limit_timestamps) >= self._config.rate_limit_requests:
            # Calculate time until next request is allowed
            oldest_request = min(self._rate_limit_timestamps)
            wait_time = self._config.rate_limit_period - (now - oldest_request)
            
            if wait_time > 0:
                raise Exception(f"Rate limit exceeded. Wait {wait_time:.2f} seconds.")
        
        # Add current timestamp
        self._rate_limit_timestamps.append(now)
    
    def _record_metrics(self, request: EchoCoreRequest, response: EchoCoreResponse) -> None:
        """Record metrics for an operation."""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "operation": request.operation.value,
            "status": response.status.value,
            "response_time": response.response_time,
            "error": response.error
        }
        
        if request.operation.value not in self._metrics:
            self._metrics[request.operation.value] = []
        
        self._metrics[request.operation.value].append(metric)
        
        # Limit the number of metrics stored
        if len(self._metrics[request.operation.value]) > 1000:
            self._metrics[request.operation.value] = self._metrics[request.operation.value][-1000:]