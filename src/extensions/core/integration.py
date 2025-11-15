"""
Integration layer between the FastAPI server and the ai_karen_engine extension system.

This module exposes a thin runtime surface that initializes the production-grade
extension manager via the shared factory while exposing a simple handle for the server
to retrieve the manager for health monitoring and recovery.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from ai_karen_engine.extensions.factory import (
    ExtensionServiceConfig,
    initialize_extensions_for_production,
)
from ai_karen_engine.extensions.manager import ExtensionManager

logger = logging.getLogger(__name__)


class ExtensionSystemIntegration:
    """
    Lightweight handle that keeps the extension manager alive for server integrations.
    """

    def __init__(
        self,
        manager: ExtensionManager,
        config: ExtensionServiceConfig,
        db_session: Optional[object] = None,
        plugin_router: Optional[object] = None,
    ):
        self.extension_manager = manager
        self.config = config
        self.db_session = db_session
        self.plugin_router = plugin_router

    def get_extension_manager(self) -> ExtensionManager:
        """Expose the initialized extension manager to the server."""
        return self.extension_manager


async def initialize_extensions(
    app: FastAPI,
    extension_root: str = "extensions",
    db_session: Optional[object] = None,
    plugin_router: Optional[object] = None,
) -> bool:
    """
    Initialize the extension system for the given FastAPI app.

    This is the entry point used by ``server.app`` to bootstrap the ai_karen_engine
    extension system during startup.
    """
    try:
        config = ExtensionServiceConfig(extension_root=Path(extension_root))
        manager = initialize_extensions_for_production(config)
        if manager is None:
            logger.warning("Extension manager factory returned None")
            return False

        integration = ExtensionSystemIntegration(
            manager=manager,
            config=config,
            db_session=db_session,
            plugin_router=plugin_router,
        )

        app.state.extension_system = integration
        app.state.extension_manager = manager
        logger.info("Extension system initialized and attached to application state")
        return True
    except Exception as exc:
        logger.warning("Failed to initialize extension system: %s", exc, exc_info=True)
        return False
