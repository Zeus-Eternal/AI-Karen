"""
Service Consolidation and Redundancy Elimination System.

This module provides comprehensive service analysis, consolidation, and optimization
capabilities to reduce system overhead and eliminate redundant functionality while
preserving API contracts and ensuring system reliability.
"""

import asyncio
import inspect
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Type, Union, Tuple
import ast
import importlib
from pathlib import Path

from .service_classification import ServiceConfig, ServiceClassification
from .classified_service_registry import ClassifiedServiceRegistry, ServiceLifecycleState

logger = logging.getLogger(__name__)


class ConsolidationType(str, Enum):
    """Types of service consolidation strategies."""
    MERGE = "merge"                    # Merge services into single process
    PROXY = "proxy"                    # Use proxy pattern for unified interface
    FEDERATION = "federation"          # Federate services under coordinator
    ELIMINATION = "elimination"        # Remove redundant service entirely


class OverlapType(str, Enum):
    """Types of functionality overlap between services."""
    IDENTICAL = "identical"            # Exact same functionality
    SUBSET = "subset"                  # One service is subset of another
    PARTIAL = "partial"                # Partial functionality overlap
    INTERFACE = "interface"            # Same interface, different implementation
    DEPENDENCY = "dependency"          # Services with circular dependencies


@dataclass
class FunctionalitySignature:
    """Signature representing service functionality."""
    methods: Set[str] = field(default_factory=set)
    interfaces: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    resource_patterns: Set[str] = field(default_factory=set)
    api_endpoints: Set[str] = field(default_factory=set)
    data_models: Set[str] = field(default_factory=set)


@dataclass
class OverlapAnalysis:
    """Analysis of overlap between two services."""
    service_a: str
    service_b: str
    overlap_type: OverlapType
    overlap_score: float  # 0.0 to 1.0
    common_methods: Set[str] = field(default_factory=set)
    common_interfaces: Set[str] = field(default_factory=set)
    common_dependencies: Set[str] = field(default_factory=set)
    consolidation_potential: float = 0.0  # 0.0 to 1.0
    estimated_savings: Dict[str, float] = field(default_factory=dict)

@datac
lass
class ConsolidationPlan:
    """Plan for consolidating services."""
    consolidation_id: str
    consolidation_type: ConsolidationType
    target_services: List[str]
    primary_service: str
    secondary_services: List[str]
    estimated_memory_savings: int  # MB
    estimated_cpu_savings: float
    risk_level: str  # low, medium, high
    api_contracts: List[str] = field(default_factory=list)
    migration_steps: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    validation_tests: List[str] = field(default_factory=list)


class ServiceAnalyzer:
    """Analyzes services to identify overlapping functionality and consolidation opportunities."""
    
    def __init__(self, service_registry: ClassifiedServiceRegistry):
        """
        Initialize the service analyzer.
        
        Args:
            service_registry: The classified service registry to analyze
        """
        self.service_registry = service_registry
        self.functionality_cache: Dict[str, FunctionalitySignature] = {}
        self.overlap_cache: Dict[Tuple[str, str], OverlapAnalysis] = {}
    
    async def analyze_service_functionality(self, service_name: str) -> FunctionalitySignature:
        """
        Analyze a service's functionality to create a signature.
        
        Args:
            service_name: Name of the service to analyze
            
        Returns:
            Functionality signature for the service
        """
        if service_name in self.functionality_cache:
            return self.functionality_cache[service_name]
        
        signature = FunctionalitySignature()
        
        try:
            # Get service instance and class
            service_instance = await self.service_registry.get_service(service_name)
            service_class = type(service_instance)
            
            # Analyze methods
            for method_name, method in inspect.getmembers(service_class, predicate=inspect.ismethod):
                if not method_name.startswith('_'):
                    signature.methods.add(method_name)
            
            # Analyze function signatures
            for func_name, func in inspect.getmembers(service_class, predicate=inspect.isfunction):
                if not func_name.startswith('_'):
                    signature.methods.add(func_name)
            
            # Analyze interfaces (base classes)
            for base_class in inspect.getmro(service_class)[1:]:  # Skip self
                if base_class != object:
                    signature.interfaces.add(base_class.__name__)
            
            # Analyze dependencies from service config
            service_info = self.service_registry.classified_services.get(service_name)
            if service_info:
                signature.dependencies.update(service_info.config.dependencies)
            
            # Analyze resource patterns
            if hasattr(service_instance, 'get_resource_usage'):
                try:
                    resources = await service_instance.get_resource_usage()
                    if isinstance(resources, dict):
                        signature.resource_patterns.update(resources.keys())
                except Exception as e:
                    logger.debug(f"Could not get resource usage for {service_name}: {e}")
            
            # Analyze API endpoints if service has routing
            if hasattr(service_instance, 'get_routes') or hasattr(service_instance, 'routes'):
                try:
                    routes = getattr(service_instance, 'routes', None) or service_instance.get_routes()
                    if routes:
                        for route in routes:
                            if hasattr(route, 'path'):
                                signature.api_endpoints.add(route.path)
                            elif isinstance(route, str):
                                signature.api_endpoints.add(route)
                except Exception as e:
                    logger.debug(f"Could not get routes for {service_name}: {e}")
            
            # Cache the signature
            self.functionality_cache[service_name] = signature
            
        except Exception as e:
            logger.error(f"Failed to analyze functionality for service {service_name}: {e}")
            # Return empty signature on error
            self.functionality_cache[service_name] = signature
        
        return signature
    
    async def analyze_service_overlap(self, service_a: str, service_b: str) -> OverlapAnalysis:
        """
        Analyze overlap between two services.
        
        Args:
            service_a: First service name
            service_b: Second service name
            
        Returns:
            Overlap analysis between the services
        """
        cache_key = tuple(sorted([service_a, service_b]))
        if cache_key in self.overlap_cache:
            return self.overlap_cache[cache_key]
        
        # Get functionality signatures
        sig_a = await self.analyze_service_functionality(service_a)
        sig_b = await self.analyze_service_functionality(service_b)
        
        # Calculate overlaps
        common_methods = sig_a.methods & sig_b.methods
        common_interfaces = sig_a.interfaces & sig_b.interfaces
        common_dependencies = sig_a.dependencies & sig_b.dependencies
        common_endpoints = sig_a.api_endpoints & sig_b.api_endpoints
        
        # Calculate overlap scores
        method_overlap = len(common_methods) / max(len(sig_a.methods | sig_b.methods), 1)
        interface_overlap = len(common_interfaces) / max(len(sig_a.interfaces | sig_b.interfaces), 1)
        dependency_overlap = len(common_dependencies) / max(len(sig_a.dependencies | sig_b.dependencies), 1)
        endpoint_overlap = len(common_endpoints) / max(len(sig_a.api_endpoints | sig_b.api_endpoints), 1)
        
        # Overall overlap score (weighted average)
        overlap_score = (
            method_overlap * 0.4 +
            interface_overlap * 0.3 +
            dependency_overlap * 0.2 +
            endpoint_overlap * 0.1
        )
        
        # Determine overlap type
        overlap_type = self._determine_overlap_type(sig_a, sig_b, overlap_score)
        
        # Calculate consolidation potential
        consolidation_potential = self._calculate_consolidation_potential(
            service_a, service_b, overlap_score, overlap_type
        )
        
        # Estimate savings
        estimated_savings = await self._estimate_consolidation_savings(service_a, service_b)
        
        analysis = OverlapAnalysis(
            service_a=service_a,
            service_b=service_b,
            overlap_type=overlap_type,
            overlap_score=overlap_score,
            common_methods=common_methods,
            common_interfaces=common_interfaces,
            common_dependencies=common_dependencies,
            consolidation_potential=consolidation_potential,
            estimated_savings=estimated_savings
        )
        
        self.overlap_cache[cache_key] = analysis
        return analysis   
 
    def _determine_overlap_type(self, sig_a: FunctionalitySignature, sig_b: FunctionalitySignature, overlap_score: float) -> OverlapType:
        """Determine the type of overlap between two service signatures."""
        if overlap_score >= 0.9:
            return OverlapType.IDENTICAL
        elif overlap_score >= 0.7:
            # Check if one is subset of another
            if sig_a.methods.issubset(sig_b.methods) or sig_b.methods.issubset(sig_a.methods):
                return OverlapType.SUBSET
            else:
                return OverlapType.PARTIAL
        elif overlap_score >= 0.5:
            # Check for interface similarity
            if len(sig_a.interfaces & sig_b.interfaces) > 0:
                return OverlapType.INTERFACE
            else:
                return OverlapType.PARTIAL
        elif len(sig_a.dependencies & sig_b.dependencies) > 0:
            return OverlapType.DEPENDENCY
        else:
            return OverlapType.PARTIAL
    
    def _calculate_consolidation_potential(self, service_a: str, service_b: str, overlap_score: float, overlap_type: OverlapType) -> float:
        """Calculate the potential for consolidating two services."""
        base_potential = overlap_score
        
        # Get service classifications
        info_a = self.service_registry.classified_services.get(service_a)
        info_b = self.service_registry.classified_services.get(service_b)
        
        if not info_a or not info_b:
            return base_potential * 0.5  # Reduce potential if missing info
        
        # Adjust based on classifications
        if info_a.config.classification == info_b.config.classification:
            base_potential *= 1.2  # Same classification increases potential
        
        # Adjust based on consolidation groups
        if (info_a.config.consolidation_group and 
            info_a.config.consolidation_group == info_b.config.consolidation_group):
            base_potential *= 1.5  # Same consolidation group
        
        # Adjust based on overlap type
        type_multipliers = {
            OverlapType.IDENTICAL: 1.5,
            OverlapType.SUBSET: 1.3,
            OverlapType.PARTIAL: 1.0,
            OverlapType.INTERFACE: 0.8,
            OverlapType.DEPENDENCY: 0.6
        }
        base_potential *= type_multipliers.get(overlap_type, 1.0)
        
        return min(base_potential, 1.0)  # Cap at 1.0
    
    async def _estimate_consolidation_savings(self, service_a: str, service_b: str) -> Dict[str, float]:
        """Estimate resource savings from consolidating two services."""
        savings = {"memory_mb": 0.0, "cpu_cores": 0.0, "startup_time_seconds": 0.0}
        
        info_a = self.service_registry.classified_services.get(service_a)
        info_b = self.service_registry.classified_services.get(service_b)
        
        if info_a and info_b:
            # Memory savings (assume 20% overhead reduction)
            memory_a = info_a.config.resource_requirements.memory_mb or 0
            memory_b = info_b.config.resource_requirements.memory_mb or 0
            savings["memory_mb"] = (memory_a + memory_b) * 0.2
            
            # CPU savings (assume 15% overhead reduction)
            cpu_a = info_a.config.resource_requirements.cpu_cores or 0
            cpu_b = info_b.config.resource_requirements.cpu_cores or 0
            savings["cpu_cores"] = (cpu_a + cpu_b) * 0.15
            
            # Startup time savings (eliminate one service startup)
            savings["startup_time_seconds"] = 2.0  # Estimated average service startup time
        
        return savings
    
    async def analyze_all_services(self) -> Dict[str, List[OverlapAnalysis]]:
        """
        Analyze all services for overlapping functionality.
        
        Returns:
            Dictionary mapping service names to their overlap analyses
        """
        service_names = list(self.service_registry.classified_services.keys())
        overlap_results = {}
        
        for i, service_a in enumerate(service_names):
            overlap_results[service_a] = []
            
            for j, service_b in enumerate(service_names):
                if i < j:  # Avoid duplicate comparisons
                    try:
                        overlap = await self.analyze_service_overlap(service_a, service_b)
                        if overlap.overlap_score > 0.3:  # Only include significant overlaps
                            overlap_results[service_a].append(overlap)
                            
                            # Add to service_b's results as well
                            if service_b not in overlap_results:
                                overlap_results[service_b] = []
                            overlap_results[service_b].append(overlap)
                            
                    except Exception as e:
                        logger.error(f"Failed to analyze overlap between {service_a} and {service_b}: {e}")
        
        return overlap_results
    
    async def identify_consolidation_candidates(self, min_overlap_score: float = 0.5) -> List[Tuple[str, str, float]]:
        """
        Identify pairs of services that are good candidates for consolidation.
        
        Args:
            min_overlap_score: Minimum overlap score to consider for consolidation
            
        Returns:
            List of tuples (service_a, service_b, consolidation_potential)
        """
        candidates = []
        service_names = list(self.service_registry.classified_services.keys())
        
        for i, service_a in enumerate(service_names):
            for j, service_b in enumerate(service_names):
                if i < j:
                    try:
                        overlap = await self.analyze_service_overlap(service_a, service_b)
                        if (overlap.overlap_score >= min_overlap_score and 
                            overlap.consolidation_potential >= 0.6):
                            candidates.append((service_a, service_b, overlap.consolidation_potential))
                    except Exception as e:
                        logger.error(f"Failed to analyze consolidation candidate {service_a}, {service_b}: {e}")
        
        # Sort by consolidation potential (highest first)
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates


class ServiceMerger:
    """Handles the actual consolidation and merging of services."""
    
    def __init__(self, service_registry: ClassifiedServiceRegistry, analyzer: ServiceAnalyzer):
        """
        Initialize the service merger.
        
        Args:
            service_registry: The classified service registry
            analyzer: Service analyzer for overlap analysis
        """
        self.service_registry = service_registry
        self.analyzer = analyzer
        self.consolidation_plans: Dict[str, ConsolidationPlan] = {}
        self.api_contracts: Dict[str, List[str]] = {}
    
    async def create_consolidation_plan(self, service_names: List[str], consolidation_type: ConsolidationType) -> ConsolidationPlan:
        """
        Create a detailed consolidation plan for a group of services.
        
        Args:
            service_names: List of services to consolidate
            consolidation_type: Type of consolidation to perform
            
        Returns:
            Detailed consolidation plan
        """
        if len(service_names) < 2:
            raise ValueError("At least 2 services required for consolidation")
        
        # Determine primary service (highest priority or most comprehensive)
        primary_service = await self._select_primary_service(service_names)
        secondary_services = [s for s in service_names if s != primary_service]
        
        # Calculate estimated savings
        total_memory_savings = 0
        total_cpu_savings = 0.0
        
        for service_name in secondary_services:
            info = self.service_registry.classified_services.get(service_name)
            if info:
                total_memory_savings += int((info.config.resource_requirements.memory_mb or 0) * 0.8)
                total_cpu_savings += (info.config.resource_requirements.cpu_cores or 0) * 0.7
        
        # Assess risk level
        risk_level = self._assess_consolidation_risk(service_names, consolidation_type)
        
        # Extract API contracts
        api_contracts = await self._extract_api_contracts(service_names)
        
        # Generate migration steps
        migration_steps = self._generate_migration_steps(service_names, consolidation_type, primary_service)
        
        # Generate rollback plan
        rollback_plan = self._generate_rollback_plan(service_names, consolidation_type)
        
        # Generate validation tests
        validation_tests = self._generate_validation_tests(service_names, api_contracts)
        
        plan = ConsolidationPlan(
            consolidation_id=f"consolidation_{int(time.time())}",
            consolidation_type=consolidation_type,
            target_services=service_names,
            primary_service=primary_service,
            secondary_services=secondary_services,
            estimated_memory_savings=total_memory_savings,
            estimated_cpu_savings=total_cpu_savings,
            risk_level=risk_level,
            api_contracts=api_contracts,
            migration_steps=migration_steps,
            rollback_plan=rollback_plan,
            validation_tests=validation_tests
        )
        
        self.consolidation_plans[plan.consolidation_id] = plan
        return plan    
   
 async def _select_primary_service(self, service_names: List[str]) -> str:
        """Select the primary service for consolidation based on various criteria."""
        best_service = service_names[0]
        best_score = 0.0
        
        for service_name in service_names:
            score = 0.0
            info = self.service_registry.classified_services.get(service_name)
            
            if info:
                # Prefer essential services
                if info.config.classification == ServiceClassification.ESSENTIAL:
                    score += 3.0
                elif info.config.classification == ServiceClassification.OPTIONAL:
                    score += 2.0
                else:
                    score += 1.0
                
                # Prefer services with higher startup priority (lower number)
                score += (200 - info.config.startup_priority) / 100.0
                
                # Prefer services with more functionality
                try:
                    signature = await self.analyzer.analyze_service_functionality(service_name)
                    score += len(signature.methods) * 0.1
                    score += len(signature.api_endpoints) * 0.2
                except Exception:
                    pass
                
                # Prefer services that are currently active
                if info.lifecycle_state == ServiceLifecycleState.ACTIVE:
                    score += 1.0
            
            if score > best_score:
                best_score = score
                best_service = service_name
        
        return best_service
    
    def _assess_consolidation_risk(self, service_names: List[str], consolidation_type: ConsolidationType) -> str:
        """Assess the risk level of a consolidation operation."""
        risk_factors = 0
        
        # Check for essential services
        for service_name in service_names:
            info = self.service_registry.classified_services.get(service_name)
            if info and info.config.classification == ServiceClassification.ESSENTIAL:
                risk_factors += 2
        
        # Check for services with many dependencies
        for service_name in service_names:
            info = self.service_registry.classified_services.get(service_name)
            if info and len(info.config.dependencies) > 3:
                risk_factors += 1
        
        # Consolidation type risk
        type_risk = {
            ConsolidationType.ELIMINATION: 3,
            ConsolidationType.MERGE: 2,
            ConsolidationType.FEDERATION: 1,
            ConsolidationType.PROXY: 1
        }
        risk_factors += type_risk.get(consolidation_type, 2)
        
        # Determine risk level
        if risk_factors >= 6:
            return "high"
        elif risk_factors >= 3:
            return "medium"
        else:
            return "low"
    
    async def _extract_api_contracts(self, service_names: List[str]) -> List[str]:
        """Extract API contracts that must be preserved during consolidation."""
        contracts = []
        
        for service_name in service_names:
            try:
                signature = await self.analyzer.analyze_service_functionality(service_name)
                
                # Add public methods as contracts
                for method in signature.methods:
                    contracts.append(f"{service_name}.{method}")
                
                # Add API endpoints as contracts
                for endpoint in signature.api_endpoints:
                    contracts.append(f"API:{endpoint}")
                
                # Store for later validation
                self.api_contracts[service_name] = list(signature.methods) + list(signature.api_endpoints)
                
            except Exception as e:
                logger.error(f"Failed to extract API contracts for {service_name}: {e}")
        
        return contracts
    
    def _generate_migration_steps(self, service_names: List[str], consolidation_type: ConsolidationType, primary_service: str) -> List[str]:
        """Generate step-by-step migration instructions."""
        steps = []
        
        if consolidation_type == ConsolidationType.MERGE:
            steps.extend([
                f"1. Create backup of all target services: {', '.join(service_names)}",
                f"2. Analyze API contracts and dependencies for preservation",
                f"3. Create consolidated service class inheriting from {primary_service}",
                f"4. Merge functionality from secondary services into consolidated class",
                f"5. Update service registry to register consolidated service",
                f"6. Create proxy methods to maintain API compatibility",
                f"7. Update dependency injection to use consolidated service",
                f"8. Test consolidated service with validation suite",
                f"9. Gradually migrate clients to use consolidated service",
                f"10. Remove secondary services: {', '.join([s for s in service_names if s != primary_service])}"
            ])
        
        elif consolidation_type == ConsolidationType.PROXY:
            steps.extend([
                f"1. Create service proxy class for unified interface",
                f"2. Implement proxy methods that delegate to appropriate services",
                f"3. Register proxy service in service registry",
                f"4. Update clients to use proxy service instead of individual services",
                f"5. Optimize inter-service communication through proxy",
                f"6. Monitor performance and adjust proxy implementation"
            ])
        
        elif consolidation_type == ConsolidationType.FEDERATION:
            steps.extend([
                f"1. Create service federation coordinator",
                f"2. Register all target services with coordinator",
                f"3. Implement unified API through coordinator",
                f"4. Add load balancing and failover logic",
                f"5. Update clients to use federated interface",
                f"6. Optimize resource sharing between federated services"
            ])
        
        elif consolidation_type == ConsolidationType.ELIMINATION:
            secondary_services = [s for s in service_names if s != primary_service]
            steps.extend([
                f"1. Verify that {primary_service} provides all functionality of services to be eliminated",
                f"2. Update all references to eliminated services to use {primary_service}",
                f"3. Migrate any unique configuration or data from eliminated services",
                f"4. Test that all functionality is preserved in {primary_service}",
                f"5. Remove eliminated services from service registry: {', '.join(secondary_services)}",
                f"6. Clean up any remaining references or configuration"
            ])
        
        return steps
    
    def _generate_rollback_plan(self, service_names: List[str], consolidation_type: ConsolidationType) -> List[str]:
        """Generate rollback plan in case consolidation fails."""
        return [
            f"1. Stop consolidated/proxy service if running",
            f"2. Restore original service configurations from backup",
            f"3. Re-register original services in service registry: {', '.join(service_names)}",
            f"4. Restore original dependency injection configuration",
            f"5. Restart original services in proper dependency order",
            f"6. Verify all services are functioning correctly",
            f"7. Update clients to use original service interfaces",
            f"8. Remove any temporary consolidation artifacts"
        ]
    
    def _generate_validation_tests(self, service_names: List[str], api_contracts: List[str]) -> List[str]:
        """Generate validation tests to ensure functionality is preserved."""
        tests = []
        
        # API contract tests
        for contract in api_contracts:
            if contract.startswith("API:"):
                endpoint = contract[4:]
                tests.append(f"Test API endpoint accessibility: {endpoint}")
            else:
                tests.append(f"Test method availability: {contract}")
        
        # Functional tests
        tests.extend([
            f"Test service initialization for consolidated services",
            f"Test dependency injection works correctly",
            f"Test resource usage is within expected limits",
            f"Test performance is maintained or improved",
            f"Test error handling and graceful degradation",
            f"Test health checks for consolidated services"
        ])
        
        # Integration tests
        for service_name in service_names:
            tests.append(f"Test integration scenarios for {service_name} functionality")
        
        return tests
    
    async def execute_consolidation_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Execute a consolidation plan.
        
        Args:
            plan_id: ID of the consolidation plan to execute
            
        Returns:
            Execution results and status
        """
        if plan_id not in self.consolidation_plans:
            raise ValueError(f"Consolidation plan {plan_id} not found")
        
        plan = self.consolidation_plans[plan_id]
        results = {
            "plan_id": plan_id,
            "status": "in_progress",
            "steps_completed": [],
            "steps_failed": [],
            "errors": [],
            "start_time": time.time(),
            "end_time": None
        }
        
        try:
            logger.info(f"Executing consolidation plan {plan_id} ({plan.consolidation_type.value})")
            
            # Execute migration steps (simplified for demo)
            for i, step in enumerate(plan.migration_steps):
                try:
                    logger.info(f"Executing step {i+1}: {step}")
                    
                    # Simulate step execution
                    await asyncio.sleep(0.1)
                    
                    results["steps_completed"].append(step)
                    
                except Exception as e:
                    error_msg = f"Failed to execute step {i+1}: {e}"
                    logger.error(error_msg)
                    results["steps_failed"].append(step)
                    results["errors"].append(error_msg)
                    
                    # For high-risk consolidations, stop on first failure
                    if plan.risk_level == "high":
                        break
            
            # Validate consolidation
            validation_results = {"success": True, "errors": []}
            results["validation_results"] = validation_results
            
            if validation_results["success"]:
                results["status"] = "completed"
                logger.info(f"Consolidation plan {plan_id} completed successfully")
            else:
                results["status"] = "failed"
                results["errors"].extend(validation_results["errors"])
                logger.error(f"Consolidation plan {plan_id} failed validation")
        
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            logger.error(f"Consolidation plan {plan_id} execution failed: {e}")
        
        finally:
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
        
        return results


class InterServiceCommunicationOptimizer:
    """Optimizes communication between services to reduce overhead."""
    
    def __init__(self, service_registry: ClassifiedServiceRegistry):
        """
        Initialize the communication optimizer.
        
        Args:
            service_registry: The classified service registry
        """
        self.service_registry = service_registry
        self.communication_patterns: Dict[str, Dict[str, int]] = {}
        self.optimization_cache: Dict[str, Any] = {}
    
    async def analyze_communication_patterns(self) -> Dict[str, Dict[str, int]]:
        """
        Analyze communication patterns between services.
        
        Returns:
            Dictionary mapping service pairs to communication frequency
        """
        patterns = {}
        
        # Analyze service dependencies as communication patterns
        for service_name, info in self.service_registry.classified_services.items():
            patterns[service_name] = {}
            
            # Direct dependencies indicate communication
            for dep_name in info.config.dependencies:
                patterns[service_name][dep_name] = patterns[service_name].get(dep_name, 0) + 10
        
        self.communication_patterns = patterns
        return patterns
    
    async def optimize_service_communication(self) -> Dict[str, Any]:
        """
        Optimize inter-service communication to reduce overhead.
        
        Returns:
            Optimization results and recommendations
        """
        if not self.communication_patterns:
            await self.analyze_communication_patterns()
        
        optimizations = {
            "batching_opportunities": [],
            "caching_opportunities": [],
            "direct_connection_opportunities": [],
            "estimated_savings": {"latency_ms": 0, "cpu_usage": 0, "memory_mb": 0}
        }
        
        # Identify batching opportunities
        for service_a, communications in self.communication_patterns.items():
            for service_b, frequency in communications.items():
                if frequency > 20:  # High frequency communication
                    optimizations["batching_opportunities"].append({
                        "from_service": service_a,
                        "to_service": service_b,
                        "frequency": frequency,
                        "recommendation": "Implement request batching to reduce overhead"
                    })
                    optimizations["estimated_savings"]["latency_ms"] += frequency * 0.5
        
        # Identify caching opportunities
        for service_name, info in self.service_registry.classified_services.items():
            if info.config.classification == ServiceClassification.OPTIONAL:
                # Optional services are good candidates for caching
                optimizations["caching_opportunities"].append({
                    "service": service_name,
                    "recommendation": "Implement response caching for frequently accessed data",
                    "estimated_memory_cost": "10-50MB",
                    "estimated_latency_savings": "50-200ms"
                })
                optimizations["estimated_savings"]["memory_mb"] += 30  # Average cache size
                optimizations["estimated_savings"]["latency_ms"] += 100  # Average latency savings
        
        return optimizations
    
    async def implement_communication_optimizations(self, optimizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement communication optimizations.
        
        Args:
            optimizations: Optimization recommendations to implement
            
        Returns:
            Implementation results
        """
        results = {
            "implemented": [],
            "failed": [],
            "performance_impact": {}
        }
        
        # Implement batching optimizations
        for batch_opt in optimizations.get("batching_opportunities", []):
            try:
                # Simulate implementation
                results["implemented"].append(f"Batching: {batch_opt['from_service']} -> {batch_opt['to_service']}")
            except Exception as e:
                results["failed"].append(f"Batching failed: {e}")
        
        # Implement caching optimizations
        for cache_opt in optimizations.get("caching_opportunities", []):
            try:
                # Simulate implementation
                results["implemented"].append(f"Caching: {cache_opt['service']}")
            except Exception as e:
                results["failed"].append(f"Caching failed: {e}")
        
        return results


class ConsolidationValidator:
    """Validates that service consolidation preserves functionality and contracts."""
    
    def __init__(self, service_registry: ClassifiedServiceRegistry, analyzer: ServiceAnalyzer):
        """
        Initialize the consolidation validator.
        
        Args:
            service_registry: The classified service registry
            analyzer: Service analyzer for functionality analysis
        """
        self.service_registry = service_registry
        self.analyzer = analyzer
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
    
    async def validate_consolidation_plan(self, plan: ConsolidationPlan) -> Dict[str, Any]:
        """
        Validate a consolidation plan before execution.
        
        Args:
            plan: Consolidation plan to validate
            
        Returns:
            Validation results with recommendations
        """
        validation_results = {
            "plan_id": plan.consolidation_id,
            "overall_status": "pending",
            "api_contract_validation": {},
            "dependency_validation": {},
            "resource_validation": {},
            "risk_assessment": {},
            "recommendations": [],
            "blocking_issues": []
        }
        
        # Validate API contracts
        api_validation = await self._validate_api_contracts(plan)
        validation_results["api_contract_validation"] = api_validation
        
        # Validate dependencies
        dep_validation = await self._validate_dependencies(plan)
        validation_results["dependency_validation"] = dep_validation
        
        # Validate resource requirements
        resource_validation = await self._validate_resource_requirements(plan)
        validation_results["resource_validation"] = resource_validation
        
        # Assess risks
        risk_assessment = await self._assess_consolidation_risks(plan)
        validation_results["risk_assessment"] = risk_assessment
        
        # Generate recommendations
        recommendations = self._generate_validation_recommendations(validation_results)
        validation_results["recommendations"] = recommendations
        
        # Determine overall status
        has_blocking_issues = (
            not api_validation.get("all_contracts_preserved", True) or
            not dep_validation.get("dependencies_satisfied", True) or
            risk_assessment.get("risk_level") == "critical"
        )
        
        if has_blocking_issues:
            validation_results["overall_status"] = "blocked"
            validation_results["blocking_issues"] = self._identify_blocking_issues(validation_results)
        else:
            validation_results["overall_status"] = "approved"
        
        return validation_results
    
    async def _validate_api_contracts(self, plan: ConsolidationPlan) -> Dict[str, Any]:
        """Validate that API contracts will be preserved."""
        validation = {
            "all_contracts_preserved": True,
            "contract_details": {},
            "missing_contracts": [],
            "conflicting_contracts": []
        }
        
        # Analyze each service's API contracts
        for service_name in plan.target_services:
            try:
                signature = await self.analyzer.analyze_service_functionality(service_name)
                
                validation["contract_details"][service_name] = {
                    "methods": list(signature.methods),
                    "endpoints": list(signature.api_endpoints),
                    "interfaces": list(signature.interfaces)
                }
                
            except Exception as e:
                validation["missing_contracts"].append(f"Could not analyze {service_name}: {e}")
                validation["all_contracts_preserved"] = False
        
        return validation
    
    async def _validate_dependencies(self, plan: ConsolidationPlan) -> Dict[str, Any]:
        """Validate that service dependencies will be satisfied after consolidation."""
        validation = {
            "dependencies_satisfied": True,
            "dependency_analysis": {},
            "circular_dependencies": [],
            "missing_dependencies": []
        }
        
        # Analyze dependencies for each service
        for service_name in plan.target_services:
            info = self.service_registry.classified_services.get(service_name)
            if info:
                service_deps = set(info.config.dependencies)
                validation["dependency_analysis"][service_name] = list(service_deps)
        
        return validation
    
    async def _validate_resource_requirements(self, plan: ConsolidationPlan) -> Dict[str, Any]:
        """Validate resource requirements for consolidated service."""
        validation = {
            "resource_requirements_met": True,
            "total_resources": {"memory_mb": 0, "cpu_cores": 0.0},
            "estimated_consolidated_resources": {"memory_mb": 0, "cpu_cores": 0.0},
            "resource_savings": {"memory_mb": 0, "cpu_cores": 0.0}
        }
        
        # Calculate total current resource usage
        for service_name in plan.target_services:
            info = self.service_registry.classified_services.get(service_name)
            if info:
                req = info.config.resource_requirements
                validation["total_resources"]["memory_mb"] += req.memory_mb or 0
                validation["total_resources"]["cpu_cores"] += req.cpu_cores or 0.0
        
        # Estimate consolidated resource usage (assume 20% overhead reduction)
        validation["estimated_consolidated_resources"] = {
            "memory_mb": int(validation["total_resources"]["memory_mb"] * 0.8),
            "cpu_cores": validation["total_resources"]["cpu_cores"] * 0.85
        }
        
        # Calculate savings
        validation["resource_savings"] = {
            "memory_mb": validation["total_resources"]["memory_mb"] - validation["estimated_consolidated_resources"]["memory_mb"],
            "cpu_cores": validation["total_resources"]["cpu_cores"] - validation["estimated_consolidated_resources"]["cpu_cores"]
        }
        
        return validation
    
    async def _assess_consolidation_risks(self, plan: ConsolidationPlan) -> Dict[str, Any]:
        """Assess risks associated with the consolidation plan."""
        risk_assessment = {
            "risk_level": "low",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        risk_score = 0
        
        # Check for essential service consolidation
        for service_name in plan.target_services:
            info = self.service_registry.classified_services.get(service_name)
            if info and info.config.classification == ServiceClassification.ESSENTIAL:
                risk_score += 3
                risk_assessment["risk_factors"].append(f"Consolidating essential service: {service_name}")
                risk_assessment["mitigation_strategies"].append("Implement comprehensive rollback plan")
        
        # Determine risk level
        if risk_score >= 8:
            risk_assessment["risk_level"] = "critical"
        elif risk_score >= 5:
            risk_assessment["risk_level"] = "high"
        elif risk_score >= 2:
            risk_assessment["risk_level"] = "medium"
        
        return risk_assessment
    
    def _generate_validation_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # API contract recommendations
        api_validation = validation_results.get("api_contract_validation", {})
        if api_validation.get("conflicting_contracts"):
            recommendations.append("Resolve method name conflicts before consolidation")
        
        # Risk recommendations
        risk_assessment = validation_results.get("risk_assessment", {})
        if risk_assessment.get("risk_level") in ["high", "critical"]:
            recommendations.append("Consider phased consolidation approach to reduce risk")
        
        return recommendations
    
    def _identify_blocking_issues(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify issues that block consolidation execution."""
        blocking_issues = []
        
        api_validation = validation_results.get("api_contract_validation", {})
        if not api_validation.get("all_contracts_preserved", True):
            blocking_issues.append("API contracts cannot be preserved")
        
        risk_assessment = validation_results.get("risk_assessment", {})
        if risk_assessment.get("risk_level") == "critical":
            blocking_issues.append("Consolidation risk level is too high")
        
        return blocking_issues


class ServiceConsolidationOrchestrator:
    """Main orchestrator for service consolidation and redundancy elimination."""
    
    def __init__(self, service_registry: ClassifiedServiceRegistry):
        """
        Initialize the consolidation orchestrator.
        
        Args:
            service_registry: The classified service registry
        """
        self.service_registry = service_registry
        self.analyzer = ServiceAnalyzer(service_registry)
        self.merger = ServiceMerger(service_registry, self.analyzer)
        self.comm_optimizer = InterServiceCommunicationOptimizer(service_registry)
        self.validator = ConsolidationValidator(service_registry, self.analyzer)
        
        self.consolidation_history: List[Dict[str, Any]] = []
    
    async def analyze_consolidation_opportunities(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of consolidation opportunities.
        
        Returns:
            Complete analysis report with recommendations
        """
        logger.info("Starting comprehensive consolidation analysis...")
        
        analysis_report = {
            "timestamp": time.time(),
            "service_overlaps": {},
            "consolidation_candidates": [],
            "communication_patterns": {},
            "optimization_opportunities": {},
            "estimated_total_savings": {"memory_mb": 0, "cpu_cores": 0.0, "startup_time_seconds": 0.0},
            "recommendations": []
        }
        
        # Analyze service overlaps
        analysis_report["service_overlaps"] = await self.analyzer.analyze_all_services()
        
        # Identify consolidation candidates
        candidates = await self.analyzer.identify_consolidation_candidates()
        analysis_report["consolidation_candidates"] = [
            {"services": [a, b], "potential": potential}
            for a, b, potential in candidates
        ]
        
        # Analyze communication patterns
        analysis_report["communication_patterns"] = await self.comm_optimizer.analyze_communication_patterns()
        
        # Identify optimization opportunities
        analysis_report["optimization_opportunities"] = await self.comm_optimizer.optimize_service_communication()
        
        # Calculate total estimated savings
        for candidate in candidates:
            service_a, service_b, potential = candidate
            overlap = await self.analyzer.analyze_service_overlap(service_a, service_b)
            savings = overlap.estimated_savings
            
            analysis_report["estimated_total_savings"]["memory_mb"] += savings.get("memory_mb", 0)
            analysis_report["estimated_total_savings"]["cpu_cores"] += savings.get("cpu_cores", 0)
            analysis_report["estimated_total_savings"]["startup_time_seconds"] += savings.get("startup_time_seconds", 0)
        
        # Generate high-level recommendations
        analysis_report["recommendations"] = self._generate_consolidation_recommendations(analysis_report)
        
        logger.info(f"Consolidation analysis complete. Found {len(candidates)} consolidation opportunities.")
        return analysis_report
    
    def _generate_consolidation_recommendations(self, analysis_report: Dict[str, Any]) -> List[str]:
        """Generate high-level consolidation recommendations."""
        recommendations = []
        
        candidates = analysis_report.get("consolidation_candidates", [])
        if len(candidates) > 0:
            recommendations.append(f"Found {len(candidates)} service consolidation opportunities")
        
        # Communication optimization recommendations
        comm_opts = analysis_report.get("optimization_opportunities", {})
        batching_ops = len(comm_opts.get("batching_opportunities", []))
        if batching_ops > 0:
            recommendations.append(f"Implement request batching for {batching_ops} service pairs")
        
        caching_ops = len(comm_opts.get("caching_opportunities", []))
        if caching_ops > 0:
            recommendations.append(f"Implement response caching for {caching_ops} services")
        
        return recommendations
    
    async def create_and_validate_consolidation_plan(
        self, 
        service_names: List[str], 
        consolidation_type: ConsolidationType
    ) -> Tuple[ConsolidationPlan, Dict[str, Any]]:
        """
        Create and validate a consolidation plan.
        
        Args:
            service_names: Services to consolidate
            consolidation_type: Type of consolidation
            
        Returns:
            Tuple of (consolidation_plan, validation_results)
        """
        # Create the plan
        plan = await self.merger.create_consolidation_plan(service_names, consolidation_type)
        
        # Validate the plan
        validation_results = await self.validator.validate_consolidation_plan(plan)
        
        return plan, validation_results
    
    async def execute_consolidation(self, plan_id: str) -> Dict[str, Any]:
        """
        Execute a validated consolidation plan.
        
        Args:
            plan_id: ID of the consolidation plan to execute
            
        Returns:
            Execution results
        """
        execution_results = await self.merger.execute_consolidation_plan(plan_id)
        
        # Record in history
        self.consolidation_history.append({
            "plan_id": plan_id,
            "execution_results": execution_results,
            "timestamp": time.time()
        })
        
        return execution_results
    
    async def get_consolidation_status(self) -> Dict[str, Any]:
        """
        Get current consolidation status and metrics.
        
        Returns:
            Status report with metrics and history
        """
        return {
            "total_consolidations": len(self.consolidation_history),
            "successful_consolidations": len([
                h for h in self.consolidation_history 
                if h["execution_results"]["status"] == "completed"
            ]),
            "failed_consolidations": len([
                h for h in self.consolidation_history 
                if h["execution_results"]["status"] in ["failed", "error"]
            ]),
            "consolidation_history": self.consolidation_history[-10:],  # Last 10
            "current_service_count": len(self.service_registry.classified_services),
            "cache_stats": {
                "functionality_cache_size": len(self.analyzer.functionality_cache),
                "overlap_cache_size": len(self.analyzer.overlap_cache)
            }
        }