from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_karen_engine.server.routers import wire_routers
from ai_karen_engine.server.config import Settings


def test_store_mock_route_not_mounted_in_production():
    app = FastAPI()
    settings = Settings()
    wire_routers(app, settings)

    matched = [r for r in app.router.routes if getattr(r, 'path', '').startswith('/api/store')]
    assert matched, 'Expected production store routes to be mounted'
    for route in matched:
        endpoint_module = getattr(route.endpoint, '__module__', '')
        assert 'store_mock' not in endpoint_module


def test_production_store_search_does_not_return_mock_constants(monkeypatch):
    from ai_karen_engine.api_routes.plugins import store as store_routes

    class P:
        def __init__(self):
            self.name = 'real-plugin'
            self.description = 'real description'
            self.category = 'utilities'
            self.enabled = True
            self.version = '1.0.0'
        def model_dump(self):
            return {'name': self.name, 'description': self.description, 'category': self.category, 'enabled': self.enabled, 'version': self.version}

    class Svc:
        async def list_plugins(self):
            return [P()]

    app = FastAPI()
    app.include_router(store_routes.router, prefix='/api')
    app.dependency_overrides[store_routes.get_plugin_service] = lambda: Svc()

    client = TestClient(app)
    resp = client.get('/api/store/search', params={'query': 'real-plugin', 'page': 1, 'per_page': 20})
    assert resp.status_code == 200
    data = resp.json()
    assert 'MOCK_PLUGINS' not in str(data)
    assert all(p.get('name') != 'Weather Plugin' for p in data.get('plugins', []))
