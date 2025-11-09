"""
DRY Formatter with CopilotKit hooks for consistent response formatting (Kari v3).

Goals:
- Deterministic, consistent output (headings, bullets, code, sections)
- Prompt-first + local-first: pure formatting, zero external hard deps
- CopilotKit hooks are purely additive, fully optional, and gracefully degrade
- Security-minded sanitization and size guards
- Observability (Prometheus optional) + structured metadata
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# Optional Prometheus (no hard dependency)
try:
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover
    class _Noop:
        def labels(self, *_, **__): return self
        def observe(self, *_): pass
        def inc(self, *_): pass
    Counter = Histogram = _Noop  # type: ignore

from .protocols import ResponseFormatter
from .config import PipelineConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)

# -------------------------
# Metrics (optional hooks)
# -------------------------
_FMT_LATENCY = Histogram("karen_formatter_latency_seconds", "Latency of DRY formatter", ["component"]).labels(component="dry")
_FMT_ERRORS = Counter("karen_formatter_errors_total", "Total formatting errors", ["component"]).labels(component="dry")
_FMT_REQUESTS = Counter("karen_formatter_requests_total", "Total formatting requests", ["component"]).labels(component="dry")

# -------------------------
# Data Models
# -------------------------

@dataclass
class FormattingOptions:
    """Options for response formatting."""
    enable_copilotkit: bool = True
    enable_code_highlighting: bool = True
    enable_structured_sections: bool = True
    enable_onboarding_format: bool = True
    enable_auto_headings: bool = True
    enable_table_normalization: bool = True
    enable_json_yaml_blocks: bool = True
    max_code_block_lines: int = 200
    max_total_output_chars: int = 120_000
    bullet_style: str = "•"     # Unicode bullet
    heading_style: str = "##"   # Markdown heading level
    # CopilotKit specific options
    copilotkit_complexity_graphs: bool = True
    copilotkit_inline_suggestions: bool = True
    copilotkit_ui_hints: bool = True
    # Security / Safety
    strip_html_tags: bool = False          # used for untrusted html payloads
    collapse_triple_newlines: bool = True  # reduce vertical noise


@dataclass
class FormattedResponse:
    """Structured response with formatting metadata."""
    content: str
    sections: Dict[str, str] = field(default_factory=dict)
    code_blocks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    copilotkit_enhancements: Optional[Dict[str, Any]] = None


# -------------------------
# Formatter Implementation
# -------------------------

class DRYFormatter(ResponseFormatter):
    """
    DRY (Don't Repeat Yourself) Formatter with CopilotKit hooks.

    Design:
    - Never blocks on CopilotKit. If unavailable or disabled, behave identically.
    - Pure formatting (prompt-first). No I/O. Deterministic transforms.
    - Sanitization options for risky payloads (strip_html_tags).
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.options = FormattingOptions(enable_copilotkit=self.config.enable_copilotkit)
        self._copilotkit_available = self._check_copilotkit_availability()

    def format_response(
        self,
        raw_response: str,
        intent: str,
        persona: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        _FMT_REQUESTS.inc(1)

        try:
            with _LatencyTimer(_FMT_LATENCY):
                options = self._merge_options(kwargs)
                safe_text = self._sanitize_input(raw_response, options)

                # Parse structure (sections + fenced blocks)
                structured = self._parse_response_structure(safe_text, options)

                # Apply formatting pipeline
                formatted = self._apply_consistent_formatting(structured, intent, persona, options)

                # CopilotKit (optional & additive)
                copilotkit_enhancements = None
                if options.enable_copilotkit and self._copilotkit_available:
                    copilotkit_enhancements = self._add_copilotkit_enhancements(
                        formatted, intent, persona, options
                    )

                # Build final response
                response: Dict[str, Any] = {
                    "content": formatted.content,
                    "sections": formatted.sections,
                    "code_blocks": formatted.code_blocks,
                    "metadata": {
                        "intent": intent,
                        "persona": persona,
                        "formatter_version": "3.0",
                        "copilotkit_enabled": bool(options.enable_copilotkit and self._copilotkit_available),
                        "formatting_applied": True,
                        **formatted.metadata,
                    },
                }
                if copilotkit_enhancements:
                    response["copilotkit"] = copilotkit_enhancements

                # Size guard for downstream renderers
                if len(response["content"]) > options.max_total_output_chars:
                    response["metadata"]["truncated"] = True
                    response["content"] = response["content"][: options.max_total_output_chars] + "\n… [truncated]"

                return response

        except Exception as e:
            _FMT_ERRORS.inc(1)
            logger.warning(f"[DRYFormatter] Formatting failed, returning raw response: {e}")
            # Graceful degradation
            return {
                "content": raw_response,
                "sections": {},
                "code_blocks": [],
                "metadata": {
                    "intent": intent,
                    "persona": persona,
                    "formatter_version": "3.0",
                    "copilotkit_enabled": False,
                    "formatting_applied": False,
                    "error": str(e),
                },
            }

    # -------------------------
    # Options / Sanitization
    # -------------------------

    def _merge_options(self, kwargs: Dict[str, Any]) -> FormattingOptions:
        options = FormattingOptions(enable_copilotkit=self.config.enable_copilotkit)
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)
        return options

    def _sanitize_input(self, text: str, options: FormattingOptions) -> str:
        """Lightweight guards; no heavy HTML parsing to stay local-first."""
        if options.collapse_triple_newlines:
            text = re.sub(r"\n{3,}", "\n\n", text)
        if options.strip_html_tags:
            # Very conservative tag stripping (doesn't touch code blocks)
            fence = r"```.*?```"
            placeholders: List[str] = []
            def _stash(m):
                placeholders.append(m.group(0))
                return f"__FENCE_{len(placeholders)-1}__"
            stashed = re.sub(fence, _stash, text, flags=re.DOTALL)

            stashed = re.sub(r"</?[^>\n]+>", "", stashed)  # naive tag strip
            # Restore fences
            def _restore(m):
                idx = int(m.group(1))
                return placeholders[idx]
            text = re.sub(r"__FENCE_(\d+)__", _restore, stashed)
        return text

    # -------------------------
    # Parsing
    # -------------------------

    def _parse_response_structure(self, raw_response: str, options: FormattingOptions) -> FormattedResponse:
        """
        Extract:
        - fenced code blocks (```lang ... ```)
        - JSON/YAML blocks if present (as code)
        - major sections (Quick Plan, Next Action, Optional Boost, Summary, Details)
        """
        code_blocks: List[Dict[str, Any]] = []

        # Capture triple-fenced blocks (supports ```lang\n ... \n```)
        fence_pattern = r"```([a-zA-Z0-9_+-]*)\n(.*?)\n```"
        def _collect_fences(text: str) -> str:
            idx = 0
            def _sub(m):
                nonlocal idx
                lang = (m.group(1) or "text").strip() or "text"
                code = m.group(2)
                cb = {
                    "id": f"code_block_{idx}",
                    "language": lang,
                    "code": code,
                    "line_count": len(code.splitlines()),
                }
                code_blocks.append(cb)
                token = f"__CODE_BLOCK_{idx}__"
                idx += 1
                return token
            return re.sub(fence_pattern, _sub, text, flags=re.DOTALL)

        content_placeheld = _collect_fences(raw_response)

        # Optionally detect JSON/YAML blocks that aren't fenced and fence them virtually
        if options.enable_json_yaml_blocks:
            content_placeheld = self._detect_and_virtual_fence_structs(content_placeheld, code_blocks)

        # Extract sections (case-insensitive markers)
        sections = self._extract_sections(content_placeheld)

        return FormattedResponse(
            content=raw_response,  # we reapply transforms later with blocks restored
            sections=sections,
            code_blocks=code_blocks,
            metadata={},
        )

    def _detect_and_virtual_fence_structs(self, text: str, code_blocks: List[Dict[str, Any]]) -> str:
        """
        Detect inline JSON/YAML (simple heuristics) and replace with placeholders
        so later formatting can treat them as code blocks.
        """
        replaced = text

        # JSON: starts with { or [ and ends reasonably
        json_candidates = re.finditer(r"(\{[\s\S]*?\}|\[[\s\S]*?\])", replaced)
        for m in list(json_candidates)[:5]:  # guard: max 5 large captures
            snippet = m.group(0).strip()
            if len(snippet) < 30:  # too small to be meaningful
                continue
            # Basic sanity: must be valid JSON or close enough
            try:
                json.loads(snippet)
            except Exception:
                continue
            idx = len(code_blocks)
            code_blocks.append({"id": f"code_block_{idx}", "language": "json", "code": snippet, "line_count": len(snippet.splitlines())})
            replaced = replaced.replace(snippet, f"__CODE_BLOCK_{idx}__", 1)

        # YAML heuristic (very light): key: value lines with dashes
        yaml_candidates = re.finditer(r"(^|\n)([ \t]*-?[ \t]*[A-Za-z0-9_\-]+:[^\n]*\n(?:[ \t]+[^\n]*\n)*)", replaced)
        count = 0
        for m in yaml_candidates:
            if count >= 3:
                break
            snippet = m.group(0).strip()
            if len(snippet.splitlines()) < 3:
                continue
            idx = len(code_blocks)
            code_blocks.append({"id": f"code_block_{idx}", "language": "yaml", "code": snippet, "line_count": len(snippet.splitlines())})
            replaced = replaced.replace(snippet, f"__CODE_BLOCK_{idx}__", 1)
            count += 1

        return replaced

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """
        Extract structured sections by headings while ignoring code placeholders.
        Supported (case-insensitive): Quick Plan, Next Action/Step, Optional Boost/Enhancement,
        Summary/Overview, Details/Explanation.
        """
        sections: Dict[str, str] = {}
        lines = content.split("\n")
        current_key: Optional[str] = None
        buf: List[str] = []

        def flush():
            nonlocal current_key, buf
            if current_key and buf:
                sections[current_key] = "\n".join(buf).strip()
            current_key, buf = None, []

        def classify(line: str) -> Optional[str]:
            stripped = line.strip()
            if re.match(r"^#{1,6}\s*(quick\s*plan|plan)\s*:?\s*$", stripped, re.I):
                return "quick_plan"
            if re.match(r"^#{1,6}\s*(next\s*(action|step))\s*:?\s*$", stripped, re.I):
                return "next_action"
            if re.match(r"^#{1,6}\s*(optional\s*boost|boost|enhancement)\s*:?\s*$", stripped, re.I):
                return "optional_boost"
            if re.match(r"^#{1,6}\s*(summary|overview)\s*:?\s*$", stripped, re.I):
                return "summary"
            if re.match(r"^#{1,6}\s*(details|explanation)\s*:?\s*$", stripped, re.I):
                return "details"
            return None

        for line in lines:
            # treat code placeholders as normal text; section parsing ignores them implicitly
            key = classify(line)
            if key:
                flush()
                current_key = key
                continue
            if current_key is not None:
                buf.append(line)

        flush()
        return sections

    # -------------------------
    # Formatting Pipeline
    # -------------------------

    def _apply_consistent_formatting(
        self,
        structured: FormattedResponse,
        intent: str,
        persona: str,
        options: FormattingOptions
    ) -> FormattedResponse:
        """
        Rebuild content deterministically:
          1) Normalize headings
          2) Normalize bullets
          3) Normalize code blocks (truncate if needed) and restore placeholders
          4) Optional onboarding skeleton (Quick Plan, Next Action, Optional Boost)
          5) Normalize tables if present
        """
        # Work from the original content (keeps text outside detected blocks)
        content = structured.content

        # Headings
        if options.enable_structured_sections and options.enable_auto_headings:
            content = self._format_headings(content, options)

        # Bullets
        content = self._format_bullets(content, options)

        # Tables
        if options.enable_table_normalization:
            content = self._normalize_tables(content)

        # Code blocks (truncate + ensure proper triple-fence style)
        content = self._format_and_restore_code_blocks(content, structured.code_blocks, options)

        # Onboarding scaffold (if intent/sections suggest it)
        if options.enable_onboarding_format and self._needs_onboarding_format(intent, structured.sections):
            content = self._apply_onboarding_format(content, structured.sections, options)

        # Metadata
        meta = {
            "headings_formatted": bool(options.enable_structured_sections and options.enable_auto_headings),
            "bullets_formatted": True,
            "tables_normalized": options.enable_table_normalization,
            "code_highlighted": options.enable_code_highlighting,
            "onboarding_applied": options.enable_onboarding_format,
        }

        return FormattedResponse(
            content=content,
            sections=structured.sections,
            code_blocks=structured.code_blocks,
            metadata={**structured.metadata, **meta},
        )

    def _format_headings(self, content: str, options: FormattingOptions) -> str:
        """
        Normalize heading levels/shape:
        - Convert any #..###### or Title: lines to the chosen heading_style
        - Keep existing text; avoid duplicate reformatting by running once
        """
        lines = content.split("\n")
        out: List[str] = []
        for line in lines:
            s = line.strip()
            # markdown headings
            m = re.match(r"^(#{1,6})\s+(.+)$", s)
            if m:
                out.append(f"{options.heading_style} {m.group(2).strip()}")
                continue
            # Title-like lines
            m2 = re.match(r"^([A-Z][A-Za-z0-9\s\/&\-\(\)]+):\s*$", s)
            if m2:
                out.append(f"{options.heading_style} {m2.group(1).strip()}")
                continue
            out.append(line)
        return "\n".join(out)

    def _format_bullets(self, content: str, options: FormattingOptions) -> str:
        """Normalize bullets and ordered lists to a single bullet style."""
        lines = content.split("\n")
        out: List[str] = []
        for line in lines:
            if re.match(r"^\s*[-*+]\s+", line):
                out.append(re.sub(r"^\s*[-*+]\s+", f"{options.bullet_style} ", line))
            elif re.match(r"^\s*\d+\.\s+", line):
                out.append(re.sub(r"^\s*\d+\.\s+", f"{options.bullet_style} ", line))
            else:
                out.append(line)
        return "\n".join(out)

    def _normalize_tables(self, content: str) -> str:
        """
        Light normalization for Markdown tables:
        - Ensure header separators exist when header row pattern is detected.
        """
        # Very light heuristic: if a table header line with pipes has no separator next line, add one.
        lines = content.split("\n")
        out: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            out.append(line)
            if re.search(r"\|", line) and not re.match(r"^\s*[-:|]+\s*$", line):
                # Potential header. If next line is not a separator but also has pipes, add one.
                if i + 1 < len(lines):
                    nxt = lines[i + 1]
                    if re.search(r"\|", nxt) and not re.match(r"^\s*[-:|]+\s*$", nxt):
                        cols = max(1, len([c for c in line.split("|") if c.strip() != ""]))
                        out.append("| " + " | ".join(["---"] * cols) + " |")
                        # Don't skip next line; just continue normally
            i += 1
        return "\n".join(out)

    def _format_and_restore_code_blocks(
        self,
        content: str,
        code_blocks: List[Dict[str, Any]],
        options: FormattingOptions
    ) -> str:
        """Restore placeholders to deterministic fenced blocks with truncation if necessary."""
        def _truncate(code: str, limit: int) -> str:
            lines = code.splitlines()
            if len(lines) <= limit:
                return code
            visible = "\n".join(lines[:limit])
            return f"{visible}\n... ({len(lines) - limit} more lines)"

        # Replace each placeholder with its properly fenced block
        for i, block in enumerate(code_blocks):
            lang = (block.get("language") or "text").strip() or "text"
            code = block.get("code") or ""
            if options.enable_code_highlighting:
                code_out = _truncate(code, options.max_code_block_lines)
                fenced = f"```{lang}\n{code_out}\n```"
            else:
                # Even if highlighting is off, keep code fenced for consistency
                code_out = _truncate(code, options.max_code_block_lines)
                fenced = f"```\n{code_out}\n```"
            placeholder = f"__CODE_BLOCK_{i}__"
            content = content.replace(placeholder, fenced)
        return content

    def _needs_onboarding_format(self, intent: str, sections: Dict[str, str]) -> bool:
        onboarding_intents = {"general_assist", "setup_help", "getting_started"}
        has_sections = any(k in sections for k in ("quick_plan", "next_action"))
        return intent in onboarding_intents or has_sections

    def _apply_onboarding_format(
        self,
        content: str,
        sections: Dict[str, str],
        options: FormattingOptions
    ) -> str:
        if not sections:
            return content

        parts: List[str] = []
        if "quick_plan" in sections:
            parts.append(f"{options.heading_style} Quick Plan\n{sections['quick_plan'].strip()}")
        if "next_action" in sections:
            parts.append(f"{options.heading_style} Next Action\n{sections['next_action'].strip()}")
        if "optional_boost" in sections:
            parts.append(f"{options.heading_style} Optional Boost\n{sections['optional_boost'].strip()}")

        if not parts:
            return content

        # Try to avoid duplicating section content: remove raw occurrences before appending scaffold
        structured = content
        for v in sections.values():
            if v and v in structured:
                structured = structured.replace(v, "").strip()

        scaffold = "\n\n".join(parts)
        if structured and structured != content:
            return f"{structured}\n\n{scaffold}"
        return scaffold

    # -------------------------
    # CopilotKit (Optional)
    # -------------------------

    def _check_copilotkit_availability(self) -> bool:
        """Soft-check; never raises."""
        try:
            # In Kari, availability is config-driven. Do not import heavy libs here.
            return bool(self.config.enable_copilotkit)
        except Exception:
            return False

    def _add_copilotkit_enhancements(
        self,
        formatted_response: FormattedResponse,
        intent: str,
        persona: str,
        options: FormattingOptions
    ) -> Optional[Dict[str, Any]]:
        if not self._copilotkit_available:
            return None
        try:
            enhancements: Dict[str, Any] = {}

            # Complexity graph
            if options.copilotkit_complexity_graphs and self._has_code_content(formatted_response):
                enhancements["complexity_graph"] = self._generate_complexity_graph(formatted_response)

            # Inline suggestions
            if options.copilotkit_inline_suggestions:
                enhancements["inline_suggestions"] = self._generate_inline_suggestions(formatted_response, intent, persona)

            # UI hints
            if options.copilotkit_ui_hints:
                enhancements["ui_hints"] = self._generate_ui_hints(formatted_response, intent)

            # Metrics
            enhancements["performance_metrics"] = {
                "code_blocks_count": len(formatted_response.code_blocks),
                "sections_count": len(formatted_response.sections),
                "estimated_complexity": self._estimate_complexity(formatted_response),
                "suggested_next_actions": self._suggest_next_actions(intent, persona),
            }

            return enhancements or None
        except Exception as e:
            logger.warning(f"[DRYFormatter] CopilotKit enhancement failed: {e}")
            return None

    def _has_code_content(self, response: FormattedResponse) -> bool:
        return len(response.code_blocks) > 0

    def _generate_complexity_graph(self, response: FormattedResponse) -> Dict[str, Any]:
        graph = {"type": "complexity_graph", "data": {"nodes": [], "edges": [], "metrics": {}}}
        for i, block in enumerate(response.code_blocks):
            lang = (block.get("language") or "text").strip() or "text"
            lines = int(block.get("line_count") or 0)
            score = min(lines * 0.08, 10.0)
            graph["data"]["nodes"].append(
                {"id": f"code_block_{i}", "label": f"{lang.upper()} Block", "complexity": round(score, 2), "lines": lines}
            )
        return graph

    def _generate_inline_suggestions(
        self,
        response: FormattedResponse,
        intent: str,
        persona: str
    ) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []
        intent_map = {
            "optimize_code": [
                {"type": "optimization", "text": "Run a profiler and capture hotspots."},
                {"type": "refactor", "text": "Consolidate duplicate logic and extract pure functions."},
            ],
            "debug_error": [
                {"type": "debugging", "text": "Enable structured logging around failure points."},
                {"type": "testing", "text": "Reproduce the error with a minimal failing test."},
            ],
            "documentation": [
                {"type": "docs", "text": "Include runnable examples and edge-case notes."},
                {"type": "docs", "text": "Add a quickstart and a troubleshooting section."},
            ],
            "general_assist": [
                {"type": "process", "text": "Clarify constraints, resources, and timelines."},
            ],
        }
        suggestions.extend(intent_map.get(intent, []))
        if self._has_code_content(response):
            suggestions.extend(
                [
                    {"type": "code_review", "text": "Scan for security issues (injection, unsafe deserialization)."},
                    {"type": "testing", "text": "Increase coverage on branches with high cyclomatic complexity."},
                ]
            )
        return suggestions

    def _generate_ui_hints(self, response: FormattedResponse, intent: str) -> Dict[str, Any]:
        hints: Dict[str, Any] = {"suggested_actions": [], "ui_components": [], "interaction_hints": []}
        if intent == "optimize_code":
            hints["suggested_actions"].append("Show performance metrics")
            hints["ui_components"].append("performance_dashboard")
        if intent == "debug_error":
            hints["suggested_actions"].append("Enable debug mode")
            hints["ui_components"].append("debug_console")
        if self._has_code_content(response):
            hints["suggested_actions"] += ["Syntax highlighting", "Copy to clipboard", "Run in sandbox"]
            hints["ui_components"].append("code_editor")
        return hints

    def _estimate_complexity(self, response: FormattedResponse) -> str:
        score = 0
        score += len(response.code_blocks) * 2
        score += len(response.sections)
        L = len(response.content)
        score += 2 if L > 1000 else (1 if L > 500 else 0)
        return "high" if score >= 8 else "medium" if score >= 4 else "low"

    def _suggest_next_actions(self, intent: str, persona: str) -> List[str]:
        actions: Dict[str, List[str]] = {
            "optimize_code": ["Profile performance", "Run benchmarks", "Review architecture"],
            "debug_error": ["Add logging", "Write tests", "Check dependencies"],
            "documentation": ["Add examples", "Review clarity", "Update references"],
            "general_assist": ["Clarify requirements", "Break down tasks", "Set priorities"],
        }
        return (actions.get(intent) or ["Continue conversation", "Ask follow-up questions"])[:3]


# -------------------------
# Utilities
# -------------------------

class _LatencyTimer:
    """Async-agnostic context manager for Prometheus observe() calls."""
    def __init__(self, hist): self.hist = hist
    def __enter__(self): self._t = None  # pragma: no cover
    def __exit__(self, exc_type, exc, tb):  # pragma: no cover
        try:
            pass
        finally:
            pass
    def __call__(self, *args, **kwargs):  # allow 'with _LatencyTimer(hist):'
        return self
    def __aenter__(self):  # pragma: no cover
        import time as _t
        self._start = _t.time()
        return self
    def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        import time as _t
        try:
            self.hist.observe(max(0.0, _t.time() - getattr(self, "_start", _t.time())))
        except Exception:
            pass


# Factory function
def create_formatter(config: Optional[PipelineConfig] = None) -> DRYFormatter:
    return DRYFormatter(config)


__all__ = ["DRYFormatter", "FormattingOptions", "FormattedResponse", "create_formatter"]
