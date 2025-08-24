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
        """Create a simple prompt from context, input, and analysis."""

        persona = analysis.get("persona", "assistant")
        parts = [self.prompt_builder.render("system_base", persona=persona)]
        for msg in context[-self.config.max_history :]:
            parts.append(self.prompt_builder.render("user_frame", user_input=msg))
        parts.append(self.prompt_builder.render("user_frame", user_input=user_input))
        if analysis.get("profile_gaps"):
            parts.append(
                self.prompt_builder.render(
                    "onboarding", gaps=analysis["profile_gaps"]
                )
            )
        return "\n".join(self.config.system_prompts + parts)

    def respond(self, conversation_id: str, user_input: str, **llm_kwargs: Any) -> str:
        """Generate a model response for *user_input* in *conversation_id*."""

        analysis = self.analyzer.analyze(user_input)
        context = self.memory.fetch_context(conversation_id)
        prompt = self.build_prompt(user_input, context, analysis)
        response = self.llm_client.generate(prompt, **llm_kwargs)
        formatted = self.formatter.format(response)
        self.memory.store(conversation_id, user_input, formatted)
        return formatted
