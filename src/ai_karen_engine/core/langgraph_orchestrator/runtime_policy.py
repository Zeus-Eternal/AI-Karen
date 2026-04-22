"""
Runtime Policy Enforcer

Enforces runtime-level policies including degraded mode, routing restrictions,
and execution constraints across the entire orchestration flow.
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum

from .contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


class RuntimeLevel(str, Enum):
    """Runtime execution levels"""

    FULL = "FULL"
    REDUCED = "REDUCED"
    SAFE = "SAFE"
    EMERGENCY = "EMERGENCY"


class PolicyCheckResult:
    """Result of policy enforcement"""

    def __init__(self, allowed: bool, reason: str, severity: str = "info"):
        self.allowed = allowed
        self.reason = reason
        self.severity = severity


@dataclass
class RuntimePolicyConfig:
    """Configuration for runtime policy enforcement"""

    default_level: RuntimeLevel = RuntimeLevel.FULL
    enable_degraded_mode: bool = True
    enable_routing_restrictions: bool = True
    enable_execution_constraints: bool = True
    enable_safety_overrides: bool = True


class RuntimePolicyEnforcer:
    """Enforces runtime policies across orchestration"""

    def __init__(self, config: Optional[RuntimePolicyConfig] = None):
        self.config = config or RuntimePolicyConfig()
        self.level_transitions = {
            RuntimeLevel.FULL: [RuntimeLevel.REDUCED],
            RuntimeLevel.REDUCED: [RuntimeLevel.SAFE, RuntimeLevel.FULL],
            RuntimeLevel.SAFE: [RuntimeLevel.EMERGENCY, RuntimeLevel.REDUCED],
            RuntimeLevel.EMERGENCY: [RuntimeLevel.SAFE],
        }

    async def check_routing_policy(
        self, state: LangGraphOrchestrationState, provider_selection: Dict[str, Any]
    ) -> PolicyCheckResult:
        """Check if routing decision is allowed"""

        if not self.config.enable_routing_restrictions:
            return PolicyCheckResult(True, "Routing restrictions disabled")

        current_level = self._get_runtime_level(state)

        # Check provider restrictions based on runtime level
        provider = provider_selection.get("provider")
        model = provider_selection.get("model")

        if current_level == RuntimeLevel.EMERGENCY:
            # Only allow fallback providers in emergency mode
            if provider not in ["fallback", "local"]:
                return PolicyCheckResult(
                    False,
                    f"Provider '{provider}' not allowed in {current_level} mode",
                    "critical",
                )

        elif current_level == RuntimeLevel.SAFE:
            # Only allow trusted providers in safe mode
            trusted_providers = ["openai", "anthropic", "local"]
            if provider not in trusted_providers:
                return PolicyCheckResult(
                    False,
                    f"Provider '{provider}' not trusted in {current_level} mode",
                    "high",
                )

        elif current_level == RuntimeLevel.REDUCED:
            # Limit model complexity in reduced mode
            complex_models = ["gpt-4", "claude-3", "gemini-pro"]
            if any(model in complex_models for model in [model] if model):
                return PolicyCheckResult(
                    False,
                    f"Complex models not allowed in {current_level} mode",
                    "medium",
                )

        return PolicyCheckResult(True, "Routing policy check passed")

    async def check_execution_policy(
        self, state: LangGraphOrchestrationState, execution_plan: Dict[str, Any]
    ) -> PolicyCheckResult:
        """Check if execution plan is allowed"""

        if not self.config.enable_execution_constraints:
            return PolicyCheckResult(True, "Execution constraints disabled")

        current_level = self._get_runtime_level(state)
        intent = execution_plan.get("intent", "general_chat")

        # Check intent restrictions based on runtime level
        if current_level == RuntimeLevel.EMERGENCY:
            # Only allow basic intents in emergency mode
            allowed_intents = ["general_chat", "information_retrieval", "basic_search"]
            if intent not in allowed_intents:
                return PolicyCheckResult(
                    False,
                    f"Intent '{intent}' not allowed in {current_level} mode",
                    "critical",
                )

        elif current_level == RuntimeLevel.SAFE:
            # Disallow high-risk intents in safe mode
            high_risk_intents = ["code_generation", "file_access", "system_command"]
            if intent in high_risk_intents:
                return PolicyCheckResult(
                    False,
                    f"High-risk intent '{intent}' not allowed in {current_level} mode",
                    "high",
                )

        # Check tool requirements
        tools_required = execution_plan.get("tools_required", [])
        if tools_required:
            tool_check = await self._check_tool_availability(
                tools_required, current_level
            )
            if not tool_check.allowed:
                return tool_check

        return PolicyCheckResult(True, "Execution policy check passed")

    async def check_response_policy(
        self, state: LangGraphOrchestrationState, response_content: str
    ) -> PolicyCheckResult:
        """Check if response content is allowed"""

        if not self.config.enable_safety_overrides:
            return PolicyCheckResult(True, "Safety overrides disabled")

        current_level = self._get_runtime_level(state)

        # Apply content restrictions based on runtime level
        if current_level == RuntimeLevel.EMERGENCY:
            # Only allow minimal responses in emergency mode
            if len(response_content) > 500:
                return PolicyCheckResult(
                    False, "Response too long for emergency mode", "critical"
                )

        elif current_level == RuntimeLevel.SAFE:
            # Disallow potentially harmful content
            harmful_keywords = ["delete", "remove", "disable", "format", "reset"]
            if any(keyword in response_content.lower() for keyword in harmful_keywords):
                return PolicyCheckResult(
                    False, "Response contains potentially harmful content", "high"
                )

        return PolicyCheckResult(True, "Response policy check passed")

    async def enforce_runtime_level_transition(
        self, current_level: RuntimeLevel, target_level: RuntimeLevel
    ) -> PolicyCheckResult:
        """Check if runtime level transition is allowed"""

        if target_level not in self.level_transitions.get(current_level, []):
            return PolicyCheckResult(
                False,
                f"Cannot transition from {current_level} to {target_level}",
                "critical",
            )

        return PolicyCheckResult(True, "Runtime level transition allowed")

    def _get_runtime_level(self, state: LangGraphOrchestrationState) -> RuntimeLevel:
        """Get current runtime level from state"""
        level_str = state.get("runtime_level", self.config.default_level.value)
        try:
            return RuntimeLevel(level_str)
        except ValueError:
            logger.warning(f"Invalid runtime level '{level_str}', using default")
            return self.config.default_level

    async def _check_tool_availability(
        self, tools: List[str], runtime_level: RuntimeLevel
    ) -> PolicyCheckResult:
        """Check if tools are available in current runtime level"""

        tool_restrictions = {
            RuntimeLevel.FULL: [],  # No restrictions
            RuntimeLevel.REDUCED: ["file_access", "system_command"],
            RuntimeLevel.SAFE: ["file_access", "system_command", "code_generation"],
            RuntimeLevel.EMERGENCY: [
                "file_access",
                "system_command",
                "code_generation",
                "network_access",
            ],
        }

        restricted_tools = tool_restrictions.get(runtime_level, [])

        for tool in tools:
            if tool in restricted_tools:
                return PolicyCheckResult(
                    False,
                    f"Tool '{tool}' not available in {runtime_level} mode",
                    "high",
                )

        return PolicyCheckResult(True, "Tool availability check passed")

    def apply_runtime_constraints(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Apply runtime constraints to state"""

        current_level = self._get_runtime_level(state)

        # Add runtime metadata
        state["runtime_constraints"] = {
            "level": current_level.value,
            "applied_at": state.get("timestamp"),
            "effective_immediately": True,
        }

        # Apply level-specific constraints
        if current_level == RuntimeLevel.EMERGENCY:
            state["streaming_enabled"] = False
            state["max_response_length"] = 500
            state["enable_tool_execution"] = False

        elif current_level == RuntimeLevel.SAFE:
            state["streaming_enabled"] = False
            state["max_response_length"] = 2000
            state["enable_tool_execution"] = True
            state["allowed_tool_types"] = ["basic_search", "information_retrieval"]

        elif current_level == RuntimeLevel.REDUCED:
            state["streaming_enabled"] = True
            state["max_response_length"] = 5000
            state["enable_tool_execution"] = True
            state["allowed_tool_types"] = [
                "basic_search",
                "information_retrieval",
                "text_analysis",
            ]

        else:  # FULL
            state["streaming_enabled"] = True
            state["max_response_length"] = 100000
            state["enable_tool_execution"] = True
            state["allowed_tool_types"] = ["all"]

        return state


async def runtime_policy_enforcer_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """
    Runtime policy enforcement node for LangGraph orchestration

    Checks policies before routing, tool execution, and response synthesis
    """
    logger.info("Runtime policy enforcement processing")

    try:
        # Initialize policy enforcer
        policy_enforcer = RuntimePolicyEnforcer()

        # Apply runtime constraints
        state = policy_enforcer.apply_runtime_constraints(state)

        # Check routing policy if provider selection exists
        if "provider_selection" in state:
            routing_check = await policy_enforcer.check_routing_policy(
                state, state["provider_selection"]
            )
            if not routing_check.allowed:
                state.setdefault("errors", []).append(
                    f"Routing blocked: {routing_check.reason}"
                )
                state["routing_blocked"] = True

        # Check execution policy if execution plan exists
        if "execution_plan" in state:
            execution_check = await policy_enforcer.check_execution_policy(
                state, state["execution_plan"]
            )
            if not execution_check.allowed:
                state.setdefault("errors", []).append(
                    f"Execution blocked: {execution_check.reason}"
                )
                state["execution_blocked"] = True

        # Check response policy if response exists
        if "llm_response" in state:
            response_check = await policy_enforcer.check_response_policy(
                state, state["llm_response"]
            )
            if not response_check.allowed:
                state.setdefault("errors", []).append(
                    f"Response blocked: {response_check.reason}"
                )
                state["response_blocked"] = True

        logger.info("Runtime policy enforcement completed")

    except Exception as e:
        logger.error(f"Runtime policy enforcement error: {e}")
        state.setdefault("errors", []).append(f"Runtime policy error: {str(e)}")

    return state


def select_execution_branch(state: LangGraphOrchestrationState) -> str:
    """Select the execution branch for the LangGraph chat turn."""
    intent = str(state.get("detected_intent") or "").strip()
    request_config = state.get("request_config") or {}

    if isinstance(request_config, dict) and request_config.get("use_medusa"):
        return "medusa"

    if intent in (
        "routing.select",
        "routing.profile",
        "admin_panel",
        "extension.action",
        "agent_complex_reasoning",
    ):
        return "medusa"

    return "normal"


# Graph edge policy functions


def should_use_medusa(state: LangGraphOrchestrationState) -> str:
    """Determine if AgentMedusa should handle the request."""
    intent = state.get("detected_intent", "")
    # Extension and Routing intents go to Medusa
    if intent in (
        "routing.select",
        "routing.profile",
        "admin_panel",
        "extension.action",
        "agent_complex_reasoning",
    ):
        return "medusa"

    # Check if medusa is explicitly requested in config
    if state.get("request_config", {}).get("use_medusa"):
        return "medusa"

    return "normal"


def should_continue_after_auth(state: LangGraphOrchestrationState) -> str:
    """Determine if processing should continue after auth gate"""
    auth_status = state.get("auth_status")
    return "continue" if auth_status == "authenticated" else "reject"


def should_continue_after_safety(state: LangGraphOrchestrationState) -> str:
    """Determine if processing should continue after safety gate"""
    safety_status = state.get("safety_status")
    if safety_status == "safe":
        return "continue"
    elif safety_status == "review_required":
        return "review"
    else:
        return "reject"


def should_require_approval(state: LangGraphOrchestrationState) -> str:
    """Determine if human approval is required"""
    safety_flags = state.get("safety_flags", [])
    tool_results = state.get("tool_results", [])

    # Require approval if there are safety flags or sensitive tools were used
    if safety_flags or any("sensitive" in str(result) for result in tool_results):
        state["requires_approval"] = True
        return "review"
    else:
        return "approve"


def check_approval_status(state: LangGraphOrchestrationState) -> str:
    """Check the current approval status"""
    approval_status = state.get("approval_status", "pending")
    return approval_status
