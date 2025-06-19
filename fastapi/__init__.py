import asyncio

class FastAPI:
    def __init__(self):
        self.routes = {}

    def get(self, path):
        def decorator(func):
            self.routes[("GET", path)] = func
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.routes[("POST", path)] = func
            return func
        return decorator

    async def __call__(self, method, path, json=None):
        func = self.routes[(method, path)]
        if json is not None:
            from types import SimpleNamespace

            arg = SimpleNamespace(**json)
        else:
            arg = None

        if asyncio.iscoroutinefunction(func):
            if arg is None:
                return await func()
            else:
                return await func(arg)
        else:
            if arg is None:
                return func()
            else:
                return func(arg)

class Response:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

class TestClient:
    def __init__(self, app):
        self.app = app

    def post(self, path, json=None):
        data = asyncio.run(self.app("POST", path, json))
        return Response(data)

    def get(self, path):
        data = asyncio.run(self.app("GET", path))
        return Response(data)
