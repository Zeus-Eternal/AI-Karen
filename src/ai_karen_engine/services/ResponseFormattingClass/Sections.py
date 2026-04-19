from __future__ import annotations

import re
from typing import List, Optional

from .Enums import SectionType
from .Models import ContentSection
from .RegexPatterns import BULLET_RE, HEADER_RE, NUMBERED_RE, TABLE_RE


class SectionsMixin:
    def _safe_normalize_spacing(self, text: str) -> str:
        normalizer = getattr(self, "_normalize_spacing", None)
        if callable(normalizer):
            return str(normalizer(text))
        text = re.sub(r"\n{3,}", "\n\n", text or "")
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    async def organize_content_hierarchically(
        self, content: str
    ) -> List[ContentSection]:
        sections: List[ContentSection] = []
        text = self._safe_normalize_spacing(content)
        lines = text.splitlines()

        paragraph_buffer: List[str] = []
        nav_counter = 0

        i = 0
        total = len(lines)

        def flush_paragraph_buffer(
            section_type: SectionType = SectionType.PARAGRAPH,
        ) -> None:
            nonlocal paragraph_buffer, nav_counter

            block = "\n".join(paragraph_buffer).strip()
            if not block:
                paragraph_buffer = []
                return

            metadata = {}
            navigation_id = None

            if section_type in {
                SectionType.HEADER,
                SectionType.SUMMARY,
                SectionType.CITATIONS,
                SectionType.TITLE,
            }:
                nav_counter += 1
                slug = self._make_slug(block)
                navigation_id = slug or f"section-{nav_counter}"
                metadata["slug"] = navigation_id

            sections.append(
                ContentSection(
                    content=block,
                    section_type=section_type,
                    priority=self._section_priority(section_type, block),
                    metadata=metadata,
                    navigation_id=navigation_id,
                    accessibility_text=self._build_accessibility_text(
                        section_type, block, metadata
                    ),
                )
            )
            paragraph_buffer = []

        while i < total:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                flush_paragraph_buffer()
                i += 1
                continue

            # Fenced code block
            if stripped.startswith("```"):
                flush_paragraph_buffer()

                code_lines = [line]
                opening_fence = stripped
                language_hint = self._extract_code_language_hint(opening_fence)

                i += 1
                while i < total:
                    code_lines.append(lines[i])
                    if lines[i].strip().startswith("```"):
                        break
                    i += 1

                code_block = "\n".join(code_lines).strip()
                detected_language = (
                    language_hint or self._detect_language_from_fence_block(code_block)
                )
                line_count = (
                    max(0, len(code_lines) - 2)
                    if len(code_lines) >= 2
                    else len(code_lines)
                )

                sections.append(
                    ContentSection(
                        content=code_block,
                        section_type=SectionType.CODE,
                        priority=80,
                        metadata={
                            "language": detected_language,
                            "line_count": line_count,
                            "is_fenced": True,
                            "highlightable": detected_language != "text",
                            "starts_with_language_hint": bool(language_hint),
                        },
                        accessibility_text=self._build_accessibility_text(
                            SectionType.CODE,
                            code_block,
                            {
                                "language": detected_language,
                                "line_count": line_count,
                            },
                        ),
                    )
                )

                i += 1
                continue

            # Header
            header_match = HEADER_RE.match(stripped)
            if header_match:
                flush_paragraph_buffer()

                hashes, header_text = header_match.groups()
                level = len(hashes)
                slug = self._make_slug(header_text)

                nav_counter += 1
                navigation_id = slug or f"section-{nav_counter}"

                section_type = (
                    SectionType.TITLE
                    if not sections and level == 1
                    else SectionType.HEADER
                )

                sections.append(
                    ContentSection(
                        content=stripped,
                        section_type=section_type,
                        priority=100 if section_type == SectionType.TITLE else 95,
                        metadata={
                            "level": level,
                            "slug": navigation_id,
                            "text": header_text.strip(),
                        },
                        navigation_id=navigation_id,
                        accessibility_text=self._build_accessibility_text(
                            section_type,
                            stripped,
                            {"level": level, "text": header_text.strip()},
                        ),
                    )
                )
                i += 1
                continue

            # Block quote
            if stripped.startswith(">"):
                flush_paragraph_buffer()

                quote_lines = [line]
                i += 1
                while i < total and lines[i].strip().startswith(">"):
                    quote_lines.append(lines[i])
                    i += 1

                quote_block = "\n".join(quote_lines).strip()
                sections.append(
                    ContentSection(
                        content=quote_block,
                        section_type=SectionType.QUOTE,
                        priority=55,
                        metadata={"line_count": len(quote_lines)},
                        accessibility_text=self._build_accessibility_text(
                            SectionType.QUOTE,
                            quote_block,
                            {"line_count": len(quote_lines)},
                        ),
                    )
                )
                continue

            # Table block
            if self._looks_like_table_line(stripped):
                flush_paragraph_buffer()

                table_lines = [line]
                i += 1
                while i < total and self._looks_like_table_line(lines[i].strip()):
                    table_lines.append(lines[i])
                    i += 1

                table_block = "\n".join(table_lines).strip()
                column_count = self._estimate_table_columns(table_lines)

                sections.append(
                    ContentSection(
                        content=table_block,
                        section_type=SectionType.TABLE,
                        priority=70,
                        metadata={
                            "row_count": len(table_lines),
                            "column_count_estimate": column_count,
                        },
                        accessibility_text=self._build_accessibility_text(
                            SectionType.TABLE,
                            table_block,
                            {
                                "row_count": len(table_lines),
                                "column_count_estimate": column_count,
                            },
                        ),
                    )
                )
                continue

            # List block
            if BULLET_RE.match(stripped) or NUMBERED_RE.match(stripped):
                flush_paragraph_buffer()

                list_lines = [line]
                list_kind = "numbered" if NUMBERED_RE.match(stripped) else "bullet"

                i += 1
                while i < total:
                    next_stripped = lines[i].strip()
                    if not next_stripped:
                        break
                    if list_kind == "bullet" and BULLET_RE.match(next_stripped):
                        list_lines.append(lines[i])
                        i += 1
                        continue
                    if list_kind == "numbered" and NUMBERED_RE.match(next_stripped):
                        list_lines.append(lines[i])
                        i += 1
                        continue
                    break

                list_block = "\n".join(list_lines).strip()

                sections.append(
                    ContentSection(
                        content=list_block,
                        section_type=SectionType.LIST,
                        priority=60,
                        metadata={
                            "list_kind": list_kind,
                            "item_count": len(list_lines),
                        },
                        accessibility_text=self._build_accessibility_text(
                            SectionType.LIST,
                            list_block,
                            {
                                "list_kind": list_kind,
                                "item_count": len(list_lines),
                            },
                        ),
                    )
                )
                continue

            paragraph_buffer.append(line)
            i += 1

        flush_paragraph_buffer()

        if not sections and text:
            sections.append(
                ContentSection(
                    content=text,
                    section_type=SectionType.PARAGRAPH,
                    priority=50,
                    accessibility_text="Main content paragraph",
                )
            )

        return self._reclassify_sections(sections)

    def _reclassify_sections(
        self, sections: List[ContentSection]
    ) -> List[ContentSection]:
        out: List[ContentSection] = []

        for idx, section in enumerate(sections):
            content = section.content.strip()

            if idx == 0 and (
                content.startswith("#") or self._looks_like_title_block(content)
            ):
                section.section_type = SectionType.TITLE
                section.priority = 100
                if "slug" not in section.metadata:
                    section.metadata["slug"] = self._make_slug(
                        self._header_text(content) or content
                    )

            elif self._is_summary_section(content):
                section.section_type = SectionType.SUMMARY
                section.priority = 88

            elif content.startswith("## Sources") or content.startswith("## Citations"):
                section.section_type = SectionType.CITATIONS
                section.priority = 76
                section.metadata["source_count_estimate"] = (
                    self._estimate_sources_count(content)
                )

            elif content.startswith("```"):
                section.section_type = SectionType.CODE
                section.priority = 80

            elif self._looks_like_table_block(content):
                section.section_type = SectionType.TABLE
                section.priority = 70

            out.append(section)

        return out

    def _section_priority(self, section_type: SectionType, block: str) -> int:
        if section_type == SectionType.TITLE:
            return 100
        if section_type == SectionType.HEADER:
            return 95
        if section_type == SectionType.SUMMARY:
            return 90
        if section_type == SectionType.CODE:
            return 80
        if section_type == SectionType.CITATIONS:
            return 75
        if section_type == SectionType.TABLE:
            return 70
        if section_type == SectionType.LIST:
            return 60
        if section_type == SectionType.QUOTE:
            return 55
        return 50

    def _build_accessibility_text(
        self,
        section_type: SectionType,
        block: str,
        metadata: Optional[dict] = None,
    ) -> str:
        metadata = metadata or {}
        preview = block.strip().splitlines()[0][:120] if block.strip() else ""

        if section_type == SectionType.TITLE:
            return f"Title: {self._header_text(preview) or preview}"

        if section_type == SectionType.HEADER:
            return f"Heading: {self._header_text(preview) or preview}"

        if section_type == SectionType.CODE:
            language = metadata.get("language", "text")
            line_count = metadata.get("line_count", 0)
            return f"Code block in {language}, {line_count} lines"

        if section_type == SectionType.LIST:
            list_kind = metadata.get("list_kind", "list")
            item_count = metadata.get("item_count", 0)
            return f"{list_kind.title()} list with {item_count} items"

        if section_type == SectionType.TABLE:
            row_count = metadata.get("row_count", 0)
            column_count = metadata.get("column_count_estimate", 0)
            return (
                f"Table with approximately {column_count} columns and {row_count} rows"
            )

        if section_type == SectionType.CITATIONS:
            source_count = metadata.get("source_count_estimate", 0)
            if source_count:
                return f"Sources section with {source_count} citations"
            return "Sources section"

        if section_type == SectionType.QUOTE:
            line_count = metadata.get("line_count", 1)
            return f"Quoted block spanning {line_count} lines"

        return f"{section_type.value} section: {preview}"

    def _header_text(self, line: str) -> str:
        return re.sub(r"^#+\s*", "", line).strip()

    def _nav_label(self, content: str) -> str:
        if not content.strip():
            return "Section"

        first_line = content.strip().splitlines()[0]
        cleaned = self._header_text(first_line)
        cleaned = re.sub(r"^```[\w+-]*$", "", cleaned).strip()

        if not cleaned:
            return "Code Section" if content.strip().startswith("```") else "Section"

        return cleaned[:80]

    def _make_slug(self, text: str) -> str:
        value = self._header_text(text).lower().strip()
        value = re.sub(r"[^\w\s-]", "", value)
        value = re.sub(r"[\s_-]+", "-", value).strip("-")
        return value or "section"

    def _looks_like_table_line(self, stripped: str) -> bool:
        return bool(stripped and "|" in stripped and TABLE_RE.match(stripped))

    def _looks_like_table_block(self, content: str) -> bool:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        return sum(1 for line in lines if self._looks_like_table_line(line)) >= 2

    def _estimate_table_columns(self, table_lines: List[str]) -> int:
        counts = []
        for line in table_lines:
            stripped = line.strip().strip("|")
            if not stripped:
                continue
            counts.append(len([cell for cell in stripped.split("|")]))
        return max(counts) if counts else 0

    def _extract_code_language_hint(self, fence_line: str) -> str:
        stripped = fence_line.strip()
        if not stripped.startswith("```"):
            return ""
        hint = stripped[3:].strip().lower()
        return hint

    def _detect_language_from_fence_block(self, code_block: str) -> str:
        lines = code_block.splitlines()
        if len(lines) <= 2:
            return "text"
        body = "\n".join(lines[1:-1]).strip()
        if not body:
            return "text"
        detector = getattr(self, "_detect_language", None)
        if callable(detector):
            return str(detector(body) or "text")
        return "text"

    def _looks_like_title_block(self, content: str) -> bool:
        stripped = content.strip()
        if not stripped or "\n" in stripped:
            return False
        if len(stripped.split()) > 12:
            return False
        if stripped.endswith("."):
            return False
        return stripped == stripped.title() or stripped.isupper()

    def _is_summary_section(self, content: str) -> bool:
        stripped = content.strip().lower()
        first_line = stripped.splitlines()[0] if stripped else ""

        return first_line in {
            "summary",
            "## summary",
            "# summary",
            "key takeaways",
            "## key takeaways",
            "tl;dr",
            "## tl;dr",
        }

    def _estimate_sources_count(self, content: str) -> int:
        return sum(
            1
            for line in content.splitlines()
            if line.strip().startswith("- ") or line.strip().startswith("* ")
        )
