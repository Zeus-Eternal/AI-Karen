from __future__ import annotations

"""Health monitoring API routes.

Expose structured service health information with Prometheus metrics,
correlation-aware logging, and circuit breaker support.
"""

import time
from typing import Any, Dict

from ai_karen_engine.utils.dependency_checks import import_fastapi
from ai_karen_engine.services.connection_health_manager import (
    ConnectionHealthManager,
    get_connection_health_manager,
)
from ai_karen_engine.services.correlation_service import get_request_id
from ai_karen_engine.services.structured_logging import (
    get_structured_logging_service,
)
import logging

logger = logging.getLogger(__name__)

APIRouter, Request = import_fastapi("APIRouter", "Request")

# ---------------------------------------------------------------------------
# Prometheus metrics with safe fallbacks
# ---------------------------------------------------------------------------
try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram

    _REQ_COUNTER = Counter(
        "health_endpoint_requests_total",
        "Total health endpoint requests",
        ["endpoint"],
    )
    _LATENCY_HIST = Histogram(
        "health_endpoint_latency_seconds",
        "Latency for health endpoint requests",
        ["endpoint"],
    )
except Exception:  # pragma: no cover - prometheus optional

    class _DummyMetric:
        def labels(self, **_kwargs):  # type: ignore[override]
            return self

        def inc(self, *_args, **_kwargs):  # type: ignore[override]
            pass

        def observe(self, *_args, **_kwargs):  # type: ignore[override]
            pass

    _REQ_COUNTER = _DummyMetric()
    _LATENCY_HIST = _DummyMetric()


# Expose health endpoints under /api/health
router = APIRouter(prefix="/health")


def _record_metrics(endpoint: str, duration_ms: float) -> None:
    """Record Prometheus metrics if available."""
    _REQ_COUNTER.labels(endpoint=endpoint).inc()
    _LATENCY_HIST.labels(endpoint=endpoint).observe(duration_ms / 1000)


def _collect_health(manager: ConnectionHealthManager) -> Dict[str, Any]:
    """Collect health status for all registered services."""
    services: Dict[str, Any] = {}
    for name in list(manager.health_status.keys()):
        try:
            result = manager.health_status[name]
            services[name] = {
                "status": result.status.value,
                "last_check": result.last_check.isoformat(),
                "response_time_ms": result.response_time_ms,
                "degraded_features": result.degraded_features,
            }
        except Exception as exc:  # pragma: no cover - defensive
            services[name] = {"status": "unknown", "error": str(exc)}
    return services


@router.get("")
async def overall_health(request: Request) -> Dict[str, Any]:
    """Return overall health status for registered services."""
    start = time.time()
    correlation_id = request.headers.get("X-Correlation-Id") or get_request_id()
    manager = get_connection_health_manager()

    # Perform health checks with circuit breaker protection
    for name in list(manager.health_status.keys()):
        try:
            await manager.check_service_health(name)
        except Exception:
            # check_service_health already handles circuit breaker and
            # degraded mode. Failures are reflected in status.
            pass

    services = _collect_health(manager)
    overall = (
        "healthy"
        if all(s["status"] == "healthy" for s in services.values())
        else "degraded"
    )

    duration_ms = (time.time() - start) * 1000
    _record_metrics("overall", duration_ms)

    get_structured_logging_service().log_api_request(
        method="GET",
        endpoint="/api/health",
        status_code=200,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
    )

    return {
        "status": overall,
        "services": services,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }


async def _check_local_model_capabilities() -> Dict[str, int]:
    """Check which local model systems are actually working."""
    capabilities = {
        "llamacpp_models": 0,
        "transformers_models": 0,
        "spacy_available": 0
    }
    
    # Check llama-cpp models
    try:
        from pathlib import Path
        from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime
        
        if LlamaCppRuntime.is_available():
            models_dir = Path("models/llama-cpp")
            if models_dir.exists():
                gguf_files = list(models_dir.glob("*.gguf"))
                for gguf_file in gguf_files:
                    try:
                        # Quick test load with minimal resources
                        runtime = LlamaCppRuntime(
                            model_path=str(gguf_file),
                            n_ctx=128,
                            n_batch=32,
                            verbose=False
                        )
                        if runtime.is_loaded():
                            capabilities["llamacpp_models"] += 1
                            runtime.unload_model()
                            break  # Found at least one working model
                    except Exception:
                        continue
    except Exception:
        pass
    
    # Check transformers models
    try:
        from pathlib import Path
        import transformers
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        models_dir = Path("models/transformers")
        if models_dir.exists():
            model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
            for model_dir in model_dirs:
                try:
                    # Quick test load
                    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                    if tokenizer:
                        capabilities["transformers_models"] += 1
                        break  # Found at least one working model
                except Exception:
                    continue
    except Exception:
        pass
    
    # Check spaCy
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        if nlp:
            capabilities["spacy_available"] = 1
    except Exception:
        pass
    
    return capabilities


@router.get("/degraded-mode")
async def degraded_mode_status() -> Dict[str, Any]:
    """Check if system is running in degraded mode"""
    try:
        # Check various system components for degraded mode
        degraded_components = []
        
        # Check database
        try:
            from ai_karen_engine.services.database_connection_manager import get_database_manager
            db_manager = get_database_manager()
            if db_manager.is_degraded():
                degraded_components.append("database")
        except Exception:
            degraded_components.append("database")
        
        # Check Redis
        try:
            from ai_karen_engine.services.redis_connection_manager import get_redis_manager
            redis_manager = get_redis_manager()
            if redis_manager.is_degraded():
                degraded_components.append("redis")
        except Exception:
            degraded_components.append("redis")
        
        # Check AI providers - consider both remote providers and local models
        failed_providers = []
        try:
            from ai_karen_engine.services.provider_registry import get_provider_registry_service
            provider_service = get_provider_registry_service()
            system_status = provider_service.get_system_status()
            
            # Check LLM Orchestrator for available models (including local ones)
            llm_models_available = 0
            try:
                from ai_karen_engine.llm_orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                available_models = orchestrator.registry.list_models()
                # Count models that are actually available (not circuit broken)
                llm_models_available = len([m for m in available_models if m.get('status') != 'CIRCUIT_BROKEN'])
            except Exception as e:
                logger.debug(f"Could not check LLM orchestrator models: {e}")
            
            # Check if we have local models available as files
            from pathlib import Path
            models_dir = Path("models")
            tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
            
            # Check spaCy availability
            spacy_available = False
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
            except:
                pass
            
            # Check comprehensive local model capabilities
            local_capabilities = await _check_local_model_capabilities()
            
            # Consider system healthy if we have ANY working AI capability:
            # - Remote providers with API keys
            # - Local models registered in LLM orchestrator  
            # - Working local model files (llama-cpp, transformers)
            # - spaCy for intelligent NLP responses
            total_ai_capabilities = (
                system_status["available_providers"] +  # Remote providers
                llm_models_available +                  # LLM orchestrator models
                local_capabilities["llamacpp_models"] + # Working GGUF models
                local_capabilities["transformers_models"] + # Working transformers models
                (1 if spacy_available else 0)           # spaCy NLP
            )
            
            if total_ai_capabilities == 0:
                degraded_components.append("ai_providers")
                failed_providers = system_status.get("failed_providers", [])
            else:
                # We have some AI capability, just note failed remote providers for info
                failed_providers = system_status.get("failed_providers", [])
                
        except Exception:
            # Fallback check for local models only
            try:
                from pathlib import Path
                models_dir = Path("models")
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
                
                # Only degraded if no local capabilities at all
                if not (tinyllama_available or spacy_available):
                    degraded_components.append("ai_providers")
                    failed_providers = ["unknown"]
            except:
                degraded_components.append("ai_providers")
                failed_providers = ["unknown"]
        
        # Determine if system is degraded based on AI capabilities primarily
        # Database/Redis issues don't make the system "degraded" if AI is working
        ai_degraded = "ai_providers" in degraded_components
        infrastructure_issues = [comp for comp in degraded_components if comp != "ai_providers"]
        
        # System is only considered degraded if AI capabilities are unavailable
        # Infrastructure issues are noted but don't trigger degraded mode if AI works
        is_degraded = ai_degraded
        
        # Determine degraded mode reason
        reason = None
        if is_degraded:
            reason = "all_providers_failed"
        elif infrastructure_issues:
            # Note infrastructure issues but don't mark as degraded if AI works
            reason = None  # System is healthy from AI perspective
        
        # Core helpers availability - check actual availability including LLM orchestrator
        try:
            from pathlib import Path
            models_dir = Path("models")
            tinyllama_file_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
            
            # Check spaCy availability
            spacy_available = False
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
            except:
                pass
            
            # Check LLM orchestrator for working models
            llm_orchestrator_models = 0
            try:
                from ai_karen_engine.llm_orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                available_models = orchestrator.registry.list_models()
                llm_orchestrator_models = len([m for m in available_models if m.get('status') != 'CIRCUIT_BROKEN'])
            except Exception:
                pass
            
            # Check remote providers
            remote_providers_available = 0
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                system_status = provider_service.get_system_status()
                remote_providers_available = system_status["available_providers"]
            except Exception:
                pass
            
            # Check local model capabilities
            local_capabilities = await _check_local_model_capabilities()
            
            core_helpers_available = {
                "local_nlp": spacy_available,  # spaCy NLP processing
                "local_llm_file": tinyllama_file_available,  # TinyLlama GGUF file exists
                "llm_orchestrator_models": llm_orchestrator_models,  # Models in LLM orchestrator
                "remote_providers": remote_providers_available,  # Remote providers with API keys
                "llamacpp_working_models": local_capabilities["llamacpp_models"],  # Actually working GGUF models
                "transformers_working_models": local_capabilities["transformers_models"],  # Working transformers models
                "spacy_intelligent_responses": local_capabilities["spacy_available"],  # spaCy intelligent responses
                "fallback_responses": True,  # Always available
                "basic_analytics": True,  # Basic analytics work
                "file_operations": True,  # File ops work
                "database_fallback": "database" not in degraded_components,
                "total_ai_capabilities": (
                    llm_orchestrator_models + 
                    remote_providers_available + 
                    local_capabilities["llamacpp_models"] +
                    local_capabilities["transformers_models"] +
                    local_capabilities["spacy_available"]
                )
            }
        except Exception:
            core_helpers_available = {
                "local_nlp": False,
                "local_llm_file": False,
                "llm_orchestrator_models": 0,
                "remote_providers": 0,
                "fallback_responses": True,
                "basic_analytics": True,
                "file_operations": True,
                "database_fallback": False,
                "total_ai_capabilities": 0
            }
        
        from datetime import datetime, timezone
        return {
            "is_active": is_degraded,
            "reason": reason,
            "activated_at": datetime.now(timezone.utc).isoformat() if is_degraded else None,
            "failed_providers": failed_providers,
            "recovery_attempts": 0,  # Could track this in a persistent store
            "last_recovery_attempt": None,  # Could track this too
            "core_helpers_available": core_helpers_available,
            "infrastructure_issues": infrastructure_issues,  # Note non-AI issues
            "ai_status": "healthy" if not ai_degraded else "degraded"
        }
        
    except Exception as e:
        from datetime import datetime, timezone
        return {
            "is_active": True,
            "reason": "resource_exhaustion",
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "failed_providers": ["unknown"],
            "recovery_attempts": 0,
            "last_recovery_attempt": None,
            "core_helpers_available": {
                "local_nlp": False,
                "local_llm": False,
                "fallback_responses": True,
                "basic_analytics": True,
                "file_operations": True,
                "database_fallback": False
            }
        }


@router.get("/{service_name}")
async def service_health(service_name: str, request: Request) -> Dict[str, Any]:
    """Return health status for a specific service."""
    start = time.time()
    correlation_id = request.headers.get("X-Correlation-Id") or get_request_id()
    manager = get_connection_health_manager()

    try:
        result = await manager.check_service_health(service_name)
        status = {
            "status": result.status.value,
            "last_check": result.last_check.isoformat(),
            "response_time_ms": result.response_time_ms,
            "degraded_features": result.degraded_features,
        }
        code = 200
    except Exception as exc:
        status = {"status": "unknown", "error": str(exc)}
        code = 404

    duration_ms = (time.time() - start) * 1000
    _record_metrics(service_name, duration_ms)

    get_structured_logging_service().log_api_request(
        method="GET",
        endpoint=f"/api/health/{service_name}",
        status_code=code,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
    )

    return {"service": service_name, "result": status, "correlation_id": correlation_id}


__all__ = ["router"]
