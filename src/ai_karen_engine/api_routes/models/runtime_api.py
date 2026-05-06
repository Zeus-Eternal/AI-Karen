"""
Unified Runtime API Routes

Provides a single source of truth for LLM providers, models, and execution status.
Consumed by both settings and chat interfaces to ensure architectural alignment.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ai_karen_engine.core.model_runtime.provider_registry_service import (
    get_provider_registry_service,
    HealthStatus,
)
from ai_karen_engine.integrations.registry import get_registry
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, Depends = import_fastapi("APIRouter", "Depends")
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.runtime_api")

router = APIRouter(prefix="/runtime", tags=["runtime"])


class ProviderHealthInfo(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    last_checked_at: Optional[datetime] = None


class RuntimeModel(BaseModel):
    id: str
    label: str
    available: bool = True
    default: bool = False
    capabilities: List[str] = Field(default_factory=list)


class RuntimeProvider(BaseModel):
    id: str
    label: str
    enabled: bool
    configured: bool
    healthy: bool
    runtime_engine: str
    models: List[RuntimeModel]
    health: ProviderHealthInfo
    degradation_reason: Optional[str] = None


class RuntimeProviderCatalog(BaseModel):
    providers: List[RuntimeProvider]
    default_provider: str
    default_model: str
    fallback_order: List[str]


@router.get("/providers", response_model=RuntimeProviderCatalog)
async def get_runtime_provider_catalog():
    """
    Get the canonical provider and model catalog for the entire runtime.
    This is the ONE TRUE SOURCE for provider/model selection UI.
    """
    try:
        registry_service = get_provider_registry_service()
        base_registry = get_registry()
        
        system_status = registry_service.get_system_status()
        provider_details = system_status.get("provider_details", {})
        
        catalog_providers = []
        
        for provider_id, status in provider_details.items():
            # Get model info from base registry
            provider_info = base_registry.get_provider_info(provider_id)
            
            models = []
            if provider_info and hasattr(provider_info, "models"):
                for m in provider_info.models:
                    models.append(RuntimeModel(
                        id=m.name,
                        label=m.name,
                        available=status.get("is_available", False),
                        default=(m.name == provider_info.default_model),
                        capabilities=m.capabilities
                    ))
            
            # If no models found in registry, check if provider has a default
            if not models and provider_info and provider_info.default_model:
                models.append(RuntimeModel(
                    id=provider_info.default_model,
                    label=provider_info.default_model,
                    available=status.get("is_available", False),
                    default=True,
                    capabilities=["chat"]
                ))

            catalog_providers.append(RuntimeProvider(
                id=provider_id,
                label=provider_id.replace("_", " ").title(),
                enabled=status.get("is_available", False), # Simplified for now
                configured=status.get("has_api_key", True),
                healthy=(status.get("health_status") == HealthStatus.HEALTHY.value),
                runtime_engine=status.get("runtime_engine") or provider_id.replace("builtin_", ""),
                models=models,
                health=ProviderHealthInfo(
                    status=status.get("health_status", "unknown"),
                    latency_ms=status.get("latency_ms"),
                    last_checked_at=datetime.utcnow() # Should come from real health check
                ),
                degradation_reason=status.get("error_message")
            ))

        return RuntimeProviderCatalog(
            providers=catalog_providers,
            default_provider="builtin_transformers",
            default_model="auto",
            fallback_order=["requested", "builtin_transformers", "builtin_vllm", "ollama", "openai"]
        )
        
    except Exception as e:
        logger.error(f"Error building runtime provider catalog: {e}")
        # Return a minimal valid catalog on error to keep UI functional
        return RuntimeProviderCatalog(
            providers=[],
            default_provider="builtin_transformers",
            default_model="auto",
            fallback_order=["builtin_transformers"]
        )
