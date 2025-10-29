"""
Example usage of the extension environment configuration system.
Demonstrates how to integrate and use the configuration management features.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import os
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_configuration_system():
    """Demonstrate the extension configuration system functionality."""
    
    logger.info("🚀 Extension Configuration System Demo")
    logger.info("=" * 50)
    
    try:
        # Import configuration modules
        from .extension_environment_config import (
            ExtensionEnvironmentConfigManager,
            Environment,
            get_config_manager,
            initialize_extension_config
        )
        from .extension_config_validator import (
            validate_extension_config,
            run_extension_health_checks
        )
        from .extension_config_hot_reload import (
            initialize_hot_reload,
            reload_extension_config
        )
        from .extension_config_integration import (
            initialize_extension_config_integration,
            detect_runtime_environment,
            get_environment_specific_config
        )
        
        # 1. Environment Detection
        logger.info("\n1. 🔍 Environment Detection")
        current_env = detect_runtime_environment()
        logger.info(f"   Detected environment: {current_env}")
        
        env_config = get_environment_specific_config()
        logger.info(f"   Environment-specific settings: {len(env_config)} settings")
        logger.info(f"   Auth mode: {env_config.get('auth_mode', 'unknown')}")
        logger.info(f"   Debug mode: {env_config.get('debug', False)}")
        
        # 2. Configuration Manager Initialization
        logger.info("\n2. ⚙️  Configuration Manager Initialization")
        
        # Create temporary config directory for demo
        config_dir = Path("config/extensions")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the configuration system
        await initialize_extension_config_integration()
        logger.info("   ✅ Configuration system initialized")
        
        # Get configuration manager
        config_manager = get_config_manager()
        logger.info(f"   📁 Config directory: {config_manager.config_dir}")
        logger.info(f"   🔐 Credentials directory: {config_manager.credentials_manager.storage_path}")
        
        # 3. Environment-Specific Configurations
        logger.info("\n3. 🌍 Environment-Specific Configurations")
        
        for env in Environment:
            config = config_manager.get_config(env)
            logger.info(f"   {env.value.upper()}:")
            logger.info(f"     - Auth mode: {config.auth_mode}")
            logger.info(f"     - HTTPS required: {config.require_https}")
            logger.info(f"     - Dev bypass: {config.dev_bypass_enabled}")
            logger.info(f"     - Rate limit: {config.rate_limit_per_minute}/min")
            logger.info(f"     - Token expiry: {config.access_token_expire_minutes}min")
        
        # 4. Credential Management
        logger.info("\n4. 🔐 Credential Management")
        
        # Store a test credential
        success = config_manager.credentials_manager.store_credential(
            name="demo_api_key",
            value="demo_key_" + "x" * 32,
            environment=current_env,
            description="Demo API key for testing"
        )
        logger.info(f"   ✅ Stored demo credential: {success}")
        
        # List credentials
        credentials = config_manager.credentials_manager.list_credentials()
        logger.info(f"   📋 Total credentials: {len(credentials)}")
        
        for cred in credentials[:3]:  # Show first 3
            logger.info(f"     - {cred['name']} ({cred.get('environment', 'global')})")
        
        # 5. Configuration Validation
        logger.info("\n5. ✅ Configuration Validation")
        
        validation_result = await validate_extension_config()
        logger.info(f"   Configuration valid: {validation_result.get('valid', False)}")
        logger.info(f"   Total issues: {validation_result.get('total_issues', 0)}")
        logger.info(f"   Critical issues: {validation_result.get('critical_issues', 0)}")
        logger.info(f"   Error issues: {validation_result.get('error_issues', 0)}")
        logger.info(f"   Warning issues: {validation_result.get('warning_issues', 0)}")
        
        # Show first few issues if any
        issues = validation_result.get('issues', [])
        if issues:
            logger.info("   Sample issues:")
            for issue in issues[:3]:
                logger.info(f"     - {issue.get('severity', 'unknown').upper()}: {issue.get('message', 'No message')}")
        
        # 6. Health Checks
        logger.info("\n6. 🏥 Health Checks")
        
        health_result = await run_extension_health_checks()
        logger.info(f"   Overall status: {health_result.get('overall_status', 'unknown')}")
        logger.info(f"   Total checks: {health_result.get('checks_count', 0)}")
        logger.info(f"   Healthy: {health_result.get('healthy_count', 0)}")
        logger.info(f"   Degraded: {health_result.get('degraded_count', 0)}")
        logger.info(f"   Unhealthy: {health_result.get('unhealthy_count', 0)}")
        
        # Show health check results
        results = health_result.get('results', [])
        if results:
            logger.info("   Health check details:")
            for result in results[:5]:  # Show first 5
                status = result.get('status', 'unknown')
                name = result.get('name', 'unknown')
                message = result.get('message', 'No message')
                logger.info(f"     - {name}: {status.upper()} - {message}")
        
        # 7. Configuration Updates
        logger.info("\n7. 🔄 Configuration Updates")
        
        # Update configuration
        updates = {
            'rate_limit_per_minute': 150,
            'burst_limit': 25,
            'log_level': 'DEBUG'
        }
        
        current_env_enum = Environment(current_env) if current_env in [e.value for e in Environment] else Environment.DEVELOPMENT
        update_success = config_manager.update_config(current_env_enum, updates, save_to_file=True)
        logger.info(f"   ✅ Configuration updated: {update_success}")
        
        if update_success:
            updated_config = config_manager.get_config(current_env_enum)
            logger.info(f"   New rate limit: {updated_config.rate_limit_per_minute}/min")
            logger.info(f"   New burst limit: {updated_config.burst_limit}")
            logger.info(f"   New log level: {updated_config.log_level}")
        
        # 8. Hot Reload Demonstration
        logger.info("\n8. 🔥 Hot Reload System")
        
        # Initialize hot reload (without file watching for demo)
        await initialize_hot_reload()
        logger.info("   ✅ Hot reload system initialized")
        
        # Trigger a configuration reload
        reload_result = await reload_extension_config(environment=current_env_enum, force=True)
        logger.info(f"   Reload status: {reload_result.get('status', 'unknown')}")
        logger.info(f"   Reload trigger: {reload_result.get('trigger', 'unknown')}")
        
        if reload_result.get('changes'):
            logger.info(f"   Changes detected: {len(reload_result['changes'])}")
        
        # 9. System Status
        logger.info("\n9. 📊 System Status")
        
        system_health = config_manager.get_health_status()
        logger.info(f"   System status: {system_health.get('status', 'unknown')}")
        logger.info(f"   Environment: {system_health.get('environment', 'unknown')}")
        logger.info(f"   Config valid: {system_health.get('config_valid', False)}")
        logger.info(f"   Credentials count: {system_health.get('credentials_count', 0)}")
        logger.info(f"   Expired credentials: {system_health.get('expired_credentials_count', 0)}")
        logger.info(f"   File watching: {system_health.get('file_watching_active', False)}")
        
        # 10. Configuration Export
        logger.info("\n10. 📤 Configuration Export")
        
        # Export current configuration
        from .extension_environment_config import ConfigFormat
        
        yaml_export = config_manager.export_config(current_env_enum, ConfigFormat.YAML)
        logger.info(f"   YAML export length: {len(yaml_export)} characters")
        
        json_export = config_manager.export_config(current_env_enum, ConfigFormat.JSON)
        logger.info(f"   JSON export length: {len(json_export)} characters")
        
        env_export = config_manager.export_config(current_env_enum, ConfigFormat.ENV)
        logger.info(f"   ENV export length: {len(env_export)} characters")
        
        # Show sample of YAML export
        yaml_lines = yaml_export.split('\n')
        logger.info("   Sample YAML export:")
        for line in yaml_lines[:5]:
            logger.info(f"     {line}")
        if len(yaml_lines) > 5:
            logger.info(f"     ... ({len(yaml_lines) - 5} more lines)")
        
        logger.info("\n🎉 Demo completed successfully!")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_api_usage():
    """Demonstrate API usage patterns."""
    
    logger.info("\n📡 API Usage Patterns")
    logger.info("-" * 30)
    
    # Example API endpoint implementations
    api_examples = [
        "GET /api/extension-config/ - Get current configuration",
        "GET /api/extension-config/{environment} - Get environment-specific config",
        "PUT /api/extension-config/{environment} - Update configuration",
        "POST /api/extension-config/validate - Validate configuration",
        "GET /api/extension-config/health/status - Get health status",
        "POST /api/extension-config/reload - Reload configuration",
        "GET /api/extension-config/reload/history - Get reload history",
        "GET /api/extension-config/snapshots/{environment} - Get config snapshots",
        "GET /api/extension-config/credentials - List credentials",
        "POST /api/extension-config/credentials - Store credential",
        "POST /api/extension-config/credentials/{name}/rotate - Rotate credential",
        "GET /api/extension-config/status - Get system status",
        "GET /api/extension-config/environments - List environments"
    ]
    
    logger.info("Available API endpoints:")
    for endpoint in api_examples:
        logger.info(f"   • {endpoint}")
    
    # Example configuration update request
    logger.info("\nExample configuration update request:")
    example_update = {
        "rate_limit_per_minute": 200,
        "burst_limit": 30,
        "enable_debug_logging": True,
        "log_level": "DEBUG"
    }
    
    logger.info("   PUT /api/extension-config/development")
    logger.info("   Content-Type: application/json")
    logger.info("   {")
    for key, value in example_update.items():
        logger.info(f'     "{key}": {value if isinstance(value, bool) else f'"{value}"'},')
    logger.info("   }")
    
    # Example credential storage request
    logger.info("\nExample credential storage request:")
    logger.info("   POST /api/extension-config/credentials")
    logger.info("   Content-Type: application/json")
    logger.info("   {")
    logger.info('     "name": "my_api_key",')
    logger.info('     "value": "secret_key_value_here",')
    logger.info('     "environment": "production",')
    logger.info('     "rotation_interval_days": 30,')
    logger.info('     "description": "Production API key"')
    logger.info("   }")


def demonstrate_integration_patterns():
    """Demonstrate integration patterns with existing systems."""
    
    logger.info("\n🔗 Integration Patterns")
    logger.info("-" * 30)
    
    integration_patterns = [
        "FastAPI Lifespan Integration - Automatic startup/shutdown",
        "Middleware Integration - Request-level configuration access",
        "Authentication Integration - Dynamic auth settings",
        "Rate Limiting Integration - Environment-aware rate limits",
        "Logging Integration - Dynamic log level configuration",
        "Health Check Integration - System health monitoring",
        "Monitoring Integration - Metrics and alerting",
        "Deployment Integration - Environment-specific deployments"
    ]
    
    logger.info("Integration patterns:")
    for pattern in integration_patterns:
        logger.info(f"   • {pattern}")
    
    # Example FastAPI integration
    logger.info("\nExample FastAPI integration:")
    logger.info("""
   from fastapi import FastAPI
   from server.extension_config_integration import (
       extension_config_lifespan,
       setup_extension_config_routes,
       create_extension_config_middleware
   )
   
   app = FastAPI(lifespan=extension_config_lifespan)
   
   # Add configuration routes
   setup_extension_config_routes(app)
   
   # Add configuration middleware
   app.add_middleware(create_extension_config_middleware())
   """)
    
    # Example authentication integration
    logger.info("\nExample authentication integration:")
    logger.info("""
   from server.extension_environment_config import get_current_extension_config
   
   def get_auth_settings():
       config = get_current_extension_config()
       return {
           'secret_key': config.secret_key,
           'algorithm': config.jwt_algorithm,
           'access_token_expire_minutes': config.access_token_expire_minutes,
           'dev_bypass_enabled': config.dev_bypass_enabled
       }
   """)


async def main():
    """Main demonstration function."""
    try:
        logger.info("🎯 Extension Environment Configuration System")
        logger.info("Complete demonstration of all features")
        logger.info("=" * 60)
        
        # Run the main demonstration
        demo_success = await demonstrate_configuration_system()
        
        # Show API usage patterns
        demonstrate_api_usage()
        
        # Show integration patterns
        demonstrate_integration_patterns()
        
        if demo_success:
            logger.info("\n✅ All demonstrations completed successfully!")
            logger.info("\nThe extension environment configuration system provides:")
            logger.info("• Environment-aware configuration management")
            logger.info("• Secure credential storage and rotation")
            logger.info("• Configuration validation and health checks")
            logger.info("• Hot-reload without service restart")
            logger.info("• Comprehensive API for configuration management")
            logger.info("• Integration with FastAPI and other frameworks")
            logger.info("• Production-ready security and monitoring")
            
            return 0
        else:
            logger.error("\n❌ Some demonstrations failed!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the demonstration
    exit_code = asyncio.run(main())
    exit(exit_code)