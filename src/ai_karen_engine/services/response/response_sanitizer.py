from __future__ import annotations

import re


class ResponseSanitizer:
    LEAK_LINE_PATTERNS = [
        re.compile(r"^\s*\[transformers:[^\]]+\]\s*", re.IGNORECASE),
        re.compile(r"^\s*you are karen\b.*", re.IGNORECASE),
        re.compile(r"^\s*you are .*assistant\b.*", re.IGNORECASE),
        re.compile(r"^\s*answer only\b.*", re.IGNORECASE),
        re.compile(r"^\s*be brief\b.*", re.IGNORECASE),
        re.compile(r"^\s*be concise\b.*", re.IGNORECASE),
        re.compile(r"^\s*do not\b.*", re.IGNORECASE),
        re.compile(r"^\s*greet only\b.*", re.IGNORECASE),
        re.compile(r"^\s*first turn:\b.*", re.IGNORECASE),
        re.compile(r"^\s*system\s*:\s*.*", re.IGNORECASE),
        re.compile(r"^\s*instructions?\s*:\s*.*", re.IGNORECASE),
        re.compile(r"^\s*assistant\s*:\s*$", re.IGNORECASE),
        re.compile(r"^\s*user's latest message\s*:\s*.*", re.IGNORECASE),
        re.compile(r"^\s*tool results\s*:\s*$", re.IGNORECASE),
    ]
    BLOCK_PATTERNS = [
        re.compile(r"<system>.*?</system>", re.IGNORECASE | re.DOTALL),
        re.compile(r"<user>\s*User's latest message\s*:?,?", re.IGNORECASE),
        re.compile(r"<assistant>\s*", re.IGNORECASE),
    ]

    def sanitize(self, text: str, *, fallback: str = "I'm here to help.") -> str:
        if not isinstance(text, str):
            return fallback
        cleaned = text.strip()
        if not cleaned:
            return fallback
        for pattern in self.BLOCK_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        cleaned = self._strip_prompt_echo(cleaned)
        cleaned = self._strip_leak_lines(cleaned)
        cleaned = self._strip_debug_prefix(cleaned)
        cleaned = self._collapse_whitespace(cleaned)
        if self.looks_like_only_leakage(cleaned):
            return fallback
        return cleaned or fallback

    def looks_like_only_leakage(self, text: str) -> bool:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return True
        leaked = sum(1 for line in lines if any(p.match(line) for p in self.LEAK_LINE_PATTERNS))
        return leaked >= max(1, len(lines) - 1)

    def _strip_prompt_echo(self, text: str) -> str:
        matches = list(re.finditer(r"\bAssistant\s*:\s*", text, flags=re.IGNORECASE))
        if matches:
            tail = text[matches[-1].end():].strip()
            if tail:
                return tail
        return text

    def _strip_leak_lines(self, text: str) -> str:
        kept = []
        for raw in text.splitlines():
            line = raw.strip()
            if line and any(p.match(line) for p in self.LEAK_LINE_PATTERNS):
                continue
            kept.append(raw)
        return "\n".join(kept).strip()

    @staticmethod
    def _strip_debug_prefix(text: str) -> str:
        return re.sub(r"^\s*\[[a-z0-9_.:-]+\]\s*", "", text, flags=re.IGNORECASE).strip()

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text).strip()
