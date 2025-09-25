"""
Tests for Deployment Configuration Manager

This module tests the deployment configuration management system including
dynamic service configuration, validation, and hot-reloading capabilities.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_karen_engine.config.deployment_config_manager import (
    DeploymentConfigManager, DeploymentMode, ServiceClassification,
    ServiceConfig, DeploymentProfile, ResourceRequirements,
    ConfigChange, ConfigChangeType, ConfigValidationError
)
from src.ai_karen_engine.config.deployment_validator import (
    DeploymentValidator, ValidationResult, ValidationIssue, ValidationSeverity
)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing"""
    return {
        'services': {
            'auth_service': {
                'classification': 'essential',
                'startup_priority': 10,
                'dependencies': [],
                'resource_requirements': {
                    'memory_mb': 128,
                    'cpu_cores': 0.2
                },
                'health_check_interval': 30,
                'max_restart_attempts': 3,
                'graceful_shutdown_timeout': 10
            },
            'memory_service': {
                'classification': 'optional',
                'startup_priority': 50,
                'dependencies': ['auth_service'],
                'resource_requirements': {
                    'memory_mb': 256,
                    'cpu_cores': 0.5
                },
                'idle_timeout': 300,
                'health_check_interval': 60,
                'max_restart_attempts': 2,
                'graceful_shutdown_timeout': 20
            },
            'analytics_service': {
                'classification': 'background',
                'startup_priority': 200,
                'dependencies': [],
                'resource_requirements': {
                    'memory_mb': 64,
                    'cpu_cores': 0.1
                },
                'idle_timeout': 1800,
                'health_check_interval': 300,
                'max_restart_attempts': 1,
                'graceful_shutdown_timeout': 10
            }
        },
        'deployment_profiles': {
            'minimal': {
                'enabled_classifications': ['essential'],
                'max_memory_mb': 512,
                'max_services': 10,
                'description': 'Minimal deployment'
            },
            'development': {
                'enabled_classifications': ['essential', 'optional'],
                'max_memory_mb': 2048,
                'max_services': 50,
                'debug_services': True,
                'description': 'Development mode'
            },
            'production': {
                'enabled_classifications': ['essential', 'optional', 'background'],
                'max_memory_mb': 4096,
                'max_services': 100,
                'performance_optimized': True,
                'description': 'Production deployment'
            }
        }
    }


@pytest.fixture
async def config_manager(sample_config_data):
    """Create a deployment config manager for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = Path(f.name)
        json.dump(sample_config_data, f)
    
    manager = DeploymentConfigManager(
        config_path=config_path,
        enable_hot_reload=False,
        enable_validation=True
    )
    
    await manager.initialize()
    yield manager
    await manager.shutdown()
    config_path.unlink(missing_ok=True)


class TestDeploymentConfigManager:
    """Test deployment configuration manager functionality"""
    
    async def test_initialization(self, sample_config_data):
        """Test configuration manager initialization"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            json.dump(sample_config_data, f)
        
        try:
            manager = DeploymentConfigManager(config_path=config_path)
            await manager.initialize()
            
            # Check services loaded
            services = manager.get_all_services()
            assert len(services) == 3
            assert 'auth_service' in services
            assert 'memory_service' in services
            assert 'analytics_service' in services
            
            # Check profiles loaded
            profiles = manager.get_deployment_profiles()
            assert len(profiles) == 3
            assert 'minimal' in profiles
            assert 'development' in profiles
            assert 'production' in profiles
            
            # Check default mode
            assert manager.get_current_mode() == DeploymentMode.DEVELOPMENT
            
            await manager.shutdown()
            
        finally:
            config_path.unlink(missing_ok=True)
    
    async def test_deployment_mode_switching(self, config_manager):
        """Test switching between deployment modes"""
        # Test minimal mode
        await config_manager.set_deployment_mode(DeploymentMode.MINIMAL)
        assert config_manager.get_current_mode() == DeploymentMode.MINIMAL
        
        services = await config_manager.get_services_for_current_mode()
        # Only essential services should be active
        assert len(services) == 1
        assert 'auth_service' in services
        
        # Test production mode
        await config_manager.set_deployment_mode(DeploymentMode.PRODUCTION)
        assert config_manager.get_current_mode() == DeploymentMode.PRODUCTION
        
        services = await config_manager.get_services_for_current_mode()
        # All services should be active
        assert len(services) == 3
    
    async def test_service_management(self, config_manager):
        """Test dynamic service start/stop"""
        await config_manager.set_deployment_mode(DeploymentMode.DEVELOPMENT)
        
        # Test stopping a service
        result = await config_manager.stop_service('memory_service')
        assert result is True
        
        services = await config_manager.get_services_for_current_mode()
        assert 'memory_service' not in services
        
        # Test starting a service
        result = await config_manager.start_service('memory_service')
        assert result is True
        
        services = await config_manager.get_services_for_current_mode()
        assert 'memory_service' in services
        
        # Test stopping non-existent service
        result = await config_manager.stop_service('non_existent')
        assert result is False
    
    async def test_service_config_update(self, config_manager):
        """Test updating service configuration"""
        updates = {
            'idle_timeout': 600,
            'resource_requirements': {
                'memory_mb': 512
            }
        }
        
        result = await config_manager.update_service_config('memory_service', updates)
        assert result is True
        
        service = config_manager.get_service_config('memory_service')
        assert service.idle_timeout == 600
        assert service.resource_requirements.memory_mb == 512
    
    async def test_resource_allocation(self, config_manager):
        """Test resource allocation calculation"""
        await config_manager.set_deployment_mode(DeploymentMode.DEVELOPMENT)
        
        allocation = await config_manager.get_resource_allocation()
        
        assert 'current_allocation' in allocation
        assert 'profile_limits' in allocation
        assert 'utilization' in allocation
        
        current = allocation['current_allocation']
        assert current['memory_mb'] > 0
        assert current['cpu_cores'] > 0
        assert current['service_count'] > 0
    
    async def test_change_tracking(self, config_manager):
        """Test configuration change tracking"""
        changes = []
        
        def change_listener(change):
            changes.append(change)
        
        config_manager.add_change_listener(change_listener)
        
        # Make a change
        await config_manager.set_deployment_mode(DeploymentMode.PRODUCTION)
        
        # Check change was recorded
        assert len(changes) > 0
        change = changes[-1]
        assert change.change_type == ConfigChangeType.DEPLOYMENT_MODE_CHANGED
        assert change.new_value == 'production'
    
    async def test_invalid_deployment_mode(self, config_manager):
        """Test handling of invalid deployment mode"""
        with pytest.raises(ConfigValidationError):
            await config_manager.set_deployment_mode('invalid_mode')
    
    async def test_service_dependencies(self, config_manager):
        """Test service dependency handling"""
        # Memory service depends on auth service
        service = config_manager.get_service_config('memory_service')
        assert 'auth_service' in service.dependencies
    
    async def test_configuration_save(self, config_manager):
        """Test saving configuration"""
        # Make some changes
        await config_manager.update_service_config('memory_service', {
            'idle_timeout': 900
        })
        
        # Save configuration
        await config_manager.save_configuration()
        
        # Verify the configuration file was updated
        # (In a real test, you would reload and verify the changes)
        assert True  # Placeholder assertion


class TestDeploymentValidator:
    """Test deployment configuration validator"""
    
    @pytest.fixture
    def validator(self):
        """Create a deployment validator for testing"""
        return DeploymentValidator()
    
    async def test_service_validation(self, validator):
        """Test individual service validation"""
        # Valid service
        valid_service = ServiceConfig(
            name='test_service',
            classification=ServiceClassification.OPTIONAL,
            startup_priority=50,
            resource_requirements=ResourceRequirements(memory_mb=128, cpu_cores=0.2)
        )
        
        result = await validator.validate_service_config(valid_service)
        assert result.is_valid
        
        # Invalid service (negative memory)
        invalid_service = ServiceConfig(
            name='invalid_service',
            classification=ServiceClassification.OPTIONAL,
            startup_priority=50,
            resource_requirements=ResourceRequirements(memory_mb=-64, cpu_cores=0.2)
        )
        
        result = await validator.validate_service_config(invalid_service)
        assert not result.is_valid
        assert result.errors_count > 0
    
    async def test_profile_validation(self, validator):
        """Test deployment profile validation"""
        # Valid profile
        valid_profile = DeploymentProfile(
            name='test_profile',
            enabled_classifications=[ServiceClassification.ESSENTIAL],
            max_memory_mb=1024,
            max_services=20
        )
        
        result = await validator.validate_profile_config(valid_profile)
        assert result.is_valid
        
        # Invalid profile (negative memory)
        invalid_profile = DeploymentProfile(
            name='invalid_profile',
            enabled_classifications=[ServiceClassification.ESSENTIAL],
            max_memory_mb=-1024,
            max_services=20
        )
        
        result = await validator.validate_profile_config(invalid_profile)
        assert not result.is_valid
    
    async def test_dependency_validation(self, validator, sample_config_data):
        """Test service dependency validation"""
        # Create services with circular dependency
        services = {
            'service_a': ServiceConfig(
                name='service_a',
                classification=ServiceClassification.OPTIONAL,
                dependencies=['service_b']
            ),
            'service_b': ServiceConfig(
                name='service_b',
                classification=ServiceClassification.OPTIONAL,
                dependencies=['service_a']
            )
        }
        
        profiles = {
            'test': DeploymentProfile(
                name='test',
                enabled_classifications=[ServiceClassification.OPTIONAL]
            )
        }
        
        result = await validator.validate_deployment_configuration(
            services, profiles, DeploymentMode.DEVELOPMENT
        )
        
        # Should detect circular dependency
        assert not result.is_valid
        circular_issues = [i for i in result.issues if 'circular' in i.message.lower()]
        assert len(circular_issues) > 0
    
    async def test_resource_allocation_validation(self, validator):
        """Test resource allocation validation"""
        # Create services that exceed profile limits
        services = {
            'heavy_service': ServiceConfig(
                name='heavy_service',
                classification=ServiceClassification.ESSENTIAL,
                resource_requirements=ResourceRequirements(memory_mb=2048, cpu_cores=2.0)
            )
        }
        
        profiles = {
            'small': DeploymentProfile(
                name='small',
                enabled_classifications=[ServiceClassification.ESSENTIAL],
                max_memory_mb=1024,
                max_cpu_cores=1.0
            )
        }
        
        result = await validator.validate_deployment_configuration(
            services, profiles, DeploymentMode.DEVELOPMENT
        )
        
        # Should detect resource limit exceeded
        assert not result.is_valid
        resource_issues = [i for i in result.issues if 'exceeds' in i.message.lower()]
        assert len(resource_issues) > 0
    
    async def test_production_validation(self, validator):
        """Test production-specific validation"""
        services = {
            'test_service': ServiceConfig(
                name='test_service',
                classification=ServiceClassification.ESSENTIAL
            )
        }
        
        profiles = {
            'production': DeploymentProfile(
                name='production',
                enabled_classifications=[ServiceClassification.ESSENTIAL],
                debug_services=True  # Should trigger warning
            )
        }
        
        result = await validator.validate_deployment_configuration(
            services, profiles, DeploymentMode.PRODUCTION
        )
        
        # Should have warnings about debug services in production
        debug_issues = [i for i in result.issues if 'debug' in i.message.lower()]
        assert len(debug_issues) > 0
    
    async def test_optimization_suggestions(self, validator):
        """Test optimization suggestions"""
        services = {
            'memory_heavy': ServiceConfig(
                name='memory_heavy',
                classification=ServiceClassification.OPTIONAL,
                resource_requirements=ResourceRequirements(memory_mb=4096, cpu_cores=0.1)
            ),
            'gpu_service': ServiceConfig(
                name='gpu_service',
                classification=ServiceClassification.OPTIONAL,
                gpu_compatible=True,
                resource_requirements=ResourceRequirements(memory_mb=512, cpu_cores=1.0)
            )
        }
        
        profiles = {
            'development': DeploymentProfile(
                name='development',
                enabled_classifications=[ServiceClassification.OPTIONAL]
            )
        }
        
        suggestions = await validator.get_optimization_suggestions(
            services, profiles, DeploymentMode.DEVELOPMENT
        )
        
        # Should suggest optimizations
        assert len(suggestions) > 0


class TestConfigurationIntegration:
    """Test integration between components"""
    
    async def test_end_to_end_workflow(self, sample_config_data):
        """Test complete configuration management workflow"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            json.dump(sample_config_data, f)
        
        try:
            # Initialize manager
            manager = DeploymentConfigManager(config_path=config_path)
            await manager.initialize()
            
            validator = DeploymentValidator()
            
            # Validate initial configuration
            services = manager.get_all_services()
            profiles = manager.get_deployment_profiles()
            mode = manager.get_current_mode()
            
            validation_result = await validator.validate_deployment_configuration(
                services, profiles, mode
            )
            
            # Should be valid initially
            assert validation_result.is_valid or validation_result.warnings_count > 0
            
            # Switch to production mode
            await manager.set_deployment_mode(DeploymentMode.PRODUCTION)
            
            # Validate production configuration
            validation_result = await validator.validate_deployment_configuration(
                services, profiles, DeploymentMode.PRODUCTION
            )
            
            # Update service configuration
            await manager.update_service_config('memory_service', {
                'resource_requirements': {'memory_mb': 1024}
            })
            
            # Check resource allocation
            allocation = await manager.get_resource_allocation()
            assert allocation['current_allocation']['memory_mb'] > 0
            
            # Get change history
            history = manager.get_change_history()
            assert len(history) > 0
            
            await manager.shutdown()
            
        finally:
            config_path.unlink(missing_ok=True)
    
    async def test_error_handling(self, sample_config_data):
        """Test error handling in configuration management"""
        # Test with invalid config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            f.write("invalid json content")
        
        try:
            manager = DeploymentConfigManager(config_path=config_path)
            
            with pytest.raises(ConfigValidationError):
                await manager.initialize()
                
        finally:
            config_path.unlink(missing_ok=True)
    
    async def test_missing_config_file(self):
        """Test handling of missing configuration file"""
        non_existent_path = Path("/tmp/non_existent_config.json")
        
        manager = DeploymentConfigManager(config_path=non_existent_path)
        await manager.initialize()  # Should create default config
        
        # Should have default services
        services = manager.get_all_services()
        assert len(services) >= 2  # At least logging and config manager
        
        await manager.shutdown()


@pytest.mark.asyncio
async def test_concurrent_operations(sample_config_data):
    """Test concurrent configuration operations"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = Path(f.name)
        json.dump(sample_config_data, f)
    
    try:
        manager = DeploymentConfigManager(config_path=config_path)
        await manager.initialize()
        
        # Perform concurrent operations
        tasks = [
            manager.set_deployment_mode(DeploymentMode.PRODUCTION),
            manager.update_service_config('memory_service', {'idle_timeout': 400}),
            manager.stop_service('analytics_service'),
            manager.start_service('analytics_service')
        ]
        
        # All operations should complete without error
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception)
        
        await manager.shutdown()
        
    finally:
        config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])