from __future__ import annotations

import math
import re
from urllib.parse import urlparse
from typing import Any, Dict, List

from .Enums import ComplexityLevel, ContentType, SectionType
from .Models import CitationInfo, CodeBlockInfo, ContentSection
from .RegexPatterns import (
    BULLET_RE,
    CODE_BLOCK_RE,
    HEADER_RE,
    INLINE_CODE_RE,
    MARKDOWN_LINK_RE,
    NUMBERED_RE,
    TABLE_RE,
    URL_RE,
)


class AnalysisMixin:
    def _safe_normalize_spacing(self, text: str) -> str:
        normalizer = getattr(self, "_normalize_spacing", None)
        if callable(normalizer):
            return str(normalizer(text))
        # local fallback for mixin-only static analysis paths
        text = re.sub(r"\n{3,}", "\n\n", text or "")
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    def _safe_detect_language(self, code: str) -> str:
        detector = getattr(self, "_detect_language", None)
        if callable(detector):
            return str(detector(code) or "text")
        return "text"

    async def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        content = content or ""
        normalized = self._safe_normalize_spacing(content)

        code_blocks = self._extract_code_blocks(normalized)
        citations = self._extract_citations(normalized)
        sections = self._detect_sections(normalized)
        data_structures = self._detect_data_structures(normalized)

        technical_density = self._calculate_technical_density(
            normalized,
            code_blocks,
            data_structures,
        )
        complexity = self._classify_complexity(
            len(normalized),
            technical_density,
            len(code_blocks),
            len(sections),
        )
        content_type = self._detect_content_type(
            normalized,
            code_blocks,
            citations,
            technical_density,
        )
        reading_time = self._estimate_reading_time(normalized)

        has_tables = "markdown_table" in data_structures
        has_lists = any(
            s.section_type == SectionType.LIST for s in sections
        )
        has_headers = any(
            s.section_type in {SectionType.HEADER, SectionType.TITLE}
            for s in sections
        )
        has_inline_code = bool(INLINE_CODE_RE.search(normalized))
        is_long_form = len(re.findall(r"\b\w+\b", normalized)) >= 1200

        return {
            "content_type": content_type,
            "complexity": complexity.value,
            "sections": sections,
            "code_blocks": code_blocks,
            "data_structures": data_structures,
            "length": len(normalized),
            "reading_time": reading_time,
            "technical_density": technical_density,
            "citations": citations,
            "has_tables": has_tables,
            "has_lists": has_lists,
            "has_headers": has_headers,
            "has_inline_code": has_inline_code,
            "is_long_form": is_long_form,
        }

    def _extract_code_blocks(self, content: str) -> List[CodeBlockInfo]:
        blocks: List[CodeBlockInfo] = []

        for match in CODE_BLOCK_RE.finditer(content):
            language = (match.group(1) or "").strip().lower()
            code = (match.group(2) or "").strip("\n")

            if not language:
                language = self._safe_detect_language(code)

            line_count = len(code.splitlines()) if code else 0

            blocks.append(
                CodeBlockInfo(
                    language=language or "text",
                    code=code,
                    start=match.start(),
                    end=match.end(),
                    line_count=line_count,
                    is_fenced=True,
                    highlightable=(language or "text") != "text",
                )
            )

        return blocks

    def _extract_citations(self, content: str) -> List[CitationInfo]:
        citations: List[CitationInfo] = []

        for match in MARKDOWN_LINK_RE.finditer(content):
            title = match.group(1).strip()
            url = match.group(2).strip()
            citations.append(
                CitationInfo(
                    title=title,
                    url=url,
                    domain=self._extract_domain(url),
                    source_type="web",
                )
            )

        for url in URL_RE.findall(content):
            url = url.strip()
            citations.append(
                CitationInfo(
                    title=url,
                    url=url,
                    domain=self._extract_domain(url),
                    source_type="web",
                )
            )

        deduped: List[CitationInfo] = []
        seen: set[str] = set()

        for citation in citations:
            if citation.url in seen:
                continue
            seen.add(citation.url)
            deduped.append(citation)

        return deduped

    def _detect_sections(self, content: str) -> List[ContentSection]:
        """
        Lightweight analysis-oriented section detection.

        This is intentionally simpler than the main SectionsMixin organizer.
        It provides analysis signals, not the final canonical section layout.
        """
        lines = self._safe_normalize_spacing(content).splitlines()
        sections: List[ContentSection] = []

        in_code = False
        code_buffer: List[str] = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                if not in_code:
                    in_code = True
                    code_buffer = [line]
                else:
                    code_buffer.append(line)
                    code_block = "\n".join(code_buffer)
                    sections.append(
                        ContentSection(
                            content=code_block,
                            section_type=SectionType.CODE,
                            priority=80,
                            metadata={"analysis_only": True},
                        )
                    )
                    in_code = False
                    code_buffer = []
                continue

            if in_code:
                code_buffer.append(line)
                continue

            if not stripped:
                continue

            if HEADER_RE.match(stripped):
                level = len(HEADER_RE.match(stripped).group(1))  # type: ignore[union-attr]
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.HEADER,
                        priority=90,
                        metadata={"level": level, "analysis_only": True},
                    )
                )
            elif stripped.startswith(">"):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.QUOTE,
                        priority=45,
                        metadata={"analysis_only": True},
                    )
                )
            elif BULLET_RE.match(stripped) or NUMBERED_RE.match(stripped):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.LIST,
                        priority=55,
                        metadata={"analysis_only": True},
                    )
                )
            elif TABLE_RE.match(stripped):
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.TABLE,
                        priority=70,
                        metadata={"analysis_only": True},
                    )
                )
            else:
                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=SectionType.PARAGRAPH,
                        priority=50,
                        metadata={"analysis_only": True},
                    )
                )

        if in_code and code_buffer:
            sections.append(
                ContentSection(
                    content="\n".join(code_buffer),
                    section_type=SectionType.CODE,
                    priority=80,
                    metadata={"analysis_only": True, "unterminated": True},
                )
            )

        return sections

    def _detect_data_structures(self, content: str) -> List[str]:
        structures: List[str] = []

        if "{" in content and "}" in content:
            structures.append("json_like")

        if "[" in content and "]" in content:
            structures.append("array_like")

        if TABLE_RE.search(content):
            structures.append("markdown_table")

        if BULLET_RE.search(content):
            structures.append("bullet_list")

        if NUMBERED_RE.search(content):
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
            "api",
            "endpoint",
            "schema",
            "function",
            "class",
            "method",
            "async",
            "token",
            "request",
            "response",
            "docker",
            "yaml",
            "json",
            "sql",
            "python",
            "javascript",
            "typescript",
            "regex",
            "stream",
            "orchestrator",
            "latency",
            "throughput",
            "inference",
            "embedding",
            "retrieval",
        ]

        lowered = content.lower()
        keyword_hits = sum(lowered.count(k) for k in keywords)
        keyword_score = min(keyword_hits / 20.0, 1.0)

        inline_code_score = 0.1 if INLINE_CODE_RE.search(content) else 0.0
        code_score = min(len(code_blocks) / 5.0, 1.0)
        structure_score = min(len(data_structures) / 5.0, 1.0)

        density = (
            (keyword_score * 0.45)
            + (code_score * 0.3)
            + (structure_score * 0.15)
            + inline_code_score
        )
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
        word_count = len(re.findall(r"\b\w+\b", content))

        if citations and (
            "source" in lowered
            or "according to" in lowered
            or "latest" in lowered
            or "reported by" in lowered
        ):
            return ContentType.SEARCH_SUMMARY

        if "troubleshoot" in lowered or "fix this" in lowered or "error" in lowered:
            return ContentType.TROUBLESHOOTING

        if "vs" in lowered or "comparison" in lowered or "trade-off" in lowered:
            return ContentType.COMPARISON

        if "product" in lowered or "price" in lowered or "features" in lowered:
            return ContentType.PRODUCT

        if len(code_blocks) >= 2 or technical_density > 0.7:
            return ContentType.CODE_HEAVY

        if technical_density > 0.45:
            return ContentType.TECHNICAL

        if "step 1" in lowered or "tutorial" in lowered or "how to" in lowered:
            return ContentType.TUTORIAL

        if "analysis" in lowered:
            return ContentType.ANALYSIS

        if re.search(r"\bq[:\s].+\ba[:\s]", lowered, re.DOTALL):
            return ContentType.QA

        if word_count >= 1200:
            return ContentType.ARTICLE

        return ContentType.GENERAL

    def _estimate_reading_time(self, content: str) -> int:
        plain = CODE_BLOCK_RE.sub(" ", content)
        words = re.findall(r"\b\w+\b", plain)
        return max(1, math.ceil(len(words) / 220))

    def _extract_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc.lower().removeprefix("www.")
        except Exception:
            return ""
