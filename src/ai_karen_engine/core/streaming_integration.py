"""
Streaming Integration for CopilotKit

This module provides streaming support for the LangGraph orchestrator
to integrate with CopilotKit's real-time requirements.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, AsyncGenerator, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .langgraph_orchestrator import LangGraphOrchestrator, OrchestrationState

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Represents a streaming chunk of data"""
    type: str  # "node_start", "node_end", "message", "error", "metadata"
    node: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type,
            "node": self.node,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class CopilotKitStreamer:
    """
    Streaming adapter for CopilotKit integration
    """
    
    def __init__(self, orchestrator: LangGraphOrchestrator):
        self.orchestrator = orchestrator
        
    async def stream_chat(self, 
                         message: str, 
                         user_id: str, 
                         session_id: str = None,
                         context: Dict[str, Any] = None) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat conversation through the orchestration graph
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier
            context: Additional context
            
        Yields:
            StreamChunk objects with processing updates
        """
        try:
            # Convert message to LangChain format
            messages = [HumanMessage(content=message)]
            
            # Start streaming
            yield StreamChunk(
                type="node_start",
                node="orchestration",
                content="Starting conversation processing",
                timestamp=datetime.now()
            )
            
            # Stream through the orchestration graph
            async for chunk in self.orchestrator.stream_process(
                messages=messages,
                user_id=user_id,
                session_id=session_id,
                config=context
            ):
                # Convert graph chunks to stream chunks
                for node_name, node_state in chunk.items():
                    if isinstance(node_state, dict):
                        # Node completion
                        yield StreamChunk(
                            type="node_end",
                            node=node_name,
                            content=f"Completed {node_name}",
                            metadata=self._extract_node_metadata(node_name, node_state),
                            timestamp=datetime.now()
                        )
                        
                        # Check for response content
                        if "response" in node_state and node_state["response"]:
                            yield StreamChunk(
                                type="message",
                                content=node_state["response"],
                                metadata=node_state.get("response_metadata", {}),
                                timestamp=datetime.now()
                            )
                        
                        # Check for errors
                        if "errors" in node_state and node_state["errors"]:
                            for error in node_state["errors"]:
                                yield StreamChunk(
                                    type="error",
                                    content=error,
                                    timestamp=datetime.now()
                                )
            
            # End of processing
            yield StreamChunk(
                type="node_end",
                node="orchestration",
                content="Conversation processing completed",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield StreamChunk(
                type="error",
                content=f"Streaming error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _extract_node_metadata(self, node_name: str, node_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant metadata from node state"""
        metadata = {}
        
        if node_name == "auth_gate":
            metadata["auth_status"] = node_state.get("auth_status")
            metadata["permissions"] = node_state.get("user_permissions")
            
        elif node_name == "safety_gate":
            metadata["safety_status"] = node_state.get("safety_status")
            metadata["safety_flags"] = node_state.get("safety_flags", [])
            
        elif node_name == "intent_detect":
            metadata["intent"] = node_state.get("detected_intent")
            metadata["confidence"] = node_state.get("intent_confidence")
            
        elif node_name == "router_select":
            metadata["provider"] = node_state.get("selected_provider")
            metadata["model"] = node_state.get("selected_model")
            metadata["routing_reason"] = node_state.get("routing_reason")
            
        elif node_name == "tool_exec":
            metadata["tools_used"] = len(node_state.get("tool_results", []))
            
        elif node_name == "response_synth":
            metadata["response_metadata"] = node_state.get("response_metadata", {})
            
        return metadata


class ServerSentEventStreamer:
    """
    Server-Sent Events (SSE) streaming adapter
    """
    
    def __init__(self, orchestrator: LangGraphOrchestrator):
        self.orchestrator = orchestrator
        
    async def stream_sse(self, 
                        message: str, 
                        user_id: str, 
                        session_id: str = None) -> AsyncGenerator[str, None]:
        """
        Stream conversation as Server-Sent Events
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier
            
        Yields:
            SSE-formatted strings
        """
        copilot_streamer = CopilotKitStreamer(self.orchestrator)
        
        try:
            async for chunk in copilot_streamer.stream_chat(message, user_id, session_id):
                # Format as SSE
                sse_data = json.dumps(chunk.to_dict())
                yield f"data: {sse_data}\n\n"
                
        except Exception as e:
            logger.error(f"SSE streaming error: {e}")
            error_chunk = StreamChunk(
                type="error",
                content=f"SSE streaming error: {str(e)}",
                timestamp=datetime.now()
            )
            yield f"data: {json.dumps(error_chunk.to_dict())}\n\n"
        
        # End of stream
        yield "data: [DONE]\n\n"


class WebSocketStreamer:
    """
    WebSocket streaming adapter
    """
    
    def __init__(self, orchestrator: LangGraphOrchestrator):
        self.orchestrator = orchestrator
        self.active_connections: Dict[str, Any] = {}
        
    async def handle_websocket(self, websocket, user_id: str, session_id: str = None):
        """
        Handle WebSocket connection for streaming
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            session_id: Session identifier
        """
        connection_id = f"{user_id}_{session_id or 'default'}"
        self.active_connections[connection_id] = websocket
        
        try:
            await websocket.accept()
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Listen for messages
            while True:
                try:
                    data = await websocket.receive_json()
                    message = data.get("message", "")
                    
                    if message:
                        # Stream response
                        copilot_streamer = CopilotKitStreamer(self.orchestrator)
                        async for chunk in copilot_streamer.stream_chat(message, user_id, session_id):
                            await websocket.send_json(chunk.to_dict())
                            
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Message processing error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            # Clean up connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]


class StreamingManager:
    """
    Central manager for all streaming integrations
    """
    
    def __init__(self, orchestrator: LangGraphOrchestrator = None):
        from .langgraph_orchestrator import get_default_orchestrator
        self.orchestrator = orchestrator or get_default_orchestrator()
        
        self.copilot_streamer = CopilotKitStreamer(self.orchestrator)
        self.sse_streamer = ServerSentEventStreamer(self.orchestrator)
        self.websocket_streamer = WebSocketStreamer(self.orchestrator)
        
    async def stream_for_copilotkit(self, 
                                   message: str, 
                                   user_id: str, 
                                   session_id: str = None,
                                   context: Dict[str, Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream conversation for CopilotKit integration
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier
            context: Additional context
            
        Yields:
            Dictionary chunks suitable for CopilotKit
        """
        async for chunk in self.copilot_streamer.stream_chat(message, user_id, session_id, context):
            yield chunk.to_dict()
    
    async def stream_sse(self, 
                        message: str, 
                        user_id: str, 
                        session_id: str = None) -> AsyncGenerator[str, None]:
        """
        Stream conversation as Server-Sent Events
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier
            
        Yields:
            SSE-formatted strings
        """
        async for sse_chunk in self.sse_streamer.stream_sse(message, user_id, session_id):
            yield sse_chunk
    
    async def handle_websocket(self, websocket, user_id: str, session_id: str = None):
        """
        Handle WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            session_id: Session identifier
        """
        await self.websocket_streamer.handle_websocket(websocket, user_id, session_id)


# Global streaming manager instance
_streaming_manager = None

def get_streaming_manager() -> StreamingManager:
    """Get the global streaming manager instance"""
    global _streaming_manager
    if _streaming_manager is None:
        _streaming_manager = StreamingManager()
    return _streaming_manager