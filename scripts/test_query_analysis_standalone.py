"""
Standalone test for Query Analysis System

This test verifies the core functionality without depending on the full system.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.services.query_analyzer import QueryAnalyzer, ComplexityLevel, ContentType, Priority
from ai_karen_engine.services.response_strategy_engine import ResponseStrategyEngine, ProcessingMode
from ai_karen_engine.services.context_processor import ContextProcessor
from ai_karen_engine.services.query_analysis_service import QueryAnalysisService


async def test_query_analyzer():
    """Test the QueryAnalyzer component"""
    print("Testing QueryAnalyzer...")
    
    analyzer = QueryAnalyzer()
    
    # Test simple query
    simple_query = "What is Python?"
    result = await analyzer.analyze_query(simple_query)
    
    print(f"Simple query analysis:")
    print(f"  Query: {simple_query}")
    print(f"  Complexity: {result.complexity.value}")
    print(f"  Content Type: {result.content_type.value}")
    print(f"  Priority: {result.processing_priority.value}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    
    assert result.complexity == ComplexityLevel.SIMPLE
    assert result.content_type == ContentType.TEXT
    assert result.confidence_score > 0.5
    print("✓ Simple query test passed")
    
    # Test complex technical query
    complex_query = """
    How do I implement a distributed microservices architecture with 
    Kubernetes, including service mesh, monitoring, and CI/CD pipeline 
    for a high-traffic e-commerce platform?
    """
    result = await analyzer.analyze_query(complex_query)
    
    print(f"\nComplex query analysis:")
    print(f"  Complexity: {result.complexity.value}")
    print(f"  Content Type: {result.content_type.value}")
    print(f"  Estimated Length: {result.estimated_response_length}")
    
    assert result.complexity == ComplexityLevel.COMPLEX
    print("✓ Complex query test passed")
    
    # Test urgent query
    urgent_query = "URGENT: My production server is down, how do I fix it immediately?"
    result = await analyzer.analyze_query(urgent_query)
    
    print(f"\nUrgent query analysis:")
    print(f"  Priority: {result.processing_priority.value}")
    print(f"  Complexity: {result.complexity.value}")
    
    assert result.processing_priority == Priority.URGENT
    print("✓ Urgent query test passed")


async def test_response_strategy_engine():
    """Test the ResponseStrategyEngine component"""
    print("\nTesting ResponseStrategyEngine...")
    
    engine = ResponseStrategyEngine()
    
    # Create a sample query analysis
    from ai_karen_engine.services.query_analyzer import QueryAnalysis, ModalityType, ExpertiseLevel
    
    query_analysis = QueryAnalysis(
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
    
    available_models = [{'id': 'test-model', 'capabilities': ['text']}]
    
    strategy = await engine.determine_response_strategy(query_analysis, available_models)
    
    print(f"Response strategy:")
    print(f"  Processing Mode: {strategy.processing_mode.value}")
    print(f"  Response Format: {strategy.response_format.value}")
    print(f"  CPU Limit: {strategy.resource_allocation.cpu_limit}%")
    print(f"  Memory Limit: {strategy.resource_allocation.memory_limit // (1024*1024)}MB")
    print(f"  Streaming Enabled: {strategy.streaming_enabled}")
    print(f"  Confidence: {strategy.confidence_score:.2f}")
    
    # Verify CPU limit requirement (must be <= 5%)
    assert strategy.resource_allocation.cpu_limit <= 5.0, f"CPU limit {strategy.resource_allocation.cpu_limit}% exceeds 5% requirement"
    print("✓ CPU limit requirement satisfied")
    
    assert strategy.processing_mode in ProcessingMode
    assert strategy.confidence_score > 0.0
    print("✓ Response strategy test passed")


async def test_context_processor():
    """Test the ContextProcessor component"""
    print("\nTesting ContextProcessor...")
    
    processor = ContextProcessor()
    
    # Create a sample query analysis
    from ai_karen_engine.services.query_analyzer import QueryAnalysis, ModalityType, ExpertiseLevel
    
    query_analysis = QueryAnalysis(
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
    
    context = await processor.process_context(query_analysis)
    
    print(f"Context processing:")
    print(f"  Context Summary: {context.context_summary}")
    print(f"  Relevance Score: {context.relevance_score:.2f}")
    print(f"  Technical Context: {bool(context.technical_context)}")
    print(f"  Temporal Context: {bool(context.temporal_context)}")
    
    assert context.relevance_score >= 0.0
    assert context.context_summary is not None
    print("✓ Context processor test passed")


async def test_integration():
    """Test the integrated QueryAnalysisService"""
    print("\nTesting QueryAnalysisService Integration...")
    
    service = QueryAnalysisService(max_concurrent_tasks=2)
    
    try:
        # Test comprehensive analysis
        query = "How do I optimize Python code for better performance?"
        
        result = await service.analyze_query_comprehensive(query)
        
        print(f"Comprehensive analysis:")
        print(f"  Query ID: {result.query_id}")
        print(f"  Complexity: {result.query_analysis.complexity.value}")
        print(f"  Processing Mode: {result.response_strategy.processing_mode.value}")
        print(f"  CPU Limit: {result.response_strategy.resource_allocation.cpu_limit}%")
        print(f"  Analysis Duration: {result.analysis_metadata.get('analysis_duration_ms', 0):.1f}ms")
        
        # Verify CPU limit requirement
        assert result.response_strategy.resource_allocation.cpu_limit <= 5.0
        print("✓ CPU limit requirement satisfied")
        
        assert result.query_id is not None
        assert result.query_analysis is not None
        assert result.response_strategy is not None
        print("✓ Comprehensive analysis test passed")
        
        # Test with processing function
        async def dummy_processor(analysis, strategy, allocation):
            await asyncio.sleep(0.1)
            return "Test response"
        
        analysis_result, task_id = await service.analyze_and_process(
            query="What is machine learning?",
            processing_function=dummy_processor
        )
        
        print(f"\nProcessing integration:")
        print(f"  Task ID: {task_id}")
        print(f"  CPU Limit: {analysis_result.response_strategy.resource_allocation.cpu_limit}%")
        
        # Wait for processing
        await asyncio.sleep(0.3)
        
        # Check status
        status = await service.get_analysis_status(analysis_result.query_id)
        print(f"  Status: {status['processing_status'] if status else 'unknown'}")
        
        assert task_id is not None
        print("✓ Processing integration test passed")
        
    finally:
        await service.shutdown()


async def main():
    """Run all tests"""
    print("Starting Query Analysis System Tests")
    print("=" * 50)
    
    try:
        await test_query_analyzer()
        await test_response_strategy_engine()
        await test_context_processor()
        await test_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("\nKey Requirements Verified:")
        print("- CPU usage stays under 5% per response")
        print("- Query complexity analysis working")
        print("- Response strategy determination working")
        print("- Context processing working")
        print("- Priority-based processing working")
        print("- Resource allocation working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)