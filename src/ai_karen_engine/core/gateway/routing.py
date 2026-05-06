"""
Production routing setup for the AI Karen FastAPI gateway.

Responsibilities:
- Register core gateway routes: health, readiness, liveness, info, metrics.
- Discover and mount API routers from ai_karen_engine.api_routes safely.
- Mount plugin API routes and optional plugin UI assets.
- Expose service health summaries without leaking raw service configuration.

This module must remain a gateway wiring layer only. It must not own runtime
orchestration, provider/model routing, memory logic, plugin execution policy, or
database access.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI
    from fastapi.responses import JSONResponse, PlainTextResponse

try:
    from fastapi import APIRouter, FastAPI
    from fastapi.responses import JSONResponse, PlainTextResponse
except ImportError:  # pragma: no cover - supports lightweight test stubs
    FastAPI = object  # type: ignore[assignment,misc]
    APIRouter = object  # type: ignore[assignment,misc]
    JSONResponse = object  # type: ignore[assignment,misc]
    PlainTextResponse = object  # type: ignore[assignment,misc]
    JSONResponse = object  # type: ignore[assignment,misc]
    PlainTextResponse = object  # type: ignore[assignment,misc]

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.services import ServiceContainer

logger = get_logger(__name__)

HEALTHY_SERVICE_STATES = {"running", "ready", "healthy"}
DEFAULT_CRITICAL_SERVICES = ("memory_service", "chat_runtime", "expression_gateway")
ROUTE_DISCOVERY_SKIP_MARKERS = (
    ".tests",
    ".test_",
    "_test",
    ".store_mock",
    ".deprecated",
    ".legacy",
    ".experimental",
    ".__pycache__",
)
SENSITIVE_CONFIG_KEY_PATTERN = re.compile(
    r"(secret|token|password|passwd|api[_-]?key|key|credential|dsn|url|uri|cookie|auth)",
    re.IGNORECASE,
)
SAFE_PLUGIN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def utc_now_iso() -> str:
    """Return a timezone-aware UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean-like environment flag."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def env_csv(name: str, default: Iterable[str]) -> list[str]:
    """Read a comma-separated environment value."""
    value = os.getenv(name)
    if not value:
        return [item for item in default if item]
    return [item.strip() for item in value.split(",") if item.strip()]


def service_status_value(service_health: Mapping[str, Any]) -> str:
    """Normalize a service health/status mapping to a status string."""
    value = service_health.get("status", "unknown")
    return str(value).strip().lower()


def is_service_healthy(service_health: Mapping[str, Any]) -> bool:
    """Return whether a service health mapping is considered ready/healthy."""
    return service_status_value(service_health) in HEALTHY_SERVICE_STATES


def route_exists(app: Any, path_prefix: str) -> bool:
    """Return whether the app already has a route mounted under a prefix."""
    normalized_prefix = normalize_route_path(path_prefix)
    for route in getattr(app, "routes", []):
        path = normalize_route_path(getattr(route, "path", ""))
        if path == normalized_prefix or path.startswith(f"{normalized_prefix}/"):
            return True
    return False


def normalize_route_path(path: str) -> str:
    """Normalize route path for duplicate checks and logging."""
    if not path:
        return ""
    normalized = re.sub(r"/{2,}", "/", path)
    if len(normalized) > 1:
        normalized = normalized.rstrip("/")
    return normalized


def join_route_paths(*parts: str) -> str:
    """Join route path parts without producing duplicate slashes."""
    cleaned = [part.strip("/") for part in parts if part]
    if not cleaned:
        return ""
    return normalize_route_path("/" + "/".join(cleaned))


def should_skip_route_module(full_name: str) -> bool:
    """Return whether a discovered module should be skipped."""
    return any(marker in full_name for marker in ROUTE_DISCOVERY_SKIP_MARKERS)


def router_route_count(router: Any) -> int:
    """Return the number of routes on a router-like object."""
    return len(getattr(router, "routes", []) or [])


def get_current_correlation_id() -> str | None:
    """
    Best-effort correlation ID lookup.

    This intentionally avoids hard dependency on a specific logging context
    implementation so gateway routing can be imported in lightweight test
    environments.
    """
    try:
        from ai_karen_engine.core.logging.context import get_log_context

        context = get_log_context()
        return getattr(context, "correlation_id", None)
    except Exception:
        return None


def safe_error_content(
    *,
    error: str,
    code: str,
    status: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a safe client-facing error payload."""
    payload: dict[str, Any] = {
        "error": error,
        "code": code,
        "timestamp": utc_now_iso(),
    }

    correlation_id = get_current_correlation_id()
    if correlation_id:
        payload["correlation_id"] = correlation_id

    if status is not None:
        payload["status_code"] = status

    if extra:
        payload.update(extra)

    return payload


def to_plain_mapping(value: Any) -> dict[str, Any]:
    """Convert a pydantic/dataclass/dict-like object to a plain dict when safe."""
    if value is None:
        return {}

    if isinstance(value, dict):
        return dict(value)

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            dumped = model_dump()
            return dict(dumped) if isinstance(dumped, dict) else {}
        except Exception:
            return {}

    legacy_dict = getattr(value, "dict", None)
    if callable(legacy_dict):
        try:
            dumped = legacy_dict()
            return dict(dumped) if isinstance(dumped, dict) else {}
        except Exception:
            return {}

    return {}


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Redact sensitive-looking config keys recursively."""
    redacted: dict[str, Any] = {}

    for key, value in mapping.items():
        key_text = str(key)
        if SENSITIVE_CONFIG_KEY_PATTERN.search(key_text):
            redacted[key_text] = "***REDACTED***"
            continue

        if isinstance(value, Mapping):
            redacted[key_text] = redact_mapping(value)
        elif isinstance(value, list):
            redacted[key_text] = [
                redact_mapping(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            redacted[key_text] = value

    return redacted


def safe_service_config_summary(config: Any) -> dict[str, Any]:
    """
    Return a safe service config summary.

    Raw config is not exposed by default. Only low-risk public operational fields
    are included, and every key is still passed through redaction.
    """
    raw = to_plain_mapping(config)
    if not raw:
        return {"redacted": True}

    allowed_keys = {
        "name",
        "service_name",
        "enabled",
        "mode",
        "version",
        "environment",
        "profile",
        "debug",
        "feature_flags",
    }

    safe = {key: value for key, value in raw.items() if str(key) in allowed_keys}
    safe["redacted"] = True
    return redact_mapping(safe)


def safe_health_payload(health: Any) -> dict[str, Any]:
    """Convert service health into a safe response payload."""
    health_payload = to_plain_mapping(health)
    if health_payload:
        return redact_mapping(health_payload)

    return {
        "status": str(getattr(health, "status", "unknown")),
    }


def safe_metrics_payload(metrics: Any) -> dict[str, Any]:
    """Convert service metrics to a safe response payload."""
    if callable(metrics):
        try:
            metrics = metrics()
        except Exception:
            return {"available": False}

    if isinstance(metrics, Mapping):
        return redact_mapping(metrics)

    return {}


def sanitize_plugin_id(plugin_id: str) -> str | None:
    """Return a path-safe plugin ID or None."""
    if not plugin_id or not SAFE_PLUGIN_ID_PATTERN.match(plugin_id):
        return None
    return plugin_id


def is_child_path(child: Path, parent: Path) -> bool:
    """Return whether child is inside parent after resolving paths."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def log_info(event: str, **fields: Any) -> None:
    """Best-effort structured info logging."""
    try:
        logger.info(event, **fields)
    except TypeError:
        logger.info("%s %s", event, fields)


def log_warning(event: str, **fields: Any) -> None:
    """Best-effort structured warning logging."""
    try:
        logger.warning(event, **fields)
    except TypeError:
        logger.warning("%s %s", event, fields)


def log_error(event: str, **fields: Any) -> None:
    """Best-effort structured error logging."""
    try:
        logger.error(event, **fields)
    except TypeError:
        logger.error("%s %s", event, fields)


def log_exception(event: str, **fields: Any) -> None:
    """Best-effort structured exception logging."""
    try:
        logger.exception(event, **fields)
    except TypeError:
        logger.exception("%s %s", event, fields)


def setup_health_routes(app: FastAPI, service_container: ServiceContainer) -> None:  # type: ignore[valid-type]
    """
    Setup health check routes.

    /livez:
        Process liveness. Should be cheap and always avoid dependency checks.

    /readyz:
        Critical service readiness. Intended for Kubernetes/readiness probes.

    /health:
        Full service health report.
    """

    @app.get("/health", response_class=JSONResponse, tags=["Health"])
    async def health_check():
        """Comprehensive health check endpoint."""
        try:
            service_health = service_container.get_service_health()
            all_healthy = all(
                is_service_healthy(service)
                for service in service_health.values()
                if isinstance(service, Mapping)
            )

            unhealthy_services = [
                service_name
                for service_name, service in service_health.items()
                if isinstance(service, Mapping) and not is_service_healthy(service)
            ]

            status = "healthy" if all_healthy else "degraded"

            log_info(
                "gateway.health.checked",
                status=status,
                unhealthy_services=unhealthy_services,
            )

            return {
                "status": status,
                "version": os.getenv("KAREN_VERSION", "1.0.0"),
                "environment": os.getenv("KAREN_ENV", "development"),
                "timestamp": utc_now_iso(),
                "degraded": not all_healthy,
                "critical_failures": unhealthy_services,
                "services": redact_mapping(service_health),
            }

        except Exception as exc:
            log_exception(
                "gateway.health.failed",
                error_type=type(exc).__name__,
            )
            return JSONResponse(  # type: ignore[call-arg]
                status_code=503,
                content=safe_error_content(
                    error="Health check failed",
                    code="health_check_failed",
                    status=503,
                    extra={"status": "unhealthy"},
                ),
            )

    @app.get("/livez", response_class=PlainTextResponse, tags=["Health"])
    async def liveness_probe():
        """Kubernetes liveness probe endpoint."""
        return "ok"

    @app.get("/readyz", response_class=PlainTextResponse, tags=["Health"])
    async def readiness_probe():
        """Kubernetes readiness probe endpoint."""
        critical_services = env_csv(
            "KAREN_CRITICAL_SERVICES",
            DEFAULT_CRITICAL_SERVICES,
        )

        try:
            service_health = service_container.get_service_health()
            missing_services: list[str] = []
            failing_services: list[str] = []

            for service_name in critical_services:
                service = service_health.get(service_name)
                if service is None:
                    missing_services.append(service_name)
                    continue
                if isinstance(service, Mapping) and not is_service_healthy(service):
                    failing_services.append(service_name)

            ready = not missing_services and not failing_services

            log_info(
                "gateway.ready.checked",
                ready=ready,
                critical_services=critical_services,
                missing_services=missing_services,
                failing_services=failing_services,
            )

            if ready:
                return "ready"

            return PlainTextResponse("not ready", status_code=503)  # type: ignore[call-arg]

        except Exception as exc:
            log_exception(
                "gateway.ready.failed",
                error_type=type(exc).__name__,
                critical_services=critical_services,
            )
            return PlainTextResponse("not ready", status_code=503)  # type: ignore[call-arg]


def setup_info_routes(app: FastAPI) -> None:  # type: ignore[valid-type]
    """Setup public information routes."""

    @app.get("/", response_class=JSONResponse, tags=["Info"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "AI Karen Engine",
            "message": "Welcome to the AI Karen Engine API Gateway",
            "version": os.getenv("KAREN_VERSION", "1.0.0"),
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "timestamp": utc_now_iso(),
        }

    @app.get("/info", response_class=JSONResponse, tags=["Info"])
    async def info():
        """Detailed service information."""
        return {
            "name": "AI Karen Engine",
            "version": os.getenv("KAREN_VERSION", "1.0.0"),
            "environment": os.getenv("KAREN_ENV", "development"),
            "debug": env_flag("KAREN_DEBUG", default=False),
            "timestamp": utc_now_iso(),
            "features": {
                "ai_orchestration": True,
                "memory_management": True,
                "plugin_execution": True,
                "tool_abstraction": True,
                "conversation_management": True,
                "analytics": True,
                "expression_gateway": True,
            },
        }


def setup_metrics_routes(app: FastAPI) -> None:  # type: ignore[valid-type]
    """Setup metrics routes."""
    if route_exists(app, "/metrics"):
        log_warning("gateway.metrics.already_mounted", path="/metrics")
        return

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, make_asgi_app

        if hasattr(app, "mount"):
            metrics_app = make_asgi_app()
            app.mount("/metrics", metrics_app)
            log_info("gateway.metrics.mounted", path="/metrics", mode="asgi")
            return

        @app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
        async def prometheus_metrics():
            """Prometheus metrics endpoint."""
            return PlainTextResponse(  # type: ignore[call-arg]
                generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )

        log_info("gateway.metrics.mounted", path="/metrics", mode="plain_text")

    except ImportError:
        log_warning(
            "gateway.metrics.unavailable",
            reason="prometheus_client_missing",
        )

        @app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
        async def basic_metrics():
            """Basic metrics endpoint when Prometheus is not available."""
            return (
                "# Prometheus client not available\n"
                "# Install prometheus_client for full metrics support\n"
            )


def derive_route_prefix(module_name: str, router_prefix: str) -> tuple[str, str]:
    """
    Derive include_router prefix and final prefix.

    Returns:
        (include_prefix, final_prefix)
    """
    name = module_name.rsplit(".", 1)[-1]

    if router_prefix:
        if router_prefix.startswith("/api/"):
            include_prefix = ""
        elif name == "management" and router_prefix == "/plugins":
            include_prefix = "/api"
        else:
            include_prefix = "/api"

        final_prefix = normalize_route_path(
            include_prefix + router_prefix if include_prefix else router_prefix
        )
        return include_prefix, final_prefix

    base_name = name.replace("_routes", "").replace("_api", "")
    plural_resources = {
        "persona",
        "conversation",
        "plugin",
        "provider",
        "tool",
        "plan",
        "user",
    }

    if base_name in plural_resources:
        base_name = f"{base_name}s"

    include_prefix = f"/api/{base_name}"
    return include_prefix, normalize_route_path(include_prefix)


def mount_router_once(
    app: FastAPI,  # type: ignore[valid-type]
    router: APIRouter,  # type: ignore[valid-type]
    *,
    include_prefix: str,
    final_prefix: str,
    tags: list[str],
    module_name: str,
    mounted_prefixes: set[str],
) -> bool:
    """Mount a router if the final prefix has not already been mounted."""
    normalized_final_prefix = normalize_route_path(final_prefix)

    if normalized_final_prefix in mounted_prefixes or route_exists(
        app,
        normalized_final_prefix,
    ):
        log_warning(
            "gateway.api.router.duplicate_prefix_skipped",
            module=module_name,
            prefix=normalized_final_prefix,
        )
        return False

    app.include_router(router, prefix=include_prefix, tags=tags)
    mounted_prefixes.add(normalized_final_prefix)

    log_info(
        "gateway.api.router.mounted",
        module=module_name,
        include_prefix=include_prefix,
        final_prefix=normalized_final_prefix,
        route_count=router_route_count(router),
    )

    for route in getattr(router, "routes", []) or []:
        route_path = normalize_route_path(getattr(route, "path", ""))
        route_methods = sorted(getattr(route, "methods", []) or [])
        log_info(
            "gateway.api.route.mounted",
            module=module_name,
            methods=route_methods,
            path=join_route_paths(normalized_final_prefix, route_path),
        )

    return True


def discover_and_mount_api_routes(app: FastAPI) -> None:  # type: ignore[valid-type]
    """Discover and mount API routes from the api_routes package."""
    if not env_flag("KAREN_GATEWAY_AUTO_DISCOVER_ROUTES", default=True):
        log_info("gateway.api.discovery.skipped", reason="disabled_by_config")
        return

    strict_discovery = env_flag("KAREN_GATEWAY_ROUTE_DISCOVERY_STRICT", default=True)
    mounted_prefixes: set[str] = set()
    failed_modules: list[dict[str, str]] = []

    try:
        from ai_karen_engine import api_routes

        log_info(
            "gateway.api.discovery.started",
            package_path=[str(path) for path in getattr(api_routes, "__path__", [])],
            strict=strict_discovery,
        )

        for _, full_name, _ in pkgutil.walk_packages(
            api_routes.__path__,
            prefix="ai_karen_engine.api_routes.",
        ):
            name = full_name.rsplit(".", 1)[-1]

            if should_skip_route_module(full_name):
                log_info(
                    "gateway.api.discovery.module_skipped",
                    module=full_name,
                    reason="filtered_by_name",
                )
                continue

            log_info("gateway.api.discovery.module_found", module=full_name)

            try:
                module = importlib.import_module(full_name)
            except Exception as exc:
                failed_modules.append(
                    {
                        "module": full_name,
                        "error_type": type(exc).__name__,
                    }
                )
                log_exception(
                    "gateway.api.discovery.import_failed",
                    module=full_name,
                    error_type=type(exc).__name__,
                )
                if strict_discovery:
                    continue
                continue

            router = getattr(module, "router", None)
            if isinstance(router, APIRouter) and hasattr(router, "routes"):
                router_prefix = getattr(router, "prefix", "") or ""
                include_prefix, final_prefix = derive_route_prefix(
                    full_name,
                    router_prefix,
                )

                mount_router_once(
                    app,
                    router,
                    include_prefix=include_prefix,
                    final_prefix=final_prefix,
                    tags=[name],
                    module_name=full_name,
                    mounted_prefixes=mounted_prefixes,
                )

            public_router = getattr(module, "public_router", None)
            if isinstance(public_router, APIRouter) and hasattr(
                public_router,
                "routes",
            ):
                if name == "provider_routes":
                    include_prefix = "/api/public/providers"
                    final_prefix = include_prefix
                    tags = ["public-providers"]
                else:
                    include_prefix = f"/api/public/{name}"
                    final_prefix = include_prefix
                    tags = [f"public-{name}"]

                mount_router_once(
                    app,
                    public_router,
                    include_prefix=include_prefix,
                    final_prefix=final_prefix,
                    tags=tags,
                    module_name=f"{full_name}:public_router",
                    mounted_prefixes=mounted_prefixes,
                )

        log_info(
            "gateway.api.discovery.completed",
            mounted_prefixes=sorted(mounted_prefixes),
            failed_modules=failed_modules,
        )

    except ImportError as exc:
        log_warning(
            "gateway.api.discovery.unavailable",
            error_type=type(exc).__name__,
        )


def discover_and_mount_plugin_routes(app: FastAPI) -> None:  # type: ignore[valid-type]
    """Discover and mount plugin routes."""
    if route_exists(app, "/plugins"):
        log_warning(
            "gateway.plugin.router.duplicate_prefix_skipped",
            prefix="/plugins",
        )
        return

    try:
        from ai_karen_engine.extensions.platform.core import get_plugin_router

        router = get_plugin_router()
        api_router = router.get_api_router()
        app.include_router(api_router, prefix="/plugins", tags=["plugins"])
        log_info(
            "gateway.plugin.router.mounted",
            prefix="/plugins",
            route_count=router_route_count(api_router),
        )

    except Exception as exc:
        log_exception(
            "gateway.plugin.router.mount_failed",
            error_type=type(exc).__name__,
        )


def plugin_ui_enabled(record: Any) -> bool:
    """
    Return whether a plugin record is allowed to expose static UI assets.

    The manifest shape differs across plugin systems, so this uses safe,
    conservative best-effort checks. If the plugin has no explicit UI controls,
    the global mount flag still governs whether UI assets are exposed.
    """
    manifest = getattr(record, "manifest", None)
    if manifest is None:
        manifest = getattr(record, "plugin_manifest", None)

    if manifest is None and isinstance(record, Mapping):
        manifest = record.get("manifest") or record.get("plugin_manifest")

    if manifest is None:
        return True

    manifest_data = to_plain_mapping(manifest)
    if not manifest_data and isinstance(manifest, Mapping):
        manifest_data = dict(manifest)

    ui_config = manifest_data.get("ui") or manifest_data.get("frontend") or {}

    if isinstance(ui_config, Mapping):
        if ui_config.get("enabled") is False:
            return False
        if ui_config.get("static_mount") is False:
            return False

    if manifest_data.get("ui_enabled") is False:
        return False

    return True


def discover_and_mount_plugin_ui(app: FastAPI) -> None:  # type: ignore[valid-type]
    """
    Discover and mount static UI assets for plugins.

    Controlled by KAREN_PLUGIN_UI_MOUNT_ENABLED. Static plugin UI mounting must
    never serve files outside the plugin directory.
    """
    if not env_flag("KAREN_PLUGIN_UI_MOUNT_ENABLED", default=True):
        log_info("gateway.plugin.ui.discovery_skipped", reason="disabled_by_config")
        return

    try:
        from fastapi.staticfiles import StaticFiles

        from ai_karen_engine.extensions.platform.core import get_plugin_manager

        manager = get_plugin_manager()
        registry = manager.registry

        for plugin_id, record in registry.get_all_manifests().items():
            safe_plugin_id = sanitize_plugin_id(str(plugin_id))
            if safe_plugin_id is None:
                log_warning(
                    "gateway.plugin.ui.mount_skipped",
                    plugin_id=str(plugin_id),
                    reason="unsafe_plugin_id",
                )
                continue

            if not plugin_ui_enabled(record):
                log_info(
                    "gateway.plugin.ui.mount_skipped",
                    plugin_id=safe_plugin_id,
                    reason="disabled_by_manifest",
                )
                continue

            plugin_dir = Path(getattr(record, "dir_path", ""))
            if not plugin_dir:
                log_warning(
                    "gateway.plugin.ui.mount_skipped",
                    plugin_id=safe_plugin_id,
                    reason="missing_plugin_dir",
                )
                continue

            ui_path = plugin_dir / "ui"
            if not ui_path.exists() or not ui_path.is_dir():
                continue

            if not is_child_path(ui_path, plugin_dir):
                log_warning(
                    "gateway.plugin.ui.mount_skipped",
                    plugin_id=safe_plugin_id,
                    reason="ui_path_outside_plugin_dir",
                )
                continue

            mount_path = f"/extensions/{safe_plugin_id}/ui"
            if route_exists(app, mount_path):
                log_warning(
                    "gateway.plugin.ui.duplicate_mount_skipped",
                    plugin_id=safe_plugin_id,
                    mount_path=mount_path,
                )
                continue

            app.mount(
                mount_path,
                StaticFiles(directory=str(ui_path), html=True),
                name=f"ui_{safe_plugin_id}",
            )
            log_info(
                "gateway.plugin.ui.mounted",
                plugin_id=safe_plugin_id,
                mount_path=mount_path,
            )

    except Exception as exc:
        log_exception(
            "gateway.plugin.ui.mount_failed",
            error_type=type(exc).__name__,
        )


def setup_service_routes(app: FastAPI, service_container: ServiceContainer) -> None:  # type: ignore[valid-type]
    """
    Setup service management routes.

    These routes expose sanitized operational service information. They do not
    expose raw service configuration. In production deployments, access should
    be protected at the app/auth middleware layer or moved behind admin routes.
    """

    service_routes_enabled = env_flag("KAREN_GATEWAY_SERVICE_ROUTES_ENABLED", default=True)

    if not service_routes_enabled:
        log_info("gateway.service.routes.skipped", reason="disabled_by_config")
        return

    @app.get("/services", response_class=JSONResponse, tags=["Services"])
    async def list_services():
        """List all registered services with sanitized health metadata."""
        try:
            services = service_container.get_all_services()
            log_info(
                "gateway.service.list.requested",
                service_count=len(services),
            )
            return {
                "timestamp": utc_now_iso(),
                "services": [
                    {
                        "name": name,
                        "status": str(getattr(service.status, "value", service.status)),
                        "health": safe_health_payload(getattr(service, "health", None)),
                    }
                    for name, service in services.items()
                ],
            }
        except Exception as exc:
            log_exception(
                "gateway.service.list.failed",
                error_type=type(exc).__name__,
            )
            return JSONResponse(
                status_code=500,  # type: ignore[call-arg]
                content=safe_error_content(  # type: ignore[call-arg]
                    error="Failed to list services",
                    code="service_list_failed",
                    status=500,
                ),
            )

    @app.get("/services/{service_name}", response_class=JSONResponse, tags=["Services"])
    async def get_service_info(service_name: str):
        """Get sanitized operational information for a specific service."""
        try:
            service = service_container.get_service(service_name)
            log_info(
                "gateway.service.detail.requested",
                service_name=service_name,
            )

            return {
                "timestamp": utc_now_iso(),
                "name": getattr(service, "name", service_name),
                "status": str(getattr(service.status, "value", service.status)),
                "health": safe_health_payload(getattr(service, "health", None)),
                "metrics": safe_metrics_payload(getattr(service, "get_metrics", None)),
                "config": safe_service_config_summary(getattr(service, "config", None)),
            }

        except ValueError:
            log_warning(
                "gateway.service.detail.not_found",
                service_name=service_name,
            )
            return JSONResponse(
                status_code=404,  # type: ignore[call-arg]
                content=safe_error_content(  # type: ignore[call-arg]
                    error="Service not found",
                    code="service_not_found",
                    status=404,
                    extra={"service_name": service_name},
                ),
            )

        except Exception as exc:
            log_exception(
                "gateway.service.detail.failed",
                service_name=service_name,
                error_type=type(exc).__name__,
            )
            return JSONResponse(
                status_code=500,  # type: ignore[call-arg]
                content=safe_error_content(  # type: ignore[call-arg]
                    error="Failed to get service info",
                    code="service_detail_failed",
                    status=500,
                ),
            )


def setup_memory_routes_fallback(app: FastAPI) -> None:  # type: ignore[valid-type]
    """Manually register memory routes only if discovery did not mount them."""
    if route_exists(app, "/api/memory"):
        log_info(
            "gateway.memory.manual_registration_skipped",
            reason="already_mounted",
            prefix="/api/memory",
        )
        return

    try:
        from ai_karen_engine.api_routes.memory.memory import router as memory_router

        app.include_router(memory_router, prefix="/api", tags=["memory"])
        log_info(
            "gateway.memory.manual_registration_completed",
            prefix="/api/memory",
            route_count=router_route_count(memory_router),
        )

    except Exception as exc:
        log_warning(
            "gateway.memory.manual_registration_failed",
            error_type=type(exc).__name__,
        )


def setup_routing(app: FastAPI, service_container: ServiceContainer) -> None:  # type: ignore[valid-type]
    """
    Setup all routing for the FastAPI application.

    Args:
        app: FastAPI application.
        service_container: Service container.
    """
    log_info("gateway.routing.setup.started")

    setup_health_routes(app, service_container)
    setup_info_routes(app)
    setup_metrics_routes(app)
    setup_service_routes(app, service_container)

    discover_and_mount_api_routes(app)
    setup_memory_routes_fallback(app)

    discover_and_mount_plugin_routes(app)
    discover_and_mount_plugin_ui(app)

    log_info("gateway.routing.setup.completed")