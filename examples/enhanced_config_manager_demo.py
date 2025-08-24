#!/usr/bin/env python3
"""
Enhanced Configuration Manager Demo

This script demonstrates the usage of the enhanced configuration manager
that addresses requirements 9.1-9.5 from the system-warnings-errors-fix specification.
"""

import json
import os
import tempfile
from pathlib import Path

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.config.enhanced_config_manager import (
    ConfigurationManager,
    EnvironmentVariableConfig,
    get_enhanced_config_manager,
    initialize_enhanced_config_manager
)


def demo_basic_usage():
    """Demonstrate basic configuration manager usage"""
    print("=== Basic Configuration Manager Usage ===")
    
    # Create a temporary config file
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "demo_config.json"
    
    # Create sample configuration
    sample_config = {
        'environment': 'demo',
        'database': {
            'host': 'demo-db',
            'port': 5432
        },
        'features': {
            'enable_ai': True,
            'max_connections': 100
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    # Initialize configuration manager
    manager = ConfigurationManager(config_path=config_path)
    
    # Load configuration
    config = manager.load_config()
    
    print(f"Loaded configuration from: {config_path}")
    print(f"Environment: {config['environment']}")
    print(f"Database host: {config['database']['host']}")
    print(f"AI enabled: {config['features']['enable_ai']}")
    
    # Demonstrate get_with_fallback
    print(f"Database timeout (with fallback): {manager.get_with_fallback('database.timeout', 30)}")
    print(f"Missing config (with fallback): {manager.get_with_fallback('missing.key', 'default_value')}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print()


def demo_environment_validation():
    """Demonstrate environment variable validation"""
    print("=== Environment Variable Validation ===")
    
    # Set some environment variables
    os.environ['DEMO_DB_HOST'] = 'env-db-host'
    os.environ['DEMO_DEBUG'] = 'true'
    os.environ['DEMO_PORT'] = '8080'
    
    # Create custom environment mappings
    custom_env_mappings = [
        EnvironmentVariableConfig(
            env_var="DEMO_DB_HOST",
            config_path="database.host",
            required=True,
            description="Database host for demo"
        ),
        EnvironmentVariableConfig(
            env_var="DEMO_DEBUG",
            config_path="debug",
            value_type="bool",
            default_value=False,
            description="Enable debug mode"
        ),
        EnvironmentVariableConfig(
            env_var="DEMO_PORT",
            config_path="server.port",
            value_type="int",
            default_value=3000,
            description="Server port"
        ),
        EnvironmentVariableConfig(
            env_var="DEMO_MISSING_REQUIRED",
            config_path="required.setting",
            required=True,
            description="This should trigger a validation error"
        )
    ]
    
    manager = ConfigurationManager(env_mappings=custom_env_mappings)
    
    # Validate environment
    validation_result = manager.validate_environment()
    
    print(f"Environment validation result: {'VALID' if validation_result.is_valid else 'INVALID'}")
    print(f"Issues found: {len(validation_result.issues)}")
    print(f"Missing required: {validation_result.missing_required}")
    
    # Show validation issues
    for issue in validation_result.issues:
        severity_icon = "❌" if issue.severity.value in ['error', 'critical'] else "⚠️"
        print(f"  {severity_icon} {issue.key}: {issue.message}")
        print(f"     Fix: {issue.suggested_fix}")
    
    # Clean up environment variables
    for env_var in ['DEMO_DB_HOST', 'DEMO_DEBUG', 'DEMO_PORT']:
        os.environ.pop(env_var, None)
    
    print()


def demo_pydantic_migration():
    """Demonstrate Pydantic V1 to V2 migration"""
    print("=== Pydantic V1 to V2 Migration ===")
    
    manager = ConfigurationManager(enable_migration=True)
    
    # Configuration with deprecated Pydantic V1 patterns
    config_with_deprecated = {
        'model_settings': {
            'schema_extra': {
                'example': 'This should be migrated to json_schema_extra'
            }
        },
        'other_config': 'value'
    }
    
    print("Original config with deprecated patterns:")
    print(json.dumps(config_with_deprecated, indent=2))
    
    # Migrate configuration
    migrated_config = manager.migrate_pydantic_config(config_with_deprecated)
    
    print("\nMigrated config:")
    print(json.dumps(migrated_config, indent=2))
    
    # Check if migration was successful
    config_str = json.dumps(migrated_config)
    has_json_schema_extra = 'json_schema_extra' in config_str
    has_old_schema_extra = '"schema_extra"' in config_str
    
    print(f"\nMigration successful: {has_json_schema_extra and not has_old_schema_extra}")
    print()


def demo_health_checks():
    """Demonstrate configuration health checks"""
    print("=== Configuration Health Checks ===")
    
    # Create a temporary config file
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "health_demo_config.json"
    
    # Create configuration with some issues
    config_with_issues = {
        'environment': 'production',
        'security': {
            'jwt_secret': 'change-me-in-production'  # This should trigger a warning
        },
        'database': {
            'host': 'localhost'
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_with_issues, f, indent=2)
    
    # Set a required environment variable
    os.environ['JWT_SECRET'] = 'secure-production-secret'
    
    manager = ConfigurationManager(
        config_path=config_path,
        enable_health_checks=True
    )
    
    # Load config to trigger health checks
    config = manager.load_config()
    
    # Perform explicit health checks
    health_result = manager.perform_health_checks()
    
    print(f"Overall health status: {health_result['overall_status'].upper()}")
    print(f"Health check timestamp: {health_result['timestamp']}")
    print("\nHealth check details:")
    
    for check_name, check_result in health_result['checks'].items():
        status_icon = "✅" if check_result['status'] == 'healthy' else ("⚠️" if check_result['status'] == 'warning' else "❌")
        print(f"  {status_icon} {check_name}: {check_result['message']}")
    
    # Clean up
    os.environ.pop('JWT_SECRET', None)
    import shutil
    shutil.rmtree(temp_dir)
    print()


def demo_configuration_summary():
    """Demonstrate configuration summary"""
    print("=== Configuration Summary ===")
    
    manager = ConfigurationManager()
    
    # Get summary before loading config
    summary_before = manager.get_configuration_summary()
    print("Summary before loading config:")
    for key, value in summary_before.items():
        print(f"  {key}: {value}")
    
    # Load config
    config = manager.load_config()
    
    # Get summary after loading config
    summary_after = manager.get_configuration_summary()
    print("\nSummary after loading config:")
    for key, value in summary_after.items():
        print(f"  {key}: {value}")
    
    print()


def demo_global_config_manager():
    """Demonstrate global configuration manager"""
    print("=== Global Configuration Manager ===")
    
    # Initialize global config manager
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "global_demo_config.json"
    
    global_config = {
        'app_name': 'AI Karen Enhanced Config Demo',
        'version': '1.0.0',
        'features': {
            'enhanced_config': True
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(global_config, f, indent=2)
    
    # Initialize global manager
    manager = initialize_enhanced_config_manager(config_path=str(config_path))
    config = manager.load_config()
    
    print(f"Global config manager initialized")
    print(f"App name: {config['app_name']}")
    print(f"Version: {config['version']}")
    
    # Get the same instance
    same_manager = get_enhanced_config_manager()
    print(f"Same instance: {manager is same_manager}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print()


def main():
    """Run all demonstrations"""
    print("Enhanced Configuration Manager Demo")
    print("=" * 50)
    print()
    
    try:
        demo_basic_usage()
        demo_environment_validation()
        demo_pydantic_migration()
        demo_health_checks()
        demo_configuration_summary()
        demo_global_config_manager()
        
        print("✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()