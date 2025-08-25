"""Response orchestration for the chat pipeline."""

from __future__ import annotations

from typing import Any, Dict, List

from .config import PipelineConfig
from .formatter import DRYFormatter
from .prompt_builder import PromptBuilder
from .protocols import Analyzer, LLMClient, Memory


class ResponseOrchestrator:
    """Coordinates analysis, memory, and model generation."""

    def __init__(
        self,
        config: PipelineConfig,
        analyzer: Analyzer,
        memory: Memory,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
        formatter: DRYFormatter | None = None,
    ) -> None:
        self.config = config
        self.analyzer = analyzer
        self.memory = memory
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder(config.template_dir)
        self.formatter = formatter or DRYFormatter()

    def build_prompt(
        self, user_input: str, context: List[str], analysis: Dict[str, Any]
    ) -> str:
        """Create a prompt from context, input, and analysis."""

        persona = analysis.get("persona", "assistant")
        gaps = analysis.get("profile_gaps")
        return self.prompt_builder.build(
            persona=persona,
            user_input=user_input,
            context=context,
            profile_gaps=gaps,
            system_prompts=self.config.system_prompts,
            max_history=self.config.max_history,
        )

    def respond(self, conversation_id: str, user_input: str, **llm_kwargs: Any) -> str:
        """Generate a model response for *user_input* in *conversation_id*."""

        analysis = self.analyzer.analyze(user_input)
        context = self.memory.fetch_context(conversation_id)
        prompt = self.build_prompt(user_input, context, analysis)
        llm_kwargs.setdefault("model", self.config.model)
        if self.config.fallback_model is not None:
            llm_kwargs.setdefault("fallback_model", self.config.fallback_model)
        response = self.llm_client.generate(prompt, **llm_kwargs)
        formatted = self.formatter.format("Response", response)
        self.memory.store(conversation_id, user_input, formatted)
        return formatted
