from typing import Any, Dict, Optional
import logging
from .specialist_base import SpecialistBase
from ..contracts.subagent_contract import SubagentContract, AgentCapability

logger = logging.getLogger(__name__)

class AnalystSpecialist(SpecialistBase):
    """The Analyst: specialized in parsing intent and structuring data"""
    
    def __init__(self):
        contract = SubagentContract(
            agent_id="analyst",
            role="Specialist in query analysis, intent detection, and structuring raw inputs",
            capabilities=[AgentCapability.REASONING]
        )
        super().__init__(contract)

    async def _process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes query intent and provides initial structure"""
        query = input_data.get("query", "")
        self.logger.info(f"Analyst processing query: {query}")
        
        from ai_karen_engine.services.models.routing.llm_router_service import get_llm_router, ChatRequest
        router = get_llm_router()
        
        analysis_prompt = f"""
        Analyze the following user query for Karen AI.
        Detect the primary intent (e.g., weather, information, task) and extract key terms.
        
        User Query: {query}
        
        Respond with a JSON object:
        {{
          "intent": "string",
          "key_terms": ["list", "of", "terms"],
          "requires_research": boolean
        }}
        """
        
        try:
            response_gen = router.process_chat_request(ChatRequest(message=analysis_prompt, stream=False))
            full_response = ""
            async for chunk in response_gen:
                full_response += chunk
            
            import json
            import re
            # Extract JSON from potential markdown markers
            json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {
                    "intent": result.get("intent", "information_request"),
                    "structured_query": {"raw": query, "key_terms": result.get("key_terms", [])},
                    "suggested_next_specialist": "researcher" if result.get("requires_research") else None
                }
        except Exception as e:
            self.logger.warning(f"LLM analysis failed, falling back: {e}")
        
        # Fallback to legacy logic
        intent = "information_request" if "?" in query else "task_request"
        return {
            "intent": intent,
            "structured_query": {"raw": query, "key_terms": []},
            "suggested_next_specialist": "researcher"
        }
