"""
LLM Generation Pipeline Optimization - Task 8.2
Optimizes LLM generation to achieve p95 first-token latency < 1.2 seconds
with model preloading, warming strategies, and local-first routing.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncIterator, Union, Callable
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Types of LLM models"""
    LOCAL = "local"           # llama.cpp, Transformers
    REMOTE_API = "remote_api" # OpenAI, Anthropic, Gemini
    CACHED = "cached"         # Pre-loaded models
    STREAMING = "streaming"   # Streaming-optimized models

class WarmupStrategy(str, Enum):
    """Model warming strategies"""
    EAGER = "eager"           # Warm up immediately on startup
    LAZY = "lazy"            # Warm up on first request
    SCHEDULED = "scheduled"   # Warm up on schedule
    ADAPTIVE = "adaptive"     # Warm up based on usage patterns

@dataclass
class ModelConfig:
    """Configuration for an LLM model"""
    name: str
    provider: str
    model_type: ModelType
    warmup_strategy: WarmupStrategy
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: float = 30.0
    
    # Performance settings
    batch_size: int = 1
    max_concurrent_requests: int = 10
    preload_enabled: bool = True
    cache_responses: bool = True
    
    # Optimization settings
    use_gpu: bool = True
    quantization: Optional[str] = None  # "int8", "int4", "fp16"
    context_length: int = 4096
    
    # Warmup settings
    warmup_prompts: List[str] = field(default_factory=lambda: [
        "Hello, how are you?",
        "What is the weather like today?",
        "Explain quantum computing in simple terms."
    ])

@dataclass
class GenerationMetrics:
    """Metrics for LLM generation performance"""
    model_name: str
    provider: str
    first_token_latency_ms: float
    total_latency_ms: float
    tokens_generated: int
    tokens_per_second: float
    cache_hit: bool
    error: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ModelState:
    """State tracking for a model"""
    name: str
    is_loaded: bool = False
    is_warmed: bool = False
    last_used: Optional[float] = None
    load_time: Optional[float] = None
    warmup_time: Optional[float] = None
    request_count: int = 0
    error_count: int = 0
    avg_first_token_latency: float = 0.0
    avg_total_latency: float = 0.0

class ModelPreloader:
    """Handles model preloading and warming"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.preload_tasks: Dict[str, asyncio.Task] = {}
        self.warmup_tasks: Dict[str, asyncio.Task] = {}
        
    async def preload_model(self, config: ModelConfig) -> bool:
        """Preload a model for faster first request"""
        try:
            logger.info(f"Preloading model: {config.name}")
            start_time = time.time()
            
            # Simulate model loading (in production, this would load the actual model)
            if config.model_type == ModelType.LOCAL:
                # For local models, actually load into memory
                await self._load_local_model(config)
            elif config.model_type == ModelType.REMOTE_API:
                # For remote APIs, validate connection and cache auth
                await self._validate_remote_api(config)
            
            load_time = time.time() - start_time
            logger.info(f"Model {config.name} preloaded in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to preload model {config.name}: {e}")
            return False
    
    async def _load_local_model(self, config: ModelConfig):
        """Load local model into memory"""
        # This would interface with llama.cpp, Transformers, or other local providers
        # For now, simulate loading time
        await asyncio.sleep(0.1)  # Simulate load time
        
        # In production, this would:
        # 1. Load model weights into GPU/CPU memory
        # 2. Initialize tokenizer
        # 3. Set up inference engine
        # 4. Apply quantization if specified
        
        logger.debug(f"Local model {config.name} loaded with config: {config}")
    
    async def _validate_remote_api(self, config: ModelConfig):
        """Validate remote API connection"""
        # This would validate API keys and endpoints
        # For now, simulate validation
        await asyncio.sleep(0.05)  # Simulate API validation
        
        logger.debug(f"Remote API {config.name} validated")
    
    async def warm_model(self, config: ModelConfig, provider_instance: Any) -> float:
        """Warm up a model with test prompts"""
        try:
            logger.info(f"Warming up model: {config.name}")
            start_time = time.time()
            
            # Run warmup prompts
            for prompt in config.warmup_prompts:
                try:
                    # Generate a small response to warm up the model
                    if hasattr(provider_instance, 'generate_response'):
                        await provider_instance.generate_response(
                            prompt, 
                            max_tokens=50,  # Small response for warmup
                            temperature=config.temperature
                        )
                    else:
                        # Fallback for different provider interfaces
                        await self._generic_warmup_call(provider_instance, prompt)
                    
                    # Small delay between warmup calls
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Warmup prompt failed for {config.name}: {e}")
                    continue
            
            warmup_time = time.time() - start_time
            logger.info(f"Model {config.name} warmed up in {warmup_time:.2f}s")
            
            return warmup_time
            
        except Exception as e:
            logger.error(f"Failed to warm up model {config.name}: {e}")
            return 0.0
    
    async def _generic_warmup_call(self, provider_instance: Any, prompt: str):
        """Generic warmup call for different provider interfaces"""
        # Try different common method names
        for method_name in ['generate', 'chat', 'complete', 'invoke']:
            if hasattr(provider_instance, method_name):
                method = getattr(provider_instance, method_name)
                try:
                    await method(prompt)
                    return
                except Exception:
                    continue
        
        # If no method worked, just log
        logger.debug(f"No suitable method found for warmup on {type(provider_instance)}")

class ResponseCache:
    """Cache for LLM responses to improve latency"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def _generate_cache_key(self, prompt: str, model_name: str, **kwargs) -> str:
        """Generate cache key for a request"""
        # Create a deterministic key from prompt and parameters
        key_data = {
            "prompt": prompt,
            "model": model_name,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        # Sort for consistency
        key_str = json.dumps(key_data, sort_keys=True)
        return str(hash(key_str))
    
    def get(self, prompt: str, model_name: str, **kwargs) -> Optional[str]:
        """Get cached response if available and not expired"""
        cache_key = self._generate_cache_key(prompt, model_name, **kwargs)
        
        with self.lock:
            if cache_key not in self.cache:
                return None
            
            cached_data = self.cache[cache_key]
            cache_time = cached_data.get("timestamp", 0)
            
            # Check if expired
            if time.time() - cache_time > self.ttl_seconds:
                del self.cache[cache_key]
                self.access_times.pop(cache_key, None)
                return None
            
            # Update access time
            self.access_times[cache_key] = time.time()
            
            return cached_data.get("response")
    
    def put(self, prompt: str, model_name: str, response: str, **kwargs):
        """Cache a response"""
        cache_key = self._generate_cache_key(prompt, model_name, **kwargs)
        
        with self.lock:
            # Evict old entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[cache_key] = {
                "response": response,
                "timestamp": time.time()
            }
            self.access_times[cache_key] = time.time()
    
    def _evict_oldest(self):
        """Evict the oldest cache entry"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.cache.pop(oldest_key, None)
        self.access_times.pop(oldest_key, None)
    
    def clear(self):
        """Clear the cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": 0.0,  # Would need to track hits/misses
                "ttl_seconds": self.ttl_seconds
            }

class OptimizedLLMService:
    """Optimized LLM service with preloading, warming, and caching"""
    
    def __init__(self, configs: Optional[List[ModelConfig]] = None):
        self.configs = configs or self._get_default_configs()
        self.model_states: Dict[str, ModelState] = {}
        self.preloader = ModelPreloader()
        self.response_cache = ResponseCache()
        
        # Performance tracking
        self.metrics_history: List[GenerationMetrics] = []
        self.performance_targets = {
            "first_token_latency_p95_ms": 1200.0,  # 1.2 seconds
            "total_latency_p95_ms": 5000.0,        # 5 seconds
            "cache_hit_rate_target": 0.3,          # 30% cache hit rate
        }
        
        # Initialize model states
        for config in self.configs:
            self.model_states[config.name] = ModelState(name=config.name)
        
        # Start background tasks
        self._start_background_tasks()
    
    def _get_default_configs(self) -> List[ModelConfig]:
        """Get default model configurations"""
        return [
            ModelConfig(
                name="llamacpp:tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                provider="llamacpp",
                model_type=ModelType.LOCAL,
                warmup_strategy=WarmupStrategy.EAGER,
                preload_enabled=True,
                use_gpu=False,
                quantization="q4_k_m"
            ),
            ModelConfig(
                name="openai:gpt-4o-mini",
                provider="openai",
                model_type=ModelType.REMOTE_API,
                warmup_strategy=WarmupStrategy.LAZY,
                preload_enabled=False,
                cache_responses=True
            ),
            ModelConfig(
                name="anthropic:claude-3-haiku",
                provider="anthropic",
                model_type=ModelType.REMOTE_API,
                warmup_strategy=WarmupStrategy.LAZY,
                preload_enabled=False,
                cache_responses=True
            )
        ]
    
    def _start_background_tasks(self):
        """Start background optimization tasks"""
        asyncio.create_task(self._preload_models())
        asyncio.create_task(self._performance_monitor_loop())
    
    async def _preload_models(self):
        """Preload models that are configured for preloading"""
        preload_tasks = []
        
        for config in self.configs:
            if config.preload_enabled:
                task = asyncio.create_task(self._preload_and_warm_model(config))
                preload_tasks.append(task)
        
        if preload_tasks:
            results = await asyncio.gather(*preload_tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            logger.info(f"Preloaded {successful}/{len(preload_tasks)} models")
    
    async def _preload_and_warm_model(self, config: ModelConfig) -> bool:
        """Preload and warm a specific model"""
        try:
            state = self.model_states[config.name]
            
            # Preload model
            if await self.preloader.preload_model(config):
                state.is_loaded = True
                state.load_time = time.time()
            
            # Warm up model if configured
            if config.warmup_strategy == WarmupStrategy.EAGER:
                # Get provider instance for warming
                provider_instance = await self._get_provider_instance(config)
                if provider_instance:
                    warmup_time = await self.preloader.warm_model(config, provider_instance)
                    if warmup_time > 0:
                        state.is_warmed = True
                        state.warmup_time = warmup_time
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to preload/warm model {config.name}: {e}")
            return False
    
    async def _get_provider_instance(self, config: ModelConfig) -> Optional[Any]:
        """Get provider instance for a model config"""
        try:
            # This would get the actual provider instance
            # For now, return a mock object
            from ai_karen_engine.integrations.llm_registry import get_registry
            
            registry = get_registry()
            provider = registry.get_provider(config.provider, model=config.name)
            
            return provider
            
        except Exception as e:
            logger.error(f"Failed to get provider instance for {config.name}: {e}")
            return None
    
    async def generate_optimized(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        stream: bool = True,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate response with optimization for first-token latency
        """
        start_time = time.time()
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Select best model if not specified
        if not model_name:
            model_name = await self._select_optimal_model(prompt, **kwargs)
        
        config = self._get_model_config(model_name)
        if not config:
            raise ValueError(f"Model configuration not found: {model_name}")
        
        state = self.model_states[model_name]
        
        try:
            # Check cache first for non-streaming requests
            if not stream and config.cache_responses:
                cached_response = self.response_cache.get(prompt, model_name, **kwargs)
                if cached_response:
                    # Record cache hit metrics
                    metrics = GenerationMetrics(
                        model_name=model_name,
                        provider=config.provider,
                        first_token_latency_ms=0.0,  # Instant for cache hit
                        total_latency_ms=(time.time() - start_time) * 1000,
                        tokens_generated=len(cached_response.split()),
                        tokens_per_second=float('inf'),
                        cache_hit=True,
                        correlation_id=correlation_id
                    )
                    self._record_metrics(metrics)
                    
                    yield cached_response
                    return
            
            # Ensure model is warmed up
            if not state.is_warmed and config.warmup_strategy != WarmupStrategy.LAZY:
                await self._ensure_model_warmed(config)
            
            # Get provider instance
            provider_instance = await self._get_provider_instance(config)
            if not provider_instance:
                raise RuntimeError(f"Could not get provider instance for {model_name}")
            
            # Track first token timing
            first_token_time = None
            tokens_generated = 0
            response_parts = []
            
            # Generate response
            generation_start = time.time()
            
            if stream:
                # Streaming generation
                async for chunk in self._stream_with_provider(
                    provider_instance, prompt, config, **kwargs
                ):
                    if first_token_time is None:
                        first_token_time = time.time()
                    
                    tokens_generated += 1
                    response_parts.append(chunk)
                    yield chunk
            else:
                # Non-streaming generation
                response = await self._generate_with_provider(
                    provider_instance, prompt, config, **kwargs
                )
                first_token_time = time.time()
                tokens_generated = len(response.split())
                response_parts.append(response)
                
                # Cache the response
                if config.cache_responses:
                    self.response_cache.put(prompt, model_name, response, **kwargs)
                
                yield response
            
            # Calculate metrics
            total_time = time.time() - start_time
            first_token_latency = (first_token_time - generation_start) * 1000 if first_token_time else 0.0
            total_latency = total_time * 1000
            tokens_per_second = tokens_generated / max(total_time, 0.001)
            
            # Record metrics
            metrics = GenerationMetrics(
                model_name=model_name,
                provider=config.provider,
                first_token_latency_ms=first_token_latency,
                total_latency_ms=total_latency,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_second,
                cache_hit=False,
                correlation_id=correlation_id
            )
            self._record_metrics(metrics)
            
            # Update model state
            state.request_count += 1
            state.last_used = time.time()
            
            # Update running averages
            alpha = 0.1  # Exponential moving average factor
            state.avg_first_token_latency = (
                state.avg_first_token_latency * (1 - alpha) + first_token_latency * alpha
            )
            state.avg_total_latency = (
                state.avg_total_latency * (1 - alpha) + total_latency * alpha
            )
            
            logger.info(
                f"Generated response: {tokens_generated} tokens in {total_latency:.2f}ms "
                f"(first token: {first_token_latency:.2f}ms)",
                extra={"correlation_id": correlation_id}
            )
            
        except Exception as e:
            # Record error metrics
            error_metrics = GenerationMetrics(
                model_name=model_name,
                provider=config.provider,
                first_token_latency_ms=0.0,
                total_latency_ms=(time.time() - start_time) * 1000,
                tokens_generated=0,
                tokens_per_second=0.0,
                cache_hit=False,
                error=str(e),
                correlation_id=correlation_id
            )
            self._record_metrics(error_metrics)
            
            state.error_count += 1
            
            logger.error(f"Generation failed for {model_name}: {e}", extra={"correlation_id": correlation_id})
            raise
    
    async def _select_optimal_model(self, prompt: str, **kwargs) -> str:
        """Select the optimal model based on current performance and availability"""
        # Simple heuristic: prefer local models for better latency
        local_models = [
            config.name for config in self.configs 
            if config.model_type == ModelType.LOCAL and self.model_states[config.name].is_warmed
        ]
        
        if local_models:
            # Select local model with best performance
            best_model = min(
                local_models,
                key=lambda name: self.model_states[name].avg_first_token_latency
            )
            return best_model
        
        # Fallback to remote models
        remote_models = [
            config.name for config in self.configs 
            if config.model_type == ModelType.REMOTE_API
        ]
        
        if remote_models:
            return remote_models[0]  # Use first available remote model
        
        # Last resort: use any available model
        return self.configs[0].name if self.configs else "default"
    
    def _get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a model"""
        for config in self.configs:
            if config.name == model_name:
                return config
        return None
    
    async def _ensure_model_warmed(self, config: ModelConfig):
        """Ensure model is warmed up"""
        state = self.model_states[config.name]
        
        if not state.is_warmed:
            provider_instance = await self._get_provider_instance(config)
            if provider_instance:
                warmup_time = await self.preloader.warm_model(config, provider_instance)
                if warmup_time > 0:
                    state.is_warmed = True
                    state.warmup_time = warmup_time
    
    async def _stream_with_provider(
        self, provider_instance: Any, prompt: str, config: ModelConfig, **kwargs
    ) -> AsyncIterator[str]:
        """Stream response from provider"""
        # Prepare parameters
        params = {
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
        }
        
        # Try different streaming methods
        if hasattr(provider_instance, 'stream_response'):
            async for chunk in provider_instance.stream_response(prompt, **params):
                yield chunk
        elif hasattr(provider_instance, 'stream'):
            async for chunk in provider_instance.stream(prompt, **params):
                yield chunk
        else:
            # Fallback to non-streaming
            response = await self._generate_with_provider(provider_instance, prompt, config, **kwargs)
            yield response
    
    async def _generate_with_provider(
        self, provider_instance: Any, prompt: str, config: ModelConfig, **kwargs
    ) -> str:
        """Generate response from provider"""
        # Prepare parameters
        params = {
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
        }
        
        # Try different generation methods
        if hasattr(provider_instance, 'generate_response'):
            return await provider_instance.generate_response(prompt, **params)
        elif hasattr(provider_instance, 'generate'):
            return await provider_instance.generate(prompt, **params)
        elif hasattr(provider_instance, 'chat'):
            return await provider_instance.chat(prompt, **params)
        else:
            raise RuntimeError(f"No suitable generation method found for {type(provider_instance)}")
    
    def _record_metrics(self, metrics: GenerationMetrics):
        """Record performance metrics"""
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics (last 1000)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    async def _performance_monitor_loop(self):
        """Background loop for performance monitoring"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_performance_targets()
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
    
    async def _check_performance_targets(self):
        """Check if performance targets are being met"""
        if len(self.metrics_history) < 10:
            return  # Not enough data
        
        # Calculate p95 first token latency
        recent_metrics = self.metrics_history[-100:]  # Last 100 requests
        first_token_latencies = [
            m.first_token_latency_ms for m in recent_metrics 
            if m.error is None and not m.cache_hit
        ]
        
        if first_token_latencies:
            sorted_latencies = sorted(first_token_latencies)
            p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            
            target = self.performance_targets["first_token_latency_p95_ms"]
            
            if p95_latency > target:
                logger.warning(
                    f"First token latency SLO violation: {p95_latency:.2f}ms > {target}ms"
                )
                # Could trigger optimization actions here
            else:
                logger.debug(f"First token latency SLO met: {p95_latency:.2f}ms <= {target}ms")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        recent_metrics = self.metrics_history[-100:]
        
        # Calculate statistics
        first_token_latencies = [
            m.first_token_latency_ms for m in recent_metrics 
            if m.error is None and not m.cache_hit
        ]
        
        total_latencies = [
            m.total_latency_ms for m in recent_metrics 
            if m.error is None
        ]
        
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        total_requests = len(recent_metrics)
        errors = sum(1 for m in recent_metrics if m.error is not None)
        
        report = {
            "summary": {
                "total_requests": total_requests,
                "cache_hit_rate": cache_hits / max(total_requests, 1),
                "error_rate": errors / max(total_requests, 1),
            },
            "latency_metrics": {},
            "model_states": {},
            "slo_compliance": {}
        }
        
        # Latency metrics
        if first_token_latencies:
            sorted_ft = sorted(first_token_latencies)
            report["latency_metrics"]["first_token"] = {
                "avg_ms": sum(sorted_ft) / len(sorted_ft),
                "p50_ms": sorted_ft[int(len(sorted_ft) * 0.5)],
                "p95_ms": sorted_ft[int(len(sorted_ft) * 0.95)],
                "p99_ms": sorted_ft[int(len(sorted_ft) * 0.99)],
                "max_ms": max(sorted_ft),
                "min_ms": min(sorted_ft)
            }
        
        if total_latencies:
            sorted_total = sorted(total_latencies)
            report["latency_metrics"]["total"] = {
                "avg_ms": sum(sorted_total) / len(sorted_total),
                "p50_ms": sorted_total[int(len(sorted_total) * 0.5)],
                "p95_ms": sorted_total[int(len(sorted_total) * 0.95)],
                "p99_ms": sorted_total[int(len(sorted_total) * 0.99)],
                "max_ms": max(sorted_total),
                "min_ms": min(sorted_total)
            }
        
        # Model states
        for name, state in self.model_states.items():
            report["model_states"][name] = {
                "is_loaded": state.is_loaded,
                "is_warmed": state.is_warmed,
                "request_count": state.request_count,
                "error_count": state.error_count,
                "avg_first_token_latency_ms": state.avg_first_token_latency,
                "avg_total_latency_ms": state.avg_total_latency,
                "last_used": state.last_used
            }
        
        # SLO compliance
        if first_token_latencies:
            p95_first_token = sorted(first_token_latencies)[int(len(first_token_latencies) * 0.95)]
            report["slo_compliance"]["first_token_latency"] = {
                "target_ms": self.performance_targets["first_token_latency_p95_ms"],
                "actual_p95_ms": p95_first_token,
                "is_met": p95_first_token <= self.performance_targets["first_token_latency_p95_ms"]
            }
        
        return report
    
    async def benchmark_performance(self, test_prompts: List[str]) -> Dict[str, Any]:
        """Benchmark performance with test prompts"""
        results = {
            "test_prompts": len(test_prompts),
            "results": [],
            "summary": {}
        }
        
        for i, prompt in enumerate(test_prompts):
            start_time = time.time()
            
            try:
                # Test non-streaming generation
                response_parts = []
                async for chunk in self.generate_optimized(
                    prompt, stream=False, correlation_id=f"benchmark_{i}"
                ):
                    response_parts.append(chunk)
                
                total_time = (time.time() - start_time) * 1000
                
                results["results"].append({
                    "prompt_index": i,
                    "success": True,
                    "total_latency_ms": total_time,
                    "response_length": len("".join(response_parts))
                })
                
            except Exception as e:
                results["results"].append({
                    "prompt_index": i,
                    "success": False,
                    "error": str(e),
                    "total_latency_ms": (time.time() - start_time) * 1000
                })
        
        # Calculate summary statistics
        successful_results = [r for r in results["results"] if r["success"]]
        
        if successful_results:
            latencies = [r["total_latency_ms"] for r in successful_results]
            sorted_latencies = sorted(latencies)
            
            results["summary"] = {
                "success_rate": len(successful_results) / len(test_prompts),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "p95_latency_ms": sorted_latencies[int(len(sorted_latencies) * 0.95)],
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies)
            }
        
        return results

# Global instance
_optimized_llm_service: Optional[OptimizedLLMService] = None

def get_optimized_llm_service(configs: Optional[List[ModelConfig]] = None) -> OptimizedLLMService:
    """Get the global optimized LLM service instance"""
    global _optimized_llm_service
    
    if _optimized_llm_service is None:
        _optimized_llm_service = OptimizedLLMService(configs)
    
    return _optimized_llm_service
