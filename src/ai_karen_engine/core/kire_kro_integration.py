"""
KIRE-KRO Integration Module - Production Wiring

This module integrates:
- KIRE (Kari Intelligent Routing Engine) for LLM selection
- KRO (Kari Reasoning Orchestrator) for prompt-first control
- Model Discovery Engine for comprehensive model awareness
- CUDA Acceleration Engine for GPU offloading
- Content Optimization Engine for response improvement
- OSIRIS logging for observability

This provides a single entry point for production-grade AI-Karen request processing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for KIRE-KRO integration."""
    enable_kire_routing: bool = True
    enable_cuda_acceleration: bool = True
    enable_content_optimization: bool = True
    enable_model_discovery: bool = True
    enable_degraded_mode: bool = True
    enable_metrics: bool = True
    cache_routing_decisions: bool = True
    max_concurrent_requests: int = 10
    request_timeout: float = 120.0


class KIREKROIntegration:
    """
    Production integration layer for KIRE and KRO.

    This class provides a unified interface for processing user requests through
    the complete AI-Karen pipeline with intelligent routing, reasoning, and optimization.
    """

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize integration layer."""
        self.config = config or IntegrationConfig()

        # Core components
        self.kro_orchestrator = None
        self.kire_router = None
        self.model_discovery = None
        self.cuda_engine = None
        self.optimization_engine = None
        self.llm_registry = None

        # State
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        logger.info("KIRE-KRO Integration initialized")

    async def initialize(self):
        """Initialize all components asynchronously."""
        if self._initialized:
            return

        async with self._initialization_lock:
            if self._initialized:  # Double-check after acquiring lock
                return

            try:
                logger.info("Initializing KIRE-KRO integration components...")

                # Initialize LLM Registry
                from ai_karen_engine.integrations.llm_registry import get_registry
                self.llm_registry = get_registry()
                logger.info("✓ LLM Registry initialized")

                # Initialize Model Discovery
                if self.config.enable_model_discovery:
                    try:
                        from ai_karen_engine.services.model_discovery_engine import ModelDiscoveryEngine
                        self.model_discovery = ModelDiscoveryEngine()
                        await self.model_discovery.discover_all_models()
                        stats = self.model_discovery.get_discovery_statistics()
                        logger.info(f"✓ Model Discovery initialized: {stats['total_models']} models discovered")
                    except Exception as e:
                        logger.warning(f"Model Discovery initialization failed: {e}")

                # Initialize KIRE Router
                if self.config.enable_kire_routing:
                    try:
                        from ai_karen_engine.routing.kire_router import KIRERouter
                        self.kire_router = KIRERouter(llm_registry=self.llm_registry)
                        logger.info("✓ KIRE Router initialized")
                    except Exception as e:
                        logger.error(f"KIRE Router initialization failed: {e}")
                        raise

                # Initialize CUDA Acceleration
                if self.config.enable_cuda_acceleration:
                    try:
                        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
                        self.cuda_engine = CUDAAccelerationEngine()
                        await self.cuda_engine.initialize()
                        info = self.cuda_engine.get_cuda_info()
                        if info.available:
                            logger.info(f"✓ CUDA Acceleration initialized: {info.device_count} GPU(s)")
                        else:
                            logger.info("✓ CUDA Acceleration initialized (no GPU available)")
                    except Exception as e:
                        logger.warning(f"CUDA Acceleration initialization failed: {e}")
                        self.cuda_engine = None

                # Initialize Content Optimization
                if self.config.enable_content_optimization:
                    try:
                        from ai_karen_engine.services.content_optimization_engine import ContentOptimizationEngine
                        self.optimization_engine = ContentOptimizationEngine()
                        logger.info("✓ Content Optimization initialized")
                    except Exception as e:
                        logger.warning(f"Content Optimization initialization failed: {e}")

                # Initialize KRO Orchestrator
                from ai_karen_engine.core.kro_orchestrator import KROOrchestrator
                self.kro_orchestrator = KROOrchestrator(
                    llm_registry=self.llm_registry,
                    kire_router=self.kire_router,
                    enable_cuda=bool(self.cuda_engine),
                    enable_optimization=bool(self.optimization_engine),
                )
                logger.info("✓ KRO Orchestrator initialized")

                self._initialized = True
                logger.info("✅ KIRE-KRO integration fully initialized")

            except Exception as e:
                logger.error(f"Failed to initialize KIRE-KRO integration: {e}", exc_info=True)
                raise

    async def process_user_request(
        self,
        user_input: str,
        user_id: str = "anon",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process user request through the complete pipeline.

        Args:
            user_input: User's message/query
            user_id: User identifier for routing and personalization
            conversation_history: Recent conversation turns
            context: Additional context (session_id, tenant_id, etc.)

        Returns:
            Complete response envelope with content, metadata, and suggestions
        """
        # Ensure initialization
        await self.initialize()

        try:
            # Process through KRO
            kro_response, user_message = await self.kro_orchestrator.process_request(
                user_input=user_input,
                user_id=user_id,
                conversation_history=conversation_history or [],
                ui_context=context,
                correlation_id=(context or {}).get("correlation_id"),
            )

            # Convert KRO response to dict for JSON serialization
            response_dict = self._kro_response_to_dict(kro_response)

            # Add user-facing message
            response_dict["message"] = user_message

            # Add integration metadata
            response_dict["_integration"] = {
                "kire_enabled": self.config.enable_kire_routing,
                "cuda_enabled": bool(self.cuda_engine),
                "optimization_enabled": bool(self.optimization_engine),
            }

            return response_dict

        except Exception as e:
            logger.error(f"Request processing failed: {e}", exc_info=True)

            # Return error response
            return {
                "success": False,
                "error": str(e),
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "meta": {
                    "timestamp": "",
                    "agent": "KRO",
                    "confidence": 0.0,
                    "degraded_mode": True,
                },
            }

    def _kro_response_to_dict(self, kro_response) -> Dict[str, Any]:
        """Convert KRO response dataclass to dictionary."""
        try:
            # Use dataclasses.asdict if available
            from dataclasses import asdict
            return asdict(kro_response)
        except Exception:
            # Manual conversion fallback
            return {
                "meta": {
                    "timestamp": kro_response.meta.timestamp,
                    "agent": kro_response.meta.agent,
                    "confidence": kro_response.meta.confidence,
                    "latency_ms": kro_response.meta.latency_ms,
                    "tokens_used": kro_response.meta.tokens_used,
                    "provider": kro_response.meta.provider,
                    "model": kro_response.meta.model,
                    "degraded_mode": kro_response.meta.degraded_mode,
                },
                "classification": {
                    "intent": kro_response.classification.intent.value,
                    "category": kro_response.classification.category.value,
                    "sentiment": kro_response.classification.sentiment.value,
                    "style": kro_response.classification.style.value,
                    "importance": kro_response.classification.importance,
                    "keywords": kro_response.classification.keywords,
                },
                "reasoning_summary": kro_response.reasoning_summary,
                "plan": [
                    {
                        "step": step.step,
                        "action": step.action,
                        "detail": step.detail,
                        "name": step.name,
                        "args": step.args,
                        "why": step.why,
                    }
                    for step in kro_response.plan
                ],
                "evidence": [
                    {
                        "source": ev.source,
                        "type": ev.type,
                        "hash": ev.hash,
                        "snippet": ev.snippet,
                    }
                    for ev in kro_response.evidence
                ],
                "memory_writes": [
                    {
                        "text": mem.text,
                        "tags": mem.tags,
                        "ttl": mem.ttl,
                    }
                    for mem in kro_response.memory_writes
                ],
                "ui": kro_response.ui,
                "telemetry": {
                    "tools_called": [
                        {
                            "name": tool.name,
                            "ok": tool.ok,
                            "latency_ms": tool.latency_ms,
                            "error": tool.error,
                        }
                        for tool in kro_response.telemetry.tools_called
                    ],
                    "errors": kro_response.telemetry.errors,
                    "notes": kro_response.telemetry.notes,
                },
                "suggestions": kro_response.suggestions,
            }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of all available models."""
        await self.initialize()

        if not self.model_discovery:
            # Fallback to LLM registry
            providers = self.llm_registry.list_providers()
            return [
                {
                    "provider": p,
                    "models": [self.llm_registry.get_provider(p).get("default_model", "auto")],
                    "status": "available",
                }
                for p in providers
            ]

        # Use comprehensive model discovery
        models = self.model_discovery.get_discovered_models()
        return [
            {
                "id": model.id,
                "name": model.display_name,
                "provider": model.type.value,
                "category": model.category.value,
                "capabilities": model.capabilities,
                "status": model.status.value,
                "size_gb": model.size / (1024 ** 3),
                "modalities": [mod.type.value for mod in model.modalities],
            }
            for model in models
        ]

    async def get_routing_decision(
        self,
        user_input: str,
        user_id: str = "anon",
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get routing decision without executing the full request."""
        await self.initialize()

        if not self.kire_router:
            return {"error": "KIRE routing not available"}

        try:
            from ai_karen_engine.routing.types import RouteRequest

            route_req = RouteRequest(
                user_id=user_id,
                query=user_input,
                task_type=task_type or "chat",
                context=context or {},
            )

            decision = await self.kire_router.route_provider_selection(route_req)

            return {
                "provider": decision.provider,
                "model": decision.model,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "fallback_chain": decision.fallback_chain,
                "metadata": decision.metadata,
            }

        except Exception as e:
            logger.error(f"Routing decision failed: {e}")
            return {"error": str(e)}

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        await self.initialize()

        status = {
            "initialized": self._initialized,
            "components": {
                "kro_orchestrator": bool(self.kro_orchestrator),
                "kire_router": bool(self.kire_router),
                "llm_registry": bool(self.llm_registry),
                "model_discovery": bool(self.model_discovery),
                "cuda_engine": bool(self.cuda_engine),
                "optimization_engine": bool(self.optimization_engine),
            },
            "config": {
                "kire_routing": self.config.enable_kire_routing,
                "cuda_acceleration": self.config.enable_cuda_acceleration,
                "content_optimization": self.config.enable_content_optimization,
                "model_discovery": self.config.enable_model_discovery,
            },
        }

        # Add CUDA info if available
        if self.cuda_engine:
            try:
                cuda_info = self.cuda_engine.get_cuda_info()
                status["cuda"] = {
                    "available": cuda_info.available,
                    "device_count": cuda_info.device_count,
                    "total_memory_gb": cuda_info.total_memory / (1024 ** 3) if cuda_info.total_memory else 0,
                }
            except Exception:
                status["cuda"] = {"available": False}

        # Add model discovery stats if available
        if self.model_discovery:
            try:
                stats = self.model_discovery.get_discovery_statistics()
                status["models"] = stats
            except Exception:
                pass

        # Add LLM registry info
        if self.llm_registry:
            try:
                providers = self.llm_registry.list_providers()
                status["providers"] = {
                    "count": len(providers),
                    "names": providers,
                }
            except Exception:
                pass

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        try:
            await self.initialize()

            health = {
                "status": "healthy",
                "components": {},
            }

            # Check KRO
            if self.kro_orchestrator:
                health["components"]["kro"] = "healthy"
            else:
                health["components"]["kro"] = "unavailable"
                health["status"] = "degraded"

            # Check KIRE
            if self.kire_router:
                health["components"]["kire"] = "healthy"
            else:
                health["components"]["kire"] = "unavailable"
                health["status"] = "degraded"

            # Check LLM Registry
            if self.llm_registry:
                try:
                    providers = self.llm_registry.list_providers()
                    healthy_providers = sum(
                        1 for p in providers
                        if self.llm_registry.health_check(p).get("status") == "healthy"
                    )
                    health["components"]["llm_registry"] = f"{healthy_providers}/{len(providers)} healthy"
                except Exception:
                    health["components"]["llm_registry"] = "error"
                    health["status"] = "degraded"

            # Check CUDA
            if self.cuda_engine:
                try:
                    cuda_info = self.cuda_engine.get_cuda_info()
                    health["components"]["cuda"] = "available" if cuda_info.available else "unavailable"
                except Exception:
                    health["components"]["cuda"] = "error"

            return health

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# ===================================
# FACTORY FUNCTIONS
# ===================================

_integration_instance = None

def get_integration() -> KIREKROIntegration:
    """Get singleton integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = KIREKROIntegration()
    return _integration_instance


async def initialize_integration(config: Optional[IntegrationConfig] = None):
    """Initialize the integration layer."""
    integration = get_integration()
    if config:
        integration.config = config
    await integration.initialize()
    return integration


# ===================================
# CONVENIENCE FUNCTIONS
# ===================================

async def process_request(
    user_input: str,
    user_id: str = "anon",
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience function to process a request through the integrated system."""
    integration = get_integration()
    return await integration.process_user_request(
        user_input=user_input,
        user_id=user_id,
        conversation_history=conversation_history,
        context=context,
    )


async def get_available_models() -> List[Dict[str, Any]]:
    """Convenience function to get all available models."""
    integration = get_integration()
    return await integration.get_available_models()


async def get_system_status() -> Dict[str, Any]:
    """Convenience function to get system status."""
    integration = get_integration()
    return await integration.get_system_status()


async def health_check() -> Dict[str, Any]:
    """Convenience function to perform health check."""
    integration = get_integration()
    return await integration.health_check()
