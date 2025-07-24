from __future__ import annotations

import logging
import uuid

from ai_karen_engine.services.memory_service import WebUIMemoryService, WebUIMemoryQuery, UISource
from ai_karen_engine.core.default_models import load_default_models

logger = logging.getLogger(__name__)

async def bootstrap_memory_system(memory_service: WebUIMemoryService, tenant_id: str = "default") -> bool:
    """Ensure memory schema and models are initialized and perform roundtrip test."""
    base_manager = memory_service.base_manager
    db_client = base_manager.db_client

    db_client.create_shared_tables()
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
