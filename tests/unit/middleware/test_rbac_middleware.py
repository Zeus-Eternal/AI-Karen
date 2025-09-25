import asyncio
from types import SimpleNamespace

from fastapi.responses import JSONResponse

from ai_karen_engine.middleware.rbac import RBACMiddleware, setup_rbac


def _make_request():
    return SimpleNamespace(
        headers={},
        state=SimpleNamespace(),
        url=SimpleNamespace(path="/"),
        method="GET",
        client=SimpleNamespace(host="127.0.0.1"),
    )


def test_development_mode_allows_request():
    rbac = RBACMiddleware(development_mode=True)
    req = _make_request()
    result = asyncio.run(rbac.validate_scopes(req, {"chat:write"}))
    assert result is True


def test_production_mode_requires_authentication():
    rbac = RBACMiddleware(development_mode=False)
    req = _make_request()
    result = asyncio.run(rbac.validate_scopes(req, {"chat:write"}))
    assert result is False
    error_response = rbac.create_rbac_error_response(req, "Authentication required", 401)
    resp = JSONResponse(status_code=401, content=error_response.model_dump(mode="json"))
    assert resp.status_code == 401


def test_app_instances_are_isolated():
    class DummyApp:
        def __init__(self):
            self.state = SimpleNamespace()

        def middleware(self, _type):
            def decorator(func):
                return func

            return decorator

    app1 = DummyApp()
    app2 = DummyApp()
    setup_rbac(app1, development_mode=True)
    setup_rbac(app2, development_mode=False)
    assert app1.state.rbac is not app2.state.rbac

