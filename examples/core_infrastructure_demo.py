#!/usr/bin/env python3
"""
Demo script showing how to use the AI Karen core infrastructure.

This example demonstrates:
1. Creating services with dependency injection
2. Using the service container
3. Error handling
4. Logging
5. Creating a FastAPI gateway
"""

import asyncio
from typing import Dict, Any

from ai_karen_engine.core import (
    BaseService, ServiceConfig, ServiceStatus, ServiceContainer,
    get_container, get_logger, create_app, KarenError, ValidationError
)


class DatabaseService(BaseService):
    """Example database service."""
    
    async def initialize(self):
        """Initialize database connection."""
        self.logger.info("Initializing database connection")
        self.connection = "mock_db_connection"
    
    async def start(self):
        """Start database service."""
        self.logger.info("Starting database service")
    
    async def stop(self):
        """Stop database service."""
        self.logger.info("Stopping database service")
        self.connection = None
    
    async def health_check(self):
        """Check database health."""
        return self.connection is not None
    
    def query(self, sql: str) -> Dict[str, Any]:
        """Execute a database query."""
        if not self.connection:
            raise KarenError("Database not connected", "DATABASE_ERROR")
        
        self.logger.info(f"Executing query: {sql}")
        return {"result": "mock_data", "rows": 1}


class CacheService(BaseService):
    """Example cache service that depends on database."""
    
    async def initialize(self):
        """Initialize cache."""
        self.logger.info("Initializing cache")
        self.cache = {}
    
    async def start(self):
        """Start cache service."""
        self.logger.info("Starting cache service")
        
        # Get database service dependency
        container = get_container()
        self.db_service = container.get_service("database")
    
    async def stop(self):
        """Stop cache service."""
        self.logger.info("Stopping cache service")
        self.cache.clear()
    
    async def health_check(self):
        """Check cache health."""
        return isinstance(self.cache, dict)
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        if key in self.cache:
            self.logger.info(f"Cache hit for key: {key}")
            return self.cache[key]
        
        # Cache miss - get from database
        self.logger.info(f"Cache miss for key: {key}")
        try:
            result = self.db_service.query(f"SELECT * FROM data WHERE key = '{key}'")
            self.cache[key] = result
            return result
        except Exception as e:
            self.logger.error(f"Failed to get data for key {key}: {e}")
            raise
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self.cache[key] = value
        self.logger.info(f"Set cache key: {key}")


async def demo_services():
    """Demonstrate service container usage."""
    print("\n=== Service Container Demo ===")
    
    # Get the global service container
    container = get_container()
    
    # Register services
    db_config = ServiceConfig(
        name="database",
        dependencies=[],
        config={"host": "localhost", "port": 5432}
    )
    
    cache_config = ServiceConfig(
        name="cache",
        dependencies=["database"],  # Cache depends on database
        config={"max_size": 1000}
    )
    
    container.register_service("database", DatabaseService, db_config)
    container.register_service("cache", CacheService, cache_config)
    
    # Start all services (in dependency order)
    await container.start_all_services()
    
    # Use the services
    db_service = container.get_service("database")
    cache_service = container.get_service("cache")
    
    print(f"Database status: {db_service.status}")
    print(f"Cache status: {cache_service.status}")
    
    # Test cache functionality
    cache_service.set("user:123", {"name": "John", "email": "john@example.com"})
    user_data = cache_service.get("user:123")
    print(f"Retrieved user data: {user_data}")
    
    # Test cache miss (will query database)
    try:
        missing_data = cache_service.get("user:999")
        print(f"Missing data: {missing_data}")
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Get service health
    health_info = container.get_service_health()
    print(f"Service health: {health_info}")
    
    # Stop all services
    await container.stop_all_services()
    print("All services stopped")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===")
    
    from ai_karen_engine.core.errors import ErrorHandler, get_error_handler
    
    handler = get_error_handler()
    
    # Test with KarenError
    try:
        raise ValidationError("Invalid input", field="email", value="invalid-email")
    except Exception as e:
        response = handler.handle_exception(e)
        print(f"Validation error response: {response.dict()}")
    
    # Test with unknown error
    try:
        raise ValueError("Something went wrong")
    except Exception as e:
        response = handler.handle_exception(e)
        print(f"Unknown error response: {response.dict()}")


def demo_logging():
    """Demonstrate logging."""
    print("\n=== Logging Demo ===")
    
    from ai_karen_engine.core.logging import LogLevel
    logger = get_logger("demo", level=LogLevel.INFO)
    
    # Set context
    logger.set_context(user_id="123", session_id="abc-def")
    
    # Log messages
    logger.info("This is an info message")
    logger.warning("This is a warning message", extra_field="extra_value")
    logger.error("This is an error message")
    
    # Clear context
    logger.clear_context()
    logger.info("Message without context")


def demo_fastapi_app():
    """Demonstrate FastAPI app creation."""
    print("\n=== FastAPI App Demo ===")
    
    app = create_app(
        title="Demo AI Karen App",
        description="Demo application showing core infrastructure",
        version="1.0.0",
        debug=True
    )
    
    print(f"Created FastAPI app: {app}")
    print("App routes available:")
    
    # In a real scenario, you would run this with uvicorn:
    # uvicorn demo:app --reload
    print("To run the app: uvicorn examples.core_infrastructure_demo:app --reload")
    
    return app


async def main():
    """Main demo function."""
    print("AI Karen Core Infrastructure Demo")
    print("=" * 40)
    
    # Demo logging
    demo_logging()
    
    # Demo error handling
    demo_error_handling()
    
    # Demo services
    await demo_services()
    
    # Demo FastAPI app
    app = demo_fastapi_app()
    
    print("\nDemo completed successfully!")
    return app


# Create the FastAPI app for uvicorn
app = demo_fastapi_app()

if __name__ == "__main__":
    asyncio.run(main())