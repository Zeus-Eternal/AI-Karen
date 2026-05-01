from typing import Any, Dict
import logging
import asyncio

from ai_karen_engine.services.response import ResponseContract, ResponseSanitizer, ResponseSynthesizer
from ..contracts.runtime_request import RuntimeRequest
from ..contracts.runtime_response import RuntimeResponse, ResponseStatus
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
        self.specialists = {"analyst": AnalystSpecialist(), "researcher": ResearcherSpecialist()}
        self.extension_adapter = ExtensionRuntimeAdapter()
        self.memory_adapter = MemoryRuntimeAdapter()

    async def handle_request(self, request: RuntimeRequest) -> RuntimeResponse:
        logger.info(f"Medusa Coordinator -> Handling request {request.request_id}")
        try:
            plan = await self.planner.create_plan(request)
            self.active_plans[request.request_id] = plan
            while not plan.is_complete:
                runnable_steps = plan.get_next_runnable_steps()
                if not runnable_steps:
                    if all(s.status == StepStatus.COMPLETED for s in plan.steps):
                        plan.is_complete = True
                        break
                    raise RuntimeError("Medusa Execution Stalled: Deadlock or dependency failure")
                await asyncio.gather(*[self._execute_step(step, plan, request) for step in runnable_steps])

            final_content = "I've processed your request but couldn't synthesize a natural response."
            try:
                from ai_karen_engine.services.models.routing.llm_router_service import get_llm_router
                router = get_llm_router()
                all_results = {s.agent_specialist: s.output_data for s in plan.steps if s.status == StepStatus.COMPLETED}
                contract = ResponseContract(
                    purpose="medusa_synthesis",
                    latest_user_message=request.query,
                    specialist_findings=[
                        {"specialist": k, "summary": str(v), "confidence": 1.0, "metadata": {}}
                        for k, v in all_results.items()
                    ],
                )
                response_text, _metadata = await ResponseSynthesizer(router).synthesize(
                    contract,
                    user_preferences=request.user_preferences,
                    conversation_id=request.conversation_id,
                )
                final_content = ResponseSanitizer().sanitize(response_text)
            except Exception as synth_err:
                logger.warning(f"Medusa final synthesis failed: {synth_err}")
                completed_steps = [s for s in plan.steps if s.status == StepStatus.COMPLETED]
                if completed_steps:
                    final_content = f"Execution complete. Found info: {completed_steps[-1].output_data.get('context_found', 'Results available.')}"

            return RuntimeResponse(request_id=request.request_id, status=ResponseStatus.SUCCESS, content=final_content, agent_trace=[step.agent_specialist for step in plan.steps])
        except Exception as e:
            logger.error(f"Medusa Coordinator Error: {str(e)}", exc_info=True)
            return RuntimeResponse(request_id=request.request_id, status=ResponseStatus.ERROR, content=f"An error occurred during execution: {str(e)}")

    async def _execute_step(self, step: PlanStep, plan: DeepExecutionPlan, request: RuntimeRequest):
        logger.info(f"Medusa Coordinator -> Executing Step: {step.description} via {step.agent_specialist}")
        step.status = StepStatus.RUNNING
        specialist = self.specialists.get(step.agent_specialist)
        if not specialist:
            error_msg = f"Specialist {step.agent_specialist} not found"
            step.status = StepStatus.FAILED
            step.error = error_msg
            raise ValueError(error_msg)
        context = {
            "session_id": request.session_id,
            "request_id": request.request_id,
            "plan_metadata": plan.metadata,
            "previous_steps": {s.id: s.output_data for s in plan.steps if s.status == StepStatus.COMPLETED}
        }
        result = await specialist.run(step.input_data, context)
        step.status = StepStatus.COMPLETED
        step.output_data = result
