import sys
import types

# Stub out optional GUI dependencies to avoid import-time errors
sys.modules.setdefault("pyautogui", types.ModuleType("pyautogui"))
sys.modules.setdefault("mouseinfo", types.ModuleType("mouseinfo"))

import pytest  # noqa: E402

from ai_karen_engine.auth.config import DatabaseConfig  # noqa: E402
from ai_karen_engine.auth.database import AuthDatabaseClient  # noqa: E402
from ai_karen_engine.auth.models import AuthEvent, AuthEventType  # noqa: E402


@pytest.mark.asyncio
async def test_store_auth_event_auto_initializes_schema(monkeypatch):
    client = AuthDatabaseClient(DatabaseConfig())

    initialized = False

    async def fake_initialize_schema() -> None:
        nonlocal initialized
        initialized = True
        client._schema_initialized = True

    monkeypatch.setattr(client, "initialize_schema", fake_initialize_schema)

    class DummySession:
        async def execute(self, *args, **kwargs):
            return None

        async def commit(self) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    client.session_factory = lambda: DummySession()

    event = AuthEvent(event_type=AuthEventType.LOGIN_FAILED)
    await client.store_auth_event(event)

    assert initialized
