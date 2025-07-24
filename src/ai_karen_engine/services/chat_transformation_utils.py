"""
Chat service transformation utilities for Web UI API.

This module provides functions to transform chat requests and responses between
the web UI format and the backend AI orchestrator format, with enhanced validation
and conversation history management.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ai_karen_engine.models.web_ui_types import (
    ChatProcessRequest,
    ChatProcessResponse,
)
from ai_karen_engine.models.shared_types import (
    FlowInput,
    FlowOutput,
    HandleUserMessageResult,
    ChatMessage,
    MessageRole,
    KarenSettings,
    AiData,
    MemoryContext,
    PluginInfo,
)
from ai_karen_engine.api_routes.ai_orchestrator_routes import (
    ConversationProcessingRequest,
    FlowResponse,
)

logger = logging.getLogger(__name__)


class ChatTransformationUtils:
    """Utility class for chat service transformations."""
    
    @staticmethod
    def transform_chat_request_to_backend(
        web_ui_request: ChatProcessRequest
    ) -> Tuple[ConversationProcessingRequest, FlowInput]:
        """
        Transform web UI chat request to backend format.
        
        Args:
            web_ui_request: ChatProcessRequest from the web UI
            
        Returns:
            Tuple of (ConversationProcessingRequest, FlowInput) for the backend
            
        Raises:
            ValueError: If the request format is invalid
        """
        try:
            # Validate the request
            validation_errors = ChatTransformationUtils.validate_chat_request(web_ui_request)
            if validation_errors:
                raise ValueError(f"Invalid chat request: {'; '.join(validation_errors)}")
            
            # Transform conversation history to proper format
            transformed_history = ChatTransformationUtils.transform_conversation_history_to_backend(
                web_ui_request.conversation_history
            )
            
            # Extract user settings
            user_settings = ChatTransformationUtils.extract_user_settings(web_ui_request.user_settings)
            
            # Create backend conversation processing request
            backend_request = ConversationProcessingRequest(
                prompt=web_ui_request.message,
                conversation_history=transformed_history,
                user_settings=user_settings,
                context={
                    "relevant_memories": web_ui_request.relevant_memories,
                    "ui_source": "web_ui",
                    "session_id": web_ui_request.session_id,
                    "user_id": web_ui_request.user_id
                },
                session_id=web_ui_request.session_id,
                include_memories=True,
                include_insights=True
            )
            
            # Create flow input for AI orchestrator
            flow_input = FlowInput(
                prompt=web_ui_request.message,
                conversation_history=transformed_history,
                user_settings=user_settings,
                context={
                    "relevant_memories": web_ui_request.relevant_memories,
                    "ui_source": "web_ui"
                },
                user_id=web_ui_request.user_id or "anonymous",
                session_id=web_ui_request.session_id,
                # Extract memory context from relevant memories
                context_from_memory=ChatTransformationUtils.transform_relevant_memories_to_context(
                    web_ui_request.relevant_memories
                )
            )
            
            return backend_request, flow_input
            
        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to transform chat request: {e}")
            raise ValueError(f"Invalid chat request format: {e}")
    
    @staticmethod
    def transform_backend_response_to_chat(
        backend_response: FlowOutput
    ) -> ChatProcessResponse:
        """
        Transform backend response to web UI chat format.
        
        Args:
            backend_response: FlowOutput from the backend AI orchestrator
            
        Returns:
            ChatProcessResponse for the web UI
            
        Raises:
            ValueError: If the response format is invalid
        """
        try:
            # Handle ai_data conversion
            ai_data_dict = None
            acknowledgement = None
            summary_was_generated = None
            
            if backend_response.ai_data:
                ai_data_dict = backend_response.ai_data.model_dump()
                # Extract specific fields if they exist
                acknowledgement = ai_data_dict.get("acknowledgement")
                summary_was_generated = ai_data_dict.get("summary_generated")
            
            # Extract suggested facts from backend response
            suggested_new_facts = backend_response.suggested_new_facts
            
            return ChatProcessResponse(
                finalResponse=backend_response.response,
                acknowledgement=acknowledgement,
                ai_data_for_final_response=ai_data_dict,
                suggested_new_facts=suggested_new_facts,
                proactive_suggestion=backend_response.proactive_suggestion,
                summary_was_generated=summary_was_generated or backend_response.summary_was_generated
            )
            
        except Exception as e:
            logger.error(f"Failed to transform backend response: {e}")
            raise ValueError(f"Invalid backend response format: {e}")
    
    @staticmethod
    def transform_flow_response_to_chat(
        flow_response: FlowResponse
    ) -> ChatProcessResponse:
        """
        Transform FlowResponse to web UI chat format.
        
        Args:
            flow_response: FlowResponse from the AI orchestrator API
            
        Returns:
            ChatProcessResponse for the web UI
        """
        try:
            # Extract AI data
            ai_data_dict = flow_response.ai_data
            acknowledgement = None
            summary_was_generated = None
            
            if ai_data_dict:
                acknowledgement = ai_data_dict.get("acknowledgement")
                summary_was_generated = ai_data_dict.get("summary_generated")
            
            return ChatProcessResponse(
                finalResponse=flow_response.response,
                acknowledgement=acknowledgement,
                ai_data_for_final_response=ai_data_dict,
                suggested_new_facts=flow_response.suggested_actions,  # Map suggested_actions to suggested_new_facts
                proactive_suggestion=flow_response.proactive_suggestion,
                summary_was_generated=summary_was_generated
            )
            
        except Exception as e:
            logger.error(f"Failed to transform flow response: {e}")
            raise ValueError(f"Invalid flow response format: {e}")
    
    @staticmethod
    def transform_conversation_history_to_backend(
        web_ui_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform web UI conversation history to backend format.
        
        Args:
            web_ui_history: Conversation history from web UI
            
        Returns:
            Transformed conversation history for backend
        """
        try:
            transformed_history = []
            
            for message in web_ui_history:
                # Ensure required fields exist
                if not isinstance(message, dict):
                    logger.warning(f"Skipping invalid message format: {type(message)}")
                    continue
                
                # Extract message content and role
                content = message.get("content", "")
                role = message.get("role", "user")
                
                if not content:
                    logger.warning("Skipping message with empty content")
                    continue
                
                # Validate role
                if role not in ["user", "assistant", "system"]:
                    logger.warning(f"Invalid role '{role}', defaulting to 'user'")
                    role = "user"
                
                # Transform timestamp
                timestamp = message.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        try:
                            # Try to parse ISO format
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).isoformat()
                        except ValueError:
                            timestamp = datetime.utcnow().isoformat()
                    elif isinstance(timestamp, (int, float)):
                        # Convert from Unix timestamp
                        timestamp = datetime.fromtimestamp(timestamp).isoformat()
                    else:
                        timestamp = datetime.utcnow().isoformat()
                else:
                    timestamp = datetime.utcnow().isoformat()
                
                transformed_message = {
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                }
                
                # Add optional fields if present
                if "id" in message:
                    transformed_message["id"] = str(message["id"])
                
                if "ai_data" in message:
                    transformed_message["ai_data"] = message["ai_data"]
                
                transformed_history.append(transformed_message)
            
            return transformed_history
            
        except Exception as e:
            logger.error(f"Failed to transform conversation history: {e}")
            return []
    
    @staticmethod
    def transform_conversation_history_to_web_ui(
        backend_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform backend conversation history to web UI format.
        
        Args:
            backend_history: Conversation history from backend
            
        Returns:
            Transformed conversation history for web UI
        """
        try:
            transformed_history = []
            
            for message in backend_history:
                if not isinstance(message, dict):
                    continue
                
                # Extract basic fields
                content = message.get("content", "")
                role = message.get("role", "user")
                
                if not content:
                    continue
                
                # Transform timestamp to JavaScript-compatible format
                timestamp = message.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = int(dt.timestamp() * 1000)  # Convert to milliseconds
                        except ValueError:
                            timestamp = int(datetime.utcnow().timestamp() * 1000)
                    elif isinstance(timestamp, (int, float)):
                        # Assume it's already a timestamp
                        if timestamp < 946684800000:  # Less than year 2000 in milliseconds
                            timestamp = int(timestamp * 1000)  # Convert from seconds
                        else:
                            timestamp = int(timestamp)
                    else:
                        timestamp = int(datetime.utcnow().timestamp() * 1000)
                else:
                    timestamp = int(datetime.utcnow().timestamp() * 1000)
                
                transformed_message = {
                    "id": message.get("id", f"msg_{len(transformed_history)}"),
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                }
                
                # Add AI data if present
                if "ai_data" in message:
                    transformed_message["ai_data"] = message["ai_data"]
                
                transformed_history.append(transformed_message)
            
            return transformed_history
            
        except Exception as e:
            logger.error(f"Failed to transform conversation history to web UI: {e}")
            return []
    
    @staticmethod
    def extract_user_settings(web_ui_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate user settings from web UI format.
        
        Args:
            web_ui_settings: User settings from web UI
            
        Returns:
            Validated user settings for backend
        """
        try:
            # Default settings
            default_settings = {
                "memory_depth": "medium",
                "personality_tone": "friendly",
                "personality_verbosity": "balanced",
                "personal_facts": [],
                "custom_persona_instructions": "",
                "temperature_unit": "C",
                "weather_service": "wttr_in",
                "active_listen_mode": False
            }
            
            # Merge with provided settings
            settings = default_settings.copy()
            if isinstance(web_ui_settings, dict):
                settings.update(web_ui_settings)
            
            # Validate enum values
            valid_memory_depths = ["short", "medium", "long"]
            if settings.get("memory_depth") not in valid_memory_depths:
                settings["memory_depth"] = "medium"
            
            valid_tones = ["neutral", "friendly", "formal", "humorous"]
            if settings.get("personality_tone") not in valid_tones:
                settings["personality_tone"] = "friendly"
            
            valid_verbosity = ["concise", "balanced", "detailed"]
            if settings.get("personality_verbosity") not in valid_verbosity:
                settings["personality_verbosity"] = "balanced"
            
            # Ensure personal_facts is a list
            if not isinstance(settings.get("personal_facts"), list):
                settings["personal_facts"] = []
            
            # Ensure custom_persona_instructions is a string
            if not isinstance(settings.get("custom_persona_instructions"), str):
                settings["custom_persona_instructions"] = ""
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to extract user settings: {e}")
            return {
                "memory_depth": "medium",
                "personality_tone": "friendly",
                "personality_verbosity": "balanced",
                "personal_facts": [],
                "custom_persona_instructions": ""
            }
    
    @staticmethod
    def transform_relevant_memories_to_context(
        relevant_memories: List[Dict[str, Any]]
    ) -> List[MemoryContext]:
        """
        Transform relevant memories to MemoryContext format.
        
        Args:
            relevant_memories: Relevant memories from web UI
            
        Returns:
            List of MemoryContext objects
        """
        try:
            memory_contexts = []
            
            for memory in relevant_memories:
                if not isinstance(memory, dict):
                    continue
                
                content = memory.get("content", "")
                if not content:
                    continue
                
                # Extract similarity score
                similarity_score = memory.get("similarity_score")
                if similarity_score is not None:
                    try:
                        similarity_score = float(similarity_score)
                        if not (0.0 <= similarity_score <= 1.0):
                            similarity_score = None
                    except (ValueError, TypeError):
                        similarity_score = None
                
                # Extract tags
                tags = memory.get("tags", [])
                if not isinstance(tags, list):
                    tags = []
                
                # Extract timestamp
                timestamp = memory.get("timestamp")
                if timestamp is not None:
                    try:
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = int(dt.timestamp())
                        elif isinstance(timestamp, (int, float)):
                            timestamp = int(timestamp)
                        else:
                            timestamp = None
                    except (ValueError, TypeError):
                        timestamp = None
                
                memory_context = MemoryContext(
                    content=content,
                    similarity_score=similarity_score,
                    tags=tags,
                    timestamp=timestamp
                )
                
                memory_contexts.append(memory_context)
            
            return memory_contexts
            
        except Exception as e:
            logger.error(f"Failed to transform relevant memories: {e}")
            return []
    
    @staticmethod
    def create_ai_data_transformation_helpers() -> Dict[str, Any]:
        """
        Create AI data transformation helper functions.
        
        Returns:
            Dictionary of helper functions for AI data transformation
        """
        def extract_ai_insights(ai_data: Dict[str, Any]) -> Dict[str, Any]:
            """Extract AI insights from response data."""
            insights = {}
            
            if "keywords" in ai_data:
                insights["keywords"] = ai_data["keywords"]
            
            if "knowledge_graph_insights" in ai_data:
                insights["knowledge_graph_insights"] = ai_data["knowledge_graph_insights"]
            
            if "confidence" in ai_data:
                insights["confidence"] = ai_data["confidence"]
            
            if "reasoning" in ai_data:
                insights["reasoning"] = ai_data["reasoning"]
            
            return insights
        
        def merge_ai_data_safely(base_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
            """Safely merge AI data dictionaries."""
            merged = base_data.copy()
            
            for key, value in new_data.items():
                if key in merged:
                    # Handle conflicts by creating arrays
                    if not isinstance(merged[key], list):
                        merged[key] = [merged[key]]
                    if isinstance(value, list):
                        merged[key].extend(value)
                    else:
                        merged[key].append(value)
                else:
                    merged[key] = value
            
            return merged
        
        def clean_ai_data_for_web_ui(ai_data: Dict[str, Any]) -> Dict[str, Any]:
            """Clean AI data for Web UI API."""
            cleaned = {}
            
            # Only include safe fields
            safe_fields = [
                "keywords", "knowledge_graph_insights", "confidence", "reasoning",
                "acknowledgement", "summary_generated", "model_used", "processing_time_ms"
            ]
            
            for key, value in ai_data.items():
                if key in safe_fields:
                    cleaned[key] = value
            
            return cleaned
        
        return {
            'extract_ai_insights': extract_ai_insights,
            'merge_ai_data_safely': merge_ai_data_safely,
            'clean_ai_data_for_web_ui': clean_ai_data_for_web_ui
        }
    
    @staticmethod
    def validate_chat_request(web_ui_request: ChatProcessRequest) -> List[str]:
        """
        Validate chat request and return list of error messages.
        
        Args:
            web_ui_request: ChatProcessRequest to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate message
        if not web_ui_request.message or not web_ui_request.message.strip():
            errors.append("Message cannot be empty")
        elif len(web_ui_request.message) > 10000:
            errors.append("Message cannot exceed 10,000 characters")
        
        # Validate conversation history
        if web_ui_request.conversation_history:
            if not isinstance(web_ui_request.conversation_history, list):
                errors.append("Conversation history must be a list")
            elif len(web_ui_request.conversation_history) > 100:
                errors.append("Conversation history cannot exceed 100 messages")
            else:
                for i, message in enumerate(web_ui_request.conversation_history):
                    if not isinstance(message, dict):
                        errors.append(f"Message at index {i} must be a dictionary")
                    elif "content" not in message:
                        errors.append(f"Message at index {i} must have 'content' field")
                    elif not message["content"]:
                        errors.append(f"Message at index {i} cannot have empty content")
        
        # Validate relevant memories
        if web_ui_request.relevant_memories:
            if not isinstance(web_ui_request.relevant_memories, list):
                errors.append("Relevant memories must be a list")
            elif len(web_ui_request.relevant_memories) > 50:
                errors.append("Relevant memories cannot exceed 50 entries")
        
        # Validate user settings
        if web_ui_request.user_settings:
            if not isinstance(web_ui_request.user_settings, dict):
                errors.append("User settings must be a dictionary")
        
        # Validate IDs
        if web_ui_request.user_id and len(web_ui_request.user_id) > 100:
            errors.append("User ID cannot exceed 100 characters")
        
        if web_ui_request.session_id and len(web_ui_request.session_id) > 100:
            errors.append("Session ID cannot exceed 100 characters")
        
        return errors
    
    @staticmethod
    def create_conversation_performance_tracker():
        """
        Create a performance tracker for conversation processing.
        
        Returns:
            Performance tracker context manager
        """
        class ConversationPerformanceTracker:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.processing_stages = {}
                self.metadata = {}
            
            def __enter__(self):
                self.start_time = datetime.utcnow()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.end_time = datetime.utcnow()
            
            def mark_stage(self, stage_name: str):
                """Mark a processing stage."""
                self.processing_stages[stage_name] = datetime.utcnow()
            
            def get_duration_ms(self) -> float:
                """Get total processing duration in milliseconds."""
                if self.start_time and self.end_time:
                    return (self.end_time - self.start_time).total_seconds() * 1000
                return 0.0
            
            def get_stage_durations(self) -> Dict[str, float]:
                """Get duration for each processing stage."""
                durations = {}
                prev_time = self.start_time
                
                for stage_name, stage_time in self.processing_stages.items():
                    if prev_time:
                        durations[stage_name] = (stage_time - prev_time).total_seconds() * 1000
                        prev_time = stage_time
                
                return durations
            
            def add_metadata(self, key: str, value: Any):
                """Add metadata to the performance tracker."""
                self.metadata[key] = value
            
            def get_performance_summary(self) -> Dict[str, Any]:
                """Get performance summary."""
                return {
                    'total_duration_ms': self.get_duration_ms(),
                    'stage_durations': self.get_stage_durations(),
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'end_time': self.end_time.isoformat() if self.end_time else None,
                    'metadata': self.metadata
                }
        
        return ConversationPerformanceTracker()


# Convenience functions for direct use
def transform_chat_request_to_backend(web_ui_request: ChatProcessRequest) -> Tuple[ConversationProcessingRequest, FlowInput]:
    """Transform web UI chat request to backend format."""
    return ChatTransformationUtils.transform_chat_request_to_backend(web_ui_request)


def transform_backend_response_to_chat(backend_response: FlowOutput) -> ChatProcessResponse:
    """Transform backend response to web UI chat format."""
    return ChatTransformationUtils.transform_backend_response_to_chat(backend_response)


def transform_conversation_history_to_backend(web_ui_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform web UI conversation history to backend format."""
    return ChatTransformationUtils.transform_conversation_history_to_backend(web_ui_history)


def validate_chat_request(web_ui_request: ChatProcessRequest) -> List[str]:
    """Validate chat request."""
    return ChatTransformationUtils.validate_chat_request(web_ui_request)


__all__ = [
    "ChatTransformationUtils",
    "transform_chat_request_to_backend",
    "transform_backend_response_to_chat",
    "transform_conversation_history_to_backend",
    "validate_chat_request"
]