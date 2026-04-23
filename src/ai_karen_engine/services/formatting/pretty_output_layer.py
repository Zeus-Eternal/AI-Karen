"""
Pretty Output Layer for Karen's AI system.

Canonical runtime response formatter.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from ai_karen_engine.services.response_formatting.response_formatting_models import (
    AccessibilityLevel,
    ContentType,
    DeviceType,
    DisplayContext,
    FormattingConfig,
    LayoutHint,
    LayoutType,
    OutputProfile,
    ResponseContext,
    SyntaxHighlightConfig,
)

logger = logging.getLogger(__name__)


class ResponsiveEngine:
    """Internal engine for device-specific response adaptation."""

    def __init__(self) -> None:
        self._init_layout_adaptations()

    def _init_layout_adaptations(self) -> None:
        self.layout_adaptations = {
            LayoutType.TABLE: self._adapt_table,
            LayoutType.BULLET_LIST: self._adapt_list,
            LayoutType.CODE_BLOCK: self._adapt_code,
        }

    async def adapt(
        self, content: str, context: ResponseContext, layout_type: LayoutType
    ) -> Dict[str, Any]:
        device_type = self._detect_device_type(context)
        adapted_content = content
        adaptation_func = self.layout_adaptations.get(layout_type)
        if adaptation_func and device_type in [DeviceType.PHONE, DeviceType.TABLET]:
            adapted_content = adaptation_func(content, device_type)

        return {
            "content": adapted_content,
            "css_classes": [f"device-{device_type.value}"],
            "accessibility_adaptations": (
                [f"optimized-for-{device_type.value}"]
                if device_type != DeviceType.DESKTOP
                else []
            ),
        }

    def _detect_device_type(self, context: ResponseContext) -> DeviceType:
        if context.display_context == DisplayContext.MOBILE:
            return DeviceType.PHONE
        if context.display_context == DisplayContext.TABLET:
            return DeviceType.TABLET
        if context.display_context == DisplayContext.TERMINAL:
            return DeviceType.DESKTOP
        return DeviceType.DESKTOP

    def _adapt_table(self, content: str, device: DeviceType) -> str:
        if device != DeviceType.PHONE:
            return content

        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if "|" in line and "--" not in line:
                cols = [c.strip() for c in line.split("|") if c.strip()]
                if cols:
                    new_lines.append("• " + " | ".join(cols))
            elif line.strip():
                new_lines.append(line)
        return "\n".join(new_lines)

    def _adapt_list(self, content: str, device: DeviceType) -> str:
        return content

    def _adapt_code(self, content: str, device: DeviceType) -> str:
        return content


class PrettyOutputLayer:
    """
    Unified Pretty Output Layer for formatting AI responses.
    Consolidates legacy logic into a modular transformation engine.
    """

    def __init__(self, config: Optional[FormattingConfig] = None):
        self.config = config or FormattingConfig()
        self._interactive_elements_enabled = True

        self.responsive_engine = ResponsiveEngine()
        self.content_detector = None
        self.syntax_highlighter = None

        self._performance_metrics = {
            "format_calls": 0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        self._format_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 500
        self._init_registries()

        logger.info(
            "PrettyOutputLayer initialized with profile: %s",
            self.config.output_profile.value,
        )

    def _init_registries(self) -> None:
        self._layout_detectors = {
            LayoutType.MENU: self._detect_menu,
            LayoutType.BULLET_LIST: self._detect_bullets,
            LayoutType.SYSTEM_STATUS: self._detect_sys_status,
        }
        self._layout_formatters = {
            LayoutType.DEFAULT: lambda c, p, ctx: c,
            LayoutType.MENU: lambda c, p, ctx: c,
            LayoutType.SYSTEM_STATUS: lambda c, p, ctx: c,
            LayoutType.CODE_BLOCK: self._format_code_block,
            LayoutType.TABLE: lambda c, p, ctx: c,
            LayoutType.STEPS: lambda c, p, ctx: c,
        }
        self._profile_formatters = {
            OutputProfile.PLAIN: self._apply_plain,
            OutputProfile.PRETTY: lambda c, ctx: c,
            OutputProfile.DEV_DOC: lambda c, ctx: f"### Technical Response\n{c}",
            OutputProfile.MINIMAL: lambda c, ctx: c.replace("\n\n", "\n").strip(),
            OutputProfile.VERBOSE: lambda c, ctx: (
                f"Detailed Response:\n{c}\n[Words: {len(c.split())}]"
            ),
            OutputProfile.ACCESSIBLE: lambda c, ctx: (
                f'<section aria-label="AI response">{c}</section>'
            ),
            OutputProfile.TECHNICAL: lambda c, ctx: f"```technical\n{c}\n```",
            OutputProfile.CONVERSATIONAL: lambda c, ctx: f"Here's what I found: {c}",
        }

    async def _ensure_external_subsystems(self) -> None:
        if not self.content_detector:
            try:
                from .content_type_detector import get_content_detector

                self.content_detector = get_content_detector()
            except ImportError:
                pass

        if not self.syntax_highlighter:
            try:
                from .syntax_highlighter import get_syntax_highlighter

                self.syntax_highlighter = get_syntax_highlighter()
            except ImportError:
                pass

    async def render(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Compatibility rendering entrypoint used by runtime callers."""
        context = ResponseContext(
            user_query=str((metadata or {}).get("intent", "") or ""),
            response_content=content,
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.BASIC,
            user_preferences={},
            session_data=dict(metadata or {}),
        )
        result = await self.format_response(content, context)
        return str(result.get("content", content))

    async def format_response(
        self, response_content: str, context: ResponseContext
    ) -> Dict[str, Any]:
        start_time = time.time()
        self._performance_metrics["format_calls"] += 1

        try:
            await self._ensure_external_subsystems()

            cache_key = self._generate_cache_key(response_content, context)
            if self.config.cache_enabled and cache_key in self._format_cache:
                self._performance_metrics["cache_hits"] += 1
                return self._format_cache[cache_key]

            self._performance_metrics["cache_misses"] += 1

            if self.config.safe_mode:
                response_content = self._sanitize(response_content)

            if len(response_content) > self.config.max_content_length:
                response_content = (
                    response_content[: self.config.max_content_length]
                    + "... [truncated]"
                )

            detected_type = ContentType.TEXT
            confidence = 0.5
            layout_hint = LayoutHint(layout_type=self.config.default_layout)

            if self.content_detector:
                detection = await self.content_detector.detect_content_type(
                    response_content, user_query=context.user_query
                )
                detected_type = ContentType(detection.content_type)
                confidence = detection.confidence
                if hasattr(detection, "layout_hint") and detection.layout_hint:
                    layout_hint = LayoutHint(
                        layout_type=LayoutType(detection.layout_hint.layout_type),
                        confidence=detection.layout_hint.confidence,
                        parameters=getattr(detection.layout_hint, "parameters", {}),
                    )

            if layout_hint.layout_type == LayoutType.DEFAULT:
                layout_hint = self._run_internal_detectors(response_content, context)

            formatted_content = self._layout_formatters.get(
                layout_hint.layout_type, self._layout_formatters[LayoutType.DEFAULT]
            )(response_content, layout_hint.parameters, context)

            if self.config.enable_syntax_highlighting and self.syntax_highlighter:
                if detected_type in [
                    ContentType.CODE,
                    ContentType.PYTHON,
                    ContentType.JAVASCRIPT,
                    ContentType.JSON,
                ]:
                    try:
                        res = await self.syntax_highlighter.highlight_code(
                            formatted_content,
                            SyntaxHighlightConfig(language=detected_type.value),
                        )
                        formatted_content = getattr(
                            res, "highlighted_content", formatted_content
                        )
                    except Exception:
                        pass

            css_classes = []
            accessibility_features = []
            if self.config.enable_responsive_formatting:
                resp = await self.responsive_engine.adapt(
                    formatted_content, context, layout_hint.layout_type
                )
                formatted_content = resp["content"]
                css_classes = resp["css_classes"]
                accessibility_features = resp["accessibility_adaptations"]

            profile_func = self._profile_formatters.get(
                self.config.output_profile, self._profile_formatters[OutputProfile.PRETTY]
            )
            formatted_content = profile_func(formatted_content, context)

            proc_time = time.time() - start_time
            result = {
                "content": formatted_content,
                "layout_type": layout_hint.layout_type.value,
                "output_profile": self.config.output_profile.value,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time": proc_time,
                    "content_length": len(formatted_content),
                    "confidence_score": confidence,
                    "content_type": detected_type.value,
                    "css_classes": css_classes,
                    "accessibility_features": accessibility_features,
                },
            }

            if self.config.cache_enabled:
                self._format_cache[cache_key] = result
                if len(self._format_cache) > self._cache_max_size:
                    self._format_cache.pop(next(iter(self._format_cache)))

            return result

        except Exception as e:
            self._performance_metrics["errors"] += 1
            logger.error("Formatting failed: %s\n%s", e, traceback.format_exc())
            return {
                "content": response_content,
                "metadata": {
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                },
            }

    def _sanitize(self, content: str) -> str:
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r"on\w+\s*=", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r"^\s*Your task:\s*Respond to the user's question based on the recent conversation history\.\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(r"^\s*response:\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r"^\s*(Your task:.*?\n)+(response:\s*)?",
            "",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        content = re.sub(
            r"\n?\s*Your task:\s*Respond to the user's question based on the recent conversation history\.\s*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r"\n?\s*Now complete the following instruction:\s*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r"\n?\s*Current conversation:\s*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(r"\n?\s*Solution>\s*$", "", content, flags=re.IGNORECASE | re.MULTILINE)
        content = re.sub(r"\n?\s*\*\*\s*$", "", content, flags=re.MULTILINE)
        content = re.sub(
            r"\n?\s*[A-Z][^.:\n]*\band\b[^.:\n]*\bprovide a detailed solution\.\s*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r"^\s*Since the user has greeted again without a specific new request,.*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r"^\s*I(?:'|\u2019)ll acknowledge their greeting and be ready to assist.*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(
            r"^\s*This is NOT a complete meaningful response.*$",
            "",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        content = re.sub(r"^\s*=+\s*$", "", content, flags=re.MULTILINE)
        return content.strip()

    def _run_internal_detectors(self, content: str, context: ResponseContext) -> LayoutHint:
        best_hint = LayoutHint(LayoutType.DEFAULT, 0.0)
        for _, detector in self._layout_detectors.items():
            hint = detector(content)
            if hint.confidence > best_hint.confidence:
                best_hint = hint
        return best_hint if best_hint.confidence > 0.4 else LayoutHint(LayoutType.DEFAULT)

    def _detect_menu(self, content: str) -> LayoutHint:
        count = len(re.findall(r"^\s*\d+\.\s+", content, re.MULTILINE))
        lines = len([l for l in content.split("\n") if l.strip()])
        return LayoutHint(LayoutType.MENU, count / max(lines, 1))

    def _detect_bullets(self, content: str) -> LayoutHint:
        count = len(re.findall(r"^\s*[-*+]\s+", content, re.MULTILINE))
        lines = len(content.split("\n"))
        return LayoutHint(LayoutType.BULLET_LIST, count / max(lines, 1))

    def _detect_sys_status(self, content: str) -> LayoutHint:
        keywords = ["status", "online", "active", "cpu", "memory"]
        score = sum(1 for k in keywords if k in content.lower())
        return LayoutHint(LayoutType.SYSTEM_STATUS, score / len(keywords))

    def _format_code_block(self, content: str, params: dict, context: ResponseContext) -> str:
        if "```" in content:
            return content
        lang = params.get("language", "text")
        return f"```{lang}\n{content.strip()}\n```"

    def _apply_plain(self, content: str, context: ResponseContext) -> str:
        content = re.sub(r"#{1,6}\s*", "", content)
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
        return content.strip()

    def _generate_cache_key(self, content: str, context: ResponseContext) -> str:
        key_data = f"{content}:{self.config.output_profile.value}:{context.display_context.value}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._performance_metrics


__all__ = ["PrettyOutputLayer", "ResponsiveEngine"]
