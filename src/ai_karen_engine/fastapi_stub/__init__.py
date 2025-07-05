import asyncio
import json
import re
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _Route:
    __slots__ = ("method", "pattern", "func")

    def __init__(self, method: str, path: str, func):
        regex = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        self.method = method
        self.pattern = re.compile(f"^{regex}$")
        self.func = func

class FastAPI:
    def __init__(self):
        self.routes = []
        self._startup = []

    def get(self, path):
        def decorator(func):
            self.routes.append(_Route("GET", path, func))
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.routes.append(_Route("POST", path, func))
            return func
        return decorator

    def on_event(self, event: str):
        def decorator(func):
            if event == "startup":
                self._startup.append(func)
            return func
        return decorator

    def exception_handler(self, exc):
        def decorator(func):
            return func
        return decorator

    async def _handle_request(self, method, path, json=None):
        query = {}
        if "?" in path:
            path, qs = path.split("?", 1)
            query = {k: v[0] for k, v in parse_qs(qs).items()}
        for route in self.routes:
            if route.method != method:
                continue
            m = route.pattern.match(path)
            if not m:
                continue
            params = {**m.groupdict(), **query}
            if json:
                params.update(json)
            func = route.func
            if asyncio.iscoroutinefunction(func):
                try:
                    return await func(**params)
                except TypeError:
                    arg = SimpleNamespace(**params)
                    try:
                        return await func(arg)
                    except HTTPException as exc:
                        return Response({"detail": exc.detail}, exc.status_code)
                except HTTPException as exc:
                    return Response({"detail": exc.detail}, exc.status_code)
            try:
                return func(**params)
            except TypeError:
                arg = SimpleNamespace(**params)
                try:
                    return func(arg)
                except HTTPException as exc:
                    return Response({"detail": exc.detail}, exc.status_code)
            except HTTPException as exc:
                return Response({"detail": exc.detail}, exc.status_code)
        raise KeyError((method, path))

    async def __call__(self, *args, **kwargs):
        if len(args) == 3 and isinstance(args[0], dict):
            return await self._asgi(*args)  # type: ignore[arg-type]
        return await self._handle_request(*args, **kwargs)

    async def _asgi(self, scope, receive, send):
        assert scope["type"] == "http"
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        json_data = None
        if body:
            try:
                json_data = json.loads(body.decode())
            except Exception:
                json_data = None
        data = await self._handle_request(scope["method"], scope["path"], json_data)
        resp = Response(data)
        content = json.dumps(resp.json()).encode()
        headers = [(b"content-type", b"application/json")]
        await send({"type": "http.response.start", "status": resp.status_code, "headers": headers})
        await send({"type": "http.response.body", "body": content})

class Response:
    def __init__(self, data, status_code=200, media_type=None, headers=None):
        self._data = data
        self.status_code = status_code
        self.headers = {"content-type": media_type or "application/json"}
        if headers:
            self.headers.update(headers)

    def json(self):
        if hasattr(self._data, "__dict__"):
            return vars(self._data)
        if isinstance(self._data, list):
            return [vars(x) if hasattr(x, "__dict__") else x for x in self._data]
        return self._data


class JSONResponse(Response):
    pass


responses = SimpleNamespace(JSONResponse=JSONResponse)
sys.modules["fastapi.responses"] = responses


class Request:
    pass

class TestClient:
    def __init__(self, app):
        self.app = app

    def post(self, path, json=None):
        data = asyncio.run(self.app("POST", path, json))
        status = getattr(data, "status_code", 200)
        resp = Response(
            getattr(data, "_data", data),
            status,
            media_type=data.headers.get("content-type") if hasattr(data, "headers") else None,
        )
        resp.headers.update(getattr(data, "headers", {}))
        return resp

    def get(self, path):
        data = asyncio.run(self.app("GET", path))
        status = getattr(data, "status_code", 200)
        resp = Response(
            getattr(data, "_data", data),
            status,
            media_type=data.headers.get("content-type") if hasattr(data, "headers") else None,
        )
        resp.headers.update(getattr(data, "headers", {}))
        return resp
