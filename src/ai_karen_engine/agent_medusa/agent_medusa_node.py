from typing import Dict, Any, List
import logging
from .coordinator.medusa_coordinator import MedusaCoordinator
from .contracts.runtime_request import RuntimeRequest

logger = logging.getLogger(__name__)

async def medusa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node that delegates execution to the AgentMedusa runtime"""
    logger.info("Medusa Node -> Entering AgentMedusa execution")
    
    coordinator = MedusaCoordinator()
    
    # Extract data from LangGraph state
    query = ""
    messages = state.get("messages", [])
    if messages:
        query = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
    request = RuntimeRequest(
        query=query,
        session_id=state.get("session_id", "unknown"),
        user_id=state.get("user_id"),
        context=state.get("memory_context", {})
    )
    
    # Execute via Medusa
    response = await coordinator.handle_request(request)
    
    # Update state with Medusa results
    state["response"] = response.content
    state["response_metadata"] = response.metadata
    state["agent_trace"] = response.agent_trace
    
    # Add status for routing within LangGraph if needed
    state["medusa_status"] = response.status.value
    
    return state
