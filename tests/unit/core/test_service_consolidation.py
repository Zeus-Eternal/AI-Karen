"""
Tests for Service Consolidation and Redundancy Elimination System.

This module tests the comprehensive service analysis, consolidation, and optimization
capabilities to ensure proper functionality while preserving API contracts.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Set

from src.ai_karen_engine.core.service_consolidation import (
    ServiceAnalyzer,
    ServiceMerger,
    InterServiceCommunicationOptimizer,
    ConsolidationValidator,
    ServiceConsolidationOrchestrator,
    ConsolidationType,
    OverlapType,
    FunctionalitySignature,
    OverlapAnalysis,
    ConsolidationPlan
)
from src.ai_karen_engine.core.service_classification import ServiceConfig, ServiceClassification, ResourceRequirements
from src.ai_karen_engine.core.classified_service_registry import ClassifiedServiceRegistry, ClassifiedServiceInfo, ServiceLifecycleState


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str, methods: List[str] = None, endpoints: List[str] = None):
        self.name = name
        self.methods = methods or []
        self.endpoints = endpoints or []
    
    def get_routes(self):
        return self.endpoints
    
    async def get_resource_usage(self):
        return {"memory": "100MB", "cpu": "0.5 cores"}


@pytest.fixture
def mock_service_registry():
    """Create a mock classified service registry for testing."""
    registry = Mock(spec=ClassifiedServiceRegistry)
    
    # Create mock services
    services = {
        "service_a": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="service_a",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=50,
                dependencies=["database_client"],
                resource_requirements=ResourceRequirements(memory_mb=128, cpu_cores=0.5),
                consolidation_group="group1"
            ),
            lifecycle_state=ServiceLifecycleState.ACTIVE
        ),
        "service_b": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="service_b",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=60,
                dependencies=["database_client"],
                resource_requirements=ResourceRequirements(memory_mb=96, cpu_cores=0.3),
                consolidation_group="group1"
            ),
            lifecycle_state=ServiceLifecycleState.ACTIVE
        ),
        "service_c": ClassifiedServiceInfo(
            config=ServiceConfig(
                name="service_c",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=10,
                dependencies=[],
                resource_requirements=ResourceRequirements(memory_mb=64, cpu_cores=0.2)
            ),
            lifecycle_state=ServiceLifecycleState.ACTIVE
        )
    }
    
    registry.classified_services = services
    
    # Mock get_service method
    async def mock_get_service(name: str):
        if name == "service_a":
            return MockService("service_a", ["method1", "method2", "common_method"], ["/api/a"])
        elif name == "service_b":
            return MockService("service_b", ["method3", "common_method"], ["/api/b"])
        elif name == "service_c":
            return MockService("service_c", ["essential_method"], ["/api/essential"])
        else:
            raise ValueError(f"Service {name} not found")
    
    registry.get_service = mock_get_service
    
    return registry


@pytest.fixture
def service_analyzer(mock_service_registry):
    """Create a service analyzer for testing."""
    return ServiceAnalyzer(mock_service_registry)


@pytest.fixture
def service_merger(mock_service_registry, service_analyzer):
    """Create a service merger for testing."""
    return ServiceMerger(mock_service_registry, service_analyzer)


@pytest.fixture
def communication_optimizer(mock_service_registry):
    """Create a communication optimizer for testing."""
    return InterServiceCommunicationOptimizer(mock_service_registry)


@pytest.fixture
def consolidation_validator(mock_service_registry, service_analyzer):
    """Create a consolidation validator for testing."""
    return ConsolidationValidator(mock_service_registry, service_analyzer)


@pytest.fixture
def consolidation_orchestrator(mock_service_registry):
    """Create a consolidation orchestrator for testing."""
    return ServiceConsolidationOrchestrator(mock_service_registry)


class TestServiceAnalyzer:
    """Test the ServiceAnalyzer class."""
    
    @pytest.mark.asyncio
    async def test_analyze_service_functionality(self, service_analyzer):
        """Test analyzing service functionality."""
        signature = await service_analyzer.analyze_service_functionality("service_a")
        
        assert isinstance(signature, FunctionalitySignature)
        assert "method1" in signature.methods
        assert "method2" in signature.methods
        assert "common_method" in signature.methods
        assert "database_client" in signature.dependencies
        assert "memory" in signature.resource_patterns
        assert "/api/a" in signature.api_endpoints
    
    @pytest.mark.asyncio
    async def test_analyze_service_overlap(self, service_analyzer):
        """Test analyzing overlap between services."""
        overlap = await service_analyzer.analyze_service_overlap("service_a", "service_b")
        
        assert isinstance(overlap, OverlapAnalysis)
        assert overlap.service_a == "service_a"
        assert overlap.service_b == "service_b"
        assert "common_method" in overlap.common_methods
        assert "database_client" in overlap.common_dependencies
        assert overlap.overlap_score > 0
        assert overlap.consolidation_potential > 0
    
    @pytest.mark.asyncio
    async def test_analyze_all_services(self, service_analyzer):
        """Test analyzing all services for overlaps."""
        overlaps = await service_analyzer.analyze_all_services()
        
        assert isinstance(overlaps, dict)
        assert "service_a" in overlaps
        assert "service_b" in overlaps
        
        # Should find overlap between service_a and service_b
        service_a_overlaps = overlaps["service_a"]
        assert len(service_a_overlaps) > 0
        
        # Find the overlap with service_b
        overlap_with_b = next((o for o in service_a_overlaps if o.service_b == "service_b"), None)
        assert overlap_with_b is not None
        assert overlap_with_b.overlap_score > 0.3
    
    @pytest.mark.asyncio
    async def test_identify_consolidation_candidates(self, service_analyzer):
        """Test identifying consolidation candidates."""
        candidates = await service_analyzer.identify_consolidation_candidates(min_overlap_score=0.3)
        
        assert isinstance(candidates, list)
        assert len(candidates) > 0
        
        # Should find service_a and service_b as candidates
        candidate_pairs = [(a, b) for a, b, _ in candidates]
        assert ("service_a", "service_b") in candidate_pairs or ("service_b", "service_a") in candidate_pairs
    
    @pytest.mark.asyncio
    async def test_functionality_caching(self, service_analyzer):
        """Test that functionality analysis is cached."""
        # First call
        signature1 = await service_analyzer.analyze_service_functionality("service_a")
        
        # Second call should use cache
        signature2 = await service_analyzer.analyze_service_functionality("service_a")
        
        assert signature1 is signature2  # Should be the same object from cache
        assert "service_a" in service_analyzer.functionality_cache


class TestServiceMerger:
    """Test the ServiceMerger class."""
    
    @pytest.mark.asyncio
    async def test_create_consolidation_plan(self, service_merger):
        """Test creating a consolidation plan."""
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE
        )
        
        assert isinstance(plan, ConsolidationPlan)
        assert plan.consolidation_type == ConsolidationType.MERGE
        assert set(plan.target_services) == {"service_a", "service_b"}
        assert plan.primary_service in ["service_a", "service_b"]
        assert len(plan.secondary_services) == 1
        assert plan.estimated_memory_savings > 0
        assert plan.estimated_cpu_savings > 0
        assert len(plan.migration_steps) > 0
        assert len(plan.rollback_plan) > 0
        assert len(plan.validation_tests) > 0
    
    @pytest.mark.asyncio
    async def test_select_primary_service(self, service_merger):
        """Test selecting primary service for consolidation."""
        primary = await service_merger._select_primary_service(["service_a", "service_b", "service_c"])
        
        # service_c should be selected as it's essential and has higher priority
        assert primary == "service_c"
    
    def test_assess_consolidation_risk(self, service_merger):
        """Test assessing consolidation risk."""
        # Test with essential service (high risk)
        risk = service_merger._assess_consolidation_risk(
            ["service_c", "service_a"], 
            ConsolidationType.ELIMINATION
        )
        assert risk in ["medium", "high"]
        
        # Test with optional services (lower risk)
        risk = service_merger._assess_consolidation_risk(
            ["service_a", "service_b"], 
            ConsolidationType.PROXY
        )
        assert risk in ["low", "medium"]
    
    @pytest.mark.asyncio
    async def test_extract_api_contracts(self, service_merger):
        """Test extracting API contracts."""
        contracts = await service_merger._extract_api_contracts(["service_a", "service_b"])
        
        assert isinstance(contracts, list)
        assert len(contracts) > 0
        
        # Should include methods and endpoints
        method_contracts = [c for c in contracts if "." in c and not c.startswith("API:")]
        api_contracts = [c for c in contracts if c.startswith("API:")]
        
        assert len(method_contracts) > 0
        assert len(api_contracts) > 0
        assert "service_a.method1" in contracts
        assert "API:/api/a" in contracts
    
    def test_generate_migration_steps(self, service_merger):
        """Test generating migration steps."""
        steps = service_merger._generate_migration_steps(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE, 
            "service_a"
        )
        
        assert isinstance(steps, list)
        assert len(steps) > 0
        
        # Should include key migration steps
        step_text = " ".join(steps)
        assert "backup" in step_text.lower()
        assert "consolidated service" in step_text.lower()
        assert "service registry" in step_text.lower()
        assert "remove secondary services" in step_text.lower()
    
    @pytest.mark.asyncio
    async def test_execute_consolidation_plan(self, service_merger):
        """Test executing a consolidation plan."""
        # Create a plan first
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.PROXY
        )
        
        # Execute the plan
        results = await service_merger.execute_consolidation_plan(plan.consolidation_id)
        
        assert isinstance(results, dict)
        assert "plan_id" in results
        assert "status" in results
        assert "steps_completed" in results
        assert "start_time" in results
        assert "end_time" in results
        assert results["status"] in ["completed", "failed", "error"]


class TestInterServiceCommunicationOptimizer:
    """Test the InterServiceCommunicationOptimizer class."""
    
    @pytest.mark.asyncio
    async def test_analyze_communication_patterns(self, communication_optimizer):
        """Test analyzing communication patterns."""
        patterns = await communication_optimizer.analyze_communication_patterns()
        
        assert isinstance(patterns, dict)
        assert "service_a" in patterns
        assert "service_b" in patterns
        
        # service_a should have communication with database_client (dependency)
        assert "database_client" in patterns["service_a"]
        assert patterns["service_a"]["database_client"] > 0
    
    @pytest.mark.asyncio
    async def test_optimize_service_communication(self, communication_optimizer):
        """Test optimizing service communication."""
        # First analyze patterns
        await communication_optimizer.analyze_communication_patterns()
        
        # Then optimize
        optimizations = await communication_optimizer.optimize_service_communication()
        
        assert isinstance(optimizations, dict)
        assert "batching_opportunities" in optimizations
        assert "caching_opportunities" in optimizations
        assert "direct_connection_opportunities" in optimizations
        assert "estimated_savings" in optimizations
        
        # Should have some caching opportunities for optional services
        assert len(optimizations["caching_opportunities"]) > 0
    
    @pytest.mark.asyncio
    async def test_implement_communication_optimizations(self, communication_optimizer):
        """Test implementing communication optimizations."""
        # Create mock optimizations
        optimizations = {
            "batching_opportunities": [
                {
                    "from_service": "service_a",
                    "to_service": "service_b",
                    "frequency": 25
                }
            ],
            "caching_opportunities": [
                {
                    "service": "service_a"
                }
            ]
        }
        
        results = await communication_optimizer.implement_communication_optimizations(optimizations)
        
        assert isinstance(results, dict)
        assert "implemented" in results
        assert "failed" in results
        assert len(results["implemented"]) > 0


class TestConsolidationValidator:
    """Test the ConsolidationValidator class."""
    
    @pytest.mark.asyncio
    async def test_validate_consolidation_plan(self, consolidation_validator, service_merger):
        """Test validating a consolidation plan."""
        # Create a plan first
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE
        )
        
        # Validate the plan
        validation = await consolidation_validator.validate_consolidation_plan(plan)
        
        assert isinstance(validation, dict)
        assert "plan_id" in validation
        assert "overall_status" in validation
        assert "api_contract_validation" in validation
        assert "dependency_validation" in validation
        assert "resource_validation" in validation
        assert "risk_assessment" in validation
        assert "recommendations" in validation
        
        assert validation["overall_status"] in ["approved", "blocked", "pending"]
    
    @pytest.mark.asyncio
    async def test_validate_api_contracts(self, consolidation_validator, service_merger):
        """Test validating API contracts."""
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE
        )
        
        validation = await consolidation_validator._validate_api_contracts(plan)
        
        assert isinstance(validation, dict)
        assert "all_contracts_preserved" in validation
        assert "contract_details" in validation
        assert "missing_contracts" in validation
        assert "conflicting_contracts" in validation
        
        # Should have contract details for both services
        assert "service_a" in validation["contract_details"]
        assert "service_b" in validation["contract_details"]
    
    @pytest.mark.asyncio
    async def test_validate_dependencies(self, consolidation_validator, service_merger):
        """Test validating service dependencies."""
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE
        )
        
        validation = await consolidation_validator._validate_dependencies(plan)
        
        assert isinstance(validation, dict)
        assert "dependencies_satisfied" in validation
        assert "dependency_analysis" in validation
        assert "missing_dependencies" in validation
        
        # Both services depend on database_client
        assert "service_a" in validation["dependency_analysis"]
        assert "service_b" in validation["dependency_analysis"]
    
    @pytest.mark.asyncio
    async def test_validate_resource_requirements(self, consolidation_validator, service_merger):
        """Test validating resource requirements."""
        plan = await service_merger.create_consolidation_plan(
            ["service_a", "service_b"], 
            ConsolidationType.MERGE
        )
        
        validation = await consolidation_validator._validate_resource_requirements(plan)
        
        assert isinstance(validation, dict)
        assert "resource_requirements_met" in validation
        assert "total_resources" in validation
        assert "estimated_consolidated_resources" in validation
        assert "resource_savings" in validation
        
        # Should show resource savings
        assert validation["resource_savings"]["memory_mb"] > 0
        assert validation["resource_savings"]["cpu_cores"] > 0


class TestServiceConsolidationOrchestrator:
    """Test the ServiceConsolidationOrchestrator class."""
    
    @pytest.mark.asyncio
    async def test_analyze_consolidation_opportunities(self, consolidation_orchestrator):
        """Test comprehensive consolidation analysis."""
        analysis = await consolidation_orchestrator.analyze_consolidation_opportunities()
        
        assert isinstance(analysis, dict)
        assert "timestamp" in analysis
        assert "service_overlaps" in analysis
        assert "consolidation_candidates" in analysis
        assert "communication_patterns" in analysis
        assert "optimization_opportunities" in analysis
        assert "estimated_total_savings" in analysis
        assert "recommendations" in analysis
        
        # Should find some consolidation candidates
        assert len(analysis["consolidation_candidates"]) > 0
        
        # Should have recommendations
        assert len(analysis["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_and_validate_consolidation_plan(self, consolidation_orchestrator):
        """Test creating and validating a consolidation plan."""
        plan, validation = await consolidation_orchestrator.create_and_validate_consolidation_plan(
            ["service_a", "service_b"],
            ConsolidationType.MERGE
        )
        
        assert isinstance(plan, ConsolidationPlan)
        assert isinstance(validation, dict)
        
        assert plan.consolidation_type == ConsolidationType.MERGE
        assert set(plan.target_services) == {"service_a", "service_b"}
        assert validation["overall_status"] in ["approved", "blocked", "pending"]
    
    @pytest.mark.asyncio
    async def test_execute_consolidation(self, consolidation_orchestrator):
        """Test executing a consolidation."""
        # Create and validate plan first
        plan, validation = await consolidation_orchestrator.create_and_validate_consolidation_plan(
            ["service_a", "service_b"],
            ConsolidationType.PROXY
        )
        
        # Execute if approved
        if validation["overall_status"] == "approved":
            results = await consolidation_orchestrator.execute_consolidation(plan.consolidation_id)
            
            assert isinstance(results, dict)
            assert "plan_id" in results
            assert "status" in results
            
            # Should be recorded in history
            status = await consolidation_orchestrator.get_consolidation_status()
            assert status["total_consolidations"] > 0
    
    @pytest.mark.asyncio
    async def test_get_consolidation_status(self, consolidation_orchestrator):
        """Test getting consolidation status."""
        status = await consolidation_orchestrator.get_consolidation_status()
        
        assert isinstance(status, dict)
        assert "total_consolidations" in status
        assert "successful_consolidations" in status
        assert "failed_consolidations" in status
        assert "consolidation_history" in status
        assert "current_service_count" in status
        assert "cache_stats" in status
    
    def test_generate_consolidation_recommendations(self, consolidation_orchestrator):
        """Test generating consolidation recommendations."""
        analysis_report = {
            "consolidation_candidates": [
                {"services": ["service_a", "service_b"], "potential": 0.8}
            ],
            "optimization_opportunities": {
                "batching_opportunities": [{"from": "a", "to": "b"}],
                "caching_opportunities": [{"service": "a"}, {"service": "b"}]
            },
            "estimated_total_savings": {
                "memory_mb": 150,
                "cpu_cores": 0.3,
                "startup_time_seconds": 2.0
            }
        }
        
        recommendations = consolidation_orchestrator._generate_consolidation_recommendations(analysis_report)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should include recommendations about candidates and optimizations
        rec_text = " ".join(recommendations)
        assert "consolidation" in rec_text.lower()
        assert "batching" in rec_text.lower() or "caching" in rec_text.lower()


class TestIntegration:
    """Integration tests for the complete consolidation system."""
    
    @pytest.mark.asyncio
    async def test_full_consolidation_workflow(self, consolidation_orchestrator):
        """Test the complete consolidation workflow."""
        # 1. Analyze opportunities
        analysis = await consolidation_orchestrator.analyze_consolidation_opportunities()
        assert len(analysis["consolidation_candidates"]) > 0
        
        # 2. Create and validate plan
        candidate = analysis["consolidation_candidates"][0]
        services = candidate["services"]
        
        plan, validation = await consolidation_orchestrator.create_and_validate_consolidation_plan(
            services,
            ConsolidationType.PROXY
        )
        
        assert plan is not None
        assert validation is not None
        
        # 3. Execute if approved
        if validation["overall_status"] == "approved":
            results = await consolidation_orchestrator.execute_consolidation(plan.consolidation_id)
            assert results["status"] in ["completed", "failed", "error"]
        
        # 4. Check final status
        status = await consolidation_orchestrator.get_consolidation_status()
        assert isinstance(status, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_service_registry):
        """Test error handling in consolidation system."""
        # Test with invalid service
        analyzer = ServiceAnalyzer(mock_service_registry)
        
        # Should handle missing service gracefully
        signature = await analyzer.analyze_service_functionality("nonexistent_service")
        assert isinstance(signature, FunctionalitySignature)
        assert len(signature.methods) == 0  # Empty signature for missing service
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, service_analyzer):
        """Test caching behavior across multiple operations."""
        # Multiple calls should use cache
        sig1 = await service_analyzer.analyze_service_functionality("service_a")
        sig2 = await service_analyzer.analyze_service_functionality("service_a")
        assert sig1 is sig2
        
        # Overlap analysis should also be cached
        overlap1 = await service_analyzer.analyze_service_overlap("service_a", "service_b")
        overlap2 = await service_analyzer.analyze_service_overlap("service_a", "service_b")
        overlap3 = await service_analyzer.analyze_service_overlap("service_b", "service_a")  # Reversed order
        
        assert overlap1 is overlap2
        assert overlap1 is overlap3  # Should be same due to sorted cache key


if __name__ == "__main__":
    pytest.main([__file__])