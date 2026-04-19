import logging
from typing import Any, Dict, Optional

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionContext,
    HookContext,
    HookPoint,
)

logger = logging.getLogger(__name__)


class WebSearchDeepResearchHandler(ExtensionBase):
    """
    Deep research search intent handler.

    Responsibilities:
    - Prepare a normalized retrieval strategy for deep research
    - Implement the required ExtensionBase contract
    - Return structured intent payloads for orchestrator/runtime use
    - Do NOT perform crawling, ranking, or answer generation
    """

    MODE = "deep_research"

    DEFAULTS: Dict[str, Any] = {
        "max_urls": 12,
        "depth": 2,
        "freshness_bias": 0.7,
        "require_citations": True,
        "query_strategy": "decompose_and_expand",
        "prefer_official_sources": False,
        "prefer_recent": True,
        "allow_forum_results": False,
        "max_subqueries": 5,
        "max_hops": 3,
        "require_source_diversity": True,
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
            "Initializing deep research extension",
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
            "Shutting down deep research extension",
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

        This extension prepares strategy only. It does not execute search.
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
        Prepare a normalized deep research strategy payload.
        """
        safe_context = context or {}
        normalized_query = self._normalize_query(query)
        can_execute, reason = self._can_execute(normalized_query)

        max_urls = self._coerce_positive_int(
            safe_context.get("max_urls"),
            self._read_manifest_setting("max_urls"),
            self.DEFAULTS["max_urls"],
        )
        depth = self._coerce_positive_int(
            safe_context.get("depth"),
            self._read_manifest_setting("depth"),
            self.DEFAULTS["depth"],
        )
        freshness_bias = self._coerce_float(
            safe_context.get("freshness_bias"),
            self._read_manifest_setting("freshness_bias"),
            self.DEFAULTS["freshness_bias"],
        )

        prefer_recent = self._coerce_bool(
            safe_context.get("prefer_recent"),
            self._read_manifest_setting("prefer_recent"),
            self.DEFAULTS["prefer_recent"],
        )
        prefer_official_sources = self._coerce_bool(
            safe_context.get("prefer_official_sources"),
            self._read_manifest_setting("prefer_official_sources"),
            self.DEFAULTS["prefer_official_sources"],
        )
        allow_forum_results = self._coerce_bool(
            safe_context.get("allow_forum_results"),
            self._read_manifest_setting("allow_forum_results"),
            self.DEFAULTS["allow_forum_results"],
        )
        require_source_diversity = self._coerce_bool(
            safe_context.get("require_source_diversity"),
            self._read_manifest_setting("require_source_diversity"),
            self.DEFAULTS["require_source_diversity"],
        )

        max_subqueries = self._coerce_positive_int(
            safe_context.get("max_subqueries"),
            self._read_manifest_setting("max_subqueries"),
            self.DEFAULTS["max_subqueries"],
        )
        max_hops = self._coerce_positive_int(
            safe_context.get("max_hops"),
            self._read_manifest_setting("max_hops"),
            self.DEFAULTS["max_hops"],
        )

        response = {
            "extension_id": self._get_manifest_id(),
            "extension_name": self._get_manifest_name(),
            "intent_type": "web_search",
            "mode": self.MODE,
            "query": normalized_query,
            "can_execute": can_execute,
            "reason": reason,
            "max_urls": max_urls,
            "depth": depth,
            "freshness_bias": freshness_bias,
            "require_citations": True,
            "query_strategy": "decompose_and_expand",
            "search_profile": {
                "prefer_recent": prefer_recent,
                "prefer_official_sources": prefer_official_sources,
                "prefer_news_publishers": False,
                "allow_forum_results": allow_forum_results,
                "require_source_diversity": require_source_diversity,
            },
            "research_plan": {
                "max_subqueries": max_subqueries,
                "max_hops": max_hops,
                "decompose_query": True,
                "cross_source_synthesis": True,
                "require_source_diversity": require_source_diversity,
            },
            "domain_policy": {
                "allowed_domains": self._normalize_list(safe_context.get("allowed_domains")),
                "blocked_domains": self._normalize_list(safe_context.get("blocked_domains")),
            },
            "time_policy": {
                "time_range": self._normalize_string(safe_context.get("time_range")),
                "published_after": safe_context.get("published_after"),
                "published_before": safe_context.get("published_before"),
            },
            "research_hints": {
                "target_entities": self._normalize_list(safe_context.get("target_entities")),
                "comparison_mode": self._coerce_bool(
                    safe_context.get("comparison_mode"),
                    self._read_manifest_setting("comparison_mode"),
                    False,
                ),
                "requested_sections": self._normalize_list(safe_context.get("requested_sections")),
            },
            "context_hints": self._extract_context_hints(safe_context),
            "telemetry": {
                "handler": self.__class__.__name__,
                "manifest_id": self._get_manifest_id(),
                "mode": self.MODE,
            },
        }

        self.logger.debug(
            "Prepared deep research intent strategy",
            extra={
                "extension_id": response["extension_id"],
                "mode": response["mode"],
                "can_execute": response["can_execute"],
                "max_urls": response["max_urls"],
                "max_hops": response["research_plan"]["max_hops"],
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
            can_execute, reason = self._can_execute(normalized_query)
            prepared["can_execute"] = can_execute
            prepared["reason"] = reason

        prepared.setdefault("extension_id", self._get_manifest_id())
        prepared.setdefault("extension_name", self._get_manifest_name())
        prepared.setdefault("intent_type", "web_search")
        prepared.setdefault("mode", self.MODE)
        prepared.setdefault("max_urls", self.DEFAULTS["max_urls"])
        prepared.setdefault("depth", self.DEFAULTS["depth"])
        prepared.setdefault("freshness_bias", self.DEFAULTS["freshness_bias"])
        prepared.setdefault("require_citations", True)
        prepared.setdefault("query_strategy", "decompose_and_expand")
        prepared.setdefault(
            "search_profile",
            {
                "prefer_recent": self.DEFAULTS["prefer_recent"],
                "prefer_official_sources": self.DEFAULTS["prefer_official_sources"],
                "prefer_news_publishers": False,
                "allow_forum_results": self.DEFAULTS["allow_forum_results"],
                "require_source_diversity": self.DEFAULTS["require_source_diversity"],
            },
        )
        prepared.setdefault(
            "research_plan",
            {
                "max_subqueries": self.DEFAULTS["max_subqueries"],
                "max_hops": self.DEFAULTS["max_hops"],
                "decompose_query": True,
                "cross_source_synthesis": True,
                "require_source_diversity": self.DEFAULTS["require_source_diversity"],
            },
        )
        prepared.setdefault(
            "domain_policy",
            {
                "allowed_domains": [],
                "blocked_domains": [],
            },
        )
        prepared.setdefault(
            "time_policy",
            {
                "time_range": None,
                "published_after": None,
                "published_before": None,
            },
        )
        prepared.setdefault(
            "research_hints",
            {
                "target_entities": [],
                "comparison_mode": False,
                "requested_sections": [],
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

    def _can_execute(self, query: str) -> tuple[bool, str]:
        if not query:
            return False, "Missing query"

        if len(query) < 2:
            return False, "Query too short"

        return True, "Ready"

    def _normalize_query(self, query: Any) -> str:
        if not isinstance(query, str):
            return ""
        return " ".join(query.strip().split())

    def _normalize_list(self, value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            normalized = value.strip()
            return [normalized] if normalized else []

        if isinstance(value, (list, tuple, set)):
            output: list[str] = []
            for item in value:
                if isinstance(item, str):
                    normalized = item.strip()
                    if normalized:
                        output.append(normalized)
            return output

        return []

    def _normalize_string(self, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

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

    def _coerce_float(self, *values: Any) -> float:
        for value in values:
            try:
                parsed = float(value)
                if parsed >= 0:
                    return parsed
            except (TypeError, ValueError):
                continue
        return 0.0

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


class MainExtension(WebSearchDeepResearchHandler):
    """Entry point for ExtensionLoader."""
    pass