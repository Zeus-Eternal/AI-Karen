from __future__ import annotations

import logging
import uuid
from typing import Union

try:
    from ai_karen_engine.services.memory_service import WebUIMemoryService, WebUIMemoryQuery, UISource
    from ai_karen_engine.services.memory.unified_memory_service import UnifiedMemoryService
    from ai_karen_engine.core.default_models import load_default_models
except ImportError:
    # Define dummy classes if imports fail
    class WebUIMemoryService:
        def __init__(self, memory_manager):
            self.memory_manager = memory_manager
        @property
        def base_manager(self):
            return self.memory_manager
        async def store_web_ui_memory(self, tenant_id, content, user_id, ui_source):
            return "test_id"
        async def query_memories(self, tenant_id, query):
            return []
    
    class WebUIMemoryQuery:
        def __init__(self, text):
            self.text = text
    
    class UISource:
        API = "api"
    
    class UnifiedMemoryService:
        def __init__(self):
            pass
        @property
        def base_manager(self):
            return None
        async def store_web_ui_memory(self, tenant_id, content, user_id, ui_source):
            return "test_id"
        async def query_memories(self, tenant_id, query):
            return []
    
    async def load_default_models():
        pass

logger = logging.getLogger(__name__)

async def bootstrap_memory_system(memory_service: Union[WebUIMemoryService, UnifiedMemoryService], tenant_id: str = "default") -> bool:
    """Ensure memory schema and models are initialized and perform roundtrip test."""
    base_manager = memory_service.base_manager
    db_client = base_manager.db_client

    if not db_client.ensure_memory_table(tenant_id):
        logger.error("[bootstrap] failed to ensure memory table for %s", tenant_id)
        return False

    await load_default_models()

    test_id = await memory_service.store_web_ui_memory(
        tenant_id=tenant_id,
        content="bootstrap test",
        user_id=str(uuid.uuid4()),
        ui_source=UISource.API,
    )
    results = await memory_service.query_memories(
        tenant_id=tenant_id, query=WebUIMemoryQuery(text="bootstrap test")
    )
    found = any(m.id == test_id for m in results)
    logger.info("[bootstrap] roundtrip success=%s", found)
    return found
