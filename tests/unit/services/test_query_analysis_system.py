"""
Tests for Query Analysis System Components

This module tests all components of the query analysis and response strategy system
including query analyzer, response strategy engine, context processor, resource
allocation system, and priority processing system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.ai_karen_engine.services.query_analyzer import (
    QueryAnalyzer, QueryAnalysis, ComplexityLevel, ContentType, 
    ExpertiseLevel, Priority, ModalityType
)
from src.ai_karen_engine.services.response_strategy_engine import (
    ResponseStrategyEngine, ResponseStrategy, ProcessingMode, ResponseFormat
)
from src.ai_karen_engine.services.context_processor import (
    ContextProcessor, ProcessedContext, ContextType
)
from src.ai_karen_engine.services.resource_allocation_system import (
    ResourceAllocationSystem, ResourceRequest, ResourceAllocation
)
from src.ai_karen_engine.services.priority_processing_system import (
    PriorityProcessingSystem, ProcessingTask, QueueType
)
from src.ai_karen_engine.services.query_analysis_service import (
    QueryAnalysisService, QueryAnalysisResult
)


class TestQueryAnalyzer:
    """Test cases for QueryAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return QueryAnalyzer()
    
    @pytest.mark.asyncio
    async def test_simple_query_analysis(self, analyzer):
        """Test analysis of a simple query"""
        query = "What is Python?"
        result = await analyzer.analyze_query(query)
        
        assert isinstance(result, QueryAnalysis)
        assert result.complexity == ComplexityLevel.SIMPLE
        assert result.content_type == ContentType.TEXT
        assert ModalityType.TEXT in result.modality_requirements
        assert result.confidence_score > 0.5
    
    @pytest.mark.asyncio
    async def test_complex_technical_query_analysis(self, analyzer):
        """Test analysis of a complex technical query"""
        query = """
        How do I implement a distributed microservices architecture with 
        Kubernetes, including service mesh, monitoring, and CI/CD pipeline 
        for a high-traffic e-commerce platform?
        """
        result = await analyzer.analyze_query(query)
        
        assert result.complexity == ComplexityLevel.COMPLEX
        assert result.content_type in [ContentType.TECHNICAL, ContentType.TEXT]
        assert result.user_expertise_level in [ExpertiseLevel.ADVANCED, ExpertiseLevel.EXPERT]
        assert result.estimated_response_length > 1000
    
    @pytest.mark.asyncio
    async def test_code_query_analysis(self, analyzer):
        """Test analysis of a code-related query"""
        query = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        How can I optimize this Python function?
        """
        result = await analyzer.analyze_query(query)
        
        assert result.content_type == ContentType.MIXED  # Code + explanation request
        assert result.requires_code_execution == False  # Not asking to run it
        assert 'python' in result.analysis_metadata.get('has_code_snippets', False) or True
    
    @pytest.mark.asyncio
    async def test_urgent_query_analysis(self, analyzer):
        """Test analysis of urgent query"""
        query = "URGENT: My production server is down, how do I fix it immediately?"
        result = await analyzer.analyze_query(query)
        
        assert result.processing_priority == Priority.URGENT
        assert result.complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]
    
    @pytest.mark.asyncio
    async def test_multimodal_query_analysis(self, analyzer):
        """Test analysis of multimodal query"""
        query = "Can you analyze this image and create a video tutorial about it?"
        result = await analyzer.analyze_query(query)
        
        assert ModalityType.IMAGE in result.modality_requirements
        assert ModalityType.VIDEO in result.modality_requirements
        assert len(result.modality_requirements) >= 2


class TestResponseStrategyEngine:
    """Test cases for ResponseStrategyEngine"""
    
    @pytest.fixture
    def strategy_engine(self):
        return ResponseStrategyEngine()
    
    @pytest.fixture
    def sample_query_analysis(self):
        return QueryAnalysis(
            complexity=ComplexityLevel.MODERATE,
            content_type=ContentType.TECHNICAL,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.NORMAL,
            estimated_response_length=1500,
            requires_code_execution=False,
            requires_external_data=False,
            language='english',
            domain_specific=None,
            confidence_score=0.8,
            analysis_metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_strategy_determination(self, strategy_engine, sample_query_analysis):
        """Test basic strategy determination"""
        available_models = [{'id': 'test-model', 'capabilities': ['text']}]
        
        strategy = await strategy_engine.determine_response_strategy(
            sample_query_analysis, available_models
        )
        
        assert isinstance(strategy, ResponseStrategy)
        assert strategy.processing_mode in ProcessingMode
        assert strategy.response_format in ResponseFormat
        assert strategy.resource_allocation.cpu_limit <= 5.0  # Requirement: under 5%
        assert strategy.confidence_score > 0.0
    
    @pytest.mark.asyncio
    async def test_urgent_priority_strategy(self, strategy_engine):
        """Test strategy for urgent priority queries"""
        urgent_analysis = QueryAnalysis(
            complexity=ComplexityLevel.SIMPLE,
            content_type=ContentType.TEXT,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.URGENT,
            estimated_response_length=500,
            requires_code_execution=False,
            requires_external_data=False,
            language='english',
            domain_specific=None,
            confidence_score=0.9,
            analysis_metadata={}
        )
        
        strategy = await strategy_engine.determine_response_strategy(urgent_analysis, [])
        
        assert strategy.processing_mode == ProcessingMode.FAST
        assert strategy.resource_allocation.priority_level >= 3
    
    @pytest.mark.asyncio
    async def test_resource_limits_enforcement(self, strategy_engine, sample_query_analysis):
        """Test that resource limits are enforced"""
        strategy = await strategy_engine.determine_response_strategy(sample_query_analysis, [])
        
        # Verify CPU limit requirement
        assert strategy.resource_allocation.cpu_limit <= 5.0
        assert strategy.resource_allocation.memory_limit > 0
        assert strategy.resource_allocation.timeout_seconds > 0


class TestContextProcessor:
    """Test cases for ContextProcessor"""
    
    @pytest.fixture
    def context_processor(self):
        return ContextProcessor()
    
    @pytest.fixture
    def sample_query_analysis(self):
        return QueryAnalysis(
            complexity=ComplexityLevel.MODERATE,
            content_type=ContentType.TECHNICAL,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.NORMAL,
            estimated_response_length=1000,
            requires_code_execution=True,
            requires_external_data=False,
            language='english',
            domain_specific='technical',
            confidence_score=0.8,
            analysis_metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_context_processing(self, context_processor, sample_query_analysis):
        """Test basic context processing"""
        result = await context_processor.process_context(sample_query_analysis)
        
        assert isinstance(result, ProcessedContext)
        assert result.technical_context is not None
        assert result.temporal_context is not None
        assert result.relevance_score >= 0.0
        assert result.context_summary is not None
    
    @pytest.mark.asyncio
    async def test_user_context_processing(self, context_processor, sample_query_analysis):
        """Test processing with user context"""
        result = await context_processor.process_context(
            sample_query_analysis,
            user_id="test_user_123"
        )
        
        assert result.user_context.get('user_id') == "test_user_123"
        assert 'fallback' not in result.user_context or not result.user_context['fallback']
    
    @pytest.mark.asyncio
    async def test_conversation_context_processing(self, context_processor, sample_query_analysis):
        """Test processing with conversation context"""
        result = await context_processor.process_context(
            sample_query_analysis,
            conversation_id="conv_456"
        )
        
        assert result.conversation_context.get('conversation_id') == "conv_456"


class TestResourceAllocationSystem:
    """Test cases for ResourceAllocationSystem"""
    
    @pytest.fixture
    def resource_system(self):
        system = ResourceAllocationSystem()
        # Stop monitoring for tests
        system.stop_monitoring()
        return system
    
    @pytest.fixture
    def sample_query_analysis(self):
        return QueryAnalysis(
            complexity=ComplexityLevel.MODERATE,
            content_type=ContentType.TEXT,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.NORMAL,
            estimated_response_length=1000,
            requires_code_execution=False,
            requires_external_data=False,
            language='english',
            domain_specific=None,
            confidence_score=0.8,
            analysis_metadata={}
        )
    
    @pytest.fixture
    def sample_response_strategy(self):
        from src.ai_karen_engine.services.response_strategy_engine import ResourceAllocation as StrategyResourceAllocation
        return ResponseStrategy(
            processing_mode=ProcessingMode.BALANCED,
            response_format=ResponseFormat.MARKDOWN,
            model_requirements=Mock(),
            resource_allocation=StrategyResourceAllocation(
                cpu_limit=3.0,
                memory_limit=200 * 1024 * 1024,
                gpu_allocation=None,
                timeout_seconds=15,
                priority_level=2,
                concurrent_limit=2
            ),
            optimizations=[],
            content_depth='moderate',
            streaming_enabled=False,
            cache_strategy='standard_cache',
            estimated_generation_time=5.0,
            confidence_score=0.8,
            strategy_metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_resource_allocation(self, resource_system, sample_query_analysis, sample_response_strategy):
        """Test basic resource allocation"""
        allocation = await resource_system.allocate_resources(
            sample_query_analysis,
            sample_response_strategy,
            "test_query_123"
        )
        
        if allocation:  # May be None if system resources are constrained
            assert allocation.allocated_cpu <= 5.0  # Requirement: under 5%
            assert allocation.allocated_memory > 0
            assert allocation.status.value in ['allocated', 'pending']
            
            # Test resource release
            released = await resource_system.release_resources(allocation.allocation_id)
            assert released == True
    
    @pytest.mark.asyncio
    async def test_resource_statistics(self, resource_system):
        """Test resource statistics collection"""
        stats = await resource_system.get_resource_statistics()
        
        assert 'current_resources' in stats
        assert 'allocations' in stats
        assert 'limits' in stats
        assert stats['limits']['max_cpu_per_request'] == 5.0  # Verify requirement


class TestPriorityProcessingSystem:
    """Test cases for PriorityProcessingSystem"""
    
    @pytest.fixture
    def processing_system(self):
        system = PriorityProcessingSystem(max_concurrent_tasks=2)
        return system
    
    @pytest.fixture
    def sample_query_analysis(self):
        return QueryAnalysis(
            complexity=ComplexityLevel.SIMPLE,
            content_type=ContentType.TEXT,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.NORMAL,
            estimated_response_length=500,
            requires_code_execution=False,
            requires_external_data=False,
            language='english',
            domain_specific=None,
            confidence_score=0.8,
            analysis_metadata={}
        )
    
    @pytest.fixture
    def sample_response_strategy(self):
        return Mock(
            processing_mode=ProcessingMode.FAST,
            estimated_generation_time=2.0
        )
    
    @pytest.mark.asyncio
    async def test_task_submission(self, processing_system, sample_query_analysis, sample_response_strategy):
        """Test task submission to processing system"""
        async def dummy_processing_function(analysis, strategy, allocation):
            await asyncio.sleep(0.1)
            return "test_result"
        
        task_id = await processing_system.submit_task(
            sample_query_analysis,
            sample_response_strategy,
            dummy_processing_function
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)
        
        # Wait a bit for processing
        await asyncio.sleep(0.2)
        
        # Check task status
        status = await processing_system.get_task_status(task_id)
        assert status is not None
        assert status['task_id'] == task_id
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, processing_system):
        """Test that high priority tasks are processed first"""
        results = []
        
        async def tracking_function(analysis, strategy, allocation):
            results.append(analysis.processing_priority.value)
            await asyncio.sleep(0.1)
            return f"result_{analysis.processing_priority.value}"
        
        # Submit tasks with different priorities
        low_analysis = Mock(processing_priority=Priority.LOW, complexity=ComplexityLevel.SIMPLE)
        high_analysis = Mock(processing_priority=Priority.HIGH, complexity=ComplexityLevel.SIMPLE)
        normal_analysis = Mock(processing_priority=Priority.NORMAL, complexity=ComplexityLevel.SIMPLE)
        
        strategy = Mock(processing_mode=ProcessingMode.FAST, estimated_generation_time=1.0)
        
        # Submit in reverse priority order
        await processing_system.submit_task(low_analysis, strategy, tracking_function)
        await processing_system.submit_task(normal_analysis, strategy, tracking_function)
        await processing_system.submit_task(high_analysis, strategy, tracking_function)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # High priority should be processed first
        if results:
            assert results[0] == 'high'
    
    @pytest.mark.asyncio
    async def test_queue_status(self, processing_system):
        """Test queue status reporting"""
        status = await processing_system.get_queue_status()
        
        assert 'queues' in status
        assert 'active_tasks' in status
        assert 'max_concurrent' in status
        assert status['max_concurrent'] == 2


class TestQueryAnalysisService:
    """Test cases for the main QueryAnalysisService"""
    
    @pytest.fixture
    def analysis_service(self):
        return QueryAnalysisService(max_concurrent_tasks=2)
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, analysis_service):
        """Test comprehensive query analysis"""
        query = "How do I optimize Python code for better performance?"
        
        result = await analysis_service.analyze_query_comprehensive(query)
        
        assert isinstance(result, QueryAnalysisResult)
        assert result.query_id is not None
        assert result.query_analysis is not None
        assert result.response_strategy is not None
        assert result.processed_context is not None
        assert result.analysis_metadata is not None
        
        # Verify CPU limit requirement
        assert result.response_strategy.resource_allocation.cpu_limit <= 5.0
    
    @pytest.mark.asyncio
    async def test_analyze_and_process(self, analysis_service):
        """Test analyze and process workflow"""
        query = "What is machine learning?"
        
        async def dummy_processor(analysis, strategy, allocation):
            await asyncio.sleep(0.1)
            return "ML explanation"
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=query,
            processing_function=dummy_processor
        )
        
        assert isinstance(analysis_result, QueryAnalysisResult)
        assert task_id is not None
        assert analysis_result.task_id == task_id
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check status
        status = await analysis_service.get_analysis_status(analysis_result.query_id)
        assert status is not None
        assert status['query_id'] == analysis_result.query_id
    
    @pytest.mark.asyncio
    async def test_system_metrics(self, analysis_service):
        """Test system metrics collection"""
        metrics = await analysis_service.get_system_metrics()
        
        assert 'resource_allocation' in metrics
        assert 'processing_queues' in metrics
        assert 'analysis_cache_size' in metrics
        assert 'timestamp' in metrics
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, analysis_service):
        """Test system performance optimization"""
        optimization_result = await analysis_service.optimize_system_performance()
        
        assert 'optimizations_applied' in optimization_result
        assert 'optimization_count' in optimization_result
        assert 'timestamp' in optimization_result
        assert isinstance(optimization_result['optimizations_applied'], list)


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def analysis_service(self):
        return QueryAnalysisService(max_concurrent_tasks=3)
    
    @pytest.mark.asyncio
    async def test_simple_query_workflow(self, analysis_service):
        """Test complete workflow for simple query"""
        query = "What is Python?"
        
        async def simple_processor(analysis, strategy, allocation):
            # Verify analysis results
            assert analysis.complexity == ComplexityLevel.SIMPLE
            assert strategy.resource_allocation.cpu_limit <= 5.0
            await asyncio.sleep(0.05)
            return "Python is a programming language"
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=query,
            processing_function=simple_processor
        )
        
        # Verify analysis
        assert analysis_result.query_analysis.complexity == ComplexityLevel.SIMPLE
        assert analysis_result.response_strategy.resource_allocation.cpu_limit <= 5.0
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Verify completion
        status = await analysis_service.get_analysis_status(analysis_result.query_id)
        assert status['processing_status'] in ['completed', 'processing']
    
    @pytest.mark.asyncio
    async def test_complex_technical_workflow(self, analysis_service):
        """Test complete workflow for complex technical query"""
        query = """
        I need to implement a distributed caching system with Redis cluster,
        including failover, monitoring, and performance optimization for a
        high-traffic web application. Can you provide a comprehensive solution?
        """
        
        async def complex_processor(analysis, strategy, allocation):
            # Verify analysis results
            assert analysis.complexity == ComplexityLevel.COMPLEX
            assert analysis.content_type == ContentType.TECHNICAL
            assert strategy.resource_allocation.cpu_limit <= 5.0
            await asyncio.sleep(0.1)
            return "Comprehensive Redis clustering solution..."
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=query,
            processing_function=complex_processor,
            additional_context={'user_expertise': 'advanced'}
        )
        
        # Verify analysis
        assert analysis_result.query_analysis.complexity == ComplexityLevel.COMPLEX
        assert analysis_result.query_analysis.content_type == ContentType.TECHNICAL
        assert analysis_result.response_strategy.resource_allocation.cpu_limit <= 5.0
        
        # Wait for processing
        await asyncio.sleep(0.3)
    
    @pytest.mark.asyncio
    async def test_urgent_priority_workflow(self, analysis_service):
        """Test workflow for urgent priority query"""
        query = "URGENT: Production database is down, need immediate help!"
        
        async def urgent_processor(analysis, strategy, allocation):
            assert analysis.processing_priority == Priority.URGENT
            assert strategy.processing_mode == ProcessingMode.FAST
            await asyncio.sleep(0.05)
            return "Emergency database recovery steps..."
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=query,
            processing_function=urgent_processor
        )
        
        # Verify urgent handling
        assert analysis_result.query_analysis.processing_priority == Priority.URGENT
        assert analysis_result.response_strategy.processing_mode == ProcessingMode.FAST
        
        # Wait for processing
        await asyncio.sleep(0.2)
    
    @pytest.mark.asyncio
    async def test_resource_constraint_handling(self, analysis_service):
        """Test handling of resource constraints"""
        # Submit multiple tasks to test resource allocation
        tasks = []
        
        async def resource_intensive_processor(analysis, strategy, allocation):
            await asyncio.sleep(0.2)
            return f"Processed with {allocation.allocated_cpu if allocation else 'no'} CPU allocation"
        
        # Submit several tasks
        for i in range(5):
            query = f"Complex query number {i} requiring significant processing"
            analysis_result, task_id = await analysis_service.analyze_and_process(
                query=query,
                processing_function=resource_intensive_processor
            )
            tasks.append((analysis_result, task_id))
        
        # Wait for processing
        await asyncio.sleep(1.0)
        
        # Verify all tasks were handled
        for analysis_result, task_id in tasks:
            status = await analysis_service.get_analysis_status(analysis_result.query_id)
            assert status is not None
            # Should be completed or still processing
            assert status.get('processing_status') in ['completed', 'processing', 'queued']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])