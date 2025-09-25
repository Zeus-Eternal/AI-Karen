# mypy: ignore-errors
# ruff: noqa: E402
import importlib
import sys

sys.modules.pop("fastapi", None)
sys.modules.pop("fastapi.exceptions", None)
sys.modules.pop("fastapi.responses", None)
sys.modules.pop("fastapi.testclient", None)
sys.modules.pop("pydantic", None)

sys.modules["fastapi"] = importlib.import_module("fastapi")
sys.modules["fastapi.exceptions"] = importlib.import_module("fastapi.exceptions")
sys.modules["fastapi.responses"] = importlib.import_module("fastapi.responses")
sys.modules["fastapi.testclient"] = importlib.import_module("fastapi.testclient")
sys.modules["pydantic"] = importlib.import_module("pydantic")

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel


class Item(BaseModel):
    value: int


def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(400)  # type: ignore[misc]
    async def bad_request_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:  # pragma: no cover
        return JSONResponse({"detail": "Bad Request"}, status_code=400)

    @app.exception_handler(RequestValidationError)  # type: ignore[misc]
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:  # pragma: no cover
        return JSONResponse({"detail": "Unprocessable Entity"}, status_code=422)

    @app.get("/trigger400")  # type: ignore[misc]
    async def trigger400() -> None:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Bad Request")

    @app.post("/trigger422")  # type: ignore[misc]
    async def trigger422(item: Item) -> Item:  # pragma: no cover
        return item

    return app


def test_consistent_json_error_responses() -> None:
    app = create_test_app()
    client = TestClient(app)

    resp = client.get("/trigger400")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Bad Request"

    resp = client.post("/trigger422", json={"wrong": "data"})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Unprocessable Entity"

    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Not Found"

    resp = client.post("/trigger400")
    assert resp.status_code == 405
    assert resp.json()["detail"] == "Method Not Allowed"
