"""
Production-grade response formatting engine for AI-Karen.

This engine provides:
- intelligent content analysis
- markdown normalization
- hierarchical organization
- code block detection and formatting
- lightweight syntax highlighting
- citation/source extraction
- responsive formatting variants
- accessibility augmentations
- navigation aids for long technical answers

Designed to support API routes expecting:
- ResponseFormattingEngine
- FormattingContext
- DisplayContext
- AccessibilityLevel
- FormatType
- ContentType

This file intentionally keeps external dependencies minimal.
"""

from __future__ import annotations

import html
import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    from ai_karen_engine.pydantic_stub import BaseModel, Field  # type: ignore

logger = logging.getLogger(__name__)


class DisplayContext(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TERMINAL = "terminal"
    API = "api"
    PRINT = "print"


class AccessibilityLevel(str, Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


class FormatType(str, Enum):
    STANDARD_MARKDOWN = "standard_markdown"
    TECHNICAL_MARKDOWN = "technical_markdown"
    SEARCH_ANSWER = "search_answer"
    MOBILE_COMPACT = "mobile_compact"
    TERMINAL_PLAIN = "terminal_plain"
    API_STRUCTURED = "api_structured"
    PRINT_FRIENDLY = "print_friendly"
    ACCESSIBLE_MARKDOWN = "accessible_markdown"


class ContentType(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CODE_HEAVY = "code_heavy"
    SEARCH_SUMMARY = "search_summary"
    TUTORIAL = "tutorial"
    ANALYSIS = "analysis"
    QA = "qa"
    MIXED = "mixed"


class SectionType(str, Enum):
    TITLE = "title"
    HEADER = "header"
    SUMMARY = "summary"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    CITATIONS = "citations"
    WARNING = "warning"
    FOOTER = "footer"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FormattingContext(BaseModel):
    display_context: DisplayContext = DisplayContext.DESKTOP
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    content_length: int = 0
    technical_level: str = "intermediate"
    language: str = "en"


class NavigationAid(BaseModel):
    label: str
    target_id: str
    level: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentSection(BaseModel):
    content: str
    section_type: SectionType
    priority: int = 50
    format_hint: Optional[FormatType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    navigation_id: Optional[str] = None
    accessibility_text: Optional[str] = None


class FormattedResponse(BaseModel):
    content: str
    format_type: FormatType
    sections: List[ContentSection] = Field(default_factory=list)
    navigation_aids: List[NavigationAid] = Field(default_factory=list)
    accessibility_features: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    estimated_reading_time: Optional[int] = None


@dataclass
class CodeBlockInfo:
    language: str
    code: str
    start: int
    end: int


@dataclass
class CitationInfo:
    title: str
    url: str
    snippet: str = ""


@dataclass
class AnalysisResult:
    content_type: ContentType
    complexity: ComplexityLevel
    sections: List[ContentSection]
    code_blocks: List[CodeBlockInfo]
    data_structures: List[str]
    length: int
    reading_time: int
    technical_density: float
    citations: List[CitationInfo] = field(default_factory=list)


class ResponseFormattingEngine:
    """
    High-robustness response formatting engine for model output, search synthesis,
    code-heavy answers, and structured display surfaces.
    """

    CODE_BLOCK_RE = re.compile(r"```([\w+-]*)\n?(.*?)```", re.DOTALL)
    INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
    URL_RE = re.compile(r"https?://[^\s)>\]]+")
    MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    BULLET_RE = re.compile(r"^\s*[-*]\s+.+$", re.MULTILINE)
    NUMBERED_RE = re.compile(r"^\s*\d+\.\s+.+$", re.MULTILINE)
    TABLE_RE = re.compile(r"^\|.+\|\s*$", re.MULTILINE)

    def __init__(self) -> None:
        self.code_languages = {
            "python",
            "javascript",
            "typescript",
            "bash",
            "sh",
            "json",
            "yaml",
            "yml",
            "html",
            "css",
            "sql",
            "markdown",
            "text",
            "tsx",
            "jsx",
            "dockerfile",
            "toml",
            "ini",
            "xml",
        }

        self.syntax_highlighters = {
            "python": self._highlight_python,
            "javascript": self._highlight_javascript,
            "typescript": self._highlight_javascript,
            "json": self._highlight_json,
            "yaml": self._highlight_yaml,
            "bash": self._highlight_bash,
            "sh": self._highlight_bash,
            "sql": self._highlight_sql,
        }

    async def format_response(
        self,
        content: str,
        context: FormattingContext,
    ) -> FormattedResponse:
        """
        Format content according to analysis + display/accessibility context.
        """
        analysis_dict = await self.analyze_content_structure(content)
        analysis = self._analysis_from_dict(analysis_dict)

        format_type = await self.select_optimal_format(content, context)
        sections = await self.organize_content_hierarchically(content)

        normalized = self._normalize_content(content)
        normalized = self._repair_markdown_headers(normalized)
        normalized = self._repair_lists(normalized)
        normalized = self._repair_code_blocks(normalized)
        normalized = self._normalize_tables(normalized)
        normalized = self._normalize_spacing(normalized)
        normalized = self._append_citations_section_if_needed(normalized, analysis.citations, format_type)
        normalized = self._apply_display_transform(normalized, format_type, context)
        normalized = self._apply_accessibility_transform(normalized, context, analysis)

        navigation_aids = self._build_navigation_aids(sections, context)
        accessibility_features = self._build_accessibility_features(context, analysis, navigation_aids)

        metadata = {
            "content_type": analysis.content_type.value,
            "complexity": analysis.complexity.value,
            "technical_density": analysis.technical_density,
            "code_blocks_count": len(analysis.code_blocks),
            "citations_count": len(analysis.citations),
            "sections_count": len(sections),
            "display_context": context.display_context.value,
            "accessibility_level": context.accessibility_level.value,
            "language": context.language,
            "format_version": "1.0.0",
            "has_code_blocks": len(analysis.code_blocks) > 0,
            "has_tables": bool(self.TABLE_RE.search(content)),
            "has_citations": len(analysis.citations) > 0,
        }

        return FormattedResponse(
            content=normalized,
            format_type=format_type,
            sections=sections,
            navigation_aids=navigation_aids,
            accessibility_features=accessibility_features,
            metadata=metadata,
            estimated_reading_time=analysis.reading_time,
        )

    async def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze content and return structured attributes expected by routes.
        """
        content = content or ""
        length = len(content)
        code_blocks = self._extract_code_blocks(content)
        citations = self._extract_citations(content)
        sections = self._detect_sections(content)
        data_structures = self._detect_data_structures(content)

        technical_density = self._calculate_technical_density(content, code_blocks, data_structures)
        complexity = self._classify_complexity(length, technical_density, len(code_blocks), len(sections))
        content_type = self._detect_content_type(content, code_blocks, citations, technical_density)
        reading_time = self._estimate_reading_time(content)

        return {
            "content_type": content_type,
            "complexity": complexity.value,
            "sections": sections,
            "code_blocks": code_blocks,
            "data_structures": data_structures,
            "length": length,
            "reading_time": reading_time,
            "technical_density": technical_density,
            "citations": citations,
        }

    async def select_optimal_format(
        self,
        content: str,
        context: FormattingContext,
    ) -> FormatType:
        """
        Choose best formatting mode from content + context.
        """
        analysis = await self.analyze_content_structure(content)

        if context.display_context == DisplayContext.API:
            return FormatType.API_STRUCTURED

        if context.display_context == DisplayContext.TERMINAL:
            return FormatType.TERMINAL_PLAIN

        if context.display_context == DisplayContext.PRINT:
            return FormatType.PRINT_FRIENDLY

        if context.display_context == DisplayContext.MOBILE:
            return FormatType.MOBILE_COMPACT

        if context.accessibility_level == AccessibilityLevel.FULL:
            return FormatType.ACCESSIBLE_MARKDOWN

        if analysis["content_type"] in {ContentType.CODE_HEAVY, ContentType.TECHNICAL}:
            return FormatType.TECHNICAL_MARKDOWN

        if analysis["content_type"] == ContentType.SEARCH_SUMMARY or analysis["citations"]:
            return FormatType.SEARCH_ANSWER

        return FormatType.STANDARD_MARKDOWN

    async def organize_content_hierarchically(self, content: str) -> List[ContentSection]:
        """
        Split content into hierarchical sections with metadata.
        """
        sections: List[ContentSection] = []
        text = self._normalize_spacing(content)
        lines = text.splitlines()

        buffer: List[str] = []
        current_header: Optional[str] = None
        nav_counter = 0

        def flush_buffer(section_type: SectionType = SectionType.PARAGRAPH) -> None:
            nonlocal buffer, nav_counter
            block = "\n".join(buffer).strip()
            if not block:
                buffer = []
                return

            priority = self._section_priority(section_type, block)
            nav_id = None
            if section_type in {SectionType.HEADER, SectionType.SUMMARY, SectionType.CITATIONS}:
                nav_counter += 1
                nav_id = f"section-{nav_counter}"

            sections.append(
                ContentSection(
                    content=block,
                    section_type=section_type,
                    priority=priority,
                    navigation_id=nav_id,
                    accessibility_text=self._build_accessibility_text(section_type, block),
                )
            )
            buffer = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                flush_buffer()
                continue

            if self.HEADER_RE.match(stripped):
                flush_buffer()
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.HEADER,
                        priority=95,
                        navigation_id=f"section-{nav_counter + 1}",
                        accessibility_text=f"Header: {self._header_text(stripped)}",
                    )
                )
                nav_counter += 1
                current_header = stripped
                continue

            if stripped.startswith("```"):
                flush_buffer()
                buffer.append(stripped)
                continue

            if stripped.startswith(">"):
                flush_buffer()
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.QUOTE,
                        priority=55,
                        accessibility_text=f"Quoted content: {stripped.lstrip('> ').strip()}",
                    )
                )
                continue

            buffer.append(line)

        flush_buffer()

        if not sections and text:
            sections.append(
                ContentSection(
                    content=text,
                    section_type=SectionType.PARAGRAPH,
                    priority=50,
                    accessibility_text="Main content paragraph",
                )
            )

        sections = self._reclassify_sections(sections)
        sections.sort(key=lambda s: s.priority, reverse=True)
        return sections

    async def apply_syntax_highlighting(self, code: str, language: str = "text") -> str:
        """
        Apply lightweight HTML-safe syntax highlighting.
        Returns markup string, suitable for future UI renderers.
        """
        lang = (language or "text").lower().strip()
        if lang not in self.syntax_highlighters:
            return f"<pre><code class=\"language-{html.escape(lang)}\">{html.escape(code)}</code></pre>"

        highlighted_body = self.syntax_highlighters[lang](code)
        return f"<pre><code class=\"language-{html.escape(lang)}\">{highlighted_body}</code></pre>"

    def _analysis_from_dict(self, data: Dict[str, Any]) -> AnalysisResult:
        return AnalysisResult(
            content_type=data["content_type"],
            complexity=ComplexityLevel(data["complexity"]),
            sections=data["sections"],
            code_blocks=data["code_blocks"],
            data_structures=data["data_structures"],
            length=data["length"],
            reading_time=data["reading_time"],
            technical_density=data["technical_density"],
            citations=data.get("citations", []),
        )

    def _normalize_content(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\t", "    ")
        return text.strip()

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    def _repair_markdown_headers(self, text: str) -> str:
        lines = text.splitlines()
        repaired: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                repaired.append(line)
                continue

            title_match = re.match(r"^(title)\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if title_match:
                repaired.append(f"# {title_match.group(2).strip()}")
                continue

            section_label_match = re.match(
                r"^(introduction|overview|background|summary|conclusion|key takeaways)\s*:?\s*$",
                stripped,
                re.IGNORECASE,
            )
            if section_label_match:
                section_name = section_label_match.group(1).strip().title()
                repaired.append(f"## {section_name}")
                continue

            if stripped.isupper() and 1 <= len(stripped.split()) <= 8 and not stripped.startswith("#"):
                repaired.append(f"## {stripped.title()}")
                continue

            if re.match(r"^[A-Z][A-Za-z0-9 /&:-]{3,60}$", stripped) and not stripped.startswith("#") and stripped.endswith(":") is False:
                if len(stripped.split()) <= 7 and stripped == stripped.title():
                    repaired.append(f"## {stripped}")
                    continue

            repaired.append(line)

        return "\n".join(repaired)

    def _repair_lists(self, text: str) -> str:
        lines = text.splitlines()
        out: List[str] = []
        prev_was_list = False

        for line in lines:
            stripped = line.strip()

            is_list = bool(re.match(r"^[-*]\s+.+", stripped) or re.match(r"^\d+\.\s+.+", stripped))
            if is_list and out:
                if out[-1].strip() and not prev_was_list:
                    out.append("")
            out.append(line)
            prev_was_list = is_list

        return "\n".join(out)

    def _repair_code_blocks(self, text: str) -> str:
        fence_count = text.count("```")
        if fence_count % 2 != 0:
            text += "\n```"

        def repl(match: re.Match[str]) -> str:
            language = (match.group(1) or "").strip().lower()
            body = (match.group(2) or "").strip("\n")
            if not language:
                language = self._detect_language(body)
            return f"```{language}\n{body}\n```"

        return self.CODE_BLOCK_RE.sub(repl, text)

    def _normalize_tables(self, text: str) -> str:
        lines = text.splitlines()
        if sum(1 for line in lines if self.TABLE_RE.match(line)) < 2:
            return text
        return text

    def _append_citations_section_if_needed(
        self,
        text: str,
        citations: List[CitationInfo],
        format_type: FormatType,
    ) -> str:
        if not citations:
            return text

        if format_type not in {FormatType.SEARCH_ANSWER, FormatType.TECHNICAL_MARKDOWN, FormatType.ACCESSIBLE_MARKDOWN}:
            return text

        if "## Sources" in text or "## Citations" in text:
            return text

        lines = ["", "## Sources", ""]
        seen: set[str] = set()

        for citation in citations:
            if citation.url in seen:
                continue
            seen.add(citation.url)
            title = citation.title or citation.url
            if citation.snippet:
                lines.append(f"- [{title}]({citation.url}) — {citation.snippet}")
            else:
                lines.append(f"- [{title}]({citation.url})")

        return text.rstrip() + "\n" + "\n".join(lines).rstrip()

    def _apply_display_transform(
        self,
        text: str,
        format_type: FormatType,
        context: FormattingContext,
    ) -> str:
        if format_type == FormatType.TERMINAL_PLAIN:
            return self._to_terminal_plain(text)

        if format_type == FormatType.MOBILE_COMPACT:
            return self._to_mobile_compact(text)

        if format_type == FormatType.PRINT_FRIENDLY:
            return self._to_print_friendly(text)

        if format_type == FormatType.API_STRUCTURED:
            return text

        return text

    def _apply_accessibility_transform(
        self,
        text: str,
        context: FormattingContext,
        analysis: AnalysisResult,
    ) -> str:
        if context.accessibility_level == AccessibilityLevel.BASIC:
            return text

        additions: List[str] = []

        if context.accessibility_level in {AccessibilityLevel.ENHANCED, AccessibilityLevel.FULL}:
            additions.append(f"<!-- reading-time: {analysis.reading_time} min -->")

        if context.accessibility_level == AccessibilityLevel.FULL:
            additions.append(f"<!-- content-type: {analysis.content_type.value} -->")
            additions.append(f"<!-- complexity: {analysis.complexity.value} -->")

        if additions:
            return "\n".join(additions) + "\n" + text

        return text

    def _build_navigation_aids(
        self,
        sections: List[ContentSection],
        context: FormattingContext,
    ) -> List[NavigationAid]:
        navs: List[NavigationAid] = []

        for section in sections:
            if not section.navigation_id:
                continue

            label = self._nav_label(section.content)
            navs.append(
                NavigationAid(
                    label=label,
                    target_id=section.navigation_id,
                    level=1,
                    metadata={"section_type": section.section_type.value},
                )
            )

        if context.display_context == DisplayContext.MOBILE:
            return navs[:6]

        return navs

    def _build_accessibility_features(
        self,
        context: FormattingContext,
        analysis: AnalysisResult,
        navigation_aids: List[NavigationAid],
    ) -> Dict[str, Any]:
        features: Dict[str, Any] = {
            "estimated_reading_time": analysis.reading_time,
            "technical_density": analysis.technical_density,
            "keyboard_navigation": len(navigation_aids) > 0,
        }

        if context.accessibility_level in {AccessibilityLevel.ENHANCED, AccessibilityLevel.FULL}:
            features["navigation_aids"] = [nav.model_dump() for nav in navigation_aids]
            features["screen_reader_text"] = (
                f"Content type {analysis.content_type.value}. "
                f"Complexity {analysis.complexity.value}. "
                f"Estimated reading time {analysis.reading_time} minutes."
            )

        if context.accessibility_level == AccessibilityLevel.FULL:
            features["section_count"] = len(analysis.sections)
            features["code_blocks_count"] = len(analysis.code_blocks)
            features["citations_count"] = len(analysis.citations)

        if analysis.technical_density > 0.7:
            features["content_warning"] = "Highly technical content."

        return features

    def _extract_code_blocks(self, content: str) -> List[CodeBlockInfo]:
        blocks: List[CodeBlockInfo] = []

        for match in self.CODE_BLOCK_RE.finditer(content):
            language = (match.group(1) or "").strip().lower()
            body = (match.group(2) or "").strip("\n")
            if not language:
                language = self._detect_language(body)
            blocks.append(CodeBlockInfo(language=language, code=body, start=match.start(), end=match.end()))

        return blocks

    def _extract_citations(self, content: str) -> List[CitationInfo]:
        citations: List[CitationInfo] = []

        for match in self.MARKDOWN_LINK_RE.finditer(content):
            citations.append(CitationInfo(title=match.group(1).strip(), url=match.group(2).strip()))

        if not citations:
            for url in self.URL_RE.findall(content):
                citations.append(CitationInfo(title=url, url=url))

        deduped: List[CitationInfo] = []
        seen: set[str] = set()

        for citation in citations:
            if citation.url in seen:
                continue
            seen.add(citation.url)
            deduped.append(citation)

        return deduped

    def _detect_sections(self, content: str) -> List[ContentSection]:
        lines = self._normalize_spacing(content).splitlines()
        sections: List[ContentSection] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self.HEADER_RE.match(stripped):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.HEADER,
                        priority=90,
                        navigation_id=f"auto-{len(sections) + 1}",
                    )
                )
            elif stripped.startswith("```"):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.CODE,
                        priority=80,
                    )
                )
            elif stripped.startswith(">"):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.QUOTE,
                        priority=45,
                    )
                )
            elif stripped.startswith("- ") or re.match(r"^\d+\.\s+", stripped):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.LIST,
                        priority=55,
                    )
                )
            else:
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.PARAGRAPH,
                        priority=50,
                    )
                )

        return sections

    def _detect_data_structures(self, content: str) -> List[str]:
        structures: List[str] = []

        if "{" in content and "}" in content:
            structures.append("json_like")
        if "[" in content and "]" in content:
            structures.append("array_like")
        if self.TABLE_RE.search(content):
            structures.append("markdown_table")
        if re.search(r"^\s*-\s+.+", content, re.MULTILINE):
            structures.append("bullet_list")
        if re.search(r"^\s*\d+\.\s+.+", content, re.MULTILINE):
            structures.append("numbered_list")

        return structures

    def _calculate_technical_density(
        self,
        content: str,
        code_blocks: List[CodeBlockInfo],
        data_structures: List[str],
    ) -> float:
        if not content.strip():
            return 0.0

        keywords = [
            "api", "endpoint", "schema", "function", "class", "method", "async",
            "token", "request", "response", "docker", "yaml", "json", "sql",
            "python", "javascript", "typescript", "regex", "stream", "orchestrator",
            "latency", "throughput", "inference", "embedding", "retrieval",
        ]

        lowered = content.lower()
        keyword_hits = sum(lowered.count(k) for k in keywords)
        keyword_score = min(keyword_hits / 20.0, 1.0)

        code_score = min(len(code_blocks) / 5.0, 1.0)
        structure_score = min(len(data_structures) / 5.0, 1.0)

        density = (keyword_score * 0.5) + (code_score * 0.3) + (structure_score * 0.2)
        return round(min(density, 1.0), 3)

    def _classify_complexity(
        self,
        length: int,
        technical_density: float,
        code_blocks_count: int,
        sections_count: int,
    ) -> ComplexityLevel:
        score = 0

        if length > 800:
            score += 1
        if length > 2500:
            score += 1
        if technical_density > 0.35:
            score += 1
        if technical_density > 0.65:
            score += 1
        if code_blocks_count >= 2:
            score += 1
        if sections_count >= 8:
            score += 1

        if score <= 1:
            return ComplexityLevel.SIMPLE
        if score <= 3:
            return ComplexityLevel.INTERMEDIATE
        if score <= 5:
            return ComplexityLevel.ADVANCED
        return ComplexityLevel.EXPERT

    def _detect_content_type(
        self,
        content: str,
        code_blocks: List[CodeBlockInfo],
        citations: List[CitationInfo],
        technical_density: float,
    ) -> ContentType:
        lowered = content.lower()

        if citations and ("source" in lowered or "according to" in lowered or "latest" in lowered):
            return ContentType.SEARCH_SUMMARY

        if len(code_blocks) >= 2 or technical_density > 0.7:
            return ContentType.CODE_HEAVY

        if technical_density > 0.45:
            return ContentType.TECHNICAL

        if "step 1" in lowered or "tutorial" in lowered or "how to" in lowered:
            return ContentType.TUTORIAL

        if "analysis" in lowered or "trade-off" in lowered or "comparison" in lowered:
            return ContentType.ANALYSIS

        if re.search(r"\bq[:\s].+\ba[:\s]", lowered):
            return ContentType.QA

        return ContentType.GENERAL

    def _estimate_reading_time(self, content: str) -> int:
        plain = self.CODE_BLOCK_RE.sub(" ", content)
        words = re.findall(r"\b\w+\b", plain)
        word_count = len(words)
        return max(1, math.ceil(word_count / 220))

    def _detect_language(self, code: str) -> str:
        lowered = code.lower()

        if re.search(r"^\s*from\s+\w+\s+import\s+", code, re.MULTILINE) or re.search(r"^\s*def\s+\w+\(", code, re.MULTILINE):
            return "python"
        if "console.log(" in code or "function " in code or "=>" in code:
            return "javascript"
        if re.search(r"^\s*interface\s+\w+", code, re.MULTILINE) or ": string" in code or ": number" in code:
            return "typescript"
        if lowered.strip().startswith("{") and lowered.strip().endswith("}"):
            return "json"
        if re.search(r"^\s*-\s+\w+:", code, re.MULTILINE) or ":" in code and "\n" in code and "{" not in code:
            return "yaml"
        if re.search(r"^\s*select\s+.+\s+from\s+", lowered, re.MULTILINE):
            return "sql"
        if lowered.startswith("#!/bin/bash") or re.search(r"^\s*(export|echo|if\s+\[)", lowered, re.MULTILINE):
            return "bash"
        if "<html" in lowered or re.search(r"</\w+>", lowered):
            return "html"
        return "text"

    def _highlight_python(self, code: str) -> str:
        keywords = {
            "def", "class", "return", "if", "elif", "else", "for", "while",
            "import", "from", "try", "except", "finally", "async", "await",
            "with", "pass", "raise", "yield", "lambda", "True", "False", "None",
        }
        return self._simple_keyword_highlight(code, keywords)

    def _highlight_javascript(self, code: str) -> str:
        keywords = {
            "function", "return", "if", "else", "for", "while", "const", "let",
            "var", "import", "from", "export", "async", "await", "class", "new",
            "true", "false", "null", "undefined",
        }
        return self._simple_keyword_highlight(code, keywords)

    def _highlight_json(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(r'(&quot;[^&]+&quot;)(\s*:)', r'<span class="json-key">\1</span>\2', escaped)
        return escaped

    def _highlight_yaml(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(r"^(\s*[\w\-\.]+:)", r'<span class="yaml-key">\1</span>', escaped, flags=re.MULTILINE)
        return escaped

    def _highlight_bash(self, code: str) -> str:
        keywords = {"echo", "export", "if", "then", "fi", "for", "do", "done", "case", "esac", "while", "in"}
        return self._simple_keyword_highlight(code, keywords)

    def _highlight_sql(self, code: str) -> str:
        keywords = {
            "select", "from", "where", "join", "left", "right", "inner", "outer",
            "group", "by", "order", "insert", "update", "delete", "create", "table",
            "into", "values", "limit", "having", "as",
        }
        return self._simple_keyword_highlight(code, keywords, case_insensitive=True)

    def _simple_keyword_highlight(
        self,
        code: str,
        keywords: set[str],
        case_insensitive: bool = False,
    ) -> str:
        escaped = html.escape(code)
        flags = re.IGNORECASE if case_insensitive else 0

        for keyword in sorted(keywords, key=len, reverse=True):
            escaped = re.sub(
                rf"\b({re.escape(keyword)})\b",
                r'<span class="kw">\1</span>',
                escaped,
                flags=flags,
            )

        escaped = re.sub(r"(&quot;.*?&quot;)", r'<span class="str">\1</span>', escaped)
        escaped = re.sub(r"(^\s*#.*$)", r'<span class="comment">\1</span>', escaped, flags=re.MULTILINE)
        return escaped

    def _to_terminal_plain(self, text: str) -> str:
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
        text = text.replace("```", "")
        return text

    def _to_mobile_compact(self, text: str) -> str:
        lines = text.splitlines()
        compacted: List[str] = []
        blank_streak = 0

        for line in lines:
            if not line.strip():
                blank_streak += 1
                if blank_streak <= 1:
                    compacted.append("")
                continue
            blank_streak = 0
            compacted.append(line)

        return "\n".join(compacted).strip()

    def _to_print_friendly(self, text: str) -> str:
        return text.replace("<!--", "").replace("-->", "")

    def _section_priority(self, section_type: SectionType, block: str) -> int:
        if section_type == SectionType.HEADER:
            return 95
        if section_type == SectionType.SUMMARY:
            return 90
        if section_type == SectionType.CODE:
            return 80
        if section_type == SectionType.CITATIONS:
            return 75
        if section_type == SectionType.LIST:
            return 60
        return 50

    def _build_accessibility_text(self, section_type: SectionType, block: str) -> str:
        preview = block.strip().splitlines()[0][:120]
        return f"{section_type.value} section: {preview}"

    def _header_text(self, line: str) -> str:
        return re.sub(r"^#+\s*", "", line).strip()

    def _nav_label(self, content: str) -> str:
        line = content.strip().splitlines()[0]
        return self._header_text(line)[:80]

    def _reclassify_sections(self, sections: List[ContentSection]) -> List[ContentSection]:
        out: List[ContentSection] = []

        for idx, section in enumerate(sections):
            content = section.content.strip()

            if idx == 0 and content.startswith("#"):
                section.section_type = SectionType.TITLE
                section.priority = 100

            elif "summary" in content.lower() and len(content.split()) < 20:
                section.section_type = SectionType.SUMMARY
                section.priority = 88

            elif content.startswith("## Sources") or content.startswith("## Citations"):
                section.section_type = SectionType.CITATIONS
                section.priority = 76

            elif content.startswith("```"):
                section.section_type = SectionType.CODE
                section.priority = 80

            elif self.TABLE_RE.match(content):
                section.section_type = SectionType.TABLE
                section.priority = 70

            out.append(section)

        return out


# Backward-compatible alias for older imports.
FormattingEngine = ResponseFormattingEngine
