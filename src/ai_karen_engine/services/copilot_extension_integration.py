"""
Copilot extension integration module.

This module provides integration between the copilot capability system
and the existing extension manager, enabling copilot capabilities to be
registered and managed as extensions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from ai_karen_engine.services.copilot_capabilities import (
    CopilotCapability,
    CopilotCapabilityRegistry,
    CopilotCapabilityManager,
    get_capability_registry,
    get_capability_manager
)
from ai_karen_engine.services.tools.contracts import (
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ToolContext,
    create_tool_context
)
from ai_karen_engine.services.tools.copilot_tools import COPILOT_TOOLS
from ai_karen_engine.services.tools.registry import (
    CopilotToolRegistry,
    get_copilot_tool_service
)

logger = logging.getLogger(__name__)


class CopilotExtensionIntegration:
    """
    Integration layer between copilot capabilities and extension system.
    """
    
    def __init__(
        self,
        capability_registry: Optional[CopilotCapabilityRegistry] = None,
        capability_manager: Optional[CopilotCapabilityManager] = None
    ):
        """Initialize copilot extension integration."""
        self.capability_registry = capability_registry or get_capability_registry()
        self.capability_manager = capability_manager or get_capability_manager()
        
        # Extension registration tracking
        self.registered_capabilities: Set[str] = set()
        self.extension_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Integration state
        self.is_initialized = False
        self.initialization_time: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        """
        Initialize copilot extension integration.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing copilot extension integration")
            
            # Register copilot tools with the tool service
            await self._register_copilot_tools()
            
            # Register built-in capabilities
            await self._register_builtin_capabilities()
            
            # Set up extension hooks
            await self._setup_extension_hooks()
            
            self.is_initialized = True
            self.initialization_time = datetime.utcnow()
            
            logger.info("Copilot extension integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize copilot extension integration: {e}")
            return False
    
    async def register_capability_with_extension_manager(
        self,
        capability: CopilotCapability,
        extension_name: Optional[str] = None
    ) -> bool:
        """
        Register a copilot capability with the extension manager.
        
        Args:
            capability: Capability to register
            extension_name: Optional extension name for grouping
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Register with capability registry
            if not self.capability_registry.register_capability(capability):
                return False
            
            # Track registration
            self.registered_capabilities.add(capability.id)
            
            # Store extension metadata
            self.extension_metadata[capability.id] = {
                "extension_name": extension_name or "copilot-core",
                "capability_type": "copilot",
                "registered_at": datetime.utcnow().isoformat(),
                "tool_chain": capability.tool_chain,
                "category": capability.category,
                "privacy_level": capability.privacy_level.value,
                "rbac_level": capability.required_rbac.value
            }
            
            logger.info(f"Registered copilot capability with extension manager: {capability.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register capability {capability.id}: {e}")
            return False
    
    async def unregister_capability_from_extension_manager(
        self,
        capability_id: str
    ) -> bool:
        """
        Unregister a copilot capability from the extension manager.
        
        Args:
            capability_id: ID of capability to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            # Unregister from capability registry
            if not self.capability_registry.unregister_capability(capability_id):
                return False
            
            # Clean up tracking
            self.registered_capabilities.discard(capability_id)
            
            # Clean up metadata
            if capability_id in self.extension_metadata:
                del self.extension_metadata[capability_id]
            
            logger.info(f"Unregistered copilot capability from extension manager: {capability_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister capability {capability_id}: {e}")
            return False
    
    async def execute_capability_via_extension(
        self,
        capability_id: str,
        user_id: str,
        session_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        workspace_root: Optional[str] = None,
        rbac_permissions: Optional[Set[RBACLevel]] = None,
        privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL
    ) -> Dict[str, Any]:
        """
        Execute a copilot capability through the extension system.
        
        Args:
            capability_id: ID of capability to execute
            user_id: User ID for the execution
            session_id: Session ID for the execution
            parameters: Optional parameters for the capability
            workspace_root: Optional workspace root directory
            rbac_permissions: Optional RBAC permissions
            privacy_clearance: Privacy clearance level
            
        Returns:
            Execution result dictionary
        """
        try:
            # Create execution context
            context = create_tool_context(
                user_id=user_id,
                session_id=session_id,
                rbac_permissions=rbac_permissions or {RBACLevel.DEV},
                privacy_clearance=privacy_clearance,
                workspace_root=workspace_root
            )
            
            # Execute capability
            result = await self.capability_manager.execute_capability(
                capability_id, context, parameters
            )
            
            # Convert to dictionary for extension system compatibility
            return {
                "success": result.success,
                "capability_id": capability_id,
                "execution_mode": result.execution_mode.value,
                "result": result.result,
                "artifacts": result.artifacts,
                "execution_time": result.execution_time,
                "citations_count": len(result.citations_used),
                "error": result.error,
                "error_code": result.error_code,
                "correlation_id": result.correlation_id,
                "timestamp": result.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute capability {capability_id}: {e}")
            return {
                "success": False,
                "capability_id": capability_id,
                "error": str(e),
                "error_code": "CAPABILITY_EXECUTION_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_registered_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get list of registered copilot capabilities.
        
        Returns:
            List of capability information dictionaries
        """
        capabilities = []
        
        for capability_id in self.registered_capabilities:
            capability = self.capability_registry.get_capability(capability_id)
            if capability:
                metadata = self.extension_metadata.get(capability_id, {})
                
                capabilities.append({
                    "id": capability.id,
                    "name": capability.name,
                    "description": capability.description,
                    "category": capability.category,
                    "tool_chain": capability.tool_chain,
                    "required_scope": capability.required_scope.value,
                    "required_rbac": capability.required_rbac.value,
                    "privacy_level": capability.privacy_level.value,
                    "supports_batch": capability.supports_batch,
                    "estimated_duration": capability.estimated_duration,
                    "extension_name": metadata.get("extension_name"),
                    "registered_at": metadata.get("registered_at"),
                    "tags": capability.tags
                })
        
        return sorted(capabilities, key=lambda x: x["name"])
    
    def get_capability_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get capabilities filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of capabilities in the specified category
        """
        all_capabilities = self.get_registered_capabilities()
        return [cap for cap in all_capabilities if cap["category"] == category]
    
    def get_capability_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about registered capabilities.
        
        Returns:
            Statistics dictionary
        """
        capabilities = self.get_registered_capabilities()
        
        # Count by category
        categories = {}
        for cap in capabilities:
            category = cap["category"]
            categories[category] = categories.get(category, 0) + 1
        
        # Count by RBAC level
        rbac_levels = {}
        for cap in capabilities:
            rbac = cap["required_rbac"]
            rbac_levels[rbac] = rbac_levels.get(rbac, 0) + 1
        
        # Count by privacy level
        privacy_levels = {}
        for cap in capabilities:
            privacy = cap["privacy_level"]
            privacy_levels[privacy] = privacy_levels.get(privacy, 0) + 1
        
        # Get capability metrics
        capability_metrics = self.capability_manager.get_capability_stats()
        
        return {
            "total_capabilities": len(capabilities),
            "categories": categories,
            "rbac_levels": rbac_levels,
            "privacy_levels": privacy_levels,
            "capability_metrics": capability_metrics,
            "is_initialized": self.is_initialized,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _register_copilot_tools(self) -> bool:
        """Register copilot tools with the tool service."""
        try:
            tool_service = get_copilot_tool_service()
            
            for tool_class in COPILOT_TOOLS:
                tool_instance = tool_class()
                
                # Register with tool service
                success = tool_service.register_tool(tool_instance)
                if success:
                    logger.info(f"Registered copilot tool: {tool_instance.tool_spec.name}")
                else:
                    logger.warning(f"Failed to register copilot tool: {tool_instance.tool_spec.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register copilot tools: {e}")
            return False
    
    async def _register_builtin_capabilities(self) -> bool:
        """Register built-in copilot capabilities."""
        try:
            # Built-in capabilities are already registered by the capability registry
            # during initialization. Here we just track them for extension integration.
            
            builtin_capability_ids = [
                "copilot.review",
                "copilot.debug", 
                "copilot.refactor",
                "copilot.generate_tests"
            ]
            
            for capability_id in builtin_capability_ids:
                capability = self.capability_registry.get_capability(capability_id)
                if capability:
                    await self.register_capability_with_extension_manager(
                        capability, "copilot-builtin"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register built-in capabilities: {e}")
            return False
    
    async def _setup_extension_hooks(self) -> bool:
        """Set up hooks for extension lifecycle events."""
        try:
            # This would integrate with the extension manager's hook system
            # For now, we'll just log that hooks are being set up
            logger.info("Setting up copilot extension hooks")
            
            # TODO: Integrate with actual extension manager hooks
            # - Extension loaded: Register capabilities from extension
            # - Extension unloaded: Unregister capabilities from extension
            # - Extension activated: Enable capabilities
            # - Extension deactivated: Disable capabilities
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up extension hooks: {e}")
            return False


# Global integration instance
_copilot_integration: Optional[CopilotExtensionIntegration] = None


def get_copilot_integration() -> CopilotExtensionIntegration:
    """Get global copilot extension integration instance."""
    global _copilot_integration
    if _copilot_integration is None:
        _copilot_integration = CopilotExtensionIntegration()
    return _copilot_integration


async def initialize_copilot_extension_integration() -> CopilotExtensionIntegration:
    """
    Initialize copilot extension integration.
    
    Returns:
        Initialized integration instance
    """
    global _copilot_integration
    
    _copilot_integration = CopilotExtensionIntegration()
    
    # Initialize the integration
    success = await _copilot_integration.initialize()
    if not success:
        logger.error("Failed to initialize copilot extension integration")
        raise RuntimeError("Copilot extension integration initialization failed")
    
    logger.info("Copilot extension integration initialized successfully")
    return _copilot_integration


# Convenience functions for extension manager integration

async def register_copilot_capabilities_with_extension_manager(
    extension_manager: Any
) -> bool:
    """
    Register copilot capabilities with the extension manager.
    
    Args:
        extension_manager: Extension manager instance
        
    Returns:
        True if registration successful, False otherwise
    """
    try:
        integration = get_copilot_integration()
        
        if not integration.is_initialized:
            await integration.initialize()
        
        # The capabilities are already registered during initialization
        # This function serves as a hook for the extension manager
        
        logger.info("Copilot capabilities registered with extension manager")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register copilot capabilities with extension manager: {e}")
        return False


def get_copilot_capabilities_for_extension_manager() -> List[Dict[str, Any]]:
    """
    Get copilot capabilities formatted for extension manager.
    
    Returns:
        List of capability definitions for extension manager
    """
    try:
        integration = get_copilot_integration()
        return integration.get_registered_capabilities()
        
    except Exception as e:
        logger.error(f"Failed to get copilot capabilities for extension manager: {e}")
        return []