"""
Adapter implementations for integrating existing components with Response Core protocols.

These adapters wrap existing Karen AI components to implement the Response Core
protocols, enabling seamless integration with the ResponseOrchestrator.
"""

import logging
from typing import Any, Dict, List, Optional

from .protocols import Analyzer, Memory, LLMClient
from ai_karen_engine.core.memory.manager import recall_context, update_memory

logger = logging.getLogger(__name__)


class SpacyAnalyzerAdapter(Analyzer):
    """Adapter for spaCy-based analysis components."""
    
    def __init__(self):
        """Initialize the spaCy analyzer adapter."""
        self.nlp_service = None
        self._init_nlp_service()
    
    def _init_nlp_service(self) -> None:
        """Initialize NLP service if available."""
        try:
            from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
            self.nlp_service = nlp_service_manager
        except ImportError:
            logger.warning("NLP service not available, using fallback analysis")
    
    def detect_intent(self, text: str) -> str:
        """Detect user intent from text using spaCy."""
        if self.nlp_service:
            try:
                # Use existing NLP service for intent detection
                parsed = self.nlp_service.parse_message(text)
                if hasattr(parsed, 'intent') and parsed.intent:
                    return parsed.intent
                
                # Fallback to keyword-based intent detection
                return self._keyword_intent_detection(text)
                
            except Exception as e:
                logger.warning(f"spaCy intent detection failed: {e}")
        
        return self._keyword_intent_detection(text)
    
    def sentiment(self, text: str) -> str:
        """Analyze sentiment using spaCy."""
        if self.nlp_service:
            try:
                parsed = self.nlp_service.parse_message(text)
                if hasattr(parsed, 'sentiment') and parsed.sentiment:
                    return parsed.sentiment
                
                # Fallback to keyword-based sentiment
                return self._keyword_sentiment_analysis(text)
                
            except Exception as e:
                logger.warning(f"spaCy sentiment analysis failed: {e}")
        
        return self._keyword_sentiment_analysis(text)
    
    def entities(self, text: str) -> Dict[str, Any]:
        """Extract entities using spaCy."""
        if self.nlp_service:
            try:
                parsed = self.nlp_service.parse_message(text)
                if hasattr(parsed, 'entities') and parsed.entities:
                    return parsed.entities
                
                # Fallback to basic entity extraction
                return self._basic_entity_extraction(text)
                
            except Exception as e:
                logger.warning(f"spaCy entity extraction failed: {e}")
        
        return self._basic_entity_extraction(text)
    
    def _keyword_intent_detection(self, text: str) -> str:
        """Fallback keyword-based intent detection."""
        text_lower = text.lower()
        
        # Code optimization keywords
        if any(word in text_lower for word in ['optimize', 'performance', 'faster', 'efficient', 'slow']):
            return "optimize_code"
        
        # Debug/error keywords
        if any(word in text_lower for word in ['error', 'bug', 'debug', 'fix', 'broken', 'issue']):
            return "debug_error"
        
        # Documentation keywords
        if any(word in text_lower for word in ['document', 'docs', 'readme', 'explain', 'how to']):
            return "documentation"
        
        # Help/general keywords
        if any(word in text_lower for word in ['help', 'how', 'what', 'why', 'can you']):
            return "general_assist"
        
        return "general_assist"
    
    def _keyword_sentiment_analysis(self, text: str) -> str:
        """Fallback keyword-based sentiment analysis."""
        text_lower = text.lower()
        
        # Frustrated keywords
        if any(word in text_lower for word in ['frustrating', 'frustrated', 'annoying', 'stupid', 'hate', 'terrible', 'awful']):
            return "frustrated"
        
        # Positive keywords
        if any(word in text_lower for word in ['great', 'awesome', 'love', 'perfect', 'excellent', 'amazing']):
            return "positive"
        
        # Negative keywords
        if any(word in text_lower for word in ['bad', 'wrong', 'problem', 'issue', 'difficult', 'hard']):
            return "negative"
        
        return "neutral"
    
    def _basic_entity_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback basic entity extraction."""
        entities = {}
        
        # Extract file extensions
        import re
        file_extensions = re.findall(r'\.\w+', text)
        if file_extensions:
            entities['file_types'] = list(set(file_extensions))
        
        # Extract programming languages (basic)
        languages = []
        lang_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'cpp': ['c++', 'cpp', 'cmake'],
            'rust': ['rust', 'cargo'],
            'go': ['golang', 'go'],
        }
        
        text_lower = text.lower()
        for lang, keywords in lang_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                languages.append(lang)
        
        if languages:
            entities['programming_languages'] = languages
        
        return entities


class MemoryManagerAdapter(Memory):
    """Adapter for the existing memory manager."""
    
    def __init__(self, user_id: str = "default", tenant_id: Optional[str] = None):
        """Initialize memory adapter.
        
        Args:
            user_id: User identifier for memory operations
            tenant_id: Optional tenant identifier
        """
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.user_ctx = {
            "user_id": user_id,
            "tenant_id": tenant_id,
        }
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Recall relevant context using existing memory manager."""
        try:
            results = recall_context(self.user_ctx, query, limit=k, tenant_id=self.tenant_id)
            if results:
                # Convert to standard format
                formatted_results = []
                for result in results:
                    if isinstance(result, dict):
                        formatted_results.append({
                            "text": result.get("result", result.get("query", str(result))),
                            "relevance_score": result.get("score", 1.0),
                            "timestamp": result.get("timestamp"),
                            "source": "memory",
                            "metadata": result
                        })
                return formatted_results
            return []
        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")
            return []
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        """Save conversation turn using existing memory manager."""
        try:
            # Create a structured result for storage
            result = {
                "user_message": user_msg,
                "assistant_message": assistant_msg,
                "metadata": meta
            }
            
            update_memory(
                self.user_ctx, 
                user_msg, 
                result, 
                tenant_id=self.tenant_id
            )
        except Exception as e:
            logger.warning(f"Memory save failed: {e}")


class LLMOrchestratorAdapter(LLMClient):
    """Adapter for the existing LLM orchestrator."""
    
    def __init__(self):
        """Initialize LLM orchestrator adapter."""
        self.orchestrator = None
        self._init_orchestrator()
    
    def _init_orchestrator(self) -> None:
        """Initialize LLM orchestrator if available."""
        try:
            from ai_karen_engine.llm_orchestrator import LLMOrchestrator
            self.orchestrator = LLMOrchestrator()
        except ImportError:
            logger.warning("LLM orchestrator not available")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using existing LLM orchestrator."""
        if not self.orchestrator:
            return self._fallback_response(messages)
        
        try:
            # Convert messages to prompt format expected by orchestrator
            prompt = self._messages_to_prompt(messages)
            
            # Use orchestrator's routing logic
            response = self.orchestrator.route(prompt, **kwargs)
            return response
            
        except Exception as e:
            logger.warning(f"LLM orchestrator generation failed: {e}")
            return self._fallback_response(messages)
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages format to prompt string."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate fallback response when orchestrator is unavailable."""
        user_message = ""
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        
        return (
            f"I understand you're asking about: {user_message[:100]}... "
            "I'm currently operating in limited mode. Please try again or "
            "contact support if you continue to experience issues."
        )


# Factory functions for easy instantiation
def create_spacy_analyzer() -> 'SpacyAnalyzer':
    """Create a spaCy analyzer with persona logic."""
    from .analyzer import create_spacy_analyzer as _create_analyzer
    return _create_analyzer()


def create_memory_adapter(user_id: str = "default", tenant_id: Optional[str] = None) -> MemoryManagerAdapter:
    """Create a memory manager adapter."""
    return MemoryManagerAdapter(user_id, tenant_id)


def create_llm_adapter() -> LLMOrchestratorAdapter:
    """Create an LLM orchestrator adapter."""
    return LLMOrchestratorAdapter()