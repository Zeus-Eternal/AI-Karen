"""
FastAPI dependency providers for inference services.

Provides singleton instances of all inference runtimes for dependency injection.
"""

from functools import lru_cache
from typing import Optional

from ai_karen_engine.inference.factory import (
    get_llamacpp_runtime as _get_llamacpp_runtime,
    get_transformers_runtime as _get_transformers_runtime,
    get_vllm_runtime as _get_vllm_runtime,
    get_model_store as _get_model_store,
    get_inference_service_factory,
)


# Runtime dependencies
@lru_cache()
def get_llamacpp_runtime_dependency():
    """
    FastAPI dependency for LlamaCpp runtime.

    Returns:
        LlamaCppRuntime instance or None if unavailable

    Usage:
        @app.post("/generate/llamacpp")
        def generate(
            prompt: str,
            runtime: LlamaCppRuntime = Depends(get_llamacpp_runtime_dependency)
        ):
            if not runtime:
                raise HTTPException(status_code=503, detail="LlamaCpp runtime unavailable")
            return runtime.generate(prompt)
    """
    return _get_llamacpp_runtime()


@lru_cache()
def get_transformers_runtime_dependency():
    """
    FastAPI dependency for Transformers runtime.

    Returns:
        TransformersRuntime instance or None if unavailable

    Usage:
        @app.post("/generate/transformers")
        def generate(
            prompt: str,
            runtime: TransformersRuntime = Depends(get_transformers_runtime_dependency)
        ):
            if not runtime:
                raise HTTPException(status_code=503, detail="Transformers runtime unavailable")
            return runtime.generate(prompt)
    """
    return _get_transformers_runtime()


@lru_cache()
def get_vllm_runtime_dependency():
    """
    FastAPI dependency for vLLM runtime.

    Returns:
        VLLMRuntime instance or None if unavailable

    Usage:
        @app.post("/generate/vllm")
        def generate(
            prompt: str,
            runtime: VLLMRuntime = Depends(get_vllm_runtime_dependency)
        ):
            if not runtime:
                raise HTTPException(status_code=503, detail="vLLM runtime unavailable")
            return runtime.generate(prompt)
    """
    return _get_vllm_runtime()


# Model store dependency
@lru_cache()
def get_model_store_dependency():
    """
    FastAPI dependency for model store.

    Returns:
        ModelStore instance or None if unavailable

    Usage:
        @app.get("/models")
        def list_models(
            store: ModelStore = Depends(get_model_store_dependency)
        ):
            if not store:
                raise HTTPException(status_code=503, detail="Model store unavailable")
            return store.list_models()
    """
    return _get_model_store()


# Factory dependency
@lru_cache()
def get_inference_factory_dependency():
    """
    FastAPI dependency for inference service factory.

    Returns:
        InferenceServiceFactory instance

    Usage:
        @app.get("/runtimes/available")
        def get_available_runtimes(
            factory: InferenceServiceFactory = Depends(get_inference_factory_dependency)
        ):
            return {"runtimes": factory.get_available_runtimes()}
    """
    return get_inference_service_factory()


# Health check dependency
def get_inference_health_check():
    """
    FastAPI dependency for inference service health check.

    Returns:
        Dictionary of inference service health statuses

    Usage:
        @app.get("/health/inference")
        def inference_health(health: dict = Depends(get_inference_health_check)):
            return health
    """
    factory = get_inference_service_factory()
    return factory.health_check()


# Runtime selection dependency
def get_optimal_runtime(model_format: str = "gguf"):
    """
    FastAPI dependency for selecting optimal runtime based on model format.

    Args:
        model_format: Model format (gguf, safetensors, etc.)

    Returns:
        Runtime instance or None

    Usage:
        @app.post("/generate/auto")
        def generate(
            prompt: str,
            model_format: str = "gguf",
            runtime = Depends(get_optimal_runtime)
        ):
            if not runtime:
                raise HTTPException(status_code=503, detail="No runtime available")
            return runtime.generate(prompt)
    """
    factory = get_inference_service_factory()
    runtime_name = factory.select_optimal_runtime(model_format)

    if not runtime_name:
        return None

    return factory.get_runtime(runtime_name)


def get_any_available_runtime():
    """
    FastAPI dependency that returns the first available runtime.

    Returns:
        Any available runtime instance or None

    Usage:
        @app.post("/generate")
        def generate(
            prompt: str,
            runtime = Depends(get_any_available_runtime)
        ):
            if not runtime:
                raise HTTPException(status_code=503, detail="No inference runtime available")
            return runtime.generate(prompt)
    """
    factory = get_inference_service_factory()
    available_runtimes = factory.get_available_runtimes()

    if not available_runtimes:
        return None

    # Return first available runtime
    return factory.get_runtime(available_runtimes[0])


__all__ = [
    # Runtime dependencies
    "get_llamacpp_runtime_dependency",
    "get_transformers_runtime_dependency",
    "get_vllm_runtime_dependency",
    # Model store dependency
    "get_model_store_dependency",
    # Factory dependency
    "get_inference_factory_dependency",
    # Health check
    "get_inference_health_check",
    # Runtime selection
    "get_optimal_runtime",
    "get_any_available_runtime",
]
