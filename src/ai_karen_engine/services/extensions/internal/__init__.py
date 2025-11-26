"""
Internal modules for the extensions domain.

This package contains implementation details that are not part of the public API.
These modules should only be imported by other modules within the extensions domain.
"""

# Import all internal modules for convenience
from .extension_schemas import (
    ExtensionSchema, 
    ExtensionManifestSchema, 
    ExtensionExecutionSchema,
    ExtensionConfigSchema,
    ExtensionAuthSchema,
    ExtensionPermissionSchema
)
from .extension_validation import (
    ExtensionValidator, 
    ManifestValidator, 
    ExecutionValidator,
    ConfigValidator,
    AuthValidator
)
from .extension_metrics import (
    ExtensionMetrics, 
    ExtensionPerformanceMetrics, 
    ExtensionTaskMetrics
)

__all__ = [
    # Schemas
    "ExtensionSchema",
    "ExtensionManifestSchema", 
    "ExtensionExecutionSchema",
    "ExtensionConfigSchema",
    "ExtensionAuthSchema",
    "ExtensionPermissionSchema",
    
    # Validators
    "ExtensionValidator",
    "ManifestValidator",
    "ExecutionValidator",
    "ConfigValidator",
    "AuthValidator",
    
    # Metrics
    "ExtensionMetrics",
    "ExtensionPerformanceMetrics",
    "ExtensionTaskMetrics",
]