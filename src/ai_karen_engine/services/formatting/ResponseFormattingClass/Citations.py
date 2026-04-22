from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from .Enums import FormatType
from .Models import CitationInfo


class CitationsMixin:
    def _append_citations_section_if_needed(
        self,
        text: str,
        citations: List[CitationInfo],
        format_type: FormatType,
    ) -> str:
        if not citations:
            return text

        if format_type not in {
            FormatType.SEARCH_ANSWER,
            FormatType.TECHNICAL_MARKDOWN,
            FormatType.ACCESSIBLE_MARKDOWN,
        }:
            return text

        lowered = text.lower()
        if "## sources" in lowered or "## citations" in lowered:
            return text

        deduped_citations = self._dedupe_citations(citations)
        if not deduped_citations:
            return text

        lines = ["", "## Sources", ""]

        for citation in deduped_citations:
            title = self._clean_citation_title(citation.title, citation.url)
            line = f"- [{title}]({citation.url})"

            if citation.snippet:
                snippet = citation.snippet.strip().rstrip(" -—:")
                if snippet:
                    line += f" — {snippet}"

            lines.append(line)

        return text.rstrip() + "\n" + "\n".join(lines).rstrip()

    def _dedupe_citations(self, citations: List[CitationInfo]) -> List[CitationInfo]:
        deduped: List[CitationInfo] = []
        seen: set[str] = set()

        for citation in citations:
            url = (citation.url or "").strip()
            if not url or url in seen:
                continue

            seen.add(url)

            if not getattr(citation, "domain", ""):
                citation.domain = self._extract_domain(url)

            deduped.append(citation)

        return deduped

    def _clean_citation_title(self, title: str, url: str) -> str:
        cleaned = (title or "").strip()
        if not cleaned:
            return url

        if cleaned.lower() == url.lower():
            return url

        return cleaned

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().removeprefix("www.")
        except Exception:
            return ""