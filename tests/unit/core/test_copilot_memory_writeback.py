from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request

from ai_karen_engine.services.memory_writeback import InteractionType
from src.ai_karen_engine.api_routes.copilot_routes import AssistRequest, copilot_assist


@pytest.mark.asyncio
async def test_assist_triggers_memory_writeback():
    req = AssistRequest(
        user_id="user1",
        org_id="org1",
        message="hello",
        top_k=2,
    )
    http_request = Request()

    memory_mock = Mock()
    memory_mock.link_response_to_shards = AsyncMock(return_value=["shard"])
    memory_mock.queue_interaction_writeback = AsyncMock(return_value="id")
    metrics_mock = Mock()

    with (
        patch(
            "src.ai_karen_engine.api_routes.copilot_routes.check_rbac_scope",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "src.ai_karen_engine.api_routes.copilot_routes.get_llm_provider",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "src.ai_karen_engine.api_routes.copilot_routes.get_memory_service",
            new=AsyncMock(return_value=memory_mock),
        ),
        patch(
            "src.ai_karen_engine.api_routes.copilot_routes.get_metrics_service",
            return_value=metrics_mock,
        ),
    ):
        response = await copilot_assist(req, http_request)

    assert response.answer
    memory_mock.link_response_to_shards.assert_awaited_once()
    memory_mock.queue_interaction_writeback.assert_awaited_once()
    args, kwargs = memory_mock.queue_interaction_writeback.await_args
    assert kwargs["source_shards"] == ["shard"]
    assert kwargs["interaction_type"] == InteractionType.COPILOT_RESPONSE
    assert "copilot_assist" in kwargs["tags"]

    metrics_mock.record_memory_commit.assert_called()
    commit_args, _ = metrics_mock.record_memory_commit.call_args
    assert commit_args[0] == "success"
