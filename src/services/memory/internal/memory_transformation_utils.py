"""
Memory service transformation utilities for Web UI API.

This module provides functions to transform memory requests and responses between
the web UI format and the backend service format, with enhanced validation and
JavaScript compatibility features.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_karen_engine.models.web_ui_types import (
    WebUIMemoryQuery,
    WebUIMemoryEntry,
    WebUIMemoryQueryResponse,
    WebUIMemoryStoreRequest,
    WebUIMemoryStoreResponse,
)
from src.services.memory_service import (
    WebUIMemoryQuery as ServiceWebUIMemoryQuery,
    UISource,
)
from ai_karen_engine.api_routes.memory_routes import (
    MemQuery,
    MemCommit,
    ContextHit,
)

logger = logging.getLogger(__name__)


class MemoryTransformationUtils:
    """Utility class for memory service transformations."""
    
    @staticmethod
    def transform_web_ui_memory_query(
        web_ui_query: WebUIMemoryQuery
    ) -> ServiceWebUIMemoryQuery:
        """
        Transform web UI memory query to backend service format.
        
        Args:
            web_ui_query: WebUIMemoryQuery from the web UI
            
        Returns:
            ServiceWebUIMemoryQuery for the backend service
            
        Raises:
            ValueError: If the query format is invalid
        """
        try:
            # Validate and convert time range if provided
            time_range = None
            if web_ui_query.time_range:
                if len(web_ui_query.time_range) != 2:
                    raise ValueError("Time range must contain exactly 2 datetime elements")
                
                time_range_start = web_ui_query.time_range[0]
                time_range_end = web_ui_query.time_range[1]
                
                # Additional validation for time range
                if time_range_start >= time_range_end:
                    raise ValueError("Start time must be before end time")
                
                # Check if time range is in the future (warn but don't fail)
                current_time = datetime.utcnow()
                if time_range_start > current_time:
                    logger.warning("Time range start is in the future, this may return no results")
                
                time_range = (time_range_start, time_range_end)
            
            # Process and validate tags
            processed_tags = []
            if web_ui_query.tags:
                for tag in web_ui_query.tags:
                    if isinstance(tag, str) and tag.strip():
                        cleaned_tag = tag.strip().lower()
                        if cleaned_tag not in processed_tags:
                            processed_tags.append(cleaned_tag)
            
            # Validate similarity threshold
            similarity_threshold = web_ui_query.similarity_threshold or 0.7
            if not (0.0 <= similarity_threshold <= 1.0):
                raise ValueError("Similarity threshold must be between 0.0 and 1.0")
            
            # Validate top_k
            top_k = web_ui_query.top_k or 5
            if not (1 <= top_k <= 100):
                raise ValueError("top_k must be between 1 and 100")
            
            return ServiceWebUIMemoryQuery(
                text=web_ui_query.text.strip(),
                user_id=web_ui_query.user_id,
                session_id=web_ui_query.session_id,
                ui_source=UISource.WEB,
                tags=processed_tags,
                time_range=time_range,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                include_embeddings=False
            )
            
        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to transform memory query: {e}")
            raise ValueError(f"Invalid memory query format: {e}")
    
    @staticmethod
    def transform_web_ui_memory_query_to_api_request(
        web_ui_query: WebUIMemoryQuery
    ) -> MemQuery:
        """Transform web UI memory query to API request format."""
        try:
            user_id = web_ui_query.user_id or web_ui_query.session_id or "anonymous"
            return MemQuery(
                user_id=user_id,
                org_id=None,
                query=web_ui_query.text,
                top_k=web_ui_query.top_k or 12,
            )
        except Exception as e:
            logger.error(f"Failed to transform web UI query to API request: {e}")
            raise ValueError(f"Invalid web UI query format: {e}")
    
    @staticmethod
    def transform_memory_entries_to_web_ui(
        backend_memories: List[ContextHit],
        query_time_ms: float = 0.0
    ) -> WebUIMemoryQueryResponse:
        """
        Transform backend memory entries to web UI format with JavaScript compatibility.
        
        Args:
            backend_memories: List of ContextHit from backend
            query_time_ms: Query execution time in milliseconds
            
        Returns:
            WebUIMemoryQueryResponse for the web UI
        """
        try:
            web_ui_entries = []
            
            # Handle empty memories case
            if not backend_memories:
                logger.info("No memories found, returning empty array")
                return WebUIMemoryQueryResponse(
                    memories=[],
                    total_count=0,
                    query_time_ms=query_time_ms
                )
            
            for memory in backend_memories:
                try:
                    # Convert timestamp to JavaScript-compatible format (milliseconds)
                    js_timestamp = MemoryTransformationUtils.ensure_js_compatible_timestamp(memory.created_at)

                    # Ensure content is not empty
                    content = memory.text.strip() if memory.text else ""
                    if not content:
                        logger.warning(f"Skipping memory {memory.id} with empty content")
                        continue
                    
                    # Clean and validate tags
                    cleaned_tags = []
                    if memory.tags:
                        for tag in memory.tags:
                            if isinstance(tag, str) and tag.strip():
                                cleaned_tag = tag.strip().lower()
                                if cleaned_tag not in cleaned_tags:
                                    cleaned_tags.append(cleaned_tag)

                    # Ensure metadata is a dictionary
                    metadata = memory.meta if isinstance(memory.meta, dict) else {}

                    # Validate and clamp similarity score
                    similarity_score = memory.score
                    if similarity_score is not None:
                        if not isinstance(similarity_score, (int, float)):
                            logger.warning(f"Invalid similarity score type for memory {memory.id}: {type(similarity_score)}")
                            similarity_score = None
                        elif similarity_score < 0.0:
                            similarity_score = 0.0
                        elif similarity_score > 1.0:
                            similarity_score = 1.0
                        else:
                            similarity_score = float(similarity_score)
                    
                    web_ui_entry = WebUIMemoryEntry(
                        id=str(memory.id),  # Ensure ID is string
                        content=content,
                        metadata=metadata,
                        timestamp=js_timestamp,
                        similarity_score=similarity_score,
                        tags=cleaned_tags,
                        user_id=memory.user_id,
                        session_id=None
                    )
                    
                    web_ui_entries.append(web_ui_entry)
                    
                except Exception as e:
                    logger.error(f"Failed to transform memory entry {getattr(memory, 'id', 'unknown')}: {e}")
                    # Skip this entry but continue with others
                    continue
            
            # Ensure we always return valid response structure
            response = WebUIMemoryQueryResponse(
                memories=web_ui_entries,
                total_count=len(web_ui_entries),
                query_time_ms=max(0.0, float(query_time_ms))  # Ensure non-negative
            )
            
            logger.info(f"Transformed {len(backend_memories)} backend memories to {len(web_ui_entries)} web UI entries")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to transform memory entries: {e}")
            # Return empty response instead of raising error
            return WebUIMemoryQueryResponse(
                memories=[],
                total_count=0,
                query_time_ms=max(0.0, float(query_time_ms)) if query_time_ms else 0.0
            )
    
    @staticmethod
    def transform_web_ui_memory_store_request(
        web_ui_request: WebUIMemoryStoreRequest
    ) -> MemCommit:
        """Transform web UI memory store request to backend format."""
        try:
            user_id = web_ui_request.user_id or web_ui_request.session_id or "anonymous"
            return MemCommit(
                user_id=user_id,
                org_id=None,
                text=web_ui_request.content,
                tags=web_ui_request.tags or [],
                importance=5,
                decay="short",
            )
        except Exception as e:
            logger.error(f"Failed to transform memory store request: {e}")
            raise ValueError(f"Invalid memory store request format: {e}")
    
    @staticmethod
    def transform_memory_store_response_to_web_ui(
        backend_response: Dict[str, Any]
    ) -> WebUIMemoryStoreResponse:
        """
        Transform backend memory store response to web UI format.
        
        Args:
            backend_response: Response from backend memory store API
            
        Returns:
            WebUIMemoryStoreResponse for the web UI
        """
        try:
            return WebUIMemoryStoreResponse(
                success=backend_response.get("success", False),
                memory_id=backend_response.get("memory_id"),
                message=backend_response.get("message", "Memory operation completed")
            )
            
        except Exception as e:
            logger.error(f"Failed to transform memory store response: {e}")
            raise ValueError(f"Invalid memory store response format: {e}")
    
    @staticmethod
    def convert_timestamp_to_js_compatible(timestamp: datetime) -> int:
        """
        Convert Python datetime to JavaScript-compatible Unix timestamp in milliseconds.
        
        Args:
            timestamp: Python datetime object
            
        Returns:
            Unix timestamp in milliseconds (int)
        """
        return int(timestamp.timestamp() * 1000)
    
    @staticmethod
    def convert_js_timestamp_to_datetime(timestamp: int) -> datetime:
        """
        Convert JavaScript Unix timestamp (milliseconds) to Python datetime.
        
        Args:
            timestamp: Unix timestamp in milliseconds
            
        Returns:
            Python datetime object
        """
        return datetime.fromtimestamp(timestamp / 1000)
    
    @staticmethod
    def convert_timestamp_to_js_compatible_from_float(timestamp: float) -> int:
        """
        Convert Python timestamp float to JavaScript-compatible Unix timestamp in milliseconds.
        
        Args:
            timestamp: Python timestamp as float (seconds since epoch)
            
        Returns:
            Unix timestamp in milliseconds (int)
        """
        return int(timestamp * 1000)
    
    @staticmethod
    def ensure_js_compatible_timestamp(timestamp: Any) -> int:
        """
        Ensure timestamp is in JavaScript-compatible format (milliseconds).
        
        This function handles various timestamp formats and converts them to
        JavaScript-compatible Unix timestamps in milliseconds.
        
        Args:
            timestamp: Timestamp in various formats (datetime, int, float, str)
            
        Returns:
            Unix timestamp in milliseconds (int)
        """
        if isinstance(timestamp, datetime):
            return MemoryTransformationUtils.convert_timestamp_to_js_compatible(timestamp)
        elif isinstance(timestamp, (int, float)):
            # Check if it's already in milliseconds (rough heuristic: > year 2000 in seconds)
            if timestamp > 946684800:  # Jan 1, 2000 in seconds
                if timestamp < 946684800000:  # Less than Jan 1, 2000 in milliseconds, so it's in seconds
                    return int(timestamp * 1000)
                else:
                    return int(timestamp)  # Already in milliseconds
            else:
                return int(timestamp * 1000)  # Assume it's in seconds
        elif isinstance(timestamp, str):
            try:
                # Try to parse as ISO format datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return MemoryTransformationUtils.convert_timestamp_to_js_compatible(dt)
            except ValueError:
                try:
                    # Try to parse as timestamp float
                    ts_float = float(timestamp)
                    return MemoryTransformationUtils.ensure_js_compatible_timestamp(ts_float)
                except ValueError:
                    logger.warning(f"Could not parse timestamp string: {timestamp}, using current time")
                    return int(datetime.utcnow().timestamp() * 1000)
        else:
            # Fallback to current time
            logger.warning(f"Invalid timestamp type {type(timestamp)}, using current time")
            return int(datetime.utcnow().timestamp() * 1000)
    
    @staticmethod
    def create_metadata_transformation_helpers() -> Dict[str, Any]:
        """
        Create metadata transformation helper functions.
        
        Returns:
            Dictionary of helper functions for metadata transformation
        """
        def clean_metadata_for_js(metadata: Dict[str, Any]) -> Dict[str, Any]:
            """Clean metadata for JavaScript compatibility."""
            cleaned = {}
            for key, value in metadata.items():
                # Ensure keys are strings
                clean_key = str(key)
                
                # Handle different value types
                if isinstance(value, datetime):
                    cleaned[clean_key] = value.isoformat()
                elif isinstance(value, (list, tuple)):
                    # Convert to list and clean elements
                    cleaned[clean_key] = [
                        item.isoformat() if isinstance(item, datetime) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    # Recursively clean nested dictionaries
                    cleaned[clean_key] = clean_metadata_for_js(value)
                else:
                    cleaned[clean_key] = value
            
            return cleaned
        
        def extract_search_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
            """Extract search-relevant metadata."""
            search_metadata = {}
            
            # Extract importance score
            if 'importance_score' in metadata:
                search_metadata['importance'] = metadata['importance_score']
            
            # Extract memory type
            if 'memory_type' in metadata:
                search_metadata['type'] = metadata['memory_type']
            
            # Extract UI source
            if 'ui_source' in metadata:
                search_metadata['source'] = metadata['ui_source']
            
            # Extract conversation context
            if 'conversation_id' in metadata:
                search_metadata['conversation'] = metadata['conversation_id']
            
            return search_metadata
        
        def merge_metadata_safely(base_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> Dict[str, Any]:
            """Safely merge metadata dictionaries."""
            merged = base_metadata.copy()
            
            for key, value in new_metadata.items():
                if key in merged:
                    # Handle conflicts by prefixing with 'new_'
                    merged[f"new_{key}"] = value
                else:
                    merged[key] = value
            
            return merged
        
        return {
            'clean_metadata_for_js': clean_metadata_for_js,
            'extract_search_metadata': extract_search_metadata,
            'merge_metadata_safely': merge_metadata_safely
        }
    
    @staticmethod
    def validate_memory_query_request(web_ui_query: WebUIMemoryQuery) -> List[str]:
        """
        Validate memory query request and return list of error messages.
        
        Args:
            web_ui_query: WebUIMemoryQuery to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate query text
        if not web_ui_query.text or not web_ui_query.text.strip():
            errors.append("Query text cannot be empty")
        elif len(web_ui_query.text.strip()) > 1000:
            errors.append("Query text cannot exceed 1000 characters")
        
        # Validate user_id format
        if web_ui_query.user_id and len(web_ui_query.user_id) > 100:
            errors.append("User ID cannot exceed 100 characters")
        
        # Validate session_id format
        if web_ui_query.session_id and len(web_ui_query.session_id) > 100:
            errors.append("Session ID cannot exceed 100 characters")
        
        # Validate tags
        if web_ui_query.tags:
            if len(web_ui_query.tags) > 20:
                errors.append("Maximum 20 tags allowed")
            
            for i, tag in enumerate(web_ui_query.tags):
                if not isinstance(tag, str):
                    errors.append(f"Tag at index {i} must be a string")
                elif len(tag.strip()) > 50:
                    errors.append(f"Tag at index {i} cannot exceed 50 characters")
        
        # Validate time range
        if web_ui_query.time_range:
            if not isinstance(web_ui_query.time_range, list) or len(web_ui_query.time_range) != 2:
                errors.append("Time range must be a list with exactly 2 datetime elements")
            else:
                try:
                    start_time, end_time = web_ui_query.time_range
                    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                        errors.append("Time range elements must be datetime objects")
                    elif start_time >= end_time:
                        errors.append("Start time must be before end time")
                    elif (end_time - start_time).days > 365:
                        errors.append("Time range cannot exceed 365 days")
                except (ValueError, TypeError):
                    errors.append("Invalid time range format")
        
        # Validate top_k
        if web_ui_query.top_k is not None:
            if not isinstance(web_ui_query.top_k, int) or web_ui_query.top_k < 1 or web_ui_query.top_k > 100:
                errors.append("top_k must be an integer between 1 and 100")
        
        # Validate similarity_threshold
        if web_ui_query.similarity_threshold is not None:
            if not isinstance(web_ui_query.similarity_threshold, (int, float)):
                errors.append("similarity_threshold must be a number")
            elif not (0.0 <= web_ui_query.similarity_threshold <= 1.0):
                errors.append("similarity_threshold must be between 0.0 and 1.0")
        
        # Validate metadata_filter
        if web_ui_query.metadata_filter:
            if not isinstance(web_ui_query.metadata_filter, dict):
                errors.append("metadata_filter must be a dictionary")
            elif len(web_ui_query.metadata_filter) > 10:
                errors.append("Maximum 10 metadata filter keys allowed")
            else:
                for key, value in web_ui_query.metadata_filter.items():
                    if not isinstance(key, str):
                        errors.append(f"Metadata filter key '{key}' must be a string")
                    elif len(key) > 100:
                        errors.append(f"Metadata filter key '{key}' cannot exceed 100 characters")
        
        return errors
    
    @staticmethod
    def create_query_performance_tracker():
        """
        Create a performance tracker for memory queries.
        
        Returns:
            Performance tracker context manager
        """
        class QueryPerformanceTracker:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.query_metadata = {}
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.end_time = time.time()
            
            def get_duration_ms(self) -> float:
                """Get query duration in milliseconds."""
                if self.start_time and self.end_time:
                    return (self.end_time - self.start_time) * 1000
                return 0.0
            
            def add_metadata(self, key: str, value: Any):
                """Add metadata to the performance tracker."""
                self.query_metadata[key] = value
            
            def get_performance_summary(self) -> Dict[str, Any]:
                """Get performance summary."""
                return {
                    'duration_ms': self.get_duration_ms(),
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'metadata': self.query_metadata
                }
        
        return QueryPerformanceTracker()


# Convenience functions for direct use
def transform_web_ui_memory_query(web_ui_query: WebUIMemoryQuery) -> ServiceWebUIMemoryQuery:
    """Transform web UI memory query to backend service format."""
    return MemoryTransformationUtils.transform_web_ui_memory_query(web_ui_query)


def transform_memory_entries_to_web_ui(
    backend_memories: List[ContextHit],
    query_time_ms: float = 0.0
) -> WebUIMemoryQueryResponse:
    """Transform backend memory entries to web UI format."""
    return MemoryTransformationUtils.transform_memory_entries_to_web_ui(backend_memories, query_time_ms)


def ensure_js_compatible_timestamp(timestamp: Any) -> int:
    """Ensure timestamp is in JavaScript-compatible format."""
    return MemoryTransformationUtils.ensure_js_compatible_timestamp(timestamp)


def validate_memory_query_request(web_ui_query: WebUIMemoryQuery) -> List[str]:
    """Validate memory query request."""
    return MemoryTransformationUtils.validate_memory_query_request(web_ui_query)


__all__ = [
    "MemoryTransformationUtils",
    "transform_web_ui_memory_query",
    "transform_memory_entries_to_web_ui", 
    "ensure_js_compatible_timestamp",
    "validate_memory_query_request"
]