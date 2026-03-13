"""
Fallback Chain Manager Demonstration

This script demonstrates the seamless fallback chains with capability preservation
for the Karen AI intelligent fallback system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Set

from .fallback_chain_manager import (
    FallbackChainManager, FallbackStrategy, CapabilityPreservationLevel,
    FallbackConfig, initialize_fallback_chain_manager
)
from .intelligent_provider_registry import get_intelligent_provider_registry
from .capability_aware_selector import get_capability_selector
from .model_availability_cache import get_model_availability_cache, initialize_model_availability_cache
from ..monitoring.network_connectivity import initialize_network_monitoring
from ..monitoring.comprehensive_health_monitor import initialize_comprehensive_health_monitor
from ..monitoring.health_based_decision_maker import initialize_health_decision_maker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_fallback_chains():
    """Demonstrate fallback chain capabilities."""
    logger.info("=== Karen AI Fallback Chain Manager Demo ===")
    
    try:
        # Initialize all system components
        logger.info("Initializing system components...")
        
        # Initialize network monitoring
        network_monitor = initialize_network_monitoring()
        
        # Initialize model availability cache
        model_cache = await initialize_model_availability_cache()
        
        # Initialize comprehensive health monitoring
        health_monitor = await initialize_comprehensive_health_monitor()
        
        # Initialize health-based decision maker
        decision_maker = initialize_health_decision_maker()
        
        # Initialize fallback chain manager
        fallback_config = FallbackConfig(
            enable_predictive_switching=True,
            max_chain_length=4,
            preservation_threshold=0.75,
            enable_hot_switching=True,
            optimization_interval=30.0
        )
        
        fallback_manager = await initialize_fallback_chain_manager(fallback_config)
        
        logger.info("All components initialized successfully!")
        
        # Demonstrate different fallback scenarios
        await demo_basic_fallback_creation(fallback_manager)
        await demo_capability_preservation(fallback_manager)
        await demo_predictive_switching(fallback_manager)
        await demo_analytics_and_optimization(fallback_manager)
        
        logger.info("=== Demo completed successfully ===")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        # Cleanup
        try:
            if 'fallback_manager' in locals():
                await fallback_manager.stop_monitoring()
            if 'health_monitor' in locals():
                await health_monitor.stop_monitoring()
            if 'model_cache' in locals():
                await model_cache.stop_preloading()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def demo_basic_fallback_creation(manager: FallbackChainManager):
    """Demonstrate basic fallback chain creation."""
    logger.info("\n--- Demo: Basic Fallback Chain Creation ---")
    
    # Create fallback chain for chat context
    required_capabilities = {'text', 'conversation'}
    
    chain = manager.create_fallback_chain(
        context='chat',
        primary_provider='openai',
        required_capabilities=required_capabilities,
        strategy=FallbackStrategy.ADAPTIVE,
        preservation_level=CapabilityPreservationLevel.FULL
    )
    
    logger.info(f"Created fallback chain: {chain.chain_id}")
    logger.info(f"Context: {chain.context}")
    logger.info(f"Primary provider: {chain.primary_provider}")
    logger.info(f"Strategy: {chain.strategy.value}")
    logger.info(f"Preservation level: {chain.preservation_level.value}")
    logger.info(f"Required capabilities: {chain.required_capabilities}")
    logger.info(f"Fallback steps: {len(chain.fallback_steps)}")
    
    for i, step in enumerate(chain.fallback_steps):
        logger.info(f"  Step {i+1}: {step.provider_name} "
                   f"(priority: {step.priority}, "
                   f"preservation: {step.preservation_level.value}, "
                   f"latency: {step.estimated_latency:.3f}s)")


async def demo_capability_preservation(manager: FallbackChainManager):
    """Demonstrate capability preservation during fallback."""
    logger.info("\n--- Demo: Capability Preservation ---")
    
    # Create chain with complex capabilities
    required_capabilities = {'text', 'code', 'analysis'}
    
    chain = manager.create_fallback_chain(
        context='code_analysis',
        primary_provider='openai',
        required_capabilities=required_capabilities,
        preservation_level=CapabilityPreservationLevel.PARTIAL
    )
    
    logger.info(f"Chain created with partial preservation: {chain.chain_id}")
    
    # Demonstrate context bridging
    test_context = {
        'code_language': 'python',
        'analysis_type': 'performance',
        'framework': 'django',
        'optimization_level': 'advanced'
    }
    
    logger.info(f"Original context: {test_context}")
    
    for i, step in enumerate(chain.fallback_steps[:2]):  # Show first 2 steps
        if step.context_bridge:
            bridged_context = step.context_bridge.bridge_context(test_context.copy())
            logger.info(f"Step {i+1} ({step.provider_name}) context bridge:")
            logger.info(f"  Capability mappings: {step.context_bridge.capability_mappings}")
            logger.info(f"  Preservation score: {step.context_bridge.preservation_score:.3f}")
            logger.info(f"  Bridged context keys: {list(bridged_context.keys())}")
        else:
            logger.info(f"Step {i+1} ({step.provider_name}): No context bridge needed")


async def demo_predictive_switching(manager: FallbackChainManager):
    """Demonstrate predictive switching capabilities."""
    logger.info("\n--- Demo: Predictive Switching ---")
    
    # Create chain with predictive strategy
    chain = manager.create_fallback_chain(
        context='realtime_chat',
        primary_provider='openai',
        required_capabilities={'text', 'conversation'},
        strategy=FallbackStrategy.PREDICTIVE
    )
    
    logger.info(f"Predictive chain created: {chain.chain_id}")
    
    # Simulate multiple requests to show predictive behavior
    for i in range(3):
        request_data = {
            'request_id': f'predictive_demo_{i}',
            'prompt': f'Predictive test message {i}',
            'timestamp': time.time(),
            'priority': 'normal'
        }
        
        context = {
            'user_id': 'demo_user',
            'session_id': 'demo_session',
            'message_index': i
        }
        
        logger.info(f"Executing request {i+1}...")
        result = await manager.execute_fallback_chain(
            chain.chain_id, request_data, context
        )
        
        logger.info(f"  Result: {result.success}")
        logger.info(f"  Provider: {result.original_provider} -> {result.final_provider}")
        logger.info(f"  Switches: {result.switches_performed}")
        logger.info(f"  Time: {result.total_time:.3f}s")
        logger.info(f"  Triggers: {[t.name for t in result.switch_triggers]}")
        
        # Small delay between requests
        await asyncio.sleep(1.0)


async def demo_analytics_and_optimization(manager: FallbackChainManager):
    """Demonstrate analytics and optimization features."""
    logger.info("\n--- Demo: Analytics and Optimization ---")
    
    # Create multiple chains for different contexts
    contexts = [
        ('chat', {'text', 'conversation'}),
        ('code', {'text', 'code'}),
        ('analysis', {'text', 'analysis'}),
        ('embedding', {'embeddings'})
    ]
    
    chains = []
    for context, capabilities in contexts:
        chain = manager.create_fallback_chain(
            context=context,
            primary_provider='openai',
            required_capabilities=capabilities,
            strategy=FallbackStrategy.ADAPTIVE
        )
        chains.append(chain)
        logger.info(f"Created chain for {context}: {chain.chain_id}")
    
    # Execute some requests to generate analytics data
    logger.info("Generating analytics data...")
    
    for round_num in range(2):
        logger.info(f"Analytics round {round_num + 1}")
        
        for chain in chains:
            for i in range(2):
                request_data = {
                    'request_id': f'analytics_{round_num}_{chain.context}_{i}',
                    'prompt': f'Analytics test for {chain.context}',
                    'round': round_num
                }
                
                result = await manager.execute_fallback_chain(
                    chain.chain_id, request_data
                )
                
                logger.debug(f"  {chain.context}: {result.final_provider} "
                           f"({result.total_time:.3f}s)")
        
        # Wait for potential optimization
        await asyncio.sleep(2.0)
    
    # Get comprehensive analytics
    analytics = manager.get_chain_analytics()
    metrics = manager.get_fallback_metrics()
    
    logger.info("\n--- Analytics Results ---")
    logger.info(f"Total chains: {analytics['total_chains']}")
    logger.info(f"Total fallbacks: {metrics.total_fallbacks}")
    logger.info(f"Success rate: {analytics['metrics']['success_rate']:.3f}")
    logger.info(f"Average switch time: {analytics['metrics']['average_switch_time']:.3f}s")
    logger.info(f"Average preservation score: {metrics.average_preservation_score:.3f}")
    
    logger.info("\nContext distribution:")
    for context, count in analytics['context_distribution'].items():
        logger.info(f"  {context}: {count} chains")
    
    logger.info("\nStrategy distribution:")
    for strategy, count in analytics['strategy_distribution'].items():
        logger.info(f"  {strategy}: {count} chains")
    
    if analytics['chain_usage']:
        logger.info("\nTop used chains:")
        sorted_chains = sorted(analytics['chain_usage'].items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        for chain_id, usage in sorted_chains:
            logger.info(f"  {chain_id}: {usage} uses")
    
    if analytics['provider_switches']:
        logger.info("\nProvider switches:")
        for switch, count in analytics['provider_switches'].items():
            logger.info(f"  {switch}: {count} times")


async def main():
    """Main demonstration function."""
    logger.info("Starting Karen AI Fallback Chain Manager Demonstration")
    logger.info("This demo showcases seamless fallback chains with capability preservation")
    
    await demonstrate_fallback_chains()
    
    logger.info("\n=== Key Features Demonstrated ===")
    logger.info("✓ Intelligent fallback chain creation")
    logger.info("✓ Capability preservation and context bridging")
    logger.info("✓ Predictive switching based on health monitoring")
    logger.info("✓ Comprehensive analytics and optimization")
    logger.info("✓ Integration with existing system components")
    logger.info("✓ Seamless provider switching without interruption")
    logger.info("✓ Multiple fallback strategies and preservation levels")
    
    logger.info("\n=== Integration Points ===")
    logger.info("• Network connectivity monitoring")
    logger.info("• Intelligent provider registry")
    logger.info("• Capability-aware provider selection")
    logger.info("• Model availability caching")
    logger.info("• Comprehensive health monitoring")
    logger.info("• Health-based decision making")
    
    logger.info("\nDemo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())