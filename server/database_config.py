# mypy: ignore-errors
"""
Database Configuration for FastAPI Server.
Handles database connection pool configuration, timeout settings, and graceful shutdown.
"""

import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from .config import Settings

logger = logging.getLogger("kari.database")


class DatabaseConfig:
    """Database configuration manager for FastAPI server"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._database_manager = None
        self._database_health_monitor = None
        self._shutdown_event = asyncio.Event()
        self._graceful_shutdown_task: Optional[asyncio.Task] = None
        
    async def initialize_database(self) -> bool:
        """Initialize database connection with enhanced configuration"""
        try:
            # Import here to avoid circular imports
            from ai_karen_engine.services.database_connection_manager import (
                initialize_database_manager
            )
            from ai_karen_engine.services.database_health_monitor import (
                initialize_database_health_monitor,
                get_database_health_monitor,
            )
            
            # Initialize database manager with enhanced configuration
            self._database_manager = await initialize_database_manager(
                database_url=self.settings.database_url,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_recycle=self.settings.db_pool_recycle,
                pool_pre_ping=self.settings.db_pool_pre_ping,
                echo=self.settings.db_echo,
            )
            
            # Initialize database health monitor
            self._database_health_monitor = await initialize_database_health_monitor(
                database_url=self.settings.database_url,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_recycle=self.settings.db_pool_recycle,
                pool_pre_ping=self.settings.db_pool_pre_ping,
                echo=self.settings.db_echo,
                health_check_interval=self.settings.db_health_check_interval,
                max_connection_failures=self.settings.db_max_connection_failures,
                connection_retry_delay=self.settings.db_connection_retry_delay,
                connection_timeout=self.settings.db_connection_timeout,
                query_timeout=self.settings.db_query_timeout,
                start_monitoring=True,
            )
            
            logger.info(
                "Database initialized with enhanced configuration",
                extra={
                    "pool_size": self.settings.db_pool_size,
                    "max_overflow": self.settings.db_max_overflow,
                    "connection_timeout": self.settings.db_connection_timeout,
                    "query_timeout": self.settings.db_query_timeout,
                    "pool_recycle": self.settings.db_pool_recycle,
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def setup_graceful_shutdown(self):
        """Setup graceful shutdown handling for database connections"""
        if not self.settings.enable_graceful_shutdown:
            logger.info("Graceful shutdown disabled")
            return
            
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self._shutdown_event.set()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start graceful shutdown task
        self._graceful_shutdown_task = asyncio.create_task(
            self._graceful_shutdown_handler()
        )
        
        logger.info("Graceful shutdown handler configured")
    
    async def _graceful_shutdown_handler(self):
        """Handle graceful shutdown process"""
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            logger.info("Starting graceful shutdown process")
            
            # Give active connections time to complete
            await asyncio.sleep(2)
            
            # Close database connections
            if self._database_manager:
                logger.info("Closing database connections")
                await self._database_manager.close()
                
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Get comprehensive database health information"""
        health_info = {
            "status": "not_initialized",
            "healthy": False,
            "error": "Database not initialized"
        }
        
        try:
            # Get health from database manager if available
            if self._database_manager:
                try:
                    manager_health = await self._database_manager._health_check()
                    health_info.update(manager_health)
                except Exception as e:
                    logger.warning(f"Database manager health check failed: {e}")
            
            # Get comprehensive health from database health monitor
            if self._database_health_monitor:
                try:
                    monitor_health = await self._database_health_monitor.check_health()
                    
                    health_info.update({
                        "status": monitor_health.status.value,
                        "healthy": monitor_health.is_connected,
                        "response_time_ms": monitor_health.response_time,
                        "error_count": monitor_health.error_count,
                        "consecutive_failures": monitor_health.consecutive_failures,
                        "last_success": monitor_health.last_success.isoformat() if monitor_health.last_success else None,
                        "last_error": monitor_health.last_error,
                        "degraded_features": monitor_health.degraded_features,
                        "recovery_attempts": monitor_health.recovery_attempts,
                        "next_recovery_attempt": monitor_health.next_recovery_attempt.isoformat() if monitor_health.next_recovery_attempt else None,
                    })
                    
                    # Add pool information if available
                    if monitor_health.metrics:
                        health_info["pool_info"] = {
                            "pool_size": monitor_health.metrics.pool_size,
                            "active_connections": monitor_health.metrics.active_connections,
                            "idle_connections": monitor_health.metrics.idle_connections,
                            "checked_out": monitor_health.metrics.checked_out,
                            "overflow": monitor_health.metrics.overflow,
                            "invalidated": monitor_health.metrics.invalidated,
                            "pool_status": monitor_health.metrics.pool_status.value,
                            "query_success_rate": monitor_health.metrics.query_success_rate,
                        }
                    
                except Exception as e:
                    logger.warning(f"Database health monitor check failed: {e}")
                    health_info["monitor_error"] = str(e)
            
            # Add configuration information
            health_info["configuration"] = {
                "pool_size": self.settings.db_pool_size,
                "max_overflow": self.settings.db_max_overflow,
                "connection_timeout": self.settings.db_connection_timeout,
                "query_timeout": self.settings.db_query_timeout,
                "pool_recycle": self.settings.db_pool_recycle,
                "pool_pre_ping": self.settings.db_pool_pre_ping,
                "health_check_interval": self.settings.db_health_check_interval,
                "max_connection_failures": self.settings.db_max_connection_failures,
                "connection_retry_delay": self.settings.db_connection_retry_delay,
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"Failed to get database health: {e}")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
                "configuration": {
                    "pool_size": self.settings.db_pool_size,
                    "max_overflow": self.settings.db_max_overflow,
                    "connection_timeout": self.settings.db_connection_timeout,
                    "query_timeout": self.settings.db_query_timeout,
                }
            }
    
    async def test_database_connection(self) -> bool:
        """Test database connection with timeout"""
        if not self._database_manager:
            return False
            
        try:
            # Test connection with timeout
            return await asyncio.wait_for(
                self._database_manager.async_health_check(),
                timeout=self.settings.db_connection_timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Database connection test timed out after {self.settings.db_connection_timeout}s")
            return False
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_database_manager(self):
        """Get the database manager instance"""
        return self._database_manager
    
    def get_database_health_monitor(self):
        """Get the database health monitor instance"""
        return self._database_health_monitor
    
    async def cleanup(self):
        """Cleanup database resources"""
        try:
            # Cancel graceful shutdown task
            if self._graceful_shutdown_task and not self._graceful_shutdown_task.done():
                self._graceful_shutdown_task.cancel()
                try:
                    await self._graceful_shutdown_task
                except asyncio.CancelledError:
                    pass
            
            # Close database manager
            if self._database_manager:
                await self._database_manager.close()
            
            # Shutdown database health monitor
            if self._database_health_monitor:
                await self._database_health_monitor.cleanup()
                
            logger.info("Database configuration cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")


# Global database configuration instance
_database_config: Optional[DatabaseConfig] = None


def get_database_config(settings: Optional[Settings] = None) -> DatabaseConfig:
    """Get global database configuration instance"""
    global _database_config
    if _database_config is None:
        if settings is None:
            settings = Settings()
        _database_config = DatabaseConfig(settings)
    return _database_config


@asynccontextmanager
async def database_lifespan(settings: Settings):
    """Database lifespan context manager for FastAPI"""
    db_config = get_database_config(settings)
    
    try:
        # Initialize database
        logger.info("Initializing database configuration")
        await db_config.initialize_database()
        
        # Setup graceful shutdown
        await db_config.setup_graceful_shutdown()
        
        logger.info("Database configuration startup completed")
        yield db_config
        
    except Exception as e:
        logger.error(f"Database configuration startup failed: {e}")
        yield None
        
    finally:
        # Cleanup
        logger.info("Database configuration shutdown starting")
        await db_config.cleanup()
        logger.info("Database configuration shutdown completed")