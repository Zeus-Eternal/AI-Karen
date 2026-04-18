"""
LangChain Adapter for Agent Architecture System.

This module provides integration between LangChain and the agent architecture system,
enabling agents to leverage LangChain's capabilities while maintaining compatibility
with the existing agent framework.
"""

import os
import logging
import json
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from enum import Enum

# LangChain imports
try:
    # Import core LangChain components
    from langchain.agents import AgentExecutor
    from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.tools import BaseTool
    from langchain.llms.base import BaseLLM
    from langchain.chat_models.base import BaseChatModel
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    # Import specific agent types
    try:
        from langchain.agents.conversational_chat.base import ConversationalChatAgent
        from langchain.agents.structured_chat.base import StructuredChatAgent
        from langchain.agents.agent_types import AgentType
        HAS_SPECIFIC_AGENTS = True
    except ImportError:
        HAS_SPECIFIC_AGENTS = False
        # Create placeholder classes
        class ConversationalChatAgent:
            @classmethod
            def from_llm_and_tools(cls, **kwargs):
                raise NotImplementedError("ConversationalChatAgent not available")
        
        class StructuredChatAgent:
            @classmethod
            def from_llm_and_tools(cls, **kwargs):
                raise NotImplementedError("StructuredChatAgent not available")
        
        class AgentType:
            pass
    
    # Import Tool class
    try:
        from langchain.tools import Tool as LangChainTool
        HAS_TOOL_CLASS = True
    except ImportError:
        HAS_TOOL_CLASS = False
        class LangChainTool:
            def __init__(self, **kwargs):
                raise NotImplementedError("LangChain Tool class not available")
    
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Create placeholder classes for type hints if LangChain is not available
    class AgentExecutor:
        pass
    
    class ConversationalChatAgent:
        pass
    
    class StructuredChatAgent:
        pass
    
    class AIMessage:
        pass
    
    class HumanMessage:
        pass
    
    class SystemMessage:
        pass
    
    class BaseMessage:
        pass
    
    class ConversationBufferMemory:
        pass
    
    class ConversationSummaryMemory:
        pass
    
    class BaseTool:
        pass
    
    class BaseLLM:
        pass
    
    class BaseChatModel:
        pass
    
    class PromptTemplate:
        pass
    
    class LLMChain:
        pass
    
    class AgentType:
        pass
    
    class LangChainTool:
        pass
    
    HAS_SPECIFIC_AGENTS = False
    HAS_TOOL_CLASS = False

# Local application imports
from ..internal.agent_schemas import (
    AgentDefinition, AgentTask, AgentResponse, AgentTool, AgentMemory,
    AgentStatus, TaskStatus, MessageStatus
)
from ..internal.agent_validation import AgentValidation
from ..agent_memory import EnhancedAgentMemory
from ..agent_tool_broker import AgentToolBroker

logger = logging.getLogger(__name__)


class LangChainAgentType(str, Enum):
    """LangChain agent type enumeration."""
    ZERO_SHOT_REACT_DESCRIPTION = "zero_shot_react_description"
    REACT_DOCSTORE = "react_docstore"
    SELF_ASK_WITH_SEARCH = "self_ask_with_search"
    CONVERSATIONAL_REACT_DESCRIPTION = "conversational_react_description"
    CHAT_CONVERSATIONAL_REACT_DESCRIPTION = "chat_conversational_react_description"
    CHAT_ZERO_SHOT_REACT_DESCRIPTION = "chat_zero_shot_react_description"
    STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION = "structured_chat_zero_shot_react_description"
    OPENAI_FUNCTIONS = "openai_functions"
    OPENAI_MULTI_FUNCTIONS = "openai_multi_functions"


class LangChainAdapter:
    """
    Adapter for integrating LangChain with the agent architecture system.
    
    This adapter provides functionality to:
    1. Create and manage LangChain agents
    2. Convert between LangChain and agent architecture data structures
    3. Execute LangChain agents with proper error handling
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
        Initialize the LangChain adapter.
        
        Args:
            config: Configuration dictionary for the adapter
            agent_validation: Agent validation service instance
            agent_memory: Agent memory service instance
            tool_broker: Agent tool broker instance
        """
        if not HAS_LANGCHAIN:
            logger.error("LangChain is not installed. Please install it to use this adapter.")
            raise ImportError("LangChain is required but not installed")
        
        self.config = config or {}
        self.agent_validation = agent_validation
        self.agent_memory = agent_memory
        self.tool_broker = tool_broker
        
        # LangChain components
        self._agents: Dict[str, AgentExecutor] = {}
        self._llms: Dict[str, Union[BaseLLM, BaseChatModel]] = {}
        self._tools: Dict[str, BaseTool] = {}
        self._memories: Dict[str, Union[ConversationBufferMemory, ConversationSummaryMemory]] = {}
        
        # Adapter configuration
        self._default_agent_type = LangChainAgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION
        self._default_memory_type = "buffer"  # Can be "buffer" or "summary"
        self._enable_error_handling = True
        self._max_execution_time = 300  # seconds
        self._verbose = self.config.get("verbose", False)
        
        logger.info("LangChain adapter initialized successfully")
    
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
        logger.info(f"Registered LLM {llm_id} with LangChain adapter")
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
        logger.info(f"Unregistered LLM {llm_id} from LangChain adapter")
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
        logger.info(f"Registered tool {tool_id} with LangChain adapter")
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
        logger.info(f"Unregistered tool {tool_id} from LangChain adapter")
        return True
    
    async def create_agent(
        self,
        agent_definition: AgentDefinition,
        llm_id: Optional[str] = None,
        agent_type: Optional[LangChainAgentType] = None,
        tools: Optional[List[str]] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a LangChain agent from an agent definition.
        
        Args:
            agent_definition: Agent definition to convert to LangChain agent
            llm_id: ID of the LLM to use (if None, uses the first available)
            agent_type: Type of LangChain agent to create
            tools: List of tool IDs to include in the agent
            memory_config: Configuration for the agent's memory
            
        Returns:
            True if agent creation was successful, False otherwise
        """
        if not HAS_LANGCHAIN:
            logger.error("LangChain is not available")
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
        
        # Get agent type
        agent_type = agent_type or self._default_agent_type
        
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
        
        # Create appropriate agent based on type
        try:
            if not HAS_SPECIFIC_AGENTS:
                logger.error("Specific LangChain agent types are not available")
                return False
                
            if agent_type == LangChainAgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION:
                agent = ConversationalChatAgent.from_llm_and_tools(
                    llm=llm,
                    tools=agent_tools,
                    verbose=self._verbose
                )
            elif agent_type == LangChainAgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION:
                agent = StructuredChatAgent.from_llm_and_tools(
                    llm=llm,
                    tools=agent_tools,
                    verbose=self._verbose
                )
            else:
                logger.error(f"Unsupported agent type: {agent_type}")
                return False
            
            # Create agent executor with appropriate parameters
            agent_executor_kwargs = {
                "agent": agent,
                "tools": agent_tools,
                "verbose": self._verbose,
                "max_execution_time": self._max_execution_time,
                "handle_parsing_errors": self._enable_error_handling
            }
            
            # Add memory if available
            if memory:
                agent_executor_kwargs["memory"] = memory
            
            # Create agent executor
            agent_executor = AgentExecutor(**agent_executor_kwargs)
            
            # Store the agent
            self._agents[agent_definition.agent_id] = agent_executor
            logger.info(f"Created LangChain agent for {agent_definition.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create LangChain agent: {e}")
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
        memory_type = memory_config.get("type", self._default_memory_type)
        
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
    
    async def execute_agent(
        self, 
        agent_id: str, 
        task: AgentTask
    ) -> AgentResponse:
        """
        Execute a LangChain agent with a task.
        
        Args:
            agent_id: ID of the agent to execute
            task: Task to execute
            
        Returns:
            Agent response with execution results
        """
        if agent_id not in self._agents:
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=agent_id,
                success=False,
                data={},
                error=f"Agent {agent_id} not found",
                execution_time=0.0
            )
        
        agent_executor = self._agents[agent_id]
        
        # Convert task to LangChain input format
        lc_input = await self._convert_task_to_langchain_input(task)
        
        try:
            # Execute the agent
            start_time = datetime.utcnow()
            
            # Try to use invoke method first, fallback to run if not available
            if hasattr(agent_executor, 'invoke'):
                result = agent_executor.invoke(lc_input)
            elif hasattr(agent_executor, 'run'):
                result = agent_executor.run(lc_input)
            else:
                raise AttributeError("AgentExecutor has no invoke or run method")
                
            end_time = datetime.utcnow()
            
            # Calculate execution time
            execution_time = (end_time - start_time).total_seconds()
            
            # Convert result to AgentResponse
            response = await self._convert_langchain_output_to_agent_response(
                result, task, agent_id, execution_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing agent {agent_id}: {e}")
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=agent_id,
                success=False,
                data={},
                error=str(e),
                execution_time=0.0
            )
    
    async def _convert_task_to_langchain_input(self, task: AgentTask) -> Dict[str, Any]:
        """Convert an AgentTask to LangChain input format."""
        # Extract the main task description
        input_text = task.description or task.task_type
        
        # Add input data to the input text
        if task.input_data:
            input_data_str = json.dumps(task.input_data, indent=2)
            input_text += f"\n\nInput Data:\n{input_data_str}"
        
        return {"input": input_text}
    
    async def _convert_langchain_output_to_agent_response(
        self, 
        result: Any, 
        task: AgentTask, 
        agent_id: str, 
        execution_time: float
    ) -> AgentResponse:
        """Convert LangChain output to AgentResponse format."""
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
            agent_id=agent_id,
            success=True,
            data=data,
            message="Task completed successfully",
            execution_time=execution_time
        )
    
    async def integrate_with_memory(self, agent_id: str) -> bool:
        """
        Integrate a LangChain agent with the agent memory system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if not self.agent_memory:
            logger.error("Agent memory service not available")
            return False
        
        try:
            # Get the agent's memory
            agent_executor = self._agents[agent_id]
            memory = getattr(agent_executor, "memory", None)
            
            if not memory:
                logger.error(f"Agent {agent_id} has no memory component")
                return False
            
            # Load the agent's memories from the memory service
            agent_memories = await self.agent_memory.list_memories(
                agent_id=agent_id,
                limit=100,
                include_shared=False
            )
            
            # Convert memories to LangChain format and add to memory
            for agent_memory_data in agent_memories:
                if agent_memory_data.get("memory_type") == "conversation":
                    # Convert to LangChain message format
                    content = agent_memory_data.get("content", {})
                    if "role" in content and "text" in content:
                        if content["role"] == "human":
                            message = HumanMessage(content=content["text"])
                        elif content["role"] == "ai":
                            message = AIMessage(content=content["text"])
                        else:
                            continue
                        
                        # Add to memory
                        if hasattr(memory, "chat_memory"):
                            memory.chat_memory.add_message(message)
            
            logger.info(f"Integrated agent {agent_id} with memory system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate agent {agent_id} with memory system: {e}")
            return False
    
    async def integrate_with_tools(self, agent_id: str) -> bool:
        """
        Integrate a LangChain agent with the agent tool system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if not self.tool_broker:
            logger.error("Agent tool broker not available")
            return False
        
        try:
            # Get the agent's tools from the tool broker
            agent_tools = await self.tool_broker.get_agent_tools(agent_id)
            
            # Convert tools to LangChain format
            langchain_tools = []
            for tool_data in agent_tools:
                langchain_tool = await self._convert_agent_tool_to_langchain_tool(tool_data)
                if langchain_tool:
                    langchain_tools.append(langchain_tool)
            
            # Update the agent with new tools
            if langchain_tools:
                agent_executor = self._agents[agent_id]
                
                # Update tools in the agent executor
                if hasattr(agent_executor, 'tools'):
                    agent_executor.tools = langchain_tools
                
                # If the agent has a tool-aware component, update it as well
                if hasattr(agent_executor, 'agent'):
                    if hasattr(agent_executor.agent, "tools"):
                        agent_executor.agent.tools = langchain_tools
            
            logger.info(f"Integrated agent {agent_id} with {len(langchain_tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate agent {agent_id} with tool system: {e}")
            return False
    
    async def _convert_agent_tool_to_langchain_tool(self, tool_data: Dict[str, Any]) -> Optional[BaseTool]:
        """Convert an AgentTool to LangChain BaseTool format."""
        try:
            # Extract tool information
            tool_id = tool_data.get("tool_id")
            tool_name = tool_data.get("name")
            tool_description = tool_data.get("description", "")
            
            if not tool_id or not tool_name:
                logger.error("Tool data missing required fields")
                return None
            
            # Create a wrapper function for the tool
            async def _tool_wrapper(**kwargs):
                # Execute the tool through the tool broker
                if not self.tool_broker:
                    raise ValueError("Tool broker not available")
                
                result = await self.tool_broker.execute_tool(
                    agent_id="langchain_adapter",
                    tool_id=tool_id,
                    parameters=kwargs
                )
                
                if result.get("status") == "error":
                    raise ValueError(result.get("error", "Tool execution failed"))
                
                return result.get("result", {})
            
            # Create a LangChain tool
            if not HAS_TOOL_CLASS:
                logger.error("LangChain Tool class is not available")
                return None
                
            langchain_tool = LangChainTool(
                name=tool_name,
                description=tool_description,
                func=_tool_wrapper
            )
            
            return langchain_tool
            
        except Exception as e:
            logger.error(f"Failed to convert agent tool to LangChain tool: {e}")
            return None
    
    async def integrate_with_models(self, agent_id: str, model_id: str) -> bool:
        """
        Integrate a LangChain agent with AI Orchestrator models.
        
        Args:
            agent_id: ID of the agent to integrate
            model_id: ID of the model to integrate with
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if model_id not in self._llms:
            logger.error(f"Model {model_id} not found")
            return False
        
        try:
            # Get the agent and model
            agent_executor = self._agents[agent_id]
            model = self._llms[model_id]
            
            # Update the agent's LLM
            if hasattr(agent_executor, 'agent'):
                if hasattr(agent_executor.agent, "llm_chain"):
                    agent_executor.agent.llm_chain.llm = model
                elif hasattr(agent_executor.agent, "llm"):
                    agent_executor.agent.llm = model
            
            logger.info(f"Integrated agent {agent_id} with model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate agent {agent_id} with model {model_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentExecutor]:
        """
        Get a LangChain agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            AgentExecutor instance if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        List all agent IDs in the adapter.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove a LangChain agent from the adapter.
        
        Args:
            agent_id: ID of the agent to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        del self._agents[agent_id]
        logger.info(f"Removed agent {agent_id} from LangChain adapter")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the LangChain adapter.
        
        Returns:
            Health status information
        """
        return {
            "service": "langchain_adapter",
            "timestamp": datetime.utcnow().isoformat(),
            "langchain_available": HAS_LANGCHAIN,
            "specific_agents_available": HAS_SPECIFIC_AGENTS,
            "tool_class_available": HAS_TOOL_CLASS,
            "agents_count": len(self._agents),
            "llms_count": len(self._llms),
            "tools_count": len(self._tools),
            "memories_count": len(self._memories),
            "agent_validation_available": self.agent_validation is not None,
            "agent_memory_available": self.agent_memory is not None,
            "tool_broker_available": self.tool_broker is not None
        }