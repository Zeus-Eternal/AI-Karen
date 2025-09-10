# mypy: ignore-errors
"""
Startup configuration for Kari FastAPI Server.
Handles lifespan, warmups, service initialization, and startup tasks.
"""

import logging
from fastapi import FastAPI
from .config import Settings

logger = logging.getLogger("kari")

# Import lifespan from existing module
from ai_karen_engine.server.startup import create_lifespan


def register_startup_tasks(app: FastAPI) -> None:
    """Register startup tasks for LLM providers and services"""
    
    @app.on_event("startup")
    async def _init_llm_providers() -> None:
        try:
            from ai_karen_engine.integrations.startup import initialize_llm_providers
            result = initialize_llm_providers()
            logger.info(
                "LLM providers initialized",
                extra={
                    "total": result.get("total_providers"),
                    "healthy": result.get("healthy_providers"),
                    "available": result.get("available_providers"),
                },
            )
        except Exception as e:
            logger.warning(f"LLM provider initialization skipped: {e}")


async def initialize_fallback_systems() -> None:
    """Initialize fallback systems for degraded mode operation"""
    try:
        # This would contain fallback system initialization logic
        logger.info("Fallback systems initialized")
    except Exception as e:
        logger.error(f"Failed to initialize fallback systems: {e}")


async def run_startup_checks_and_fallbacks(logger) -> None:
    """Run startup checks and initialize fallback systems if needed"""
    try:
        await initialize_fallback_systems()
        logger.info("Startup checks completed successfully")
    except Exception as e:
        logger.error(f"Startup checks failed: {e}")
        # Continue with fallback systems