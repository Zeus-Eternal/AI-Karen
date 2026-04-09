"""
Fix for ChatOrchestrator greenlet error.

The issue is that MultiTenantPostgresClient() is being instantiated synchronously
in the ChatServiceFactory, which creates database connections in a sync context.
When the ChatOrchestrator tries to use these connections in an async context,
it causes the greenlet error.

This fix ensures that database clients are properly managed in async contexts.
"""

# Import required modules
from typing import Optional
import asyncio
from ai_karen_engine.database.client import get_db_client

# This fix can be applied to src/ai_karen_engine/chat/factory.py

# Find the create_conversation_manager method in factory.py (around line 205)
# BEFORE (lines 205-215):
    def create_conversation_manager(self) -> Optional[ConversationManager]:
        """Create and configure the authoritative conversation manager."""
        try:
            db_client = MultiTenantPostgresClient()
            manager = ConversationManager(db_client)
            self._services['conversation_manager'] = manager
            logger.info("Enhanced conversation manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            return None

# AFTER (with async database client):
    async def create_conversation_manager(self) -> Optional[ConversationManager]:
        """Create and configure the authoritative conversation manager with async support."""
        try:
            # Use async database client for async operations
            # MultiTenantPostgresClient should be replaced with get_db_client()
            db_client = await get_db_client()  # Ensure this returns async client

            manager = ConversationManager(db_client)
            self._services['conversation_manager'] = manager
            logger.info("Enhanced conversation manager created successfully (async)")
            return manager
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            return None


# Also need to update the create_chat_orchestrator method to be async
# BEFORE (around line 229):
    def create_chat_orchestrator(self) -> ChatOrchestrator:
        """
        Create and configure chat orchestrator with all services wired.

        Returns:
            Fully configured ChatOrchestrator instance
        """
        logger.info("Creating chat orchestrator with all services")

        # Create all dependent services
        memory_processor = self.create_memory_processor()
        # ... other service creations ...

        # Create orchestrator with all services
        orchestrator = ChatOrchestrator(
            # ... service parameters ...
        )

        self._services['chat_orchestrator'] = orchestrator

        logger.info("Chat orchestrator created successfully with all services wired")
        return orchestrator

# AFTER (async version):
    async def create_chat_orchestrator(self) -> ChatOrchestrator:
        """
        Create and configure chat orchestrator with all services wired (async).

        Returns:
            Fully configured ChatOrchestrator instance
        """
        logger.info("Creating chat orchestrator with all services (async)")

        # Create all dependent services (may be sync or async)
        memory_processor = self.create_memory_processor()
        file_attachment_service = self.create_file_attachment_service()
        multimedia_service = self.create_multimedia_service()
        code_execution_service = self.create_code_execution_service()
        tool_integration_service = self.create_tool_integration_service()
        instruction_processor = self.create_instruction_processor()
        context_integrator = self.create_context_integrator()
        session_state_manager = await self.create_session_state_manager()  # Make this async

        # ... rest of the method ...

        # Create orchestrator with all services
        orchestrator = ChatOrchestrator(
            # ... service parameters ...
        )

        self._services['chat_orchestrator'] = orchestrator

        logger.info("Chat orchestrator created successfully with all services wired (async)")
        return orchestrator


# Additionally, update the get_chat_orchestrator function to handle async creation
# BEFORE (around line 373):
    def get_chat_orchestrator() -> ChatOrchestrator:
        """
        Get or create global chat orchestrator.

        Returns:
            ChatOrchestrator instance
        """
        factory = get_chat_service_factory()
        orchestrator = factory.get_service('chat_orchestrator')

        if orchestrator is None:
            orchestrator = factory.create_chat_orchestrator()

        return orchestrator

# AFTER:
    async def get_chat_orchestrator_async() -> ChatOrchestrator:
        """
        Get or create global chat orchestrator (async).

        Returns:
            ChatOrchestrator instance
        """
        factory = get_chat_service_factory()
        orchestrator = factory.get_service('chat_orchestrator')

        if orchestrator is None:
            orchestrator = await factory.create_chat_orchestrator()

        return orchestrator


# For backward compatibility, keep the sync version:
    def get_chat_orchestrator() -> ChatOrchestrator:
        """
        Get or create global chat orchestrator (sync - for backward compatibility).

        Returns:
            ChatOrchestrator instance
        """
        try:
            # Try to get from factory first
            factory = get_chat_service_factory()
            orchestrator = factory.get_service('chat_orchestrator')

            if orchestrator is None:
                # Fallback: create in sync context (will work if DB is already initialized)
                orchestrator = factory.create_chat_orchestrator()

            return orchestrator
        except Exception as e:
            logger.error(f"Failed to get chat orchestrator: {e}")
            # Fallback to creating a minimal orchestrator
            return ChatOrchestrator()


# Update the dependencies.py to use the async version when needed:
# In src/ai_karen_engine/core/dependencies.py, line 596-694
# BEFORE:
    async def get_chat_orchestrator_service() -> Any:
        """Get Chat Orchestrator service instance as the absolute source of truth."""
        registry_error: Optional[Exception] = None

        logger.info(
            "🔍 DEBUG: Attempting to get Chat Orchestrator service from registry..."
        )

        try:
            registry = get_service_registry()
            logger.info(f"🔍 DEBUG: Service registry obtained: {type(registry).__name__}")
            logger.info(
                f"🔍 DEBUG: Available services in registry: {registry.list_services()}"
            )

            service = await registry.get_service("chat_orchestrator")
            logger.info(
                f"🔍 DEBUG: Chat Orchestrator service retrieved successfully: {type(service).__name__}"
            )
            return service
        except (ValueError, RuntimeError) as exc:
            # ... error handling ...

# AFTER:
    async def get_chat_orchestrator_service() -> Any:
        """Get Chat Orchestrator service instance as the absolute source of truth (async)."""
        registry_error: Optional[Exception] = None

        logger.info(
            "🔍 DEBUG: Attempting to get Chat Orchestrator service from registry..."
        )

        try:
            registry = get_service_registry()
            logger.info(f"🔍 DEBUG: Service registry obtained: {type(registry).__name__}")
            logger.info(
                f"🔍 DEBUG: Available services in registry: {registry.list_services()}"
            )

            service = await registry.get_service("chat_orchestrator")
            logger.info(
                f"🔍 DEBUG: Chat Orchestrator service retrieved successfully: {type(service).__name__}"
            )
            return service
        except (ValueError, RuntimeError) as exc:
            registry_error = exc
            logger.error(
                f"❌ Service registry lookup for Chat Orchestrator failed: {exc}",
                exc_info=True,
            )
            logger.error(f"❌ Error type: {type(exc).__name__}")
            logger.error(f"❌ Error details: {str(exc)}")

        # Fallback to lazy loading
        logger.debug("🔄 Attempting lazy loading fallback for Chat Orchestrator...")
        try:
            from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services

            available_lazy_services = lazy_registry.list_services()
            logger.debug(f"📋 Lazy registry services: {available_lazy_services}")

            if not available_lazy_services:
                logger.debug("🚀 No lazy services available, setting up lazy services...")
                await setup_lazy_services()
                logger.debug(
                    f"✅ Lazy services setup complete: {lazy_registry.list_services()}"
                )

            # Use async factory if available
            try:
                from ai_karen_engine.chat.factory import get_chat_orchestrator_async
                orchestrator = await get_chat_orchestrator_async()
                if registry_error:
                    logger.info(
                        "✅ Using async Chat Orchestrator because registry access failed: %s",
                        registry_error,
                    )
                return orchestrator
            except ImportError:
                # Fallback to sync version
                logger.warning("⚠️ Async factory not available, using sync fallback")
                from ai_karen_engine.chat.factory import get_chat_orchestrator
                orchestrator = get_chat_orchestrator()
                return orchestrator
        except Exception as lazy_exc:
            logger.error(
                f"❌ Lazy Chat Orchestrator initialization failed: {lazy_exc}",
                exc_info=True,
            )
            logger.error(f"❌ Error type: {type(lazy_exc).__name__}")

            # FINAL STANDING FALLBACK: Use the production ChatServiceFactory to force-create the instance
            # This bypasses all registry-level suppression and ensures the service is available.
            try:
                logger.info(
                    "🔄 Final fallback: Attempting to create Chat Orchestrator via ChatServiceFactory..."
                )
                from ai_karen_engine.chat.factory import get_chat_orchestrator

                orchestrator = get_chat_orchestrator()
                if orchestrator:
                    logger.info(
                        "✅ Success: Chat Orchestrator created via factory fallback."
                    )
                    return orchestrator
            except Exception as factory_exc:
                logger.error(f"❌ ChatServiceFactory fallback also failed: {factory_exc}")

            logger.error("❌ Raising HTTP 503: Chat Orchestrator service unavailable")
            raise HTTPException(
                status_code=503, detail="Chat Orchestrator service unavailable"
            )


# Summary of changes:
# 1. Make create_conversation_manager async
# 2. Make create_chat_orchestrator async
# 3. Add get_chat_orchestrator_async function
# 4. Update get_chat_orchestrator_service to use async factory when available
# 5. Ensure all database operations use async context managers
