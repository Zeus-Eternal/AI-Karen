"""
Error Handling and Graceful Degradation Example

This example demonstrates the comprehensive error handling and graceful
degradation system, showing how it handles various error scenarios and
maintains system functionality.
"""

import asyncio
import logging
import time
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import error handling components
from src.ai_karen_engine.services.graceful_degradation_coordinator import (
    graceful_degradation_coordinator,
    DegradationContext,
    SystemHealthStatus,
    DegradationLevel
)
from src.ai_karen_engine.services.error_recovery_system import (
    error_recovery_system,
    ErrorContext,
    ErrorType
)
from src.ai_karen_engine.services.model_availability_handler import (
    model_availability_handler
)
from src.ai_karen_engine.services.memory_exhaustion_handler import (
    memory_exhaustion_handler
)
from src.ai_karen_engine.services.streaming_interruption_handler import (
    streaming_interruption_handler
)

from src.ai_karen_engine.core.types.shared_types import (
    Modality, ModalityType
)


async def demonstrate_system_health_monitoring():
    """Demonstrate system health monitoring and assessment."""
    print("\n" + "="*60)
    print("SYSTEM HEALTH MONITORING DEMONSTRATION")
    print("="*60)
    
    # Assess current system health
    health_report = await graceful_degradation_coordinator.assess_system_health()
    
    print(f"Overall Status: {health_report.overall_status.value}")
    print(f"Degradation Level: {health_report.degradation_level.value}")
    print(f"Available Models: {health_report.available_models}")
    print(f"Unavailable Models: {health_report.unavailable_models}")
    print(f"Memory Pressure: {health_report.memory_pressure.value}")
    print(f"Active Recoveries: {health_report.active_recoveries}")
    
    if health_report.recommendations:
        print("\nRecommendations:")
        for rec in health_report.recommendations:
            print(f"  - {rec}")
    
    return health_report


async def demonstrate_model_availability_handling():
    """Demonstrate model availability checking and fallback mechanisms."""
    print("\n" + "="*60)
    print("MODEL AVAILABILITY HANDLING DEMONSTRATION")
    print("="*60)
    
    # Test model availability
    test_models = ["tinyllama", "gpt-3.5-turbo", "nonexistent-model"]
    
    for model_id in test_models:
        print(f"\nChecking availability of model: {model_id}")
        
        health_check = await model_availability_handler.check_model_availability(model_id)
        
        print(f"  Status: {health_check.status.value}")
        print(f"  Response Time: {health_check.response_time:.3f}s")
        
        if health_check.error_message:
            print(f"  Error: {health_check.error_message}")
        
        if health_check.load_percentage > 0:
            print(f"  Load: {health_check.load_percentage:.1f}%")
    
    # Demonstrate fallback model finding
    print(f"\nFinding fallback models for failed model 'nonexistent-model':")
    
    from src.ai_karen_engine.services.model_availability_handler import ModalityRequirement
    
    modality_requirements = [
        ModalityRequirement(
            modality_type=ModalityType.TEXT,
            input_required=True,
            output_required=True
        )
    ]
    
    fallback_candidates = await model_availability_handler.find_fallback_models(
        failed_model_id="nonexistent-model",
        modality_requirements=modality_requirements,
        max_candidates=3
    )
    
    for i, candidate in enumerate(fallback_candidates, 1):
        print(f"  {i}. {candidate.model_info.id}")
        print(f"     Compatibility: {candidate.compatibility_score:.2f}")
        print(f"     Performance: {candidate.estimated_performance:.2f}")
        print(f"     Availability: {candidate.availability_score:.2f}")


async def demonstrate_memory_exhaustion_handling():
    """Demonstrate memory exhaustion detection and recovery."""
    print("\n" + "="*60)
    print("MEMORY EXHAUSTION HANDLING DEMONSTRATION")
    print("="*60)
    
    # Monitor current memory status
    memory_status = await memory_exhaustion_handler.monitor_memory_status()
    
    print(f"Current Memory Usage: {memory_status.usage_percentage:.1f}%")
    print(f"Pressure Level: {memory_status.pressure_level.value}")
    print(f"Available Memory: {memory_status.available_memory / (1024**3):.2f} GB")
    print(f"Used Memory: {memory_status.used_memory / (1024**3):.2f} GB")
    
    # Simulate memory exhaustion scenario
    print(f"\nSimulating memory exhaustion recovery...")
    
    test_query = "Complex query that requires significant memory resources for processing"
    recovery_result = await memory_exhaustion_handler.handle_memory_exhaustion(test_query)
    
    print(f"Recovery Success: {recovery_result.success}")
    print(f"Memory Freed: {recovery_result.memory_freed / (1024**2):.1f} MB")
    print(f"Recovery Time: {recovery_result.recovery_time:.2f}s")
    
    if recovery_result.optimizations_applied:
        print(f"\nOptimizations Applied:")
        for opt in recovery_result.optimizations_applied:
            print(f"  - {opt.strategy.value}: {opt.description}")
            if opt.success:
                print(f"    Saved: {opt.actual_savings / (1024**2):.1f} MB")
    
    if recovery_result.fallback_response:
        print(f"\nFallback Response Generated:")
        print(f"  {recovery_result.fallback_response[:100]}...")


async def demonstrate_streaming_interruption_handling():
    """Demonstrate streaming interruption recovery."""
    print("\n" + "="*60)
    print("STREAMING INTERRUPTION HANDLING DEMONSTRATION")
    print("="*60)
    
    # Simulate streaming session with interruption
    session_id = "demo_session_001"
    test_query = "Generate a comprehensive response about artificial intelligence"
    
    print(f"Starting streaming session: {session_id}")
    
    try:
        async with streaming_interruption_handler.streaming_session(
            session_id=session_id,
            query=test_query,
            model_id="demo-model"
        ) as session:
            
            # Simulate partial content delivery
            partial_content = "Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines..."
            
            # Create checkpoint
            checkpoint = await streaming_interruption_handler.create_checkpoint(
                session_id=session_id,
                content_delivered=partial_content,
                content_remaining="[Remaining content would continue here...]",
                stream_position=len(partial_content)
            )
            
            print(f"Created checkpoint: {checkpoint.checkpoint_id}")
            print(f"Content delivered: {len(partial_content)} characters")
            
            # Simulate interruption
            raise Exception("Simulated streaming interruption")
            
    except Exception as e:
        print(f"Streaming interrupted: {str(e)}")
        
        # The context manager should handle recovery automatically
        print("Streaming interruption was handled by the recovery system")
    
    # Get recovery statistics
    recovery_stats = await streaming_interruption_handler.get_recovery_statistics()
    print(f"\nRecovery Statistics:")
    print(f"  Active Streams: {recovery_stats['active_streams']}")
    print(f"  Total Checkpoints: {recovery_stats['total_checkpoints']}")


async def demonstrate_coordinated_error_recovery():
    """Demonstrate coordinated error recovery across all components."""
    print("\n" + "="*60)
    print("COORDINATED ERROR RECOVERY DEMONSTRATION")
    print("="*60)
    
    # Test different error scenarios
    error_scenarios = [
        {
            "name": "Model Unavailable",
            "error": Exception("Model 'advanced-model' is not available"),
            "query": "Analyze this complex dataset",
            "model_id": "advanced-model"
        },
        {
            "name": "Memory Exhaustion",
            "error": MemoryError("Out of memory during processing"),
            "query": "Process large document with detailed analysis",
            "model_id": "large-model"
        },
        {
            "name": "Timeout Error",
            "error": asyncio.TimeoutError("Request timeout after 30 seconds"),
            "query": "Generate comprehensive report",
            "model_id": "slow-model"
        },
        {
            "name": "Connection Failure",
            "error": ConnectionError("Connection to model server lost"),
            "query": "Simple text generation task",
            "model_id": "remote-model"
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\n--- Testing {scenario['name']} ---")
        
        start_time = time.time()
        
        try:
            response = await graceful_degradation_coordinator.handle_coordinated_recovery(
                query=scenario["query"],
                error=scenario["error"],
                model_id=scenario["model_id"]
            )
            
            recovery_time = time.time() - start_time
            
            print(f"Recovery Status: SUCCESS")
            print(f"Recovery Time: {recovery_time:.2f}s")
            print(f"Degradation Level: {response.degradation_level.value}")
            print(f"Model Used: {response.model_used or 'Emergency Response'}")
            print(f"Fallback Applied: {response.fallback_applied}")
            print(f"Quality Score: {response.quality_score:.2f}")
            
            if response.optimizations_applied:
                print(f"Optimizations: {', '.join(response.optimizations_applied)}")
            
            if response.warnings:
                print(f"Warnings: {len(response.warnings)} warning(s)")
            
            print(f"Response Preview: {response.content[:100]}...")
            
        except Exception as e:
            print(f"Recovery Status: FAILED - {str(e)}")


async def demonstrate_graceful_execution_context():
    """Demonstrate graceful execution context for automatic error handling."""
    print("\n" + "="*60)
    print("GRACEFUL EXECUTION CONTEXT DEMONSTRATION")
    print("="*60)
    
    # Create degradation context
    context = DegradationContext(
        query="Test query with automatic error handling",
        requested_model="test-model",
        required_modalities=[
            Modality(
                type=ModalityType.TEXT,
                input_supported=True,
                output_supported=True
            )
        ],
        user_priority=1,
        timeout_tolerance=15.0,
        quality_tolerance=0.7,
        allow_fallback=True,
        allow_degradation=True
    )
    
    print("Testing graceful execution with successful operation...")
    
    # Test successful execution
    async with graceful_degradation_coordinator.graceful_execution(context) as exec_context:
        print(f"Executing with context: {exec_context.query[:50]}...")
        await asyncio.sleep(0.1)  # Simulate work
        print("Operation completed successfully")
    
    print("\nTesting graceful execution with error handling...")
    
    # Test execution with error
    try:
        async with graceful_degradation_coordinator.graceful_execution(context) as exec_context:
            print(f"Executing with context: {exec_context.query[:50]}...")
            await asyncio.sleep(0.1)  # Simulate work
            raise Exception("Simulated operation failure")
    except Exception as e:
        print(f"Error was handled gracefully: {str(e)}")


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring and optimization recommendations."""
    print("\n" + "="*60)
    print("PERFORMANCE MONITORING DEMONSTRATION")
    print("="*60)
    
    from src.ai_karen_engine.services.timeout_performance_handler import (
        timeout_performance_handler
    )
    
    # Monitor performance for a simulated operation
    model_id = "demo-model"
    operation_type = "inference"
    
    print(f"Monitoring performance for {model_id}...")
    
    start_time = time.time()
    await asyncio.sleep(0.5)  # Simulate operation
    end_time = time.time()
    
    # Record performance metrics
    metrics = await timeout_performance_handler.monitor_performance(
        model_id=model_id,
        operation_type=operation_type,
        start_time=start_time,
        end_time=end_time
    )
    
    print(f"Performance Metrics:")
    print(f"  Response Time: {metrics.response_time:.3f}s")
    print(f"  CPU Usage: {metrics.cpu_usage:.1f}%")
    print(f"  Memory Usage: {metrics.memory_usage:.1f}%")
    print(f"  Model Efficiency: {metrics.model_efficiency:.2f}")
    
    if metrics.gpu_usage is not None:
        print(f"  GPU Usage: {metrics.gpu_usage:.1f}%")
    
    # Get performance recommendations
    recommendations = await timeout_performance_handler.get_performance_recommendations(model_id)
    
    if recommendations:
        print(f"\nPerformance Recommendations:")
        for rec in recommendations:
            print(f"  - {rec['type']}: {rec['description']}")
            print(f"    Priority: {rec['priority']}")
            print(f"    Current: {rec['current_value']:.2f}, Threshold: {rec['threshold']:.2f}")


async def demonstrate_system_status_overview():
    """Demonstrate comprehensive system status overview."""
    print("\n" + "="*60)
    print("SYSTEM STATUS OVERVIEW")
    print("="*60)
    
    # Get comprehensive system status
    status = await graceful_degradation_coordinator.get_system_status()
    
    print("Health Report:")
    health = status["health_report"]
    print(f"  Overall Status: {health['overall_status']}")
    print(f"  Degradation Level: {health['degradation_level']}")
    print(f"  Available Models: {len(health['available_models'])}")
    print(f"  Unavailable Models: {len(health['unavailable_models'])}")
    print(f"  Memory Pressure: {health['memory_pressure']}")
    print(f"  Active Recoveries: {health['active_recoveries']}")
    
    print("\nDegradation Statistics:")
    stats = status["degradation_stats"]
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Degraded Requests: {stats['degraded_requests']}")
    print(f"  Fallback Requests: {stats['fallback_requests']}")
    print(f"  Emergency Responses: {stats['emergency_responses']}")
    print(f"  Average Degradation Level: {stats['average_degradation_level']:.2f}")
    
    print("\nComponent Status:")
    components = status["component_status"]
    for component, status_val in components.items():
        print(f"  {component}: {status_val}")


async def main():
    """Main demonstration function."""
    print("ERROR HANDLING AND GRACEFUL DEGRADATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    try:
        # Run all demonstrations
        await demonstrate_system_health_monitoring()
        await demonstrate_model_availability_handling()
        await demonstrate_memory_exhaustion_handling()
        await demonstrate_streaming_interruption_handling()
        await demonstrate_coordinated_error_recovery()
        await demonstrate_graceful_execution_context()
        await demonstrate_performance_monitoring()
        await demonstrate_system_status_overview()
        
        print("\n" + "="*80)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\nKey Features Demonstrated:")
        print("✓ System health monitoring and assessment")
        print("✓ Model availability checking and fallback mechanisms")
        print("✓ Memory exhaustion detection and recovery")
        print("✓ Streaming interruption handling with checkpoints")
        print("✓ Coordinated error recovery across all components")
        print("✓ Graceful execution context with automatic error handling")
        print("✓ Performance monitoring and optimization recommendations")
        print("✓ Comprehensive system status reporting")
        
        print("\nThe error handling system provides:")
        print("• Comprehensive error recovery for all failure modes")
        print("• Graceful degradation that maintains functionality")
        print("• Intelligent fallback mechanisms with modality consideration")
        print("• Automatic optimization adjustments for resource constraints")
        print("• Streaming interruption recovery with partial response handling")
        print("• Performance monitoring and adaptive timeout handling")
        print("• Coordinated recovery across all system components")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {str(e)}")
        print(f"\nDemonstration encountered an error: {str(e)}")
        print("This demonstrates the need for robust error handling!")


if __name__ == "__main__":
    asyncio.run(main())