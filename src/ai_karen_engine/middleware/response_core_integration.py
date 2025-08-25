"""
Response Core Integration Middleware

This middleware provides seamless integration between the existing ChatOrchestrator
and the new ResponseOrchestrator, allowing for gradual migration and fallback.
"""

import logging
import time
from typing import Any, Dict, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.response.factory import get_global_orchestrator, create_local_only_orchestrator
from ..chat.chat_orchestrator import ChatOrchestrator

logger = logging.getLogger(__name__)


class ResponseCoreIntegrationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that can route requests between ChatOrchestrator and ResponseOrchestrator
    based on configuration or request parameters.
    """
    
    def __init__(self, app, enable_response_core: bool = True, fallback_enabled: bool = True):
        super().__init__(app)
        self.enable_response_core = enable_response_core
        self.fallback_enabled = fallback_enabled
        self._response_orchestrator_cache: Dict[str, Any] = {}
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and potentially route to Response Core
        """
        # Check if this is a chat endpoint that should use Response Core
        if self._should_use_response_core(request):
            # Add Response Core indicator to request state
            request.state.use_response_core = True
            request.state.response_core_fallback = self.fallback_enabled
        
        # Process request normally
        response = await call_next(request)
        
        # Add Response Core headers if used
        if hasattr(request.state, 'use_response_core') and request.state.use_response_core:
            response.headers["X-Orchestrator"] = "response-core"
            response.headers["X-Local-Processing"] = "true"
        
        return response
    
    def _should_use_response_core(self, request: Request) -> bool:
        """
        Determine if request should use Response Core orchestrator
        """
        if not self.enable_response_core:
            return False
        
        # Check for explicit Response Core request
        if "response-core" in str(request.url):
            return True
        
        # Check for Response Core header
        if request.headers.get("X-Use-Response-Core") == "true":
            return True
        
        # Check for query parameter
        if request.query_params.get("use_response_core") == "true":
            return True
        
        return False


class ResponseCoreCompatibilityLayer:
    """
    Compatibility layer that provides unified interface between orchestrators
    """
    
    def __init__(self, enable_response_core: bool = True, fallback_enabled: bool = True):
        self.enable_response_core = enable_response_core
        self.fallback_enabled = fallback_enabled
        self._orchestrator_cache: Dict[str, Any] = {}
    
    async def process_chat_request(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        session_id: Optional[str] = None,
        use_response_core: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process chat request using appropriate orchestrator
        
        Args:
            message: User message
            user_id: User identifier
            conversation_id: Conversation identifier
            session_id: Session identifier
            use_response_core: Force use of Response Core
            **kwargs: Additional parameters
            
        Returns:
            Unified response format
        """
        start_time = time.time()
        
        try:
            if self.enable_response_core and (use_response_core or self._should_prefer_response_core(message, **kwargs)):
                # Use Response Core orchestrator
                result = await self._process_with_response_core(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    **kwargs
                )
                result["orchestrator"] = "response_core"
                result["local_processing"] = True
                
            else:
                # Use existing ChatOrchestrator
                result = await self._process_with_chat_orchestrator(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    **kwargs
                )
                result["orchestrator"] = "chat_orchestrator"
                result["local_processing"] = False
            
            result["processing_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            
            if self.fallback_enabled:
                # Try fallback orchestrator
                try:
                    if use_response_core:
                        # Fallback to ChatOrchestrator
                        result = await self._process_with_chat_orchestrator(
                            message=message,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            session_id=session_id,
                            **kwargs
                        )
                        result["orchestrator"] = "chat_orchestrator"
                        result["used_fallback"] = True
                    else:
                        # Fallback to Response Core
                        result = await self._process_with_response_core(
                            message=message,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            session_id=session_id,
                            **kwargs
                        )
                        result["orchestrator"] = "response_core"
                        result["used_fallback"] = True
                    
                    result["processing_time"] = time.time() - start_time
                    result["fallback_reason"] = str(e)
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback orchestrator also failed: {fallback_error}")
            
            # Return error response
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "orchestrator": "error",
                "used_fallback": False
            }
    
    async def _process_with_response_core(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process with Response Core orchestrator"""
        try:
            # Get or create Response Core orchestrator
            orchestrator = self._get_response_orchestrator(user_id)
            
            # Process message
            result = orchestrator.respond(
                conversation_id=conversation_id,
                user_input=message,
                correlation_id=session_id
            )
            
            return {
                "response": result,
                "success": True,
                "correlation_id": session_id or conversation_id,
                "context_used": True,  # Response Core always uses context
                "used_fallback": False
            }
            
        except Exception as e:
            logger.error(f"Response Core processing error: {e}")
            raise
    
    async def _process_with_chat_orchestrator(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process with existing ChatOrchestrator"""
        try:
            # Import here to avoid circular dependencies
            from ..chat.chat_orchestrator import ChatOrchestrator, ChatRequest
            from ..chat.memory_processor import MemoryProcessor
            
            # Create ChatOrchestrator (simplified for compatibility)
            memory_processor = MemoryProcessor()
            chat_orchestrator = ChatOrchestrator(memory_processor=memory_processor)
            
            # Create request
            chat_request = ChatRequest(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                session_id=session_id,
                stream=False,
                include_context=True,
                metadata=kwargs
            )
            
            # Process message
            response = await chat_orchestrator.process_message(chat_request)
            
            return {
                "response": response.response,
                "success": True,
                "correlation_id": response.correlation_id,
                "context_used": response.context_used,
                "used_fallback": response.used_fallback,
                "metadata": response.metadata
            }
            
        except Exception as e:
            logger.error(f"ChatOrchestrator processing error: {e}")
            raise
    
    def _get_response_orchestrator(self, user_id: str):
        """Get or create Response Core orchestrator for user"""
        if user_id not in self._orchestrator_cache:
            try:
                self._orchestrator_cache[user_id] = get_global_orchestrator(user_id=user_id)
            except Exception as e:
                logger.warning(f"Failed to create global orchestrator, using local-only: {e}")
                self._orchestrator_cache[user_id] = create_local_only_orchestrator(user_id=user_id)
        
        return self._orchestrator_cache[user_id]
    
    def _should_prefer_response_core(self, message: str, **kwargs) -> bool:
        """
        Determine if Response Core should be preferred for this request
        """
        # Prefer Response Core for certain types of requests
        
        # Check for local processing preference
        if kwargs.get("local_only", False):
            return True
        
        # Check for prompt-driven requests
        if any(keyword in message.lower() for keyword in ["analyze", "explain", "help", "guide"]):
            return True
        
        # Check for persona-related requests
        if any(keyword in message.lower() for keyword in ["persona", "character", "role"]):
            return True
        
        # Default to existing orchestrator for backward compatibility
        return False


# Global compatibility layer instance
_compatibility_layer: Optional[ResponseCoreCompatibilityLayer] = None


def get_compatibility_layer() -> ResponseCoreCompatibilityLayer:
    """Get global compatibility layer instance"""
    global _compatibility_layer
    if _compatibility_layer is None:
        _compatibility_layer = ResponseCoreCompatibilityLayer()
    return _compatibility_layer


def configure_response_core_integration(
    enable_response_core: bool = True,
    fallback_enabled: bool = True
) -> ResponseCoreCompatibilityLayer:
    """Configure Response Core integration"""
    global _compatibility_layer
    _compatibility_layer = ResponseCoreCompatibilityLayer(
        enable_response_core=enable_response_core,
        fallback_enabled=fallback_enabled
    )
    return _compatibility_layer