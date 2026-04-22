"""
Travel Response Formatter.
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
class TravelInfo:
    """Structured travel information extracted from content."""

    destination: str
    duration: Optional[str] = None
    budget: Optional[str] = None
    activities: Optional[List[str]] = None
    transportation: Optional[List[str]] = None
    accommodations: Optional[List[str]] = None
    travel_style: Optional[str] = None
    best_time_to_visit: Optional[str] = None

    def __post_init__(self) -> None:
        if self.activities is None:
            self.activities = []
        if self.transportation is None:
            self.transportation = []
        if self.accommodations is None:
            self.accommodations = []


class TravelResponseFormatter(SpecializedFormatter):
    """
    Formatter for travel-related responses.
    Extracts structured travel details and renders a travel card.
    """

    def __init__(self):
        super().__init__("travel", "2.0.0")

        self._travel_patterns = [
            r"\b(?:travel|trip|vacation|holiday|visit|tour|journey|getaway)\b",
            r"\b(?:destination|place to visit|best places|where to go)\b",
            r"\b(?:itinerary|schedule|plan|day trip|weekend trip)\b",
            r"\b(?:hotel|flight|resort|hostel|airbnb|train|cruise)\b",
        ]

        self._activity_keywords = {
            "hiking": "🥾",
            "beach": "🏖️",
            "museum": "🏛️",
            "shopping": "🛍️",
            "skiing": "🎿",
            "snorkeling": "🤿",
            "diving": "🤿",
            "nightlife": "🌃",
            "food tour": "🍽️",
            "camping": "🏕️",
            "road trip": "🚗",
            "sightseeing": "📸",
            "temple": "⛩️",
            "historic sites": "🏰",
            "safari": "🦁",
            "wine tasting": "🍷",
            "cruise": "🛳️",
            "fishing": "🎣",
            "kayaking": "🛶",
            "surfing": "🏄",
        }

        self._transport_keywords = [
            "flight",
            "plane",
            "train",
            "bus",
            "car rental",
            "rental car",
            "taxi",
            "subway",
            "metro",
            "ferry",
            "cruise",
            "road trip",
        ]

        self._accommodation_keywords = [
            "hotel",
            "hostel",
            "resort",
            "airbnb",
            "villa",
            "cabin",
            "lodge",
            "apartment",
            "guesthouse",
        ]

        self._travel_styles = [
            "luxury",
            "budget",
            "family",
            "romantic",
            "solo",
            "adventure",
            "business",
            "backpacking",
            "eco travel",
            "all-inclusive",
        ]

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.TRAVEL:
            return True

        content_lower = content.lower()
        travel_keywords = [
            "travel",
            "trip",
            "vacation",
            "holiday",
            "destination",
            "itinerary",
            "hotel",
            "flight",
            "tour",
            "resort",
            "visit",
        ]
        keyword_count = sum(1 for kw in travel_keywords if kw in content_lower)

        return keyword_count >= 3 or any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in self._travel_patterns
        )

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        travel_info = self._extract_travel_info(content)

        if (
            travel_info.destination == "Unknown Destination"
            and not travel_info.activities
            and context.detected_content_type != ContentType.TRAVEL
        ):
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        formatted_html = self._generate_travel_card_html(travel_info, context)
        final_content = f"{formatted_html}\n\n{content}"

        return FormattedResponse(
            content=final_content,
            format_type=FormatType.SEARCH_ANSWER,
            metadata={
                "formatter": self.name,
                "destination": travel_info.destination,
                "duration": travel_info.duration,
                "budget": travel_info.budget,
                "activity_count": len(travel_info.activities or []),
                "transportation": travel_info.transportation,
                "accommodations": travel_info.accommodations,
                "travel_style": travel_info.travel_style,
            },
            preferred_renderer="html",
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "cards", "icons", "badges"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.TRAVEL]

    def _extract_travel_info(self, content: str) -> TravelInfo:
        info = TravelInfo(destination="Unknown Destination")

        info.destination = self._extract_destination(content)
        info.duration = self._extract_duration(content)
        info.budget = self._extract_budget(content)
        info.activities = self._extract_activities(content)
        info.transportation = self._extract_keyword_list(
            content, self._transport_keywords
        )
        info.accommodations = self._extract_keyword_list(
            content, self._accommodation_keywords
        )
        info.travel_style = self._extract_travel_style(content)
        info.best_time_to_visit = self._extract_best_time_to_visit(content)

        return info

    def _extract_destination(self, content: str) -> str:
        patterns = [
            r"(?i)(?:travel|trip|vacation|holiday|visit|go|fly)\s+to\s+([A-Z][a-zA-Z\s,\-']{1,60})",
            r"(?i)(?:destination|visiting|travelling to|traveling to)\s*[:\-]?\s*([A-Z][a-zA-Z\s,\-']{1,60})",
            r"(?i)(?:in|for)\s+([A-Z][a-zA-Z\s,\-']{1,60})\s+(?:itinerary|travel guide|vacation|trip)",
            r"(?i)^([A-Z][a-zA-Z\s,\-']{1,60})\s+(?:travel guide|itinerary|vacation|trip)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                destination = self._clean_destination(match.group(1))
                if destination:
                    return destination

        return "Unknown Destination"

    def _extract_duration(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)(\d+\s*(?:day|days|week|weeks|month|months))",
            r"(?i)(?:duration|length|stay|trip length)\s*[:\-]?\s*([A-Za-z0-9\s\-]+(?:days?|weeks?|months?))",
            r"(?i)\b(weekend trip)\b",
            r"(?i)\b(one week|two weeks|three days|four days|five days)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return self._normalize_whitespace(match.group(1))

        return None

    def _extract_budget(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)\bbudget\s*[:\-]?\s*(\$[\d,]+(?:\.\d{2})?)",
            r"(?i)(\$[\d,]+(?:\.\d{2})?)\s+(?:budget|total budget|spending budget)",
            r"(?i)\bunder\s+(\$[\d,]+(?:\.\d{2})?)",
            r"(?i)\baround\s+(\$[\d,]+(?:\.\d{2})?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_activities(self, content: str) -> List[str]:
        found: List[str] = []
        content_lower = content.lower()

        for activity in self._activity_keywords:
            if activity in content_lower:
                found.append(activity.title())

        list_patterns = [
            r"(?i)(?:activities|things to do|plans|highlights)\s*[:\-]?\s*([^\n.]+)",
            r"(?i)(?:including|such as)\s+([^\n.]+)",
        ]

        for pattern in list_patterns:
            match = re.search(pattern, content)
            if not match:
                continue

            raw_items = re.split(r",|/|;|\band\b", match.group(1))
            for item in raw_items:
                cleaned = self._normalize_whitespace(item).strip(" -•")
                if (
                    cleaned
                    and len(cleaned) > 2
                    and cleaned.lower()
                    not in {
                        "the",
                        "trip",
                        "travel",
                    }
                ):
                    title_case = cleaned[:80].title()
                    if title_case not in found:
                        found.append(title_case)

        return found[:8]

    def _extract_keyword_list(self, content: str, keywords: List[str]) -> List[str]:
        content_lower = content.lower()
        found: List[str] = []

        for keyword in keywords:
            if keyword in content_lower:
                normalized = keyword.title()
                if normalized not in found:
                    found.append(normalized)

        return found

    def _extract_travel_style(self, content: str) -> Optional[str]:
        content_lower = content.lower()
        for style in self._travel_styles:
            if style in content_lower:
                return style.title()
        return None

    def _extract_best_time_to_visit(self, content: str) -> Optional[str]:
        patterns = [
            r"(?i)(?:best time to visit|best time to travel|ideal time)\s*[:\-]?\s*([^\n.]+)",
            r"(?i)(?:best in|ideal in)\s+([A-Za-z\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return self._normalize_whitespace(match.group(1))[:80]

        return None

    def _generate_travel_card_html(
        self, info: TravelInfo, context: ResponseContext
    ) -> str:
        chips: List[str] = []
        if info.duration:
            chips.append(self._render_chip(f"🗓️ {info.duration}"))
        if info.budget:
            chips.append(self._render_chip(f"💰 {info.budget}"))
        if info.travel_style:
            chips.append(self._render_chip(f"🧭 {info.travel_style}"))
        if info.best_time_to_visit:
            chips.append(self._render_chip(f"🌤️ {info.best_time_to_visit}"))

        html_parts: List[str] = [
            '<div class="travel-card p-4 rounded-xl border border-border bg-card shadow-sm">',
            f'<h2 class="text-2xl font-bold mb-2">✈️ {self._escape_html(info.destination)}</h2>',
        ]

        if chips:
            html_parts.append(
                f'<div class="flex flex-wrap gap-2 mb-4">{"".join(chips)}</div>'
            )

        if info.activities:
            html_parts.append('<div class="mb-4">')
            html_parts.append(
                '<h3 class="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Top Activities</h3>'
            )
            html_parts.append('<div class="flex flex-wrap gap-2">')
            for activity in info.activities:
                emoji = self._activity_keywords.get(activity.lower(), "📍")
                html_parts.append(
                    self._render_chip(
                        f"{emoji} {self._escape_html(activity)}",
                        variant="secondary",
                    )
                )
            html_parts.append("</div></div>")

        if info.transportation or info.accommodations:
            html_parts.append('<div class="grid grid-cols-1 md:grid-cols-2 gap-4">')

            if info.transportation:
                html_parts.append(
                    '<div class="rounded-lg border border-border/60 bg-background/40 p-3">'
                    '<h3 class="text-sm font-semibold mb-2">Transport</h3>'
                    f'<p class="text-sm text-muted-foreground">{self._escape_html(", ".join(info.transportation))}</p>'
                    "</div>"
                )

            if info.accommodations:
                html_parts.append(
                    '<div class="rounded-lg border border-border/60 bg-background/40 p-3">'
                    '<h3 class="text-sm font-semibold mb-2">Stay</h3>'
                    f'<p class="text-sm text-muted-foreground">{self._escape_html(", ".join(info.accommodations))}</p>'
                    "</div>"
                )

            html_parts.append("</div>")

        html_parts.append("</div>")
        return "".join(html_parts)

    def _render_chip(self, value: str, variant: str = "default") -> str:
        if variant == "secondary":
            classes = "bg-secondary text-secondary-foreground"
        else:
            classes = "bg-primary/10 text-foreground"

        return (
            f'<span class="{classes} text-xs px-2.5 py-1 rounded-full border border-border/50">'
            f"{value}</span>"
        )

    def _clean_destination(self, value: str) -> str:
        cleaned = self._normalize_whitespace(value)
        cleaned = re.sub(
            r"(?i)\b(?:for \d+ days?|with .*|on a budget|itinerary|travel guide)$",
            "",
            cleaned,
        ).strip(" ,.-")
        return cleaned[:80] if cleaned else "Unknown Destination"

    def _normalize_whitespace(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _escape_html(self, text: str) -> str:
        return html.escape(text, quote=True)
