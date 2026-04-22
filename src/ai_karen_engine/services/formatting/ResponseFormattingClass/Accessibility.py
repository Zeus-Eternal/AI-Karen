from __future__ import annotations

from typing import Any, Dict, List

from .Enums import AccessibilityLevel
from .Models import AnalysisResult, FormattingContext, NavigationAid


class AccessibilityMixin:
    def _apply_accessibility_transform(
        self,
        text: str,
        context: FormattingContext,
        analysis: AnalysisResult,
    ) -> str:
        if context.accessibility_level == AccessibilityLevel.BASIC:
            return text

        additions: List[str] = []

        if context.accessibility_level in {AccessibilityLevel.ENHANCED, AccessibilityLevel.FULL}:
            additions.append(f"<!-- reading-time: {analysis.reading_time} min -->")
            additions.append(f"<!-- content-type: {analysis.content_type.value} -->")

        if context.accessibility_level == AccessibilityLevel.FULL:
            additions.append(f"<!-- complexity: {analysis.complexity.value} -->")
            additions.append(f"<!-- section-count: {len(analysis.sections)} -->")
            additions.append(f"<!-- code-blocks-count: {len(analysis.code_blocks)} -->")
            additions.append(f"<!-- citations-count: {len(analysis.citations)} -->")

            if getattr(analysis, "is_long_form", False):
                additions.append("<!-- long-form-content: true -->")

            if analysis.citations:
                additions.append("<!-- sources-available: true -->")

            if analysis.code_blocks:
                additions.append("<!-- code-sections-available: true -->")

        if additions:
            return "\n".join(additions) + "\n" + text

        return text

    def _build_accessibility_features(
        self,
        context: FormattingContext,
        analysis: AnalysisResult,
        navigation_aids: List[NavigationAid],
    ) -> Dict[str, Any]:
        has_code_blocks = len(analysis.code_blocks) > 0
        has_citations = len(analysis.citations) > 0
        is_long_form = getattr(analysis, "is_long_form", analysis.reading_time >= 6)

        features: Dict[str, Any] = {
            "estimated_reading_time": analysis.reading_time,
            "technical_density": analysis.technical_density,
            "keyboard_navigation": len(navigation_aids) > 0,
            "has_code_blocks": has_code_blocks,
            "has_sources": has_citations,
            "long_form_content": is_long_form,
        }

        if context.accessibility_level in {AccessibilityLevel.ENHANCED, AccessibilityLevel.FULL}:
            features["navigation_aids"] = [nav.model_dump() for nav in navigation_aids]
            features["toc_available"] = len(navigation_aids) > 0
            features["section_labels"] = [nav.label for nav in navigation_aids]

            summary_parts = [
                f"{analysis.content_type.value.replace('_', ' ').title()} content.",
                f"{analysis.complexity.value.title()} complexity.",
                f"Estimated reading time {analysis.reading_time} minutes.",
            ]

            if len(analysis.sections) > 0:
                summary_parts.append(f"Contains {len(analysis.sections)} sections.")

            if has_code_blocks:
                summary_parts.append(f"Contains {len(analysis.code_blocks)} code blocks.")

            if has_citations:
                summary_parts.append(f"Contains {len(analysis.citations)} sources.")

            features["screen_reader_text"] = " ".join(summary_parts)
            features["source_navigation_available"] = has_citations
            features["code_navigation_available"] = has_code_blocks

        if context.accessibility_level == AccessibilityLevel.FULL:
            features["section_count"] = len(analysis.sections)
            features["code_blocks_count"] = len(analysis.code_blocks)
            features["citations_count"] = len(analysis.citations)
            features["landmark_sections"] = [
                {
                    "label": nav.label,
                    "target_id": nav.target_id,
                    "level": nav.level,
                }
                for nav in navigation_aids
            ]
            features["skip_navigation_recommended"] = is_long_form or len(navigation_aids) >= 5

        if analysis.technical_density > 0.7:
            features["content_warning"] = "Highly technical content."

        if has_code_blocks:
            features["code_notice"] = "Contains code sections."

        if has_citations:
            features["sources_notice"] = "Contains cited sources."

        return features