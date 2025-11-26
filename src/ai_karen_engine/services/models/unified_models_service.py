"""
Unified Models Service - Primary Facade

This service provides a unified interface for all model operations in the KAREN AI system.
It consolidates functionality from:
- ModelService
- ModelDiscoveryService
- ModelValidationService
- ModelProviderService
- ModelRouterService
- ModelLoadService
- ModelSwitchService
- ModelCapabilitiesService
- ModelLibraryService
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

# Create a minimal base service class for development
class BaseService:
    def __init__(self, config=None):
        self.config = config or {}
    
    async def initialize(self):
        pass
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    async def health_check(self):
        return {"status": "healthy"}
    
    def increment_counter(self, name, value=1, tags=None):
        pass
    
    def record_timing(self, name, value, tags=None):
        pass
    
    async def handle_error(self, error, context=None):
        pass

def get_settings():
    return {}

# Import internal helper services
try:
    from .internal.model_discovery import ModelDiscoveryHelper
    from .internal.model_validation import ModelValidationHelper
    from .internal.model_provider import ModelProviderHelper
    from .internal.model_routing import ModelRoutingHelper
    from .internal.model_management import ModelManagementHelper
except ImportError:
    # Fallback for development when the internal services aren't available
    class ModelDiscoveryHelper:
        def __init__(self, config):
            self.config = config
        
        async def initialize(self):
            pass
        
        async def start(self):
            pass
        
        async def stop(self):
            pass
        
        async def health_check(self):
            return {"status": "healthy"}
        
        async def discover_models(self, data, context=None):
            return {"status": "success", "models": []}

    class ModelValidationHelper:
        def __init__(self, config):
            self.config = config
        
        async def initialize(self):
            pass
        
        async def start(self):
            pass
        
        async def stop(self):
            pass
        
        async def health_check(self):
            return {"status": "healthy"}
        
        async def validate_model(self, data, context=None):
            return {"status": "success", "valid": True}
        
        async def get_model_capabilities(self, data, context=None):
            return {"status": "success", "capabilities": {}}

    class ModelProviderHelper:
        def __init__(self, config):
            self.config = config
        
        async def initialize(self):
            pass
        
        async def start(self):
            pass
        
        async def stop(self):
            pass
        
        async def health_check(self):
            return {"status": "healthy"}
        
        async def execute_model(self, data, context=None):
            return {"status": "success", "result": {}}

    class ModelRoutingHelper:
        def __init__(self, config):
            self.config = config
        
        async def initialize(self):
            pass
        
        async def start(self):
            pass
        
        async def stop(self):
            pass
        
        async def health_check(self):
            return {"status": "healthy"}
        
        async def switch_model(self, data, context=None):
            return {"status": "success", "switched": True}

    class ModelManagementHelper:
        def __init__(self, config):
            self.config = config
        
        async def initialize(self):
            pass
        
        async def start(self):
            pass
        
        async def stop(self):
            pass
        
        async def health_check(self):
            return {"status": "healthy"}
        
        async def load_model(self, data, context=None):
            return {"status": "success", "loaded": True}
        
        async def unload_model(self, data, context=None):
            return {"status": "success", "unloaded": True}

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of models supported by the unified models service."""
    LANGUAGE = "language"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    EMBEDDING = "embedding"
    GENERATIVE = "generative"


class ModelOperation(Enum):
    """Types of model operations supported by the unified models service."""
    DISCOVER = "discover"
    VALIDATE = "validate"
    LOAD = "load"
    UNLOAD = "unload"
    SWITCH = "switch"
    EXECUTE = "execute"
    GET_CAPABILITIES = "get_capabilities"
    GET_STATUS = "get_status"


class UnifiedModelsService(BaseService):
    """
    Unified Models Service - Primary Facade
    
    This service provides a unified interface for all model operations in the KAREN AI system.
    It consolidates functionality from multiple model-related services into a single, cohesive API.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the unified models service with configuration."""
        super().__init__(config=config or {})
        
        # Initialize internal helper services
        self.model_discovery = ModelDiscoveryHelper(self.config)
        self.model_validation = ModelValidationHelper(self.config)
        self.model_provider = ModelProviderHelper(self.config)
        self.model_routing = ModelRoutingHelper(self.config)
        self.model_management = ModelManagementHelper(self.config)
        
        # Model operation handlers
        self.operation_handlers = {
            ModelOperation.DISCOVER: self._discover_models,
            ModelOperation.VALIDATE: self._validate_model,
            ModelOperation.LOAD: self._load_model,
            ModelOperation.UNLOAD: self._unload_model,
            ModelOperation.SWITCH: self._switch_model,
            ModelOperation.EXECUTE: self._execute_model,
            ModelOperation.GET_CAPABILITIES: self._get_model_capabilities,
            ModelOperation.GET_STATUS: self._get_model_status
        }
        
        # Active models
        self.active_models = {}
        self.default_model = None
    
    async def _initialize_service(self) -> None:
        """Initialize the unified models service and its internal helpers."""
        logger.info("Initializing Unified Models Service")
        
        # Initialize internal helper services
        await self.model_discovery.initialize()
        await self.model_validation.initialize()
        await self.model_provider.initialize()
        await self.model_routing.initialize()
        await self.model_management.initialize()
        
        # Load default model if specified
        default_model_id = self.config.get("default_model_id")
        if default_model_id:
            try:
                await self._load_model({"model_id": default_model_id, "set_as_default": True})
            except Exception as e:
                logger.warning(f"Failed to load default model {default_model_id}: {e}")
        
        logger.info("Unified Models Service initialized successfully")
    
    async def _start_service(self) -> None:
        """Start the unified models service and its internal helpers."""
        logger.info("Starting Unified Models Service")
        
        # Start internal helper services
        await self.model_discovery.start()
        await self.model_validation.start()
        await self.model_provider.start()
        await self.model_routing.start()
        await self.model_management.start()
        
        logger.info("Unified Models Service started successfully")
    
    async def _stop_service(self) -> None:
        """Stop the unified models service and its internal helpers."""
        logger.info("Stopping Unified Models Service")
        
        # Unload all active models
        for model_id in list(self.active_models.keys()):
            try:
                await self._unload_model({"model_id": model_id})
            except Exception as e:
                logger.error(f"Error unloading model {model_id}: {e}")
        
        # Stop internal helper services
        await self.model_management.stop()
        await self.model_routing.stop()
        await self.model_provider.stop()
        await self.model_validation.stop()
        await self.model_discovery.stop()
        
        logger.info("Unified Models Service stopped successfully")
    
    async def _health_check_service(self) -> Dict[str, Any]:
        """Check the health of the unified models service and its internal helpers."""
        health = {
            "status": "healthy",
            "details": {}
        }
        
        # Check health of internal helper services
        discovery_health = await self.model_discovery.health_check()
        validation_health = await self.model_validation.health_check()
        provider_health = await self.model_provider.health_check()
        routing_health = await self.model_routing.health_check()
        management_health = await self.model_management.health_check()
        
        # Determine overall health status
        if (discovery_health.get("status") != "healthy" or
            validation_health.get("status") != "healthy" or
            provider_health.get("status") != "healthy" or
            routing_health.get("status") != "healthy" or
            management_health.get("status") != "healthy"):
            health["status"] = "unhealthy"
        
        # Add details for each service
        health["details"] = {
            "model_discovery": discovery_health,
            "model_validation": validation_health,
            "model_provider": provider_health,
            "model_routing": routing_health,
            "model_management": management_health,
            "active_models_count": len(self.active_models),
            "default_model": self.default_model
        }
        
        return health
    
    async def execute_model_operation(
        self,
        operation: ModelOperation,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a model operation.
        
        Args:
            operation: The operation to perform
            data: Data required for the operation
            context: Additional context for the operation
            
        Returns:
            Result of the operation
        """
        start_time = datetime.now()
        self.increment_counter("model_operations_total", tags={
            "operation": operation.value
        })
        
        try:
            # Get the appropriate handler
            handler = self.operation_handlers.get(operation)
            if not handler:
                raise ValueError(f"Unsupported operation: {operation.value}")
            
            # Execute the operation
            result = await handler(data, context)
            
            # Record success metric
            duration = (datetime.now() - start_time).total_seconds()
            self.increment_counter("model_operations_success", tags={
                "operation": operation.value
            })
            self.record_timing("model_operation_duration", duration, tags={
                "operation": operation.value
            })
            
            return result
            
        except Exception as e:
            # Record error metric
            self.increment_counter("model_operations_errors", tags={
                "operation": operation.value,
                "error_type": type(e).__name__
            })
            
            # Handle the error
            await self.handle_error(e, {
                "operation": operation.value,
                "data": data,
                "context": context
            })
            
            raise
    
    # Model Operation Handlers
    async def _discover_models(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Discover available models."""
        return await self.model_discovery.discover_models(data, context)
    
    async def _validate_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a model."""
        return await self.model_validation.validate_model(data, context)
    
    async def _load_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load a model."""
        result = await self.model_management.load_model(data, context)
        
        # Update active models if successful
        if result.get("status") == "success":
            model_id = data.get("model_id")
            self.active_models[model_id] = {
                "loaded_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Set as default if requested
            if data.get("set_as_default"):
                self.default_model = model_id
        
        return result
    
    async def _unload_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Unload a model."""
        result = await self.model_management.unload_model(data, context)
        
        # Update active models if successful
        if result.get("status") == "success":
            model_id = data.get("model_id")
            if model_id in self.active_models:
                del self.active_models[model_id]
            
            # Update default model if necessary
            if self.default_model == model_id:
                self.default_model = None
        
        return result
    
    async def _switch_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Switch to a different model."""
        from_model_id = data.get("from_model_id")
        to_model_id = data.get("to_model_id")
        
        # Load the new model if not already loaded
        if to_model_id not in self.active_models:
            load_result = await self._load_model({"model_id": to_model_id}, context)
            if load_result.get("status") != "success":
                return load_result
        
        # Switch the model
        result = await self.model_routing.switch_model(data, context)
        
        # Update default model if successful
        if result.get("status") == "success" and data.get("set_as_default"):
            self.default_model = to_model_id
        
        return result
    
    async def _execute_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a model."""
        model_id = data.get("model_id", self.default_model)
        
        if not model_id:
            return {
                "status": "error",
                "message": "No model specified and no default model available"
            }
        
        if model_id not in self.active_models:
            return {
                "status": "error",
                "message": f"Model {model_id} is not loaded"
            }
        
        # Route the execution to the appropriate provider
        return await self.model_provider.execute_model({
            **data,
            "model_id": model_id
        }, context)
    
    async def _get_model_capabilities(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get model capabilities."""
        return await self.model_validation.get_model_capabilities(data, context)
    
    async def _get_model_status(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get model status."""
        model_id = data.get("model_id")
        
        if not model_id:
            return {
                "status": "error",
                "message": "Model ID is required"
            }
        
        is_loaded = model_id in self.active_models
        is_default = model_id == self.default_model
        
        return {
            "status": "success",
            "model_id": model_id,
            "is_loaded": is_loaded,
            "is_default": is_default,
            "loaded_at": self.active_models.get(model_id, {}).get("loaded_at") if is_loaded else None
        }
    
    # Convenience Methods
    async def discover_models_by_type(self, model_type: ModelType) -> Dict[str, Any]:
        """
        Discover models of a specific type.
        
        Args:
            model_type: The type of models to discover
            
        Returns:
            List of discovered models
        """
        return await self.execute_model_operation(
            ModelOperation.DISCOVER,
            {"model_type": model_type.value}
        )
    
    async def get_available_models(self) -> Dict[str, Any]:
        """
        Get all available models.
        
        Returns:
            List of all available models
        """
        return await self.execute_model_operation(
            ModelOperation.DISCOVER,
            {}
        )
    
    async def load_default_model(self) -> Dict[str, Any]:
        """
        Load the default model.
        
        Returns:
            Result of the operation
        """
        if not self.default_model:
            return {
                "status": "error",
                "message": "No default model configured"
            }
        
        return await self.execute_model_operation(
            ModelOperation.LOAD,
            {"model_id": self.default_model, "set_as_default": True}
        )
    
    async def execute_with_default_model(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an operation with the default model.
        
        Args:
            data: Data for the operation
            context: Additional context for the operation
            
        Returns:
            Result of the operation
        """
        return await self.execute_model_operation(
            ModelOperation.EXECUTE,
            data,
            context
        )
    
    async def get_active_models(self) -> Dict[str, Any]:
        """
        Get all active models.
        
        Returns:
            List of active models
        """
        return {
            "status": "success",
            "active_models": list(self.active_models.keys()),
            "default_model": self.default_model
        }