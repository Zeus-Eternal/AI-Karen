from typing import Any, Dict, List, Optional
import logging
from ..contracts.subagent_contract import SubagentContract, AgentCapability
from ..contracts.execution_action import ExecutionAction, ActionType

logger = logging.getLogger(__name__)

class SpecialistBase:
    """Base class for all Specialist Agents in the Medusa Runtime"""
    
    def __init__(self, contract: SubagentContract):
        self.contract = contract
        self.logger = logging.getLogger(f"{__name__}.{contract.agent_id}")

    async def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution logic for the specialist"""
        self.logger.info(f"Specialist {self.contract.agent_id} starting execution")
        try:
            # 1. Action Generation (via LLM in real world)
            # 2. Execution (via Adapters)
            # 3. Result Synthesis
            return await self._process(input_data, context)
        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}", exc_info=True)
            raise

    async def _process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Override this in subclasses to implement specific logic"""
        raise NotImplementedError
