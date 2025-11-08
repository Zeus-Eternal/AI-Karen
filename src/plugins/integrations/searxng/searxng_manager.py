"""
SearxNG Manager for AI-Karen
Centralized management for SearxNG plugin instances
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from .searxng_plugin import SearxNGPlugin

logger = logging.getLogger(__name__)

class SearxNGManager:
    """
    Manager for SearxNG plugin instances
    
    Features:
    - Multiple instance management
    - Load balancing
    - Health monitoring
    - Configuration management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.instances: Dict[str, SearxNGPlugin] = {}
        self.default_instance = self.config.get('default_instance', 'primary')
        
    async def initialize(self) -> None:
        """Initialize the SearxNG manager"""
        try:
            # Create default instance
            primary_config = self.config.get('instances', {}).get('primary', {})
            await self.add_instance('primary', primary_config)
            
            # Initialize additional instances
            for name, instance_config in self.config.get('instances', {}).items():
                if name != 'primary':
                    await self.add_instance(name, instance_config)
            
            logger.info(f"SearxNG manager initialized with {len(self.instances)} instances")
            
        except Exception as e:
            logger.error(f"Failed to initialize SearxNG manager: {e}")
            raise
    
    async def add_instance(self, name: str, config: Dict[str, Any]) -> None:
        """Add a new SearxNG instance"""
        try:
            plugin = SearxNGPlugin(config)
            await plugin.initialize()
            self.instances[name] = plugin
            logger.info(f"Added SearxNG instance: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add instance {name}: {e}")
            raise
    
    async def remove_instance(self, name: str) -> bool:
        """Remove a SearxNG instance"""
        if name not in self.instances:
            return False
        
        try:
            await self.instances[name].stop()
            del self.instances[name]
            logger.info(f"Removed SearxNG instance: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove instance {name}: {e}")
            return False
    
    async def search(
        self,
        query: str,
        instance: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform search using specified or default instance
        
        Args:
            query: Search query
            instance: Instance name (uses default if None)
            **kwargs: Additional search parameters
            
        Returns:
            Search results
        """
        instance_name = instance or self.default_instance
        
        if instance_name not in self.instances:
            raise ValueError(f"Instance not found: {instance_name}")
        
        return await self.instances[instance_name].search(query, **kwargs)
    
    async def search_with_fallback(
        self,
        query: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform search with automatic fallback to other instances
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            Search results from first successful instance
        """
        # Try default instance first
        if self.default_instance in self.instances:
            try:
                return await self.instances[self.default_instance].search(query, **kwargs)
            except Exception as e:
                logger.warning(f"Default instance {self.default_instance} failed: {e}")
        
        # Try other instances
        for name, instance in self.instances.items():
            if name == self.default_instance:
                continue
            
            try:
                logger.info(f"Trying fallback instance: {name}")
                return await instance.search(query, **kwargs)
            except Exception as e:
                logger.warning(f"Instance {name} failed: {e}")
                continue
        
        raise Exception("All SearxNG instances failed")
    
    async def get_healthy_instances(self) -> List[str]:
        """Get list of healthy instance names"""
        healthy = []
        
        for name, instance in self.instances.items():
            try:
                if await instance._check_health():
                    healthy.append(name)
            except:
                pass
        
        return healthy
    
    async def deploy_all(self) -> Dict[str, bool]:
        """Deploy all instances"""
        results = {}
        
        for name, instance in self.instances.items():
            try:
                await instance.deploy()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to deploy instance {name}: {e}")
                results[name] = False
        
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all instances"""
        results = {}
        
        for name, instance in self.instances.items():
            try:
                await instance.stop()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to stop instance {name}: {e}")
                results[name] = False
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all instances"""
        status = {
            'total_instances': len(self.instances),
            'default_instance': self.default_instance,
            'instances': {}
        }
        
        for name, instance in self.instances.items():
            status['instances'][name] = instance.get_status()
        
        return status
    
    def get_instance(self, name: str) -> Optional[SearxNGPlugin]:
        """Get specific instance by name"""
        return self.instances.get(name)
    
    def list_instances(self) -> List[str]:
        """List all instance names"""
        return list(self.instances.keys())
