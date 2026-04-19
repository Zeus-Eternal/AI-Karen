import logging
from typing import Any, Dict, Optional

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionContext,
    HookContext,
    HookPoint,
)

logger = logging.getLogger(__name__)


class WeatherQueryHandler(ExtensionBase):
    """
    Weather query intent handler.

    Responsibilities:
    - Prepare a normalized weather strategy payload
    - Implement the required ExtensionBase contract
    - Return structured intent payloads for orchestrator/runtime use
    - Do NOT call external weather APIs directly
    """

    MODE = "weather"

    DEFAULTS: Dict[str, Any] = {
        "units": "auto",
        "query_strategy": "location_first",
        "require_citations": False,
        "include_current": True,
        "include_hourly": False,
        "include_daily": False,
        "include_alerts": True,
        "max_forecast_days": 5,
    }

    def __init__(self, manifest: Any, context: ExtensionContext):
        super().__init__(manifest, context)

    async def initialize(self) -> None:
        """
        Initialize extension resources.

        This intent extension is lightweight and does not allocate external
        resources, but initialization is still required by the host contract.
        """
        self.logger.debug(
            "Initializing weather query extension",
            extra={
                "extension_name": getattr(self.manifest, "name", self.__class__.__name__),
                "mode": self.MODE,
            },
        )

    async def shutdown(self) -> None:
        """
        Shutdown extension resources.

        No external resources are currently allocated by this intent extension.
        """
        self.logger.debug(
            "Shutting down weather query extension",
            extra={
                "extension_name": getattr(self.manifest, "name", self.__class__.__name__),
                "mode": self.MODE,
            },
        )

    async def execute_hook(
        self,
        hook_point: HookPoint,
        context: HookContext,
    ) -> Dict[str, Any]:
        """
        Execute a supported hook by converting the host context into
        a normalized intent-preparation request.
        """
        if not self.supports_hook_point(hook_point):
            return {
                "success": False,
                "can_execute": False,
                "error": f"Unsupported hook point: {hook_point.value}",
                "hook_point": hook_point.value,
                "mode": self.MODE,
            }

        payload = self._extract_hook_payload(context)
        query = payload.get("query", "") or ""
        request_context = payload.get("context", {}) or {}

        prepared = await self.prepare(query, request_context)
        executed = await self.execute(prepared, query)

        return {
            "success": executed.get("can_execute", False),
            "hook_point": hook_point.value,
            "result": executed,
        }

    async def prepare(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a normalized weather strategy payload.
        """
        safe_context = context or {}
        normalized_query = self._normalize_query(query)
        can_execute, reason = self._can_execute(normalized_query, safe_context)

        units = self._normalize_units(
            safe_context.get("units"),
            self._read_manifest_setting("units"),
            self.DEFAULTS["units"],
        )
        include_current = self._coerce_bool(
            safe_context.get("include_current"),
            self._read_manifest_setting("include_current"),
            self.DEFAULTS["include_current"],
        )
        include_hourly = self._coerce_bool(
            safe_context.get("include_hourly"),
            self._read_manifest_setting("include_hourly"),
            self.DEFAULTS["include_hourly"],
        )
        include_daily = self._coerce_bool(
            safe_context.get("include_daily"),
            self._read_manifest_setting("include_daily"),
            self.DEFAULTS["include_daily"],
        )
        include_alerts = self._coerce_bool(
            safe_context.get("include_alerts"),
            self._read_manifest_setting("include_alerts"),
            self.DEFAULTS["include_alerts"],
        )
        max_forecast_days = self._coerce_positive_int(
            safe_context.get("max_forecast_days"),
            self._read_manifest_setting("max_forecast_days"),
            self.DEFAULTS["max_forecast_days"],
        )

        location = self._normalize_string(
            safe_context.get("location")
            or safe_context.get("city")
            or safe_context.get("place")
        )
        latitude = self._coerce_float_or_none(safe_context.get("latitude"))
        longitude = self._coerce_float_or_none(safe_context.get("longitude"))

        response = {
            "extension_id": self._get_manifest_id(),
            "extension_name": self._get_manifest_name(),
            "intent_type": "weather",
            "mode": self.MODE,
            "query": normalized_query,
            "can_execute": can_execute,
            "reason": reason,
            "query_strategy": "location_first",
            "require_citations": False,
            "location": {
                "name": location,
                "latitude": latitude,
                "longitude": longitude,
            },
            "weather_profile": {
                "units": units,
                "include_current": include_current,
                "include_hourly": include_hourly,
                "include_daily": include_daily,
                "include_alerts": include_alerts,
                "max_forecast_days": max_forecast_days,
            },
            "time_policy": {
                "requested_date": self._normalize_string(safe_context.get("requested_date")),
                "requested_time": self._normalize_string(safe_context.get("requested_time")),
                "time_range": self._normalize_string(safe_context.get("time_range")),
            },
            "context_hints": self._extract_context_hints(safe_context),
            "telemetry": {
                "handler": self.__class__.__name__,
                "manifest_id": self._get_manifest_id(),
                "mode": self.MODE,
            },
        }

        self.logger.debug(
            "Prepared weather intent strategy",
            extra={
                "extension_id": response["extension_id"],
                "mode": response["mode"],
                "can_execute": response["can_execute"],
                "location": response["location"]["name"],
            },
        )

        return response

    async def execute(self, config: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Runtime compatibility hook.

        This extension returns a normalized, execution-ready strategy payload
        and does not perform external side effects.
        """
        prepared = dict(config or {})
        normalized_query = self._normalize_query(query or prepared.get("query", ""))

        if not prepared.get("query"):
            prepared["query"] = normalized_query

        if "can_execute" not in prepared or "reason" not in prepared:
            can_execute, reason = self._can_execute(
                normalized_query,
                {"location": prepared.get("location", {}).get("name")},
            )
            prepared["can_execute"] = can_execute
            prepared["reason"] = reason

        prepared.setdefault("extension_id", self._get_manifest_id())
        prepared.setdefault("extension_name", self._get_manifest_name())
        prepared.setdefault("intent_type", "weather")
        prepared.setdefault("mode", self.MODE)
        prepared.setdefault("query_strategy", self.DEFAULTS["query_strategy"])
        prepared.setdefault("require_citations", self.DEFAULTS["require_citations"])
        prepared.setdefault(
            "location",
            {
                "name": None,
                "latitude": None,
                "longitude": None,
            },
        )
        prepared.setdefault(
            "weather_profile",
            {
                "units": self.DEFAULTS["units"],
                "include_current": self.DEFAULTS["include_current"],
                "include_hourly": self.DEFAULTS["include_hourly"],
                "include_daily": self.DEFAULTS["include_daily"],
                "include_alerts": self.DEFAULTS["include_alerts"],
                "max_forecast_days": self.DEFAULTS["max_forecast_days"],
            },
        )
        prepared.setdefault(
            "time_policy",
            {
                "requested_date": None,
                "requested_time": None,
                "time_range": None,
            },
        )

        return prepared

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard entry point for host/runtime compatibility.

        Expected params:
        - query: str
        - context: Dict[str, Any]
        """
        safe_params = params or {}
        query = safe_params.get("query", "") or ""
        context = safe_params.get("context", {}) or {}

        prepared = await self.prepare(query, context)
        return await self.execute(prepared, query)

    def _extract_hook_payload(self, context: HookContext) -> Dict[str, Any]:
        """
        Best-effort extraction from HookContext without over-assuming internals.
        """
        data = getattr(context, "data", None)
        if isinstance(data, dict):
            return data
        return {}

    def _can_execute(self, query: str, context: Dict[str, Any]) -> tuple[bool, str]:
        if not query:
            return False, "Missing query"

        if len(query) < 2:
            return False, "Query too short"

        return True, "Ready"

    def _normalize_query(self, query: Any) -> str:
        if not isinstance(query, str):
            return ""
        return " ".join(query.strip().split())

    def _normalize_string(self, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    def _normalize_units(self, *values: Any) -> str:
        valid = {"auto", "metric", "imperial"}
        for value in values:
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in valid:
                    return normalized
        return "auto"

    def _coerce_positive_int(self, *values: Any) -> int:
        for value in values:
            if isinstance(value, bool):
                continue
            try:
                parsed = int(value)
                if parsed > 0:
                    return parsed
            except (TypeError, ValueError):
                continue
        return 1

    def _coerce_bool(self, *values: Any) -> bool:
        for value in values:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "on"}:
                    return True
                if normalized in {"false", "0", "no", "off"}:
                    return False
        return False

    def _coerce_float_or_none(self, value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _extract_context_hints(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": context.get("user_id"),
            "conversation_id": context.get("conversation_id"),
            "tenant_id": context.get("tenant_id"),
            "requested_mode": context.get("mode"),
        }

    def _get_manifest_id(self) -> str:
        return (
            getattr(self.manifest, "id", None)
            or getattr(self.manifest, "plugin_id", None)
            or getattr(self.manifest, "name", None)
            or self.__class__.__name__
        )

    def _get_manifest_name(self) -> str:
        return (
            getattr(self.manifest, "name", None)
            or getattr(self.manifest, "id", None)
            or self.__class__.__name__
        )

    def _read_manifest_setting(self, field_name: str) -> Any:
        settings = getattr(self.manifest, "settings", None)
        if isinstance(settings, dict):
            return settings.get(field_name)
        return None


class MainExtension(WeatherQueryHandler):
    """Entry point for ExtensionLoader."""
    pass