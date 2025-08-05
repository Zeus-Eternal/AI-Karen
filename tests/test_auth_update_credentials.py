import json
import types

import pytest

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
except Exception:
    FASTAPI_AVAILABLE = False
    TestClient = None
    FastAPI = None
else:
    FASTAPI_AVAILABLE = True

from ai_karen_engine.security import auth_manager
from ai_karen_engine.api_routes import auth as auth_routes


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_login_and_update_credentials(tmp_path, monkeypatch):
    # Prepare temporary user store
    path = tmp_path / "users.json"
    data = {
        "test@example.com": {
            "password": auth_manager._hash_password("pass"),
            "roles": ["user"],
            "tenant_id": "default",
            "preferences": {},
        }
    }
    path.write_text(json.dumps(data))

    monkeypatch.setattr(auth_manager, "USER_STORE_PATH", path)
    monkeypatch.setattr(auth_manager, "_USERS", data.copy())
    monkeypatch.setattr(auth_manager, "save_users", lambda: None)

    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/auth")
    client = TestClient(app)

    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "pass"})
    assert resp.status_code == 200
    token = resp.json()["token"]

    resp2 = client.post(
        "/api/auth/update_credentials",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    token2 = resp2.json()["token"]
    assert token2 != token

    resp3 = client.post("/api/auth/login", json={"email": "test@example.com", "password": "newpass"})
    assert resp3.status_code == 200

