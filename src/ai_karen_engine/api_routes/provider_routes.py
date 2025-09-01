"""
Provider Management API Routes

Provides REST API endpoints for dynamic provider discovery, API key validation,
and provider health monitoring.
"""

import asyncio
import logging
import time
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.error_handler import handle_api_exception
from ai_karen_engine.integrations.registry import get_registry
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, Depends, HTTPException = import_fastapi(
    "APIRouter", "Depends", "HTTPException"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.provider_routes")

router = APIRouter(tags=["providers"])
# Public router (no auth dependencies). Exposed under /api/public/providers
public_router = APIRouter(tags=["public-providers"])


# Request/Response Models
class ApiKeyValidationRequest(BaseModel):
    """API key validation request model."""
    provider: str
    api_key: str


class ApiKeyValidationResult(BaseModel):
    """API key validation result model."""
    valid: bool
    message: str
    provider: str
    models_discovered: Optional[int] = None
    capabilities_detected: Optional[List[str]] = None


class ProviderHealthResult(BaseModel):
    """Provider health check result model."""
    status: str  # healthy, unhealthy, unknown
    message: Optional[str] = None
    error_message: Optional[str] = None
    last_check: Optional[float] = None
    response_time: Optional[float] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    """Provider information model."""
    name: str
    description: str
    category: str
    requires_api_key: bool
    capabilities: List[str]
    is_llm_provider: bool
    provider_type: str  # remote, local, hybrid
    health_status: str
    error_message: Optional[str] = None
    last_health_check: Optional[float] = None
    cached_models_count: int = 0
    last_discovery: Optional[float] = None
    api_base_url: Optional[str] = None
    documentation_url: Optional[str] = None
    pricing_info: Optional[Dict[str, Any]] = None


class ProviderStats(BaseModel):
    """Provider statistics model."""
    total_models: int
    healthy_providers: int
    total_providers: int
    last_sync: float
    degraded_mode: bool


class ModelInfo(BaseModel):
    """Model information model."""
    id: str
    name: str
    provider: str
    family: str = ""
    format: str = ""
    size: Optional[int] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    capabilities: List[str] = Field(default_factory=list)
    local_path: Optional[str] = None
    download_url: Optional[str] = None
    license: Optional[str] = None
    description: str = ""


# ------------------------------------------------------------
# Contract shapes to support unified frontend
# ------------------------------------------------------------

class ContractProviderItem(BaseModel):
    id: str
    title: str
    group: str  # "local" | "cloud"
    canListModels: bool
    canInfer: bool
    available: bool


class ContractModelInfo(BaseModel):
    id: str
    provider: str
    displayName: str
    family: str
    installed: bool = True
    remote: bool = False
    size: Optional[str] = None
    quant: Optional[str] = None
    contextWindow: Optional[int] = None
    tags: List[str] = []


def _split_env_csv(name: str) -> List[str]:
    val = os.getenv(name, "").strip()
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def _has_gguf(dir_path: Path) -> bool:
    try:
        return any(p.suffix.lower() == ".gguf" for p in dir_path.glob("**/*"))
    except Exception:
        return False


def _list_gguf(dir_path: Path) -> List[ContractModelInfo]:
    models: List[ContractModelInfo] = []
    for p in dir_path.glob("**/*.gguf"):
        name = p.stem
        display = name
        quant = None
        size = None
        lowered = name.lower()
        for token in ("3b", "4b", "7b", "8b", "13b", "34b", "70b"):
            if token in lowered:
                size = token.upper()
                break
        for part in name.split("-"):
            if part.upper().startswith("Q"):
                quant = part.upper()
                break
        models.append(
            ContractModelInfo(
                id=f"llama:/{p.name}",
                provider="llama-cpp",
                displayName=display,
                family="llama",
                installed=True,
                remote=False,
                size=size,
                quant=quant,
                contextWindow=8192,
                tags=["gguf"],
            )
        )
    return models


def _list_transformers(dir_path: Path) -> List[ContractModelInfo]:
    models: List[ContractModelInfo] = []
    try:
        for child in dir_path.iterdir():
            if child.is_dir():
                models.append(
                    ContractModelInfo(
                        id=f"transformers:/{child.name}",
                        provider="transformers-local",
                        displayName=child.name,
                        family="transformers",
                        installed=True,
                        remote=False,
                        tags=["hf", "local"],
                    )
                )
    except Exception:
        pass
    return models


# Dependency to get registry
def get_llm_registry():
    """Get the global LLM registry instance."""
    return get_registry()


@router.get("/", response_model=List[ProviderInfo])
async def list_providers(
    category: Optional[str] = None,
    healthy_only: bool = False,
    llm_only: bool = False,
    registry=Depends(get_llm_registry)
):
    """
    Get list of all registered providers with their information.
    
    Args:
        category: Filter by provider category (LLM, UI_FRAMEWORK, etc.)
        healthy_only: Only return healthy providers
        
    Returns:
        List of provider information
    """
    try:
        if llm_only:
            provider_names = registry.list_llm_providers(healthy_only=healthy_only)
        else:
            provider_names = registry.list_providers(category=category, healthy_only=healthy_only)
        providers = []
        
        for name in provider_names:
            spec = registry.get_provider_spec(name)
            if not spec:
                continue
                
            health = registry.get_health_status(f"provider:{name}")
            
            # Determine provider type based on capabilities and requirements
            provider_type = "local"
            if spec.requires_api_key:
                provider_type = "remote"
            if "local_execution" in spec.capabilities and spec.requires_api_key:
                provider_type = "hybrid"
                
            # Get documentation URL based on provider
            doc_urls = {
                "openai": "https://platform.openai.com/docs",
                "gemini": "https://ai.google.dev/docs",
                "deepseek": "https://platform.deepseek.com/docs",
                "huggingface": "https://huggingface.co/docs",
            }
            
            # Get model availability from Model Library
            model_library_info = {}
            try:
                from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
                compatibility_service = ProviderModelCompatibilityService()
                validation = compatibility_service.validate_provider_model_setup(name)
                model_library_info = {
                    "has_compatible_models": validation.get("has_compatible_models", False),
                    "local_models_count": validation.get("local_models_count", 0),
                    "available_for_download": validation.get("available_for_download", 0),
                    "total_compatible": validation.get("total_compatible", 0)
                }
            except Exception as e:
                logger.warning(f"Failed to get model library info for {name}: {e}")
            
            provider_info = ProviderInfo(
                name=spec.name,
                description=spec.description,
                category=spec.category,
                requires_api_key=spec.requires_api_key,
                capabilities=list(spec.capabilities),
                is_llm_provider=(spec.category == "LLM"),
                provider_type=provider_type,
                health_status=health.status if health else "unknown",
                error_message=health.error_message if health else None,
                last_health_check=health.last_check if health else None,
                cached_models_count=model_library_info.get("local_models_count", len(spec.fallback_models)),
                documentation_url=doc_urls.get(name)
            )
            
            providers.append(provider_info)
        
        return providers
        
    except Exception as ex:
        logger.error(f"Failed to list providers: {ex}")
        raise handle_api_exception(ex, "Failed to retrieve provider list")


@router.get("/llm", response_model=List[ProviderInfo])
async def list_llm_providers(
    healthy_only: bool = False,
    registry=Depends(get_llm_registry)
):
    """
    Get list of LLM providers only (excludes UI frameworks like CopilotKit).
    
    Args:
        healthy_only: Only return healthy providers
        
    Returns:
        List of LLM provider information
    """
    try:
        provider_names = registry.list_llm_providers(healthy_only=healthy_only)
        providers = []
        
        for name in provider_names:
            spec = registry.get_provider_spec(name)
            if not spec or spec.category != "LLM":
                continue
                
            health = registry.get_health_status(f"provider:{name}")
            
            provider_type = "local"
            if spec.requires_api_key:
                provider_type = "remote"
            if "local_execution" in spec.capabilities and spec.requires_api_key:
                provider_type = "hybrid"
                
            doc_urls = {
                "openai": "https://platform.openai.com/docs",
                "gemini": "https://ai.google.dev/docs", 
                "deepseek": "https://platform.deepseek.com/docs",
                "huggingface": "https://huggingface.co/docs",
            }
            
            provider_info = ProviderInfo(
                name=spec.name,
                description=spec.description,
                category=spec.category,
                requires_api_key=spec.requires_api_key,
                capabilities=list(spec.capabilities),
                is_llm_provider=True,
                provider_type=provider_type,
                health_status=health.status if health else "unknown",
                error_message=health.error_message if health else None,
                last_health_check=health.last_check if health else None,
                cached_models_count=len(spec.fallback_models),
                documentation_url=doc_urls.get(name)
            )
            
            providers.append(provider_info)
        
        return providers
        
    except Exception as ex:
        logger.error(f"Failed to list LLM providers: {ex}")
        raise handle_api_exception(ex, "Failed to retrieve LLM provider list")


@router.post("/validate-api-key", response_model=ApiKeyValidationResult)
async def validate_api_key(
    request: ApiKeyValidationRequest,
    registry=Depends(get_llm_registry)
):
    """
    Validate API key for a provider and discover available models.
    
    Args:
        request: API key validation request
        
    Returns:
        Validation result with model discovery information
    """
    try:
        provider_name = request.provider
        api_key = request.api_key
        
        # Get provider spec
        spec = registry.get_provider_spec(provider_name)
        if not spec:
            return ApiKeyValidationResult(
                valid=False,
                message=f"Provider '{provider_name}' not found",
                provider=provider_name
            )
        
        if not spec.requires_api_key:
            return ApiKeyValidationResult(
                valid=True,
                message=f"Provider '{provider_name}' does not require API key",
                provider=provider_name,
                models_discovered=len(spec.fallback_models)
            )
        
        # Validate API key using provider's validation function
        if spec.validate:
            try:
                is_valid = spec.validate({"api_key": api_key})
                
                if is_valid:
                    # Try to discover models if provider supports it
                    models_discovered = 0
                    capabilities_detected = list(spec.capabilities)
                    
                    if spec.discover:
                        try:
                            models = spec.discover()
                            models_discovered = len(models) if models else 0
                        except Exception as e:
                            logger.warning(f"Model discovery failed for {provider_name}: {e}")
                            # Use fallback models count
                            models_discovered = len(spec.fallback_models)
                    else:
                        models_discovered = len(spec.fallback_models)
                    
                    return ApiKeyValidationResult(
                        valid=True,
                        message=f"API key valid for {provider_name}",
                        provider=provider_name,
                        models_discovered=models_discovered,
                        capabilities_detected=capabilities_detected
                    )
                else:
                    return ApiKeyValidationResult(
                        valid=False,
                        message=f"Invalid API key for {provider_name}",
                        provider=provider_name
                    )
                    
            except Exception as e:
                logger.error(f"API key validation failed for {provider_name}: {e}")
                return ApiKeyValidationResult(
                    valid=False,
                    message=f"Validation error: {str(e)}",
                    provider=provider_name
                )
        else:
            # No validation function available, assume valid if key is provided
            return ApiKeyValidationResult(
                valid=bool(api_key.strip()),
                message="No validation available, assuming valid" if api_key.strip() else "API key required",
                provider=provider_name,
                models_discovered=len(spec.fallback_models)
            )
            
    except Exception as ex:
        logger.error(f"Failed to validate API key: {ex}")
        return ApiKeyValidationResult(
            valid=False,
            message=f"Validation failed: {str(ex)}",
            provider=request.provider
        )


@router.get("/{provider_name}/models", response_model=List[ModelInfo])
async def get_provider_models(
    provider_name: str,
    force_refresh: bool = False,
    registry=Depends(get_llm_registry)
):
    """
    Get available models for a provider.
    
    Args:
        provider_name: Name of the provider
        force_refresh: Force refresh from provider API
        
    Returns:
        List of available models
    """
    try:
        spec = registry.get_provider_spec(provider_name)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found"
            )
        
        models = []
        
        # Try to discover models from provider API
        if spec.discover and force_refresh:
            try:
                discovered_models = spec.discover()
                if discovered_models:
                    for model_data in discovered_models:
                        model_info = ModelInfo(
                            id=model_data.get("id", ""),
                            name=model_data.get("name", model_data.get("id", "")),
                            provider=provider_name,
                            family=model_data.get("family", ""),
                            format=model_data.get("format", ""),
                            size=model_data.get("size"),
                            parameters=model_data.get("parameters"),
                            quantization=model_data.get("quantization"),
                            context_length=model_data.get("context_length"),
                            capabilities=model_data.get("capabilities", []),
                            download_url=model_data.get("download_url"),
                            license=model_data.get("license"),
                            description=model_data.get("description", "")
                        )
                        models.append(model_info)
                else:
                    # Fall back to fallback models
                    for model_data in spec.fallback_models:
                        model_info = ModelInfo(
                            id=model_data.get("id", ""),
                            name=model_data.get("name", model_data.get("id", "")),
                            provider=provider_name,
                            family=model_data.get("family", ""),
                            capabilities=model_data.get("capabilities", [])
                        )
                        models.append(model_info)
            except Exception as e:
                logger.warning(f"Model discovery failed for {provider_name}: {e}")
                # Fall back to fallback models
                for model_data in spec.fallback_models:
                    model_info = ModelInfo(
                        id=model_data.get("id", ""),
                        name=model_data.get("name", model_data.get("id", "")),
                        provider=provider_name,
                        family=model_data.get("family", ""),
                        capabilities=model_data.get("capabilities", [])
                    )
                    models.append(model_info)
        else:
            # Use fallback models
            for model_data in spec.fallback_models:
                model_info = ModelInfo(
                    id=model_data.get("id", ""),
                    name=model_data.get("name", model_data.get("id", "")),
                    provider=provider_name,
                    family=model_data.get("family", ""),
                    capabilities=model_data.get("capabilities", [])
                )
                models.append(model_info)
        
        return models
        
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to get models for provider {provider_name}: {ex}")
        raise handle_api_exception(ex, f"Failed to get models for provider {provider_name}")


@router.post("/health-check-all", response_model=Dict[str, ProviderHealthResult])
async def health_check_all_providers(registry=Depends(get_llm_registry)):
    """
    Perform health check on all registered providers.
    
    Returns:
        Dict containing health check results for each provider
    """
    try:
        results = {}
        provider_names = registry.list_providers()
        
        # Run health checks concurrently
        async def check_provider(name: str):
            try:
                health = registry.health_check(f"provider:{name}")
                return name, ProviderHealthResult(
                    status=health.status,
                    message=f"Provider {name} health check",
                    error_message=health.error_message,
                    last_check=health.last_check,
                    response_time=health.response_time,
                    capabilities=health.capabilities
                )
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                return name, ProviderHealthResult(
                    status="unhealthy",
                    error_message=str(e),
                    last_check=time.time()
                )
        
        # Execute health checks concurrently
        tasks = [check_provider(name) for name in provider_names]
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in health_results:
            if isinstance(result, tuple):
                name, health_result = result
                results[name] = health_result
            else:
                logger.error(f"Health check task failed: {result}")
        
        return results
        
    except Exception as ex:
        logger.error(f"Failed to perform health check on all providers: {ex}")
        raise handle_api_exception(ex, "Failed to perform provider health checks")


@router.get("/health/{provider_name}", response_model=ProviderHealthResult)
async def health_check_provider(
    provider_name: str,
    registry=Depends(get_llm_registry)
):
    """
    Perform health check on a specific provider.
    
    Args:
        provider_name: Name of the provider to check
        
    Returns:
        Health check result for the provider
    """
    try:
        spec = registry.get_provider_spec(provider_name)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found"
            )
        
        health = registry.health_check(f"provider:{provider_name}")
        
        return ProviderHealthResult(
            status=health.status,
            message=f"Provider {provider_name} health check",
            error_message=health.error_message,
            last_check=health.last_check,
            response_time=health.response_time,
            capabilities=health.capabilities
        )
        
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to health check provider {provider_name}: {ex}")
        raise handle_api_exception(ex, f"Failed to health check provider {provider_name}")


@router.get("/stats", response_model=ProviderStats)
async def get_provider_stats(registry=Depends(get_llm_registry)):
    """
    Get provider statistics and system status.
    
    Returns:
        Provider statistics including health status and model counts
    """
    try:
        provider_names = registry.list_providers()
        healthy_providers = registry.get_healthy_providers()
        
        # Count total models across all providers
        total_models = 0
        for name in provider_names:
            spec = registry.get_provider_spec(name)
            if spec:
                total_models += len(spec.fallback_models)
        
        # Check if system is in degraded mode
        unhealthy_components = registry.get_unhealthy_components()
        degraded_mode = len(unhealthy_components) > len(provider_names) // 2
        
        return ProviderStats(
            total_models=total_models,
            healthy_providers=len(healthy_providers),
            total_providers=len(provider_names),
            last_sync=time.time(),
            degraded_mode=degraded_mode
        )
        
    except Exception as ex:
            logger.error(f"Failed to get provider stats: {ex}")
            raise handle_api_exception(ex, "Failed to get provider statistics")


# ----------------- Contract endpoints under /api/providers -----------------


@router.get("/discovery", response_model=List[ContractProviderItem])
async def provider_discovery() -> List[ContractProviderItem]:
    items: List[ContractProviderItem] = []

    llama_dir = Path(os.getenv("LLAMA_CPP_MODELS_DIR", "./models/gguf")).resolve()
    llama_available = llama_dir.exists() and _has_gguf(llama_dir)

    tf_dir = Path(os.getenv("TRANSFORMERS_MODELS_DIR", "./models/transformers")).resolve()
    transformers_available = tf_dir.exists() and any(tf_dir.iterdir())

    spacy_pipelines = _split_env_csv("SPACY_PIPELINES")
    spacy_available = len(spacy_pipelines) > 0

    cloud_envs = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "mistral": bool(os.getenv("MISTRAL_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
    }

    items.extend(
        [
            ContractProviderItem(
                id="llama-cpp",
                title="llama.cpp (Local)",
                group="local",
                canListModels=True,
                canInfer=False,
                available=llama_available,
            ),
            ContractProviderItem(
                id="transformers-local",
                title="Transformers (Local)",
                group="local",
                canListModels=True,
                canInfer=False,
                available=transformers_available,
            ),
            ContractProviderItem(
                id="spacy",
                title="spaCy (Pipelines)",
                group="local",
                canListModels=True,
                canInfer=False,
                available=spacy_available,
            ),
            ContractProviderItem(
                id="openai",
                title="OpenAI",
                group="cloud",
                canListModels=True,
                canInfer=False,
                available=cloud_envs["openai"],
            ),
        ]
    )

    for pid, ok in cloud_envs.items():
        if pid == "openai":
            continue
        title = pid.title() if pid != "groq" else "Groq"
        items.append(
            ContractProviderItem(
                id=pid,
                title=title,
                group="cloud",
                canListModels=True,
                canInfer=False,
                available=ok,
            )
        )

    return items

# Public mirrors
@public_router.get("/discovery", response_model=List[ContractProviderItem])
async def public_provider_discovery() -> List[ContractProviderItem]:
    return await provider_discovery()


@router.get("/local/llama/models", response_model=List[ContractModelInfo])
async def contract_llama_models() -> List[ContractModelInfo]:
    base = Path(os.getenv("LLAMA_CPP_MODELS_DIR", "./models/gguf")).resolve()
    if not base.exists():
        return []
    return _list_gguf(base)

@public_router.get("/local/llama/models", response_model=List[ContractModelInfo])
async def public_llama_models() -> List[ContractModelInfo]:
    return await contract_llama_models()


@router.get("/local/transformers/models", response_model=List[ContractModelInfo])
async def contract_transformers_models() -> List[ContractModelInfo]:
    base = Path(os.getenv("TRANSFORMERS_MODELS_DIR", "./models/transformers")).resolve()
    if not base.exists():
        return []
    return _list_transformers(base)

@public_router.get("/local/transformers/models", response_model=List[ContractModelInfo])
async def public_transformers_models() -> List[ContractModelInfo]:
    return await contract_transformers_models()


@router.get("/local/spacy/pipelines", response_model=List[str])
async def contract_spacy_pipelines() -> List[str]:
    return _split_env_csv("SPACY_PIPELINES")

@public_router.get("/local/spacy/pipelines", response_model=List[str])
async def public_spacy_pipelines() -> List[str]:
    return await contract_spacy_pipelines()


@router.get("/cloud/openai/ping")
async def contract_openai_ping():
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not configured")
    return {"ok": True}


@router.get("/cloud/openai/models", response_model=List[ContractModelInfo])
async def contract_openai_models() -> List[ContractModelInfo]:
    key = os.getenv("OPENAI_API_KEY")
    allowlist = _split_env_csv("OPENAI_MODELS_ALLOWLIST")
    models: List[ContractModelInfo] = []

    if allowlist:
        for mid in allowlist:
            models.append(
                ContractModelInfo(
                    id=mid,
                    provider="openai",
                    displayName=mid,
                    family="gpt" if mid.startswith("gpt") else "openai",
                    installed=False,
                    remote=True,
                    tags=["cloud"],
                )
            )
        return models

    if key:
        try:
            import requests  # type: ignore

            base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            resp = requests.get(
                f"{base.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                for item in data.get("data", []):
                    mid = item.get("id", "")
                    if not mid:
                        continue
                    if not (mid.startswith("gpt") or mid.startswith("o")):
                        continue
                    models.append(
                        ContractModelInfo(
                            id=mid,
                            provider="openai",
                            displayName=mid,
                            family="gpt" if mid.startswith("gpt") else "openai",
                            installed=False,
                            remote=True,
                            tags=["cloud"],
                        )
                    )
                return models
        except Exception:
            pass

    for mid in ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "o4-mini"]:
        models.append(
            ContractModelInfo(
                id=mid,
                provider="openai",
                displayName=mid,
                family="gpt" if mid.startswith("gpt") else "openai",
                installed=False,
                remote=True,
                tags=["cloud"],
            )
        )
    return models


@router.get("/{provider_name}/suggestions")
async def get_provider_model_suggestions(
    provider_name: str,
    registry=Depends(get_llm_registry)
):
    """
    Get comprehensive model suggestions for a specific provider from Model Library.
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider-specific model suggestions with compatibility information
    """
    try:
        spec = registry.get_provider_spec(provider_name)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found"
            )
        
        # Use the compatibility service to get suggestions
        try:
            from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
            compatibility_service = ProviderModelCompatibilityService()
            suggestions = compatibility_service.get_provider_model_suggestions(provider_name)
            
            if "error" in suggestions:
                raise HTTPException(status_code=500, detail=suggestions["error"])
            
            return suggestions
            
        except ImportError:
            # Fallback if compatibility service is not available
            return {
                "provider": provider_name,
                "provider_capabilities": {
                    "supported_formats": ["unknown"],
                    "required_capabilities": list(spec.capabilities),
                    "optional_capabilities": [],
                    "performance_type": "unknown",
                    "quantization_support": "unknown"
                },
                "recommendations": {
                    "excellent": [],
                    "good": [model.get("id", "") for model in spec.fallback_models[:3]],
                    "acceptable": []
                },
                "total_compatible_models": len(spec.fallback_models),
                "compatibility_details": {}
            }
            
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to get model suggestions for provider {provider_name}: {ex}")
        raise handle_api_exception(ex, f"Failed to get model suggestions for provider {provider_name}")


@router.get("/integration/status")
async def get_integration_status(registry=Depends(get_llm_registry)):
    """
    Get integration status between providers and Model Library.
    
    Returns:
        Integration status information including model availability and compatibility
    """
    try:
        provider_names = registry.list_llm_providers()
        integration_status = {
            "providers": {},
            "overall_status": "healthy",
            "total_providers": len(provider_names),
            "healthy_providers": 0,
            "providers_with_models": 0,
            "total_compatible_models": 0,
            "recommendations": []
        }
        
        for provider_name in provider_names:
            try:
                # Get provider health
                health = registry.get_health_status(f"provider:{provider_name}")
                is_healthy = health and health.status == "healthy"
                
                # Get model compatibility info
                try:
                    from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
                    compatibility_service = ProviderModelCompatibilityService()
                    validation = compatibility_service.validate_provider_model_setup(provider_name)
                    
                    provider_status = {
                        "name": provider_name,
                        "healthy": is_healthy,
                        "has_compatible_models": validation.get("has_compatible_models", False),
                        "has_local_models": validation.get("has_local_models", False),
                        "local_models_count": validation.get("local_models_count", 0),
                        "available_for_download": validation.get("available_for_download", 0),
                        "total_compatible": validation.get("total_compatible", 0),
                        "status": validation.get("status", "unknown"),
                        "recommendations": validation.get("recommendations", [])
                    }
                    
                    if is_healthy:
                        integration_status["healthy_providers"] += 1
                    
                    if validation.get("has_compatible_models", False):
                        integration_status["providers_with_models"] += 1
                    
                    integration_status["total_compatible_models"] += validation.get("total_compatible", 0)
                    
                except ImportError:
                    # Fallback without compatibility service
                    spec = registry.get_provider_spec(provider_name)
                    provider_status = {
                        "name": provider_name,
                        "healthy": is_healthy,
                        "has_compatible_models": len(spec.fallback_models) > 0 if spec else False,
                        "has_local_models": False,  # Can't determine without compatibility service
                        "local_models_count": 0,
                        "available_for_download": len(spec.fallback_models) if spec else 0,
                        "total_compatible": len(spec.fallback_models) if spec else 0,
                        "status": "unknown",
                        "recommendations": ["Install Model Library compatibility service for full integration"]
                    }
                    
                    if is_healthy:
                        integration_status["healthy_providers"] += 1
                
                integration_status["providers"][provider_name] = provider_status
                
            except Exception as e:
                logger.warning(f"Failed to get integration status for {provider_name}: {e}")
                integration_status["providers"][provider_name] = {
                    "name": provider_name,
                    "healthy": False,
                    "has_compatible_models": False,
                    "has_local_models": False,
                    "local_models_count": 0,
                    "available_for_download": 0,
                    "total_compatible": 0,
                    "status": "error",
                    "recommendations": [f"Error checking integration: {e}"]
                }
        
        # Determine overall status
        if integration_status["healthy_providers"] == 0:
            integration_status["overall_status"] = "unhealthy"
        elif integration_status["providers_with_models"] == 0:
            integration_status["overall_status"] = "needs_models"
        elif integration_status["healthy_providers"] < integration_status["total_providers"] // 2:
            integration_status["overall_status"] = "degraded"
        
        # Add overall recommendations
        if integration_status["providers_with_models"] == 0:
            integration_status["recommendations"].append("No providers have compatible models. Visit Model Library to download models.")
        elif integration_status["providers_with_models"] < integration_status["total_providers"]:
            integration_status["recommendations"].append("Some providers need compatible models. Check Model Library for recommendations.")
        
        return integration_status
        
    except Exception as ex:
        logger.error(f"Failed to get integration status: {ex}")
        raise handle_api_exception(ex, "Failed to get integration status")


@router.get("/{provider_name}/model-recommendations")
async def get_provider_model_recommendations(
    provider_name: str,
    limit: int = 10,
    registry=Depends(get_llm_registry)
):
    """
    Get model recommendations for a specific provider from Model Library.
    
    Args:
        provider_name: Name of the provider
        limit: Maximum number of recommendations to return
        
    Returns:
        Provider-specific model recommendations with compatibility information
    """
    try:
        spec = registry.get_provider_spec(provider_name)
        if not spec:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found"
            )
        
        # Get recommendations from Model Library compatibility service
        try:
            from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
            compatibility_service = ProviderModelCompatibilityService()
            
            # Get comprehensive suggestions
            suggestions = compatibility_service.get_provider_model_suggestions(provider_name)
            
            if "error" in suggestions:
                return {
                    "provider": provider_name,
                    "recommendations": [],
                    "error": suggestions["error"],
                    "fallback_models": spec.fallback_models
                }
            
            return {
                "provider": provider_name,
                "provider_capabilities": suggestions.get("provider_capabilities", {}),
                "recommendations": suggestions.get("recommendations", {}),
                "total_compatible_models": suggestions.get("total_compatible_models", 0),
                "compatibility_details": suggestions.get("compatibility_details", {}),
                "validation": compatibility_service.validate_provider_model_setup(provider_name)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get Model Library recommendations for {provider_name}: {e}")
            
            # Fallback to provider's own models
            return {
                "provider": provider_name,
                "recommendations": {
                    "fallback": [model.get("id", model.get("name", "")) for model in spec.fallback_models]
                },
                "total_compatible_models": len(spec.fallback_models),
                "error": f"Model Library unavailable: {str(e)}",
                "fallback_models": spec.fallback_models
            }
        
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to get model recommendations for {provider_name}: {ex}")
        raise handle_api_exception(ex, f"Failed to get recommendations for provider {provider_name}")


# Export the router
__all__ = ["router"]
@router.get("/{provider_name}/health")
async def check_provider_health(provider_name: str, registry=Depends(get_llm_registry)):
    """Check health of a single provider."""
    try:
        status = registry.health_check(f"provider:{provider_name}")
        return {
            "name": provider_name,
            "status": status.status,
            "last_check": status.last_check,
            "error_message": status.error_message,
            "response_time": status.response_time,
            "capabilities": status.capabilities,
        }
    except Exception as ex:
        logger.error(f"Health check failed for {provider_name}: {ex}")
        return handle_api_exception(ex, f"Failed to check health for {provider_name}")


@router.post("/{provider_name}/disable")
async def disable_provider(provider_name: str, registry=Depends(get_llm_registry)):
    """Disable a provider without unregistering it."""
    try:
        ok = registry.disable_provider(provider_name)
        if not ok:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"success": True, "provider": provider_name, "disabled": True}
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Disable provider failed for {provider_name}: {ex}")
        return handle_api_exception(ex, f"Failed to disable provider {provider_name}")


@router.post("/{provider_name}/enable")
async def enable_provider(provider_name: str, registry=Depends(get_llm_registry)):
    """Enable a previously disabled provider."""
    try:
        ok = registry.enable_provider(provider_name)
        if not ok:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"success": True, "provider": provider_name, "disabled": False}
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Enable provider failed for {provider_name}: {ex}")
        return handle_api_exception(ex, f"Failed to enable provider {provider_name}")
