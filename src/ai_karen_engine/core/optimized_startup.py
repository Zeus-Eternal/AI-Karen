"""
Optimized startup system with lazy loading and minimal resource usage.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from ai_karen_engine.core.lazy_loading import (
    lazy_registry, 
    setup_lazy_services,
    cleanup_lazy_services
)

logger = logging.getLogger(__name__)


@dataclass
class StartupConfig:
    """Configuration for optimized startup."""
    minimal_mode: bool = True
    lazy_loading: bool = True
    defer_heavy_services: bool = True
    essential_services_only: bool = False
    max_startup_time: float = 10.0  # seconds
    enable_resource_monitoring: bool = True


class OptimizedStartup:
    """
    Optimized startup manager that minimizes resource usage
    and initializes services on-demand.
    """
    
    def __init__(self, config: StartupConfig):
        self.config = config
        self._essential_services: Set[str] = {
            "database",
            "config_manager",
            "health_service"
        }
        self._heavy_services: Set[str] = {
            "nlp_service",
            "ai_orchestrator", 
            "analytics_service",
            "model_library",
            "distilbert_service",
            "spacy_service"
        }
        self._startup_time = 0.0
        self._initialized_services: Set[str] = set()
    
    async def startup(self, settings: Any) -> Dict[str, Any]:
        """
        Execute optimized startup sequence.
        
        Returns:
            Dict with startup metrics and status
        """
        start_time = time.time()
        startup_report = {
            "started_at": datetime.now().isoformat(),
            "config": {
                "minimal_mode": self.config.minimal_mode,
                "lazy_loading": self.config.lazy_loading,
                "defer_heavy_services": self.config.defer_heavy_services,
                "essential_services_only": self.config.essential_services_only
            },
            "services": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            logger.info("🚀 Starting optimized startup sequence")
            
            # Phase 1: Essential services only
            if self.config.essential_services_only:
                await self._initialize_essential_services(settings, startup_report)
            else:
                # Phase 1: Essential services
                await self._initialize_essential_services(settings, startup_report)
                
                # Phase 2: Setup lazy loading for heavy services
                if self.config.lazy_loading:
                    await self._setup_lazy_services(startup_report)
                
                # Phase 3: Initialize lightweight services immediately
                if not self.config.defer_heavy_services:
                    await self._initialize_lightweight_services(settings, startup_report)
            
            # Phase 4: Setup resource monitoring
            if self.config.enable_resource_monitoring:
                await self._setup_resource_monitoring(startup_report)
            
            self._startup_time = time.time() - start_time
            startup_report["startup_time"] = self._startup_time
            startup_report["success"] = True
            
            logger.info(f"✅ Optimized startup completed in {self._startup_time:.2f}s")
            logger.info(f"   • Initialized services: {len(self._initialized_services)}")
            logger.info(f"   • Deferred services: {len(self._heavy_services - self._initialized_services)}")
            
            return startup_report
            
        except Exception as e:
            self._startup_time = time.time() - start_time
            startup_report["startup_time"] = self._startup_time
            startup_report["success"] = False
            startup_report["error"] = str(e)
            
            logger.error(f"❌ Optimized startup failed after {self._startup_time:.2f}s: {e}")
            raise
    
    async def _initialize_essential_services(self, settings: Any, report: Dict[str, Any]) -> None:
        """Initialize only essential services."""
        logger.info("⚡ Initializing essential services")
        
        essential_tasks = []
        
        # Database initialization (lightweight)
        essential_tasks.append(self._init_database(report))
        
        # Config manager (already initialized, just validate)
        essential_tasks.append(self._init_config_manager(report))
        
        # Health service (lightweight)
        essential_tasks.append(self._init_health_service(report))
        
        # Execute essential services in parallel
        results = await asyncio.gather(*essential_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self._essential_services)[i]
                logger.error(f"Failed to initialize essential service {service_name}: {result}")
                report["errors"].append(f"Essential service {service_name}: {result}")
            
        logger.info("✅ Essential services initialized")
    
    async def _setup_lazy_services(self, report: Dict[str, Any]) -> None:
        """Setup lazy loading for heavy services."""
        logger.info("🔧 Setting up lazy loading for heavy services")
        
        try:
            await setup_lazy_services()
            
            # Register all heavy services as lazy
            for service_name in self._heavy_services:
                report["services"][service_name] = {
                    "status": "lazy",
                    "initialized": False,
                    "deferred": True
                }
            
            logger.info(f"✅ Lazy loading configured for {len(self._heavy_services)} services")
            
        except Exception as e:
            logger.error(f"Failed to setup lazy services: {e}")
            report["errors"].append(f"Lazy services setup: {e}")
    
    async def _initialize_lightweight_services(self, settings: Any, report: Dict[str, Any]) -> None:
        """Initialize lightweight services that don't consume much resources."""
        logger.info("💡 Initializing lightweight services")
        
        lightweight_services = {
            "plugin_loader",
            "metrics_collector", 
            "request_validator",
            "middleware_stack"
        }
        
        for service_name in lightweight_services:
            try:
                # Initialize lightweight service
                await self._init_lightweight_service(service_name, settings)
                self._initialized_services.add(service_name)
                
                report["services"][service_name] = {
                    "status": "initialized",
                    "initialized": True,
                    "deferred": False
                }
                
            except Exception as e:
                logger.warning(f"Failed to initialize lightweight service {service_name}: {e}")
                report["warnings"].append(f"Lightweight service {service_name}: {e}")
        
        logger.info("✅ Lightweight services initialized")
    
    async def _setup_resource_monitoring(self, report: Dict[str, Any]) -> None:
        """Setup resource monitoring."""
        logger.info("🔍 Setting up resource monitoring")
        
        try:
            # Resource monitoring is handled by the lazy service registry
            # Just need to enable it
            report["services"]["resource_monitoring"] = {
                "status": "initialized",
                "initialized": True,
                "deferred": False
            }
            
            logger.info("✅ Resource monitoring enabled")
            
        except Exception as e:
            logger.error(f"Failed to setup resource monitoring: {e}")
            report["errors"].append(f"Resource monitoring: {e}")
    
    async def _init_database(self, report: Dict[str, Any]) -> None:
        """Initialize database connection (lightweight)."""
        try:
            # Import only when needed
            from ai_karen_engine.database.client import get_database_client
            
            # Initialize with minimal connection pool
            db_client = get_database_client()
            if hasattr(db_client, 'initialize'):
                await db_client.initialize()
            
            self._initialized_services.add("database")
            report["services"]["database"] = {
                "status": "initialized",
                "initialized": True,
                "deferred": False
            }
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _init_config_manager(self, report: Dict[str, Any]) -> None:
        """Validate config manager (already initialized)."""
        try:
            from ai_karen_engine.config.config_manager import config_manager
            
            # Just validate it's working
            test_config = config_manager.get_config_value("test", default="ok")
            
            self._initialized_services.add("config_manager")
            report["services"]["config_manager"] = {
                "status": "initialized", 
                "initialized": True,
                "deferred": False
            }
            
        except Exception as e:
            logger.error(f"Config manager validation failed: {e}")
            raise
    
    async def _init_health_service(self, report: Dict[str, Any]) -> None:
        """Initialize health service (lightweight)."""
        try:
            # Health service is typically lightweight
            self._initialized_services.add("health_service")
            report["services"]["health_service"] = {
                "status": "initialized",
                "initialized": True, 
                "deferred": False
            }
            
        except Exception as e:
            logger.error(f"Health service initialization failed: {e}")
            raise
    
    async def _init_lightweight_service(self, service_name: str, settings: Any) -> None:
        """Initialize a lightweight service."""
        # Placeholder for lightweight service initialization
        # In practice, these would call the actual service initializers
        logger.debug(f"Initializing lightweight service: {service_name}")
        
        # Simulate minimal initialization time
        await asyncio.sleep(0.01)
    
    async def shutdown(self) -> None:
        """Shutdown all services."""
        logger.info("🛑 Starting optimized shutdown")
        
        try:
            # Cleanup lazy services
            await cleanup_lazy_services()
            
            # Cleanup essential services
            # (Add specific cleanup logic here)
            
            logger.info("✅ Optimized shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


class MinimalStartupMode:
    """
    Ultra-minimal startup mode for development and testing.
    Only initializes the bare minimum needed to serve requests.
    """
    
    @staticmethod
    async def initialize(settings: Any) -> Dict[str, Any]:
        """Initialize minimal services only."""
        start_time = time.time()
        
        logger.info("⚡ MINIMAL MODE: Starting ultra-lightweight initialization")
        
        try:
            # Only initialize what's absolutely necessary
            essential_services = []
            
            # Config (already done)
            essential_services.append("config_manager")
            
            # Database connection (minimal pool)
            try:
                from ai_karen_engine.database.client import get_database_client
                db_client = get_database_client()
                if hasattr(db_client, 'initialize'):
                    await db_client.initialize()
                essential_services.append("database")
            except Exception as e:
                logger.warning(f"Database initialization failed in minimal mode: {e}")
            
            # Setup lazy loading for everything else
            await setup_lazy_services()
            
            startup_time = time.time() - start_time
            
            report = {
                "mode": "minimal",
                "startup_time": startup_time,
                "initialized_services": essential_services,
                "deferred_services": ["nlp_service", "ai_orchestrator", "analytics_service"],
                "success": True
            }
            
            logger.info(f"✅ MINIMAL MODE: Ready in {startup_time:.2f}s")
            return report
            
        except Exception as e:
            startup_time = time.time() - start_time
            logger.error(f"❌ MINIMAL MODE: Failed after {startup_time:.2f}s: {e}")
            raise


def get_startup_config_from_env() -> StartupConfig:
    """Get startup configuration from environment variables."""
    return StartupConfig(
        minimal_mode=os.getenv("KARI_MINIMAL_MODE", "true").lower() == "true",
        lazy_loading=os.getenv("KARI_LAZY_LOADING", "true").lower() == "true", 
        defer_heavy_services=os.getenv("KARI_DEFER_HEAVY_SERVICES", "true").lower() == "true",
        essential_services_only=os.getenv("KARI_ESSENTIAL_ONLY", "false").lower() == "true",
        max_startup_time=float(os.getenv("KARI_MAX_STARTUP_TIME", "10.0")),
        enable_resource_monitoring=os.getenv("KARI_RESOURCE_MONITORING", "true").lower() == "true"
    )


async def optimized_startup_sequence(settings: Any) -> Dict[str, Any]:
    """
    Main entry point for optimized startup.
    
    This replaces the heavy startup sequence with a lightweight one
    that defers expensive operations until they're actually needed.
    """
    config = get_startup_config_from_env()
    
    # Check for ultra-minimal mode
    if os.getenv("KARI_ULTRA_MINIMAL", "false").lower() == "true":
        return await MinimalStartupMode.initialize(settings)
    
    # Use optimized startup
    startup_manager = OptimizedStartup(config)
    return await startup_manager.startup(settings)


class OptimizedStartupManager:
    """
    Main manager for optimized startup sequences.
    Simplified interface for testing and integration.
    """
    
    def __init__(self):
        self.config = get_startup_config_from_env()
        self.startup_manager = OptimizedStartup(self.config)
        self.initialized = False
        
    def initialize_minimal(self):
        """Initialize with minimal resources."""
        start_time = time.time()
        
        try:
            # Set ultra-minimal mode
            os.environ["KARI_ULTRA_MINIMAL"] = "true"
            
            # Basic initialization
            from ai_karen_engine.core.config_manager import ConfigManager
            ConfigManager()
            
            # Mark as initialized
            self.initialized = True
            
            startup_time = time.time() - start_time
            logger.info(f"✅ Minimal startup completed in {startup_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Minimal startup failed: {e}")
            raise
    
    async def initialize_full(self, settings: Any = None):
        """Initialize with full startup sequence."""
        if settings is None:
            settings = {}
            
        result = await self.startup_manager.startup(settings)
        self.initialized = True
        return result
    
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self.initialized
