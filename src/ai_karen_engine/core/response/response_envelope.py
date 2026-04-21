from __future__ import annotations

"""Utilities for building structured response envelopes."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ResponseEnvelope:
    """
    Builder for standardized response envelopes.

    The envelope is intentionally compact and predictable so it can be used by
    runtime code, APIs, UI layers, and formatting pipelines without extra text
    or wrapper noise.
    """

    include_timestamp: bool = True

    def build_response_envelope(
        self,
        final_text: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
        status: str = "ok",
    ) -> Dict[str, Any]:
        """
        Create a standardized response envelope with no extraneous text.

        Args:
            final_text: Final user-facing response text
            provider: Provider name used to generate the response
            model: Model identifier used to generate the response
            metadata: Optional response metadata
            suggestions: Optional suggested follow-up actions or prompts
            alerts: Optional alert objects for warnings/errors/system notices
            status: Envelope status marker

        Returns:
            A normalized response envelope dictionary
        """
        normalized_final = self._normalize_text(final_text)
        normalized_provider = self._normalize_required_string(provider, "provider")
        normalized_model = self._normalize_required_string(model, "model")
        normalized_status = self._normalize_required_string(status, "status")

        meta = dict(metadata or {})
        meta.setdefault("provider", normalized_provider)
        meta.setdefault("model", normalized_model)

        if self.include_timestamp:
            meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        return {
            "final": normalized_final,
            "status": normalized_status,
            "meta": meta,
            "suggestions": self._normalize_suggestions(suggestions),
            "alerts": self._normalize_alerts(alerts),
        }

    def build_error_envelope(
        self,
        final_text: str,
        provider: str,
        model: str,
        error_code: str,
        metadata: Optional[Dict[str, Any]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized error response envelope.
        """
        meta = dict(metadata or {})
        meta["error_code"] = self._normalize_required_string(error_code, "error_code")

        normalized_alerts = self._normalize_alerts(alerts)
        if not normalized_alerts:
            normalized_alerts = [
                {
                    "level": "error",
                    "code": meta["error_code"],
                    "message": self._normalize_text(final_text),
                }
            ]

        return self.build_response_envelope(
            final_text=final_text,
            provider=provider,
            model=model,
            metadata=meta,
            suggestions=[],
            alerts=normalized_alerts,
            status="error",
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        """
        Normalize user-facing text while preserving intentional formatting.
        """
        if value is None:
            return ""

        if not isinstance(value, str):
            value = str(value)

        return value.strip()

    @staticmethod
    def _normalize_required_string(value: str, field_name: str) -> str:
        """
        Normalize and validate required string fields.
        """
        if value is None:
            raise ValueError(f"{field_name} is required")

        if not isinstance(value, str):
            value = str(value)

        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} cannot be empty")

        return normalized

    @staticmethod
    def _normalize_suggestions(
        suggestions: Optional[List[str]],
    ) -> List[str]:
        """
        Normalize suggestions into a clean string list.
        """
        if not suggestions:
            return []

        normalized: List[str] = []
        for item in suggestions:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.append(text)

        return normalized

    @staticmethod
    def _normalize_alerts(
        alerts: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Normalize alerts into a list of dictionaries.
        """
        if not alerts:
            return []

        normalized: List[Dict[str, Any]] = []
        for alert in alerts:
            if isinstance(alert, dict):
                normalized.append(dict(alert))

        return normalized