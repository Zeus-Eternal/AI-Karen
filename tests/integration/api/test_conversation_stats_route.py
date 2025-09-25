from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_karen_engine.api_routes.conversation_routes import (
    router,
    get_conversation_service,
    get_current_tenant,
)


def test_get_conversation_stats_resolves_tenant_id():
    app = FastAPI()
    app.include_router(router)
    # Ensure the /stats route is matched before dynamic routes like /{conversation_id}
    app.router.routes.sort(key=lambda r: 0 if getattr(r, "path", "") == "/stats" else 1)

    called = {}

    class DummyBaseManager:
        async def get_conversation_stats(self, tenant, user):
            called["tenant_id"] = tenant
            called["user_id"] = user
            return {}

    class DummyService:
        def __init__(self):
            self.base_manager = DummyBaseManager()

        def get_metrics(self):
            return {}

    async def override_service():
        return DummyService()

    async def override_tenant():
        return "test-tenant"

    app.dependency_overrides[get_conversation_service] = override_service
    app.dependency_overrides[get_current_tenant] = override_tenant

    client = TestClient(app)
    response = client.get("/stats")
    assert response.status_code == 200
    assert called["tenant_id"] == "test-tenant"
