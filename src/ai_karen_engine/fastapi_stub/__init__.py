"""Lightweight FastAPI stub used for testing."""
# mypy: ignore-errors

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
    __slots__ = ("method", "pattern", "func", "tags", "mount")

    def __init__(self, method: str, path: str, func, *, tags=None, mount=False):
        self.method = method
        self.func = func
        self.tags = tags or []
        self.mount = mount
        if mount:
            prefix = path.rstrip("/")
            self.pattern = re.compile(f"^{re.escape(prefix)}(?P<sub>/.*)?$")
        else:
            regex = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
            self.pattern = re.compile(f"^{regex}$")


class FastAPI:
    def __init__(self, *_, **__):
        self.routes = []
        self._startup = []
        self.prefix = ""
        self._middlewares = []

    def add_middleware(self, *_, **__):
        pass

    def middleware(self, _type):
        def decorator(func):
            self._middlewares.append(func)
            return func

        return decorator

    async def _handle_request(self, method, path, json=None, headers=None):
        query = {}
        if "?" in path:
            path, qs = path.split("?", 1)
            query = {k: v[0] for k, v in parse_qs(qs).items()}
        for route in self.routes:
            if route.mount:
                m = route.pattern.match(path)
                if not m:
                    continue
                sub = m.group("sub") or "/"
                return await route.func(method, sub, json)
            if route.method != method:
                continue
            m = route.pattern.match(path)
            if not m:
                continue
            params = {**m.groupdict(), **query}
            if json:
                params.update(json)
            func = route.func
            req_obj = Request()
            req_obj.headers.update(headers or {})
            resp_obj = Response()
            if asyncio.iscoroutinefunction(func):
                try:
                    return await func(**params)
                except TypeError:
                    arg = SimpleNamespace(**params)
                    try:
                        return await func(arg, req_obj, resp_obj)
                    except HTTPException as exc:
                        return Response({"detail": exc.detail}, exc.status_code)
                except HTTPException as exc:
                    return Response({"detail": exc.detail}, exc.status_code)
            try:
                return func(**params)
            except TypeError:
                arg = SimpleNamespace(**params)
                try:
                    return func(arg, req_obj, resp_obj)
                except HTTPException as exc:
                    return Response({"detail": exc.detail}, exc.status_code)
            except HTTPException as exc:
                return Response({"detail": exc.detail}, exc.status_code)
        raise KeyError((method, path))

    async def __call__(self, *args, **kwargs):
        if len(args) == 3 and isinstance(args[0], dict):
            return await self._asgi(*args)  # type: ignore[arg-type]
        method, path, json, headers = args[0], args[1], None, None
        if len(args) > 2:
            json = args[2]
        if len(args) > 3:
            headers = args[3]
        return await self._handle_request(method, path, json, headers)

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
        await send(
            {
                "type": "http.response.start",
                "status": resp.status_code,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": content})

    def get(self, path, **_kw):
        tags = _kw.get("tags")

        def decorator(func):
            self.routes.append(_Route("GET", path, func, tags=tags))
            return func

        return decorator

    def post(self, path, **_kw):
        tags = _kw.get("tags")

        def decorator(func):
            self.routes.append(_Route("POST", path, func, tags=tags))
            return func

        return decorator

    def put(self, path, **_kw):
        tags = _kw.get("tags")

        def decorator(func):
            self.routes.append(_Route("PUT", path, func, tags=tags))
            return func

        return decorator

    def delete(self, path, **_kw):
        tags = _kw.get("tags")

        def decorator(func):
            self.routes.append(_Route("DELETE", path, func, tags=tags))
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

    def include_router(self, router, prefix: str = ""):
        prefix = prefix or getattr(router, "prefix", "")
        tags = getattr(router, "tags", [])
        for route in router.routes:
            route.pattern = re.compile(f"^{prefix}{route.pattern.pattern.lstrip('^')}")
            route.tags = getattr(route, "tags", []) + tags
            self.routes.append(route)

    def mount(self, path: str, app, name: str | None = None):
        self.routes.append(_Route("MOUNT", path, app, mount=True))


class APIRouter(FastAPI):
    def __init__(self, prefix: str = "", tags=None):
        super().__init__()
        self.prefix = prefix
        self.tags = tags or []

    def get(self, path, **_kw):
        tags = _kw.get("tags") or self.tags

        def decorator(func):
            self.routes.append(_Route("GET", path, func, tags=tags))
            return func

        return decorator

    def post(self, path, **_kw):
        tags = _kw.get("tags") or self.tags

        def decorator(func):
            self.routes.append(_Route("POST", path, func, tags=tags))
            return func

        return decorator

    def put(self, path, **_kw):
        tags = _kw.get("tags") or self.tags

        def decorator(func):
            self.routes.append(_Route("PUT", path, func, tags=tags))
            return func

        return decorator

    def delete(self, path, **_kw):
        tags = _kw.get("tags") or self.tags

        def decorator(func):
            self.routes.append(_Route("DELETE", path, func, tags=tags))
            return func

        return decorator


class Response:
    def __init__(self, content=None, status_code=200, media_type=None, headers=None):
        self._data = content
        self.status_code = status_code
        self.headers = {"content-type": media_type or "application/json"}
        if headers:
            self.headers.update(headers)
        self.cookies = {}

    def set_cookie(self, key, value, **_kw):
        self.cookies[key] = value

    def delete_cookie(self, key):
        self.cookies.pop(key, None)

    def json(self):
        if hasattr(self._data, "__dict__"):
            return vars(self._data)
        if isinstance(self._data, list):
            return [vars(x) if hasattr(x, "__dict__") else x for x in self._data]
        return self._data


class JSONResponse(Response):
    pass


class PlainTextResponse(Response):
    def __init__(self, content: str, status_code: int = 200, headers=None):
        super().__init__(content, status_code, media_type="text/plain", headers=headers)


responses = SimpleNamespace(
    JSONResponse=JSONResponse,
    Response=Response,
    PlainTextResponse=PlainTextResponse,
    StreamingResponse=Response,
)
sys.modules["fastapi.responses"] = responses  # type: ignore[assignment]

# Middleware stubs
cors_stub = SimpleNamespace(CORSMiddleware=object)
gzip_stub = SimpleNamespace(GZipMiddleware=object)
sys.modules.setdefault("fastapi.middleware.cors", cors_stub)
sys.modules.setdefault("fastapi.middleware.gzip", gzip_stub)


def Depends(func):
    """Simplistic dependency injection stub."""
    return func


def Query(default=None, **_kw):
    """Simplified Query parameter stub."""
    return default


def File(default=None, **_kw):
    """Simplified File parameter stub."""
    return default


def Form(default=None, **_kw):
    """Simplified Form parameter stub."""
    return default


class UploadFile:
    def __init__(self, filename: str = "", file=None):
        self.filename = filename
        self.file = file


class status:
    HTTP_401_UNAUTHORIZED = 401


class Request:
    def __init__(self, client_host="test"):
        self.client = SimpleNamespace(host=client_host)
        self.headers = {}
        self.cookies = {}


class TestClient:
    def __init__(self, app):
        self.app = app
        for fn in getattr(app, "_startup", []):
            if asyncio.iscoroutinefunction(fn):
                asyncio.run(fn())
            else:
                fn()

    def post(self, path, json=None):
        data = asyncio.run(self.app("POST", path, json))
        status = getattr(data, "status_code", 200)
        resp = Response(
            getattr(data, "_data", data),
            status,
            media_type=data.headers.get("content-type")
            if hasattr(data, "headers")
            else None,
        )
        resp.headers.update(getattr(data, "headers", {}))
        return resp

    def get(self, path):
        data = asyncio.run(self.app("GET", path))
        status = getattr(data, "status_code", 200)
        resp = Response(
            getattr(data, "_data", data),
            status,
            media_type=data.headers.get("content-type")
            if hasattr(data, "headers")
            else None,
        )
        resp.headers.update(getattr(data, "headers", {}))
        return resp
