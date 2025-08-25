"""
spaCy-based analyzer with persona logic for the Response Core orchestrator.

This module implements the Analyzer protocol with intent detection, sentiment analysis,
entity extraction, and persona selection rules based on intent + mood mapping.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_karen_engine.core.response.protocols import Analyzer
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.models.persona_models import SYSTEM_PERSONAS


def create_spacy_analyzer(spacy_service: Optional[SpacyService] = None) -> 'SpacyAnalyzer':
    """
    Factory function to create a SpacyAnalyzer instance.
    
    Args:
        spacy_service: Optional SpacyService instance. If None, creates a new one.
        
    Returns:
        Configured SpacyAnalyzer instance
    """
    return SpacyAnalyzer(spacy_service=spacy_service)

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Supported intent types for persona mapping."""
    OPTIMIZE_CODE = "optimize_code"
    DEBUG_ERROR = "debug_error"
    GENERAL_ASSIST = "general_assist"
    TECHNICAL_QUESTION = "technical_question"
    CREATIVE_TASK = "creative_task"
    BUSINESS_ADVICE = "business_advice"
    CASUAL_CHAT = "casual_chat"
    DOCUMENTATION = "documentation"
    TROUBLESHOOT = "troubleshoot"
    EXPLAIN_CONCEPT = "explain_concept"


class SentimentType(str, Enum):
    """Sentiment types for persona mapping."""
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    EXCITED = "excited"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    URGENT = "urgent"
    CALM = "calm"


@dataclass
class PersonaMapping:
    """Mapping configuration for intent + mood → persona selection."""
    intent: IntentType
    sentiment: SentimentType
    persona_id: str
    confidence: float = 1.0


class SpacyAnalyzer:
    """
    spaCy-based analyzer implementing the Analyzer protocol.
    
    Provides intent detection, sentiment analysis, entity extraction,
    and persona selection rules based on intent + mood mapping.
    """
    
    def __init__(self, spacy_service: Optional[SpacyService] = None):
        """Initialize the analyzer with spaCy service."""
        self.spacy_service = spacy_service or SpacyService()
        
        # Intent detection patterns
        self._intent_patterns = self._build_intent_patterns()
        
        # Sentiment keywords
        self._sentiment_keywords = self._build_sentiment_keywords()
        
        # Persona mapping rules
        self._persona_mappings = self._build_persona_mappings()
        
        # Profile gap detection patterns
        self._gap_patterns = self._build_gap_patterns()
        
        logger.info("SpacyAnalyzer initialized with persona logic")
    
    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build regex patterns for intent detection."""
        return {
            IntentType.OPTIMIZE_CODE: [
                r'\b(optimize|improve|refactor|performance|faster|efficient)\b',
                r'\b(slow|inefficient|bottleneck)\b',
                r'\b(make.*better|speed.*up|clean.*up)\b'
            ],
            IntentType.DEBUG_ERROR: [
                r'\b(error|bug|exception|crash|fail|broken)\b',
                r'\b(debug|fix|solve)\b',
                r'\b(not working|doesn\'t work|won\'t run)\b',
                r'\b(stack trace|traceback|error message)\b'
            ],
            IntentType.TECHNICAL_QUESTION: [
                r'\b(how to|how do|what is)\b.*\b(api|library|framework|database|server)\b',
                r'\b(api|library|framework|database|server)\b',
                r'\b(implement|integrate|configure|setup)\b'
            ],
            IntentType.CREATIVE_TASK: [
                r'\b(create|design|build|generate|make)\b.*\b(app|website|ui|interface)\b',
                r'\b(brainstorm|ideas|creative|innovative)\b',
                r'\b(prototype|mockup|concept)\b'
            ],
            IntentType.BUSINESS_ADVICE: [
                r'\b(business|strategy|market|revenue|profit)\b',
                r'\b(startup|company|enterprise|organization)\b',
                r'\b(plan|roadmap|goals|objectives)\b'
            ],
            IntentType.DOCUMENTATION: [
                r'\b(document|write|readme|guide|tutorial)\b',
                r'\b(explain|describe|outline)\b.*\b(process|procedure|workflow)\b',
                r'\b(comments|documentation|specs)\b'
            ],
            IntentType.TROUBLESHOOT: [
                r'\b(problem|issue|trouble|difficulty)\b',
                r'\b(help|assist|support)\b.*\b(with|me)\b',
                r'\b(stuck|confused|lost)\b'
            ],
            IntentType.EXPLAIN_CONCEPT: [
                r'\b(what is|explain|understand|learn about)\b',
                r'\b(concept|theory|principle|idea)\b',
                r'\b(how does.*work|why does)\b'
            ],
            IntentType.CASUAL_CHAT: [
                r'\b(hi|hello|hey|chat|talk)\b',
                r'\b(how are you|what\'s up|good morning|good afternoon)\b',
                r'\b(thanks|thank you|appreciate)\b'
            ],
            IntentType.GENERAL_ASSIST: [
                r'\b(help|assist|support)\b',
                r'\b(can you|could you|please)\b',
                r'\b(need|want|would like)\b'
            ]
        }
    
    def _build_sentiment_keywords(self) -> Dict[SentimentType, List[str]]:
        """Build keyword lists for sentiment detection."""
        return {
            SentimentType.FRUSTRATED: [
                'frustrated', 'annoying', 'irritating', 'stupid', 'hate', 'terrible',
                'awful', 'worst', 'useless', 'broken', 'damn', 'shit', 'fuck'
            ],
            SentimentType.CONFUSED: [
                'confused', 'lost', 'stuck', 'don\'t understand', 'unclear',
                'puzzled', 'bewildered', 'perplexed', 'baffled'
            ],
            SentimentType.EXCITED: [
                'excited', 'awesome', 'amazing', 'fantastic', 'great', 'love',
                'perfect', 'excellent', 'wonderful', 'brilliant'
            ],
            SentimentType.URGENT: [
                'urgent', 'asap', 'immediately', 'quickly', 'fast', 'emergency',
                'critical', 'important', 'deadline', 'rush'
            ],
            SentimentType.POSITIVE: [
                'good', 'nice', 'helpful', 'useful', 'working', 'success',
                'thank', 'appreciate', 'pleased', 'satisfied'
            ],
            SentimentType.NEGATIVE: [
                'bad', 'wrong', 'failed', 'error', 'problem', 'issue',
                'difficult', 'hard', 'challenging', 'disappointing'
            ]
        }
    
    def _build_persona_mappings(self) -> List[PersonaMapping]:
        """Build persona mapping rules based on intent + sentiment combinations."""
        return [
            # Frustrated + any technical issue → calm_fixit (support-assistant)
            PersonaMapping(IntentType.DEBUG_ERROR, SentimentType.FRUSTRATED, "support-assistant", 0.9),
            PersonaMapping(IntentType.TROUBLESHOOT, SentimentType.FRUSTRATED, "support-assistant", 0.9),
            PersonaMapping(IntentType.TECHNICAL_QUESTION, SentimentType.FRUSTRATED, "support-assistant", 0.8),
            
            # Code optimization → ruthless_optimizer (technical-expert)
            PersonaMapping(IntentType.OPTIMIZE_CODE, SentimentType.NEUTRAL, "technical-expert", 0.9),
            PersonaMapping(IntentType.OPTIMIZE_CODE, SentimentType.EXCITED, "technical-expert", 0.8),
            
            # Technical questions → technical expert
            PersonaMapping(IntentType.TECHNICAL_QUESTION, SentimentType.NEUTRAL, "technical-expert", 0.8),
            PersonaMapping(IntentType.EXPLAIN_CONCEPT, SentimentType.NEUTRAL, "technical-expert", 0.7),
            
            # Creative tasks → creative collaborator
            PersonaMapping(IntentType.CREATIVE_TASK, SentimentType.EXCITED, "creative-collaborator", 0.9),
            PersonaMapping(IntentType.CREATIVE_TASK, SentimentType.NEUTRAL, "creative-collaborator", 0.8),
            
            # Business advice → business advisor
            PersonaMapping(IntentType.BUSINESS_ADVICE, SentimentType.NEUTRAL, "business-advisor", 0.9),
            
            # Documentation → technical writer (use technical-expert with documentation focus)
            PersonaMapping(IntentType.DOCUMENTATION, SentimentType.NEUTRAL, "technical-expert", 0.7),
            
            # Casual chat → casual friend
            PersonaMapping(IntentType.CASUAL_CHAT, SentimentType.POSITIVE, "casual-friend", 0.9),
            PersonaMapping(IntentType.CASUAL_CHAT, SentimentType.NEUTRAL, "casual-friend", 0.8),
            
            # Confused users → support assistant
            PersonaMapping(IntentType.GENERAL_ASSIST, SentimentType.CONFUSED, "support-assistant", 0.8),
            PersonaMapping(IntentType.TECHNICAL_QUESTION, SentimentType.CONFUSED, "support-assistant", 0.8),
            
            # Default fallbacks
            PersonaMapping(IntentType.GENERAL_ASSIST, SentimentType.NEUTRAL, "support-assistant", 0.6),
        ]
    
    def _build_gap_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for detecting profile gaps in onboarding flows."""
        return {
            "project_context": [
                r'\b(project|app|application|system|codebase)\b',
                r'\b(working on|building|developing|creating)\b'
            ],
            "tech_stack": [
                r'\b(using|with|in)\b.*\b(python|javascript|java|react|node|django)\b',
                r'\b(framework|library|language|technology)\b'
            ],
            "experience_level": [
                r'\b(beginner|new to|learning|junior|senior|expert)\b',
                r'\b(years of experience|experience with)\b'
            ],
            "goals": [
                r'\b(want to|trying to|goal|objective|aim)\b',
                r'\b(learn|build|create|improve|optimize)\b'
            ]
        }
    

    
    def select_persona(self, intent: str, sentiment: str, **kwargs) -> str:
        """
        Select appropriate persona based on intent + sentiment mapping.
        
        Args:
            intent: Detected user intent
            sentiment: Detected sentiment
            **kwargs: Additional context for persona selection
            
        Returns:
            Persona ID string
        """
        try:
            intent_enum = IntentType(intent)
            sentiment_enum = SentimentType(sentiment)
        except ValueError:
            # Fallback to default persona if invalid intent/sentiment
            logger.warning(f"Invalid intent ({intent}) or sentiment ({sentiment}), using default persona")
            return "support-assistant"
        
        # Find matching persona mappings
        matching_mappings = [
            mapping for mapping in self._persona_mappings
            if mapping.intent == intent_enum and mapping.sentiment == sentiment_enum
        ]
        
        if matching_mappings:
            # Return the highest confidence mapping
            best_mapping = max(matching_mappings, key=lambda x: x.confidence)
            logger.debug(f"Persona selected: {best_mapping.persona_id} "
                        f"(intent: {intent}, sentiment: {sentiment}, confidence: {best_mapping.confidence})")
            return best_mapping.persona_id
        
        # Fallback: look for intent-only matches
        intent_mappings = [
            mapping for mapping in self._persona_mappings
            if mapping.intent == intent_enum
        ]
        
        if intent_mappings:
            best_mapping = max(intent_mappings, key=lambda x: x.confidence)
            logger.debug(f"Persona selected by intent only: {best_mapping.persona_id} "
                        f"(intent: {intent}, confidence: {best_mapping.confidence})")
            return best_mapping.persona_id
        
        # Final fallback: default persona
        logger.debug(f"No persona mapping found for intent: {intent}, sentiment: {sentiment}, using default")
        return "support-assistant"
    
    async def detect_profile_gaps(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect profile gaps for onboarding flows.
        
        Args:
            text: User input text
            ui_caps: UI capabilities and context
            
        Returns:
            Dictionary containing detected gaps and onboarding suggestions
        """
        gaps = {}
        suggestions = []
        
        text_lower = text.lower()
        
        # Check for missing project context
        if not ui_caps.get("project_name") and not any(
            re.search(pattern, text_lower) for pattern in self._gap_patterns["project_context"]
        ):
            gaps["project_context"] = {
                "missing": True,
                "priority": "high",
                "question": "What project are you working on? This helps me provide more relevant assistance."
            }
        
        # Check for missing tech stack information
        if not ui_caps.get("tech_stack") and not any(
            re.search(pattern, text_lower) for pattern in self._gap_patterns["tech_stack"]
        ):
            gaps["tech_stack"] = {
                "missing": True,
                "priority": "medium",
                "question": "What programming languages or frameworks are you using?"
            }
        
        # Check for missing experience level
        if not ui_caps.get("experience_level") and not any(
            re.search(pattern, text_lower) for pattern in self._gap_patterns["experience_level"]
        ):
            gaps["experience_level"] = {
                "missing": True,
                "priority": "low",
                "question": "What's your experience level with this technology?"
            }
        
        # Check for missing goals
        if not ui_caps.get("user_goals") and not any(
            re.search(pattern, text_lower) for pattern in self._gap_patterns["goals"]
        ):
            gaps["goals"] = {
                "missing": True,
                "priority": "medium",
                "question": "What are you trying to accomplish with this project?"
            }
        
        # Generate onboarding suggestions based on gaps
        high_priority_gaps = [gap for gap in gaps.values() if gap.get("priority") == "high"]
        if high_priority_gaps:
            # Ask about the most important gap
            gap = high_priority_gaps[0]
            suggestions.append({
                "type": "onboarding_question",
                "content": gap["question"],
                "priority": "high"
            })
        
        # Suggest CopilotKit features if available
        if ui_caps.get("copilotkit_available") and not ui_caps.get("copilotkit_enabled"):
            suggestions.append({
                "type": "feature_suggestion",
                "content": "I can provide enhanced code analysis and suggestions with CopilotKit. Would you like to enable it?",
                "priority": "low"
            })
        
        return {
            "gaps": gaps,
            "suggestions": suggestions,
            "onboarding_needed": len(gaps) > 0,
            "next_question": suggestions[0]["content"] if suggestions else None
        }
    
    # Protocol implementation methods (synchronous wrappers)
    def detect_intent(self, text: str) -> str:
        """Synchronous wrapper for async detect_intent method."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._detect_intent_async(text))
                    return future.result()
            else:
                return loop.run_until_complete(self._detect_intent_async(text))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self._detect_intent_async(text))
    
    async def _detect_intent_async(self, text: str) -> str:
        """Async implementation of detect_intent."""
        if not text or not text.strip():
            return IntentType.GENERAL_ASSIST.value

        text_lower = text.lower()

        # Score each intent based on pattern matches
        intent_scores = {}

        for intent, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches

            if score > 0:
                intent_scores[intent] = score

        # If we have pattern matches, return the highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Intent detected: {best_intent.value} (score: {intent_scores[best_intent]})")
            return best_intent.value

        # Fallback: use spaCy analysis for more sophisticated detection
        try:
            parsed = await self.spacy_service.parse_message(text)

            # Look for technical entities
            tech_entities = [ent for ent, label in parsed.entities 
                           if label in ['ORG', 'PRODUCT', 'LANGUAGE']]

            # Look for action verbs in dependencies
            action_verbs = []
            for dep in parsed.dependencies:
                if dep.get('pos') == 'VERB' and dep.get('dep') in ['ROOT', 'ccomp']:
                    action_verbs.append(dep.get('lemma', '').lower())

            # Heuristic classification based on spaCy analysis
            if any(verb in ['optimize', 'improve', 'refactor', 'speed'] for verb in action_verbs):
                return IntentType.OPTIMIZE_CODE.value
            elif any(verb in ['debug', 'fix', 'solve', 'troubleshoot'] for verb in action_verbs):
                return IntentType.DEBUG_ERROR.value
            elif any(verb in ['explain', 'understand', 'learn'] for verb in action_verbs):
                return IntentType.EXPLAIN_CONCEPT.value
            elif any(verb in ['create', 'build', 'design', 'make'] for verb in action_verbs):
                return IntentType.CREATIVE_TASK.value
            elif tech_entities:
                return IntentType.TECHNICAL_QUESTION.value

        except Exception as e:
            logger.debug(f"spaCy intent analysis failed: {e}")

        # Default fallback
        logger.debug("No specific intent detected, using general_assist")
        return IntentType.GENERAL_ASSIST.value
    
    def sentiment(self, text: str) -> str:
        """Synchronous wrapper for async sentiment method."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._sentiment_async(text))
                    return future.result()
            else:
                return loop.run_until_complete(self._sentiment_async(text))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self._sentiment_async(text))
    
    async def _sentiment_async(self, text: str) -> str:
        """Async implementation of sentiment."""
        if not text or not text.strip():
            return SentimentType.NEUTRAL.value

        text_lower = text.lower()

        # Score each sentiment based on keyword matches
        sentiment_scores = {}

        for sentiment, keywords in self._sentiment_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1

            if score > 0:
                sentiment_scores[sentiment] = score

        # If we have keyword matches, return the highest scoring sentiment
        if sentiment_scores:
            best_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Sentiment detected: {best_sentiment.value} (score: {sentiment_scores[best_sentiment]})")
            return best_sentiment.value

        # Fallback: use spaCy for more sophisticated sentiment analysis
        try:
            parsed = await self.spacy_service.parse_message(text)

            # Look for emotional indicators in POS tags and dependencies
            emotional_indicators = []
            for dep in parsed.dependencies:
                pos = dep.get('pos', '')
                lemma = dep.get('lemma', '').lower()

                # Look for adjectives and adverbs that indicate emotion
                if pos in ['ADJ', 'ADV'] and lemma in [
                    'good', 'bad', 'great', 'terrible', 'awesome', 'awful',
                    'excellent', 'horrible', 'amazing', 'disappointing'
                ]:
                    emotional_indicators.append(lemma)

            # Simple heuristic classification
            positive_words = ['good', 'great', 'awesome', 'excellent', 'amazing']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']

            positive_count = sum(1 for word in emotional_indicators if word in positive_words)
            negative_count = sum(1 for word in emotional_indicators if word in negative_words)

            if positive_count > negative_count:
                return SentimentType.POSITIVE.value
            elif negative_count > positive_count:
                return SentimentType.NEGATIVE.value

        except Exception as e:
            logger.debug(f"spaCy sentiment analysis failed: {e}")

        # Default fallback
        logger.debug("No specific sentiment detected, using neutral")
        return SentimentType.NEUTRAL.value
    
    def entities(self, text: str) -> Dict[str, Any]:
        """Synchronous wrapper for async entities method."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._entities_async(text))
                    return future.result()
            else:
                return loop.run_until_complete(self._entities_async(text))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self._entities_async(text))
    
    async def _entities_async(self, text: str) -> Dict[str, Any]:
        """Async implementation of entities."""
        if not text or not text.strip():
            return {"entities": [], "metadata": {"used_fallback": True}}

        try:
            parsed = await self.spacy_service.parse_message(text)

            # Extract entities with additional metadata
            entities = []
            for entity_text, entity_label in parsed.entities:
                entities.append({
                    "text": entity_text,
                    "label": entity_label,
                    "start": None,  # spaCy service doesn't provide positions
                    "end": None,
                    "confidence": 1.0  # spaCy entities are generally high confidence
                })

            # Extract additional linguistic features
            metadata = {
                "entity_count": len(entities),
                "token_count": len(parsed.tokens),
                "sentence_count": len(parsed.sentences),
                "noun_phrases": parsed.noun_phrases,
                "used_fallback": parsed.used_fallback,
                "processing_time": parsed.processing_time,
                "language": parsed.language
            }

            return {
                "entities": entities,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {
                "entities": [],
                "metadata": {
                    "error": str(e),
                    "used_fallback": True
                }
            }