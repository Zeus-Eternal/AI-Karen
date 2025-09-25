"""
Core tests for the Service Classification System.

This module tests the core service classification functionality without
dependencies on the complex service registry to avoid circular imports.
"""

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


def test_configuration_file_loading():
    """Test loading the actual configuration file."""
    config_path = Path("config/services.yml")
    
    if config_path.exists():
        loader = ServiceConfigurationLoader([str(config_path)])
        loader.load_configurations()
        
        # Check that services were loaded from file
        assert len(loader.services) > 0
        
        # Check that we have services in all classifications
        essential_count = len(loader.get_services_by_classification(ServiceClassification.ESSENTIAL))
        optional_count = len(loader.get_services_by_classification(ServiceClassification.OPTIONAL))
        background_count = len(loader.get_services_by_classification(ServiceClassification.BACKGROUND))
        
        assert essential_count > 0
        assert optional_count > 0
        assert background_count > 0
        
        print(f"Loaded {len(loader.services)} services:")
        print(f"  Essential: {essential_count}")
        print(f"  Optional: {optional_count}")
        print(f"  Background: {background_count}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])