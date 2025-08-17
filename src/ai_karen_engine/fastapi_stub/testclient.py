import asyncio
from fastapi_stub import Response


class TestClient:
    __test__ = False

    def __init__(self, app):
        self.app = app
        for fn in getattr(app, "_startup", []):
            if asyncio.iscoroutinefunction(fn):
                asyncio.run(fn())
            else:
                fn()

    def post(self, path, json=None, headers=None):
        data = asyncio.run(self.app("POST", path, json, headers))
        if isinstance(data, Response):
            return data
        resp = Response(data)
        resp.headers.update(headers or {})
        return resp

    def get(self, path, headers=None):
        data = asyncio.run(self.app("GET", path, None, headers))
        if isinstance(data, Response):
            resp = data
        else:
            resp = Response(data)
        resp.headers.update(headers or {})
        return resp

