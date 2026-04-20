from typing import Any, Dict, List, Optional
import logging
import asyncio

from ..contracts.runtime_request import MedusaRuntimeRequest
from ..contracts.runtime_response import MedusaRuntimeResponse, ResponseStatus
from ..contracts.deep_execution_plan import DeepExecutionPlan, PlanStep, StepStatus
from ..planning.medusa_planner import MedusaPlanner
from ..specialists.analyst_specialist import AnalystSpecialist
from ..specialists.researcher_specialist import ResearcherSpecialist
from ..adapters.extension_runtime_adapter import ExtensionRuntimeAdapter
from ..adapters.memory_runtime_adapter import MemoryRuntimeAdapter

logger = logging.getLogger(__name__)

class MedusaCoordinator:
    """The central orchestration authority for the AgentMedusa runtime layer"""
    
    def __init__(self, planner: MedusaPlanner = None):
        self.planner = planner or MedusaPlanner()
        self.active_plans: Dict[str, DeepExecutionPlan] = {}
        
        # Initialize specialists
        self.specialists = {
            "analyst": AnalystSpecialist(),
            "researcher": ResearcherSpecialist()
        }
        
        # Initialize adapters
        self.extension_adapter = ExtensionRuntimeAdapter()
        self.memory_adapter = MemoryRuntimeAdapter()

    async def handle_request(self, request: MedusaRuntimeRequest) -> MedusaRuntimeResponse:
        """Main entry point: Creates a plan, executes it via specialists, and returns a response"""
        logger.info(f"Medusa Coordinator -> Handling request {request.request_id}")
        
        try:
            # 1. Plan Phase
            plan = await self.planner.create_plan(request)
            self.active_plans[request.request_id] = plan
            
            # 2. Execution Loop
            while not plan.is_complete:
                runnable_steps = plan.get_next_runnable_steps()
                if not runnable_steps:
                    if all(s.status == StepStatus.COMPLETED for s in plan.steps):
                        plan.is_complete = True
                        break
                    else:
                        raise RuntimeError("Medusa Execution Stalled: Deadlock or dependency failure")
                
                # Execute steps (potentially in parallel if independent)
                await asyncio.gather(*[self._execute_step(step, plan, request) for step in runnable_steps])
                
            # 3. Finalization
            # Extract final answer from context (simplified)
            final_content = "Medusa execution complete. Final synthesis placeholder."
            
            return MedusaRuntimeResponse(
                request_id=request.request_id,
                status=ResponseStatus.SUCCESS,
                content=final_content,
                agent_trace=[step.agent_specialist for step in plan.steps]
            )
            
        except Exception as e:
            logger.error(f"Medusa Coordinator Error: {str(e)}", exc_info=True)
            return MedusaRuntimeResponse(
                request_id=request.request_id,
                status=ResponseStatus.ERROR,
                content=f"An error occurred during execution: {str(e)}"
            )

    async def _execute_step(self, step: PlanStep, plan: DeepExecutionPlan, request: MedusaRuntimeRequest):
        """Dispatches a step to a specialist agent and handles the result"""
        logger.info(f"Medusa Coordinator -> Executing Step: {step.description} via {step.agent_specialist}")
        step.status = StepStatus.RUNNING
        
        specialist = self.specialists.get(step.agent_specialist)
        if not specialist:
            error_msg = f"Specialist {step.agent_specialist} not found"
            step.status = StepStatus.FAILED
            step.error = error_msg
            raise ValueError(error_msg)
            
        # Prepare context for specialist
        context = {
            "session_id": request.session_id,
            "request_id": request.request_id,
            "plan_metadata": plan.metadata,
            "previous_steps": {s.id: s.output_data for s in plan.steps if s.status == StepStatus.COMPLETED}
        }
        
        # Execute specialist
        result = await specialist.run(step.input_data, context)
        
        step.status = StepStatus.COMPLETED
        step.output_data = result
