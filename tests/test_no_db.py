import sys
from unittest.mock import MagicMock

sys.modules["pyautogui"] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ui_launchers.backend.developer_api import get_current_user, setup_developer_api


def test_developer_api_runs_without_db_client() -> None:
    app = FastAPI()
    setup_developer_api(app)
    client = TestClient(app)

    mock_user = MagicMock()
    mock_user.user_id = "test"
    mock_user.roles = ["admin"]
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = client.get("/api/developer/chat-metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "summary" in data
