import re

from .Enums import DisplayContext, FormatType
from .Models import FormattingContext


class DisplayTransformsMixin:
    def _apply_display_transform(self, text: str, format_type: FormatType, context: FormattingContext) -> str:
        if format_type == FormatType.TERMINAL_PLAIN:
            return self._to_terminal_plain(text)

        if format_type == FormatType.MOBILE_COMPACT:
            return self._to_mobile_compact(text)

        if format_type == FormatType.PRINT_FRIENDLY:
            return self._to_print_friendly(text)

        if format_type == FormatType.API_STRUCTURED:
            return text.strip()

        if (
            context.display_context == DisplayContext.MOBILE
            and getattr(context, "prefer_compact_output", False)
        ):
            return self._to_mobile_compact(text)

        return text

    def _to_terminal_plain(self, text: str) -> str:
        # Convert markdown links to readable terminal form.
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

        # Remove fenced code markers but preserve code content.
        text = re.sub(r"```[\w+-]*\n?", "", text)
        text = text.replace("```", "")

        # Strip lightweight HTML comments.
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Normalize excess blank space.
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _to_mobile_compact(self, text: str) -> str:
        lines = text.splitlines()
        out = []
        blank_streak = 0

        for line in lines:
            stripped = line.strip()

            # collapse repeated blank lines
            if not stripped:
                blank_streak += 1
                if blank_streak <= 1:
                    out.append("")
                continue

            blank_streak = 0

            # trim trailing whitespace but preserve indentation
            cleaned = line.rstrip()

            # compact excessive spacing after headers
            if cleaned.lstrip().startswith("#"):
                if out and out[-1] != "":
                    out.append("")
                out.append(cleaned)
                continue

            out.append(cleaned)

        compacted = "\n".join(out).strip()
        compacted = re.sub(r"\n{3,}", "\n\n", compacted)
        return compacted

    def _to_print_friendly(self, text: str) -> str:
        # Strip HTML comments used for accessibility metadata.
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Normalize markdown links into readable print-friendly form.
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

        # Keep code fences, but normalize excess blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()