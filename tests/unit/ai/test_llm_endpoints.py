import sys

import pytest

# Restore real FastAPI/Pydantic implementations instead of test stubs
sys.modules.pop("fastapi", None)
sys.modules.pop("pydantic", None)
sys.modules.pop("fastapi.testclient", None)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ai_karen_engine.api_routes.llm_routes import router as llm_router


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(llm_router, prefix="/api/llm")
    with TestClient(app) as c:
        yield c

def test_list_providers(client):
    response = client.get("/api/llm/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("providers"), list)


def test_list_profiles(client):
    response = client.get("/api/llm/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("profiles"), list)
