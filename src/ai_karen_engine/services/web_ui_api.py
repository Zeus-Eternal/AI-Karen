"""
Web UI API transformation utilities.

This module provides functions to transform requests and responses between
the web UI format and the backend service format.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_karen_engine.models.web_ui_types import (
    ChatProcessRequest,
    ChatProcessResponse,
    WebUIMemoryQuery,
    WebUIMemoryEntry,
    WebUIMemoryQueryResponse,
    WebUIMemoryStoreRequest,
    WebUIMemoryStoreResponse,
    WebUIPluginInfo,
    WebUISystemMetrics,
    WebUIUsageAnalytics,
    WebUIHealthCheck
)
from ai_karen_engine.models.shared_types import FlowInput, FlowOutput, HandleUserMessageResult
from ai_karen_engine.api_routes.ai_orchestrator_routes import ConversationProcessingRequest
from ai_karen_engine.api_routes.memory_routes import MemQuery, MemCommit, ContextHit
from ai_karen_engine.services.memory_service import UISource, WebUIMemoryQuery as ServiceWebUIMemoryQuery

# Import the new transformation utilities
from ai_karen_engine.services.memory_transformation_utils import MemoryTransformationUtils
from ai_karen_engine.services.chat_transformation_utils import ChatTransformationUtils

logger = logging.getLogger(__name__)

# Force reload - updated transformation service with new utilities


class WebUITransformationService:
    """Service for transforming data between web UI and backend formats."""
    
    @staticmethod
    def transform_chat_request_to_backend(
        web_ui_request: ChatProcessRequest
    ) -> Tuple[ConversationProcessingRequest, FlowInput]:
        """Transform web UI chat request to backend format."""
        try:
            return ChatTransformationUtils.transform_chat_request_to_backend(web_ui_request)

        except Exception as e:
            logger.error(f"Failed to transform chat request: {e}")
            raise ValueError(f"Invalid chat request format: {e}")

    @staticmethod
    def transform_backend_response_to_chat(
        backend_response: FlowOutput
    ) -> ChatProcessResponse:
        """Transform backend response to web UI chat format."""
        try:
            return ChatTransformationUtils.transform_backend_response_to_chat(backend_response)

        except Exception as e:
            logger.error(f"Failed to transform backend response: {e}")
            raise ValueError(f"Invalid backend response format: {e}")
    
    @staticmethod
    def transform_web_ui_memory_query(
        web_ui_query: WebUIMemoryQuery
    ) -> ServiceWebUIMemoryQuery:
        """Transform web UI memory query to backend format with enhanced validation."""
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
                    cleaned_tag = tag.strip().lower()
                    if cleaned_tag and cleaned_tag not in processed_tags:
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
    def validate_memory_query_request(web_ui_query: WebUIMemoryQuery) -> List[str]:
        """Validate memory query request and return list of error messages."""
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
    def transform_memory_entries_to_web_ui(
        backend_memories: List[ContextHit],
        query_time_ms: float = 0.0
    ) -> WebUIMemoryQueryResponse:
        """Transform backend memory entries to web UI format with JavaScript compatibility."""
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
                    js_timestamp = WebUITransformationService.ensure_js_compatible_timestamp(memory.created_at)

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
        """Transform backend memory store response to web UI format."""
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
    def transform_plugin_info_to_web_ui(
        backend_plugins: List[Dict[str, Any]]
    ) -> List[WebUIPluginInfo]:
        """Transform backend plugin info to web UI format."""
        try:
            web_ui_plugins = []
            for plugin in backend_plugins:
                web_ui_plugins.append(WebUIPluginInfo(
                    name=plugin.get("name", ""),
                    description=plugin.get("description", ""),
                    category=plugin.get("category", "general"),
                    enabled=plugin.get("enabled", False),
                    version=plugin.get("version")
                ))
            
            return web_ui_plugins
            
        except Exception as e:
            logger.error(f"Failed to transform plugin info: {e}")
            raise ValueError(f"Invalid plugin info format: {e}")
    
    @staticmethod
    def transform_system_metrics_to_web_ui(
        backend_metrics: Dict[str, Any]
    ) -> WebUISystemMetrics:
        """Transform backend system metrics to web UI format."""
        try:
            return WebUISystemMetrics(
                cpu_usage=backend_metrics.get("cpu_usage", 0.0),
                memory_usage=backend_metrics.get("memory_usage", 0.0),
                disk_usage=backend_metrics.get("disk_usage", 0.0),
                active_sessions=backend_metrics.get("active_sessions", 0),
                total_requests=backend_metrics.get("total_requests", 0),
                error_rate=backend_metrics.get("error_rate", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Failed to transform system metrics: {e}")
            raise ValueError(f"Invalid system metrics format: {e}")
    
    @staticmethod
    def transform_usage_analytics_to_web_ui(
        backend_analytics: Dict[str, Any]
    ) -> WebUIUsageAnalytics:
        """Transform backend usage analytics to web UI format."""
        try:
            return WebUIUsageAnalytics(
                total_conversations=backend_analytics.get("total_conversations", 0),
                total_messages=backend_analytics.get("total_messages", 0),
                average_session_duration=backend_analytics.get("average_session_duration", 0.0),
                most_used_features=backend_analytics.get("most_used_features", []),
                user_activity=backend_analytics.get("user_activity", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to transform usage analytics: {e}")
            raise ValueError(f"Invalid usage analytics format: {e}")
    
    @staticmethod
    def transform_health_check_to_web_ui(
        backend_health: Dict[str, Any]
    ) -> WebUIHealthCheck:
        """Transform backend health check to web UI format."""
        try:
            return WebUIHealthCheck(
                status=backend_health.get("status", "unknown"),
                services=backend_health.get("services", {}),
                timestamp=backend_health.get("timestamp", datetime.utcnow().isoformat()),
                uptime=backend_health.get("uptime", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Failed to transform health check: {e}")
            raise ValueError(f"Invalid health check format: {e}")
    
    @staticmethod
    def convert_timestamp_to_js_compatible(timestamp: datetime) -> int:
        """Convert Python datetime to JavaScript-compatible Unix timestamp in milliseconds."""
        return int(timestamp.timestamp() * 1000)
    
    @staticmethod
    def convert_js_timestamp_to_datetime(timestamp: int) -> datetime:
        """Convert JavaScript Unix timestamp (milliseconds) to Python datetime."""
        return datetime.fromtimestamp(timestamp / 1000)
    
    @staticmethod
    def convert_timestamp_to_js_compatible_from_float(timestamp: float) -> int:
        """Convert Python timestamp float to JavaScript-compatible Unix timestamp in milliseconds."""
        return int(timestamp * 1000)
    
    @staticmethod
    def ensure_js_compatible_timestamp(timestamp: Any) -> int:
        """Ensure timestamp is in JavaScript-compatible format (milliseconds)."""
        if isinstance(timestamp, datetime):
            return WebUITransformationService.convert_timestamp_to_js_compatible(timestamp)
        elif isinstance(timestamp, (int, float)):
            # Check if it's already in milliseconds (rough heuristic: > year 2000 in seconds)
            if timestamp > 946684800:  # Jan 1, 2000 in seconds
                if timestamp < 946684800000:  # Less than Jan 1, 2000 in milliseconds, so it's in seconds
                    return int(timestamp * 1000)
                else:
                    return int(timestamp)  # Already in milliseconds
            else:
                return int(timestamp * 1000)  # Assume it's in seconds
        else:
            # Fallback to current time
            logger.warning(f"Invalid timestamp type {type(timestamp)}, using current time")
            return int(datetime.utcnow().timestamp() * 1000)
    
    @staticmethod
    def sanitize_error_response(error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize error response to remove sensitive information."""
        sanitized = {}
        
        # Only include safe fields
        safe_fields = [
            "error", "message", "type", "timestamp", "request_id",
            "validation_errors", "field", "invalid_value"
        ]
        
        for key, value in error_details.items():
            if key in safe_fields:
                sanitized[key] = value
            elif key == "details" and isinstance(value, dict):
                # Recursively sanitize nested details
                sanitized[key] = WebUITransformationService.sanitize_error_response(value)
        
        return sanitized