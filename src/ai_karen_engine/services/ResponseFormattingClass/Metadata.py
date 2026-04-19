from __future__ import annotations

from typing import Any, Dict, List

from .Enums import DisplayContext, FormatType, SectionType
from .Models import AnalysisResult, ContentSection, FormattingContext, NavigationAid


class MetadataMixin:
    def _build_navigation_aids(
        self,
        sections: List[ContentSection],
        context: FormattingContext,
    ) -> List[NavigationAid]:
        navs: List[NavigationAid] = []

        for section in sections:
            if not section.navigation_id:
                continue

            nav_label = getattr(self, "_nav_label", None)
            if callable(nav_label):
                label = str(nav_label(section.content) or "Section")
            else:
                label = "Section"
            level = 1

            if section.section_type in {SectionType.HEADER, SectionType.TITLE}:
                level = int(section.metadata.get("level", 1))

            navs.append(
                NavigationAid(
                    label=label,
                    target_id=section.navigation_id,
                    level=level,
                    metadata={
                        "section_type": section.section_type.value,
                        "slug": section.metadata.get("slug"),
                        "priority": section.priority,
                    },
                )
            )

        if context.display_context == DisplayContext.MOBILE:
            return navs[:6]

        return navs

    def _build_metadata(
        self,
        analysis: AnalysisResult,
        context: FormattingContext,
        format_type: FormatType,
        sections: List[ContentSection],
        has_tables: bool,
    ) -> Dict[str, Any]:
        has_code_blocks = len(analysis.code_blocks) > 0
        has_citations = len(analysis.citations) > 0
        has_headers = getattr(analysis, "has_headers", any(s.section_type in {SectionType.HEADER, SectionType.TITLE} for s in sections))
        has_lists = getattr(analysis, "has_lists", any(s.section_type == SectionType.LIST for s in sections))
        has_inline_code = getattr(analysis, "has_inline_code", False)
        is_long_form = getattr(analysis, "is_long_form", analysis.length >= 2500)

        preferred_renderer = self._determine_preferred_renderer(
            analysis=analysis,
            format_type=format_type,
            has_code_blocks=has_code_blocks,
            has_citations=has_citations,
            is_long_form=is_long_form,
        )

        render_blocks_available = len(sections) > 0
        source_panel_recommended = has_citations and format_type in {
            FormatType.SEARCH_ANSWER,
            FormatType.TECHNICAL_MARKDOWN,
            FormatType.ACCESSIBLE_MARKDOWN,
        }
        navigation_panel_recommended = (
            has_headers or is_long_form or len(sections) >= 6
        )

        metadata: Dict[str, Any] = {
            "content_type": analysis.content_type.value,
            "complexity": analysis.complexity.value,
            "technical_density": analysis.technical_density,
            "code_blocks_count": len(analysis.code_blocks),
            "citations_count": len(analysis.citations),
            "sections_count": len(sections),
            "display_context": context.display_context.value,
            "accessibility_level": context.accessibility_level.value,
            "language": context.language,
            "technical_level": context.technical_level,
            "request_type": getattr(context, "request_type", "general"),
            "format_version": "1.1.0",
            "format_type": format_type.value,
            "preferred_renderer": preferred_renderer,
            "render_blocks_available": render_blocks_available,
            "source_panel_recommended": source_panel_recommended,
            "navigation_panel_recommended": navigation_panel_recommended,
            "has_code_blocks": has_code_blocks,
            "has_tables": has_tables,
            "has_citations": has_citations,
            "has_headers": has_headers,
            "has_lists": has_lists,
            "has_inline_code": has_inline_code,
            "is_long_form": is_long_form,
            "reading_time": analysis.reading_time,
            "content_length": analysis.length,
        }

        if has_citations:
            metadata["source_domains"] = sorted(
                {
                    citation.domain
                    for citation in analysis.citations
                    if getattr(citation, "domain", "")
                }
            )

        if has_code_blocks:
            metadata["code_languages"] = sorted(
                {
                    code_block.language
                    for code_block in analysis.code_blocks
                    if getattr(code_block, "language", "")
                }
            )

        return metadata

    def _determine_preferred_renderer(
        self,
        analysis: AnalysisResult,
        format_type: FormatType,
        has_code_blocks: bool,
        has_citations: bool,
        is_long_form: bool,
    ) -> str:
        if format_type == FormatType.SEARCH_ANSWER or has_citations:
            return "search_answer"

        if format_type == FormatType.TECHNICAL_MARKDOWN or has_code_blocks:
            return "technical"

        if is_long_form:
            return "article"

        if format_type == FormatType.MOBILE_COMPACT:
            return "mobile_compact"

        return "markdown"
