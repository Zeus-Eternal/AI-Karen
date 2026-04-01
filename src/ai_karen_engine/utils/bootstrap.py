from __future__ import annotations

import logging
import uuid
from typing import Union

try:
    from services.memory.memory_service import WebUIMemoryService, WebUIMemoryQuery, UISource
    from services.memory.unified_memory_service import (
        UnifiedMemoryService,
        MemoryCommitRequest,
        MemoryQueryRequest,
    )
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

    class MemoryCommitRequest:
        def __init__(self, user_id, org_id, text, tags, importance, decay, metadata):
            self.user_id = user_id
            self.org_id = org_id
            self.text = text
            self.tags = tags
            self.importance = importance
            self.decay = decay
            self.metadata = metadata

    class MemoryQueryRequest:
        def __init__(self, user_id, org_id, query, top_k, similarity_threshold=0.0, include_metadata=True):
            self.user_id = user_id
            self.org_id = org_id
            self.query = query
            self.top_k = top_k
            self.similarity_threshold = similarity_threshold
            self.include_metadata = include_metadata

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

    user_id = str(uuid.uuid4())
    if hasattr(memory_service, "commit") and hasattr(memory_service, "query"):
        commit_response = await memory_service.commit(
            tenant_id=tenant_id,
            request=MemoryCommitRequest(
                user_id=user_id,
                org_id=None,
                text="bootstrap test",
                tags=["bootstrap"],
                importance=5,
                decay="short",
                metadata={"ui_source": UISource.API if hasattr(UISource, "API") else "api"},
            ),
        )
        test_id = commit_response.id
        search_response = await memory_service.query(
            tenant_id=tenant_id,
            request=MemoryQueryRequest(
                user_id=user_id,
                org_id=None,
                query="bootstrap test",
                top_k=10,
                similarity_threshold=0.0,
                include_metadata=True,
            ),
        )
        found = any(hit.id == test_id for hit in search_response.hits)
    else:
        test_id = await memory_service.store_web_ui_memory(
            tenant_id=tenant_id,
            content="bootstrap test",
            user_id=user_id,
            ui_source=UISource.API,
        )
        results = await memory_service.query_memories(
            tenant_id=tenant_id, query=WebUIMemoryQuery(text="bootstrap test")
        )
        found = any(m.id == test_id for m in results)
    logger.info("[bootstrap] roundtrip success=%s", found)
    return found
