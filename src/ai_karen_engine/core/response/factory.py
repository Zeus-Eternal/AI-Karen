"""
Factory for creating ResponseOrchestrator instances with appropriate adapters.

This module provides convenient factory functions for creating ResponseOrchestrator
instances with the correct adapters for the existing Karen AI infrastructure,
including scheduler manager initialization for autonomous training.
"""

import logging
from typing import Optional
from pathlib import Path

from .orchestrator import ResponseOrchestrator
from .config import PipelineConfig, DEFAULT_CONFIG
from .adapters import create_spacy_analyzer, create_memory_adapter, create_llm_adapter
from .scheduler_manager import SchedulerManager
from .autonomous_learner import AutonomousLearner

logger = logging.getLogger(__name__)


def create_response_orchestrator(
    user_id: str = "default",
    tenant_id: Optional[str] = None,
    config: Optional[PipelineConfig] = None
) -> ResponseOrchestrator:
    """Create a ResponseOrchestrator with default adapters.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        config: Pipeline configuration (uses default if None)
        
    Returns:
        Configured ResponseOrchestrator instance
    """
    config = config or DEFAULT_CONFIG
    
    try:
        # Create adapters for existing components
        analyzer = create_spacy_analyzer()
        memory = create_memory_adapter(user_id, tenant_id)
        llm_client = create_llm_adapter()
        
        # Create orchestrator
        orchestrator = ResponseOrchestrator(
            analyzer=analyzer,
            memory=memory,
            llm_client=llm_client,
            config=config
        )
        
        logger.info(f"ResponseOrchestrator created for user {user_id}")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to create ResponseOrchestrator: {e}")
        raise


def create_local_only_orchestrator(
    user_id: str = "default",
    tenant_id: Optional[str] = None
) -> ResponseOrchestrator:
    """Create a ResponseOrchestrator configured for local-only operation.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        
    Returns:
        ResponseOrchestrator configured for local-only operation
    """
    config = PipelineConfig(
        local_only=True,
        enable_copilotkit=False,  # Disable for pure local operation
        local_model_preference="local:tinyllama-1.1b"
    )
    
    return create_response_orchestrator(user_id, tenant_id, config)


def create_enhanced_orchestrator(
    user_id: str = "default",
    tenant_id: Optional[str] = None
) -> ResponseOrchestrator:
    """Create a ResponseOrchestrator with all features enabled.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        
    Returns:
        ResponseOrchestrator with enhanced features enabled
    """
    config = PipelineConfig(
        local_only=False,  # Allow cloud acceleration
        enable_copilotkit=True,
        enable_onboarding=True,
        enable_persona_detection=True,
        enable_memory_persistence=True,
        enable_metrics=True,
        enable_audit_logging=True
    )
    
    return create_response_orchestrator(user_id, tenant_id, config)


# Singleton instances for global use
_global_orchestrator: Optional[ResponseOrchestrator] = None
_global_scheduler_manager: Optional[SchedulerManager] = None


def create_autonomous_learner(
    user_id: str = "default",
    tenant_id: Optional[str] = None
) -> AutonomousLearner:
    """Create an AutonomousLearner instance.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        
    Returns:
        Configured AutonomousLearner instance
    """
    try:
        # Create components needed for autonomous learner
        analyzer = create_spacy_analyzer()
        memory = create_memory_adapter(user_id, tenant_id)
        
        # Create autonomous learner
        learner = AutonomousLearner(
            spacy_analyzer=analyzer,
            memory_service=memory
        )
        
        logger.info(f"AutonomousLearner created for user {user_id}")
        return learner
        
    except Exception as e:
        logger.error(f"Failed to create AutonomousLearner: {e}")
        raise


def create_scheduler_manager(
    user_id: str = "default",
    tenant_id: Optional[str] = None,
    storage_path: Optional[Path] = None
) -> SchedulerManager:
    """Create a SchedulerManager instance.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        storage_path: Optional path for schedule storage
        
    Returns:
        Configured SchedulerManager instance
    """
    try:
        # Create autonomous learner
        autonomous_learner = create_autonomous_learner(user_id, tenant_id)
        
        # Create memory adapter for notifications
        memory = create_memory_adapter(user_id, tenant_id)
        
        # Create scheduler manager
        scheduler = SchedulerManager(
            autonomous_learner=autonomous_learner,
            memory_service=memory,
            storage_path=storage_path
        )
        
        logger.info(f"SchedulerManager created for user {user_id}")
        return scheduler
        
    except Exception as e:
        logger.error(f"Failed to create SchedulerManager: {e}")
        raise


def get_global_orchestrator(
    user_id: str = "default",
    tenant_id: Optional[str] = None,
    force_recreate: bool = False
) -> ResponseOrchestrator:
    """Get or create a global ResponseOrchestrator instance.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        force_recreate: Force recreation of the global instance
        
    Returns:
        Global ResponseOrchestrator instance
    """
    global _global_orchestrator

    if _global_orchestrator is None or force_recreate:
        _global_orchestrator = create_response_orchestrator(user_id, tenant_id)

    return _global_orchestrator


def rebuild_global_orchestrator(
    config: PipelineConfig,
    user_id: str = "default",
    tenant_id: Optional[str] = None,
) -> ResponseOrchestrator:
    """Rebuild the global orchestrator with a new configuration."""

    global _global_orchestrator
    _global_orchestrator = create_response_orchestrator(
        user_id=user_id,
        tenant_id=tenant_id,
        config=config
    )
    return _global_orchestrator


def get_global_scheduler_manager(
    user_id: str = "default",
    tenant_id: Optional[str] = None,
    force_recreate: bool = False
) -> SchedulerManager:
    """Get or create a global SchedulerManager instance.
    
    Args:
        user_id: User identifier for memory operations
        tenant_id: Optional tenant identifier
        force_recreate: Force recreation of the global instance
        
    Returns:
        Global SchedulerManager instance
    """
    global _global_scheduler_manager
    
    if _global_scheduler_manager is None or force_recreate:
        _global_scheduler_manager = create_scheduler_manager(user_id, tenant_id)
    
    return _global_scheduler_manager


async def initialize_global_scheduler():
    """Initialize and start the global scheduler manager."""
    try:
        scheduler = get_global_scheduler_manager()
        await scheduler.start_scheduler()
        logger.info("Global scheduler manager started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize global scheduler: {e}")
        raise


async def shutdown_global_scheduler():
    """Shutdown the global scheduler manager."""
    try:
        global _global_scheduler_manager
        if _global_scheduler_manager:
            await _global_scheduler_manager.stop_scheduler()
            logger.info("Global scheduler manager stopped successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown global scheduler: {e}")
        raise