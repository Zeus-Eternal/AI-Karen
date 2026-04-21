from typing import (
    Dict,
    Any,
    List,
    Optional,
    cast,
)
import logging

from ai_karen_engine.core.cortex.routing_intents import resolve_routing_intent
from ai_karen_engine.core.response.analyzer import SpacyAnalyzer, AnalysisContext
from ai_karen_engine.core.reasoning.synthesis import (
    MetacognitiveMonitor,
)
from ai_karen_engine.memory.distilbert_service import DistilBertService

logger = logging.getLogger(__name__)

class DecisionEngine:
    """Adapter exposing the legacy intent-analysis surface via the reasoning stack."""

    def __init__(
        self,
        analyzer: Optional[SpacyAnalyzer] = None,
        classifier: Optional[DistilBertService] = None,
    ):
        self._analyzer = analyzer or SpacyAnalyzer()
        self._classifier = classifier or DistilBertService()
        self._metacognition = MetacognitiveMonitor()

    @staticmethod
    def _suggest_tools(intent: str) -> List[str]:
        mapping = {
            "greeting": [],
            "weather_query": ["weather"],
            "time_query": ["time"],
            "book_query": ["search_books"],
            "information_retrieval": ["search_memory"],
            "technical_question": ["search_docs"],
            "debug_error": ["search_logs"],
            "documentation": ["search_docs"],
            "troubleshoot": ["search_logs"],
            "system_config": ["search_docs"],
        }
        return mapping.get(intent, [])

    @staticmethod
    def _normalize_cortex_intent(cortex_intent: str, analyzer_intent: str) -> str:
        normalized = (cortex_intent or "").strip().lower()
        if normalized in {"", "unknown", "general", "general_assist"}:
            return analyzer_intent

        cortex_to_response = {
            "greeting": "casual_chat",
            "search": "information_retrieval",
            "memory": "information_retrieval",
            "diagnostics": "troubleshoot",
            "system_status": "system_config",
            "audit_log": "documentation",
            "logout": "casual_chat",
            "routing.select": "system_config",
            "routing.profile": "system_config",
            "admin_panel": "system_config",
        }
        return cortex_to_response.get(normalized, normalized)

    @staticmethod
    def _normalize_classifier_intent(
        classifier_intent: str, analyzer_intent: str
    ) -> str:
        normalized = (classifier_intent or "").strip().lower()
        if normalized in {"", "unknown"}:
            return analyzer_intent

        classifier_to_response = {
            "information_seeking": "information_retrieval",
            "task_completion": "how_to_guide",
            "problem_solving": "troubleshoot",
            "creative_assistance": "creative_task",
            "decision_making": "business_advice",
            "social_interaction": "casual_chat",
        }
        return classifier_to_response.get(normalized, analyzer_intent)

    async def analyze_intent(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = await self._analyzer.analyze_comprehensive(
            prompt,
            context=AnalysisContext(
                user_id=str((context or {}).get("user_id") or "") or None,
                session_id=str((context or {}).get("session_id") or "") or None,
                interaction_history=cast(
                    List[Dict[str, Any]],
                    (context or {}).get("conversation_history") or [],
                ),
                system_capabilities=cast(Dict[str, Any], context or {}),
            ),
        )
        context_dict = context or {}
        cortex_intent, cortex_meta = resolve_routing_intent(prompt, context_dict)
        analyzer_intent = result.intent.primary_intent.value
        cortex_confidence = 0.0
        if isinstance(cortex_meta, dict):
            raw_confidence = cortex_meta.get("confidence")
            if isinstance(raw_confidence, (int, float)):
                cortex_confidence = float(raw_confidence)

        classifier_intent = "unknown"
        classifier_confidence = 0.0
        classifier_entities: List[Dict[str, Any]] = []
        try:
            classifier_result = await self._classifier.detect_intent(prompt)
            classifier_intent = classifier_result.intent
            classifier_confidence = classifier_result.confidence
            classifier_entities = classifier_result.entities
        except Exception as exc:
            logger.debug("DistilBERT intent classification unavailable: %s", exc)

        if cortex_intent and cortex_intent.lower() not in {"unknown", ""}:
            primary_intent = self._normalize_cortex_intent(
                cortex_intent, analyzer_intent
            )
        else:
            primary_intent = self._normalize_classifier_intent(
                classifier_intent, analyzer_intent
            )

        reasoning_state = self._metacognition.monitor_reasoning_process(
            query=prompt,
            current_output=primary_intent,
            context=[
                str(context_dict.get("context_summary", "")),
            ]
            if context
            else None,
        )
        strategy = self._metacognition.select_strategy(
            query=prompt,
            task_type=primary_intent,
            current_state=reasoning_state,
        )
        raw_entities = (
            result.entities.get("entities", [])
            if isinstance(result.entities, dict)
            else []
        )

        normalized_entities: List[Dict[str, Any]] = []
        for entity in raw_entities:
            if isinstance(entity, dict):
                normalized_entities.append(entity)
            elif hasattr(entity, "text"):
                normalized_entities.append(
                    {
                        "type": getattr(entity, "label_", "unknown"),
                        "value": getattr(entity, "text", ""),
                    }
                )
        for entity in classifier_entities:
            if isinstance(entity, dict):
                normalized_entities.append(entity)

        return {
            "primary_intent": primary_intent,
            "intent": primary_intent,
            "confidence": max(
                result.intent.confidence,
                classifier_confidence,
                cortex_confidence,
                reasoning_state.confidence,
            ),
            "suggested_tools": self._suggest_tools(primary_intent),
            "entities": normalized_entities,
            "requires_clarification": result.intent.confidence < 0.45
            or bool(reasoning_state.knowledge_gaps),
            "sentiment": result.sentiment.primary_sentiment.value,
            "persona_recommendation": result.persona_recommendation,
            "metadata": {
                **result.metadata,
                "intent_source": "cortex+response_analyzer",
                "cortex_intent": cortex_intent,
                "cortex_meta": cortex_meta,
                "classifier_intent": classifier_intent,
                "classifier_confidence": classifier_confidence,
                "analyzer_intent": analyzer_intent,
                "analyzer_confidence": result.intent.confidence,
                "reasoning_trace": [
                    f"intent={primary_intent}",
                    f"cortex={cortex_intent}",
                    f"strategy={strategy.value}",
                    f"state={reasoning_state.cognitive_state.value}",
                ],
                "strategy_used": strategy.value,
                "quality_score": reasoning_state.performance_estimate,
                "knowledge_gaps": reasoning_state.knowledge_gaps,
                "metacognitive_state": reasoning_state.cognitive_state.value,
                "reasoning_confidence": reasoning_state.confidence,
                "reasoning_certainty": reasoning_state.certainty,
            },
            "context": context or {},
        }
