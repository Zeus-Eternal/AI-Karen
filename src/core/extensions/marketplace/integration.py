"""
Extension Marketplace Integration

This module provides integration utilities to wire the marketplace
into the main Kari application.
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from sqlalchemy.orm import Session

from .database import MarketplaceDatabaseManager, init_marketplace_database
from .service import ExtensionMarketplaceService
from .routes import router as marketplace_router
from .version_manager import VersionManager
from ..manager import ExtensionManager
from ..registry import ExtensionRegistry

logger = logging.getLogger(__name__)


class MarketplaceIntegration:
    """Handles integration of the marketplace into the main application."""
    
    def __init__(
        self,
        database_url: str,
        extensions_path: Path,
        extension_manager: Optional[ExtensionManager] = None,
        extension_registry: Optional[ExtensionRegistry] = None
    ):
        self.database_url = database_url
        self.extensions_path = extensions_path
        self.db_manager: Optional[MarketplaceDatabaseManager] = None
        self.marketplace_service: Optional[ExtensionMarketplaceService] = None
        self.version_manager: Optional[VersionManager] = None
        self.extension_manager = extension_manager
        self.extension_registry = extension_registry
    
    def initialize(self) -> bool:
        """Initialize the marketplace integration."""
        try:
            # Initialize database
            self.db_manager = init_marketplace_database(self.database_url)
            if not self.db_manager:
                logger.error("Failed to initialize marketplace database")
                return False
            
            # Create extension manager if not provided
            if not self.extension_manager:
                self.extension_manager = ExtensionManager(self.extensions_path, None)
            
            # Create extension registry if not provided
            if not self.extension_registry:
                self.extension_registry = ExtensionRegistry()
            
            # Create version manager
            with self.db_manager.get_session() as session:
                self.version_manager = VersionManager(session)
            
            # Create marketplace service
            with self.db_manager.get_session() as session:
                self.marketplace_service = ExtensionMarketplaceService(
                    session, self.extension_manager, self.extension_registry
                )
            
            logger.info("Marketplace integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize marketplace integration: {e}")
            return False
    
    def register_routes(self, app: FastAPI) -> None:
        """Register marketplace routes with the FastAPI app."""
        if not self.marketplace_service:
            logger.error("Marketplace service not initialized")
            return
        
        # Include the marketplace router
        app.include_router(marketplace_router)
        logger.info("Marketplace routes registered")
    
    def get_marketplace_service(self) -> Optional[ExtensionMarketplaceService]:
        """Get the marketplace service instance."""
        return self.marketplace_service
    
    def get_version_manager(self) -> Optional[VersionManager]:
        """Get the version manager instance."""
        return self.version_manager
    
    def get_database_session(self) -> Optional[Session]:
        """Get a database session."""
        if not self.db_manager:
            return None
        return self.db_manager.get_session()
    
    def health_check(self) -> dict:
        """Perform health check on marketplace components."""
        health = {
            "database": False,
            "marketplace_service": False,
            "version_manager": False,
            "extension_manager": False,
            "extension_registry": False
        }
        
        try:
            # Check database
            if self.db_manager and self.db_manager.health_check():
                health["database"] = True
            
            # Check marketplace service
            if self.marketplace_service:
                health["marketplace_service"] = True
            
            # Check version manager
            if self.version_manager:
                health["version_manager"] = True
            
            # Check extension manager
            if self.extension_manager:
                health["extension_manager"] = True
            
            # Check extension registry
            if self.extension_registry:
                health["extension_registry"] = True
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        return health
    
    def get_statistics(self) -> dict:
        """Get marketplace statistics."""
        stats = {
            "total_extensions": 0,
            "total_versions": 0,
            "total_installations": 0,
            "categories": []
        }
        
        try:
            if self.db_manager:
                counts = self.db_manager.get_table_counts()
                stats.update(counts)
                
                # Get categories (this would need to be implemented)
                # stats["categories"] = self.get_categories()
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown the marketplace integration."""
        try:
            # Close database connections
            if self.db_manager:
                # Database connections are closed automatically
                pass
            
            logger.info("Marketplace integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during marketplace shutdown: {e}")


def create_marketplace_integration(
    database_url: str = "sqlite:///marketplace.db",
    extensions_path: str = "extensions"
) -> MarketplaceIntegration:
    """Create and initialize a marketplace integration."""
    integration = MarketplaceIntegration(
        database_url=database_url,
        extensions_path=Path(extensions_path)
    )
    
    if integration.initialize():
        return integration
    else:
        raise RuntimeError("Failed to initialize marketplace integration")


def setup_marketplace_for_fastapi(
    app: FastAPI,
    database_url: str = "sqlite:///marketplace.db",
    extensions_path: str = "extensions"
) -> MarketplaceIntegration:
    """Setup marketplace integration for a FastAPI application."""
    integration = create_marketplace_integration(database_url, extensions_path)
    integration.register_routes(app)
    
    # Add health check endpoint
    @app.get("/api/extensions/marketplace/health")
    async def marketplace_health():
        return integration.health_check()
    
    # Add statistics endpoint
    @app.get("/api/extensions/marketplace/stats")
    async def marketplace_stats():
        return integration.get_statistics()
    
    return integration


# Example usage for standalone testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    # Create FastAPI app
    app = FastAPI(title="Extension Marketplace API")
    
    # Setup marketplace
    try:
        integration = setup_marketplace_for_fastapi(app)
        print("✅ Marketplace integration setup complete")
        
        # Run the server
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        print(f"❌ Failed to setup marketplace: {e}")
        exit(1)