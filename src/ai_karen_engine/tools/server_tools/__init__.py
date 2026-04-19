"""
Server Tools Package for AI-Karen
Dedicated tools system for prompt-first architecture
"""

import logging
logger = logging.getLogger(__name__)

# Search Server Tool
try:
    from .search_tool import SearchServerTool
except ImportError as e:
    logger.warning(f"Could not import SearchServerTool: {e}")
    class SearchServerTool: pass

# Documents Server Tool
try:
    from .documents_tool import DocumentsServerTool
except ImportError as e:
    logger.warning(f"Could not import DocumentsServerTool: {e}")
    class DocumentsServerTool: pass

# Excel Server Tool
try:
    from .excel_tool import ExcelServerTool
except ImportError as e:
    logger.warning(f"Could not import ExcelServerTool: {e}")
    class ExcelServerTool: pass

# Image Server Tool
try:
    from .image_tool import ImageServerTool
except ImportError as e:
    logger.warning(f"Could not import ImageServerTool: {e}")
    class ImageServerTool: pass

__all__ = [
    'SearchServerTool',
    'DocumentsServerTool', 
    'ExcelServerTool',
    'ImageServerTool'
]
