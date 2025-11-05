"""
Production Tool Plugins for AI-Karen
Tool plugins following the BaseTool pattern for integration with the existing tool service.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from ai_karen_engine.services.tool_service import (
    BaseTool,
    ToolMetadata,
    ToolCategory,
    ToolParameter,
    ToolStatus
)

# Import the utility implementations
from ai_karen_engine.tools.http_client_tool import HTTPClientTool as HTTPClientImpl
from ai_karen_engine.tools.filesystem_tool import FileSystemTool as FileSystemImpl
from ai_karen_engine.tools.text_processing_tool import TextProcessingTool as TextProcessingImpl
from ai_karen_engine.tools.data_analysis_tool import DataAnalysisTool as DataAnalysisImpl

logger = logging.getLogger(__name__)


# ==================== HTTP CLIENT TOOL PLUGIN ====================

class HTTPClientTool(BaseTool):
    """HTTP client tool plugin for making web requests and API calls."""

    def __init__(self):
        super().__init__()
        self._impl = HTTPClientImpl()

    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="http_client",
            description="Make HTTP requests (GET, POST, PUT, DELETE, etc.) to web APIs and services",
            category=ToolCategory.SYSTEM,
            version="1.0.0",
            author="AI Karen",
            parameters=[
                ToolParameter(
                    name="method",
                    type=str,
                    description="HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)",
                    required=True
                ),
                ToolParameter(
                    name="url",
                    type=str,
                    description="Target URL",
                    required=True
                ),
                ToolParameter(
                    name="headers",
                    type=dict,
                    description="Request headers",
                    required=False
                ),
                ToolParameter(
                    name="params",
                    type=dict,
                    description="URL query parameters",
                    required=False
                ),
                ToolParameter(
                    name="json_data",
                    type=dict,
                    description="JSON body data",
                    required=False
                ),
                ToolParameter(
                    name="timeout",
                    type=int,
                    description="Request timeout in seconds",
                    required=False,
                    default=30
                )
            ],
            return_type=dict,
            examples=[
                {
                    "description": "Make GET request",
                    "parameters": {
                        "method": "GET",
                        "url": "https://api.example.com/users"
                    }
                },
                {
                    "description": "Make POST request with JSON",
                    "parameters": {
                        "method": "POST",
                        "url": "https://api.example.com/users",
                        "json_data": {"name": "John", "email": "john@example.com"}
                    }
                }
            ],
            tags=["http", "api", "web", "client", "requests"],
            timeout=30
        )

    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        method = parameters.get("method", "GET")
        url = parameters["url"]
        headers = parameters.get("headers")
        params = parameters.get("params")
        json_data = parameters.get("json_data")
        timeout = parameters.get("timeout", 30)

        result = await self._impl.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json_data=json_data,
            timeout=timeout
        )

        return result


# ==================== FILE SYSTEM TOOL PLUGIN ====================

class FileSystemTool(BaseTool):
    """File system operations tool plugin."""

    def __init__(self):
        super().__init__()
        self._impl = FileSystemImpl()

    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="filesystem",
            description="Perform file system operations (read, write, list, delete, move, copy)",
            category=ToolCategory.SYSTEM,
            version="1.0.0",
            author="AI Karen",
            parameters=[
                ToolParameter(
                    name="operation",
                    type=str,
                    description="Operation to perform (read, write, list, delete, move, copy, info, mkdir)",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=str,
                    description="File or directory path",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type=str,
                    description="Content to write (for write operation)",
                    required=False
                ),
                ToolParameter(
                    name="destination",
                    type=str,
                    description="Destination path (for move/copy operations)",
                    required=False
                ),
                ToolParameter(
                    name="pattern",
                    type=str,
                    description="Pattern for filtering (for list operation)",
                    required=False
                ),
                ToolParameter(
                    name="recursive",
                    type=bool,
                    description="Recursive operation",
                    required=False,
                    default=False
                )
            ],
            return_type=dict,
            examples=[
                {
                    "description": "Read file contents",
                    "parameters": {
                        "operation": "read",
                        "path": "/path/to/file.txt"
                    }
                },
                {
                    "description": "List directory contents",
                    "parameters": {
                        "operation": "list",
                        "path": "/path/to/directory",
                        "pattern": "*.py",
                        "recursive": True
                    }
                }
            ],
            tags=["filesystem", "file", "directory", "io"],
            timeout=30
        )

    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        operation = parameters["operation"]
        path = parameters["path"]

        if operation == "read":
            return await self._impl.read_file(path)

        elif operation == "write":
            content = parameters.get("content", "")
            overwrite = parameters.get("overwrite", True)
            return await self._impl.write_file(path, content, overwrite=overwrite)

        elif operation == "list":
            pattern = parameters.get("pattern")
            recursive = parameters.get("recursive", False)
            return await self._impl.list_directory(path, pattern=pattern, recursive=recursive)

        elif operation == "delete":
            return await self._impl.delete_file(path)

        elif operation == "move":
            destination = parameters["destination"]
            return await self._impl.move_file(path, destination)

        elif operation == "copy":
            destination = parameters["destination"]
            return await self._impl.copy_file(path, destination)

        elif operation == "info":
            return await self._impl.get_file_info(path)

        elif operation == "mkdir":
            parents = parameters.get("parents", True)
            return await self._impl.create_directory(path, parents=parents)

        else:
            raise ValueError(f"Unknown operation: {operation}")


# ==================== TEXT PROCESSING TOOL PLUGIN ====================

class TextProcessingTool(BaseTool):
    """Text processing and analysis tool plugin."""

    def __init__(self):
        super().__init__()
        self._impl = TextProcessingImpl()

    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="text_processing",
            description="Process and analyze text (clean, tokenize, extract patterns, statistics)",
            category=ToolCategory.ANALYTICS,
            version="1.0.0",
            author="AI Karen",
            parameters=[
                ToolParameter(
                    name="operation",
                    type=str,
                    description="Operation to perform (clean, tokenize_words, tokenize_sentences, stats, extract_emails, extract_urls, similarity, hash)",
                    required=True
                ),
                ToolParameter(
                    name="text",
                    type=str,
                    description="Input text",
                    required=True
                ),
                ToolParameter(
                    name="text2",
                    type=str,
                    description="Second text (for similarity operation)",
                    required=False
                ),
                ToolParameter(
                    name="lowercase",
                    type=bool,
                    description="Convert to lowercase",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="remove_punctuation",
                    type=bool,
                    description="Remove punctuation",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="method",
                    type=str,
                    description="Method for operation (e.g., 'jaccard' for similarity)",
                    required=False
                )
            ],
            return_type=dict,
            examples=[
                {
                    "description": "Get text statistics",
                    "parameters": {
                        "operation": "stats",
                        "text": "This is a sample text for analysis."
                    }
                },
                {
                    "description": "Extract email addresses",
                    "parameters": {
                        "operation": "extract_emails",
                        "text": "Contact us at info@example.com or support@example.org"
                    }
                }
            ],
            tags=["text", "nlp", "processing", "analysis"],
            timeout=30
        )

    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        operation = parameters["operation"]
        text = parameters["text"]

        if operation == "clean":
            return await self._impl.clean_text(
                text,
                remove_whitespace=True,
                remove_punctuation=parameters.get("remove_punctuation", False),
                lowercase=parameters.get("lowercase", False)
            )

        elif operation == "tokenize_words":
            return await self._impl.tokenize_words(
                text,
                lowercase=parameters.get("lowercase", True),
                remove_punctuation=parameters.get("remove_punctuation", True)
            )

        elif operation == "tokenize_sentences":
            return await self._impl.tokenize_sentences(text)

        elif operation == "stats":
            return await self._impl.get_text_stats(text)

        elif operation == "extract_emails":
            return await self._impl.extract_emails(text)

        elif operation == "extract_urls":
            return await self._impl.extract_urls(text)

        elif operation == "extract_phones":
            return await self._impl.extract_phone_numbers(text)

        elif operation == "similarity":
            text2 = parameters["text2"]
            method = parameters.get("method", "jaccard")
            return await self._impl.calculate_similarity(text, text2, method=method)

        elif operation == "hash":
            algorithm = parameters.get("algorithm", "sha256")
            return await self._impl.generate_text_hash(text, algorithm=algorithm)

        else:
            raise ValueError(f"Unknown operation: {operation}")


# ==================== DATA ANALYSIS TOOL PLUGIN ====================

class DataAnalysisTool(BaseTool):
    """Data analysis and statistics tool plugin."""

    def __init__(self):
        super().__init__()
        self._impl = DataAnalysisImpl()

    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="data_analysis",
            description="Analyze data with statistical methods (statistics, aggregation, filtering, correlation)",
            category=ToolCategory.ANALYTICS,
            version="1.0.0",
            author="AI Karen",
            parameters=[
                ToolParameter(
                    name="operation",
                    type=str,
                    description="Operation to perform (statistics, count_values, filter, group_by, aggregate, sort, correlation, outliers, normalize)",
                    required=True
                ),
                ToolParameter(
                    name="data",
                    type=list,
                    description="Input data (list of numbers or dictionaries)",
                    required=True
                ),
                ToolParameter(
                    name="key",
                    type=str,
                    description="Key for grouping/sorting",
                    required=False
                ),
                ToolParameter(
                    name="filters",
                    type=dict,
                    description="Filters for data (field: value pairs)",
                    required=False
                ),
                ToolParameter(
                    name="aggregations",
                    type=dict,
                    description="Aggregations to perform (field: operation pairs)",
                    required=False
                ),
                ToolParameter(
                    name="method",
                    type=str,
                    description="Method for operation (e.g., 'iqr' for outliers)",
                    required=False
                )
            ],
            return_type=dict,
            examples=[
                {
                    "description": "Calculate statistics",
                    "parameters": {
                        "operation": "statistics",
                        "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    }
                },
                {
                    "description": "Group and aggregate data",
                    "parameters": {
                        "operation": "aggregate",
                        "data": [
                            {"category": "A", "value": 10},
                            {"category": "A", "value": 20},
                            {"category": "B", "value": 15}
                        ],
                        "key": "category",
                        "aggregations": {"value": "sum"}
                    }
                }
            ],
            tags=["data", "statistics", "analysis", "aggregation"],
            timeout=30
        )

    async def _execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        operation = parameters["operation"]
        data = parameters["data"]

        if operation == "statistics":
            return await self._impl.calculate_statistics(data)

        elif operation == "count_values":
            top_n = parameters.get("top_n")
            return await self._impl.count_values(data, top_n=top_n)

        elif operation == "filter":
            filters = parameters.get("filters", {})
            return await self._impl.filter_data(data, filters)

        elif operation == "group_by":
            key = parameters["key"]
            return await self._impl.group_by(data, key)

        elif operation == "aggregate":
            group_by = parameters["key"]
            aggregations = parameters["aggregations"]
            return await self._impl.aggregate(data, group_by, aggregations)

        elif operation == "sort":
            key = parameters["key"]
            reverse = parameters.get("reverse", False)
            return await self._impl.sort_data(data, key, reverse=reverse)

        elif operation == "correlation":
            # Expects data to be [x_values, y_values]
            if len(data) != 2:
                raise ValueError("Correlation requires exactly 2 lists of values")
            return await self._impl.calculate_correlation(data[0], data[1])

        elif operation == "outliers":
            method = parameters.get("method", "iqr")
            threshold = parameters.get("threshold", 1.5)
            return await self._impl.detect_outliers(data, method=method, threshold=threshold)

        elif operation == "normalize":
            method = parameters.get("method", "minmax")
            return await self._impl.normalize_data(data, method=method)

        else:
            raise ValueError(f"Unknown operation: {operation}")


# ==================== TOOL REGISTRATION ====================

def get_production_tools() -> List[BaseTool]:
    """
    Get all production tool plugins.

    Returns:
        List of production tool instances
    """
    return [
        HTTPClientTool(),
        FileSystemTool(),
        TextProcessingTool(),
        DataAnalysisTool()
    ]


def register_production_tools(tool_registry):
    """
    Register all production tools with the tool registry.

    Args:
        tool_registry: ToolRegistry instance
    """
    tools = get_production_tools()
    registered_count = 0

    for tool in tools:
        try:
            tool_registry.register_tool(tool)
            registered_count += 1
            logger.info(f"Registered production tool: {tool.metadata.name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool.metadata.name}: {e}")

    logger.info(f"Registered {registered_count}/{len(tools)} production tools")
    return registered_count


__all__ = [
    "HTTPClientTool",
    "FileSystemTool",
    "TextProcessingTool",
    "DataAnalysisTool",
    "get_production_tools",
    "register_production_tools"
]
