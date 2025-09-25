"""Verify that copilot assist triggers memory write-back."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest  # type: ignore[import-not-found]

from src.ai_karen_engine.api_routes.copilot_routes import AssistRequest, copilot_assist


@pytest.mark.asyncio
async def test_assist_triggers_writeback() -> None:
    request = AssistRequest(
        user_id="user123",
        org_id="org456",
        message="remember this for later",
        top_k=3,
    )

    http_request = SimpleNamespace(
        headers={},
        url=SimpleNamespace(path="/copilot/assist"),
        method="POST",
        client=None,
    )

    mock_memory = Mock()
    mock_memory.link_response_to_shards = AsyncMock(return_value=[Mock()])
    mock_memory.queue_interaction_writeback = AsyncMock()

    mock_metrics = Mock()

    with patch(
        "src.ai_karen_engine.api_routes.copilot_routes.check_rbac_scope",
        AsyncMock(return_value=True),
    ), patch(
        "src.ai_karen_engine.api_routes.copilot_routes.get_memory_service",
        AsyncMock(return_value=mock_memory),
    ), patch(
        "src.ai_karen_engine.api_routes.copilot_routes.get_llm_provider",
        AsyncMock(return_value=None),
    ), patch(
        "src.ai_karen_engine.api_routes.copilot_routes.get_metrics_service",
        return_value=mock_metrics,
    ):
        await copilot_assist(request, http_request)

    mock_memory.link_response_to_shards.assert_awaited_once()
    mock_memory.queue_interaction_writeback.assert_awaited_once()
    mock_metrics.record_memory_commit.assert_called_once()
