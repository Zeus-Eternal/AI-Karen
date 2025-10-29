"""
Test script to verify service-isolated database configuration
for fixing LLM runtime cache interference with extension services.
"""

import asyncio
import logging
from typing import Dict, Any

from .database_config import DatabaseConfig, ServiceType
from .config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_service_isolation():
    """Test service-isolated database configuration"""
    try:
        # Initialize settings
        settings = Settings()
        
        # Initialize database config
        db_config = DatabaseConfig(settings)
        
        # Initialize database with service isolation
        success = await db_config.initialize_database()
        if not success:
            logger.error("Failed to initialize database")
            return False
        
        # Test service isolation
        service_manager = db_config.get_service_isolated_manager()
        if not service_manager:
            logger.warning("Service isolation not available")
            return False
        
        # Test extension service health
        extension_health = await db_config.get_service_health(ServiceType.EXTENSION)
        logger.info(f"Extension service health: {extension_health}")
        
        # Test authentication service health
        auth_health = await db_config.get_service_health(ServiceType.AUTHENTICATION)
        logger.info(f"Authentication service health: {auth_health}")
        
        # Test comprehensive health with interference detection
        comprehensive_health = await db_config.get_extension_service_health_with_interference_detection()
        logger.info(f"Comprehensive health: {comprehensive_health}")
        
        # Test connection pool optimization
        optimization_report = db_config.optimize_connection_pools_for_extension_performance()
        logger.info(f"Pool optimization report: {optimization_report}")
        
        # Cleanup
        await db_config.cleanup()
        
        logger.info("Service isolation test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Service isolation test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_service_isolation())