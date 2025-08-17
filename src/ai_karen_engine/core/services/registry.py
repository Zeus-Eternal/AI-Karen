"""
Service registry for managing service discovery and metadata.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServiceMetadata:
    """Metadata for a registered service."""
    name: str
    version: str
    description: str
    tags: List[str]
    endpoints: List[str]
    dependencies: List[str]
    health_endpoint: Optional[str] = None
    metrics_endpoint: Optional[str] = None
    documentation_url: Optional[str] = None
    registered_at: datetime = None
    
    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = datetime.now()


class ServiceRegistry:
    """
    Registry for service discovery and metadata management.
    
    Provides a centralized location for services to register themselves
    and for other components to discover available services.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceMetadata] = {}
        self._tags: Dict[str, List[str]] = {}  # tag -> list of service names
        self._endpoints: Dict[str, str] = {}  # endpoint -> service name
    
    def register(self, metadata: ServiceMetadata) -> None:
        """
        Register a service with the registry.
        
        Args:
            metadata: Service metadata
        """
        self._services[metadata.name] = metadata
        
        # Index by tags
        for tag in metadata.tags:
            if tag not in self._tags:
                self._tags[tag] = []
            if metadata.name not in self._tags[tag]:
                self._tags[tag].append(metadata.name)
        
        # Index by endpoints
        for endpoint in metadata.endpoints:
            self._endpoints[endpoint] = metadata.name
        
        logger.info(f"Registered service: {metadata.name}")
    
    def unregister(self, service_name: str) -> None:
        """
        Unregister a service from the registry.
        
        Args:
            service_name: Name of the service to unregister
        """
        if service_name not in self._services:
            return
        
        metadata = self._services[service_name]
        
        # Remove from tag index
        for tag in metadata.tags:
            if tag in self._tags and service_name in self._tags[tag]:
                self._tags[tag].remove(service_name)
                if not self._tags[tag]:
                    del self._tags[tag]
        
        # Remove from endpoint index
        for endpoint in metadata.endpoints:
            if endpoint in self._endpoints:
                del self._endpoints[endpoint]
        
        # Remove from main registry
        del self._services[service_name]
        
        logger.info(f"Unregistered service: {service_name}")
    
    def get_service(self, service_name: str) -> Optional[ServiceMetadata]:
        """
        Get service metadata by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service metadata or None if not found
        """
        return self._services.get(service_name)
    
    def list_services(self) -> List[ServiceMetadata]:
        """
        List all registered services.
        
        Returns:
            List of service metadata
        """
        return list(self._services.values())
    
    def find_by_tag(self, tag: str) -> List[ServiceMetadata]:
        """
        Find services by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of service metadata matching the tag
        """
        service_names = self._tags.get(tag, [])
        return [self._services[name] for name in service_names]
    
    def find_by_endpoint(self, endpoint: str) -> Optional[ServiceMetadata]:
        """
        Find service by endpoint.
        
        Args:
            endpoint: Endpoint to search for
            
        Returns:
            Service metadata or None if not found
        """
        service_name = self._endpoints.get(endpoint)
        return self._services.get(service_name) if service_name else None
    
    def get_dependencies(self, service_name: str) -> List[ServiceMetadata]:
        """
        Get dependencies for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of dependency service metadata
        """
        service = self.get_service(service_name)
        if not service:
            return []
        
        dependencies = []
        for dep_name in service.dependencies:
            dep_service = self.get_service(dep_name)
            if dep_service:
                dependencies.append(dep_service)
        
        return dependencies
    
    def get_dependents(self, service_name: str) -> List[ServiceMetadata]:
        """
        Get services that depend on the given service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of dependent service metadata
        """
        dependents = []
        for service in self._services.values():
            if service_name in service.dependencies:
                dependents.append(service)
        
        return dependents
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_services": len(self._services),
            "total_tags": len(self._tags),
            "total_endpoints": len(self._endpoints),
            "services_by_tag": {tag: len(services) for tag, services in self._tags.items()},
            "registered_services": list(self._services.keys())
        }


# Global service registry instance
_registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return _registry