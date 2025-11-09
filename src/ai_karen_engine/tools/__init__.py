"""
Tools Package for AI-Karen
Production-ready tool plugins for agent execution

Provides comprehensive tool plugins including:
- Search tools (web search via SearxNG)
- Document processing tools (PDF, DOCX, etc.)
- Image analysis tools (vision models)
- HTTP client tools (API calls, web requests)
- File system tools (read, write, list, etc.)
- Text processing tools (analysis, extraction, formatting)
- Data analysis tools (statistics, aggregation, filtering)
- Code interpreters (Python, IPython, Docker, subprocess)
- Excel tools (spreadsheet operations)
"""

# Import existing tool categories
from . import interpreters
from . import search
from . import documents
from . import server_tools

# Import production tool plugins
from ai_karen_engine.tools.production_tools import (
    HTTPClientTool,
    FileSystemTool,
    TextProcessingTool,
    DataAnalysisTool,
    get_production_tools,
    register_production_tools
)

# Import tool implementations (for direct use if needed)
from ai_karen_engine.tools.http_client_tool import (
    HTTPClientTool as HTTPClientImpl,
    get_http_client_tool
)
from ai_karen_engine.tools.filesystem_tool import (
    FileSystemTool as FileSystemImpl,
    get_filesystem_tool
)
from ai_karen_engine.tools.text_processing_tool import (
    TextProcessingTool as TextProcessingImpl,
    get_text_processing_tool
)
from ai_karen_engine.tools.data_analysis_tool import (
    DataAnalysisTool as DataAnalysisImpl,
    get_data_analysis_tool
)

__all__ = [
    # Tool categories
    'interpreters',
    'search',
    'documents',
    'server_tools',
    # Production tool plugins (BaseTool implementations)
    'HTTPClientTool',
    'FileSystemTool',
    'TextProcessingTool',
    'DataAnalysisTool',
    # Tool registration
    'get_production_tools',
    'register_production_tools',
    # Tool implementations (for direct use)
    'HTTPClientImpl',
    'FileSystemImpl',
    'TextProcessingImpl',
    'DataAnalysisImpl',
    # Convenience getters
    'get_http_client_tool',
    'get_filesystem_tool',
    'get_text_processing_tool',
    'get_data_analysis_tool',
]
