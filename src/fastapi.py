"""Compatibility wrapper for environments without FastAPI."""
from ai_karen_engine.fastapi_stub import (
    FastAPI,
    HTTPException,
    Request,
    JSONResponse,
    Response,
    TestClient,
)
import types
import sys

testclient = types.ModuleType('testclient')
testclient.TestClient = TestClient
sys.modules[__name__ + '.testclient'] = testclient

__all__ = [
    'FastAPI',
    'HTTPException',
    'Request',
    'Response',
    'JSONResponse',
    'TestClient',
    'testclient',
]
