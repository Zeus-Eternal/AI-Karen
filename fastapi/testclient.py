import asyncio
from . import Response

class TestClient:
    __test__ = False  # Prevent pytest from collecting this class as tests
    
    def __init__(self, app):
        self.app = app

    def post(self, path, json=None):
        data = asyncio.run(self.app("POST", path, json))
        return Response(data)

    def get(self, path):
        data = asyncio.run(self.app("GET", path))
        return Response(data)
