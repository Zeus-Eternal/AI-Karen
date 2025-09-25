from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.ai_karen_engine.api_routes.memory_routes import MemCommit, memory_commit


@pytest.mark.asyncio
async def test_memory_commit_error_timestamp_iso() -> None:
    request_data = MemCommit(
        user_id="test_user",
        org_id=None,
        text="remember this",
        tags=[],
        importance=5,
        decay="short",
    )
    http_request = SimpleNamespace(
        headers={}, url=SimpleNamespace(path="/memory/commit")
    )
    with patch(
        "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
        return_value=False,
    ), patch(
        "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc:
            await memory_commit(request_data, http_request)
    data = exc.value.detail
    assert isinstance(data["timestamp"], str)
    datetime.fromisoformat(data["timestamp"])


@pytest.mark.asyncio
async def test_memory_commit_success_contains_no_datetimes() -> None:
    request_data = MemCommit(
        user_id="test_user",
        org_id=None,
        text="remember this",
        tags=[],
        importance=5,
        decay="short",
    )
    http_request = SimpleNamespace(
        headers={}, url=SimpleNamespace(path="/memory/commit")
    )
    with patch(
        "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
        return_value=True,
    ), patch(
        "src.ai_karen_engine.api_routes.memory_routes.get_memory_service",
        return_value=None,
    ):
        response = await memory_commit(request_data, http_request)
    for value in response.model_dump().values():
        assert not isinstance(value, datetime)
