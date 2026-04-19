import re
from typing import List

from .RegexPatterns import BULLET_RE, CODE_BLOCK_RE, NUMBERED_RE, TABLE_RE


class NormalizationMixin:
    def _normalize_content(self, text: str) -> str:
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
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
                repaired.append(f"## {section_label_match.group(1).strip().title()}")
                continue

            if (
                stripped.isupper()
                and 1 <= len(stripped.split()) <= 8
                and not stripped.startswith("#")
            ):
                repaired.append(f"## {stripped.title()}")
                continue

            if (
                re.match(r"^[A-Z][A-Za-z0-9 /&:-]{3,60}$", stripped)
                and not stripped.startswith("#")
                and not stripped.endswith(":")
                and len(stripped.split()) <= 7
                and stripped == stripped.title()
            ):
                repaired.append(f"## {stripped}")
                continue

            repaired.append(line)

        return "\n".join(repaired)

    def _repair_lists(self, text: str) -> str:
        lines = text.splitlines()
        out: List[str] = []
        prev_was_list = False
        prev_list_indent = 0

        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            is_list = bool(BULLET_RE.match(stripped) or NUMBERED_RE.match(stripped))

            if is_list:
                if out and out[-1].strip() and not prev_was_list:
                    out.append("")

                # normalize excessive indentation for top-level lists only
                if indent == 0:
                    out.append(stripped)
                else:
                    out.append(line.rstrip())

                prev_was_list = True
                prev_list_indent = indent
                continue

            # continuation lines under a list item should stay attached
            if prev_was_list and stripped and indent > prev_list_indent:
                out.append(line.rstrip())
                continue

            out.append(line.rstrip())
            prev_was_list = False
            prev_list_indent = 0

        return "\n".join(out)

    def _repair_code_blocks(self, text: str) -> str:
        fence_count = text.count("```")
        if fence_count % 2 != 0:
            text += "\n```"

        def repl(match: re.Match[str]) -> str:
            language = (match.group(1) or "").strip().lower()
            body = (match.group(2) or "").strip("\n")

            if not language and body:
                detector = getattr(self, "_detect_language", None)
                if callable(detector):
                    language = str(detector(body) or "text")
                else:
                    language = "text"

            if not language:
                language = "text"

            return f"```{language}\n{body}\n```"

        return CODE_BLOCK_RE.sub(repl, text)

    def _normalize_tables(self, text: str) -> str:
        lines = text.splitlines()
        out: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not self._looks_like_table_line(stripped):
                out.append(line.rstrip())
                i += 1
                continue

            table_block: List[str] = []
            j = i
            while j < len(lines):
                candidate = lines[j].strip()
                if not candidate or not self._looks_like_table_line(candidate):
                    break
                table_block.append(lines[j])
                j += 1

            if len(table_block) < 2:
                out.append(line.rstrip())
                i += 1
                continue

            normalized_rows: List[str] = []
            parsed_rows: List[List[str]] = []

            for row in table_block:
                row_stripped = row.strip()

                if not row_stripped.startswith("|"):
                    row_stripped = "| " + row_stripped
                if not row_stripped.endswith("|"):
                    row_stripped = row_stripped + " |"

                cells = [c.strip() for c in row_stripped.strip("|").split("|")]
                parsed_rows.append(cells)

            max_cols = max(len(row) for row in parsed_rows) if parsed_rows else 0
            if max_cols == 0:
                out.extend(r.rstrip() for r in table_block)
                i = j
                continue

            for idx, cells in enumerate(parsed_rows):
                padded = cells + ([""] * (max_cols - len(cells)))
                normalized_rows.append("| " + " | ".join(padded) + " |")

            if len(normalized_rows) >= 2 and not self._is_separator_row(
                normalized_rows[1]
            ):
                normalized_rows.insert(1, "| " + " | ".join(["---"] * max_cols) + " |")
            elif len(normalized_rows) >= 2 and self._is_separator_row(
                normalized_rows[1]
            ):
                normalized_rows[1] = "| " + " | ".join(["---"] * max_cols) + " |"

            out.extend(normalized_rows)
            i = j

        return "\n".join(out)

    def _looks_like_table_line(self, stripped: str) -> bool:
        return bool(stripped and "|" in stripped and TABLE_RE.match(stripped))

    def _is_separator_row(self, row: str) -> bool:
        candidate = row.strip().strip("|")
        if not candidate:
            return False

        cells = [c.strip() for c in candidate.split("|")]
        if not cells:
            return False

        return all(re.match(r"^:?-{2,}:?$", cell) for cell in cells)
