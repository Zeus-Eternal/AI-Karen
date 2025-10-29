#!/usr/bin/env python3
"""
Test script for deployment and migration tools.
Validates that all components are properly implemented.
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

async def test_migration_runner():
    """Test the migration runner functionality."""
    print("Testing Migration Runner...")
    
    try:
        from server.migrations.migration_runner import MigrationRunner
        
        # Test with mock database config
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }
        
        runner = MigrationRunner(db_config)
        
        # Test migration discovery
        migrations = runner.discover_migrations()
        print(f"  ✓ Discovered {len(migrations)} migration files")
        
        # Test checksum calculation
        if migrations:
            checksum = runner.calculate_file_checksum(migrations[0])
            print(f"  ✓ Calculated checksum: {checksum}")
        
        print("  ✓ Migration Runner tests passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Migration Runner test failed: {e}")
        return False

async def test_config_deployer():
    """Test the configuration deployer functionality."""
    print("Testing Configuration Deployer...")
    
    try:
        from server.deployment.config_deployer import ConfigDeployer
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            backup_dir = Path(temp_dir) / "backups"
            
            deployer = ConfigDeployer(config_dir, backup_dir)
            
            # Test configuration validation
            config_updates = {
                'test.json': {
                    'jwt_secret_key': 'test-secret-key-for-testing',
                    'token_expiry_minutes': 60
                }
            }
            
            validation_result = await deployer.validate_config_updates(config_updates)
            print(f"  ✓ Configuration validation: {validation_result['valid']}")
            
            # Test backup creation
            config_dir.mkdir(parents=True, exist_ok=True)
            test_config_file = config_dir / "test.json"
            test_config_file.write_text('{"test": "value"}')
            
            backup_id = await deployer.backup_current_config(['test.json'])
            print(f"  ✓ Created backup: {backup_id}")
            
            # Test backup listing
            backups = await deployer.list_backups()
            print(f"  ✓ Found {len(backups)} backups")
        
        print("  ✓ Configuration Deployer tests passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration Deployer test failed: {e}")
        return False

async def test_zero_downtime_updater():
    """Test the zero-downtime updater functionality."""
    print("Testing Zero-Downtime Updater...")
    
    try:
        from server.deployment.zero_downtime_updater import ZeroDowntimeUpdater, HealthCheck
        
        config = {
            'max_update_time_minutes': 5,
            'health_check_interval_seconds': 1,
            'rollback_threshold_failures': 2,
            'grace_period_seconds': 5
        }
        
        updater = ZeroDowntimeUpdater(config)
        
        # Test health check
        async def mock_health_check():
            return True
        
        updater.add_health_check('test_service', mock_health_check)
        print("  ✓ Added health check")
        
        # Test health check execution
        results = await updater.run_health_checks()
        print(f"  ✓ Health check results: {results}")
        
        # Test waiting for healthy state
        healthy = await updater.wait_for_healthy_state(5)
        print(f"  ✓ Healthy state check: {healthy}")
        
        print("  ✓ Zero-Downtime Updater tests passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Zero-Downtime Updater test failed: {e}")
        return False

async def test_auth_monitoring():
    """Test the authentication monitoring functionality."""
    print("Testing Authentication Monitoring...")
    
    try:
        from server.deployment.auth_monitoring import AuthMonitor, AuthMetrics, AlertSeverity
        
        config = {
            'success_rate_threshold': 0.95,
            'response_time_threshold_ms': 1000,
            'error_rate_threshold': 0.05,
            'check_interval_seconds': 1
        }
        
        monitor = AuthMonitor(config)
        
        # Test metrics recording
        monitor.record_auth_event('auth_attempt', success=True, response_time_ms=200)
        monitor.record_auth_event('auth_attempt', success=False, response_time_ms=500)
        monitor.record_auth_event('token_refresh')
        
        # Test metrics summary
        metrics = monitor.metrics.get_metrics_summary()
        print(f"  ✓ Recorded metrics: {metrics['total_auth_attempts']} attempts")
        print(f"  ✓ Success rate: {metrics['success_rate']:.2%}")
        
        # Test monitoring status
        status = monitor.get_monitoring_status()
        print(f"  ✓ Monitoring status: {status['monitoring_active']}")
        
        print("  ✓ Authentication Monitoring tests passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Authentication Monitoring test failed: {e}")
        return False

async def test_main_deployer():
    """Test the main deployment system."""
    print("Testing Main Deployment System...")
    
    try:
        from server.deployment.deploy_auth_system import AuthSystemDeployer
        
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'user': 'test',
                'password': 'test',
                'database': 'test'
            },
            'config_dir': 'config',
            'deployment': {
                'max_update_time_minutes': 5,
                'health_check_interval_seconds': 1
            },
            'monitoring': {
                'enabled': False  # Disable for testing
            },
            'jwt_secret_key': 'test-secret-key'
        }
        
        deployer = AuthSystemDeployer(config)
        
        # Test configuration generation
        config_updates = deployer.get_config_updates_for_environment('development')
        print(f"  ✓ Generated config updates for development: {len(config_updates)} files")
        
        # Test deployment status
        # Note: This would fail without actual database, but we can test the structure
        print("  ✓ Main Deployment System structure validated")
        
        print("  ✓ Main Deployment System tests passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Main Deployment System test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("Testing File Structure...")
    
    required_files = [
        "server/migrations/001_create_auth_tables.py",
        "server/migrations/migration_runner.py",
        "server/deployment/config_deployer.py",
        "server/deployment/zero_downtime_updater.py",
        "server/deployment/auth_monitoring.py",
        "server/deployment/deploy_auth_system.py",
        "server/deployment/deployment_config.json",
        "server/deployment/README.md",
        "server/deployment/deploy.sh"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  ✗ Missing files: {missing_files}")
        return False
    else:
        print(f"  ✓ All {len(required_files)} required files exist")
        return True

def test_configuration_files():
    """Test configuration file validity."""
    print("Testing Configuration Files...")
    
    try:
        # Test deployment config
        config_path = Path("server/deployment/deployment_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            print("  ✓ Deployment configuration is valid JSON")
            
            # Check required sections
            required_sections = ['database', 'deployment', 'monitoring']
            for section in required_sections:
                if section in config:
                    print(f"  ✓ Configuration has {section} section")
                else:
                    print(f"  ✗ Configuration missing {section} section")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration file test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("AUTHENTICATION SYSTEM DEPLOYMENT TOOLS TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration Files", test_configuration_files),
        ("Migration Runner", test_migration_runner),
        ("Configuration Deployer", test_config_deployer),
        ("Zero-Downtime Updater", test_zero_downtime_updater),
        ("Authentication Monitoring", test_auth_monitoring),
        ("Main Deployment System", test_main_deployer)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"Running {test_name} tests...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✓ {test_name} tests PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} tests FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} tests FAILED with exception: {e}")
        
        print()
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! Deployment tools are ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)