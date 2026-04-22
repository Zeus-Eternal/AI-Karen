import logging
from typing import Dict, Any

from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


class ApprovalGateNode:
    """Human approval gate for sensitive operations"""

    def __init__(self):
        pass

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Process approval requirements"""
        logger.info("Approval gate processing")

        try:
            requires_approval = bool(state.get("requires_approval"))
            safety_status = state.get("safety_status")
            plan = state.get("execution_plan") or {}

            if safety_status == "review_required":
                requires_approval = True

            if plan.get("requires_human_review"):
                requires_approval = True

            state["requires_approval"] = requires_approval

            if requires_approval:
                state["approval_status"] = "pending"
                state["approval_reason"] = plan.get(
                    "review_reason",
                    "Flagged by safety or planning policies",
                )
            else:
                state["approval_status"] = "approved"
                state["approval_reason"] = "Policy auto-approval"

        except Exception as e:
            logger.error(f"Approval gate error: {e}")
            state.setdefault("errors", []).append(f"Approval gate error: {str(e)}")

        return state


async def approval_gate_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for ApprovalGateNode"""
    node = ApprovalGateNode()
    return await node(state)
