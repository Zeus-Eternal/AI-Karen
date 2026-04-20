import logging
from typing import Any, Dict

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionContext,
    HookContext,
    HookPoint,
)

from .handlers.general_handler import GeneralHandler
from .handlers.news_handler import NewsHandler
from .handlers.docs_handler import DocsHandler
from .handlers.deep_research_handler import DeepResearchHandler
from .handlers.structured_extract_handler import StructuredExtractHandler
from .handlers.weather_handler import WeatherHandler
from .handlers.stock_market_handler import StockMarketHandler

logger = logging.getLogger(__name__)

MODE_HANDLER_MAP = {
    "general": GeneralHandler,
    "news": NewsHandler,
    "docs": DocsHandler,
    "deep_research": DeepResearchHandler,
    "structured_extract": StructuredExtractHandler,
    "weather": WeatherHandler,
    "stock_market": StockMarketHandler,
}


class WebSearchDispatcher(ExtensionBase):
    """
    Main dispatcher for web search plugin.

    Handles mode resolution and delegates to appropriate handler.
    """

    def __init__(self, manifest: Any, context: ExtensionContext):
        super().__init__(manifest, context)
        self._handlers: Dict[str, Any] = {}
        self._default_mode = "general"

    async def initialize(self) -> None:
        self.logger.debug(
            "Initializing web search dispatcher",
            extra={
                "extension_name": getattr(
                    self.manifest, "name", self.__class__.__name__
                ),
                "available_modes": list(MODE_HANDLER_MAP.keys()),
                "default_mode": self._default_mode,
            },
        )

        self._default_mode = self._read_manifest_setting("default_mode") or "general"

    async def shutdown(self) -> None:
        self.logger.debug(
            "Shutting down web search dispatcher",
            extra={
                "extension_name": getattr(
                    self.manifest, "name", self.__class__.__name__
                ),
                "handler_count": len(self._handlers),
            },
        )
        self._handlers.clear()

    async def execute_hook(
        self,
        hook_point: HookPoint,
        context: HookContext,
    ) -> Dict[str, Any]:
        if not self.supports_hook_point(hook_point):
            return {
                "success": False,
                "can_execute": False,
                "error": f"Unsupported hook point: {hook_point.value}",
                "hook_point": hook_point.value,
                "plugin_id": self._get_manifest_id(),
            }

        payload = self._extract_hook_payload(context)
        params = self._extract_params(payload)

        mode = self._resolve_mode(params)
        handler = self._get_handler(mode)

        if not handler:
            return {
                "success": False,
                "can_execute": False,
                "error": f"Unknown mode: {mode}",
                "hook_point": hook_point.value,
                "plugin_id": self._get_manifest_id(),
                "mode": mode,
            }

        query = params.get("query", "") or ""
        request_context = params.get("context", {}) or {}

        prepared = await handler.prepare(query, request_context)
        executed = await handler.execute(prepared, query)

        return {
            "success": executed.get("can_execute", False),
            "hook_point": hook_point.value,
            "result": executed,
            "mode": mode,
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        safe_params = params or {}
        query = safe_params.get("query", "") or ""
        context = safe_params.get("context", {}) or {}

        mode = self._resolve_mode(safe_params)
        handler = self._get_handler(mode)

        if not handler:
            return {
                "success": False,
                "can_execute": False,
                "error": f"Unknown mode: {mode}",
                "plugin_id": self._get_manifest_id(),
                "mode": mode,
                "query": query,
            }

        prepared = await handler.prepare(query, context)
        result = await handler.execute(prepared, query)

        result.setdefault("mode", mode)

        return result

    def _resolve_mode(self, params: Dict[str, Any]) -> str:
        mode = params.get("mode")

        if mode:
            normalized = mode.lower().replace("-", "_")
            if normalized in MODE_HANDLER_MAP:
                return normalized

        if "context" in params and isinstance(params["context"], dict):
            context_mode = params["context"].get("mode")
            if context_mode:
                normalized = context_mode.lower().replace("-", "_")
                if normalized in MODE_HANDLER_MAP:
                    return normalized

        manifest_default = self._read_manifest_setting("default_mode")
        if manifest_default:
            normalized = manifest_default.lower().replace("-", "_")
            if normalized in MODE_HANDLER_MAP:
                return normalized

        return self._default_mode

    def _get_handler(self, mode: str):
        if mode not in MODE_HANDLER_MAP:
            return None

        if mode not in self._handlers:
            handler_class = MODE_HANDLER_MAP[mode]
            self._handlers[mode] = handler_class(self.manifest, self.context)

        return self._handlers[mode]

    def _extract_hook_payload(self, context: HookContext) -> Dict[str, Any]:
        data = getattr(context, "data", None)
        if isinstance(data, dict):
            return data
        return {}

    def _extract_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload or {}

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


class MainExtension(WebSearchDispatcher):
    """Entry point for ExtensionLoader."""

    pass
