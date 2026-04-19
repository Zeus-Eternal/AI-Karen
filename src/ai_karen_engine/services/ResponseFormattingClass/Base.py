class FormatterBase:
    """
    Shared base configuration for the response formatting subsystem.

    Responsibilities:
    - declare supported code languages
    - declare normalized language aliases
    - expose syntax highlighter registry
    - provide lightweight capability helpers
    """

    LANGUAGE_ALIASES = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "ts": "typescript",
        "shell": "bash",
        "zsh": "bash",
        "sh": "bash",
        "yml": "yaml",
        "md": "markdown",
        "htm": "html",
    }

    def __init__(self) -> None:
        self.code_languages = {
            "python",
            "javascript",
            "typescript",
            "bash",
            "json",
            "yaml",
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
            "python": self._resolve_highlighter("_highlight_python"),
            "javascript": self._resolve_highlighter("_highlight_javascript"),
            "typescript": self._resolve_highlighter("_highlight_typescript"),
            "json": self._resolve_highlighter("_highlight_json"),
            "yaml": self._resolve_highlighter("_highlight_yaml"),
            "bash": self._resolve_highlighter("_highlight_bash"),
            "sql": self._resolve_highlighter("_highlight_sql"),
            "html": self._resolve_highlighter("_highlight_html"),
            "css": self._resolve_highlighter("_highlight_css"),
            "markdown": self._resolve_highlighter("_highlight_markdown"),
            "text": self._resolve_highlighter("_highlight_plain_text"),
        }

    def _resolve_highlighter(self, name: str):
        candidate = getattr(self, name, None)
        if callable(candidate):
            return candidate
        return self._fallback_highlighter

    @staticmethod
    def _fallback_highlighter(code: str) -> str:
        return code

    def _normalize_language_name(self, language: str) -> str:
        lang = (language or "text").strip().lower()
        return self.LANGUAGE_ALIASES.get(lang, lang)

    def _is_supported_language(self, language: str) -> bool:
        return self._normalize_language_name(language) in self.code_languages

    def _get_highlighter(self, language: str):
        normalized = self._normalize_language_name(language)
        return self.syntax_highlighters.get(normalized)

    def _get_supported_languages(self) -> list[str]:
        return sorted(self.code_languages)
