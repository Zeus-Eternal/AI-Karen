from typing import Any, Dict, List, Optional
import logging
import asyncio

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
        
        # Initialize specialists
        self.specialists = {
            "analyst": AnalystSpecialist(),
            "researcher": ResearcherSpecialist()
        }
        
        # Initialize adapters
        self.extension_adapter = ExtensionRuntimeAdapter()
        self.memory_adapter = MemoryRuntimeAdapter()

    async def handle_request(self, request: RuntimeRequest) -> RuntimeResponse:
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
            # Extract final answer by synthesizing specialist results via LLM
            final_content = "I've processed your request but couldn't synthesize a natural response."
            
            try:
                from ai_karen_engine.services.models.routing.llm_router_service import get_llm_router, ChatRequest
                import json
                
                router = get_llm_router()
                
                # Gather all results
                all_results = {s.agent_specialist: s.output_data for s in plan.steps if s.status == StepStatus.COMPLETED}
                results_json = json.dumps(all_results, indent=2)
                
                synthesis_prompt = f"""
                You are Karen, an intelligent AI assistant.
                Synthesize a final, helpful, and natural response for the user based on the query and specialist agent findings.
                
                User Query: {request.query}
                
                Agent Findings:
                {results_json}
                
                Respond directly to the user.
                """
                
                response_gen = router.process_chat_request(ChatRequest(message=synthesis_prompt, stream=False))
                full_answer = ""
                async for chunk in response_gen:
                    full_answer += chunk
                
                if full_answer.strip():
                    final_content = full_answer.strip()
            except Exception as synth_err:
                logger.warning(f"Medusa final synthesis failed: {synth_err}")
                # Fallback to simple concatenation if LLM fails
                completed_steps = [s for s in plan.steps if s.status == StepStatus.COMPLETED]
                if completed_steps:
                    final_content = f"Execution complete. Found info: {completed_steps[-1].output_data.get('context_found', 'Results available.')}"

            return RuntimeResponse(
                request_id=request.request_id,
                status=ResponseStatus.SUCCESS,
                content=final_content,
                agent_trace=[step.agent_specialist for step in plan.steps]
            )
            
        except Exception as e:
            logger.error(f"Medusa Coordinator Error: {str(e)}", exc_info=True)
            return RuntimeResponse(
                request_id=request.request_id,
                status=ResponseStatus.ERROR,
                content=f"An error occurred during execution: {str(e)}"
            )

    async def _execute_step(self, step: PlanStep, plan: DeepExecutionPlan, request: RuntimeRequest):
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
