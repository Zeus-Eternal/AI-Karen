"""
Capsule System Initialization

This module handles the initialization of the capsule system
during application startup. It should be called from the main
app initialization sequence.

Usage:
    from ai_karen_engine.capsules.initialization import initialize_capsule_system

    # During app startup
    initialize_capsule_system()
"""

import logging
from typing import Optional

from ai_karen_engine.capsules.orchestrator import get_capsule_orchestrator
from ai_karen_engine.capsules.registry import get_capsule_registry
from ai_karen_engine.capsules.cortex_integration import get_cortex_adapter

logger = logging.getLogger(__name__)


def initialize_capsule_system(
    auto_discover: bool = True,
    register_with_cortex: bool = True,
) -> dict:
    """
    Initialize the complete capsule system.

    This function should be called during application startup to:
    1. Initialize the capsule registry
    2. Discover available capsules
    3. Initialize the orchestrator
    4. Register capsules with CORTEX (optional)

    Args:
        auto_discover: Automatically discover capsules from filesystem
        register_with_cortex: Register capsules with CORTEX dispatch

    Returns:
        Dict with initialization metrics and status
    """
    logger.info("Initializing capsule system...")

    metrics = {
        "initialized": False,
        "capsules_discovered": 0,
        "cortex_registered": False,
        "errors": [],
    }

    try:
        # Step 1: Get registry instance
        registry = get_capsule_registry()
        logger.info("Capsule registry instantiated")

        # Step 2: Discover capsules
        if auto_discover:
            try:
                discovered = registry.discover()
                metrics["capsules_discovered"] = discovered
                logger.info(f"Discovered {discovered} capsules")
            except Exception as e:
                error_msg = f"Capsule discovery failed: {e}"
                logger.error(error_msg)
                metrics["errors"].append(error_msg)

        # Step 3: Initialize orchestrator
        orchestrator = get_capsule_orchestrator()
        orchestrator.initialize(auto_discover=False)  # Already discovered above
        logger.info("Capsule orchestrator initialized")

        # Step 4: Register with CORTEX
        if register_with_cortex:
            try:
                adapter = get_cortex_adapter()
                adapter.initialize()

                intents = adapter.list_capsule_intents()
                capabilities = adapter.get_capabilities()

                logger.info(
                    f"Registered {len(intents)} intents and "
                    f"{len(capabilities)} capabilities with CORTEX"
                )
                metrics["cortex_registered"] = True
            except Exception as e:
                error_msg = f"CORTEX registration failed: {e}"
                logger.warning(error_msg)
                metrics["errors"].append(error_msg)
                metrics["cortex_registered"] = False

        metrics["initialized"] = True
        logger.info("Capsule system initialization complete")

        # Log summary
        logger.info(
            f"Capsule System Status: "
            f"{metrics['capsules_discovered']} capsules, "
            f"CORTEX={'enabled' if metrics['cortex_registered'] else 'disabled'}"
        )

        return metrics

    except Exception as e:
        error_msg = f"Capsule system initialization failed: {e}"
        logger.error(error_msg, exc_info=True)
        metrics["errors"].append(error_msg)
        return metrics


def get_system_status() -> dict:
    """
    Get current status of the capsule system.

    Returns:
        Dict with system status and metrics
    """
    try:
        registry = get_capsule_registry()
        orchestrator = get_capsule_orchestrator()

        return {
            "status": "operational",
            "registry_metrics": registry.get_metrics(),
            "orchestrator_metrics": orchestrator.get_metrics(),
            "capsules": registry.list_capsules(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


__all__ = [
    "initialize_capsule_system",
    "get_system_status",
]
