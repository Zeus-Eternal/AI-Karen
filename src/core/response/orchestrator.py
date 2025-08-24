"""Response orchestration for the chat pipeline."""

from __future__ import annotations

from typing import Any, Dict, List

from .config import PipelineConfig
from .protocols import Analyzer, LLMClient, Memory


class ResponseOrchestrator:
    """Coordinates analysis, memory, and model generation."""

    def __init__(
        self,
        config: PipelineConfig,
        analyzer: Analyzer,
        memory: Memory,
        llm_client: LLMClient,
    ) -> None:
        self.config = config
        self.analyzer = analyzer
        self.memory = memory
        self.llm_client = llm_client

    def build_prompt(
        self, user_input: str, context: List[str], analysis: Dict[str, Any]
    ) -> str:
        """Create a simple prompt from context, input, and analysis."""

        _ = analysis  # placeholder for future prompt logic
        segments = context[-self.config.max_history :] + [user_input]
        return "\n".join(self.config.system_prompts + segments)

    def respond(self, conversation_id: str, user_input: str, **llm_kwargs: Any) -> str:
        """Generate a model response for *user_input* in *conversation_id*."""

        analysis = self.analyzer.analyze(user_input)
        context = self.memory.fetch_context(conversation_id)
        prompt = self.build_prompt(user_input, context, analysis)
        response = self.llm_client.generate(prompt, **llm_kwargs)
        self.memory.store(conversation_id, user_input, response)
        return response
