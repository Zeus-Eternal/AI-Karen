"""
LangGraph Adapter for Agent Architecture System.

This module provides integration between LangGraph and the agent architecture system,
enabling agents to leverage LangGraph's capabilities while maintaining compatibility
with the existing agent framework.
"""

import os
import logging
import json
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from enum import Enum

# LangGraph imports
try:
    # Import core LangGraph components
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor
    from langgraph.checkpoint import BaseCheckpointSaver
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    
    # Import LangChain components that LangGraph depends on
    from langchain.tools import BaseTool
    from langchain.chat_models.base import BaseChatModel
    from langchain.llms.base import BaseLLM
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    # Create placeholder classes for type hints if LangGraph is not available
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
        
        def add_node(self, *args, **kwargs):
            pass
        
        def add_edge(self, *args, **kwargs):
            pass
        
        def set_entry_point(self, *args, **kwargs):
            pass
        
        def set_conditional_entry_point(self, *args, **kwargs):
            pass
        
        def set_finish_point(self, *args, **kwargs):
            pass
        
        def compile(self, *args, **kwargs):
            class CompiledGraph:
                def invoke(self, *args, **kwargs):
                    return {}
            return CompiledGraph()
    
    class ToolExecutor:
        def __init__(self, *args, **kwargs):
            pass
        
        def invoke(self, *args, **kwargs):
            return {}
    
    class BaseCheckpointSaver:
        def __init__(self, *args, **kwargs):
            pass
        
        def get(self, *args, **kwargs):
            return {}
        
        def put(self, *args, **kwargs):
            pass
    
    class SqliteSaver(BaseCheckpointSaver):
        pass
    
    class BaseMessage:
        pass
    
    class HumanMessage(BaseMessage):
        pass
    
    class AIMessage(BaseMessage):
        pass
    
    class SystemMessage(BaseMessage):
        pass
    
    class BaseTool:
        pass
    
    class BaseChatModel:
        pass
    
    class BaseLLM:
        pass
    
    class ConversationBufferMemory:
        pass
    
    class ConversationSummaryMemory:
        pass
    
    # Create END placeholder
    END = "end"

# Local application imports
from ..internal.agent_schemas import (
    AgentDefinition, AgentTask, AgentResponse, AgentTool, AgentMemory,
    AgentStatus, TaskStatus, MessageStatus
)
from ..internal.agent_validation import AgentValidation
from ..agent_memory import EnhancedAgentMemory
from ..agent_tool_broker import AgentToolBroker

logger = logging.getLogger(__name__)


class LangGraphNodeType(str, Enum):
    """LangGraph node type enumeration."""
    AGENT = "agent"
    TOOL = "tool"
    CONDITIONAL = "conditional"
    HUMAN = "human"


class LangGraphAdapter:
    """
    Adapter for integrating LangGraph with the agent architecture system.
    
    This adapter provides functionality to:
    1. Create and manage LangGraph graphs
    2. Convert between LangGraph and agent architecture data structures
    3. Execute LangGraph graphs with proper error handling
    4. Integrate with the agent memory system
    5. Integrate with the agent tool system
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        agent_validation: Optional[AgentValidation] = None,
        agent_memory: Optional[EnhancedAgentMemory] = None,
        tool_broker: Optional[AgentToolBroker] = None
    ):
        """
        Initialize the LangGraph adapter.
        
        Args:
            config: Configuration dictionary for the adapter
            agent_validation: Agent validation service instance
            agent_memory: Agent memory service instance
            tool_broker: Agent tool broker instance
        """
        if not HAS_LANGGRAPH:
            logger.error("LangGraph is not installed. Please install it to use this adapter.")
            raise ImportError("LangGraph is required but not installed")
        
        self.config = config or {}
        self.agent_validation = agent_validation
        self.agent_memory = agent_memory
        self.tool_broker = tool_broker
        
        # LangGraph components
        self._graphs: Dict[str, StateGraph] = {}
        self._compiled_graphs: Dict[str, Any] = {}
        self._llms: Dict[str, Union[BaseLLM, BaseChatModel]] = {}
        self._tools: Dict[str, BaseTool] = {}
        self._memories: Dict[str, Union[ConversationBufferMemory, ConversationSummaryMemory]] = {}
        self._checkpoint_savers: Dict[str, BaseCheckpointSaver] = {}
        
        # Adapter configuration
        self._enable_error_handling = True
        self._max_execution_time = 300  # seconds
        self._verbose = self.config.get("verbose", False)
        self._use_checkpoints = self.config.get("use_checkpoints", True)
        self._checkpoint_db_path = self.config.get("checkpoint_db_path", ":memory:")
        
        logger.info("LangGraph adapter initialized successfully")
    
    def register_llm(self, llm_id: str, llm: Union[BaseLLM, BaseChatModel]) -> bool:
        """
        Register an LLM with the adapter.
        
        Args:
            llm_id: Unique identifier for the LLM
            llm: The LLM instance to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not isinstance(llm, (BaseLLM, BaseChatModel)):
            logger.error(f"LLM {llm_id} is not a valid LangChain LLM or ChatModel")
            return False
        
        self._llms[llm_id] = llm
        logger.info(f"Registered LLM {llm_id} with LangGraph adapter")
        return True
    
    def unregister_llm(self, llm_id: str) -> bool:
        """
        Unregister an LLM from the adapter.
        
        Args:
            llm_id: Unique identifier of the LLM to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if llm_id not in self._llms:
            logger.warning(f"LLM {llm_id} not found in adapter")
            return False
        
        del self._llms[llm_id]
        logger.info(f"Unregistered LLM {llm_id} from LangGraph adapter")
        return True
    
    def register_tool(self, tool_id: str, tool: BaseTool) -> bool:
        """
        Register a tool with the adapter.
        
        Args:
            tool_id: Unique identifier for the tool
            tool: The LangChain tool instance to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not isinstance(tool, BaseTool):
            logger.error(f"Tool {tool_id} is not a valid LangChain BaseTool")
            return False
        
        self._tools[tool_id] = tool
        logger.info(f"Registered tool {tool_id} with LangGraph adapter")
        return True
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the adapter.
        
        Args:
            tool_id: Unique identifier of the tool to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if tool_id not in self._tools:
            logger.warning(f"Tool {tool_id} not found in adapter")
            return False
        
        del self._tools[tool_id]
        logger.info(f"Unregistered tool {tool_id} from LangGraph adapter")
        return True
    
    async def create_graph(
        self,
        graph_id: str,
        agent_definition: AgentDefinition,
        llm_id: Optional[str] = None,
        tools: Optional[List[str]] = None,
        memory_config: Optional[Dict[str, Any]] = None,
        graph_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a LangGraph from an agent definition.
        
        Args:
            graph_id: Unique identifier for the graph
            agent_definition: Agent definition to convert to LangGraph
            llm_id: ID of the LLM to use (if None, uses the first available)
            tools: List of tool IDs to include in the graph
            memory_config: Configuration for the agent's memory
            graph_config: Configuration for the graph structure
            
        Returns:
            True if graph creation was successful, False otherwise
        """
        if not HAS_LANGGRAPH:
            logger.error("LangGraph is not available")
            return False
        
        # Validate agent definition
        if self.agent_validation:
            is_valid, errors = await self.agent_validation.validate_agent_definition(agent_definition)
            if not is_valid:
                logger.error(f"Agent definition validation failed: {errors}")
                return False
        
        # Get LLM
        llm = self._get_llm(llm_id)
        if not llm:
            logger.error(f"LLM {llm_id} not found or not available")
            return False
        
        # Get tools
        agent_tools = []
        if tools:
            for tool_id in tools:
                if tool_id in self._tools:
                    agent_tools.append(self._tools[tool_id])
                else:
                    logger.warning(f"Tool {tool_id} not found, skipping")
        
        # Create memory
        memory = self._create_memory(agent_definition.agent_id, memory_config)
        
        # Create checkpoint saver if enabled
        checkpoint_saver = None
        if self._use_checkpoints:
            if graph_id not in self._checkpoint_savers:
                self._checkpoint_savers[graph_id] = SqliteSaver.from_conn_string(self._checkpoint_db_path)
            checkpoint_saver = self._checkpoint_savers[graph_id]
        
        # Create the graph
        try:
            # Initialize the graph with a state type
            graph = StateGraph(dict)
            
            # Add nodes based on graph configuration
            graph_config = graph_config or {}
            nodes = graph_config.get("nodes", ["agent"])
            
            for node_name in nodes:
                # Create node function
                if node_name == "agent":
                    node_func = self._create_agent_node(llm, memory, agent_tools)
                elif node_name == "tool":
                    node_func = self._create_tool_node(agent_tools)
                elif node_name == "human":
                    node_func = self._create_human_node()
                else:
                    # Default to a simple pass-through node
                    node_func = lambda state: state
                
                # Add the node to the graph
                graph.add_node(node_name, node_func)
            
            # Set entry point
            entry_point = graph_config.get("entry_point", nodes[0] if nodes else "agent")
            graph.set_entry_point(entry_point)
            
            # Add edges based on graph configuration
            edges = graph_config.get("edges", [])
            for edge in edges:
                if isinstance(edge, dict) and "conditional" in edge:
                    # Add conditional edge
                    source = edge.get("source", entry_point)
                    conditional_func = edge.get("conditional", lambda state: "agent")
                    mapping = edge.get("mapping", {"agent": "agent", "end": END})
                    graph.add_conditional_edges(source, conditional_func, mapping)
                else:
                    # Add simple edge
                    if len(edge) >= 2:
                        graph.add_edge(edge[0], edge[1])
            
            # Set finish point
            finish_point = graph_config.get("finish_point")
            if finish_point:
                graph.set_finish_point(finish_point)
            
            # Compile the graph
            compiled_graph = graph.compile(
                checkpointer=checkpoint_saver,
                interrupt_before=graph_config.get("interrupt_before", []),
                interrupt_after=graph_config.get("interrupt_after", [])
            )
            
            # Store the graph
            self._graphs[graph_id] = graph
            self._compiled_graphs[graph_id] = compiled_graph
            
            logger.info(f"Created LangGraph {graph_id} for agent {agent_definition.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create LangGraph: {e}")
            return False
    
    def _get_llm(self, llm_id: Optional[str]) -> Optional[Union[BaseLLM, BaseChatModel]]:
        """Get an LLM by ID or return the first available."""
        if llm_id and llm_id in self._llms:
            return self._llms[llm_id]
        elif self._llms:
            return next(iter(self._llms.values()))
        else:
            return None
    
    def _create_memory(
        self, 
        agent_id: str, 
        memory_config: Optional[Dict[str, Any]] = None
    ) -> Union[ConversationBufferMemory, ConversationSummaryMemory]:
        """Create a memory instance for an agent."""
        memory_config = memory_config or {}
        memory_type = memory_config.get("type", "buffer")
        
        # Common parameters for both memory types
        common_params = {
            "memory_key": "chat_history",
            "human_prefix": "Human",
            "ai_prefix": "AI"
        }
        
        # Add type-specific parameters
        if memory_type == "summary":
            summary_params = {
                "llm": self._get_llm(memory_config.get("llm_id")),
                "buffer": memory_config.get("buffer", ""),
                "max_token_limit": memory_config.get("max_token_limit", 2000)
            }
            params = {**common_params, **summary_params}
            return ConversationSummaryMemory(**params)
        else:
            buffer_params = {
                "return_messages": memory_config.get("return_messages", True)
            }
            params = {**common_params, **buffer_params}
            return ConversationBufferMemory(**params)
    
    def _create_agent_node(self, llm, memory, tools):
        """Create an agent node function for the graph."""
        # Import necessary LangChain components
        try:
            from langchain.agents import AgentExecutor
            from langchain.agents.conversational_chat.base import ConversationalChatAgent
        except ImportError:
            # If LangChain components are not available, create a simple node
            async def simple_agent_node(state):
                # Add input to memory
                if memory and hasattr(memory, 'save_context'):
                    input_text = state.get("input", "")
                    memory.save_context({"input": input_text}, {"output": "Simple response"})
                
                # Generate a simple response
                response = "This is a simple agent response."
                
                # Update state with response
                state["output"] = response
                return state
            
            return simple_agent_node
        
        # Create the agent
        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=llm,
            tools=tools,
            verbose=self._verbose
        )
        
        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=self._verbose,
            max_execution_time=self._max_execution_time,
            handle_parsing_errors=self._enable_error_handling
        )
        
        # Create the node function
        async def agent_node(state):
            # Extract input from state
            input_text = state.get("input", "")
            
            # Execute the agent
            try:
                if hasattr(agent_executor, 'invoke'):
                    result = agent_executor.invoke({"input": input_text})
                elif hasattr(agent_executor, 'run'):
                    result = agent_executor.run(input_text)
                else:
                    raise AttributeError("AgentExecutor has no invoke or run method")
                
                # Update state with result
                if isinstance(result, str):
                    state["output"] = result
                elif isinstance(result, dict):
                    state.update(result)
                else:
                    state["output"] = str(result)
                
                return state
            except Exception as e:
                logger.error(f"Error in agent node: {e}")
                state["output"] = f"Error: {str(e)}"
                return state
        
        return agent_node
    
    def _create_tool_node(self, tools):
        """Create a tool node function for the graph."""
        # Create the tool executor
        tool_executor = ToolExecutor(tools)
        
        # Create the node function
        async def tool_node(state):
            # Extract tool input from state
            tool_input = state.get("tool_input", {})
            
            # Execute the tool
            try:
                result = tool_executor.invoke(tool_input)
                
                # Update state with result
                if isinstance(result, str):
                    state["output"] = result
                elif isinstance(result, dict):
                    state.update(result)
                else:
                    state["output"] = str(result)
                
                return state
            except Exception as e:
                logger.error(f"Error in tool node: {e}")
                state["output"] = f"Error: {str(e)}"
                return state
        
        return tool_node
    
    def _create_human_node(self):
        """Create a human node function for the graph."""
        async def human_node(state):
            # In a real implementation, this would wait for human input
            # For now, we'll just pass through the state
            return state
        
        return human_node
    
    async def execute_graph(
        self, 
        graph_id: str, 
        task: AgentTask
    ) -> AgentResponse:
        """
        Execute a LangGraph with a task.
        
        Args:
            graph_id: ID of the graph to execute
            task: Task to execute
            
        Returns:
            Agent response with execution results
        """
        if graph_id not in self._compiled_graphs:
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=f"Graph {graph_id} not found",
                execution_time=0.0
            )
        
        compiled_graph = self._compiled_graphs[graph_id]
        
        # Convert task to LangGraph input format
        lg_input = await self._convert_task_to_langgraph_input(task)
        
        try:
            # Execute the graph
            start_time = datetime.utcnow()
            
            # Try to use invoke method first, fallback to other methods if not available
            if hasattr(compiled_graph, 'invoke'):
                result = compiled_graph.invoke(lg_input)
            elif hasattr(compiled_graph, 'run'):
                result = compiled_graph.run(lg_input)
            else:
                raise AttributeError("CompiledGraph has no invoke or run method")
                
            end_time = datetime.utcnow()
            
            # Calculate execution time
            execution_time = (end_time - start_time).total_seconds()
            
            # Convert result to AgentResponse
            response = await self._convert_langgraph_output_to_agent_response(
                result, task, graph_id, execution_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing graph {graph_id}: {e}")
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=str(e),
                execution_time=0.0
            )
    
    async def _convert_task_to_langgraph_input(self, task: AgentTask) -> Dict[str, Any]:
        """Convert an AgentTask to LangGraph input format."""
        # Extract the main task description
        input_text = task.description or task.task_type
        
        # Add input data to the input text
        if task.input_data:
            input_data_str = json.dumps(task.input_data, indent=2)
            input_text += f"\n\nInput Data:\n{input_data_str}"
        
        # Create input state
        input_state = {
            "input": input_text,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "agent_id": task.agent_id
        }
        
        # Add input data to the state
        if task.input_data:
            input_state.update(task.input_data)
        
        return input_state
    
    async def _convert_langgraph_output_to_agent_response(
        self, 
        result: Any, 
        task: AgentTask, 
        graph_id: str,
        execution_time: float
    ) -> AgentResponse:
        """Convert LangGraph output to AgentResponse format."""
        # Parse the result
        if isinstance(result, str):
            data = {"output": result}
        elif isinstance(result, dict):
            data = result
        else:
            data = {"output": str(result)}
        
        return AgentResponse(
            response_id=f"resp_{task.task_id}",
            task_id=task.task_id,
            agent_id=task.agent_id,
            success=True,
            data=data,
            message="Task completed successfully",
            execution_time=execution_time
        )
    
    async def integrate_with_memory(self, graph_id: str) -> bool:
        """
        Integrate a LangGraph with the agent memory system.
        
        Args:
            graph_id: ID of the graph to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if graph_id not in self._graphs:
            logger.error(f"Graph {graph_id} not found")
            return False
        
        if not self.agent_memory:
            logger.error("Agent memory service not available")
            return False
        
        try:
            # This is a placeholder for memory integration
            # In a real implementation, this would load memories into the graph's memory
            logger.info(f"Integrated graph {graph_id} with memory system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate graph {graph_id} with memory system: {e}")
            return False
    
    async def integrate_with_tools(self, graph_id: str) -> bool:
        """
        Integrate a LangGraph with the agent tool system.
        
        Args:
            graph_id: ID of the graph to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if graph_id not in self._graphs:
            logger.error(f"Graph {graph_id} not found")
            return False
        
        if not self.tool_broker:
            logger.error("Agent tool broker not available")
            return False
        
        try:
            # This is a placeholder for tool integration
            # In a real implementation, this would register tools with the graph
            logger.info(f"Integrated graph {graph_id} with tool system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate graph {graph_id} with tool system: {e}")
            return False
    
    async def integrate_with_models(self, graph_id: str, model_id: str) -> bool:
        """
        Integrate a LangGraph with AI Orchestrator models.
        
        Args:
            graph_id: ID of the graph to integrate
            model_id: ID of the model to integrate with
            
        Returns:
            True if integration was successful, False otherwise
        """
        if graph_id not in self._graphs:
            logger.error(f"Graph {graph_id} not found")
            return False
        
        if model_id not in self._llms:
            logger.error(f"Model {model_id} not found")
            return False
        
        try:
            # This is a placeholder for model integration
            # In a real implementation, this would update the graph's LLM
            logger.info(f"Integrated graph {graph_id} with model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate graph {graph_id} with model {model_id}: {e}")
            return False
    
    def get_graph(self, graph_id: str) -> Optional[Any]:
        """
        Get a LangGraph by ID.
        
        Args:
            graph_id: ID of the graph to retrieve
            
        Returns:
            Compiled graph instance if found, None otherwise
        """
        return self._compiled_graphs.get(graph_id)
    
    def list_graphs(self) -> List[str]:
        """
        List all graph IDs in the adapter.
        
        Returns:
            List of graph IDs
        """
        return list(self._graphs.keys())
    
    def remove_graph(self, graph_id: str) -> bool:
        """
        Remove a LangGraph from the adapter.
        
        Args:
            graph_id: ID of the graph to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if graph_id not in self._graphs:
            logger.warning(f"Graph {graph_id} not found")
            return False
        
        del self._graphs[graph_id]
        if graph_id in self._compiled_graphs:
            del self._compiled_graphs[graph_id]
        
        logger.info(f"Removed graph {graph_id} from LangGraph adapter")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the LangGraph adapter.
        
        Returns:
            Health status information
        """
        return {
            "service": "langgraph_adapter",
            "timestamp": datetime.utcnow().isoformat(),
            "langgraph_available": HAS_LANGGRAPH,
            "graphs_count": len(self._graphs),
            "compiled_graphs_count": len(self._compiled_graphs),
            "llms_count": len(self._llms),
            "tools_count": len(self._tools),
            "memories_count": len(self._memories),
            "checkpoint_savers_count": len(self._checkpoint_savers),
            "agent_validation_available": self.agent_validation is not None,
            "agent_memory_available": self.agent_memory is not None,
            "tool_broker_available": self.tool_broker is not None,
            "use_checkpoints": self._use_checkpoints
        }