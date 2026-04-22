"""
Tool Execution Node

Implements unified tool execution through AgentMedusa with extension support.
Ensures all tools pass through Medusa execution engine with proper permissions.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..contracts.orchestration_state import LangGraphOrchestrationState
from ai_karen_engine.agent_medusa.contracts import (
    ToolExecutionRequest,
    ToolExecutionResult,
    MedusaArbitrator,
    MedusaExecutionEngine,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtensionRuntimeConfig:
    """Configuration for extension runtime execution"""

    manifest_required: bool = True
    rbac_enabled: bool = True
    sandbox_enabled: bool = True
    permissions_check: bool = True


class ToolExecutionNode:
    """Unified tool execution through AgentMedusa"""

    def __init__(self, config: Optional[ExtensionRuntimeConfig] = None):
        self.config = config or ExtensionRuntimeConfig()
        self.execution_engine = MedusaExecutionEngine()
        self.arbitrator = MedusaArbitrator()

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """
        Execute tools through unified AgentMedusa pipeline

        Flow: tool_exec node → MedusaExecutionEngine → arbitration → MedusaArbitrator
        """
        logger.info("Tool execution processing")

        try:
            # Extract tool calls from state
            tool_calls = state.get("tool_calls", [])
            if not tool_calls:
                logger.info("No tool calls to execute")
                return state

            # Execute tools
            state = await self.execute_tools(state, tool_calls)

            # Generate execution summary
            if "tool_results" in state:
                state["execution_summary"] = {
                    "executed_tools": len(state["tool_results"]),
                    "successful_executions": len(
                        [
                            r
                            for r in state["tool_results"]
                            if r.get("status") == "success"
                        ]
                    ),
                    "failed_executions": len(
                        [
                            r
                            for r in state["tool_results"]
                            if r.get("status") == "failed"
                        ]
                    ),
                }

            logger.info("Tool execution completed")

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            state.setdefault("errors", []).append(f"Tool execution error: {str(e)}")

        return state

    async def execute_tools(
        self, state: LangGraphOrchestrationState, tool_calls: List[Dict[str, Any]]
    ) -> LangGraphOrchestrationState:
        """
        Execute tools through unified AgentMedusa pipeline

        Flow: tool_exec node → MedusaExecutionEngine → arbitration → MedusaArbitrator
        """
        logger.info(f"Executing {len(tool_calls)} tools through AgentMedusa")

        try:
            execution_results = []

            for tool_call in tool_calls:
                # Create execution request
                request = self._create_execution_request(tool_call, state)

                # Execute through Medusa
                result = await self.execution_engine.execute_tool(request)

                # Apply arbitration if needed
                if result.requires_arbitration:
                    result = await self.arbitrator.arbitrate(result)

                execution_results.append(result)

            # Update state with results
            state["tool_execution_results"] = execution_results
            state["tool_results"] = [
                self._result_to_dict(result) for result in execution_results
            ]

            # Check for execution errors
            failed_executions = [
                result for result in execution_results if result.status == "failed"
            ]

            if failed_executions:
                error_messages = [
                    f"Tool '{result.tool_name}' failed: {result.error}"
                    for result in failed_executions
                ]
                state.setdefault("errors", []).extend(error_messages)

            logger.info(f"Tool execution completed: {len(execution_results)} results")

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            state.setdefault("errors", []).append(f"Tool execution error: {str(e)}")

        return state

    def _create_execution_request(
        self, tool_call: Dict[str, Any], state: LangGraphOrchestrationState
    ) -> ToolExecutionRequest:
        """Create AgentMedusa execution request"""

        # Extract tool parameters
        tool_name = tool_call.get("tool", "")
        parameters = tool_call.get("parameters", {})

        # Apply extension runtime policies
        if self.config.manifest_required:
            self._validate_tool_manifest(tool_name, state)

        if self.config.permissions_check:
            self._check_tool_permissions(tool_name, state)

        # Create execution request
        request = ToolExecutionRequest(
            tool_name=tool_name,
            parameters=parameters,
            context={
                "session_id": state.get("session_id"),
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
                "memory_context": state.get("memory_context"),
                "safety_status": state.get("safety_status"),
            },
            metadata={
                "execution_plan": state.get("execution_plan"),
                "selected_provider": state.get("selected_provider"),
                "selected_model": state.get("selected_model"),
                "streaming_enabled": state.get("streaming_enabled", False),
            },
        )

        return request

    def _validate_tool_manifest(
        self, tool_name: str, state: LangGraphOrchestrationState
    ):
        """Validate tool manifest for extension runtime"""
        # This would typically check against extension manifests
        # For now, basic validation
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError(f"Invalid tool name: {tool_name}")

        # Check if tool is allowed in current degraded mode
        degraded_mode = state.get("runtime_level", "FULL")
        if degraded_mode in ["REDUCED", "SAFE", "EMERGENCY"]:
            allowed_tools = self._get_degraded_mode_allowed_tools(degraded_mode)
            if tool_name not in allowed_tools:
                raise ValueError(
                    f"Tool '{tool_name}' not allowed in {degraded_mode} mode"
                )

    def _check_tool_permissions(
        self, tool_name: str, state: LangGraphOrchestrationState
    ):
        """Check tool permissions for extension runtime"""
        # This would typically implement RBAC checks
        # For now, basic permission validation
        user_id = state.get("user_id")
        if not user_id:
            raise ValueError("User ID required for tool execution")

        # Check if user has permission to use this tool
        # This would integrate with the auth system
        pass

    def _get_degraded_mode_allowed_tools(self, mode: str) -> List[str]:
        """Get tools allowed in degraded mode"""
        tool_restrictions = {
            "REDUCED": ["basic_search", "information_retrieval", "text_analysis"],
            "SAFE": ["basic_search", "text_analysis"],
            "EMERGENCY": ["basic_search"],
        }
        return tool_restrictions.get(mode, [])

    def _result_to_dict(self, result: ToolExecutionResult) -> Dict[str, Any]:
        """Convert execution result to dictionary"""
        return {
            "tool_name": result.tool_name,
            "status": result.status,
            "output": result.output,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata,
        }


async def tool_exec_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """
    Tool execution node for LangGraph orchestration

    Routes execution through AgentMedusa with extension runtime policies
    """
    logger.info("Tool execution processing")

    try:
        # Extract tool calls from state
        tool_calls = state.get("tool_calls", [])
        if not tool_calls:
            logger.info("No tool calls to execute")
            return state

        # Initialize execution node
        exec_node = ToolExecutionNode()

        # Execute tools
        state = await exec_node.execute_tools(state, tool_calls)

        # Generate execution summary
        if "tool_results" in state:
            state["execution_summary"] = {
                "executed_tools": len(state["tool_results"]),
                "successful_executions": len(
                    [r for r in state["tool_results"] if r.get("status") == "success"]
                ),
                "failed_executions": len(
                    [r for r in state["tool_results"] if r.get("status") == "failed"]
                ),
            }

        logger.info("Tool execution completed")

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        state.setdefault("errors", []).append(f"Tool execution error: {str(e)}")

    return state
