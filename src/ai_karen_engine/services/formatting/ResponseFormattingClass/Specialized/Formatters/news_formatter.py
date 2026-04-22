"""
News Response Formatter.
Migrated from extension system to core services.
"""

import html
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from ..Base import SpecializedFormatter, ResponseContext
from ...Models import FormattedResponse
from ...Enums import ContentType, FormatType

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Data structure for news article information."""

    headline: str
    source: Optional[str] = None
    publication_date: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    key_points: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.key_points is None:
            self.key_points = []


class NewsResponseFormatter(SpecializedFormatter):
    """
    Formatter for news-related responses.
    """

    def __init__(self):
        super().__init__("news", "2.0.0")

        self._news_patterns = [
            r"(?i)\b(?:news|article|report|story|breaking news)\b",
            r"(?i)(?:headline|title)\s*[:\-]?\s*([^,\n]+)",
            r"(?i)(?:source|published by|reported by|according to)\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\b(?:published|updated|dated)\s*[:\-]?\s*([A-Za-z0-9,\-/: ]+)",
        ]

        self._category_keywords = {
            "politics": [
                "election",
                "senate",
                "president",
                "government",
                "policy",
                "minister",
            ],
            "business": ["market", "stocks", "earnings", "company", "ceo", "revenue"],
            "technology": ["ai", "software", "startup", "chip", "device", "platform"],
            "sports": ["game", "season", "score", "team", "player", "league"],
            "health": [
                "health",
                "medical",
                "hospital",
                "disease",
                "treatment",
                "study",
            ],
            "world": ["international", "global", "conflict", "summit", "foreign"],
            "science": [
                "research",
                "scientists",
                "study",
                "discovery",
                "space",
                "climate",
            ],
            "entertainment": [
                "film",
                "music",
                "actor",
                "series",
                "celebrity",
                "streaming",
            ],
        }

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.NEWS:
            return True

        content_lower = content.lower()
        news_keywords = [
            "news",
            "article",
            "report",
            "breaking",
            "headline",
            "journalist",
            "source",
            "published",
            "reported",
        ]
        keyword_count = sum(1 for kw in news_keywords if kw in content_lower)

        return keyword_count >= 3 or any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in self._news_patterns
        )

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        article = self._extract_news_info(content, context)

        if (
            article.headline == "News Update"
            and not article.source
            and not article.summary
            and context.detected_content_type != ContentType.NEWS
        ):
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        formatted_html = self._generate_news_article_html(article)
        final_content = f"{formatted_html}\n\n{content}"

        return FormattedResponse(
            content=final_content,
            format_type=FormatType.SEARCH_ANSWER,
            metadata={
                "formatter": self.name,
                "headline": article.headline,
                "source": article.source,
                "publication_date": article.publication_date,
                "category": article.category,
                "key_point_count": len(article.key_points or []),
            },
            preferred_renderer="html",
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "cards", "badges", "lists"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.NEWS]

    def _extract_news_info(self, content: str, context: ResponseContext) -> NewsArticle:
        article = NewsArticle(headline="News Update")

        article.headline = self._extract_headline(content)
        article.source = self._extract_source(content)
        article.publication_date = self._extract_publication_date(content)
        article.summary = self._extract_summary(content, article.headline)
        article.category = self._detect_category(content)
        article.key_points = self._extract_key_points(content)

        return article

    def _extract_headline(self, content: str) -> str:
        patterns = [
            r'(?i)(?:headline|title|breaking|breaking news)\s*[:\-]?\s*["\']?([^"\n]+)',
            r'(?i)^["\']?([A-Z][^\n]{15,140})["\']?\n',
            r'(?i)^([A-Z][A-Za-z0-9,:\-\'"()\s]{15,140})$',
            r'(?i)(?:news|article|report|story)\s*[:\-]?\s*["\']?([^"\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                candidate = self._clean_text(match.group(1))
                if candidate and len(candidate) >= 8:
                    return candidate[:160]

        first_line = self._first_meaningful_line(content)
        if first_line and len(first_line) >= 8:
            return first_line[:160]

        return "News Update"

    def _extract_source(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)(?:source|published by|reported by|according to)\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\b(?:from|via)\s+([A-Z][A-Za-z0-9&.\- ]{2,60})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                source = self._clean_text(match.group(1))
                if source:
                    return source[:80]

        return None

    def _extract_publication_date(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)(?:published|updated|dated|publication date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"(?i)(?:published|updated|dated|publication date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
            r"(?i)(?:published|updated|dated|publication date)\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})",
            r"\b([A-Za-z]+\s+\d{1,2},\s+\d{4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return self._clean_text(match.group(1))

        return None

    def _extract_summary(self, content: str, headline: str) -> Optional[str]:
        paragraphs = [
            self._clean_text(p)
            for p in re.split(r"\n\s*\n+", content)
            if self._clean_text(p)
        ]

        filtered: List[str] = []
        for paragraph in paragraphs:
            lower = paragraph.lower()
            if any(
                marker in lower
                for marker in [
                    "headline:",
                    "title:",
                    "source:",
                    "published:",
                    "updated:",
                    "reported by:",
                ]
            ):
                continue
            if paragraph == headline:
                continue
            if len(paragraph) < 30:
                continue
            filtered.append(paragraph)

        if filtered:
            return filtered[0][:320]

        sentences = re.split(r"(?<=[.!?])\s+", self._clean_text(content))
        cleaned_sentences = [
            s for s in sentences if len(s) > 25 and headline.lower() not in s.lower()
        ]
        if cleaned_sentences:
            return " ".join(cleaned_sentences[:2])[:320]

        return None

    def _extract_key_points(self, content: str) -> List[str]:
        points: List[str] = []

        bullet_matches = re.findall(r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s+(.+)", content)
        for item in bullet_matches:
            cleaned = self._clean_text(item)
            if cleaned and len(cleaned) > 10:
                points.append(cleaned)

        if not points:
            sentences = re.split(r"(?<=[.!?])\s+", self._clean_text(content))
            for sentence in sentences:
                cleaned = self._clean_text(sentence)
                if len(cleaned) > 35:
                    points.append(cleaned)
                if len(points) >= 3:
                    break

        deduped: List[str] = []
        seen = set()
        for point in points:
            key = point.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(point[:180])

        return deduped[:4]

    def _detect_category(self, content: str) -> Optional[str]:
        content_lower = content.lower()

        scores = {}
        for category, keywords in self._category_keywords.items():
            scores[category] = sum(1 for kw in keywords if kw in content_lower)

        best_category = max(scores.keys(), key=lambda k: scores[k])
        return best_category.title() if scores[best_category] > 0 else None

    def _generate_news_article_html(self, article: NewsArticle) -> str:
        html_parts = [
            '<div class="news-article p-4 rounded-xl border border-border bg-card shadow-sm">',
            '<div class="flex flex-col gap-3">',
            '<div class="flex flex-wrap items-start justify-between gap-3">',
            f'<h1 class="text-xl font-bold leading-tight flex-1">📰 {self._escape_html(article.headline)}</h1>',
        ]

        if article.source:
            html_parts.append(
                f'<span class="bg-primary/10 text-primary text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">'
                f"{self._escape_html(article.source)}</span>"
            )

        html_parts.append("</div>")

        meta_chips: List[str] = []
        if article.publication_date:
            meta_chips.append(self._chip(f"📅 {article.publication_date}"))
        if article.category:
            meta_chips.append(self._chip(f"🏷️ {article.category}"))

        if meta_chips:
            html_parts.append(
                f'<div class="flex flex-wrap gap-2">{"".join(meta_chips)}</div>'
            )

        if article.summary:
            html_parts.append(
                f'<p class="text-sm text-muted-foreground leading-6">'
                f"{self._escape_html(article.summary)}</p>"
            )

        if article.key_points:
            html_parts.append('<div class="mt-1">')
            html_parts.append(
                '<h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-2">Key Points</h2>'
            )
            html_parts.append('<ul class="list-disc pl-5 space-y-1">')
            for point in article.key_points:
                html_parts.append(
                    f'<li class="text-sm">{self._escape_html(point)}</li>'
                )
            html_parts.append("</ul></div>")

        html_parts.append("</div></div>")
        return "".join(html_parts)

    def _chip(self, value: str) -> str:
        return (
            f'<span class="bg-secondary text-secondary-foreground text-xs px-2 py-1 rounded-full">'
            f"{self._escape_html(value)}</span>"
        )

    def _first_meaningful_line(self, content: str) -> Optional[str]:
        for line in content.splitlines():
            cleaned = self._clean_text(line)
            if cleaned and len(cleaned) > 8:
                return cleaned
        return None

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:;,'\"")

    def _escape_html(self, text: str) -> str:
        return html.escape(text, quote=True)
