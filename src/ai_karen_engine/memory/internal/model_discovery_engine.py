"""
Internal Model Discovery Engine Module

This module provides internal access to the model discovery engine functionality
for memory and internal components. It re-exports the necessary classes and
functions from the main services module.

This module serves as an abstraction layer for internal components that need
access to model discovery functionality.
"""

from ai_karen_engine.services.model_discovery_engine import (
    ModelDiscoveryEngine,
    ModelInfo,
    ModelType,
    ModalityType,
    ModelCategory,
    ModelSpecialization,
    ModelStatus,
    Modality,
    ResourceRequirements,
    ModelMetadata,
)

# Global instance for internal use
_discovery_engine_instance = None


def get_model_discovery_engine() -> ModelDiscoveryEngine:
    """
    Get or create a singleton instance of the ModelDiscoveryEngine.

    Returns:
        ModelDiscoveryEngine: The discovery engine instance
    """
    global _discovery_engine_instance

    if _discovery_engine_instance is None:
        _discovery_engine_instance = ModelDiscoveryEngine()

    return _discovery_engine_instance


def refresh_discovery_engine() -> int:
    """
    Refresh the discovery engine instance and return the count of discovered models.

    Returns:
        int: Number of discovered models
    """
    global _discovery_engine_instance

    if _discovery_engine_instance is None:
        _discovery_engine_instance = ModelDiscoveryEngine()

    return _discovery_engine_instance.refresh_model_registry()


def cleanup_discovery_engine():
    """Cleanup the discovery engine resources."""
    global _discovery_engine_instance

    if _discovery_engine_instance is not None:
        _discovery_engine_instance.cleanup()
        _discovery_engine_instance = None
