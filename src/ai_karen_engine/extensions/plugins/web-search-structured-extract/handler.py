import logging
from typing import Any, Dict, Optional

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionContext,
)

logger = logging.getLogger(__name__)


class WebSearchStructuredExtractHandler(ExtensionBase):
    """
    Structured extraction intent handler.

    Responsibility:
    - Declare a structured-extract retrieval strategy
    - Normalize and validate incoming parameters
    - Return backend-ready extraction directives
    - Do NOT perform crawling, extraction, ranking, or answer generation
    """

    MODE = "structured_extract"

    DEFAULTS: Dict[str, Any] = {
        "max_urls": 5,
        "depth": 1,
        "require_citations": True,
        "query_strategy": "targeted_extract",
        "extraction_preference": "schema_first",
        "allow_llm_fallback": True,
        "freshness_bias": 0.5,
    }

    def __init__(self, manifest: Any, context: ExtensionContext):
        super().__init__(manifest, context)

    async def prepare(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a normalized structured extraction strategy payload.

        Expected context keys may include:
        - schema
        - extraction_schema
        - extraction_type
        - extraction_instruction
        - target_fields
        - target_selectors
        - allowed_domains
        - blocked_domains
        - max_urls
        - depth
        - user_id
        - conversation_id
        - tenant_id
        """
        safe_context = context or {}
        normalized_query = self._normalize_query(query)
        can_execute, reason = self._can_execute(normalized_query)

        extraction_schema = (
            safe_context.get("schema")
            or safe_context.get("extraction_schema")
            or self._read_manifest_setting("schema")
        )
        extraction_type = self._resolve_extraction_type(safe_context, extraction_schema)
        extraction_instruction = self._resolve_extraction_instruction(safe_context)
        target_fields = self._normalize_list(safe_context.get("target_fields"))
        target_selectors = self._normalize_dict(safe_context.get("target_selectors"))

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

        allow_llm_fallback = self._coerce_bool(
            safe_context.get("allow_llm_fallback"),
            self._read_manifest_setting("allow_llm_fallback"),
            self.DEFAULTS["allow_llm_fallback"],
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
            "require_citations": self.DEFAULTS["require_citations"],
            "query_strategy": self.DEFAULTS["query_strategy"],
            "freshness_bias": self.DEFAULTS["freshness_bias"],
            "extraction": {
                "type": extraction_type,
                "schema": extraction_schema,
                "instruction": extraction_instruction,
                "target_fields": target_fields,
                "target_selectors": target_selectors,
                "preference": self.DEFAULTS["extraction_preference"],
                "allow_llm_fallback": allow_llm_fallback,
            },
            "domain_policy": {
                "allowed_domains": self._normalize_list(safe_context.get("allowed_domains")),
                "blocked_domains": self._normalize_list(safe_context.get("blocked_domains")),
            },
            "context_hints": self._extract_context_hints(safe_context),
            "telemetry": {
                "handler": self.__class__.__name__,
                "manifest_id": self._get_manifest_id(),
                "mode": self.MODE,
                "extraction_type": extraction_type,
            },
        }

        logger.debug(
            "Prepared structured extraction intent strategy",
            extra={
                "extension_id": response["extension_id"],
                "mode": response["mode"],
                "can_execute": response["can_execute"],
                "extraction_type": extraction_type,
            },
        )

        return response

    async def execute(self, config: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Runtime compatibility hook.

        This extension is intent-oriented, so execute simply returns a normalized,
        execution-ready strategy payload rather than performing side effects.
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
        prepared.setdefault("require_citations", self.DEFAULTS["require_citations"])
        prepared.setdefault("query_strategy", self.DEFAULTS["query_strategy"])

        extraction = dict(prepared.get("extraction") or {})
        extraction.setdefault("type", "schema" if extraction.get("schema") else "instruction")
        extraction.setdefault("preference", self.DEFAULTS["extraction_preference"])
        extraction.setdefault("allow_llm_fallback", self.DEFAULTS["allow_llm_fallback"])
        extraction.setdefault("schema", None)
        extraction.setdefault("instruction", None)
        extraction.setdefault("target_fields", [])
        extraction.setdefault("target_selectors", {})
        prepared["extraction"] = extraction

        prepared.setdefault(
            "domain_policy",
            {
                "allowed_domains": [],
                "blocked_domains": [],
            },
        )

        return prepared

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard extension-host entry point.

        Expected params:
        - query: str
        - context: Dict[str, Any]
        """
        safe_params = params or {}
        query = safe_params.get("query", "") or ""
        context = safe_params.get("context", {}) or {}

        prepared = await self.prepare(query, context)
        return await self.execute(prepared, query)

    def _resolve_extraction_type(
        self,
        context: Dict[str, Any],
        extraction_schema: Any,
    ) -> str:
        explicit = context.get("extraction_type") or self._read_manifest_setting("extraction_type")
        if isinstance(explicit, str):
            normalized = explicit.strip().lower().replace("-", "_")
            if normalized in {"schema", "css", "xpath", "instruction", "llm"}:
                return normalized

        if extraction_schema:
            return "schema"

        if context.get("target_selectors"):
            return "css"

        return "instruction"

    def _resolve_extraction_instruction(self, context: Dict[str, Any]) -> Optional[str]:
        instruction = (
            context.get("extraction_instruction")
            or context.get("instruction")
            or self._read_manifest_setting("extraction_instruction")
            or self._read_manifest_setting("instruction")
        )

        if not isinstance(instruction, str):
            return None

        normalized = " ".join(instruction.strip().split())
        return normalized or None

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

    def _normalize_dict(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

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

    def _extract_context_hints(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": context.get("user_id"),
            "conversation_id": context.get("conversation_id"),
            "tenant_id": context.get("tenant_id"),
            "requested_mode": context.get("mode"),
            "requested_extraction_type": context.get("extraction_type"),
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


class MainExtension(WebSearchStructuredExtractHandler):
    """Entry point for ExtensionLoader."""
    pass