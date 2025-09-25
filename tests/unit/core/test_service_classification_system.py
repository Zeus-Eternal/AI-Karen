"""
Tests for the Service Classification and Configuration System.

This module tests the service classification, configuration loading,
dependency analysis, and classified service registry functionality.
"""

import asyncio
import json
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

from src.ai_karen_engine.core.service_classification import (
    ServiceClassification,
    DeploymentMode,
    ServiceConfig,
    ResourceRequirements,
    ServiceConfigurationLoader,
    DependencyGraphAnalyzer,
    ServiceConfigurationValidator,
)

from src.ai_karen_engine.core.classified_service_registry import (
    ClassifiedServiceRegistry,
    ServiceLifecycleState,
    ClassifiedServiceInfo,
)


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str = "mock_service"):
        self.name = name
        self.initialized = False
        self.shutdown_called = False
    
    async def initialize(self):
        self.initialized = True
    
    async def shutdown(self):
        self.shutdown_called = True


class TestServiceConfig:
    """Test ServiceConfig data model."""
    
    def test_service_config_creation(self):
        """Test creating a ServiceConfig instance."""
        config = ServiceConfig(
            name="test_service",
            classification=ServiceClassification.ESSENTIAL,
            startup_priority=10,
            dependencies=["dep1", "dep2"],
            resource_requirements=ResourceRequirements(memory_mb=128, cpu_cores=0.5),
            gpu_compatible=True,
            idle_timeout=300,
        )
        
        assert config.name == "test_service"
        assert config.classification == ServiceClassification.ESSENTIAL
        assert config.startup_priority == 10
        assert config.dependencies == ["dep1", "dep2"]
        assert config.resource_requirements.memory_mb == 128
        assert config.resource_requirements.cpu_cores == 0.5
        assert config.gpu_compatible is True
        assert config.idle_timeout == 300
    
    def test_service_config_serialization(self):
        """Test ServiceConfig to_dict and from_dict methods."""
        config = ServiceConfig(
            name="test_service",
            classification=ServiceClassification.OPTIONAL,
            startup_priority=50,
            resource_requirements=ResourceRequirements(memory_mb=256),
        )
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["name"] == "test_service"
        assert config_dict["classification"] == ServiceClassification.OPTIONAL
        assert config_dict["startup_priority"] == 50
        
        # Test from_dict
        restored_config = ServiceConfig.from_dict(config_dict)
        assert restored_config.name == config.name
        assert restored_config.classification == config.classification
        assert restored_config.startup_priority == config.startup_priority


class TestServiceConfigurationLoader:
    """Test ServiceConfigurationLoader functionality."""
    
    def test_default_configurations(self):
        """Test that default configurations are loaded."""
        loader = ServiceConfigurationLoader([])
        
        # Check that default services are loaded
        assert "auth_service" in loader.services
        assert "config_manager" in loader.services
        assert "logging_service" in loader.services
        
        # Check classifications
        auth_config = loader.get_service_config("auth_service")
        assert auth_config.classification == ServiceClassification.ESSENTIAL
        
        memory_config = loader.get_service_config("memory_service")
        assert memory_config.classification == ServiceClassification.OPTIONAL
        
        analytics_config = loader.get_service_config("analytics_service")
        assert analytics_config.classification == ServiceClassification.BACKGROUND
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "services": {
                "test_service": {
                    "classification": "essential",
                    "startup_priority": 15,
                    "dependencies": ["dep1"],
                    "resource_requirements": {
                        "memory_mb": 64,
                        "cpu_cores": 0.2
                    },
                    "idle_timeout": 600
                }
            },
            "deployment_profiles": {
                "test_mode": {
                    "enabled_classifications": ["essential"],
                    "max_memory_mb": 1024
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            loader = ServiceConfigurationLoader([config_path])
            loader.load_configurations()
            
            # Check loaded service
            test_config = loader.get_service_config("test_service")
            assert test_config is not None
            assert test_config.classification == ServiceClassification.ESSENTIAL
            assert test_config.startup_priority == 15
            assert test_config.dependencies == ["dep1"]
            assert test_config.resource_requirements.memory_mb == 64
            assert test_config.idle_timeout == 600
            
            # Check deployment profile
            assert DeploymentMode.TEST_MODE in loader.deployment_profiles
            
        finally:
            Path(config_path).unlink()
    
    def test_get_services_by_classification(self):
        """Test filtering services by classification."""
        loader = ServiceConfigurationLoader([])
        
        essential_services = loader.get_services_by_classification(ServiceClassification.ESSENTIAL)
        optional_services = loader.get_services_by_classification(ServiceClassification.OPTIONAL)
        background_services = loader.get_services_by_classification(ServiceClassification.BACKGROUND)
        
        # Check that we have services in each category
        assert len(essential_services) > 0
        assert len(optional_services) > 0
        assert len(background_services) > 0
        
        # Check that all services in each category have correct classification
        for service in essential_services:
            assert service.classification == ServiceClassification.ESSENTIAL
        
        for service in optional_services:
            assert service.classification == ServiceClassification.OPTIONAL
        
        for service in background_services:
            assert service.classification == ServiceClassification.BACKGROUND
    
    def test_get_services_for_deployment_mode(self):
        """Test getting services for different deployment modes."""
        loader = ServiceConfigurationLoader([])
        
        minimal_services = loader.get_services_for_deployment_mode(DeploymentMode.MINIMAL)
        production_services = loader.get_services_for_deployment_mode(DeploymentMode.PRODUCTION)
        
        # Minimal should only have essential services
        for service in minimal_services:
            assert service.classification == ServiceClassification.ESSENTIAL
        
        # Production should have all classifications
        production_classifications = {service.classification for service in production_services}
        assert ServiceClassification.ESSENTIAL in production_classifications
        assert ServiceClassification.OPTIONAL in production_classifications
        assert ServiceClassification.BACKGROUND in production_classifications


class TestDependencyGraphAnalyzer:
    """Test DependencyGraphAnalyzer functionality."""
    
    def create_test_services(self) -> Dict[str, ServiceConfig]:
        """Create test services with dependencies."""
        return {
            "service_a": ServiceConfig(
                name="service_a",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=10,
                dependencies=[]
            ),
            "service_b": ServiceConfig(
                name="service_b",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=20,
                dependencies=["service_a"]
            ),
            "service_c": ServiceConfig(
                name="service_c",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=30,
                dependencies=["service_b"]
            ),
            "service_d": ServiceConfig(
                name="service_d",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=40,
                dependencies=["service_a", "service_c"]
            ),
        }
    
    def test_dependency_graph_construction(self):
        """Test that dependency graph is built correctly."""
        services = self.create_test_services()
        analyzer = DependencyGraphAnalyzer(services)
        
        # Check that all services are in the graph
        assert len(analyzer.graph) == 4
        assert "service_a" in analyzer.graph
        assert "service_b" in analyzer.graph
        assert "service_c" in analyzer.graph
        assert "service_d" in analyzer.graph
        
        # Check dependencies
        assert len(analyzer.graph["service_a"].dependencies) == 0
        assert "service_a" in analyzer.graph["service_b"].dependencies
        assert "service_b" in analyzer.graph["service_c"].dependencies
        assert "service_a" in analyzer.graph["service_d"].dependencies
        assert "service_c" in analyzer.graph["service_d"].dependencies
        
        # Check dependents
        assert "service_b" in analyzer.graph["service_a"].dependents
        assert "service_d" in analyzer.graph["service_a"].dependents
        assert "service_c" in analyzer.graph["service_b"].dependents
        assert "service_d" in analyzer.graph["service_c"].dependents
    
    def test_startup_order(self):
        """Test that startup order respects dependencies and priorities."""
        services = self.create_test_services()
        analyzer = DependencyGraphAnalyzer(services)
        
        startup_order = analyzer.get_startup_order()
        
        # Check that dependencies come before dependents
        a_index = startup_order.index("service_a")
        b_index = startup_order.index("service_b")
        c_index = startup_order.index("service_c")
        d_index = startup_order.index("service_d")
        
        assert a_index < b_index  # service_a before service_b
        assert b_index < c_index  # service_b before service_c
        assert a_index < d_index  # service_a before service_d
        assert c_index < d_index  # service_c before service_d
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        services = {
            "service_a": ServiceConfig(
                name="service_a",
                classification=ServiceClassification.ESSENTIAL,
                dependencies=["service_b"]
            ),
            "service_b": ServiceConfig(
                name="service_b",
                classification=ServiceClassification.ESSENTIAL,
                dependencies=["service_c"]
            ),
            "service_c": ServiceConfig(
                name="service_c",
                classification=ServiceClassification.ESSENTIAL,
                dependencies=["service_a"]  # Creates circular dependency
            ),
        }
        
        analyzer = DependencyGraphAnalyzer(services)
        circular_deps = analyzer.detect_circular_dependencies()
        
        assert len(circular_deps) > 0
        # Should detect the circular dependency involving all three services
        cycle = circular_deps[0]
        assert len(cycle) >= 3
    
    def test_resource_analysis(self):
        """Test resource requirements analysis."""
        services = self.create_test_services()
        
        # Add resource requirements
        services["service_a"].resource_requirements = ResourceRequirements(memory_mb=100, cpu_cores=0.5)
        services["service_b"].resource_requirements = ResourceRequirements(memory_mb=200, cpu_cores=1.0)
        services["service_c"].resource_requirements = ResourceRequirements(memory_mb=150, cpu_cores=0.5)
        services["service_d"].resource_requirements = ResourceRequirements(memory_mb=50, cpu_cores=0.2)
        
        analyzer = DependencyGraphAnalyzer(services)
        analysis = analyzer.analyze_resource_requirements()
        
        # Check total resources
        assert analysis["total"].memory_mb == 500  # 100 + 200 + 150 + 50
        assert analysis["total"].cpu_cores == 2.2  # 0.5 + 1.0 + 0.5 + 0.2
        
        # Check by classification
        essential_analysis = analysis["by_classification"]["essential"]
        assert essential_analysis["total_memory_mb"] == 300  # service_a + service_b
        assert essential_analysis["service_count"] == 2


class TestServiceConfigurationValidator:
    """Test ServiceConfigurationValidator functionality."""
    
    def test_validation_with_valid_config(self):
        """Test validation with a valid configuration."""
        loader = ServiceConfigurationLoader([])
        validator = ServiceConfigurationValidator(loader)
        
        results = validator.validate_all()
        
        # Should have minimal errors with default configuration
        assert isinstance(results["errors"], list)
        assert isinstance(results["warnings"], list)
        assert isinstance(results["recommendations"], list)
    
    def test_validation_with_missing_dependencies(self):
        """Test validation detects missing dependencies."""
        services = {
            "service_a": ServiceConfig(
                name="service_a",
                classification=ServiceClassification.ESSENTIAL,
                dependencies=["nonexistent_service"]
            )
        }
        
        loader = ServiceConfigurationLoader([])
        loader.services = services
        validator = ServiceConfigurationValidator(loader)
        
        results = validator.validate_all()
        
        # Should detect missing dependency
        assert len(results["errors"]) > 0
        error_messages = " ".join(results["errors"])
        assert "nonexistent_service" in error_messages


@pytest.mark.asyncio
class TestClassifiedServiceRegistry:
    """Test ClassifiedServiceRegistry functionality."""
    
    async def test_registry_initialization(self):
        """Test that registry initializes with default configurations."""
        registry = ClassifiedServiceRegistry([])
        
        # Check that classified services are loaded
        assert len(registry.classified_services) > 0
        assert "auth_service" in registry.classified_services
        assert "memory_service" in registry.classified_services
        
        # Check startup order is calculated
        assert len(registry.startup_order) > 0
        assert len(registry.shutdown_order) > 0
    
    async def test_service_registration(self):
        """Test registering a service with classification."""
        registry = ClassifiedServiceRegistry([])
        
        config = ServiceConfig(
            name="test_service",
            classification=ServiceClassification.OPTIONAL,
            startup_priority=100,
            dependencies=[],
            idle_timeout=300
        )
        
        registry.register_classified_service(
            service_name="test_service",
            service_type=MockService,
            config=config
        )
        
        # Check that service is registered
        assert "test_service" in registry.classified_services
        assert "test_service" in registry._services
        
        classified_info = registry.classified_services["test_service"]
        assert classified_info.config.name == "test_service"
        assert classified_info.config.classification == ServiceClassification.OPTIONAL
        assert classified_info.lifecycle_state == ServiceLifecycleState.NOT_LOADED
    
    async def test_deployment_mode_setting(self):
        """Test setting deployment mode affects service enablement."""
        registry = ClassifiedServiceRegistry([])
        
        # Set to minimal mode
        registry.set_deployment_mode(DeploymentMode.MINIMAL)
        
        # Check that only essential services are enabled
        for service_name, classified_info in registry.classified_services.items():
            if classified_info.config.classification == ServiceClassification.ESSENTIAL:
                assert classified_info.config.enabled
            else:
                assert not classified_info.config.enabled
    
    async def test_essential_services_startup(self):
        """Test starting only essential services."""
        registry = ClassifiedServiceRegistry([])
        
        # Register a mock essential service
        config = ServiceConfig(
            name="mock_essential",
            classification=ServiceClassification.ESSENTIAL,
            startup_priority=5,
            dependencies=[]
        )
        
        registry.register_classified_service(
            service_name="mock_essential",
            service_type=MockService,
            config=config
        )
        
        # Start essential services
        results = await registry.start_essential_services()
        
        # Check that essential service was started
        assert "mock_essential" in results
        
        # Check lifecycle state
        classified_info = registry.classified_services["mock_essential"]
        assert classified_info.lifecycle_state == ServiceLifecycleState.ACTIVE
        assert classified_info.last_accessed is not None
    
    async def test_on_demand_loading(self):
        """Test loading services on-demand."""
        registry = ClassifiedServiceRegistry([])
        
        # Register a mock optional service
        config = ServiceConfig(
            name="mock_optional",
            classification=ServiceClassification.OPTIONAL,
            startup_priority=50,
            dependencies=[],
            idle_timeout=300
        )
        
        registry.register_classified_service(
            service_name="mock_optional",
            service_type=MockService,
            config=config
        )
        
        # Load service on-demand
        service_instance = await registry.load_service_on_demand("mock_optional")
        
        # Check that service was loaded
        assert service_instance is not None
        assert isinstance(service_instance, MockService)
        
        # Check lifecycle state
        classified_info = registry.classified_services["mock_optional"]
        assert classified_info.lifecycle_state == ServiceLifecycleState.ACTIVE
        assert classified_info.last_accessed is not None
    
    async def test_service_suspension(self):
        """Test service suspension functionality."""
        registry = ClassifiedServiceRegistry([])
        
        # Register and load a service
        config = ServiceConfig(
            name="suspendable_service",
            classification=ServiceClassification.OPTIONAL,
            startup_priority=50,
            dependencies=[],
            idle_timeout=1  # Very short timeout for testing
        )
        
        registry.register_classified_service(
            service_name="suspendable_service",
            service_type=MockService,
            config=config
        )
        
        # Load the service
        service_instance = await registry.load_service_on_demand("suspendable_service")
        assert service_instance is not None
        
        # Wait for idle timeout and suspend
        await asyncio.sleep(2)  # Wait longer than idle timeout
        suspended_services = await registry.suspend_idle_services()
        
        # Check that service was suspended
        assert "suspendable_service" in suspended_services
        
        classified_info = registry.classified_services["suspendable_service"]
        assert classified_info.lifecycle_state == ServiceLifecycleState.SUSPENDED
        assert classified_info.suspension_count == 1
    
    async def test_classification_report(self):
        """Test getting classification report."""
        registry = ClassifiedServiceRegistry([])
        
        report = registry.get_service_classification_report()
        
        # Check report structure
        assert "deployment_mode" in report
        assert "total_services" in report
        assert "by_classification" in report
        assert "by_lifecycle_state" in report
        assert "performance_metrics" in report
        assert "startup_order" in report
        assert "shutdown_order" in report
        assert "services" in report
        
        # Check that all classifications are represented
        assert "essential" in report["by_classification"]
        assert "optional" in report["by_classification"]
        assert "background" in report["by_classification"]
        
        # Check service details
        for service_name, service_info in report["services"].items():
            assert "classification" in service_info
            assert "lifecycle_state" in service_info
            assert "enabled" in service_info
            assert "resource_requirements" in service_info
    
    async def test_configuration_validation(self):
        """Test configuration validation through registry."""
        registry = ClassifiedServiceRegistry([])
        
        validation_results = registry.validate_configuration()
        
        # Check validation structure
        assert "errors" in validation_results
        assert "warnings" in validation_results
        assert "recommendations" in validation_results
        
        # Results should be lists
        assert isinstance(validation_results["errors"], list)
        assert isinstance(validation_results["warnings"], list)
        assert isinstance(validation_results["recommendations"], list)
    
    async def test_resource_analysis(self):
        """Test resource analysis through registry."""
        registry = ClassifiedServiceRegistry([])
        
        analysis = registry.get_resource_analysis()
        
        # Check analysis structure
        assert "by_classification" in analysis
        assert "total" in analysis
        
        # Check that all classifications are analyzed
        assert "essential" in analysis["by_classification"]
        assert "optional" in analysis["by_classification"]
        assert "background" in analysis["by_classification"]
        
        # Check total resources
        total_resources = analysis["total"]
        assert hasattr(total_resources, 'memory_mb')
        assert hasattr(total_resources, 'cpu_cores')


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])