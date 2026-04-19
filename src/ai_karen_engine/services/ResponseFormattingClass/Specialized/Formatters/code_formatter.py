"""
Code Response Formatter.
Migrated from extension system to core services.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Set

from ..Base import SpecializedFormatter, ResponseContext
from ...Models import FormattedResponse
from ...Enums import ContentType, FormatType

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Data structure for code block information."""
    language: str
    code: str
    block_type: str = "fenced"


class CodeResponseFormatter(SpecializedFormatter):
    """
    Formatter for code-related responses.
    Preserves markdown rendering while enriching metadata with extracted code structure.
    """

    FENCED_BLOCK_PATTERN = re.compile(
        r"```(?P<language>[a-zA-Z0-9_+\-#.]*)[ \t]*\n(?P<code>.*?)\n```",
        re.DOTALL,
    )
    INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
    INDENTED_BLOCK_PATTERN = re.compile(
        r"(?:(?:^|\n)(?: {4}|\t).+(?:\n(?: {4}|\t).+)*)",
        re.MULTILINE,
    )

    def __init__(self):
        super().__init__("code", "2.0.0")

        self._code_keywords = {
            "code",
            "function",
            "variable",
            "class",
            "method",
            "algorithm",
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "sql",
            "json",
            "api",
            "script",
            "import",
            "return",
            "def",
            "const",
            "let",
        }

        self._language_signatures = [
            ("python", [r"\bdef\s+\w+\(", r"\bimport\s+\w+", r"\bclass\s+\w+", r":\s*$"]),
            ("javascript", [r"\bfunction\s+\w+\(", r"\bconst\s+\w+\s*=", r"\blet\s+\w+\s*=", r"=>"]),
            ("typescript", [r"\binterface\s+\w+", r"\btype\s+\w+\s*=", r":\s*(string|number|boolean|unknown|any)"]),
            ("java", [r"\bpublic\s+class\s+\w+", r"\bpublic\s+static\s+void\s+main", r"\bSystem\.out\.println"]),
            ("sql", [r"\bSELECT\b", r"\bFROM\b", r"\bWHERE\b", r"\bINSERT\b|\bUPDATE\b|\bDELETE\b"]),
            ("json", [r"^\s*\{", r'"\w+"\s*:']),
            ("html", [r"<html", r"<div", r"<body", r"</\w+>"]),
            ("css", [r"[.#]?\w+\s*\{", r"\bcolor\s*:", r"\bdisplay\s*:"]),
            ("bash", [r"^\s*#!/bin/(bash|sh)", r"\becho\b", r"\bchmod\b", r"\bgrep\b"]),
            ("yaml", [r"^\s*\w+:\s*$", r"^\s*-\s+\w+", r"^\s*\w+:\s+\S+"]),
        ]

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.CODE:
            return True

        if self.FENCED_BLOCK_PATTERN.search(content):
            return True

        if self.INDENTED_BLOCK_PATTERN.search(content):
            return True

        inline_matches = self.INLINE_CODE_PATTERN.findall(content)
        if len(inline_matches) >= 2:
            return True

        content_lower = content.lower()
        keyword_count = sum(1 for kw in self._code_keywords if kw in content_lower)

        syntax_signals = [
            r"\bdef\s+\w+\(",
            r"\bclass\s+\w+",
            r"\bfunction\s+\w+\(",
            r"\breturn\b",
            r"\bimport\s+\w+",
            r"\bSELECT\b.*\bFROM\b",
            r"\{.*\}",
        ]
        syntax_hits = sum(
            1 for pattern in syntax_signals
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        )

        return keyword_count >= 3 or syntax_hits >= 2

    async def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        code_blocks = self._extract_code_blocks(content)
        inline_code = self._extract_inline_code(content)

        detected_languages: List[str] = sorted({
            block.language for block in code_blocks
            if block.language and block.language != "text"
        })

        has_fenced_blocks = any(block.block_type == "fenced" for block in code_blocks)
        has_indented_blocks = any(block.block_type == "indented" for block in code_blocks)

        return FormattedResponse(
            content=content,
            format_type=FormatType.STANDARD_MARKDOWN,
            metadata={
                "formatter": self.name,
                "code_blocks_count": len(code_blocks),
                "inline_code_count": len(inline_code),
                "detected_languages": detected_languages,
                "has_fenced_blocks": has_fenced_blocks,
                "has_indented_blocks": has_indented_blocks,
                "primary_language": detected_languages[0] if detected_languages else None,
            },
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "code_blocks", "syntax_highlighting"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.CODE]

    def _extract_code_blocks(self, content: str) -> List[CodeBlock]:
        code_blocks: List[CodeBlock] = []
        occupied_ranges: List[tuple[int, int]] = []

        for match in self.FENCED_BLOCK_PATTERN.finditer(content):
            raw_language = (match.group("language") or "").strip().lower()
            code = match.group("code").strip()
            if not code:
                continue

            language = raw_language or self._infer_language(code)
            code_blocks.append(
                CodeBlock(
                    language=language,
                    code=code,
                    block_type="fenced",
                )
            )
            occupied_ranges.append(match.span())

        for match in self.INDENTED_BLOCK_PATTERN.finditer(content):
            start, end = match.span()
            if self._overlaps_existing_range(start, end, occupied_ranges):
                continue

            raw_block = match.group(0)
            code = self._normalize_indented_block(raw_block)
            if not code or len(code.splitlines()) < 2:
                continue

            language = self._infer_language(code)
            code_blocks.append(
                CodeBlock(
                    language=language,
                    code=code,
                    block_type="indented",
                )
            )

        return code_blocks

    def _extract_inline_code(self, content: str) -> List[str]:
        values: List[str] = []
        for match in self.INLINE_CODE_PATTERN.finditer(content):
            code = match.group(1).strip()
            if code:
                values.append(code)
        return values

    def _infer_language(self, code: str) -> str:
        normalized = code.strip()
        if not normalized:
            return "text"

        scores: dict[str, int] = {}

        for language, patterns in self._language_signatures:
            score = 0
            for pattern in patterns:
                if re.search(pattern, normalized, re.IGNORECASE | re.MULTILINE):
                    score += 1
            if score > 0:
                scores[language] = score

        if scores:
            best_language = max(scores.items(), key=lambda item: item[1])[0]
            return best_language

        return "text"

    def _normalize_indented_block(self, block: str) -> str:
        lines = block.splitlines()
        normalized_lines: List[str] = []

        for line in lines:
            if line.startswith("    "):
                normalized_lines.append(line[4:])
            elif line.startswith("\t"):
                normalized_lines.append(line[1:])
            else:
                normalized_lines.append(line)

        return "\n".join(normalized_lines).strip()

    def _overlaps_existing_range(
        self,
        start: int,
        end: int,
        ranges: List[tuple[int, int]],
    ) -> bool:
        for existing_start, existing_end in ranges:
            if start < existing_end and end > existing_start:
                return True
        return False