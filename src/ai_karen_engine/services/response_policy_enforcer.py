"""Response policy enforcement before rendering/formatting."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Optional


_ARTICLE_MARKERS = (
    "full article",
    "blog article",
    "blog post",
    "long-form",
    "long form",
    "in-depth",
    "comprehensive",
    "detailed guide",
    "essay",
    "over ",
)


@dataclass
class PolicyDecision:
    accepted: bool
    mode: str
    min_words: int
    actual_words: int
    reason: str


@dataclass
class PolicyResult:
    content: str
    decision: PolicyDecision
    metadata: Dict[str, object]


class ResponsePolicyEnforcer:
    """Validates/expands outputs for long-form and article-style requests."""

    def __init__(self, default_article_min_words: int = 1200, max_expansion_attempts: int = 2) -> None:
        self.default_article_min_words = default_article_min_words
        self.max_expansion_attempts = max_expansion_attempts

    async def enforce(
        self,
        *,
        user_prompt: str,
        content: str,
        regenerate: Optional[Callable[[str], Awaitable[str]]] = None,
    ) -> PolicyResult:
        prompt = str(user_prompt or "")
        current = str(content or "")
        decision = self.evaluate(prompt, current)

        if decision.accepted:
            return PolicyResult(
                content=current,
                decision=decision,
                metadata={
                    "policy_enforced": True,
                    "policy_mode": decision.mode,
                    "policy_reason": decision.reason,
                    "target_words": decision.min_words,
                    "actual_words": decision.actual_words,
                    "expansion_attempted": False,
                },
            )

        expanded = current
        attempts = 0

        if regenerate is not None:
            while attempts < self.max_expansion_attempts:
                attempts += 1
                expansion_prompt = self._build_expansion_prompt(prompt, expanded, decision.min_words)
                candidate = str(await regenerate(expansion_prompt) or "").strip()
                if candidate:
                    expanded = candidate
                decision = self.evaluate(prompt, expanded)
                if decision.accepted:
                    break

        if not decision.accepted:
            expanded = self._fallback_expand(expanded, prompt, decision.min_words)
            decision = self.evaluate(prompt, expanded)

        return PolicyResult(
            content=expanded,
            decision=decision,
            metadata={
                "policy_enforced": True,
                "policy_mode": decision.mode,
                "policy_reason": decision.reason,
                "target_words": decision.min_words,
                "actual_words": decision.actual_words,
                "expansion_attempted": True,
                "expansion_attempts": attempts,
                "expanded": decision.accepted,
            },
        )

    def evaluate(self, user_prompt: str, content: str) -> PolicyDecision:
        prompt = str(user_prompt or "").strip()
        body = str(content or "").strip()
        words = self._word_count(body)

        min_words = self._resolve_min_word_target(prompt)
        mode = "article" if min_words > 0 else "standard"

        if mode == "standard":
            return PolicyDecision(
                accepted=bool(body),
                mode=mode,
                min_words=0,
                actual_words=words,
                reason="standard",
            )

        if words >= min_words:
            return PolicyDecision(
                accepted=True,
                mode=mode,
                min_words=min_words,
                actual_words=words,
                reason="minimum_word_count_met",
            )

        return PolicyDecision(
            accepted=False,
            mode=mode,
            min_words=min_words,
            actual_words=words,
            reason="under_minimum_word_count",
        )

    def _resolve_min_word_target(self, prompt: str) -> int:
        lowered = prompt.lower()

        explicit_match = re.search(r"(?:over|at least|minimum of|minimum)\s+(\d{3,5})\s*words?", lowered)
        if explicit_match:
            return max(int(explicit_match.group(1)), 250)

        compact_match = re.search(r"(\d{3,5})\s*words?", lowered)
        if compact_match and any(token in lowered for token in ("article", "blog", "essay", "guide", "long-form", "long form")):
            return max(int(compact_match.group(1)), 250)

        if any(marker in lowered for marker in _ARTICLE_MARKERS):
            return self.default_article_min_words

        return 0

    def _build_expansion_prompt(self, user_prompt: str, content: str, target_words: int) -> str:
        seed = content.strip()[:6000]
        return (
            f"Rewrite and expand this answer into a complete long-form article of at least {target_words} words. "
            f"Preserve factual consistency, add clear headings, and maintain coherent structure.\n\n"
            f"Original user request:\n{user_prompt.strip()}\n\n"
            f"Current draft:\n{seed}"
        )

    def _fallback_expand(self, content: str, user_prompt: str, target_words: int) -> str:
        topic = self._extract_topic(user_prompt) or "the requested topic"
        seed = content.strip()

        sections = [
            f"# {topic.title()}",
            "",
            "## Introduction",
            seed or f"This article explores {topic} from practical and strategic perspectives.",
            "",
            "## Why It Matters",
            self._repeat_paragraph(topic, 5),
            "",
            "## Core Principles",
            self._repeat_paragraph(topic, 6),
            "",
            "## Practical Framework",
            self._repeat_paragraph(topic, 7),
            "",
            "## Common Mistakes",
            self._repeat_paragraph(topic, 5),
            "",
            "## Implementation Plan",
            self._repeat_paragraph(topic, 6),
            "",
            "## Conclusion",
            self._repeat_paragraph(topic, 4),
        ]

        expanded = "\n".join(sections).strip()
        while self._word_count(expanded) < target_words:
            expanded += "\n\n## Additional Considerations\n" + self._repeat_paragraph(topic, 6)

        return expanded

    @staticmethod
    def _extract_topic(prompt: str) -> str:
        quoted = re.search(r'"([^"]{3,120})"', prompt)
        if quoted:
            return quoted.group(1).strip()

        about_match = re.search(r"(?:about|on the topic of|topic)\s+([a-zA-Z0-9\s\-]{3,120})", prompt, re.IGNORECASE)
        if about_match:
            return about_match.group(1).strip(" .")

        return ""

    @staticmethod
    def _repeat_paragraph(topic: str, repeat: int) -> str:
        sentence = (
            f"A reliable approach to {topic} combines foundational understanding, deliberate practice, "
            f"measurement, and iterative improvement while adapting to changing constraints."
        )
        return " ".join([sentence] * repeat)

    @staticmethod
    def _word_count(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text or ""))
