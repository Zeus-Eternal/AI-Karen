"""
Provider Registry

This service manages model providers and their configurations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ProviderType(Enum):
    """Types of providers."""
    API = "api"
    LOCAL = "local"
    HYBRID = "hybrid"


class ProviderStatus(Enum):
    """Provider status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    id: str
    name: str
    type: ProviderType
    api_endpoint: str = ""
    api_key: str = ""
    model_endpoint: str = ""
    auth_method: str = "bearer"
    rate_limit: int = 60  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    """Information about a provider."""
    config: ProviderConfig
    status: ProviderStatus
    last_check: str = ""
    error_message: str = ""
    capabilities: List[str] = field(default_factory=list)
    supported_models: List[str] = field(default_factory=list)


class ProviderRegistry:
    """
    Provider Registry manages model providers and their configurations.
    
    This service provides a central registry for all providers with their
    configurations, status, and capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Provider Registry.
        
        Args:
            config: Configuration for the provider registry
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Provider storage
        self.providers: Dict[str, ProviderInfo] = {}
        
        # Load initial providers
        self._load_initial_providers()
    
    def _load_initial_providers(self):
        """Load initial providers from configuration."""
        initial_providers = self.config.get("initial_providers", [])
        
        for provider_data in initial_providers:
            provider_config = ProviderConfig(**provider_data.get("config", {}))
            provider_info = ProviderInfo(
                config=provider_config,
                status=ProviderStatus(provider_data.get("status", "inactive"))
            )
            self.register_provider(provider_info)
    
    def register_provider(self, provider_info: ProviderInfo) -> str:
        """
        Register a provider in the registry.
        
        Args:
            provider_info: Information about the provider
            
        Returns:
            The provider ID
        """
        # Store the provider
        self.providers[provider_info.config.id] = provider_info
        
        self.logger.info(f"Registered provider: {provider_info.config.id}")
        return provider_info.config.id
    
    def get_provider(self, provider_id: str) -> Optional[ProviderInfo]:
        """
        Get provider information by ID.
        
        Args:
            provider_id: The provider ID
            
        Returns:
            Provider information if found, None otherwise
        """
        return self.providers.get(provider_id)
    
    def list_providers(
        self, 
        provider_type: Optional[ProviderType] = None,
        status: Optional[ProviderStatus] = None,
        active_only: bool = False
    ) -> List[ProviderInfo]:
        """
        List providers with optional filtering.
        
        Args:
            provider_type: Filter by provider type
            status: Filter by status
            active_only: Only return active providers
            
        Returns:
            List of matching providers
        """
        providers = list(self.providers.values())
        
        # Apply filters
        if provider_type:
            providers = [p for p in providers if p.config.type == provider_type]
        
        if status:
            providers = [p for p in providers if p.status == status]
        
        if active_only:
            providers = [p for p in providers if p.status == ProviderStatus.ACTIVE]
        
        return providers
    
    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update provider information.
        
        Args:
            provider_id: The provider ID to update
            updates: Dictionary of updates
            
        Returns:
            True if updated, False otherwise
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return False
        
        # Apply updates
        if "config" in updates:
            for key, value in updates["config"].items():
                if hasattr(provider.config, key):
                    setattr(provider.config, key, value)
        
        if "status" in updates:
            provider.status = ProviderStatus(updates["status"])
        
        if "capabilities" in updates:
            provider.capabilities = updates["capabilities"]
        
        if "supported_models" in updates:
            provider.supported_models = updates["supported_models"]
        
        return True
    
    def activate_provider(self, provider_id: str) -> bool:
        """
        Activate a provider.
        
        Args:
            provider_id: The provider ID to activate
            
        Returns:
            True if activated, False otherwise
        """
        return self.update_provider(provider_id, {"status": "active"})
    
    def deactivate_provider(self, provider_id: str) -> bool:
        """
        Deactivate a provider.
        
        Args:
            provider_id: The provider ID to deactivate
            
        Returns:
            True if deactivated, False otherwise
        """
        return self.update_provider(provider_id, {"status": "inactive"})
    
    def set_provider_error(self, provider_id: str, error_message: str) -> bool:
        """
        Set provider error status.
        
        Args:
            provider_id: The provider ID
            error_message: The error message
            
        Returns:
            True if updated, False otherwise
        """
        return self.update_provider(
            provider_id, 
            {
                "status": "error",
                "error_message": error_message
            }
        )
    
    def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """
        Get provider configuration.
        
        Args:
            provider_id: The provider ID
            
        Returns:
            Provider configuration if found, None otherwise
        """
        provider = self.get_provider(provider_id)
        return provider.config if provider else None
    
    def get_active_providers(self) -> List[ProviderInfo]:
        """
        Get all active providers.
        
        Returns:
            List of active providers
        """
        return self.list_providers(status=ProviderStatus.ACTIVE)
    
    def get_provider_by_type(self, provider_type: ProviderType) -> List[ProviderInfo]:
        """
        Get providers by type.
        
        Args:
            provider_type: The provider type
            
        Returns:
            List of providers of the specified type
        """
        return self.list_providers(provider_type=provider_type)
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """
        Get provider registry statistics.
        
        Returns:
            Dictionary of statistics
        """
        active_providers = [p for p in self.providers.values() if p.status == ProviderStatus.ACTIVE]
        
        return {
            "total_providers": len(self.providers),
            "active_providers": len(active_providers),
            "by_type": {
                provider_type.value: len(self.get_provider_by_type(provider_type))
                for provider_type in ProviderType
            },
            "by_status": {
                status.value: len(self.list_providers(status=status))
                for status in ProviderStatus
            }
        }
