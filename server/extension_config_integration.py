"""
Integration module for extension environment configuration system.
Provides startup, shutdown, and integration with the main application.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .extension_environment_config import (
    get_config_manager,
    initialize_extension_config,
    shutdown_extension_config,
    get_current_extension_config
)
from .extension_config_hot_reload import (
    initialize_hot_reload,
    shutdown_hot_reload,
    get_hot_reloader
)
from .extension_config_api import extension_config_router

logger = logging.getLogger(__name__)


class ExtensionConfigIntegration:
    """Manages integration of extension configuration system with the main application."""
    
    def __init__(self):
        self.initialized = False
        self.startup_tasks = []
        self.shutdown_tasks = []
        self.health_check_task: Optional[asyncio.Task] = None
        self.credential_rotation_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the extension configuration system."""
        if self.initialized:
            logger.warning("Extension configuration system already initialized")
            return
        
        try:
            logger.info("Initializing extension configuration system...")
            
            # Initialize configuration manager
            await initialize_extension_config()
            
            # Initialize hot-reload system
            await initialize_hot_reload()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Register shutdown handlers
            self._register_shutdown_handlers()
            
            self.initialized = True
            logger.info("Extension configuration system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize extension configuration system: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the extension configuration system."""
        if not self.initialized:
            return
        
        try:
            logger.info("Shutting down extension configuration system...")
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Shutdown hot-reload system
            shutdown_hot_reload()
            
            # Shutdown configuration system
            shutdown_extension_config()
            
            self.initialized = False
            logger.info("Extension configuration system shutdown completed")
            
        except Exception as e:
            logger.error(f"Failed to shutdown extension configuration system: {e}")
    
    async def _start_background_tasks(self):
        """Start background tasks for configuration management."""
        try:
            # Start periodic health checks
            self.health_check_task = asyncio.create_task(
                self._periodic_health_check()
            )
            
            # Start credential rotation monitoring
            self.credential_rotation_task = asyncio.create_task(
                self._monitor_credential_rotation()
            )
            
            logger.info("Started extension configuration background tasks")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
            raise
    
    async def _stop_background_tasks(self):
        """Stop background tasks."""
        try:
            tasks_to_cancel = [
                self.health_check_task,
                self.credential_rotation_task
            ]
            
            for task in tasks_to_cancel:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("Stopped extension configuration background tasks")
            
        except Exception as e:
            logger.error(f"Failed to stop background tasks: {e}")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks on the configuration system."""
        try:
            while True:
                try:
                    config = get_current_extension_config()
                    if config.health_check_enabled:
                        config_manager = get_config_manager()
                        health_status = config_manager.get_health_status()
                        
                        if health_status.get('status') != 'healthy':
                            logger.warning(f"Configuration system health check failed: {health_status}")
                        
                        # Check for expired credentials
                        expired_credentials = health_status.get('expired_credentials', [])
                        if expired_credentials:
                            logger.error(f"Expired credentials detected: {expired_credentials}")
                    
                    # Wait for next check
                    await asyncio.sleep(config.health_check_interval_seconds)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
                    
        except asyncio.CancelledError:
            logger.info("Periodic health check task cancelled")
        except Exception as e:
            logger.error(f"Periodic health check task failed: {e}")
    
    async def _monitor_credential_rotation(self):
        """Monitor and handle credential rotation."""
        try:
            while True:
                try:
                    config_manager = get_config_manager()
                    credentials_list = config_manager.credentials_manager.list_credentials()
                    
                    # Check for credentials that need rotation
                    for cred in credentials_list:
                        if cred.get('expired'):
                            logger.warning(f"Credential '{cred['name']}' has expired")
                            
                            # Attempt automatic rotation if configured
                            if cred.get('rotation_interval_days'):
                                try:
                                    success = config_manager.credentials_manager.rotate_credential(cred['name'])
                                    if success:
                                        logger.info(f"Automatically rotated expired credential '{cred['name']}'")
                                    else:
                                        logger.error(f"Failed to rotate expired credential '{cred['name']}'")
                                except Exception as e:
                                    logger.error(f"Error rotating credential '{cred['name']}': {e}")
                    
                    # Wait 1 hour before next check
                    await asyncio.sleep(3600)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Credential rotation monitoring error: {e}")
                    await asyncio.sleep(3600)  # Wait 1 hour before retrying
                    
        except asyncio.CancelledError:
            logger.info("Credential rotation monitoring task cancelled")
        except Exception as e:
            logger.error(f"Credential rotation monitoring task failed: {e}")
    
    def _register_shutdown_handlers(self):
        """Register shutdown handlers for graceful cleanup."""
        import signal
        import atexit
        
        def shutdown_handler(signum=None, frame=None):
            """Handle shutdown signals."""
            logger.info(f"Received shutdown signal: {signum}")
            try:
                # Run shutdown in event loop if available
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.shutdown())
                else:
                    asyncio.run(self.shutdown())
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        # Register exit handler
        atexit.register(lambda: asyncio.run(self.shutdown()) if not self.initialized else None)
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        try:
            return {
                'initialized': self.initialized,
                'health_check_task_running': self.health_check_task and not self.health_check_task.done(),
                'credential_rotation_task_running': self.credential_rotation_task and not self.credential_rotation_task.done(),
                'background_tasks_count': len([t for t in [self.health_check_task, self.credential_rotation_task] if t and not t.done()]),
                'startup_tasks_count': len(self.startup_tasks),
                'shutdown_tasks_count': len(self.shutdown_tasks)
            }
        except Exception as e:
            logger.error(f"Failed to get integration status: {e}")
            return {'error': str(e)}


# Global integration instance
integration: Optional[ExtensionConfigIntegration] = None


def get_integration() -> ExtensionConfigIntegration:
    """Get the global integration instance."""
    global integration
    if integration is None:
        integration = ExtensionConfigIntegration()
    return integration


async def initialize_extension_config_integration():
    """Initialize the extension configuration integration."""
    try:
        integration_instance = get_integration()
        await integration_instance.initialize()
        logger.info("Extension configuration integration initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extension configuration integration: {e}")
        raise


async def shutdown_extension_config_integration():
    """Shutdown the extension configuration integration."""
    try:
        global integration
        if integration:
            await integration.shutdown()
            integration = None
        logger.info("Extension configuration integration shutdown")
    except Exception as e:
        logger.error(f"Failed to shutdown extension configuration integration: {e}")


def setup_extension_config_routes(app: FastAPI):
    """Setup extension configuration routes in FastAPI app."""
    try:
        app.include_router(extension_config_router)
        logger.info("Extension configuration routes registered")
    except Exception as e:
        logger.error(f"Failed to setup extension configuration routes: {e}")
        raise


@asynccontextmanager
async def extension_config_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for extension configuration."""
    try:
        # Startup
        await initialize_extension_config_integration()
        yield
    finally:
        # Shutdown
        await shutdown_extension_config_integration()


def create_extension_config_middleware():
    """Create middleware for extension configuration."""
    
    async def extension_config_middleware(request, call_next):
        """Middleware to inject configuration context."""
        try:
            # Add configuration to request state
            request.state.extension_config = get_current_extension_config()
            
            # Process request
            response = await call_next(request)
            
            # Add configuration headers if needed
            if hasattr(request.state, 'extension_config'):
                config = request.state.extension_config
                response.headers["X-Extension-Auth-Mode"] = config.auth_mode
                response.headers["X-Extension-Environment"] = config.environment.value
            
            return response
            
        except Exception as e:
            logger.error(f"Extension configuration middleware error: {e}")
            # Continue processing even if configuration fails
            return await call_next(request)
    
    return extension_config_middleware


def get_extension_config_for_request(request) -> Optional[Dict[str, Any]]:
    """Get extension configuration from request state."""
    try:
        if hasattr(request.state, 'extension_config'):
            config = request.state.extension_config
            return {
                'environment': config.environment.value,
                'auth_mode': config.auth_mode,
                'auth_enabled': config.auth_enabled,
                'require_https': config.require_https,
                'rate_limit_per_minute': config.rate_limit_per_minute,
                'enable_rate_limiting': config.enable_rate_limiting,
                'dev_bypass_enabled': config.dev_bypass_enabled
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get extension config from request: {e}")
        return None


# Configuration validation decorator
def validate_config_on_startup(func):
    """Decorator to validate configuration on startup."""
    async def wrapper(*args, **kwargs):
        try:
            # Validate configuration before starting
            from .extension_config_validator import validate_extension_config
            validation_result = await validate_extension_config()
            
            if not validation_result.get('valid', False):
                critical_issues = validation_result.get('critical_issues', 0)
                error_issues = validation_result.get('error_issues', 0)
                
                if critical_issues > 0:
                    raise RuntimeError(f"Configuration has {critical_issues} critical issues that prevent startup")
                elif error_issues > 0:
                    logger.warning(f"Configuration has {error_issues} error issues, but continuing startup")
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Configuration validation failed during startup: {e}")
            raise
    
    return wrapper


# Environment detection utilities
def detect_runtime_environment() -> str:
    """Detect the runtime environment from various sources."""
    # Check environment variables in order of preference
    env_vars = [
        "EXTENSION_ENVIRONMENT",
        "ENVIRONMENT", 
        "KARI_ENV",
        "ENV",
        "NODE_ENV",
        "FLASK_ENV",
        "DJANGO_SETTINGS_MODULE"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Normalize common values
            value = value.lower()
            if value in ["dev", "develop"]:
                return "development"
            elif value in ["prod", "production"]:
                return "production"
            elif value in ["stage", "staging"]:
                return "staging"
            elif value in ["test", "testing"]:
                return "test"
            else:
                return value
    
    # Default to development
    return "development"


def is_production_environment() -> bool:
    """Check if running in production environment."""
    env = detect_runtime_environment()
    return env in ["production", "prod"]


def is_development_environment() -> bool:
    """Check if running in development environment."""
    env = detect_runtime_environment()
    return env in ["development", "dev", "local"]


def get_environment_specific_config() -> Dict[str, Any]:
    """Get environment-specific configuration overrides."""
    env = detect_runtime_environment()
    
    # Base configuration
    config = {
        'environment': env,
        'debug': is_development_environment(),
        'testing': env in ["test", "testing"]
    }
    
    # Environment-specific overrides
    if is_production_environment():
        config.update({
            'auth_mode': 'strict',
            'require_https': True,
            'dev_bypass_enabled': False,
            'log_sensitive_data': False,
            'enable_debug_logging': False,
            'rate_limit_per_minute': 100,
            'max_failed_attempts': 3,
            'lockout_duration_minutes': 30
        })
    elif env == "staging":
        config.update({
            'auth_mode': 'hybrid',
            'require_https': True,
            'dev_bypass_enabled': False,
            'log_sensitive_data': False,
            'enable_debug_logging': True,
            'rate_limit_per_minute': 200,
            'max_failed_attempts': 5,
            'lockout_duration_minutes': 10
        })
    elif is_development_environment():
        config.update({
            'auth_mode': 'development',
            'require_https': False,
            'dev_bypass_enabled': True,
            'log_sensitive_data': True,
            'enable_debug_logging': True,
            'rate_limit_per_minute': 1000,
            'max_failed_attempts': 10,
            'lockout_duration_minutes': 1
        })
    elif env in ["test", "testing"]:
        config.update({
            'auth_mode': 'development',
            'require_https': False,
            'dev_bypass_enabled': True,
            'log_sensitive_data': True,
            'enable_debug_logging': True,
            'rate_limit_per_minute': 10000,
            'max_failed_attempts': 100,
            'lockout_duration_minutes': 0
        })
    
    return config