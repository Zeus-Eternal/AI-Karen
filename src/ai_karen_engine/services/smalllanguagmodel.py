"""
Production-ready SmallLanguageModel service for fast reasoning scaffolding and outline generation.

Implements requirements:
- Fast reasoning scaffolding and outline generation (Requirement 3.1)
- Conversation outlines and quick scaffolding interface (Requirement 3.2)
- Short generative fills and context summarization (Requirement 3.3)
- Integration with main orchestration agent for augmenting responses
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from cachetools import TTLCache
import threading
import importlib

try:
    from ai_karen_engine.services.nlp_config import SmallLanguageModelConfig
except ImportError:
    # Create a basic config if not available
    class SmallLanguageModelConfig:
        def __init__(self, **kwargs):
            self.model_name = kwargs.get("model_name", "tinyllama-1.1b-chat")
            self.max_tokens = kwargs.get("max_tokens", 150)
            self.temperature = kwargs.get("temperature", 0.7)
            self.enable_fallback = kwargs.get("enable_fallback", True)
            self.cache_size = kwargs.get("cache_size", 1000)
            self.cache_ttl = kwargs.get("cache_ttl", 1800)
            self.scaffold_max_tokens = kwargs.get("scaffold_max_tokens", 100)
            self.outline_max_tokens = kwargs.get("outline_max_tokens", 80)
            self.summary_max_tokens = kwargs.get("summary_max_tokens", 120)

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
llamacpp_inprocess_client = None
LLAMACPP_AVAILABLE = False

def _get_llamacpp_client():
    """Lazy loading of LlamaCpp client to avoid import-time errors."""
    global llamacpp_inprocess_client, LLAMACPP_AVAILABLE
    
    if LLAMACPP_AVAILABLE:
        return llamacpp_inprocess_client
    
    import_paths = [
        "plugins_hub.ai.llm_services.llama.llama_client",
        "plugins.ai.llm_services.llama.llama_client",
        "ai_karen_engine.plugins.llm_services.llama.llama_client",
    ]
    
    for module_path in import_paths:
        try:
            module = importlib.import_module(module_path)
            llamacpp_inprocess_client = module.llamacpp_inprocess_client
            LLAMACPP_AVAILABLE = True
            return llamacpp_inprocess_client
        except (ImportError, FileNotFoundError, Exception) as e:
            logger.debug(f"Failed to import LlamaCpp client from {module_path}: {e}")
    
    return None


@dataclass
class ScaffoldResult:
    """Result of scaffolding generation."""
    
    content: str
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0
    output_tokens: int = 0


@dataclass
class OutlineResult:
    """Result of outline generation."""
    
    outline: List[str]
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0


@dataclass
class SummaryResult:
    """Result of context summarization."""
    
    summary: str
    processing_time: float
    used_fallback: bool
    model_name: Optional[str] = None
    input_length: int = 0
    compression_ratio: float = 0.0


@dataclass
class LiteHealthStatus:
    """Health status for Lite service."""
    
    is_healthy: bool
    model_loaded: bool
    fallback_mode: bool
    cache_size: int
    cache_hit_rate: float
    avg_processing_time: float
    error_count: int
    last_error: Optional[str] = None


class SmallLanguageModelService:
    """Production-ready Small Language Model service for fast reasoning and scaffolding."""
    
    def __init__(self, config: Optional[SmallLanguageModelConfig] = None):
        self.config = config or SmallLanguageModelConfig()
        self.client = None
        self.fallback_mode = False
        self.cache = TTLCache(maxsize=self.config.cache_size, ttl=self.config.cache_ttl)
        self.lock = threading.RLock()
        
        # Monitoring metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._processing_times = []
        self._error_count = 0
        self._last_error = None
        
        # Initialize service
        self._initialize()
    
    def _initialize(self):
        """Initialize Lite service with model loading and fallback setup."""
        try:
            client = _get_llamacpp_client()
            if client is not None:
                self.client = client
                
                # Verify client is working
                health = self.client.health_check()
                if health.get("status") != "healthy":
                    logger.warning(f"LlamaCpp client unhealthy: {health}")
                    if self.config.enable_fallback:
                        self.fallback_mode = True
                    else:
                        raise RuntimeError("LlamaCpp client unhealthy and fallback disabled")
                else:
                    logger.info(f"Lite service initialized with model: {self.config.model_name}")
            else:
                logger.warning("LlamaCpp client not available, using fallback mode")
                if self.config.enable_fallback:
                    self.fallback_mode = True
                else:
                    raise RuntimeError("LlamaCpp client not available and fallback disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize Lite service: {e}")
            self._last_error = str(e)
            self._error_count += 1
            if self.config.enable_fallback:
                self.fallback_mode = True
                logger.info("Enabled fallback mode due to initialization failure")
            else:
                raise
    
    async def generate_scaffold(
        self, 
        text: str, 
        scaffold_type: str = "reasoning",
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ScaffoldResult:
        """
        Generate fast reasoning scaffolding for the given text.
        
        Args:
            text: Input text to scaffold
            scaffold_type: Type of scaffold ("reasoning", "outline", "structure", "conversation", "analysis")
            max_tokens: Maximum tokens to generate
            context: Additional context for scaffolding (conversation history, user preferences, etc.)
            
        Returns:
            ScaffoldResult with generated scaffolding content
        """
        if not text or not text.strip():
            return ScaffoldResult(
                content="",
                processing_time=0.0,
                used_fallback=True,
                input_length=0,
                output_tokens=0
            )
        
        # Check cache first
        cache_key = self._get_cache_key(f"scaffold:{scaffold_type}:{text}")
        with self.lock:
            if cache_key in self.cache:
                self._cache_hits += 1
                return self.cache[cache_key]
            self._cache_misses += 1
        
        start_time = time.time()
        max_tokens = max_tokens or self.config.scaffold_max_tokens
        
        try:
            if self.fallback_mode or not self.client:
                content = await self._fallback_scaffold(text, scaffold_type, context)
                used_fallback = True
                output_tokens = len(content.split())
            else:
                content = await self._generate_scaffold_llm(text, scaffold_type, max_tokens, context)
                used_fallback = False
                output_tokens = len(content.split())
            
            processing_time = time.time() - start_time
            
            result = ScaffoldResult(
                content=content,
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text),
                output_tokens=output_tokens
            )
            
            # Cache result
            with self.lock:
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 1000:
                    self._processing_times = self._processing_times[-1000:]
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Scaffold generation failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                logger.info("Falling back to rule-based scaffolding due to error")
                content = await self._fallback_scaffold(text, scaffold_type, context)
                processing_time = time.time() - start_time
                return ScaffoldResult(
                    content=content,
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text),
                    output_tokens=len(content.split())
                )
            else:
                raise
    
    async def generate_outline(
        self, 
        text: str, 
        outline_style: str = "bullet",
        max_points: int = 5
    ) -> OutlineResult:
        """
        Generate conversation outline and quick scaffolding.
        
        Args:
            text: Input text to outline
            outline_style: Style of outline ("bullet", "numbered", "structured")
            max_points: Maximum number of outline points
            
        Returns:
            OutlineResult with generated outline points
        """
        if not text or not text.strip():
            return OutlineResult(
                outline=[],
                processing_time=0.0,
                used_fallback=True,
                input_length=0
            )
        
        # Check cache first
        cache_key = self._get_cache_key(f"outline:{outline_style}:{max_points}:{text}")
        with self.lock:
            if cache_key in self.cache:
                self._cache_hits += 1
                return self.cache[cache_key]
            self._cache_misses += 1
        
        start_time = time.time()
        
        try:
            if self.fallback_mode or not self.client:
                outline = await self._fallback_outline(text, outline_style, max_points)
                used_fallback = True
            else:
                outline = await self._generate_outline_llm(text, outline_style, max_points)
                used_fallback = False
            
            processing_time = time.time() - start_time
            
            result = OutlineResult(
                outline=outline,
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text)
            )
            
            # Cache result
            with self.lock:
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 1000:
                    self._processing_times = self._processing_times[-1000:]
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Outline generation failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                logger.info("Falling back to rule-based outline due to error")
                outline = await self._fallback_outline(text, outline_style, max_points)
                processing_time = time.time() - start_time
                return OutlineResult(
                    outline=outline,
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text)
                )
            else:
                raise
    
    async def generate_short_fill(
        self, 
        context: str, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        fill_type: str = "continuation"
    ) -> ScaffoldResult:
        """
        Generate short generative fills for context completion.
        
        Args:
            context: Context text
            prompt: Specific prompt for generation
            max_tokens: Maximum tokens to generate
            fill_type: Type of fill ("continuation", "completion", "bridge", "elaboration")
            
        Returns:
            ScaffoldResult with generated fill content
        """
        # Enhanced prompt construction based on fill type
        if fill_type == "completion":
            combined_input = f"Complete this thought: {context}\n\n{prompt}"
        elif fill_type == "bridge":
            combined_input = f"Bridge these ideas: {context}\n\nConnecting to: {prompt}"
        elif fill_type == "elaboration":
            combined_input = f"Elaborate on: {context}\n\nSpecifically: {prompt}"
        else:  # continuation
            combined_input = f"{context}\n\n{prompt}"
        
        max_tokens = max_tokens or min(50, self.config.scaffold_max_tokens)
        
        return await self.generate_scaffold(
            combined_input, 
            scaffold_type="fill", 
            max_tokens=max_tokens
        )
    
    async def generate_conversation_outline(
        self, 
        topic: str, 
        conversation_context: Optional[Dict[str, Any]] = None,
        outline_depth: str = "standard"
    ) -> OutlineResult:
        """
        Generate conversation outlines for interactive discussions.
        
        Args:
            topic: Main topic for conversation
            conversation_context: Context including participants, goals, constraints
            outline_depth: Depth of outline ("brief", "standard", "detailed")
            
        Returns:
            OutlineResult with conversation flow outline
        """
        # Determine max points based on depth
        max_points_map = {"brief": 3, "standard": 5, "detailed": 8}
        max_points = max_points_map.get(outline_depth, 5)
        
        # Enhanced topic preparation with conversation context
        if conversation_context:
            participants = conversation_context.get("participants", "participants")
            goal = conversation_context.get("goal", "explore the topic")
            enhanced_topic = f"Conversation between {participants} to {goal} regarding: {topic}"
        else:
            enhanced_topic = f"Interactive discussion about: {topic}"
        
        return await self.generate_outline(
            enhanced_topic, 
            outline_style="conversation_flow", 
            max_points=max_points
        )
    
    async def generate_quick_scaffolding(
        self, 
        text: str, 
        scaffolding_purpose: str = "analysis",
        user_context: Optional[Dict[str, Any]] = None
    ) -> ScaffoldResult:
        """
        Generate quick scaffolding for immediate use in responses.
        
        Args:
            text: Input text to scaffold
            scaffolding_purpose: Purpose ("analysis", "response", "exploration", "synthesis")
            user_context: User context for personalization
            
        Returns:
            ScaffoldResult with quick scaffolding content
        """
        # Map purpose to scaffold type
        purpose_mapping = {
            "analysis": "analysis",
            "response": "conversation", 
            "exploration": "reasoning",
            "synthesis": "structure"
        }
        
        scaffold_type = purpose_mapping.get(scaffolding_purpose, "reasoning")
        
        # Use shorter token limit for quick scaffolding
        max_tokens = min(75, self.config.scaffold_max_tokens)
        
        return await self.generate_scaffold(
            text, 
            scaffold_type=scaffold_type, 
            max_tokens=max_tokens,
            context=user_context
        )
    
    async def summarize_context(
        self, 
        text: str, 
        summary_type: str = "concise",
        max_tokens: Optional[int] = None
    ) -> SummaryResult:
        """
        Generate context summarization for memory management.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary ("concise", "detailed", "key_points")
            max_tokens: Maximum tokens for summary
            
        Returns:
            SummaryResult with generated summary
        """
        if not text or not text.strip():
            return SummaryResult(
                summary="",
                processing_time=0.0,
                used_fallback=True,
                input_length=0,
                compression_ratio=0.0
            )
        
        # Check cache first
        cache_key = self._get_cache_key(f"summary:{summary_type}:{text}")
        with self.lock:
            if cache_key in self.cache:
                self._cache_hits += 1
                return self.cache[cache_key]
            self._cache_misses += 1
        
        start_time = time.time()
        max_tokens = max_tokens or self.config.summary_max_tokens
        
        try:
            if self.fallback_mode or not self.client:
                summary = await self._fallback_summary(text, summary_type)
                used_fallback = True
            else:
                summary = await self._generate_summary_llm(text, summary_type, max_tokens)
                used_fallback = False
            
            processing_time = time.time() - start_time
            compression_ratio = len(summary) / len(text) if text else 0.0
            
            result = SummaryResult(
                summary=summary,
                processing_time=processing_time,
                used_fallback=used_fallback,
                model_name=self.config.model_name if not used_fallback else "fallback",
                input_length=len(text),
                compression_ratio=compression_ratio
            )
            
            # Cache result
            with self.lock:
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 1000:
                    self._processing_times = self._processing_times[-1000:]
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Context summarization failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            
            # Fallback on error
            if not self.fallback_mode and self.config.enable_fallback:
                logger.info("Falling back to rule-based summary due to error")
                summary = await self._fallback_summary(text, summary_type)
                processing_time = time.time() - start_time
                compression_ratio = len(summary) / len(text) if text else 0.0
                return SummaryResult(
                    summary=summary,
                    processing_time=processing_time,
                    used_fallback=True,
                    model_name="fallback",
                    input_length=len(text),
                    compression_ratio=compression_ratio
                )
            else:
                raise
    
    async def _generate_scaffold_llm(
        self, 
        text: str, 
        scaffold_type: str, 
        max_tokens: int,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate scaffolding using Lite model with enhanced prompts."""
        # Create appropriate prompt based on scaffold type with enhanced context awareness
        if scaffold_type == "reasoning":
            prompt = f"Create a brief step-by-step reasoning outline for: {text}\n\nReasoning steps:"
        elif scaffold_type == "structure":
            prompt = f"Structure the following content into logical sections: {text}\n\nStructure:"
        elif scaffold_type == "conversation":
            # New scaffold type for conversation flow
            prompt = f"Create a conversation flow outline for discussing: {text}\n\nConversation flow:"
        elif scaffold_type == "analysis":
            # New scaffold type for analytical thinking
            prompt = f"Create an analytical framework for: {text}\n\nAnalysis framework:"
        elif scaffold_type == "fill":
            prompt = f"{text}\n\nContinue logically:"
        else:
            prompt = f"Create a structured scaffold for: {text}\n\nScaffold:"
        
        # Add context-aware enhancements if available
        if context:
            user_level = context.get("user_level", "intermediate")
            if user_level == "novice":
                prompt += "\n(Provide simple, clear steps)"
            elif user_level == "expert":
                prompt += "\n(Focus on key insights and advanced considerations)"
            
            # Add conversation history context if available
            if context.get("conversation_history"):
                prompt = f"Given the ongoing conversation context, {prompt.lower()}"
        
        messages = [{"role": "user", "content": prompt}]
        
        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.client.chat(
                messages, 
                max_tokens=max_tokens,
                temperature=self.config.temperature,
                stream=False
            )
        )
        
        return response.strip() if response else ""
    
    async def _generate_outline_llm(
        self, 
        text: str, 
        outline_style: str, 
        max_points: int
    ) -> List[str]:
        """Generate outline using Lite model with enhanced styles."""
        style_instruction = {
            "bullet": "Create a bullet point outline",
            "numbered": "Create a numbered outline", 
            "structured": "Create a structured hierarchical outline",
            "conversation_flow": "Create a conversation flow outline with natural discussion points",
            "analytical": "Create an analytical outline with logical progression",
            "exploratory": "Create an exploratory outline for investigating the topic"
        }.get(outline_style, "Create an outline")
        
        # Enhanced prompt construction
        if outline_style == "conversation_flow":
            prompt = f"{style_instruction} with {max_points} discussion phases for: {text}\n\nConversation outline:"
        elif outline_style == "analytical":
            prompt = f"{style_instruction} with {max_points} analytical steps for: {text}\n\nAnalytical outline:"
        else:
            prompt = f"{style_instruction} with {max_points} main points for: {text}\n\nOutline:"
        
        messages = [{"role": "user", "content": prompt}]
        
        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat(
                messages,
                max_tokens=self.config.outline_max_tokens,
                temperature=self.config.temperature,
                stream=False
            )
        )
        
        # Enhanced parsing for different outline styles
        if response:
            lines = response.strip().split('\n')
            outline = []
            for line in lines:
                line = line.strip()
                # More flexible parsing for different formats
                if line and (line.startswith('-') or line.startswith('•') or 
                           line.startswith('*') or line.startswith('→') or
                           any(line.startswith(f"{i}.") for i in range(1, 10)) or
                           any(line.startswith(f"Phase {i}") for i in range(1, 10)) or
                           any(line.startswith(f"Step {i}") for i in range(1, 10))):
                    # Clean up formatting while preserving meaningful prefixes
                    clean_line = line.lstrip('-•*→0123456789. ').strip()
                    # Handle "Phase" and "Step" prefixes
                    if line.startswith(("Phase", "Step")):
                        clean_line = line.strip()
                    if clean_line:
                        outline.append(clean_line)
            return outline[:max_points]
        
        return []
    
    async def _generate_summary_llm(
        self, 
        text: str, 
        summary_type: str, 
        max_tokens: int
    ) -> str:
        """Generate summary using Lite model with enhanced types."""
        type_instruction = {
            "concise": "Summarize concisely in 2-3 sentences",
            "detailed": "Provide a comprehensive summary with key details",
            "key_points": "Extract the most important key points",
            "contextual": "Summarize with focus on context and implications",
            "actionable": "Summarize with emphasis on actionable insights",
            "conversational": "Summarize in a conversational, accessible way"
        }.get(summary_type, "Summarize")
        
        # Enhanced prompt construction based on summary type
        if summary_type == "contextual":
            prompt = f"{type_instruction}: {text}\n\nContextual summary:"
        elif summary_type == "actionable":
            prompt = f"{type_instruction}: {text}\n\nActionable summary:"
        elif summary_type == "conversational":
            prompt = f"{type_instruction}: {text}\n\nConversational summary:"
        else:
            prompt = f"{type_instruction}: {text}\n\nSummary:"
        
        messages = [{"role": "user", "content": prompt}]
        
        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat(
                messages,
                max_tokens=max_tokens,
                temperature=self.config.temperature,
                stream=False
            )
        )
        
        return response.strip() if response else ""
    
    async def _fallback_scaffold(self, text: str, scaffold_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate enhanced rule-based scaffolding when Lite is unavailable."""
        if scaffold_type == "reasoning":
            # Enhanced reasoning steps with better analysis
            sentences = text.replace('?', '.').replace('!', '.').split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) > 1:
                return f"1. Analyze: {sentences[0][:60]}...\n2. Evaluate: {sentences[-1][:60]}...\n3. Synthesize findings\n4. Draw evidence-based conclusions"
            else:
                return f"1. Break down the core question\n2. Identify key factors and constraints\n3. Analyze relationships and implications\n4. Formulate reasoned conclusions"
        
        elif scaffold_type == "structure":
            # Enhanced structural breakdown with better organization
            words = text.split()
            if len(words) > 15:
                return f"Overview: {' '.join(words[:7])}...\nCore Analysis: {' '.join(words[7:14])}...\nImplications: Key insights and next steps\nConclusion: Summary and recommendations"
            elif len(words) > 5:
                return f"Main Topic: {' '.join(words[:5])}...\nKey Points: Analysis and details\nSummary: Conclusions and takeaways"
            else:
                return f"Focus: {text[:100]}...\nAnalysis: Context and implications\nOutcome: Key insights"
        
        elif scaffold_type == "conversation":
            # New conversation flow scaffold
            return f"Opening: Introduce the topic of {text[:40]}...\nExploration: Discuss key aspects and perspectives\nDeepening: Address complexities and nuances\nSynthesis: Integrate insights and conclusions"
        
        elif scaffold_type == "analysis":
            # New analytical framework scaffold
            return f"Problem Definition: {text[:50]}...\nData Gathering: Identify relevant information\nPattern Recognition: Find connections and trends\nEvaluation: Assess significance and implications\nConclusions: Synthesize findings"
        
        elif scaffold_type == "fill":
            # Enhanced continuation with better context awareness
            words = text.split()
            if words:
                last_word = words[-1]
                if "?" in text:
                    return f"To address the question about '{last_word}', we should consider..."
                elif any(word in text.lower() for word in ["because", "since", "therefore"]):
                    return f"Building on '{last_word}', this leads to..."
                else:
                    return f"Continuing from '{last_word}', the logical next step involves..."
            else:
                return "The discussion continues with relevant analysis and supporting details..."
        
        else:
            # Enhanced generic scaffold with better structure
            key_words = [word for word in text.split() if len(word) > 4][:3]
            return f"Framework for {' '.join(key_words) if key_words else 'analysis'}:\n• Context: {text[:50]}...\n• Key factors and relationships\n• Implications and consequences\n• Actionable insights and next steps"
    
    async def _fallback_outline(self, text: str, outline_style: str, max_points: int) -> List[str]:
        """Generate simple rule-based outline when Lite is unavailable."""
        # Break text into sentences and create outline points
        sentences = text.replace('?', '.').replace('!', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        outline = []
        for i, sentence in enumerate(sentences[:max_points]):
            if len(sentence) > 10:  # Skip very short fragments
                # Truncate long sentences
                clean_sentence = sentence[:80] + "..." if len(sentence) > 80 else sentence
                outline.append(clean_sentence)
        
        # If we don't have enough points, add generic ones
        while len(outline) < min(3, max_points):
            if len(outline) == 0:
                outline.append("Main topic analysis")
            elif len(outline) == 1:
                outline.append("Key considerations")
            elif len(outline) == 2:
                outline.append("Conclusions and next steps")
        
        return outline
    
    async def _fallback_summary(self, text: str, summary_type: str) -> str:
        """Generate simple rule-based summary when Lite is unavailable."""
        # Simple extractive summarization
        sentences = text.replace('?', '.').replace('!', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
        
        if not sentences:
            return "No content to summarize."
        
        if summary_type == "key_points":
            # Take first few sentences as key points
            points = sentences[:3]
            return "Key points: " + "; ".join(points)
        
        elif summary_type == "detailed":
            # Take more sentences for detailed summary
            summary_sentences = sentences[:min(5, len(sentences))]
            return " ".join(summary_sentences)
        
        else:  # concise
            # Take first and last sentence if available
            if len(sentences) == 1:
                return sentences[0]
            elif len(sentences) >= 2:
                return f"{sentences[0]} ... {sentences[-1]}"
            else:
                return sentences[0] if sentences else "Brief summary of content."
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        # Include model name and config in cache key
        config_hash = hashlib.md5(
            f"{self.config.model_name}_{self.config.temperature}_{self.config.max_tokens}".encode()
        ).hexdigest()[:8]
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"tinyllama:{config_hash}:{text_hash}"
    
    def get_health_status(self) -> LiteHealthStatus:
        """Get current health status of the service."""
        with self.lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            return LiteHealthStatus(
                is_healthy=not self.fallback_mode or self.config.enable_fallback,
                model_loaded=self.client is not None and not self.fallback_mode,
                fallback_mode=self.fallback_mode,
                cache_size=len(self.cache),
                cache_hit_rate=cache_hit_rate,
                avg_processing_time=avg_processing_time,
                error_count=self._error_count,
                last_error=self._last_error
            )
    
    def clear_cache(self):
        """Clear the service cache."""
        with self.lock:
            self.cache.clear()
            logger.info("Lite service cache cleared")
    
    def reset_metrics(self):
        """Reset monitoring metrics."""
        with self.lock:
            self._cache_hits = 0
            self._cache_misses = 0
            self._processing_times = []
            self._error_count = 0
            self._last_error = None
            logger.info("Lite service metrics reset")
    
    async def augment_response(
        self, 
        user_message: str, 
        main_response: str, 
        augmentation_type: str = "enhancement"
    ) -> Dict[str, Any]:
        """
        Augment main LLM responses with Lite insights for orchestration agent integration.
        
        Args:
            user_message: Original user message
            main_response: Response from main LLM
            augmentation_type: Type of augmentation ("enhancement", "scaffolding", "suggestions")
            
        Returns:
            Dictionary with augmentation results
        """
        augmentation_results = {
            "original_response": main_response,
            "augmentations": {},
            "processing_time": 0.0,
            "used_fallback": self.fallback_mode
        }
        
        start_time = time.time()
        
        try:
            if augmentation_type == "enhancement":
                # Generate scaffolding to enhance the response structure
                scaffold_result = await self.generate_scaffold(
                    f"User asked: {user_message}\nResponse given: {main_response}",
                    scaffold_type="analysis",
                    max_tokens=60
                )
                augmentation_results["augmentations"]["scaffold"] = scaffold_result.content
                
                # Generate follow-up suggestions
                outline_result = await self.generate_outline(
                    f"Follow-up topics for: {user_message}",
                    outline_style="conversation_flow",
                    max_points=3
                )
                augmentation_results["augmentations"]["follow_ups"] = outline_result.outline
                
            elif augmentation_type == "scaffolding":
                # Focus on structural scaffolding
                scaffold_result = await self.generate_scaffold(
                    user_message,
                    scaffold_type="structure",
                    max_tokens=80
                )
                augmentation_results["augmentations"]["structure"] = scaffold_result.content
                
            elif augmentation_type == "suggestions":
                # Focus on conversation suggestions
                outline_result = await self.generate_conversation_outline(
                    user_message,
                    outline_depth="brief"
                )
                augmentation_results["augmentations"]["conversation_flow"] = outline_result.outline
            
            augmentation_results["processing_time"] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Response augmentation failed: {e}")
            augmentation_results["error"] = str(e)
            augmentation_results["processing_time"] = time.time() - start_time
        
        return augmentation_results
    
    async def generate_response_prefix(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a brief prefix to guide main LLM responses.
        
        Args:
            user_message: User's message
            context: Additional context for prefix generation
            
        Returns:
            Brief prefix string for response guidance
        """
        try:
            # Generate quick scaffolding for response structure
            scaffold_result = await self.generate_quick_scaffolding(
                user_message,
                scaffolding_purpose="response",
                user_context=context
            )
            
            if scaffold_result.content:
                return f"Response structure: {scaffold_result.content[:100]}..."
            else:
                return ""
                
        except Exception as e:
            logger.debug(f"Prefix generation failed: {e}")
            return ""
    
    async def reload_model(self, new_model_name: Optional[str] = None):
        """Reload Lite model, optionally with a new model name."""
        if new_model_name:
            self.config.model_name = new_model_name
        
        logger.info(f"Reloading Lite model: {self.config.model_name}")
        
        try:
            if self.client and hasattr(self.client, 'switch_model'):
                # Use the switch_model method if available
                self.client.switch_model(self.config.model_name)
                self.fallback_mode = False
                logger.info("Lite model reloaded successfully")
                # Clear cache since model changed
                self.clear_cache()
            else:
                # Re-initialize the service
                self._initialize()
                
        except Exception as e:
            logger.error(f"Model reload failed: {e}")
            self._error_count += 1
            self._last_error = str(e)
            if self.config.enable_fallback:
                self.fallback_mode = True
                logger.warning("Model reload failed, using fallback mode")
            else:
                raise


# Factory function for easy instantiation
def get_small_language_model_service(config: Optional[SmallLanguageModelConfig] = None) -> SmallLanguageModelService:
    """Factory function to create Small Language Model service instance."""
    return SmallLanguageModelService(config=config)
