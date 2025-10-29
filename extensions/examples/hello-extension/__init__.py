"""
Hello Extension - A simple example extension for the AI Karen Extensions System.

This extension demonstrates the basic capabilities of the extension system,
including API endpoints, UI components, and health monitoring.
"""

from src.extensions.base import BaseExtension
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timezone


class HelloExtension(BaseExtension):
    """
    Hello Extension - A simple demonstration extension.
    
    This extension provides basic greeting functionality and serves as an
    example of how to build extensions for the AI Karen platform.
    """
    
    async def _initialize(self) -> None:
        """Initialize the Hello Extension."""
        self.logger.info("Hello Extension initializing...")
        
        # Initialize extension-specific resources
        self.greeting_count = 0
        self.start_time = datetime.now(timezone.utc)
        
        # Simulate some initialization work
        await asyncio.sleep(0.1)
        
        self.logger.info("Hello Extension initialized successfully")
    
    async def _shutdown(self) -> None:
        """Cleanup the Hello Extension."""
        self.logger.info("Hello Extension shutting down...")
        
        # Log final statistics
        self.logger.info(f"Hello Extension served {self.greeting_count} greetings")
        
        self.logger.info("Hello Extension shut down successfully")
    
    def create_api_router(self) -> Optional[APIRouter]:
        """Create API routes for the Hello Extension."""
        router = APIRouter()
        
        @router.get("/hello")
        async def get_hello():
            """Get a simple hello message."""
            self.greeting_count += 1
            return {
                "message": "Hello from the AI Karen Extension System!",
                "extension": self.manifest.name,
                "version": self.manifest.version,
                "greeting_number": self.greeting_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        @router.get("/hello/{name}")
        async def get_hello_name(name: str):
            """Get a personalized hello message."""
            if not name or len(name.strip()) == 0:
                raise HTTPException(status_code=400, detail="Name cannot be empty")
            
            if len(name) > 50:
                raise HTTPException(status_code=400, detail="Name too long")
            
            self.greeting_count += 1
            return {
                "message": f"Hello, {name}! Welcome to the AI Karen Extension System!",
                "extension": self.manifest.name,
                "version": self.manifest.version,
                "greeting_number": self.greeting_count,
                "personalized": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        @router.get("/stats")
        async def get_stats():
            """Get extension statistics."""
            uptime = datetime.now(timezone.utc) - self.start_time
            
            return {
                "extension": self.manifest.name,
                "version": self.manifest.version,
                "uptime_seconds": uptime.total_seconds(),
                "greeting_count": self.greeting_count,
                "start_time": self.start_time.isoformat(),
                "status": self._status.value,
                "healthy": self.is_healthy()
            }
        
        @router.get("/info")
        async def get_info():
            """Get extension information."""
            return {
                "name": self.manifest.name,
                "display_name": self.manifest.display_name,
                "description": self.manifest.description,
                "version": self.manifest.version,
                "author": self.manifest.author,
                "category": self.manifest.category,
                "capabilities": {
                    "provides_ui": self.manifest.capabilities.provides_ui,
                    "provides_api": self.manifest.capabilities.provides_api,
                    "provides_background_tasks": self.manifest.capabilities.provides_background_tasks,
                    "provides_webhooks": self.manifest.capabilities.provides_webhooks
                },
                "resource_limits": {
                    "max_memory_mb": self.manifest.resources.max_memory_mb,
                    "max_cpu_percent": self.manifest.resources.max_cpu_percent,
                    "max_disk_mb": self.manifest.resources.max_disk_mb
                }
            }
        
        return router
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Hello Extension."""
        components = super().create_ui_components()
        
        # Add custom dashboard data
        uptime = datetime.now(timezone.utc) - self.start_time
        
        components["hello_dashboard"] = {
            "title": "Hello Extension Dashboard",
            "description": "Simple greeting extension with statistics",
            "data": {
                "greeting_count": self.greeting_count,
                "uptime_hours": round(uptime.total_seconds() / 3600, 2),
                "status": self._status.value,
                "healthy": self.is_healthy(),
                "start_time": self.start_time.isoformat()
            },
            "widgets": [
                {
                    "type": "metric",
                    "title": "Total Greetings",
                    "value": self.greeting_count,
                    "icon": "👋"
                },
                {
                    "type": "metric", 
                    "title": "Uptime (hours)",
                    "value": round(uptime.total_seconds() / 3600, 2),
                    "icon": "⏰"
                },
                {
                    "type": "status",
                    "title": "Extension Status",
                    "value": self._status.value,
                    "healthy": self.is_healthy(),
                    "icon": "✅" if self.is_healthy() else "❌"
                }
            ]
        }
        
        return components
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform extension health check."""
        base_health = await super().health_check()
        
        # Add extension-specific health metrics
        uptime = datetime.now(timezone.utc) - self.start_time
        
        base_health.update({
            "greeting_count": self.greeting_count,
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "memory_usage": "unknown",  # Would be calculated by resource monitor
            "cpu_usage": "unknown",     # Would be calculated by resource monitor
            "custom_checks": {
                "greeting_service": "healthy",
                "api_endpoints": "healthy",
                "ui_components": "healthy"
            }
        })
        
        return base_health
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed extension status."""
        base_status = super().get_status()
        
        # Add extension-specific status information
        uptime = datetime.now(timezone.utc) - self.start_time
        
        base_status.update({
            "greeting_count": self.greeting_count,
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "api_endpoints": len(self.manifest.api.endpoints),
            "ui_pages": len(self.manifest.ui.control_room_pages)
        })
        
        return base_status


# Export the extension class
__all__ = ["HelloExtension"]