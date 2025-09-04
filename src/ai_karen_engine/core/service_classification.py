"""
Service Classification and Configuration System for Runtime Performance Optimization.

This module provides service classification, configuration management, and dependency
graph analysis for optimizing system startup and runtime performance.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
import yaml

logger = logging.getLogger(__name__)


class ServiceClassification(str, Enum):
    """Service classification tiers for performance optimization."""
    ESSENTIAL = "essential"      # Core services required for basic functionality
    OPTIONAL = "optional"        # Feature services that can be loaded on-demand
    BACKGROUND = "background"    # Non-critical services that can be suspended


class DeploymentMode(str, Enum):
    """Deployment modes with different service profiles."""
    MINIMAL = "minimal"          # Only essential services
    DEVELOPMENT = "development"  # Essential + debugging services
    PRODUCTION = "production"    # Optimized for performance


@dataclass
class ResourceRequirements:
    """Resource requirements for a service."""
    cpu_cores: Optional[float] = None
    memory_mb: Optional[int] = None
    gpu_memory_mb: Optional[int] = None
    disk_space_mb: Optional[int] = None
    network_bandwidth_mbps: Optional[float] = None


@dataclass
class ServiceConfig:
    """Configuration for a service with classification and dependencies."""
    name: str
    classification: ServiceClassification
    startup_priority: int = 100
    idle_timeout: Optional[int] = None  # seconds
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    gpu_compatible: bool = False
    consolidation_group: Optional[str] = None
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: int = 30  # seconds
    max_restart_attempts: int = 3
    graceful_shutdown_timeout: int = 10  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceConfig':
        """Create from dictionary."""
        # Handle nested ResourceRequirements
        if 'resource_requirements' in data and isinstance(data['resource_requirements'], dict):
            data['resource_requirements'] = ResourceRequirements(**data['resource_requirements'])
        
        # Handle enum conversion
        if 'classification' in data and isinstance(data['classification'], str):
            data['classification'] = ServiceClassification(data['classification'])
        
        return cls(**data)


@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    name: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    classification: ServiceClassification = ServiceClassification.OPTIONAL
    startup_priority: int = 100


class ServiceConfigurationLoader:
    """Loads and manages service configurations from files."""
    
    def __init__(self, config_paths: Optional[List[Union[str, Path]]] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_paths: List of paths to search for configuration files
        """
        self.config_paths = config_paths or [
            Path("config/services.yml"),
            Path("config/services.yaml"),
            Path("config/services.json"),
            Path(".kiro/config/services.yml"),
            Path(".kiro/config/services.yaml"),
            Path(".kiro/config/services.json"),
        ]
        self.services: Dict[str, ServiceConfig] = {}
        self.deployment_profiles: Dict[DeploymentMode, Dict[str, Any]] = {}
        self._load_default_configurations()
    
    def _load_default_configurations(self) -> None:
        """Load default service configurations."""
        # Default essential services
        essential_services = {
            "auth_service": ServiceConfig(
                name="auth_service",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=10,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=64),
            ),
            "config_manager": ServiceConfig(
                name="config_manager",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=5,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=32),
            ),
            "logging_service": ServiceConfig(
                name="logging_service",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=1,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=32),
            ),
            "database_client": ServiceConfig(
                name="database_client",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=20,
                dependencies=["config_manager"],
                resource_requirements=ResourceRequirements(memory_mb=128),
            ),
        }
        
        # Default optional services
        optional_services = {
            "memory_service": ServiceConfig(
                name="memory_service",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=50,
                dependencies=["database_client"],
                resource_requirements=ResourceRequirements(memory_mb=256),
                idle_timeout=300,
            ),
            "conversation_service": ServiceConfig(
                name="conversation_service",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=60,
                dependencies=["memory_service"],
                resource_requirements=ResourceRequirements(memory_mb=128),
                idle_timeout=300,
            ),
            "ai_orchestrator": ServiceConfig(
                name="ai_orchestrator",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=70,
                dependencies=["memory_service"],
                resource_requirements=ResourceRequirements(memory_mb=512, gpu_memory_mb=1024),
                gpu_compatible=True,
                idle_timeout=600,
            ),
            "plugin_service": ServiceConfig(
                name="plugin_service",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=80,
                dependencies=["config_manager"],
                resource_requirements=ResourceRequirements(memory_mb=128),
                idle_timeout=600,
            ),
        }
        
        # Default background services
        background_services = {
            "analytics_service": ServiceConfig(
                name="analytics_service",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=200,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=64),
                idle_timeout=1800,
            ),
            "metrics_collector": ServiceConfig(
                name="metrics_collector",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=210,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=32),
                idle_timeout=3600,
            ),
            "cleanup_service": ServiceConfig(
                name="cleanup_service",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=220,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=32),
                idle_timeout=7200,
            ),
        }
        
        # Combine all default services
        self.services.update(essential_services)
        self.services.update(optional_services)
        self.services.update(background_services)
        
        # Default deployment profiles
        self.deployment_profiles = {
            DeploymentMode.MINIMAL: {
                "enabled_classifications": [ServiceClassification.ESSENTIAL],
                "max_memory_mb": 512,
                "max_services": 10,
                "aggressive_idle_timeout": True,
            },
            DeploymentMode.DEVELOPMENT: {
                "enabled_classifications": [
                    ServiceClassification.ESSENTIAL,
                    ServiceClassification.OPTIONAL
                ],
                "max_memory_mb": 2048,
                "max_services": 50,
                "debug_services": True,
            },
            DeploymentMode.PRODUCTION: {
                "enabled_classifications": [
                    ServiceClassification.ESSENTIAL,
                    ServiceClassification.OPTIONAL,
                    ServiceClassification.BACKGROUND
                ],
                "max_memory_mb": 4096,
                "max_services": 100,
                "performance_optimized": True,
            },
        }
    
    def load_configurations(self) -> Dict[str, ServiceConfig]:
        """Load service configurations from files."""
        for config_path in self.config_paths:
            if isinstance(config_path, str):
                config_path = Path(config_path)
            
            if config_path.exists():
                try:
                    self._load_config_file(config_path)
                    logger.info(f"Loaded service configuration from {config_path}")
                except Exception as e:
                    logger.warning(f"Failed to load configuration from {config_path}: {e}")
        
        return self.services
    
    def _load_config_file(self, config_path: Path) -> None:
        """Load configuration from a specific file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Load services
        if 'services' in data:
            for service_name, service_data in data['services'].items():
                service_data['name'] = service_name
                self.services[service_name] = ServiceConfig.from_dict(service_data)
        
        # Load deployment profiles
        if 'deployment_profiles' in data:
            for mode_name, profile_data in data['deployment_profiles'].items():
                try:
                    mode = DeploymentMode(mode_name)
                    self.deployment_profiles[mode] = profile_data
                except ValueError:
                    logger.warning(f"Unknown deployment mode: {mode_name}")
    
    def save_configuration(self, output_path: Union[str, Path]) -> None:
        """Save current configuration to file."""
        if isinstance(output_path, str):
            output_path = Path(output_path)
        
        # Prepare data for serialization
        data = {
            'services': {
                name: config.to_dict() 
                for name, config in self.services.items()
            },
            'deployment_profiles': {
                mode.value: profile 
                for mode, profile in self.deployment_profiles.items()
            }
        }
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save based on file extension
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved service configuration to {output_path}")
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service."""
        return self.services.get(service_name)
    
    def add_service_config(self, config: ServiceConfig) -> None:
        """Add or update a service configuration."""
        self.services[config.name] = config
        logger.info(f"Added/updated service configuration: {config.name}")
    
    def get_services_by_classification(self, classification: ServiceClassification) -> List[ServiceConfig]:
        """Get all services with a specific classification."""
        return [
            config for config in self.services.values()
            if config.classification == classification and config.enabled
        ]
    
    def get_services_for_deployment_mode(self, mode: DeploymentMode) -> List[ServiceConfig]:
        """Get services that should be enabled for a deployment mode."""
        profile = self.deployment_profiles.get(mode, {})
        enabled_classifications = profile.get('enabled_classifications', [ServiceClassification.ESSENTIAL])
        
        return [
            config for config in self.services.values()
            if config.classification in enabled_classifications and config.enabled
        ]


class DependencyGraphAnalyzer:
    """Analyzes service dependency graphs for validation and optimization."""
    
    def __init__(self, services: Dict[str, ServiceConfig]):
        """
        Initialize the analyzer with service configurations.
        
        Args:
            services: Dictionary of service configurations
        """
        self.services = services
        self.graph: Dict[str, DependencyNode] = {}
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the dependency graph from service configurations."""
        # Create nodes for all services
        for service_name, config in self.services.items():
            self.graph[service_name] = DependencyNode(
                name=service_name,
                classification=config.classification,
                startup_priority=config.startup_priority
            )
        
        # Add dependencies and dependents
        for service_name, config in self.services.items():
            node = self.graph[service_name]
            for dep_name in config.dependencies:
                if dep_name in self.graph:
                    node.dependencies.add(dep_name)
                    self.graph[dep_name].dependents.add(service_name)
                else:
                    logger.warning(f"Service {service_name} depends on unknown service: {dep_name}")
    
    def validate_dependencies(self) -> List[str]:
        """
        Validate the dependency graph for issues.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for circular dependencies
        circular_deps = self.detect_circular_dependencies()
        if circular_deps:
            errors.extend([f"Circular dependency detected: {' -> '.join(cycle)}" for cycle in circular_deps])
        
        # Check for missing dependencies
        for service_name, config in self.services.items():
            for dep_name in config.dependencies:
                if dep_name not in self.services:
                    errors.append(f"Service {service_name} depends on unknown service: {dep_name}")
        
        # Check for essential service dependencies on non-essential services
        for service_name, config in self.services.items():
            if config.classification == ServiceClassification.ESSENTIAL:
                for dep_name in config.dependencies:
                    dep_config = self.services.get(dep_name)
                    if dep_config and dep_config.classification != ServiceClassification.ESSENTIAL:
                        errors.append(
                            f"Essential service {service_name} depends on non-essential service {dep_name}"
                        )
        
        return errors
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.
        
        Returns:
            List of circular dependency cycles
        """
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node_name: str, path: List[str]) -> None:
            if node_name in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_name)
                cycle = path[cycle_start:] + [node_name]
                cycles.append(cycle)
                return
            
            if node_name in visited:
                return
            
            visited.add(node_name)
            rec_stack.add(node_name)
            
            node = self.graph.get(node_name)
            if node:
                for dep_name in node.dependencies:
                    dfs(dep_name, path + [node_name])
            
            rec_stack.remove(node_name)
        
        for service_name in self.graph:
            if service_name not in visited:
                dfs(service_name, [])
        
        return cycles
    
    def get_startup_order(self) -> List[str]:
        """
        Get the optimal startup order based on dependencies and priorities.
        
        Returns:
            List of service names in startup order
        """
        # Topological sort with priority consideration
        in_degree = {name: len(node.dependencies) for name, node in self.graph.items()}
        queue = []
        result = []
        
        # Start with services that have no dependencies, sorted by priority
        for name, node in self.graph.items():
            if in_degree[name] == 0:
                queue.append((node.startup_priority, name))
        
        queue.sort()  # Sort by priority
        
        while queue:
            _, current = queue.pop(0)
            result.append(current)
            
            # Update in-degrees for dependents
            current_node = self.graph[current]
            next_candidates = []
            
            for dependent in current_node.dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    dep_node = self.graph[dependent]
                    next_candidates.append((dep_node.startup_priority, dependent))
            
            # Add new candidates sorted by priority
            next_candidates.sort()
            queue.extend(next_candidates)
            queue.sort()  # Re-sort the entire queue
        
        return result
    
    def get_shutdown_order(self) -> List[str]:
        """
        Get the optimal shutdown order (reverse of startup order).
        
        Returns:
            List of service names in shutdown order
        """
        return list(reversed(self.get_startup_order()))
    
    def get_consolidation_groups(self) -> Dict[str, List[str]]:
        """
        Identify services that can be consolidated based on consolidation_group.
        
        Returns:
            Dictionary mapping group names to lists of service names
        """
        groups = {}
        
        for service_name, config in self.services.items():
            if config.consolidation_group:
                if config.consolidation_group not in groups:
                    groups[config.consolidation_group] = []
                groups[config.consolidation_group].append(service_name)
        
        # Only return groups with multiple services
        return {group: services for group, services in groups.items() if len(services) > 1}
    
    def analyze_resource_requirements(self) -> Dict[str, Any]:
        """
        Analyze total resource requirements by classification.
        
        Returns:
            Dictionary with resource analysis
        """
        analysis = {
            "by_classification": {},
            "total": ResourceRequirements(),
            "consolidation_savings": {}
        }
        
        # Analyze by classification
        for classification in ServiceClassification:
            services = [
                config for config in self.services.values()
                if config.classification == classification and config.enabled
            ]
            
            total_memory = sum(
                (config.resource_requirements.memory_mb or 0) for config in services
            )
            total_cpu = sum(
                (config.resource_requirements.cpu_cores or 0) for config in services
            )
            total_gpu_memory = sum(
                (config.resource_requirements.gpu_memory_mb or 0) for config in services
            )
            
            analysis["by_classification"][classification.value] = {
                "service_count": len(services),
                "total_memory_mb": total_memory,
                "total_cpu_cores": total_cpu,
                "total_gpu_memory_mb": total_gpu_memory,
                "services": [config.name for config in services]
            }
        
        # Calculate totals
        all_enabled_services = [config for config in self.services.values() if config.enabled]
        analysis["total"] = ResourceRequirements(
            memory_mb=sum((config.resource_requirements.memory_mb or 0) for config in all_enabled_services),
            cpu_cores=sum((config.resource_requirements.cpu_cores or 0) for config in all_enabled_services),
            gpu_memory_mb=sum((config.resource_requirements.gpu_memory_mb or 0) for config in all_enabled_services),
        )
        
        # Analyze consolidation opportunities
        consolidation_groups = self.get_consolidation_groups()
        for group_name, service_names in consolidation_groups.items():
            group_services = [self.services[name] for name in service_names]
            current_memory = sum((config.resource_requirements.memory_mb or 0) for config in group_services)
            # Estimate 20% memory savings from consolidation
            estimated_savings = int(current_memory * 0.2)
            
            analysis["consolidation_savings"][group_name] = {
                "services": service_names,
                "current_memory_mb": current_memory,
                "estimated_savings_mb": estimated_savings,
                "estimated_final_memory_mb": current_memory - estimated_savings
            }
        
        return analysis


class ServiceConfigurationValidator:
    """Validates service configurations for correctness and best practices."""
    
    def __init__(self, loader: ServiceConfigurationLoader):
        """
        Initialize the validator.
        
        Args:
            loader: Service configuration loader
        """
        self.loader = loader
        self.analyzer = DependencyGraphAnalyzer(loader.services)
    
    def validate_all(self) -> Dict[str, List[str]]:
        """
        Perform comprehensive validation of all configurations.
        
        Returns:
            Dictionary with validation results by category
        """
        results = {
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Dependency validation
        dependency_errors = self.analyzer.validate_dependencies()
        results["errors"].extend(dependency_errors)
        
        # Essential service validation
        essential_warnings = self._validate_essential_services()
        results["warnings"].extend(essential_warnings)
        
        # Resource validation
        resource_warnings = self._validate_resource_requirements()
        results["warnings"].extend(resource_warnings)
        
        # Best practice recommendations
        recommendations = self._generate_recommendations()
        results["recommendations"].extend(recommendations)
        
        return results
    
    def _validate_essential_services(self) -> List[str]:
        """Validate that essential services are properly configured."""
        warnings = []
        essential_services = self.loader.get_services_by_classification(ServiceClassification.ESSENTIAL)
        
        # Check for minimum essential services
        required_essential = {"auth_service", "config_manager", "logging_service"}
        existing_essential = {service.name for service in essential_services}
        
        missing_essential = required_essential - existing_essential
        if missing_essential:
            warnings.append(f"Missing recommended essential services: {', '.join(missing_essential)}")
        
        # Check essential service priorities
        for service in essential_services:
            if service.startup_priority > 50:
                warnings.append(f"Essential service {service.name} has low startup priority ({service.startup_priority})")
        
        return warnings
    
    def _validate_resource_requirements(self) -> List[str]:
        """Validate resource requirements are reasonable."""
        warnings = []
        
        for service_name, config in self.loader.services.items():
            req = config.resource_requirements
            
            # Check for excessive memory requirements
            if req.memory_mb and req.memory_mb > 1024:
                warnings.append(f"Service {service_name} has high memory requirement: {req.memory_mb}MB")
            
            # Check for GPU requirements on non-GPU compatible services
            if req.gpu_memory_mb and not config.gpu_compatible:
                warnings.append(f"Service {service_name} has GPU memory requirement but is not GPU compatible")
        
        return warnings
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Analyze consolidation opportunities
        consolidation_groups = self.analyzer.get_consolidation_groups()
        if consolidation_groups:
            for group_name, services in consolidation_groups.items():
                recommendations.append(
                    f"Consider consolidating services in group '{group_name}': {', '.join(services)}"
                )
        
        # Check for services without idle timeouts
        optional_services = self.loader.get_services_by_classification(ServiceClassification.OPTIONAL)
        for service in optional_services:
            if service.idle_timeout is None:
                recommendations.append(f"Consider adding idle timeout to optional service: {service.name}")
        
        # Check for background services with high priority
        background_services = self.loader.get_services_by_classification(ServiceClassification.BACKGROUND)
        for service in background_services:
            if service.startup_priority < 100:
                recommendations.append(f"Background service {service.name} has high startup priority")
        
        return recommendations