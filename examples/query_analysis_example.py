"""
Query Analysis System Example

This example demonstrates how to use the query analysis and response strategy
system for intelligent response optimization.
"""

import asyncio
import logging
from typing import Dict, Any

from src.ai_karen_engine.services.query_analysis_service import QueryAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_processing_function(query_analysis, response_strategy, resource_allocation):
    """
    Example processing function that simulates response generation
    """
    logger.info(f"Processing query with complexity: {query_analysis.complexity.value}")
    logger.info(f"Using processing mode: {response_strategy.processing_mode.value}")
    logger.info(f"CPU allocation: {resource_allocation.allocated_cpu if resource_allocation else 'N/A'}%")
    
    # Simulate processing time based on complexity
    processing_time = {
        'simple': 0.5,
        'moderate': 1.5,
        'complex': 3.0
    }.get(query_analysis.complexity.value, 1.0)
    
    await asyncio.sleep(processing_time)
    
    return f"Generated response for {query_analysis.content_type.value} query"


async def completion_callback(task, result):
    """
    Example callback function called when processing completes
    """
    logger.info(f"Task {task.task_id} completed with result: {result}")
    logger.info(f"Processing took: {(task.completed_at - task.started_at).total_seconds():.2f} seconds")


async def main():
    """
    Main example function demonstrating the query analysis system
    """
    logger.info("Starting Query Analysis System Example")
    
    # Initialize the service
    analysis_service = QueryAnalysisService(max_concurrent_tasks=3)
    
    try:
        # Example 1: Simple query
        logger.info("\n=== Example 1: Simple Query ===")
        simple_query = "What is Python?"
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=simple_query,
            processing_function=example_processing_function,
            callback=completion_callback,
            metadata={'example': 'simple_query'}
        )
        
        logger.info(f"Simple query analysis:")
        logger.info(f"  Complexity: {analysis_result.query_analysis.complexity.value}")
        logger.info(f"  Content Type: {analysis_result.query_analysis.content_type.value}")
        logger.info(f"  Priority: {analysis_result.query_analysis.processing_priority.value}")
        logger.info(f"  CPU Limit: {analysis_result.response_strategy.resource_allocation.cpu_limit}%")
        logger.info(f"  Task ID: {task_id}")
        
        # Example 2: Complex technical query
        logger.info("\n=== Example 2: Complex Technical Query ===")
        complex_query = """
        I need to design a scalable microservices architecture for an e-commerce platform
        that can handle 1 million concurrent users. The system should include:
        - API Gateway with rate limiting
        - Service mesh for inter-service communication
        - Distributed caching with Redis
        - Event-driven architecture with Kafka
        - Monitoring and observability
        - CI/CD pipeline with automated testing
        Can you provide a comprehensive solution with code examples?
        """
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=complex_query,
            processing_function=example_processing_function,
            callback=completion_callback,
            user_id="expert_user_123",
            additional_context={
                'user_expertise': 'advanced',
                'system_resources': {
                    'cpu_usage': 45.0,
                    'memory_usage': 60.0,
                    'gpu_available': True
                }
            },
            metadata={'example': 'complex_technical'}
        )
        
        logger.info(f"Complex query analysis:")
        logger.info(f"  Complexity: {analysis_result.query_analysis.complexity.value}")
        logger.info(f"  Content Type: {analysis_result.query_analysis.content_type.value}")
        logger.info(f"  Expertise Level: {analysis_result.query_analysis.user_expertise_level.value}")
        logger.info(f"  Processing Mode: {analysis_result.response_strategy.processing_mode.value}")
        logger.info(f"  Streaming Enabled: {analysis_result.response_strategy.streaming_enabled}")
        logger.info(f"  CPU Limit: {analysis_result.response_strategy.resource_allocation.cpu_limit}%")
        logger.info(f"  Estimated Time: {analysis_result.response_strategy.estimated_generation_time}s")
        
        # Example 3: Urgent query
        logger.info("\n=== Example 3: Urgent Query ===")
        urgent_query = "URGENT: My production server is down and users can't access the website!"
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=urgent_query,
            processing_function=example_processing_function,
            callback=completion_callback,
            metadata={'example': 'urgent_query'}
        )
        
        logger.info(f"Urgent query analysis:")
        logger.info(f"  Priority: {analysis_result.query_analysis.processing_priority.value}")
        logger.info(f"  Processing Mode: {analysis_result.response_strategy.processing_mode.value}")
        logger.info(f"  CPU Limit: {analysis_result.response_strategy.resource_allocation.cpu_limit}%")
        
        # Example 4: Code-related query
        logger.info("\n=== Example 4: Code Query ===")
        code_query = """
        def bubble_sort(arr):
            n = len(arr)
            for i in range(n):
                for j in range(0, n-i-1):
                    if arr[j] > arr[j+1]:
                        arr[j], arr[j+1] = arr[j+1], arr[j]
            return arr
        
        How can I optimize this sorting algorithm?
        """
        
        analysis_result, task_id = await analysis_service.analyze_and_process(
            query=code_query,
            processing_function=example_processing_function,
            callback=completion_callback,
            metadata={'example': 'code_query'}
        )
        
        logger.info(f"Code query analysis:")
        logger.info(f"  Content Type: {analysis_result.query_analysis.content_type.value}")
        logger.info(f"  Requires Code Execution: {analysis_result.query_analysis.requires_code_execution}")
        logger.info(f"  Response Format: {analysis_result.response_strategy.response_format.value}")
        
        # Wait for all processing to complete
        logger.info("\n=== Waiting for Processing to Complete ===")
        await asyncio.sleep(5)
        
        # Show system metrics
        logger.info("\n=== System Metrics ===")
        metrics = await analysis_service.get_system_metrics()
        logger.info(f"Analysis cache size: {metrics['analysis_cache_size']}")
        logger.info(f"Active analyses: {metrics['active_analyses']}")
        
        if 'processing_queues' in metrics:
            queue_info = metrics['processing_queues']
            logger.info(f"Active tasks: {queue_info['active_tasks']}")
            logger.info(f"Total completed: {queue_info['total_completed']}")
        
        # Demonstrate optimization
        logger.info("\n=== System Optimization ===")
        optimization_result = await analysis_service.optimize_system_performance()
        logger.info(f"Optimizations applied: {len(optimization_result['optimizations_applied'])}")
        for optimization in optimization_result['optimizations_applied']:
            logger.info(f"  - {optimization}")
        
        # Example 5: Batch processing multiple queries
        logger.info("\n=== Example 5: Batch Processing ===")
        batch_queries = [
            "How do I install Python?",
            "What are the best practices for REST API design?",
            "Explain machine learning algorithms",
            "How to optimize database queries?",
            "What is Docker and how do I use it?"
        ]
        
        batch_tasks = []
        for i, query in enumerate(batch_queries):
            analysis_result, task_id = await analysis_service.analyze_and_process(
                query=query,
                processing_function=example_processing_function,
                metadata={'example': 'batch_processing', 'batch_index': i}
            )
            batch_tasks.append((query, analysis_result, task_id))
            logger.info(f"Submitted batch query {i+1}: {analysis_result.query_analysis.complexity.value} complexity")
        
        # Wait for batch processing
        await asyncio.sleep(3)
        
        # Check status of batch tasks
        logger.info("\n=== Batch Processing Results ===")
        for query, analysis_result, task_id in batch_tasks:
            status = await analysis_service.get_analysis_status(analysis_result.query_id)
            if status:
                logger.info(f"Query: '{query[:50]}...' - Status: {status.get('processing_status', 'unknown')}")
        
        logger.info("\n=== Example Complete ===")
        
    except Exception as e:
        logger.error(f"Error in example: {e}")
        raise
    
    finally:
        # Shutdown the service
        await analysis_service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())