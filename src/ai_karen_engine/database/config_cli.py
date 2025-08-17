#!/usr/bin/env python3
"""
Database Configuration CLI Tool.

This tool provides command-line utilities for validating and debugging
database configuration, helping administrators troubleshoot connection issues.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_karen_engine.database.config import (
    load_database_config,
    validate_database_connection,
    DatabaseConfigurationError
)


def validate_config_command(args) -> int:
    """Validate database configuration."""
    print("🔍 Validating database configuration...")
    
    try:
        config = load_database_config(args.env_file)
        
        print("✅ Configuration loaded successfully!")
        print(f"📊 Configuration summary:")
        
        sanitized = config.get_sanitized_config()
        for key, value in sanitized.items():
            print(f"  {key}: {value}")
        
        validation = config.get_validation_summary()
        
        if validation["errors"]:
            print(f"\n❌ Validation errors ({validation['error_count']}):")
            for error in validation["errors"]:
                print(f"  • {error}")
        
        if validation["warnings"]:
            print(f"\n⚠️  Validation warnings ({validation['warning_count']}):")
            for warning in validation["warnings"]:
                print(f"  • {warning}")
        
        if validation["valid"]:
            print(f"\n✅ Configuration is valid!")
            print(f"🔗 Database URL: {config.build_database_url()}")
            return 0
        else:
            print(f"\n❌ Configuration is invalid!")
            return 1
            
    except DatabaseConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        if e.errors:
            print("Errors:")
            for error in e.errors:
                print(f"  • {error}")
        if e.warnings:
            print("Warnings:")
            for warning in e.warnings:
                print(f"  • {warning}")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1


def test_connection_command(args) -> int:
    """Test database connection."""
    print("🔌 Testing database connection...")
    
    try:
        config = load_database_config(args.env_file)
        
        if not config.is_valid():
            print("❌ Configuration is invalid, cannot test connection")
            return 1
        
        print(f"🔗 Connecting to: {config.host}:{config.port}/{config.database}")
        
        result = validate_database_connection(config)
        
        if result["success"]:
            print("✅ Connection successful!")
            print(f"⏱️  Connection time: {result['connection_time']:.3f}s")
            print(f"🗄️  Server version: {result['server_version']}")
            print(f"📊 Database exists: {result['database_exists']}")
            return 0
        else:
            print("❌ Connection failed!")
            print(f"💥 Error: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1


def show_config_command(args) -> int:
    """Show current configuration."""
    try:
        config = load_database_config(args.env_file)
        
        if args.format == "json":
            output = {
                "config": config.get_sanitized_config(),
                "validation": config.get_validation_summary(),
                "database_url": config.build_database_url() if config.is_valid() else None,
                "async_database_url": config.build_async_database_url() if config.is_valid() else None
            }
            print(json.dumps(output, indent=2))
        else:
            print("📋 Database Configuration")
            print("=" * 50)
            
            sanitized = config.get_sanitized_config()
            for key, value in sanitized.items():
                print(f"{key:20}: {value}")
            
            validation = config.get_validation_summary()
            print(f"\n📊 Validation Status: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            
            if validation["errors"]:
                print(f"\n❌ Errors ({validation['error_count']}):")
                for error in validation["errors"]:
                    print(f"  • {error}")
            
            if validation["warnings"]:
                print(f"\n⚠️  Warnings ({validation['warning_count']}):")
                for warning in validation["warnings"]:
                    print(f"  • {warning}")
            
            if config.is_valid():
                print(f"\n🔗 Database URLs:")
                print(f"  Sync:  {config.build_database_url()}")
                print(f"  Async: {config.build_async_database_url()}")
        
        return 0
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1


def debug_env_command(args) -> int:
    """Debug environment variables."""
    import os
    from ai_karen_engine.database.config import DatabaseConfigLoader
    
    print("🔍 Environment Variables Debug")
    print("=" * 50)
    
    # Show all relevant environment variables
    for config_key, env_vars in DatabaseConfigLoader.ENV_MAPPINGS.items():
        print(f"\n{config_key}:")
        found = False
        for env_var in env_vars:
            value = os.getenv(env_var)
            if value is not None:
                # Sanitize password values
                if "password" in env_var.lower():
                    value = "***"
                print(f"  ✅ {env_var} = {value}")
                found = True
            else:
                print(f"  ❌ {env_var} = (not set)")
        
        if not found:
            print(f"  ⚠️  No environment variable found for {config_key}")
    
    # Show .env file content if it exists
    env_file = args.env_file or ".env"
    if Path(env_file).exists():
        print(f"\n📄 .env file content ({env_file}):")
        print("-" * 30)
        try:
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip()
                    # Sanitize password lines
                    if "password" in line.lower() and "=" in line:
                        key, _ = line.split("=", 1)
                        line = f"{key}=***"
                    print(f"{line_num:3}: {line}")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"\n📄 .env file not found: {env_file}")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Configuration CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s validate                    # Validate configuration
  %(prog)s test                        # Test database connection
  %(prog)s show                        # Show current configuration
  %(prog)s show --format json          # Show configuration as JSON
  %(prog)s debug                       # Debug environment variables
  %(prog)s validate --env-file .env.prod  # Use custom .env file
        """
    )
    
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate database configuration"
    )
    validate_parser.set_defaults(func=validate_config_command)
    
    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Test database connection"
    )
    test_parser.set_defaults(func=test_connection_command)
    
    # Show command
    show_parser = subparsers.add_parser(
        "show",
        help="Show current configuration"
    )
    show_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    show_parser.set_defaults(func=show_config_command)
    
    # Debug command
    debug_parser = subparsers.add_parser(
        "debug",
        help="Debug environment variables"
    )
    debug_parser.set_defaults(func=debug_env_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())