from typing import Any, Dict, Optional
import logging
from .specialist_base import SpecialistBase
from ..contracts.subagent_contract import SubagentContract, AgentCapability

logger = logging.getLogger(__name__)

class ResearcherSpecialist(SpecialistBase):
    """The Researcher: specialized in gathering context and executing tool-based searches"""

    def __init__(self):
        contract = SubagentContract(
            agent_id="researcher",
            role="Specialist in gathering external/internal context and using search tools",
            capabilities=[AgentCapability.WEB_SEARCH, AgentCapability.MEMORY_RETRIEVAL]
        )
        super().__init__(contract)

    async def _process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather context via tools or memory"""
        self.logger.info(f"Researcher gathering context")

        from ai_karen_engine.services.tooling.tool_service import get_tool_service, ToolInput
        from ai_karen_engine.services.models.routing.llm_router_service import get_llm_router, ChatRequest

        tools = get_tool_service()
        router = get_llm_router()

        query = input_data.get("raw", "")

        tool_results = []

        # If we have a query, attempt a web search; weather requests are handled by search.
        if query:
            tool_name = "web_search"

            try:
                self.logger.info(f"Researcher executing tool: {tool_name}")
                tool_output = await tools.execute_tool(ToolInput(
                    tool_name=tool_name,
                    parameters={"query": query},
                    user_id=context.get("user_id"),
                    session_id=context.get("session_id")
                ))
                if tool_output.success:
                    tool_results.append({
                        "tool": tool_name,
                        "result": tool_output.result
                    })
            except Exception as e:
                self.logger.warning(f"Researcher tool execution failed: {e}")

        # Synthesize findings
        if tool_results:
            import json
            findings_data = json.dumps(tool_results, indent=2)
            synthesis_prompt = f"""
            As a Researcher Agent, summarize the following tool findings for the query: "{query}"

            Findings:
            {findings_data}
            """
            try:
                response_gen = router.process_chat_request(ChatRequest(message=synthesis_prompt, stream=False))
                full_summary = ""
                async for chunk in response_gen:
                    full_summary += chunk

                return {
                    "search_results": tool_results,
                    "context_found": full_summary.strip(),
                    "confidence": 0.9
                }
            except Exception:
                pass

        # Final fallback
        return {
            "search_results": tool_results,
            "context_found": f"Found {len(tool_results)} results related to {query}" if tool_results else "No additional context found.",
            "confidence": 0.5
        }
