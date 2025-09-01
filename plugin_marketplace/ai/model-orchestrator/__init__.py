"""
Model Orchestrator Plugin

Provides comprehensive model management capabilities including:
- CLI and web UI interfaces for model operations
- HuggingFace model browsing and downloading
- Filesystem layout normalization
- Registry management with integrity verification
- Integration with existing LLM services
"""

# Handle different import contexts
try:
    from .service import ModelOrchestratorService
except ImportError:
    # Fallback for direct module loading
    import importlib.util
    import os
    service_path = os.path.join(os.path.dirname(__file__), 'service.py')
    spec = importlib.util.spec_from_file_location("service", service_path)
    service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service_module)
    ModelOrchestratorService = service_module.ModelOrchestratorService

# Plugin metadata
__plugin_name__ = "ModelOrchestrator"
__plugin_version__ = "1.0.0"
__plugin_type__ = "ai"
__plugin_description__ = "Comprehensive model management system providing CLI and web UI for production-grade model operations"

# Plugin registration
def register_plugin():
    """Register the Model Orchestrator plugin with the system."""
    return {
        "name": __plugin_name__,
        "version": __plugin_version__,
        "type": __plugin_type__,
        "description": __plugin_description__,
        "service_class": ModelOrchestratorService,
        "capabilities": [
            "model_listing",
            "model_download", 
            "filesystem_migration",
            "registry_management",
            "garbage_collection",
            "cli_interface",
            "web_api",
            "rbac_integration"
        ]
    }

__all__ = ["ModelOrchestratorService", "register_plugin"]