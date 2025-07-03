import asyncio
from . import Response


class TestClient:
    __test__ = False

    def __init__(self, app):
        self.app = app

    def post(self, path, json=None):
        data = asyncio.run(self.app("POST", path, json))
        if isinstance(data, Response):
            return data
        return Response(data)

    def get(self, path):
        data = asyncio.run(self.app("GET", path))
        if isinstance(data, Response):
            return data
        return Response(data)

