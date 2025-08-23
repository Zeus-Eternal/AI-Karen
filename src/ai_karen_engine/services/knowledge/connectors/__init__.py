"""
Knowledge connectors for ingesting data from various sources.
"""

from .base_connector import BaseConnector, IngestionResult, ChangeDetection
from .file_connector import FileConnector
from .git_connector import GitConnector
from .database_connector import DatabaseConnector
from .documentation_connector import DocumentationConnector
from .ingestion_pipeline import IngestionPipeline

__all__ = [
    "BaseConnector",
    "IngestionResult", 
    "ChangeDetection",
    "FileConnector",
    "GitConnector",
    "DatabaseConnector",
    "DocumentationConnector",
    "IngestionPipeline"
]