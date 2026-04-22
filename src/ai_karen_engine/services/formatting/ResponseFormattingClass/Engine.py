from __future__ import annotations

from typing import Any, Dict

from .Accessibility import AccessibilityMixin
from .Analysis import AnalysisMixin
from .Base import FormatterBase
from .Citations import CitationsMixin
from .CodeFormatting import CodeFormattingMixin
from .display_transforms import DisplayTransformsMixin
from .Enums import AccessibilityLevel, ContentType, DisplayContext, FormatType
from .Metadata import MetadataMixin
from .Models import AnalysisResult, FormattedResponse, FormattingContext
from .Normalization import NormalizationMixin
from .Sections import SectionsMixin
from .SyntaxHighlighting import SyntaxHighlightingMixin
from .RegexPatterns import TABLE_RE


class ResponseFormattingEngine(
    FormatterBase,
    AnalysisMixin,
    NormalizationMixin,
    SectionsMixin,
    CitationsMixin,
    CodeFormattingMixin,
    SyntaxHighlightingMixin,
    AccessibilityMixin,
    DisplayTransformsMixin,
    MetadataMixin,
):
    """Canonical runtime response formatting engine implementation."""

    def __init__(self) -> None:
        super().__init__()

    async def format_response(self, content: str, context: FormattingContext) -> FormattedResponse:
        # 1) normalize raw content
        normalized = self._normalize_content(content)

        # 2) analyze content structure
        analysis_dict = await self.analyze_content_structure(normalized)
        analysis = self._analysis_from_dict(analysis_dict)

        # 3) choose format type
        format_type = self._select_optimal_format_from_analysis(analysis, context)

        # 4) organize into sections
        sections = await self.organize_content_hierarchically(normalized)

        # 5) repair markdown issues
        normalized = self._repair_markdown_headers(normalized)
        normalized = self._repair_lists(normalized)

        # 6) repair code blocks
        normalized = self._repair_code_blocks(normalized)

        # table + spacing normalization
        normalized = self._normalize_tables(normalized)
        normalized = self._normalize_spacing(normalized)

        # 7) append sources/citations when needed
        normalized = self._append_citations_section_if_needed(normalized, analysis.citations, format_type)

        # 8) apply display-context transform
        normalized = self._apply_display_transform(normalized, format_type, context)

        # 9) apply accessibility transform
        normalized = self._apply_accessibility_transform(normalized, context, analysis)

        # 10) generate navigation aids
        navigation_aids = self._build_navigation_aids(sections, context)

        # accessibility features
        accessibility_features = self._build_accessibility_features(context, analysis, navigation_aids)

        # 11) generate final metadata envelope
        metadata = self._build_metadata(
            analysis=analysis,
            context=context,
            format_type=format_type,
            sections=sections,
            has_tables=bool(TABLE_RE.search(content or "")),
        )

        return FormattedResponse(
            content=normalized,
            format_type=format_type,
            sections=sections,
            navigation_aids=navigation_aids,
            accessibility_features=accessibility_features,
            metadata=metadata,
            estimated_reading_time=analysis.reading_time,
        )

    async def select_optimal_format(self, content: str, context: FormattingContext) -> FormatType:
        analysis_dict = await self.analyze_content_structure(content)
        analysis = self._analysis_from_dict(analysis_dict)
        return self._select_optimal_format_from_analysis(analysis, context)

    def _select_optimal_format_from_analysis(self, analysis: AnalysisResult, context: FormattingContext) -> FormatType:
        if context.display_context == DisplayContext.API:
            return FormatType.API_STRUCTURED
        if context.display_context == DisplayContext.TERMINAL:
            return FormatType.TERMINAL_PLAIN
        if context.display_context == DisplayContext.PRINT:
            return FormatType.PRINT_FRIENDLY
        if context.display_context == DisplayContext.MOBILE:
            return FormatType.MOBILE_COMPACT

        if context.accessibility_level == AccessibilityLevel.FULL:
            return FormatType.ACCESSIBLE_MARKDOWN

        if analysis.content_type in {ContentType.CODE_HEAVY, ContentType.TECHNICAL}:
            return FormatType.TECHNICAL_MARKDOWN

        if analysis.content_type == ContentType.SEARCH_SUMMARY or analysis.citations:
            return FormatType.SEARCH_ANSWER

        return FormatType.STANDARD_MARKDOWN

    def _analysis_from_dict(self, data: Dict[str, Any]) -> AnalysisResult:
        from .Enums import ComplexityLevel

        return AnalysisResult(
            content_type=data["content_type"],
            complexity=ComplexityLevel(data["complexity"]),
            sections=data["sections"],
            code_blocks=data["code_blocks"],
            data_structures=data["data_structures"],
            length=data["length"],
            reading_time=data["reading_time"],
            technical_density=data["technical_density"],
            citations=data.get("citations", []),
        )
