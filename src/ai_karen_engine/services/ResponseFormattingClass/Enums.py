from enum import Enum


class DisplayContext(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TERMINAL = "terminal"
    API = "api"
    PRINT = "print"


class AccessibilityLevel(str, Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


class FormatType(str, Enum):
    STANDARD_MARKDOWN = "standard_markdown"
    TECHNICAL_MARKDOWN = "technical_markdown"
    SEARCH_ANSWER = "search_answer"
    MOBILE_COMPACT = "mobile_compact"
    TERMINAL_PLAIN = "terminal_plain"
    API_STRUCTURED = "api_structured"
    PRINT_FRIENDLY = "print_friendly"
    ACCESSIBLE_MARKDOWN = "accessible_markdown"


class ContentType(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CODE_HEAVY = "code_heavy"
    SEARCH_SUMMARY = "search_summary"
    TUTORIAL = "tutorial"
    ANALYSIS = "analysis"
    QA = "qa"
    MIXED = "mixed"
    ARTICLE = "article"
    COMPARISON = "comparison"
    PRODUCT = "product"
    TROUBLESHOOTING = "troubleshooting"
    REFERENCE = "reference"


class SectionType(str, Enum):
    TITLE = "title"
    HEADER = "header"
    SUMMARY = "summary"
    INTRO = "intro"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    CITATIONS = "citations"
    SOURCES = "sources"
    NOTE = "note"
    WARNING = "warning"
    CONCLUSION = "conclusion"
    FOOTER = "footer"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"