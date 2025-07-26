#!/usr/bin/env python3
"""
Database Configuration Example.

This example demonstrates how to use the database configuration validation
module to load, validate, and use database configuration in your applications.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.database.config import (
    DatabaseConfig,
    load_database_config,
    validate_database_connection,
    DatabaseConfigurationError
)
from ai_karen_engine.database.client import MultiTenantPostgresClient


def example_basic_configuration():
    """Example 1: Basic configuration creation and validation."""
    print("=" * 60)
    print("Example 1: Basic Configuration Creation and Validation")
    print("=" * 60)
    
    # Create a basic configuration
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        user="myuser",
        password="mypassword",
        database="mydatabase"
    )
    
    print(f"Configuration valid: {config.is_valid()}")
    print(f"Database URL: {config.build_database_url()}")
    print(f"Async URL: {config.build_async_database_url()}")
    
    # Show sanitized configuration (safe for logging)
    sanitized = config.get_sanitized_config()
    print(f"Sanitized config: {sanitized}")
    
    # Get validation summary
    validation = config.get_validation_summary()
    print(f"Validation summary: {validation}")


def example_environment_loading():
    """Example 2: Loading configuration from environment variables."""
    print("\n" + "=" * 60)
    print("Example 2: Loading Configuration from Environment")
    print("=" * 60)
    
    try:
        # Load configuration from .env file
        config = load_database_config(".env")
        
        print("✅ Configuration loaded successfully!")
        print(f"Host: {config.host}")
        print(f"User: {config.user}")
        print(f"Database: {config.database}")
        print(f"Valid: {config.is_valid()}")
        
        if config.is_valid():
            print(f"Database URL: {config.build_database_url()}")
        
        # Show any warnings
        if config.validation_warnings:
            print("⚠️  Warnings:")
            for warning in config.validation_warnings:
                print(f"  • {warning}")
                
    except DatabaseConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        print("Errors:")
        for error in e.errors:
            print(f"  • {error}")
        print("Warnings:")
        for warning in e.warnings:
            print(f"  • {warning}")


def example_invalid_configuration():
    """Example 3: Handling invalid configuration."""
    print("\n" + "=" * 60)
    print("Example 3: Handling Invalid Configuration")
    print("=" * 60)
    
    # Create an invalid configuration
    config = DatabaseConfig(
        host="",  # Invalid: empty host
        port=0,   # Invalid: port must be > 0
        user="",  # Invalid: empty user
        password="",  # Warning: empty password
        database="123invalid"  # Invalid: database name must start with letter
    )
    
    print(f"Configuration valid: {config.is_valid()}")
    
    validation = config.get_validation_summary()
    print(f"Errors ({validation['error_count']}):")
    for error in validation["errors"]:
        print(f"  • {error}")
    
    print(f"Warnings ({validation['warning_count']}):")
    for warning in validation["warnings"]:
        print(f"  • {warning}")


def example_connection_testing():
    """Example 4: Testing database connection."""
    print("\n" + "=" * 60)
    print("Example 4: Testing Database Connection")
    print("=" * 60)
    
    try:
        config = load_database_config(".env")
        
        if not config.is_valid():
            print("❌ Configuration is invalid, cannot test connection")
            return
        
        print(f"Testing connection to {config.host}:{config.port}/{config.database}...")
        
        result = validate_database_connection(config)
        
        if result["success"]:
            print("✅ Connection successful!")
            print(f"Connection time: {result['connection_time']:.3f}s")
            print(f"Server version: {result['server_version']}")
            print(f"Database exists: {result['database_exists']}")
        else:
            print("❌ Connection failed!")
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Error: {e}")


def example_client_integration():
    """Example 5: Using configuration with database client."""
    print("\n" + "=" * 60)
    print("Example 5: Database Client Integration")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_database_config(".env")
        
        # Create database client with validated configuration
        client = MultiTenantPostgresClient(config=config)
        
        print("✅ Database client initialized successfully!")
        print(f"Database URL: {client.database_url}")
        print(f"Pool configuration: size={client.pool_size}, overflow={client.max_overflow}")
        
        # Perform health check
        health = client.health_check()
        print(f"Health check status: {health['status']}")
        
        if health['status'] == 'healthy':
            print("✅ Database is healthy and ready!")
        else:
            print(f"⚠️  Database health issue: {health.get('error', 'Unknown error')}")
        
        # Clean up
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")


def example_custom_configuration():
    """Example 6: Creating custom configuration with SSL."""
    print("\n" + "=" * 60)
    print("Example 6: Custom Configuration with SSL")
    print("=" * 60)
    
    config = DatabaseConfig(
        host="secure-db.example.com",
        port=5432,
        user="secure_user",
        password="secure_password",
        database="secure_db",
        ssl_mode="require",
        ssl_cert="/path/to/client.crt",
        ssl_key="/path/to/client.key",
        ssl_ca="/path/to/ca.crt",
        pool_size=20,
        max_overflow=30,
        debug_sql=True
    )
    
    print(f"Configuration valid: {config.is_valid()}")
    print(f"SSL mode: {config.ssl_mode}")
    print(f"Debug SQL: {config.debug_sql}")
    
    if config.is_valid():
        url = config.build_database_url()
        print(f"Database URL with SSL: {url}")
    
    sanitized = config.get_sanitized_config()
    print(f"Sanitized config: {sanitized}")


def main():
    """Run all examples."""
    print("Database Configuration Examples")
    print("This demonstrates the database configuration validation module.")
    
    example_basic_configuration()
    example_environment_loading()
    example_invalid_configuration()
    example_connection_testing()
    example_client_integration()
    example_custom_configuration()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("  • src/ai_karen_engine/database/config.py")
    print("  • python src/ai_karen_engine/database/config_cli.py --help")


if __name__ == "__main__":
    main()