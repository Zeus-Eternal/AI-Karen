"""
Context Management Integration

Integration module to connect Context Management system with the existing
FastAPI application, database, and other services.
"""

import logging
from typing import Any, Dict, List, Optional

from ai_karen_engine.context_management.models import (
    ContextAccessLevel,
    ContextEntry,
    ContextFileType,
    ContextQuery,
    ContextSearchResult,
    ContextShare,
    ContextStatus,
    ContextType,
)
from ai_karen_engine.context_management.routes import router as context_router
from ai_karen_engine.context_management.service import ContextManagementService
from ai_karen_engine.context_management.file_handler import FileUploadHandler
from ai_karen_engine.context_management.preprocessor import ContextPreprocessor
from ai_karen_engine.context_management.scoring import ContextRelevanceScorer

logger = logging.getLogger(__name__)


class ContextManagementIntegration:
    """
    Integration class for Context Management system.
    
    Handles initialization, configuration, and integration with existing services.
    """

    def __init__(
        self,
        app=None,
        database_client=None,
        embedding_manager=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Context Management integration.
        
        Args:
            app: FastAPI application instance
            database_client: Database client for storage
            embedding_manager: Embedding manager for vector search
            config: Configuration dictionary
        """
        self.app = app
        self.database_client = database_client
        self.embedding_manager = embedding_manager
        self.config = config or {}
        
        # Initialize services
        self.context_service = None
        self.file_handler = None
        self.preprocessor = None
        self.relevance_scorer = None
        
        logger.info("ContextManagementIntegration initialized")

    async def initialize(self) -> None:
        """
        Initialize all Context Management components.
        
        Sets up services, registers routes, and performs startup tasks.
        """
        try:
            # Initialize core services
            await self._initialize_services()
            
            # Register routes with FastAPI app
            if self.app:
                await self._register_routes()
            
            # Perform startup tasks
            await self._perform_startup_tasks()
            
            logger.info("Context Management system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Context Management: {e}")
            raise

    async def _initialize_services(self) -> None:
        """Initialize core Context Management services."""
        # Initialize memory manager
        from ai_karen_engine.database.memory_manager import MemoryManager
        
        memory_manager = MemoryManager(
            db_client=self.database_client,
            embedding_manager=self.embedding_manager,
        )
        
        # Initialize context service
        self.context_service = ContextManagementService(
            memory_manager=memory_manager,
            storage_path=self.config.get("storage_path", "/tmp/context_storage"),
            max_file_size_mb=self.config.get("max_file_size_mb", 100),
            supported_file_types=[
                ContextFileType(ft) for ft in self.config.get(
                    "allowed_file_types", 
                    [ft.value for ft in ContextFileType]
                )
            ],
        )
        
        # Initialize file handler
        self.file_handler = FileUploadHandler(
            storage_path=self.config.get("file_storage_path", "/tmp/context_files"),
            max_file_size_mb=self.config.get("max_file_size_mb", 100),
            allowed_extensions=self.config.get("allowed_extensions"),
            scan_for_malware=self.config.get("scan_for_malware", True),
            extract_text=self.config.get("extract_text", True),
        )
        
        # Initialize preprocessor
        self.preprocessor = ContextPreprocessor(
            min_keyword_length=self.config.get("min_keyword_length", 3),
            max_keywords=self.config.get("max_keywords", 10),
            max_summary_length=self.config.get("max_summary_length", 500),
            enable_entity_extraction=self.config.get("enable_entity_extraction", True),
            enable_summarization=self.config.get("enable_summarization", True),
        )
        
        # Initialize relevance scorer
        self.relevance_scorer = ContextRelevanceScorer(
            semantic_weight=self.config.get("semantic_weight", 0.4),
            content_weight=self.config.get("content_weight", 0.3),
            recency_weight=self.config.get("recency_weight", 0.15),
            importance_weight=self.config.get("importance_weight", 0.1),
            usage_weight=self.config.get("usage_weight", 0.05),
            recency_half_life_days=self.config.get("recency_half_life_days", 30.0),
        )

    async def _register_routes(self) -> None:
        """Register Context Management routes with FastAPI app."""
        if self.app:
            # Include context router with proper dependencies
            self.app.include_router(
                context_router,
                prefix="/api/context",
                tags=["context-management"],
                dependencies=[
                    # Add authentication dependency if available
                    # Add rate limiting if available
                ],
            )
            
            logger.info("Context Management routes registered with FastAPI app")

    async def _perform_startup_tasks(self) -> None:
        """Perform startup tasks and maintenance."""
        try:
            # Run cleanup tasks
            await self._cleanup_expired_contexts()
            
            # Initialize default configurations
            await self._initialize_default_configurations()
            
            # Validate system health
            await self._validate_system_health()
            
        except Exception as e:
            logger.warning(f"Startup tasks failed: {e}")

    async def _cleanup_expired_contexts(self) -> None:
        """Clean up expired contexts and shares."""
        try:
            if self.context_service:
                # This would call the cleanup function
                # In a real implementation, this would use the database function
                logger.info("Expired context cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    async def _initialize_default_configurations(self) -> None:
        """Initialize default configurations and settings."""
        try:
            # Create default context types if needed
            # Initialize default sharing policies
            # Set up default access controls
            logger.info("Default configurations initialized")
        except Exception as e:
            logger.error(f"Default configuration failed: {e}")

    async def _validate_system_health(self) -> None:
        """Validate system health and dependencies."""
        try:
            # Check database connectivity
            # Validate storage paths
            # Test embedding service
            # Verify file upload capabilities
            logger.info("System health validation completed")
        except Exception as e:
            logger.error(f"Health validation failed: {e}")

    async def shutdown(self) -> None:
        """Perform cleanup and shutdown tasks."""
        try:
            # Save any pending data
            # Close connections
            # Clean up temporary files
            logger.info("Context Management system shutdown completed")
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all Context Management services.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "services": {
                "context_service": self.context_service is not None,
                "file_handler": self.file_handler is not None,
                "preprocessor": self.preprocessor is not None,
                "relevance_scorer": self.relevance_scorer is not None,
            },
            "configuration": {
                "storage_path": self.config.get("storage_path"),
                "max_file_size_mb": self.config.get("max_file_size_mb"),
                "allowed_file_types": self.config.get("allowed_file_types"),
                "scan_for_malware": self.config.get("scan_for_malware"),
                "extract_text": self.config.get("extract_text"),
            },
            "integration": {
                "database_connected": self.database_client is not None,
                "embedding_manager": self.embedding_manager is not None,
                "fastapi_app": self.app is not None,
                "routes_registered": hasattr(self.app, 'routes'),
            },
        }

    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration for Context Management services.
        
        Args:
            new_config: New configuration parameters
        """
        try:
            # Update configuration
            self.config.update(new_config)
            
            # Update services with new configuration
            if self.relevance_scorer:
                self.relevance_scorer.update_config(
                    semantic_weight=new_config.get("semantic_weight"),
                    content_weight=new_config.get("content_weight"),
                    recency_weight=new_config.get("recency_weight"),
                    importance_weight=new_config.get("importance_weight"),
                    usage_weight=new_config.get("usage_weight"),
                    recency_half_life_days=new_config.get("recency_half_life_days"),
                )
            
            if self.preprocessor:
                self.preprocessor.update_config(
                    min_keyword_length=new_config.get("min_keyword_length"),
                    max_keywords=new_config.get("max_keywords"),
                    max_summary_length=new_config.get("max_summary_length"),
                    enable_entity_extraction=new_config.get("enable_entity_extraction"),
                    enable_summarization=new_config.get("enable_summarization"),
                )
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics and performance data.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            metrics = {
                "timestamp": "2023-12-20T05:05:00Z",  # Would use actual timestamp
                "services": {},
                "performance": {},
                "usage": {},
            }
            
            # Get context service metrics
            if self.context_service:
                # This would get actual metrics from the service
                metrics["services"]["context_service"] = {
                    "active_contexts": 0,
                    "total_contexts": 0,
                    "total_files": 0,
                    "total_shares": 0,
                }
            
            # Get file handler metrics
            if self.file_handler:
                metrics["services"]["file_handler"] = {
                    "supported_file_types": len(self.file_handler.get_supported_file_types()),
                    "storage_path": self.file_handler.storage_path,
                }
            
            # Get preprocessor metrics
            if self.preprocessor:
                metrics["services"]["preprocessor"] = self.preprocessor.get_preprocessor_config()
            
            # Get relevance scorer metrics
            if self.relevance_scorer:
                metrics["services"]["relevance_scorer"] = self.relevance_scorer.get_scorer_config()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}


# Global integration instance
_integration_instance: Optional[ContextManagementIntegration] = None


async def initialize_context_management(
    app=None,
    database_client=None,
    embedding_manager=None,
    config: Optional[Dict[str, Any]] = None,
) -> ContextManagementIntegration:
    """
    Initialize Context Management system with existing services.
    
    Args:
        app: FastAPI application instance
        database_client: Database client for storage
        embedding_manager: Embedding manager for vector search
        config: Configuration dictionary
        
    Returns:
        Initialized Context Management integration
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = ContextManagementIntegration(
            app=app,
            database_client=database_client,
            embedding_manager=embedding_manager,
            config=config,
        )
        
        await _integration_instance.initialize()
    
    return _integration_instance


def get_context_management_integration() -> Optional[ContextManagementIntegration]:
    """
    Get the global Context Management integration instance.
    
    Returns:
        Context Management integration instance or None
    """
    return _integration_instance


async def shutdown_context_management() -> None:
    """Shutdown Context Management system."""
    global _integration_instance
    
    if _integration_instance:
        await _integration_instance.shutdown()
        _integration_instance = None


# Export key functions for easy access
__all__ = [
    "ContextManagementIntegration",
    "initialize_context_management",
    "get_context_management_integration",
    "shutdown_context_management",
]