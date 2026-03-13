"""
Test scenarios for Fallback Chain Manager

This module demonstrates the seamless fallback chain implementation with
capability preservation for the Karen AI intelligent fallback system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Set

from .fallback_chain_manager import (
    FallbackChainManager, FallbackStrategy, CapabilityPreservationLevel,
    FallbackConfig, get_fallback_chain_manager, initialize_fallback_chain_manager
)
from .intelligent_provider_registry import (
    IntelligentProviderRegistry, ProviderType, ProviderPriority,
    IntelligentProviderRegistration, ProviderMetrics
)
from .provider_registry import ProviderRegistration, ModelInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockProvider:
    """Mock provider for testing."""
    
    def __init__(self, name: str, reliability: float = 1.0, latency: float = 0.1):
        self.name = name
        self.reliability = reliability
        self.latency = latency
        self.request_count = 0
        self.failure_rate = 1.0 - reliability
    
    async def process_request(self, request_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request with simulated reliability."""
        self.request_count += 1
        
        # Simulate processing time
        await asyncio.sleep(self.latency)
        
        # Simulate failures based on reliability
        import random
        if random.random() < self.failure_rate:
            return {
                'success': False,
                'error': f"Provider {self.name} failed randomly",
                'request_id': request_data.get('request_id', 'unknown')
            }
        
        return {
            'success': True,
            'response': f"Response from {self.name}",
            'request_id': request_data.get('request_id', 'unknown'),
            'processing_time': self.latency
        }


async def setup_test_providers(registry: IntelligentProviderRegistry) -> None:
    """Setup mock providers for testing."""
    
    # Create mock providers with different characteristics
    providers = [
        {
            'name': 'openai_gpt4',
            'type': ProviderType.CLOUD,
            'priority': ProviderPriority.PREFERRED,
            'reliability': 0.95,
            'latency': 0.5,
            'capabilities': ['text', 'conversation', 'code', 'analysis'],
            'cost_tier': 'premium'
        },
        {
            'name': 'anthropic_claude',
            'type': ProviderType.CLOUD,
            'priority': ProviderPriority.PREFERRED,
            'reliability': 0.90,
            'latency': 0.7,
            'capabilities': ['text', 'conversation', 'analysis', 'creative'],
            'cost_tier': 'premium'
        },
        {
            'name': 'local_llama',
            'type': ProviderType.LOCAL,
            'priority': ProviderPriority.LOCAL,
            'reliability': 0.85,
            'latency': 0.2,
            'capabilities': ['text', 'conversation'],
            'cost_tier': 'free'
        },
        {
            'name': 'huggingface_model',
            'type': ProviderType.CLOUD,
            'priority': ProviderPriority.STANDARD,
            'reliability': 0.80,
            'latency': 1.0,
            'capabilities': ['text', 'embedding'],
            'cost_tier': 'standard'
        }
    ]
    
    for provider_config in providers:
        # Create provider registration
        models = [
            ModelInfo(
                name=provider_config['name'],
                capabilities=provider_config['capabilities']
            )
        ]
        
        base_registration = ProviderRegistration(
            name=provider_config['name'],
            provider_class=MockProvider,
            description=f"Mock provider {provider_config['name']}",
            models=models,
            requires_api_key=provider_config['type'] == ProviderType.CLOUD,
            default_model=provider_config['name']
        )
        
        # Create intelligent registration with metrics
        metrics = ProviderMetrics(
            success_rate=provider_config['reliability'],
            average_latency=provider_config['latency']
        )
        
        intelligent_reg = IntelligentProviderRegistration(
            base_registration=base_registration,
            provider_type=provider_config['type'],
            priority=provider_config['priority'],
            network_dependent=provider_config['type'] == ProviderType.CLOUD,
            offline_capable=provider_config['type'] == ProviderType.LOCAL,
            cost_tier=provider_config['cost_tier'],
            reliability_score=provider_config['reliability'],
            metrics=metrics
        )
        
        registry.register_intelligent_provider(
            base_registration, provider_config['type'], provider_config['priority']
        )


async def test_basic_fallback_chain() -> None:
    """Test basic fallback chain creation and execution."""
    logger.info("=== Testing Basic Fallback Chain ===")
    
    # Initialize manager
    config = FallbackConfig(
        max_chain_length=3,
        enable_predictive_switching=True,
        preservation_threshold=0.7
    )
    
    manager = get_fallback_chain_manager(config)
    await manager.start_monitoring()
    
    try:
        # Create fallback chain for chat context
        required_capabilities = {'text', 'conversation'}
        chain = manager.create_fallback_chain(
            context='chat',
            primary_provider='openai_gpt4',
            required_capabilities=required_capabilities,
            strategy=FallbackStrategy.ADAPTIVE,
            preservation_level=CapabilityPreservationLevel.FULL
        )
        
        logger.info(f"Created fallback chain: {chain.chain_id}")
        logger.info(f"Primary provider: {chain.primary_provider}")
        logger.info(f"Fallback steps: {[step.provider_name for step in chain.fallback_steps]}")
        
        # Execute request with fallback chain
        request_data = {
            'request_id': 'test_001',
            'prompt': 'Hello, how are you?',
            'max_tokens': 100
        }
        
        context = {
            'user_id': 'user123',
            'session_id': 'session456',
            'conversation_history': []
        }
        
        result = await manager.execute_fallback_chain(
            chain.chain_id, request_data, context
        )
        
        logger.info(f"Execution result:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Original provider: {result.original_provider}")
        logger.info(f"  Final provider: {result.final_provider}")
        logger.info(f"  Switches performed: {result.switches_performed}")
        logger.info(f"  Total time: {result.total_time:.3f}s")
        logger.info(f"  Context preserved: {result.context_preserved}")
        logger.info(f"  Quality maintained: {result.quality_maintained}")
        
        # Get analytics
        analytics = manager.get_chain_analytics()
        logger.info(f"Chain analytics: {analytics}")
        
    finally:
        await manager.stop_monitoring()


async def test_capability_preservation() -> None:
    """Test capability preservation during fallback."""
    logger.info("=== Testing Capability Preservation ===")
    
    manager = get_fallback_chain_manager()
    await manager.start_monitoring()
    
    try:
        # Create chain with specific capabilities
        required_capabilities = {'text', 'code', 'analysis'}
        chain = manager.create_fallback_chain(
            context='code_generation',
            primary_provider='openai_gpt4',
            required_capabilities=required_capabilities,
            preservation_level=CapabilityPreservationLevel.PARTIAL
        )
        
        logger.info(f"Chain created with preservation level: {chain.preservation_level}")
        
        # Check context bridges
        for i, step in enumerate(chain.fallback_steps):
            if step.context_bridge:
                logger.info(f"Step {i+1} context bridge:")
                logger.info(f"  Source: {step.context_bridge.source_provider}")
                logger.info(f"  Target: {step.context_bridge.target_provider}")
                logger.info(f"  Capability mappings: {step.context_bridge.capability_mappings}")
                logger.info(f"  Preservation score: {step.context_bridge.preservation_score}")
        
        # Test context bridging
        test_context = {
            'code_language': 'python',
            'complexity': 'medium',
            'framework': 'django'
        }
        
        for step in chain.fallback_steps:
            if step.context_bridge:
                bridged = step.context_bridge.bridge_context(test_context.copy())
                logger.info(f"Bridged context for {step.provider_name}: {bridged}")
        
    finally:
        await manager.stop_monitoring()


async def test_predictive_switching() -> None:
    """Test predictive switching based on health degradation."""
    logger.info("=== Testing Predictive Switching ===")
    
    config = FallbackConfig(
        enable_predictive_switching=True,
        health_degradation_threshold=0.7,
        performance_degradation_threshold=0.3
    )
    
    manager = get_fallback_chain_manager(config)
    await manager.start_monitoring()
    
    try:
        # Create chain
        chain = manager.create_fallback_chain(
            context='realtime_chat',
            primary_provider='openai_gpt4',
            required_capabilities={'text', 'conversation'},
            strategy=FallbackStrategy.PREDICTIVE
        )
        
        # Simulate multiple requests to trigger predictive checks
        for i in range(5):
            request_data = {
                'request_id': f'predictive_test_{i}',
                'prompt': f'Test message {i}',
                'timestamp': time.time()
            }
            
            result = await manager.execute_fallback_chain(
                chain.chain_id, request_data
            )
            
            logger.info(f"Request {i+1}: {result.final_provider} "
                      f"(switches: {result.switches_performed})")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        # Get metrics
        metrics = manager.get_fallback_metrics()
        logger.info(f"Predictive switching metrics:")
        logger.info(f"  Total fallbacks: {metrics.total_fallbacks}")
        logger.info(f"  Successful fallbacks: {metrics.successful_fallbacks}")
        logger.info(f"  Average switch time: {metrics.average_switch_time:.3f}s")
        
    finally:
        await manager.stop_monitoring()


async def test_graceful_degradation() -> None:
    """Test graceful degradation with minimal capabilities."""
    logger.info("=== Testing Graceful Degradation ===")
    
    manager = get_fallback_chain_manager()
    await manager.start_monitoring()
    
    try:
        # Create chain with minimal preservation
        chain = manager.create_fallback_chain(
            context='emergency_chat',
            primary_provider='openai_gpt4',
            required_capabilities={'text'},
            preservation_level=CapabilityPreservationLevel.MINIMAL
        )
        
        logger.info(f"Emergency chain with minimal preservation: {chain.chain_id}")
        
        # Execute with degraded capabilities
        request_data = {
            'request_id': 'emergency_test',
            'prompt': 'Emergency message',
            'priority': 'high'
        }
        
        result = await manager.execute_fallback_chain(
            chain.chain_id, request_data
        )
        
        logger.info(f"Emergency fallback result:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Preservation level: {result.preservation_level.value}")
        logger.info(f"  Switch triggers: {[t.name for t in result.switch_triggers]}")
        
    finally:
        await manager.stop_monitoring()


async def test_performance_optimization() -> None:
    """Test performance optimization of fallback chains."""
    logger.info("=== Testing Performance Optimization ===")
    
    config = FallbackConfig(
        optimization_interval=5.0,  # Optimize every 5 seconds for testing
        analytics_history_size=50
    )
    
    manager = get_fallback_chain_manager(config)
    await manager.start_monitoring()
    
    try:
        # Create multiple chains
        contexts = ['chat', 'code', 'analysis']
        chains = []
        
        for context in contexts:
            chain = manager.create_fallback_chain(
                context=context,
                primary_provider='openai_gpt4',
                required_capabilities={'text', context}
            )
            chains.append(chain)
        
        # Execute multiple requests to generate optimization data
        for round_num in range(3):
            logger.info(f"Execution round {round_num + 1}")
            
            for chain in chains:
                for i in range(3):
                    request_data = {
                        'request_id': f'opt_{round_num}_{chain.context}_{i}',
                        'prompt': f'Test for {chain.context}',
                        'round': round_num
                    }
                    
                    result = await manager.execute_fallback_chain(
                        chain.chain_id, request_data
                    )
                    
                    logger.debug(f"  {chain.context}: {result.final_provider} "
                               f"({result.total_time:.3f}s)")
            
            # Wait for optimization
            await asyncio.sleep(6.0)
        
        # Get final analytics
        analytics = manager.get_chain_analytics()
        logger.info("Performance optimization results:")
        logger.info(f"  Total chains: {analytics['total_chains']}")
        logger.info(f"  Success rate: {analytics['metrics']['success_rate']:.3f}")
        logger.info(f"  Average switch time: {analytics['metrics']['average_switch_time']:.3f}s")
        logger.info(f"  Context distribution: {analytics['context_distribution']}")
        
    finally:
        await manager.stop_monitoring()


async def test_error_scenarios() -> None:
    """Test various error scenarios and recovery."""
    logger.info("=== Testing Error Scenarios ===")
    
    manager = get_fallback_chain_manager()
    await manager.start_monitoring()
    
    try:
        # Test 1: Provider failure
        logger.info("Test 1: Provider failure simulation")
        chain1 = manager.create_fallback_chain(
            context='failure_test',
            primary_provider='openai_gpt4',
            required_capabilities={'text'}
        )
        
        # Simulate provider failure
        request_data = {
            'request_id': 'failure_test',
            'prompt': 'Test failure',
            'simulate_failure': True
        }
        
        result1 = await manager.execute_fallback_chain(
            chain1.chain_id, request_data
        )
        
        logger.info(f"Failure test result: {result1.success}, "
                  f"final provider: {result1.final_provider}")
        
        # Test 2: Network degradation
        logger.info("Test 2: Network degradation simulation")
        chain2 = manager.create_fallback_chain(
            context='network_test',
            primary_provider='anthropic_claude',
            required_capabilities={'text', 'conversation'},
            strategy=FallbackStrategy.GRACEFUL
        )
        
        request_data = {
            'request_id': 'network_test',
            'prompt': 'Test network degradation',
            'simulate_network_issue': True
        }
        
        result2 = await manager.execute_fallback_chain(
            chain2.chain_id, request_data
        )
        
        logger.info(f"Network test result: {result2.success}, "
                  f"switches: {result2.switches_performed}")
        
        # Test 3: Capability gaps
        logger.info("Test 3: Capability gap handling")
        chain3 = manager.create_fallback_chain(
            context='capability_test',
            primary_provider='openai_gpt4',
            required_capabilities={'text', 'code', 'vision', 'audio'},
            preservation_level=CapabilityPreservationLevel.PARTIAL
        )
        
        request_data = {
            'request_id': 'capability_test',
            'prompt': 'Test capability gaps',
            'required_capabilities': ['text', 'code', 'vision', 'audio']
        }
        
        result3 = await manager.execute_fallback_chain(
            chain3.chain_id, request_data
        )
        
        logger.info(f"Capability test result: {result3.success}, "
                  f"context preserved: {result3.context_preserved}")
        
    finally:
        await manager.stop_monitoring()


async def main():
    """Run all test scenarios."""
    logger.info("Starting Fallback Chain Manager Tests")
    
    # Setup test environment
    registry = get_fallback_chain_manager()._provider_registry
    await setup_test_providers(registry)
    
    # Run test scenarios
    test_functions = [
        test_basic_fallback_chain,
        test_capability_preservation,
        test_predictive_switching,
        test_graceful_degradation,
        test_performance_optimization,
        test_error_scenarios
    ]
    
    for test_func in test_functions:
        try:
            await test_func()
            logger.info(f"✓ {test_func.__name__} completed")
        except Exception as e:
            logger.error(f"✗ {test_func.__name__} failed: {e}")
        
        # Small delay between tests
        await asyncio.sleep(1.0)
    
    logger.info("All Fallback Chain Manager Tests completed")


if __name__ == "__main__":
    asyncio.run(main())