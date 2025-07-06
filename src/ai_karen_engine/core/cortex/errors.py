"""
Kari CORTEX Error Definitions
- Unified error taxonomy for all CORTEX ops
- Use these exceptions for intent/dispatch/plugin errors
- Pure backend, import-safe, no dependencies
"""

class CortexDispatchError(Exception):
    """CORTEX-level error, intent dispatch failed."""

class UnsupportedIntentError(CortexDispatchError):
    """No handler available for this intent."""

class PluginExecutionError(CortexDispatchError):
    """Plugin execution failed."""

class PredictorExecutionError(CortexDispatchError):
    """Predictor execution failed."""

class MemoryRecallError(CortexDispatchError):
    """Memory/contextual recall failed."""

__all__ = [
    "CortexDispatchError",
    "UnsupportedIntentError",
    "PluginExecutionError",
    "PredictorExecutionError",
    "MemoryRecallError"
]
