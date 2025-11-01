"""
LangGraph Orchestration Foundation

This module implements the core orchestration backbone using LangGraph for
human-in-the-loop workflows with typed state management and checkpointing.

Graph Structure:
auth_gate → safety_gate → memory_fetch → intent_detect → planner → 
router_select → tool_exec → response_synth → approval_gate → memory_write
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal, Deque
from dataclasses import dataclass, field, replace
import asyncio
from collections import deque
import logging
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class OrchestrationState(TypedDict):
    """Typed state for the orchestration graph"""
    # Input/Output
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    
    # Authentication & Authorization
    auth_status: Optional[str]  # "authenticated", "failed", "pending"
    user_permissions: Optional[Dict[str, Any]]
    
    # Safety & Guardrails
    safety_status: Optional[str]  # "safe", "unsafe", "review_required"
    safety_flags: Optional[List[str]]
    
    # Memory & Context
    memory_context: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]]
    
    # Intent & Planning
    detected_intent: Optional[str]
    intent_confidence: Optional[float]
    execution_plan: Optional[Dict[str, Any]]
    
    # Routing & Execution
    selected_provider: Optional[str]
    selected_model: Optional[str]
    routing_reason: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    
    # Response Generation
    response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]
    
    # Human-in-the-loop
    requires_approval: Optional[bool]
    approval_status: Optional[str]  # "pending", "approved", "rejected"
    approval_reason: Optional[str]
    
    # Error Handling
    errors: List[str]
    warnings: List[str]
    
    # Streaming Support
    streaming_enabled: Optional[bool]
    stream_chunks: Optional[List[str]]


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration system"""
    enable_auth_gate: bool = True
    enable_safety_gate: bool = True
    enable_memory_fetch: bool = True
    enable_approval_gate: bool = False
    streaming_enabled: bool = False
    checkpoint_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300


class LangGraphOrchestrator:
    """
    Main orchestration class using LangGraph for workflow management
    """
    
    def __init__(self, config: OrchestrationConfig = None):
        self.config = config or OrchestrationConfig()
        self.checkpointer = MemorySaver() if self.config.checkpoint_enabled else None
        self.graph = None
        self._build_graph()

        # Runtime telemetry
        self._start_time = datetime.now(timezone.utc)
        self._stats_lock = asyncio.Lock()
        self._config_lock = asyncio.Lock()
        self._active_sessions: Dict[str, datetime] = {}
        self._total_processed: int = 0
        self._total_failed: int = 0
        self._latency_samples: Deque[float] = deque(maxlen=1000)
        self._last_error: Optional[Dict[str, Any]] = None
        
    def _build_graph(self):
        """Build the orchestration graph with all nodes and edges"""
        workflow = StateGraph(OrchestrationState)
        
        # Add nodes
        workflow.add_node("auth_gate", self._auth_gate)
        workflow.add_node("safety_gate", self._safety_gate)
        workflow.add_node("memory_fetch", self._memory_fetch)
        workflow.add_node("intent_detect", self._intent_detect)
        workflow.add_node("planner", self._planner)
        workflow.add_node("router_select", self._router_select)
        workflow.add_node("tool_exec", self._tool_exec)
        workflow.add_node("response_synth", self._response_synth)
        workflow.add_node("approval_gate", self._approval_gate)
        workflow.add_node("memory_write", self._memory_write)
        
        # Define the flow
        workflow.add_edge(START, "auth_gate")
        
        # Conditional edges based on configuration
        if self.config.enable_auth_gate:
            workflow.add_conditional_edges(
                "auth_gate",
                self._should_continue_after_auth,
                {
                    "continue": "safety_gate" if self.config.enable_safety_gate else "memory_fetch",
                    "reject": END
                }
            )
        else:
            workflow.add_edge("auth_gate", "safety_gate" if self.config.enable_safety_gate else "memory_fetch")
            
        if self.config.enable_safety_gate:
            workflow.add_conditional_edges(
                "safety_gate",
                self._should_continue_after_safety,
                {
                    "continue": "memory_fetch" if self.config.enable_memory_fetch else "intent_detect",
                    "reject": END,
                    "review": "approval_gate"
                }
            )
        
        if self.config.enable_memory_fetch:
            workflow.add_edge("memory_fetch", "intent_detect")
        
        workflow.add_edge("intent_detect", "planner")
        workflow.add_edge("planner", "router_select")
        workflow.add_edge("router_select", "tool_exec")
        workflow.add_edge("tool_exec", "response_synth")
        
        if self.config.enable_approval_gate:
            workflow.add_conditional_edges(
                "response_synth",
                self._should_require_approval,
                {
                    "approve": "memory_write",
                    "review": "approval_gate"
                }
            )
            workflow.add_conditional_edges(
                "approval_gate",
                self._check_approval_status,
                {
                    "approved": "memory_write",
                    "rejected": END,
                    "pending": "approval_gate"  # Wait for human input
                }
            )
        else:
            workflow.add_edge("response_synth", "memory_write")
            
        workflow.add_edge("memory_write", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
    async def _auth_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Authentication and authorization gate"""
        logger.info(f"Auth gate processing for user: {state.get('user_id')}")
        
        try:
            # TODO: Integrate with existing auth system
            # For now, assume authenticated if user_id is provided
            if state.get("user_id"):
                state["auth_status"] = "authenticated"
                state["user_permissions"] = {"chat": True, "tools": True}
            else:
                state["auth_status"] = "failed"
                state["errors"].append("Authentication required")
                
        except Exception as e:
            logger.error(f"Auth gate error: {e}")
            state["auth_status"] = "failed"
            state["errors"].append(f"Authentication error: {str(e)}")
            
        return state
    
    async def _safety_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Safety and guardrails gate"""
        logger.info("Safety gate processing")
        
        try:
            # TODO: Integrate with existing guardrails system
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1].content if messages else ""
                
                # Basic safety checks (placeholder)
                unsafe_patterns = ["hack", "exploit", "malicious"]
                safety_flags = []
                
                for pattern in unsafe_patterns:
                    if pattern.lower() in last_message.lower():
                        safety_flags.append(f"Detected: {pattern}")
                
                if safety_flags:
                    state["safety_status"] = "review_required"
                    state["safety_flags"] = safety_flags
                else:
                    state["safety_status"] = "safe"
            else:
                state["safety_status"] = "safe"
                
        except Exception as e:
            logger.error(f"Safety gate error: {e}")
            state["safety_status"] = "unsafe"
            state["errors"].append(f"Safety check error: {str(e)}")
            
        return state
    
    async def _memory_fetch(self, state: OrchestrationState) -> OrchestrationState:
        """Memory and context fetching"""
        logger.info("Memory fetch processing")
        
        try:
            # TODO: Integrate with existing memory system
            user_id = state.get("user_id")
            session_id = state.get("session_id")
            
            # Placeholder memory context
            state["memory_context"] = {
                "user_preferences": {},
                "conversation_summary": "",
                "relevant_history": []
            }
            state["conversation_history"] = []
            
        except Exception as e:
            logger.error(f"Memory fetch error: {e}")
            state["errors"].append(f"Memory fetch error: {str(e)}")
            
        return state
    
    async def _intent_detect(self, state: OrchestrationState) -> OrchestrationState:
        """Intent detection and classification"""
        logger.info("Intent detection processing")
        
        try:
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1].content if messages else ""
                
                # TODO: Integrate with existing intent engine
                # Basic intent detection (placeholder)
                if any(word in last_message.lower() for word in ["code", "program", "function"]):
                    state["detected_intent"] = "code_generation"
                    state["intent_confidence"] = 0.8
                elif any(word in last_message.lower() for word in ["search", "find", "lookup"]):
                    state["detected_intent"] = "information_retrieval"
                    state["intent_confidence"] = 0.7
                else:
                    state["detected_intent"] = "general_chat"
                    state["intent_confidence"] = 0.6
            else:
                state["detected_intent"] = "unknown"
                state["intent_confidence"] = 0.0
                
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            state["errors"].append(f"Intent detection error: {str(e)}")
            
        return state
    
    async def _planner(self, state: OrchestrationState) -> OrchestrationState:
        """Execution planning based on intent"""
        logger.info("Planning processing")
        
        try:
            intent = state.get("detected_intent", "general_chat")
            
            # TODO: Integrate with existing planning system
            execution_plan = {
                "steps": [],
                "tools_required": [],
                "estimated_time": 0,
                "complexity": "low"
            }
            
            if intent == "code_generation":
                execution_plan["steps"] = ["analyze_requirements", "generate_code", "validate_syntax"]
                execution_plan["tools_required"] = ["code_generator", "syntax_validator"]
                execution_plan["complexity"] = "medium"
            elif intent == "information_retrieval":
                execution_plan["steps"] = ["search_knowledge", "rank_results", "synthesize_answer"]
                execution_plan["tools_required"] = ["search_engine", "knowledge_base"]
                execution_plan["complexity"] = "low"
            else:
                execution_plan["steps"] = ["generate_response"]
                execution_plan["tools_required"] = ["llm"]
                execution_plan["complexity"] = "low"
                
            state["execution_plan"] = execution_plan
            
        except Exception as e:
            logger.error(f"Planning error: {e}")
            state["errors"].append(f"Planning error: {str(e)}")
            
        return state
    
    async def _router_select(self, state: OrchestrationState) -> OrchestrationState:
        """LLM provider and model selection"""
        logger.info("Router selection processing")
        
        try:
            # TODO: Integrate with existing LLM router
            intent = state.get("detected_intent", "general_chat")
            plan = state.get("execution_plan", {})
            
            # Basic routing logic (placeholder)
            if intent == "code_generation":
                state["selected_provider"] = "openai"
                state["selected_model"] = "gpt-4"
                state["routing_reason"] = "Code generation requires advanced reasoning"
            elif plan.get("complexity") == "high":
                state["selected_provider"] = "anthropic"
                state["selected_model"] = "claude-3-opus"
                state["routing_reason"] = "High complexity task requires powerful model"
            else:
                state["selected_provider"] = "local"
                state["selected_model"] = "llama-3.1-8b"
                state["routing_reason"] = "Standard task suitable for local model"
                
        except Exception as e:
            logger.error(f"Router selection error: {e}")
            state["errors"].append(f"Router selection error: {str(e)}")
            
        return state
    
    async def _tool_exec(self, state: OrchestrationState) -> OrchestrationState:
        """Tool execution based on plan"""
        logger.info("Tool execution processing")
        
        try:
            plan = state.get("execution_plan", {})
            tools_required = plan.get("tools_required", [])
            
            # TODO: Integrate with existing tool system
            tool_results = []
            
            for tool_name in tools_required:
                # Placeholder tool execution
                result = {
                    "tool": tool_name,
                    "status": "success",
                    "output": f"Mock output from {tool_name}",
                    "execution_time": 0.1
                }
                tool_results.append(result)
                
            state["tool_results"] = tool_results
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            state["errors"].append(f"Tool execution error: {str(e)}")
            
        return state
    
    async def _response_synth(self, state: OrchestrationState) -> OrchestrationState:
        """Response synthesis and generation"""
        logger.info("Response synthesis processing")
        
        try:
            messages = state.get("messages", [])
            tool_results = state.get("tool_results", [])
            selected_model = state.get("selected_model", "default")
            
            # TODO: Integrate with existing LLM providers
            # For now, create a basic response
            if messages:
                user_message = messages[-1].content if messages else "Hello"
                response = f"I understand you said: '{user_message}'. "
                
                if tool_results:
                    response += f"I used {len(tool_results)} tools to help with your request. "
                    
                response += f"This response was generated using {selected_model}."
                
                state["response"] = response
                state["response_metadata"] = {
                    "model_used": selected_model,
                    "tools_used": len(tool_results),
                    "generation_time": 0.5
                }
                
                # Add AI message to conversation
                if "messages" not in state:
                    state["messages"] = []
                state["messages"].append(AIMessage(content=response))
            
        except Exception as e:
            logger.error(f"Response synthesis error: {e}")
            state["errors"].append(f"Response synthesis error: {str(e)}")
            
        return state
    
    async def _approval_gate(self, state: OrchestrationState) -> OrchestrationState:
        """Human approval gate for sensitive operations"""
        logger.info("Approval gate processing")
        
        try:
            # TODO: Integrate with human-in-the-loop system
            # For now, auto-approve unless explicitly marked for review
            if state.get("requires_approval"):
                state["approval_status"] = "pending"
                state["approval_reason"] = "Awaiting human review"
            else:
                state["approval_status"] = "approved"
                state["approval_reason"] = "Auto-approved"
                
        except Exception as e:
            logger.error(f"Approval gate error: {e}")
            state["errors"].append(f"Approval gate error: {str(e)}")
            
        return state
    
    async def _memory_write(self, state: OrchestrationState) -> OrchestrationState:
        """Memory writing and conversation storage"""
        logger.info("Memory write processing")
        
        try:
            # TODO: Integrate with existing memory system
            user_id = state.get("user_id")
            session_id = state.get("session_id")
            messages = state.get("messages", [])
            
            # Placeholder memory writing
            logger.info(f"Storing conversation for user {user_id}, session {session_id}")
            logger.info(f"Messages to store: {len(messages)}")
            
        except Exception as e:
            logger.error(f"Memory write error: {e}")
            state["errors"].append(f"Memory write error: {str(e)}")
            
        return state
    
    # Conditional edge functions
    def _should_continue_after_auth(self, state: OrchestrationState) -> str:
        """Determine if processing should continue after auth gate"""
        auth_status = state.get("auth_status")
        return "continue" if auth_status == "authenticated" else "reject"
    
    def _should_continue_after_safety(self, state: OrchestrationState) -> str:
        """Determine if processing should continue after safety gate"""
        safety_status = state.get("safety_status")
        if safety_status == "safe":
            return "continue"
        elif safety_status == "review_required":
            return "review"
        else:
            return "reject"
    
    def _should_require_approval(self, state: OrchestrationState) -> str:
        """Determine if human approval is required"""
        # Check if approval is required based on various factors
        safety_flags = state.get("safety_flags", [])
        tool_results = state.get("tool_results", [])
        
        # Require approval if there are safety flags or sensitive tools were used
        if safety_flags or any("sensitive" in str(result) for result in tool_results):
            state["requires_approval"] = True
            return "review"
        else:
            return "approve"
    
    def _check_approval_status(self, state: OrchestrationState) -> str:
        """Check the current approval status"""
        approval_status = state.get("approval_status", "pending")
        return approval_status
    
    async def process(self, 
                     messages: List[BaseMessage], 
                     user_id: str, 
                     session_id: str = None,
                     config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a conversation through the orchestration graph
        
        Args:
            messages: List of conversation messages
            user_id: User identifier
            session_id: Session identifier (optional)
            config: Additional configuration (optional)
            
        Returns:
            Final state after processing
        """
        if not session_id:
            session_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"
            
        # Initialize state
        initial_state: OrchestrationState = {
            "messages": messages,
            "user_id": user_id,
            "session_id": session_id,
            "auth_status": None,
            "user_permissions": None,
            "safety_status": None,
            "safety_flags": None,
            "memory_context": None,
            "conversation_history": None,
            "detected_intent": None,
            "intent_confidence": None,
            "execution_plan": None,
            "selected_provider": None,
            "selected_model": None,
            "routing_reason": None,
            "tool_calls": None,
            "tool_results": None,
            "response": None,
            "response_metadata": None,
            "requires_approval": None,
            "approval_status": None,
            "approval_reason": None,
            "errors": [],
            "warnings": [],
            "streaming_enabled": self.config.streaming_enabled,
            "stream_chunks": None
        }
        
        start_time = datetime.now(timezone.utc)
        error_message: Optional[str] = None

        await self._register_session(session_id)

        try:
            # Process through the graph
            thread_config = {"configurable": {"thread_id": session_id}}
            final_state = await self.graph.ainvoke(initial_state, config=thread_config)

            return final_state

        except Exception as e:
            error_message = str(e)
            logger.error(f"Orchestration processing error: {e}")
            initial_state["errors"].append(f"Processing error: {error_message}")
            return initial_state

        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._finalize_session(session_id, duration, error_message)
    
    async def stream_process(self, 
                           messages: List[BaseMessage], 
                           user_id: str, 
                           session_id: str = None,
                           config: Dict[str, Any] = None):
        """
        Stream process a conversation through the orchestration graph
        
        Args:
            messages: List of conversation messages
            user_id: User identifier
            session_id: Session identifier (optional)
            config: Additional configuration (optional)
            
        Yields:
            State updates during processing
        """
        if not session_id:
            session_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"
            
        # Initialize state (same as process method)
        initial_state: OrchestrationState = {
            "messages": messages,
            "user_id": user_id,
            "session_id": session_id,
            "auth_status": None,
            "user_permissions": None,
            "safety_status": None,
            "safety_flags": None,
            "memory_context": None,
            "conversation_history": None,
            "detected_intent": None,
            "intent_confidence": None,
            "execution_plan": None,
            "selected_provider": None,
            "selected_model": None,
            "routing_reason": None,
            "tool_calls": None,
            "tool_results": None,
            "response": None,
            "response_metadata": None,
            "requires_approval": None,
            "approval_status": None,
            "approval_reason": None,
            "errors": [],
            "warnings": [],
            "streaming_enabled": True,
            "stream_chunks": []
        }
        
        start_time = datetime.now(timezone.utc)
        error_message: Optional[str] = None

        await self._register_session(session_id)

        try:
            thread_config = {"configurable": {"thread_id": session_id}}

            # Stream through the graph
            async for chunk in self.graph.astream(initial_state, config=thread_config):
                yield chunk

        except Exception as e:
            error_message = str(e)
            logger.error(f"Orchestration streaming error: {e}")
            yield {"error": f"Streaming error: {error_message}"}

        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._finalize_session(session_id, duration, error_message)

    async def _register_session(self, session_id: str) -> None:
        """Register an active orchestration session for telemetry."""

        async with self._stats_lock:
            self._active_sessions[session_id] = datetime.now(timezone.utc)

    async def _finalize_session(
        self,
        session_id: str,
        duration: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Finalize bookkeeping for a session."""

        async with self._stats_lock:
            self._active_sessions.pop(session_id, None)
            if duration is not None:
                self._latency_samples.append(max(duration, 0.0))
            self._total_processed += 1

            if error_message:
                self._total_failed += 1
                self._last_error = {
                    "message": error_message,
                    "timestamp": datetime.now(timezone.utc),
                }

    async def update_configuration(self, updates: Dict[str, Any]) -> OrchestrationConfig:
        """Update orchestrator configuration and rebuild the graph."""

        if not updates:
            return self.config

        allowed_fields = set(OrchestrationConfig.__annotations__.keys())
        sanitized_updates = {
            key: value
            for key, value in updates.items()
            if key in allowed_fields and value is not None
        }

        if not sanitized_updates:
            return self.config

        async with self._config_lock:
            self.config = replace(self.config, **sanitized_updates)
            self.checkpointer = (
                MemorySaver() if self.config.checkpoint_enabled else None
            )
            self._build_graph()
            return self.config

    async def get_runtime_status(self) -> Dict[str, Any]:
        """Return telemetry snapshot for orchestration runtime."""

        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        async with self._stats_lock:
            active_sessions = len(self._active_sessions)
            total_processed = self._total_processed
            failed_sessions = self._total_failed
            latency_samples = list(self._latency_samples)
            last_error = self._last_error.copy() if self._last_error else None

        average_latency = (
            sum(latency_samples) / len(latency_samples)
            if latency_samples
            else 0.0
        )
        p95_latency = self._percentile(latency_samples, 0.95)

        return {
            "active_sessions": active_sessions,
            "total_processed": total_processed,
            "failed_sessions": failed_sessions,
            "uptime": uptime,
            "average_latency": average_latency,
            "p95_latency": p95_latency,
            "last_error": last_error,
        }

    @staticmethod
    def _percentile(samples: List[float], percentile: float) -> float:
        """Calculate percentile for latency samples."""

        if not samples:
            return 0.0

        ordered = sorted(samples)
        index = max(0, min(len(ordered) - 1, int(round(percentile * (len(ordered) - 1)))))
        return ordered[index]


# Factory function for easy instantiation
def create_orchestrator(config: OrchestrationConfig = None) -> LangGraphOrchestrator:
    """Create a new LangGraph orchestrator instance"""
    return LangGraphOrchestrator(config)


# Default orchestrator instance
default_orchestrator = None

def get_default_orchestrator() -> LangGraphOrchestrator:
    """Get the default orchestrator instance (singleton)"""
    global default_orchestrator
    if default_orchestrator is None:
        default_orchestrator = create_orchestrator()
    return default_orchestrator
