"""
Extension Monitoring System Startup Integration

This module handles the initialization and shutdown of the extension monitoring
system during FastAPI application lifecycle.

Requirements addressed:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .extension_monitoring_integration import extension_monitoring
from .extension_alerting_system import extension_alert_manager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def extension_monitoring_lifespan() -> AsyncGenerator[None, None]:
    """Lifespan context manager for extension monitoring system."""
    
    logger.info("🚀 Starting extension monitoring system...")
    
    try:
        # Initialize monitoring integration
        await extension_monitoring.initialize()
        
        # Start alert monitoring
        await extension_alert_manager.start_monitoring(check_interval=60)
        
        logger.info("✅ Extension monitoring system started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start extension monitoring system: {e}")
        raise
    
    finally:
        logger.info("🛑 Shutting down extension monitoring system...")
        
        try:
            # Shutdown monitoring integration
            await extension_monitoring.shutdown()
            
            # Stop alert monitoring
            await extension_alert_manager.stop_monitoring()
            
            logger.info("✅ Extension monitoring system shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during extension monitoring shutdown: {e}")

async def initialize_extension_monitoring():
    """Initialize extension monitoring system during startup."""
    try:
        logger.info("🔧 Initializing extension monitoring system...")
        
        # Initialize monitoring integration
        await extension_monitoring.initialize()
        
        # Start alert monitoring with 60-second check interval
        await extension_alert_manager.start_monitoring(check_interval=60)
        
        logger.info("✅ Extension monitoring system initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize extension monitoring system: {e}")
        # Don't raise - monitoring is not critical for core functionality
        # but log the error for debugging

async def shutdown_extension_monitoring():
    """Shutdown extension monitoring system during application shutdown."""
    try:
        logger.info("🛑 Shutting down extension monitoring system...")
        
        # Shutdown monitoring integration
        await extension_monitoring.shutdown()
        
        # Stop alert monitoring
        await extension_alert_manager.stop_monitoring()
        
        logger.info("✅ Extension monitoring system shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during extension monitoring shutdown: {e}")
        # Don't raise during shutdown - just log the error

def register_monitoring_startup_tasks(startup_tasks: list):
    """Register monitoring system startup tasks."""
    startup_tasks.append({
        'name': 'extension_monitoring',
        'task': initialize_extension_monitoring,
        'critical': False,  # Not critical for core functionality
        'timeout': 30
    })
    
    logger.info("📋 Extension monitoring startup task registered")

def register_monitoring_shutdown_tasks(shutdown_tasks: list):
    """Register monitoring system shutdown tasks."""
    shutdown_tasks.append({
        'name': 'extension_monitoring',
        'task': shutdown_extension_monitoring,
        'timeout': 10
    })
    
    logger.info("📋 Extension monitoring shutdown task registered")