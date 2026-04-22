"""
Movie Response Formatter.
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
class MovieInfo:
    """Data structure for movie information."""

    title: str
    year: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[List[str]] = None
    genre: Optional[List[str]] = None
    rating: Optional[str] = None
    plot: Optional[str] = None

    def __post_init__(self) -> None:
        if self.cast is None:
            self.cast = []
        if self.genre is None:
            self.genre = []


class MovieResponseFormatter(SpecializedFormatter):
    """
    Formatter for movie-related responses.
    """

    def __init__(self):
        super().__init__("movie", "2.0.0")

        self._movie_patterns = [
            r"(?i)\b(?:movie|film)\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\btitle\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\bdirected by\s+([^,\n]+)",
            r"(?i)\bstarring\s+([^,\n]+)",
            r"(?i)\b(?:imdb|rating|score)\s*[:\-]?\s*([\d.]+)",
            r"(?i)\bgenre\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\bplot\s*[:\-]?\s*(.+)",
        ]

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.MOVIE:
            return True

        content_lower = content.lower()
        movie_keywords = [
            "movie",
            "film",
            "cinema",
            "director",
            "actor",
            "cast",
            "rating",
            "starring",
            "genre",
            "plot",
        ]
        keyword_count = sum(1 for keyword in movie_keywords if keyword in content_lower)

        return keyword_count >= 3 or any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in self._movie_patterns
        )

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        movie_info = self._extract_movie_info(content)

        if (
            movie_info.title == "Unknown Movie"
            and not movie_info.director
            and not movie_info.cast
            and context.detected_content_type != ContentType.MOVIE
        ):
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        formatted_html = self._generate_movie_card_html(movie_info)
        final_content = f"{formatted_html}\n\n{content}"

        return FormattedResponse(
            content=final_content,
            format_type=FormatType.SEARCH_ANSWER,
            metadata={
                "formatter": self.name,
                "movie_title": movie_info.title,
                "rating": movie_info.rating,
                "year": movie_info.year,
                "director": movie_info.director,
                "cast_count": len(movie_info.cast or []),
                "genre_count": len(movie_info.genre or []),
            },
            preferred_renderer="html",
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "cards", "badges", "lists"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.MOVIE]

    def _extract_movie_info(self, content: str) -> MovieInfo:
        movie_info = MovieInfo(title=self._extract_title(content))

        movie_info.year = self._extract_year(content)
        movie_info.director = self._extract_director(content)
        movie_info.cast = self._extract_cast(content)
        movie_info.genre = self._extract_genre(content)
        movie_info.rating = self._extract_rating(content)
        movie_info.plot = self._extract_plot(content)

        return movie_info

    def _extract_title(self, content: str) -> str:
        patterns = [
            r'(?i)(?:movie|film|title)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'(?i)^["\']?([A-Z][A-Za-z0-9:\-\'&,.\s]{2,80})["\']?\s*(?:\(\d{4}\))?$',
            r"(?i)([A-Z][A-Za-z0-9:\-\'&,.\s]{2,80})\s*\(\d{4}\)",
        ]

        lines = [line.strip() for line in content.splitlines() if line.strip()]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                title = self._clean_text(match.group(1))
                if self._is_valid_title(title):
                    return title

        for line in lines[:3]:
            cleaned = self._clean_text(line)
            if self._is_valid_title(cleaned):
                return cleaned

        return "Unknown Movie"

    def _extract_year(self, content: str) -> Optional[str]:
        patterns = [
            r"\((\d{4})\)",
            r"(?i)\byear\s*[:\-]?\s*(\d{4})",
            r"(?i)\breleased?\s*[:\-]?\s*(\d{4})",
            r"(?i)\bfrom\s+(\d{4})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_director(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)directed?\s*by\s*[:\-]?\s*([^,\n]+)",
            r"(?i)\bdirector\s*[:\-]?\s*([^,\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                director = self._clean_text(match.group(1))
                if director:
                    return director

        return None

    def _extract_cast(self, content: str) -> List[str]:
        cast: List[str] = []

        patterns = [
            r"(?i)\bstarring\s*[:\-]?\s*([^\n]+)",
            r"(?i)\bcast\s*[:\-]?\s*([^\n]+)",
            r"(?i)\bfeaturing\s*[:\-]?\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if not match:
                continue

            values = re.split(r",|\band\b|/|;", match.group(1))
            for value in values:
                cleaned = self._clean_person_name(value)
                if cleaned and cleaned not in cast:
                    cast.append(cleaned)

        return cast[:8]

    def _extract_genre(self, content: str) -> List[str]:
        genres: List[str] = []

        patterns = [
            r"(?i)\bgenre\s*[:\-]?\s*([^\n]+)",
            r"(?i)\bgenres\s*[:\-]?\s*([^\n]+)",
            r"(?i)\b(?:an?|the)\s+([A-Za-z/\-,\s]+)\s+(?:movie|film)\b",
        ]

        known_genres = {
            "action",
            "adventure",
            "animation",
            "biography",
            "comedy",
            "crime",
            "documentary",
            "drama",
            "family",
            "fantasy",
            "history",
            "horror",
            "musical",
            "mystery",
            "romance",
            "sci-fi",
            "science fiction",
            "sport",
            "thriller",
            "war",
            "western",
        }

        for pattern in patterns:
            match = re.search(pattern, content)
            if not match:
                continue

            values = re.split(r",|/|\band\b|;", match.group(1))
            for value in values:
                cleaned = self._clean_text(value).lower()
                if cleaned in known_genres:
                    normalized = cleaned.title()
                    if normalized == "Sci-Fi":
                        normalized = "Sci-Fi"
                    if normalized == "Science Fiction":
                        normalized = "Science Fiction"
                    if normalized not in genres:
                        genres.append(normalized)

        return genres[:5]

    def _extract_rating(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)(?:imdb|rating|score)\s*[:\-]?\s*([\d.]+)(?:/10|/5|\s*stars?)?",
            r"(?i)\b([\d.]+)\s*/\s*10\b",
            r"(?i)\b([\d.]+)\s*/\s*5\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                rating = match.group(1).strip()
                return rating

        return None

    def _extract_plot(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)\bplot\s*[:\-]?\s*(.+?)(?:\n\n|\Z)",
            r"(?i)\bsynopsis\s*[:\-]?\s*(.+?)(?:\n\n|\Z)",
            r"(?i)\bstory\s*[:\-]?\s*(.+?)(?:\n\n|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                plot = self._clean_text(match.group(1))
                if len(plot) >= 20:
                    return plot[:400]

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        for paragraph in paragraphs:
            cleaned = self._clean_text(paragraph)
            lower = cleaned.lower()
            if any(
                marker in lower
                for marker in [
                    "plot:",
                    "synopsis:",
                    "story:",
                    "movie:",
                    "film:",
                    "title:",
                ]
            ):
                continue
            if len(cleaned) >= 40:
                return cleaned[:400]

        return None

    def _generate_movie_card_html(self, info: MovieInfo) -> str:
        html_parts = [
            '<div class="movie-card p-4 rounded-xl border border-border bg-card shadow-sm">',
            f'<h2 class="text-2xl font-bold mb-2">🎬 {self._escape_html(info.title)}</h2>',
        ]

        detail_chips: List[str] = []
        if info.year:
            detail_chips.append(self._render_chip(f"📅 {info.year}"))
        if info.director:
            detail_chips.append(self._render_chip(f"🎥 {info.director}"))
        if info.rating:
            detail_chips.append(self._render_chip(f"⭐ {info.rating}"))

        if detail_chips:
            html_parts.append(
                f'<div class="flex flex-wrap gap-2 mb-3">{"".join(detail_chips)}</div>'
            )

        if info.genre:
            html_parts.append('<div class="mb-3">')
            html_parts.append(
                '<h3 class="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Genre</h3>'
            )
            html_parts.append('<div class="flex flex-wrap gap-2">')
            for genre in info.genre:
                html_parts.append(self._render_chip(genre, variant="secondary"))
            html_parts.append("</div></div>")

        if info.cast:
            html_parts.append('<div class="mb-3">')
            html_parts.append(
                '<h3 class="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Cast</h3>'
            )
            html_parts.append(
                f'<p class="text-sm text-muted-foreground">{self._escape_html(", ".join(info.cast))}</p>'
            )
            html_parts.append("</div>")

        if info.plot:
            html_parts.append("<div>")
            html_parts.append(
                '<h3 class="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Plot</h3>'
            )
            html_parts.append(
                f'<p class="text-sm leading-6 text-muted-foreground">{self._escape_html(info.plot)}</p>'
            )
            html_parts.append("</div>")

        html_parts.append("</div>")
        return "".join(html_parts)

    def _render_chip(self, value: str, variant: str = "default") -> str:
        if variant == "secondary":
            classes = "bg-secondary text-secondary-foreground"
        else:
            classes = "bg-primary/10 text-primary"

        return (
            f'<span class="{classes} text-xs font-medium px-2 py-1 rounded-full">'
            f"{self._escape_html(value)}</span>"
        )

    def _is_valid_title(self, value: str) -> bool:
        if not value:
            return False

        lower = value.lower()
        invalid_fragments = {
            "director",
            "starring",
            "rating",
            "genre",
            "plot",
            "synopsis",
            "cast",
        }
        if any(fragment in lower for fragment in invalid_fragments):
            return False

        return 2 <= len(value) <= 80

    def _clean_person_name(self, value: str) -> str:
        cleaned = self._clean_text(value)
        cleaned = re.sub(r"(?i)\b(?:starring|cast|featuring)\b", "", cleaned).strip(
            " ,.-"
        )
        return cleaned[:60] if cleaned else ""

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:;,'\"")

    def _escape_html(self, text: str) -> str:
        return html.escape(text, quote=True)
