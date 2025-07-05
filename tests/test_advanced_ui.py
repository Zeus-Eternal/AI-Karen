import types
from ui_launchers.common.components import rbac
from ai_karen_engine.services import health_checker
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_has_role():
    fake_state = {"roles": ["admin"]}
    rbac.st = types.SimpleNamespace(session_state=fake_state)
    assert rbac.has_role("admin")
    assert not rbac.has_role("user")


def test_require_role(monkeypatch):
    fake_state = {"roles": ["user"]}
    monkeypatch.setattr(
        rbac,
        "st",
        types.SimpleNamespace(session_state=fake_state, error=lambda *a, **k: None),
    )

    @rbac.require_role("admin")
    def _page():
        return "ok"

    assert _page() is None
    fake_state["roles"].append("admin")
    assert _page() == "ok"


def test_health_checker_keys():
    data = health_checker.get_system_health()
    assert "runtime" in data and "memory" in data


def test_plugin_toggle():
    intent = client.get("/plugins").json()[0]
    resp = client.post(f"/plugins/{intent}/disable")
    assert resp.status_code == 200
    assert intent not in client.get("/plugins").json()
    resp = client.post(f"/plugins/{intent}/enable")
    assert resp.status_code == 200
    assert intent in client.get("/plugins").json()


def test_prometheus_endpoint():
    resp = client.get("/metrics/prometheus")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")

