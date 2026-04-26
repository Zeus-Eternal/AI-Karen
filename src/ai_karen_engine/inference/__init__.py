"""
Inference Engine

Production-ready inference system with support for multiple runtimes:
- Transformers: HuggingFace safetensors models
- Core Helpers: Utility models

Features:
- Automatic runtime selection based on model format
- Unified model store for all models
- Factory pattern for centralized initialization
- Health monitoring and resource tracking
"""

try:
    from .transformers_runtime import TransformersRuntime
except ImportError:
    TransformersRuntime = None

try:
    from .vllm_runtime import VLLMRuntime
except ImportError:
    VLLMRuntime = None

try:
    from .core_helpers_runtime import CoreHelpersRuntime
except ImportError:
    CoreHelpersRuntime = None

# Import model store
try:
    from .model_store import ModelStore
except ImportError:
    ModelStore = None

# Import factory for centralized initialization
from .factory import (
    InferenceServiceConfig,
    InferenceServiceFactory,
    get_inference_service_factory,
    get_transformers_runtime,
    get_model_store,
)

# Import dependencies for FastAPI dependency injection
from .dependencies import (
    get_transformers_runtime_dependency,
    get_model_store_dependency,
    get_inference_factory_dependency,
    get_inference_health_check,
    get_optimal_runtime,
    get_any_available_runtime,
)

__all__ = [
    "TransformersRuntime",
    "VLLMRuntime",
    "CoreHelpersRuntime",
    # Model Store
    "ModelStore",
    # Factory
    "InferenceServiceConfig",
    "InferenceServiceFactory",
    "get_inference_service_factory",
    # Factory convenience functions
    "get_transformers_runtime",
    "get_model_store",
    # Dependencies (FastAPI)
    "get_transformers_runtime_dependency",
    "get_model_store_dependency",
    "get_inference_factory_dependency",
    "get_inference_health_check",
    "get_optimal_runtime",
    "get_any_available_runtime",
]
