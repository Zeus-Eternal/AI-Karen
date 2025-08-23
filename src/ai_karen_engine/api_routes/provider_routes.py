"""
Provider Management API Routes

Provides REST API endpoints for dynamic provider discovery, API key validation,
and provider health monitoring.
"""

import asyncio
import logging
import time
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


# Dependency to get registry
def get_llm_registry():
    """Get the global LLM registry instance."""
    return get_registry()


@router.get("/", response_model=List[ProviderInfo])
async def list_providers(
    category: Optional[str] = None,
    healthy_only: bool = False,
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
                cached_models_count=len(spec.fallback_models),
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


# Export the router
__all__ = ["router"]