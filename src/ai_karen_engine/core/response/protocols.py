"""
Protocol interfaces for the Response Core orchestrator.

These protocols define the contracts that components must implement to work
with the ResponseOrchestrator, enabling dependency injection and modular
component architecture.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime


@runtime_checkable
class Analyzer(Protocol):
    """Protocol for text analysis components (spaCy, etc.)."""
    
    def detect_intent(self, text: str) -> str:
        """Detect user intent from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Intent string (e.g., "optimize_code", "general_assist", "debug_error")
        """
        ...
    
    def sentiment(self, text: str) -> str:
        """Analyze sentiment of text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Sentiment string (e.g., "positive", "negative", "neutral", "frustrated")
        """
        ...
    
    def entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing extracted entities and their metadata
        """
        ...


@runtime_checkable
class Memory(Protocol):
    """Protocol for memory/context recall components."""
    
    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Recall relevant context for a query.
        
        Args:
            query: Query text to find relevant context for
            k: Number of results to return
            
        Returns:
            List of context dictionaries with relevance scores and metadata
        """
        ...
    
    def save_turn(self, user_msg: str, assistant_msg: str, meta: Dict[str, Any]) -> None:
        """Save a conversation turn to memory.
        
        Args:
            user_msg: User's message
            assistant_msg: Assistant's response
            meta: Metadata about the interaction (persona, intent, etc.)
        """
        ...


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated response text
        """
        ...


# Additional protocol for enhanced LLM clients with streaming support
@runtime_checkable
class StreamingLLMClient(LLMClient, Protocol):
    """Protocol for LLM clients that support streaming responses."""
    
    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Generate streaming response from messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional generation parameters
            
        Returns:
            Async generator yielding response chunks
        """
        ...


# Protocol for model selection logic
@runtime_checkable
class ModelSelector(Protocol):
    """Protocol for model selection components."""
    
    def select_model(self, intent: str, context_size: int, **kwargs) -> str:
        """Select appropriate model for the request.
        
        Args:
            intent: Detected user intent
            context_size: Size of context in tokens
            **kwargs: Additional selection criteria
            
        Returns:
            Model identifier string
        """
        ...


# Protocol for prompt building
@runtime_checkable
class PromptBuilder(Protocol):
    """Protocol for prompt construction components."""
    
    def build_prompt(
        self, 
        user_text: str, 
        persona: str, 
        context: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, str]]:
        """Build structured prompt from components.
        
        Args:
            user_text: User's input text
            persona: Selected persona
            context: Retrieved context from memory
            **kwargs: Additional prompt variables
            
        Returns:
            List of message dictionaries for LLM
        """
        ...


# Protocol for response formatting
@runtime_checkable
class ResponseFormatter(Protocol):
    """Protocol for response formatting components."""
    
    def format_response(
        self, 
        raw_response: str, 
        intent: str, 
        persona: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Format raw LLM response into structured output.
        
        Args:
            raw_response: Raw response from LLM
            intent: User intent
            persona: Selected persona
            **kwargs: Additional formatting options
            
        Returns:
            Formatted response dictionary
        """
        ...