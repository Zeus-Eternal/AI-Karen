"""
Fallback Mechanisms for Service Failures

This module provides fallback handlers for different types of services
to ensure graceful degradation when services fail.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .error_recovery_manager import get_error_recovery_manager


class FallbackType(Enum):
    """Types of fallback mechanisms"""
    CACHE = "cache"
    STATIC = "static"
    SIMPLIFIED = "simplified"
    PROXY = "proxy"
    MOCK = "mock"
    DEGRADED = "degraded"


@dataclass
class FallbackConfig:
    """Configuration for a fallback mechanism"""
    fallback_type: FallbackType
    priority: int = 1  # Lower number = higher priority
    timeout: int = 30  # seconds
    retry_after: int = 300  # seconds before trying main service again
    config: Dict[str, Any] = None


class FallbackHandler(ABC):
    """Abstract base class for fallback handlers"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        self.service_name = service_name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        self.active = False
        self.activation_time = None
    
    @abstractmethod
    async def activate(self) -> bool:
        """Activate the fallback mechanism"""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """Deactivate the fallback mechanism"""
        pass
    
    @abstractmethod
    async def handle_request(self, *args, **kwargs) -> Any:
        """Handle a request using the fallback mechanism"""
        pass
    
    async def is_ready(self) -> bool:
        """Check if fallback is ready to handle requests"""
        return self.active


class CacheFallbackHandler(FallbackHandler):
    """Fallback handler that serves cached responses"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        super().__init__(service_name, config)
        self.cache: Dict[str, Any] = {}
        self.cache_file = Path(f"cache/{service_name}_fallback_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        
    async def activate(self) -> bool:
        """Activate cache fallback"""
        try:
            # Load existing cache if available
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            
            self.active = True
            self.logger.info(f"Activated cache fallback for {self.service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate cache fallback: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Deactivate cache fallback"""
        try:
            # Save cache to file
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            
            self.active = False
            self.logger.info(f"Deactivated cache fallback for {self.service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate cache fallback: {e}")
            return False
    
    async def handle_request(self, request_key: str, *args, **kwargs) -> Any:
        """Handle request using cached response"""
        if request_key in self.cache:
            self.logger.debug(f"Serving cached response for {request_key}")
            return self.cache[request_key]
        else:
            raise Exception(f"No cached response available for {request_key}")
    
    def cache_response(self, request_key: str, response: Any):
        """Cache a response for future fallback use"""
        self.cache[request_key] = response


class StaticFallbackHandler(FallbackHandler):
    """Fallback handler that serves static responses"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        super().__init__(service_name, config)
        self.static_responses = config.config.get('static_responses', {})
        self.default_response = config.config.get('default_response')
    
    async def activate(self) -> bool:
        """Activate static fallback"""
        self.active = True
        self.logger.info(f"Activated static fallback for {self.service_name}")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate static fallback"""
        self.active = False
        self.logger.info(f"Deactivated static fallback for {self.service_name}")
        return True
    
    async def handle_request(self, request_type: str = None, *args, **kwargs) -> Any:
        """Handle request using static response"""
        if request_type and request_type in self.static_responses:
            return self.static_responses[request_type]
        elif self.default_response is not None:
            return self.default_response
        else:
            raise Exception(f"No static response available for {request_type}")


class SimplifiedFallbackHandler(FallbackHandler):
    """Fallback handler that provides simplified functionality"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        super().__init__(service_name, config)
        self.simplified_handler = config.config.get('simplified_handler')
    
    async def activate(self) -> bool:
        """Activate simplified fallback"""
        if not self.simplified_handler:
            return False
        
        self.active = True
        self.logger.info(f"Activated simplified fallback for {self.service_name}")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate simplified fallback"""
        self.active = False
        self.logger.info(f"Deactivated simplified fallback for {self.service_name}")
        return True
    
    async def handle_request(self, *args, **kwargs) -> Any:
        """Handle request using simplified functionality"""
        if asyncio.iscoroutinefunction(self.simplified_handler):
            return await self.simplified_handler(*args, **kwargs)
        else:
            return self.simplified_handler(*args, **kwargs)


class ProxyFallbackHandler(FallbackHandler):
    """Fallback handler that proxies to alternative service"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        super().__init__(service_name, config)
        self.proxy_service = config.config.get('proxy_service')
        self.proxy_endpoint = config.config.get('proxy_endpoint')
    
    async def activate(self) -> bool:
        """Activate proxy fallback"""
        if not (self.proxy_service or self.proxy_endpoint):
            return False
        
        self.active = True
        self.logger.info(f"Activated proxy fallback for {self.service_name}")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate proxy fallback"""
        self.active = False
        self.logger.info(f"Deactivated proxy fallback for {self.service_name}")
        return True
    
    async def handle_request(self, *args, **kwargs) -> Any:
        """Handle request by proxying to alternative service"""
        if self.proxy_service:
            # Proxy to another service in the system
            from .service_registry import ServiceRegistry
            registry = ServiceRegistry()
            service = registry.get_service(self.proxy_service)
            
            if service and hasattr(service, 'handle_request'):
                return await service.handle_request(*args, **kwargs)
            else:
                raise Exception(f"Proxy service {self.proxy_service} not available")
        
        elif self.proxy_endpoint:
            # Proxy to external HTTP endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.proxy_endpoint, json=kwargs) as response:
                    if response.status >= 400:
                        raise Exception(f"Proxy request failed: {response.status}")
                    return await response.json()


class MockFallbackHandler(FallbackHandler):
    """Fallback handler that provides mock responses"""
    
    def __init__(self, service_name: str, config: FallbackConfig):
        super().__init__(service_name, config)
        self.mock_generator = config.config.get('mock_generator')
        self.mock_data = config.config.get('mock_data', {})
    
    async def activate(self) -> bool:
        """Activate mock fallback"""
        self.active = True
        self.logger.info(f"Activated mock fallback for {self.service_name}")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate mock fallback"""
        self.active = False
        self.logger.info(f"Deactivated mock fallback for {self.service_name}")
        return True
    
    async def handle_request(self, *args, **kwargs) -> Any:
        """Handle request using mock response"""
        if self.mock_generator:
            if asyncio.iscoroutinefunction(self.mock_generator):
                return await self.mock_generator(*args, **kwargs)
            else:
                return self.mock_generator(*args, **kwargs)
        else:
            # Return mock data based on request type
            request_type = kwargs.get('type', 'default')
            return self.mock_data.get(request_type, {"status": "mock_response"})


class FallbackManager:
    """
    Manages fallback mechanisms for all services
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fallback_handlers: Dict[str, List[FallbackHandler]] = {}
        self.active_fallbacks: Dict[str, FallbackHandler] = {}
        
        # Register with error recovery manager
        self.error_recovery_manager = get_error_recovery_manager()
        self._register_fallback_handlers()
    
    def _register_fallback_handlers(self):
        """Register fallback handlers with error recovery manager"""
        async def fallback_wrapper(service_name: str):
            """Wrapper function for error recovery manager"""
            await self.activate_fallback(service_name)
        
        # This will be called by error recovery manager when services fail
        self.error_recovery_manager.register_alert_handler(
            self._handle_service_failure_alert
        )
    
    def register_fallback(self, service_name: str, handler: FallbackHandler):
        """Register a fallback handler for a service"""
        if service_name not in self.fallback_handlers:
            self.fallback_handlers[service_name] = []
        
        self.fallback_handlers[service_name].append(handler)
        
        # Sort by priority (lower number = higher priority)
        self.fallback_handlers[service_name].sort(key=lambda h: h.config.priority)
        
        self.logger.info(f"Registered {handler.config.fallback_type.value} fallback for {service_name}")
        
        # Register fallback handler with error recovery manager
        self.error_recovery_manager.register_fallback_handler(
            service_name, 
            lambda: self.activate_fallback(service_name)
        )
    
    def register_cache_fallback(self, service_name: str, priority: int = 1):
        """Register a cache-based fallback for a service"""
        config = FallbackConfig(FallbackType.CACHE, priority=priority)
        handler = CacheFallbackHandler(service_name, config)
        self.register_fallback(service_name, handler)
        return handler
    
    def register_static_fallback(self, service_name: str, static_responses: Dict[str, Any],
                               default_response: Any = None, priority: int = 2):
        """Register a static response fallback for a service"""
        config = FallbackConfig(
            FallbackType.STATIC, 
            priority=priority,
            config={
                'static_responses': static_responses,
                'default_response': default_response
            }
        )
        handler = StaticFallbackHandler(service_name, config)
        self.register_fallback(service_name, handler)
        return handler
    
    def register_simplified_fallback(self, service_name: str, 
                                   simplified_handler: Callable,
                                   priority: int = 3):
        """Register a simplified functionality fallback for a service"""
        config = FallbackConfig(
            FallbackType.SIMPLIFIED,
            priority=priority,
            config={'simplified_handler': simplified_handler}
        )
        handler = SimplifiedFallbackHandler(service_name, config)
        self.register_fallback(service_name, handler)
        return handler
    
    def register_proxy_fallback(self, service_name: str, 
                              proxy_service: str = None,
                              proxy_endpoint: str = None,
                              priority: int = 4):
        """Register a proxy fallback for a service"""
        config = FallbackConfig(
            FallbackType.PROXY,
            priority=priority,
            config={
                'proxy_service': proxy_service,
                'proxy_endpoint': proxy_endpoint
            }
        )
        handler = ProxyFallbackHandler(service_name, config)
        self.register_fallback(service_name, handler)
        return handler
    
    def register_mock_fallback(self, service_name: str,
                             mock_generator: Callable = None,
                             mock_data: Dict[str, Any] = None,
                             priority: int = 5):
        """Register a mock response fallback for a service"""
        config = FallbackConfig(
            FallbackType.MOCK,
            priority=priority,
            config={
                'mock_generator': mock_generator,
                'mock_data': mock_data or {}
            }
        )
        handler = MockFallbackHandler(service_name, config)
        self.register_fallback(service_name, handler)
        return handler
    
    async def activate_fallback(self, service_name: str) -> bool:
        """Activate the highest priority fallback for a service"""
        if service_name not in self.fallback_handlers:
            self.logger.warning(f"No fallback handlers registered for {service_name}")
            return False
        
        # Try fallback handlers in priority order
        for handler in self.fallback_handlers[service_name]:
            try:
                if await handler.activate():
                    self.active_fallbacks[service_name] = handler
                    self.logger.info(f"Activated {handler.config.fallback_type.value} fallback for {service_name}")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to activate fallback {handler.config.fallback_type.value} for {service_name}: {e}")
        
        self.logger.error(f"All fallback mechanisms failed for {service_name}")
        return False
    
    async def deactivate_fallback(self, service_name: str) -> bool:
        """Deactivate the active fallback for a service"""
        if service_name not in self.active_fallbacks:
            return True
        
        handler = self.active_fallbacks[service_name]
        try:
            success = await handler.deactivate()
            if success:
                del self.active_fallbacks[service_name]
                self.logger.info(f"Deactivated fallback for {service_name}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to deactivate fallback for {service_name}: {e}")
            return False
    
    async def handle_fallback_request(self, service_name: str, *args, **kwargs) -> Any:
        """Handle a request using the active fallback for a service"""
        if service_name not in self.active_fallbacks:
            raise Exception(f"No active fallback for service {service_name}")
        
        handler = self.active_fallbacks[service_name]
        return await handler.handle_request(*args, **kwargs)
    
    def is_fallback_active(self, service_name: str) -> bool:
        """Check if a fallback is currently active for a service"""
        return service_name in self.active_fallbacks
    
    def get_active_fallback_type(self, service_name: str) -> Optional[FallbackType]:
        """Get the type of active fallback for a service"""
        if service_name in self.active_fallbacks:
            return self.active_fallbacks[service_name].config.fallback_type
        return None
    
    async def _handle_service_failure_alert(self, alert_data: Dict[str, Any]):
        """Handle service failure alerts from error recovery manager"""
        message = alert_data.get('message', '')
        
        # Extract service name from alert message
        if 'Circuit breaker opened for service' in message:
            service_name = message.split('service ')[-1]
            await self.activate_fallback(service_name)
        elif 'Service' in message and 'failed' in message:
            # Parse service name from failure message
            parts = message.split()
            if len(parts) > 1:
                service_name = parts[1]
                await self.activate_fallback(service_name)
    
    async def get_fallback_status(self) -> Dict[str, Any]:
        """Get status of all fallback mechanisms"""
        status = {
            "active_fallbacks": {},
            "registered_fallbacks": {}
        }
        
        # Active fallbacks
        for service_name, handler in self.active_fallbacks.items():
            status["active_fallbacks"][service_name] = {
                "type": handler.config.fallback_type.value,
                "priority": handler.config.priority,
                "active_since": handler.activation_time.isoformat() if handler.activation_time else None
            }
        
        # Registered fallbacks
        for service_name, handlers in self.fallback_handlers.items():
            status["registered_fallbacks"][service_name] = [
                {
                    "type": h.config.fallback_type.value,
                    "priority": h.config.priority
                }
                for h in handlers
            ]
        
        return status


# Global instance for easy access
_fallback_manager = None

def get_fallback_manager() -> FallbackManager:
    """Get global fallback manager instance"""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager