"""
KIRE-KRO Production Initialization Script

This script initializes and wires all components for the Kari Intelligent Routing Engine (KIRE)
and Kari Reasoning Orchestrator (KRO) systems in production.

Usage:
    from ai_karen_engine.initialize_kire_kro import initialize_production_system

    # Initialize asynchronously
    await initialize_production_system()

    # Or synchronously
    import asyncio
    asyncio.run(initialize_production_system())
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def initialize_production_system(
    enable_cuda: bool = True,
    enable_optimization: bool = True,
    enable_model_discovery: bool = True,
    verbose: bool = True,
) -> bool:
    """
    Initialize the complete KIRE-KRO production system.

    Args:
        enable_cuda: Enable CUDA GPU acceleration if available
        enable_optimization: Enable response content optimization
        enable_model_discovery: Enable comprehensive model discovery
        verbose: Enable verbose logging

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    logger.info("=" * 60)
    logger.info("KIRE-KRO Production System Initialization")
    logger.info("=" * 60)

    try:
        # Step 1: Import and configure integration
        logger.info("\n[1/5] Importing KIRE-KRO integration module...")
        from ai_karen_engine.core.kire_kro_integration import (
            IntegrationConfig,
            initialize_integration,
        )

        config = IntegrationConfig(
            enable_kire_routing=True,
            enable_cuda_acceleration=enable_cuda,
            enable_content_optimization=enable_optimization,
            enable_model_discovery=enable_model_discovery,
            enable_degraded_mode=True,
            enable_metrics=True,
        )

        # Step 2: Initialize integration layer
        logger.info("\n[2/5] Initializing integration layer...")
        integration = await initialize_integration(config)

        # Step 3: Discover models
        if enable_model_discovery:
            logger.info("\n[3/5] Discovering available models...")
            models = await integration.get_available_models()
            logger.info(f"✓ Discovered {len(models)} models")
        else:
            logger.info("\n[3/5] Model discovery disabled")

        # Step 4: Perform health check
        logger.info("\n[4/5] Performing health check...")
        health = await integration.health_check()
        logger.info(f"✓ System status: {health.get('status', 'unknown')}")

        # Step 5: Get system status
        logger.info("\n[5/5] Getting system status...")
        status = await integration.get_system_status()

        logger.info("\n" + "=" * 60)
        logger.info("System Status Summary:")
        logger.info("=" * 60)

        # Display component status
        logger.info("\nComponents:")
        for component, status_value in status.get("components", {}).items():
            status_symbol = "✓" if status_value else "✗"
            logger.info(f"  {status_symbol} {component}: {status_value}")

        # Display configuration
        logger.info("\nConfiguration:")
        for key, value in status.get("config", {}).items():
            logger.info(f"  - {key}: {value}")

        # Display CUDA info if available
        if "cuda" in status:
            logger.info("\nCUDA Status:")
            cuda_info = status["cuda"]
            logger.info(f"  - Available: {cuda_info.get('available', False)}")
            logger.info(f"  - Devices: {cuda_info.get('device_count', 0)}")
            logger.info(f"  - Memory: {cuda_info.get('total_memory_gb', 0):.2f} GB")

        # Display model stats if available
        if "models" in status:
            logger.info("\nModel Discovery:")
            models_info = status["models"]
            logger.info(f"  - Total Models: {models_info.get('total_models', 0)}")
            logger.info(f"  - Total Size: {models_info.get('total_size_gb', 0):.2f} GB")

        # Display provider info
        if "providers" in status:
            logger.info("\nProviders:")
            provider_info = status["providers"]
            logger.info(f"  - Count: {provider_info.get('count', 0)}")
            logger.info(f"  - Names: {', '.join(provider_info.get('names', []))}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ KIRE-KRO Production System Initialized Successfully")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Initialization failed: {e}", exc_info=True)
        logger.error("\n" + "=" * 60)
        logger.error("⚠️  KIRE-KRO Production System Initialization Failed")
        logger.error("=" * 60)
        return False


async def test_system():
    """Test the initialized system with a sample request."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing KIRE-KRO System")
    logger.info("=" * 60)

    try:
        from ai_karen_engine.core.kire_kro_integration import process_request

        # Test request
        test_input = "What is the capital of France?"

        logger.info(f"\nTest Input: {test_input}")
        logger.info("\nProcessing...")

        response = await process_request(
            user_input=test_input,
            user_id="test_user",
        )

        logger.info("\n" + "-" * 60)
        logger.info("Response:")
        logger.info("-" * 60)
        logger.info(f"\nMessage: {response.get('message', 'No message')}")
        logger.info(f"\nProvider: {response.get('meta', {}).get('provider', 'unknown')}")
        logger.info(f"Model: {response.get('meta', {}).get('model', 'unknown')}")
        logger.info(f"Confidence: {response.get('meta', {}).get('confidence', 0):.2f}")
        logger.info(f"Latency: {response.get('meta', {}).get('latency_ms', 0):.0f}ms")

        if response.get("suggestions"):
            logger.info(f"\nSuggestions:")
            for i, suggestion in enumerate(response.get("suggestions", []), 1):
                logger.info(f"  {i}. {suggestion}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ System Test Completed Successfully")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ System test failed: {e}", exc_info=True)
        logger.error("\n" + "=" * 60)
        logger.error("⚠️  System Test Failed")
        logger.error("=" * 60)
        return False


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize KIRE-KRO Production System"
    )
    parser.add_argument(
        "--no-cuda",
        action="store_true",
        help="Disable CUDA GPU acceleration"
    )
    parser.add_argument(
        "--no-optimization",
        action="store_true",
        help="Disable response content optimization"
    )
    parser.add_argument(
        "--no-model-discovery",
        action="store_true",
        help="Disable comprehensive model discovery"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run system test after initialization"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce logging verbosity"
    )

    args = parser.parse_args()

    # Run initialization
    success = asyncio.run(
        initialize_production_system(
            enable_cuda=not args.no_cuda,
            enable_optimization=not args.no_optimization,
            enable_model_discovery=not args.no_model_discovery,
            verbose=not args.quiet,
        )
    )

    if not success:
        sys.exit(1)

    # Run test if requested
    if args.test:
        test_success = asyncio.run(test_system())
        if not test_success:
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
