import html
import re
from typing import Callable, Dict, Set


class SyntaxHighlightingMixin:
    """
    Lightweight HTML-safe syntax highlighting mixin.

    Design goals:
    - never return unsafe raw code
    - keep behavior deterministic
    - avoid heavy third-party dependencies
    - support graceful fallback for unknown languages
    """

    LANGUAGE_ALIASES: Dict[str, str] = {
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

    def _get_syntax_highlighters(self) -> Dict[str, Callable[[str], str]]:
        return {
            "python": self._highlight_python,
            "javascript": self._highlight_javascript,
            "typescript": self._highlight_typescript,
            "json": self._highlight_json,
            "yaml": self._highlight_yaml,
            "bash": self._highlight_bash,
            "sql": self._highlight_sql,
            "html": self._highlight_html,
            "css": self._highlight_css,
            "markdown": self._highlight_markdown,
            "text": self._highlight_plain_text,
        }

    async def apply_syntax_highlighting(self, code: str, language: str = "text") -> str:
        lang = self._normalize_language(language)
        highlighters = self._get_syntax_highlighters()

        if lang not in highlighters:
            return self._wrap_code_block(html.escape(code), lang)

        highlighted_body = highlighters[lang](code)
        return self._wrap_code_block(highlighted_body, lang)

    def _normalize_language(self, language: str) -> str:
        lang = (language or "text").lower().strip()
        return self.LANGUAGE_ALIASES.get(lang, lang)

    def _wrap_code_block(self, body: str, language: str) -> str:
        safe_lang = html.escape(language)
        return f'<pre><code class="language-{safe_lang}">{body}</code></pre>'

    def _highlight_plain_text(self, code: str) -> str:
        return html.escape(code)

    def _highlight_python(self, code: str) -> str:
        keywords = {
            "def", "class", "return", "if", "elif", "else", "for", "while",
            "import", "from", "try", "except", "finally", "async", "await",
            "with", "pass", "raise", "yield", "lambda", "True", "False", "None",
            "match", "case", "as", "is", "in", "not", "and", "or",
        }
        return self._simple_keyword_highlight(
            code=code,
            keywords=keywords,
            comment_patterns=[r"(^\s*#.*$)"],
        )

    def _highlight_javascript(self, code: str) -> str:
        keywords = {
            "function", "return", "if", "else", "for", "while", "const", "let",
            "var", "import", "from", "export", "async", "await", "class", "new",
            "true", "false", "null", "undefined", "try", "catch", "finally",
            "switch", "case", "break", "continue", "default",
        }
        return self._simple_keyword_highlight(
            code=code,
            keywords=keywords,
            comment_patterns=[r"(^\s*//.*$)"],
        )

    def _highlight_typescript(self, code: str) -> str:
        keywords = {
            "function", "return", "if", "else", "for", "while", "const", "let",
            "var", "import", "from", "export", "async", "await", "class", "new",
            "true", "false", "null", "undefined", "try", "catch", "finally",
            "interface", "type", "extends", "implements", "public", "private",
            "protected", "readonly", "enum", "as",
        }
        return self._simple_keyword_highlight(
            code=code,
            keywords=keywords,
            comment_patterns=[r"(^\s*//.*$)"],
        )

    def _highlight_json(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(
            r'(&quot;[^&]+&quot;)(\s*:)',
            r'<span class="json-key">\1</span>\2',
            escaped,
        )
        escaped = re.sub(
            r'(:\s*)(&quot;.*?&quot;)',
            r'\1<span class="str">\2</span>',
            escaped,
        )
        escaped = re.sub(
            r'(:\s*)(\b-?\d+(?:\.\d+)?\b)',
            r'\1<span class="num">\2</span>',
            escaped,
        )
        escaped = re.sub(
            r'(:\s*)(\btrue\b|\bfalse\b|\bnull\b)',
            r'\1<span class="kw">\2</span>',
            escaped,
            flags=re.IGNORECASE,
        )
        return escaped

    def _highlight_yaml(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(
            r"^(\s*[\w\-\.]+:)",
            r'<span class="yaml-key">\1</span>',
            escaped,
            flags=re.MULTILINE,
        )
        escaped = re.sub(
            r'(:\s*)(&quot;.*?&quot;)',
            r'\1<span class="str">\2</span>',
            escaped,
        )
        escaped = re.sub(
            r'(:\s*)(\b-?\d+(?:\.\d+)?\b)',
            r'\1<span class="num">\2</span>',
            escaped,
        )
        escaped = re.sub(
            r'(:\s*)(\btrue\b|\bfalse\b|\bnull\b)',
            r'\1<span class="kw">\2</span>',
            escaped,
            flags=re.IGNORECASE,
        )
        return escaped

    def _highlight_bash(self, code: str) -> str:
        keywords = {
            "echo", "export", "if", "then", "fi", "for", "do", "done",
            "case", "esac", "while", "in", "function", "local", "readonly",
        }
        return self._simple_keyword_highlight(
            code=code,
            keywords=keywords,
            comment_patterns=[r"(^\s*#.*$)"],
        )

    def _highlight_sql(self, code: str) -> str:
        keywords = {
            "select", "from", "where", "join", "left", "right", "inner", "outer",
            "group", "by", "order", "insert", "update", "delete", "create", "table",
            "into", "values", "limit", "having", "as", "and", "or", "on",
            "union", "distinct", "alter", "drop", "index",
        }
        return self._simple_keyword_highlight(
            code=code,
            keywords=keywords,
            case_insensitive=True,
            comment_patterns=[r"(^\s*--.*$)"],
        )

    def _highlight_html(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(
            r"(&lt;/?)([\w:-]+)",
            r'\1<span class="kw">\2</span>',
            escaped,
        )
        escaped = re.sub(
            r'([\w:-]+)=(&quot;.*?&quot;)',
            r'<span class="html-attr">\1</span>=<span class="str">\2</span>',
            escaped,
        )
        return escaped

    def _highlight_css(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(
            r"(^\s*[\.\#]?[a-zA-Z][\w\-\s\.\#,:>*\[\]=\"']*\s*\{)",
            r'<span class="kw">\1</span>',
            escaped,
            flags=re.MULTILINE,
        )
        escaped = re.sub(
            r"(^\s*[\w-]+)(\s*:)",
            r'<span class="css-prop">\1</span>\2',
            escaped,
            flags=re.MULTILINE,
        )
        return escaped

    def _highlight_markdown(self, code: str) -> str:
        escaped = html.escape(code)
        escaped = re.sub(
            r"^(#{1,6}\s+.*)$",
            r'<span class="kw">\1</span>',
            escaped,
            flags=re.MULTILINE,
        )
        escaped = re.sub(
            r"(`[^`\n]+`)",
            r'<span class="str">\1</span>',
            escaped,
        )
        escaped = re.sub(
            r"(\[[^\]]+\]\([^)]+\))",
            r'<span class="link">\1</span>',
            escaped,
        )
        return escaped

    def _simple_keyword_highlight(
        self,
        code: str,
        keywords: Set[str],
        case_insensitive: bool = False,
        comment_patterns: list[str] | None = None,
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

        escaped = re.sub(
            r"(&quot;.*?&quot;)",
            r'<span class="str">\1</span>',
            escaped,
        )

        escaped = re.sub(
            r"\b(-?\d+(?:\.\d+)?)\b",
            r'<span class="num">\1</span>',
            escaped,
        )

        for pattern in comment_patterns or []:
            escaped = re.sub(
                pattern,
                r'<span class="comment">\1</span>',
                escaped,
                flags=re.MULTILINE,
            )

        return escaped