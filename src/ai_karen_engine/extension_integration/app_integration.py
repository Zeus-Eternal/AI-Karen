"""Extension System Application Integration - FastAPI application integration for extension system.

This module provides integration with the existing FastAPI application structure:
- Extension system initialization
- API route registration
- Database session management
- Configuration integration
- Middleware setup
- Event handling
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ai_karen_engine.extension_integration import (
    ExtensionIntegrationManager, set_integration_manager, get_integration_manager,
    extension_api_router
)


class ExtensionSystemIntegration:
    """
    Integration class for connecting extension system with FastAPI application.
    
    This class handles the integration of the extension system with the
    existing FastAPI application structure.
    """
    
    def __init__(
        self,
        app: FastAPI,
        config: Optional[Dict[str, Any]] = None,
        db_session_factory=None
    ):
        """
        Initialize extension system integration.
        
        Args:
            app: FastAPI application instance
            config: Extension system configuration
            db_session_factory: Database session factory
        """
        self.app = app
        self.config = config or {}
        self.db_session_factory = db_session_factory
        
        self.logger = logging.getLogger("extension.app_integration")
        
        # Initialize extension integration manager
        self.integration_manager = ExtensionIntegrationManager(
            config=self.config,
            db_session_factory=self.db_session_factory
        )
        
        # Set as global instance
        set_integration_manager(self.integration_manager)
        
        self.logger.info("Extension system integration initialized")
    
    async def setup(self) -> bool:
        """
        Set up extension system integration with FastAPI application.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Setting up extension system integration")
            
            # Initialize extension system
            if not await self.integration_manager.initialize():
                self.logger.error("Failed to initialize extension system")
                return False
            
            # Register API routes
            self._register_api_routes()
            
            # Set up middleware
            self._setup_middleware()
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Start extension system
            if not await self.integration_manager.start():
                self.logger.error("Failed to start extension system")
                return False
            
            self.logger.info("Extension system integration set up successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set up extension system integration: {e}")
            return False
    
    def _register_api_routes(self) -> None:
        """Register extension API routes with FastAPI application."""
        try:
            # Register extension API router
            self.app.include_router(
                extension_api_router,
                prefix="/api/v1",
                tags=["extensions"]
            )
            
            self.logger.info("Extension API routes registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register extension API routes: {e}")
    
    def _setup_middleware(self) -> None:
        """Set up middleware for extension system."""
        try:
            # Add CORS middleware if needed
            if self.config.get("enable_cors", True):
                self.app.add_middleware(
                    CORSMiddleware,
                    allow_origins=self.config.get("cors_origins", ["*"]),
                    allow_credentials=self.config.get("cors_credentials", True),
                    allow_methods=self.config.get("cors_methods", ["*"]),
                    allow_headers=self.config.get("cors_headers", ["*"]),
                )
            
            # Add extension context middleware
            @self.app.middleware("http")
            async def extension_context_middleware(request: Request, call_next):
                # Add extension context to request state
                request.state.extension_manager = self.integration_manager
                
                # Process request
                response = await call_next(request)
                
                return response
            
            self.logger.info("Extension system middleware set up")
            
        except Exception as e:
            self.logger.error(f"Failed to set up extension system middleware: {e}")
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for FastAPI application lifecycle."""
        try:
            # Set up startup event handler
            @self.app.on_event("startup")
            async def startup_event():
                self.logger.info("FastAPI application startup - extension system ready")
            
            # Set up shutdown event handler
            @self.app.on_event("shutdown")
            async def shutdown_event():
                self.logger.info("FastAPI application shutdown - stopping extension system")
                await self.integration_manager.stop()
            
            self.logger.info("Extension system event handlers set up")
            
        except Exception as e:
            self.logger.error(f"Failed to set up extension system event handlers: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown extension system integration."""
        try:
            if self.integration_manager:
                await self.integration_manager.stop()
            
            self.logger.info("Extension system integration shut down")
            
        except Exception as e:
            self.logger.error(f"Failed to shut down extension system integration: {e}")


def setup_extension_system(
    app: FastAPI,
    config: Optional[Dict[str, Any]] = None,
    db_session_factory=None
) -> ExtensionSystemIntegration:
    """
    Set up extension system with FastAPI application.
    
    Args:
        app: FastAPI application instance
        config: Extension system configuration
        db_session_factory: Database session factory
        
    Returns:
        Extension system integration instance
    """
    integration = ExtensionSystemIntegration(app, config, db_session_factory)
    return integration


@asynccontextmanager
async def get_extension_db_session(db_session_factory):
    """
    Get database session for extension operations.
    
    Args:
        db_session_factory: Database session factory
        
    Yields:
        Database session
    """
    if db_session_factory:
        session = db_session_factory()
        try:
            yield session
        finally:
            session.close()
    else:
        yield None


def get_extension_manager_from_request(request: Request) -> Optional[ExtensionIntegrationManager]:
    """
    Get extension manager from FastAPI request.
    
    Args:
        request: FastAPI request
        
    Returns:
        Extension integration manager or None
    """
    return getattr(request.state, "extension_manager", None)


# Dependency injection functions for FastAPI
def get_extension_manager(request: Request) -> Optional[ExtensionIntegrationManager]:
    """FastAPI dependency to get extension manager."""
    return get_extension_manager_from_request(request)


def get_extension_lifecycle_manager(request: Request):
    """FastAPI dependency to get extension lifecycle manager."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.lifecycle_manager
    return None


def get_extension_discovery_service(request: Request):
    """FastAPI dependency to get extension discovery service."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.discovery_service
    return None


def get_extension_sandbox_manager(request: Request):
    """FastAPI dependency to get extension sandbox manager."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.sandbox_manager
    return None


def get_extension_communication_manager(request: Request):
    """FastAPI dependency to get extension communication manager."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.communication_manager
    return None


def get_extension_version_manager(request: Request):
    """FastAPI dependency to get extension version manager."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.version_manager
    return None


def get_extension_permissions_manager(request: Request):
    """FastAPI dependency to get extension permissions manager."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.permissions_manager
    return None


def get_extension_metrics_collector(request: Request):
    """FastAPI dependency to get extension metrics collector."""
    extension_manager = get_extension_manager_from_request(request)
    if extension_manager:
        return extension_manager.metrics_collector
    return None


def get_extension_db_session_from_request(request: Request):
    """FastAPI dependency to get extension database session."""
    # This would typically get the session from the request state
    # or create a new one using the session factory
    return getattr(request.state, "db_session", None)


# Utility functions
def get_extension_system_status() -> Dict[str, Any]:
    """
    Get extension system status.
    
    Returns:
        Status dictionary
    """
    integration_manager = get_integration_manager()
    if integration_manager:
        return integration_manager.get_status()
    return {"error": "Extension system not initialized"}


async def restart_extension_system() -> bool:
    """
    Restart extension system.
    
    Returns:
        True if successful, False otherwise
    """
    integration_manager = get_integration_manager()
    if integration_manager:
        return await integration_manager.restart()
    return False


__all__ = [
    "ExtensionSystemIntegration",
    "setup_extension_system",
    "get_extension_db_session",
    "get_extension_manager_from_request",
    "get_extension_manager",
    "get_extension_lifecycle_manager",
    "get_extension_discovery_service",
    "get_extension_sandbox_manager",
    "get_extension_communication_manager",
    "get_extension_version_manager",
    "get_extension_permissions_manager",
    "get_extension_metrics_collector",
    "get_extension_db_session_from_request",
    "get_extension_system_status",
    "restart_extension_system",
]