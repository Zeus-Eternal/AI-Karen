import re


class CodeFormattingMixin:
    def _detect_language(self, code: str) -> str:
        code = (code or "").strip()
        lowered = code.lower()

        if not code:
            return "text"

        # Python
        if (
            re.search(r"^\s*from\s+\w+(\.\w+)*\s+import\s+", code, re.MULTILINE)
            or re.search(r"^\s*import\s+\w+(\.\w+)*", code, re.MULTILINE)
            or re.search(r"^\s*def\s+\w+\s*\(", code, re.MULTILINE)
            or re.search(r"^\s*class\s+\w+\s*(\(|:)", code, re.MULTILINE)
        ):
            return "python"

        # TypeScript
        if (
            re.search(r"^\s*interface\s+\w+", code, re.MULTILINE)
            or re.search(r"^\s*type\s+\w+\s*=", code, re.MULTILINE)
            or re.search(r"^\s*enum\s+\w+", code, re.MULTILINE)
            or re.search(r":\s*(string|number|boolean|unknown|any|void)\b", code)
            or "implements " in lowered
        ):
            return "typescript"

        # JavaScript
        if (
            "console.log(" in code
            or "function " in code
            or "=>" in code
            or re.search(r"\b(const|let|var)\s+\w+\s*=", code)
            or re.search(r"^\s*export\s+(default\s+)?(function|class|const|let|var)", code, re.MULTILINE)
        ):
            return "javascript"

        # JSON
        if (
            lowered.startswith("{")
            and lowered.endswith("}")
            and '"' in code
        ):
            return "json"

        # YAML
        if (
            re.search(r"^\s*[\w\-\.]+:\s*.+$", code, re.MULTILINE)
            or re.search(r"^\s*-\s+[\w\-\.]+:\s*.+$", code, re.MULTILINE)
        ) and "{" not in code and "}" not in code:
            return "yaml"

        # SQL
        if re.search(
            r"^\s*(select|insert|update|delete|create|alter|drop)\b",
            lowered,
            re.MULTILINE,
        ):
            return "sql"

        # Bash / shell
        if (
            lowered.startswith("#!/bin/bash")
            or lowered.startswith("#!/usr/bin/env bash")
            or lowered.startswith("#!/bin/sh")
            or re.search(r"^\s*(export|echo|if\s+\[|for\s+\w+\s+in|while\s+\[)", lowered, re.MULTILINE)
        ):
            return "bash"

        # HTML
        if (
            "<html" in lowered
            or re.search(r"</[a-zA-Z][\w:-]*>", code)
            or re.search(r"<[a-zA-Z][\w:-]*(\s+[^>]*)?>", code)
        ):
            return "html"

        # CSS
        if (
            re.search(r"^[\.\#]?[a-zA-Z][\w\-\s\.\#,:>*\[\]=\"']*\s*\{", code, re.MULTILINE)
            and re.search(r"^\s*[\w-]+\s*:\s*[^;]+;?", code, re.MULTILINE)
        ):
            return "css"

        # Markdown
        if (
            re.search(r"^(#{1,6})\s+.+$", code, re.MULTILINE)
            or re.search(r"\[([^\]]+)\]\(([^)]+)\)", code)
            or re.search(r"^\s*[-*]\s+.+$", code, re.MULTILINE)
        ):
            return "markdown"

        return "text"