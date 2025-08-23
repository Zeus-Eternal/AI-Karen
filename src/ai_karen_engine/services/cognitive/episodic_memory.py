"""
Episodic Memory Service - Human-like Conversation Memory

This module implements episodic memory patterns for conversation context,
including temporal tracking, emotional markers, and adaptive learning
from user interactions and outcomes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import math

from sqlalchemy import select, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession


class EmotionalValence(Enum):
    """Emotional valence of interactions."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


class InteractionOutcome(Enum):
    """Outcomes of interactions for learning."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    USER_SATISFIED = "user_satisfied"
    USER_FRUSTRATED = "user_frustrated"
    TASK_COMPLETED = "task_completed"
    TASK_ABANDONED = "task_abandoned"


class ContextImportance(Enum):
    """Importance levels for context weighting."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


@dataclass
class EmotionalMarker:
    """Represents emotional context of an interaction."""
    valence: EmotionalValence
    arousal: float  # 0.0 to 1.0, intensity of emotion
    confidence: float  # 0.0 to 1.0, confidence in emotion detection
    indicators: List[str] = field(default_factory=list)  # What indicated this emotion
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valence": self.valence.value,
            "arousal": self.arousal,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionalMarker':
        return cls(
            valence=EmotionalValence(data["valence"]),
            arousal=data["arousal"],
            confidence=data["confidence"],
            indicators=data.get("indicators", []),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


@dataclass
class InteractionPattern:
    """Represents learned patterns from user interactions."""
    pattern_id: str
    pattern_type: str  # "preference", "behavior", "communication_style", etc.
    description: str
    confidence: float
    frequency: int  # How often this pattern has been observed
    last_observed: datetime
    context_tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": self.confidence,
            "frequency": self.frequency,
            "last_observed": self.last_observed.isoformat(),
            "context_tags": self.context_tags,
            "examples": self.examples
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionPattern':
        return cls(
            pattern_id=data["pattern_id"],
            pattern_type=data["pattern_type"],
            description=data["description"],
            confidence=data["confidence"],
            frequency=data["frequency"],
            last_observed=datetime.fromisoformat(data["last_observed"]),
            context_tags=data.get("context_tags", []),
            examples=data.get("examples", [])
        )


@dataclass
class EpisodicMemory:
    """Represents a single episodic memory with temporal and emotional context."""
    memory_id: str
    conversation_id: str
    user_id: str
    content: str
    context_summary: str
    interaction_type: str  # "question", "request", "feedback", "casual", etc.
    timestamp: datetime
    session_id: Optional[str] = None
    
    # Temporal context
    session_duration: Optional[timedelta] = None
    time_since_last_interaction: Optional[timedelta] = None
    
    # Emotional context
    emotional_marker: Optional[EmotionalMarker] = None
    user_satisfaction: Optional[float] = None  # 0.0 to 1.0
    
    # Outcome and learning
    interaction_outcome: Optional[InteractionOutcome] = None
    success_indicators: List[str] = field(default_factory=list)
    failure_indicators: List[str] = field(default_factory=list)
    
    # Importance and decay
    importance_score: float = 0.5  # 0.0 to 1.0
    context_importance: ContextImportance = ContextImportance.MEDIUM
    decay_factor: float = 1.0  # Multiplier for importance over time
    
    # Relationships and patterns
    related_memories: List[str] = field(default_factory=list)  # memory_ids
    extracted_patterns: List[str] = field(default_factory=list)  # pattern_ids
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_current_importance(self) -> float:
        """Calculate current importance considering decay."""
        # Time-based decay (memories become less important over time)
        age_hours = (datetime.utcnow() - self.timestamp).total_seconds() / 3600
        time_decay = math.exp(-age_hours / (24 * 7))  # Half-life of 1 week
        
        # Emotional amplification (emotional memories are more important)
        emotional_boost = 1.0
        if self.emotional_marker:
            emotional_boost = 1.0 + (abs(self.emotional_marker.valence.value) * 0.3)
            emotional_boost *= (1.0 + self.emotional_marker.arousal * 0.2)
        
        # Outcome-based importance
        outcome_multiplier = 1.0
        if self.interaction_outcome:
            if self.interaction_outcome in [InteractionOutcome.SUCCESS, InteractionOutcome.USER_SATISFIED]:
                outcome_multiplier = 1.2
            elif self.interaction_outcome in [InteractionOutcome.FAILURE, InteractionOutcome.USER_FRUSTRATED]:
                outcome_multiplier = 1.3  # Failures are important to remember
        
        # Context importance multiplier
        context_multiplier = self.context_importance.value / 3.0  # Normalize to ~1.0
        
        return (
            self.importance_score * 
            self.decay_factor * 
            time_decay * 
            emotional_boost * 
            outcome_multiplier * 
            context_multiplier
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "session_duration": self.session_duration.total_seconds() if self.session_duration else None,
            "time_since_last_interaction": self.time_since_last_interaction.total_seconds() if self.time_since_last_interaction else None,
            "content": self.content,
            "context_summary": self.context_summary,
            "interaction_type": self.interaction_type,
            "emotional_marker": self.emotional_marker.to_dict() if self.emotional_marker else None,
            "user_satisfaction": self.user_satisfaction,
            "interaction_outcome": self.interaction_outcome.value if self.interaction_outcome else None,
            "success_indicators": self.success_indicators,
            "failure_indicators": self.failure_indicators,
            "importance_score": self.importance_score,
            "context_importance": self.context_importance.value,
            "decay_factor": self.decay_factor,
            "related_memories": self.related_memories,
            "extracted_patterns": self.extracted_patterns,
            "tags": self.tags,
            "metadata": self.metadata
        }


class EpisodicMemoryService:
    """
    Service for managing episodic memories with human-like temporal context,
    emotional markers, and adaptive learning from user interactions.
    """
    
    def __init__(self, db_client, storage_path: str = "data/episodic_memory"):
        self.db_client = db_client
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)
        
        # Memory management configuration
        self.max_memories_per_user = 10000
        self.memory_cleanup_interval_hours = 24
        self.importance_threshold = 0.1  # Memories below this are candidates for cleanup
        
        # Pattern learning configuration
        self.pattern_detection_enabled = True
        self.min_pattern_frequency = 3  # Minimum occurrences to establish a pattern
        self.pattern_confidence_threshold = 0.7
        
        # Emotional analysis configuration
        self.emotion_detection_enabled = True
        self.emotion_keywords = self._build_emotion_keywords()
        
        # In-memory caches for performance
        self.user_patterns: Dict[str, List[InteractionPattern]] = {}
        self.recent_memories: Dict[str, List[EpisodicMemory]] = {}  # user_id -> memories
        
        # Initialize storage
        asyncio.create_task(self._initialize_storage())
    
    def _build_emotion_keywords(self) -> Dict[EmotionalValence, List[str]]:
        """Build keyword mappings for emotion detection."""
        return {
            EmotionalValence.VERY_POSITIVE: [
                "excellent", "amazing", "perfect", "love", "fantastic", "brilliant",
                "outstanding", "wonderful", "incredible", "awesome"
            ],
            EmotionalValence.POSITIVE: [
                "good", "great", "nice", "helpful", "useful", "thanks", "thank you",
                "appreciate", "pleased", "satisfied", "happy", "glad"
            ],
            EmotionalValence.NEUTRAL: [
                "okay", "fine", "alright", "understand", "got it", "clear"
            ],
            EmotionalValence.NEGATIVE: [
                "bad", "wrong", "error", "problem", "issue", "difficult", "confused",
                "frustrated", "annoying", "slow", "broken", "not working"
            ],
            EmotionalValence.VERY_NEGATIVE: [
                "terrible", "awful", "hate", "horrible", "useless", "garbage",
                "worst", "disaster", "furious", "angry", "disgusted"
            ]
        }
    
    async def _initialize_storage(self):
        """Initialize storage for episodic memories."""
        try:
            # Create storage directory if it doesn't exist
            import os
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Load recent memories into cache
            await self._load_recent_memories_cache()
            
            # Load user patterns into cache
            await self._load_user_patterns_cache()
            
            self.logger.info("Episodic memory storage initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize episodic memory storage: {e}")
    
    async def _load_recent_memories_cache(self):
        """Load recent memories into cache for performance."""
        try:
            # Load memories from the last 7 days for active users
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # This would typically query a database table
            # For now, we'll initialize empty cache
            self.recent_memories = {}
            
        except Exception as e:
            self.logger.error(f"Failed to load recent memories cache: {e}")
    
    async def _load_user_patterns_cache(self):
        """Load user patterns into cache."""
        try:
            # Load established patterns for active users
            # For now, we'll initialize empty cache
            self.user_patterns = {}
            
        except Exception as e:
            self.logger.error(f"Failed to load user patterns cache: {e}")
    
    async def store_episodic_memory(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        context_summary: str,
        interaction_type: str,
        session_id: Optional[str] = None,
        user_feedback: Optional[str] = None,
        success_indicators: Optional[List[str]] = None,
        failure_indicators: Optional[List[str]] = None,
        importance: ContextImportance = ContextImportance.MEDIUM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EpisodicMemory:
        """Store a new episodic memory with full context."""
        try:
            memory_id = str(uuid.uuid4())
            
            # Calculate temporal context
            session_duration = None
            time_since_last = None
            
            if user_id in self.recent_memories:
                recent = self.recent_memories[user_id]
                if recent:
                    last_memory = recent[-1]
                    time_since_last = datetime.utcnow() - last_memory.timestamp
            
            # Detect emotional markers
            emotional_marker = None
            if self.emotion_detection_enabled:
                emotional_marker = await self._detect_emotional_markers(
                    content, user_feedback, success_indicators, failure_indicators
                )
            
            # Determine interaction outcome
            interaction_outcome = await self._determine_interaction_outcome(
                user_feedback, success_indicators, failure_indicators, emotional_marker
            )
            
            # Calculate user satisfaction
            user_satisfaction = await self._calculate_user_satisfaction(
                emotional_marker, interaction_outcome, user_feedback
            )
            
            # Create episodic memory
            memory = EpisodicMemory(
                memory_id=memory_id,
                conversation_id=conversation_id,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                session_duration=session_duration,
                time_since_last_interaction=time_since_last,
                content=content,
                context_summary=context_summary,
                interaction_type=interaction_type,
                emotional_marker=emotional_marker,
                user_satisfaction=user_satisfaction,
                interaction_outcome=interaction_outcome,
                success_indicators=success_indicators or [],
                failure_indicators=failure_indicators or [],
                importance_score=0.5,  # Will be adjusted based on learning
                context_importance=importance,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Store memory
            await self._persist_memory(memory)
            
            # Update cache
            if user_id not in self.recent_memories:
                self.recent_memories[user_id] = []
            self.recent_memories[user_id].append(memory)
            
            # Keep only recent memories in cache
            if len(self.recent_memories[user_id]) > 100:
                self.recent_memories[user_id] = self.recent_memories[user_id][-100:]
            
            # Learn patterns from this memory
            if self.pattern_detection_enabled:
                await self._learn_patterns_from_memory(memory)
            
            # Update related memories
            await self._update_memory_relationships(memory)
            
            self.logger.info(f"Stored episodic memory {memory_id} for user {user_id}")
            return memory
        
        except Exception as e:
            self.logger.error(f"Failed to store episodic memory: {e}")
            raise
    
    async def _detect_emotional_markers(
        self,
        content: str,
        user_feedback: Optional[str],
        success_indicators: Optional[List[str]],
        failure_indicators: Optional[List[str]]
    ) -> Optional[EmotionalMarker]:
        """Detect emotional markers from content and context."""
        try:
            content_lower = content.lower()
            indicators = []
            
            # Analyze content for emotional keywords
            valence_scores = {}
            for valence, keywords in self.emotion_keywords.items():
                score = sum(1 for keyword in keywords if keyword in content_lower)
                if score > 0:
                    valence_scores[valence] = score
                    indicators.extend([kw for kw in keywords if kw in content_lower])
            
            # Analyze user feedback
            if user_feedback:
                feedback_lower = user_feedback.lower()
                if any(word in feedback_lower for word in ["good", "great", "helpful", "thanks"]):
                    valence_scores[EmotionalValence.POSITIVE] = valence_scores.get(EmotionalValence.POSITIVE, 0) + 2
                    indicators.append("positive_feedback")
                elif any(word in feedback_lower for word in ["bad", "wrong", "unhelpful", "frustrated"]):
                    valence_scores[EmotionalValence.NEGATIVE] = valence_scores.get(EmotionalValence.NEGATIVE, 0) + 2
                    indicators.append("negative_feedback")
            
            # Analyze success/failure indicators
            if success_indicators:
                valence_scores[EmotionalValence.POSITIVE] = valence_scores.get(EmotionalValence.POSITIVE, 0) + len(success_indicators)
                indicators.extend([f"success:{ind}" for ind in success_indicators])
            
            if failure_indicators:
                valence_scores[EmotionalValence.NEGATIVE] = valence_scores.get(EmotionalValence.NEGATIVE, 0) + len(failure_indicators)
                indicators.extend([f"failure:{ind}" for ind in failure_indicators])
            
            if not valence_scores:
                return None
            
            # Determine dominant valence
            dominant_valence = max(valence_scores.items(), key=lambda x: x[1])
            valence = dominant_valence[0]
            
            # Calculate arousal (intensity) based on keyword strength and frequency
            arousal = min(dominant_valence[1] / 5.0, 1.0)  # Normalize to 0-1
            
            # Calculate confidence based on number of indicators
            confidence = min(len(indicators) / 3.0, 1.0)  # Normalize to 0-1
            
            return EmotionalMarker(
                valence=valence,
                arousal=arousal,
                confidence=confidence,
                indicators=indicators[:10]  # Limit indicators
            )
        
        except Exception as e:
            self.logger.error(f"Error detecting emotional markers: {e}")
            return None
    
    async def _determine_interaction_outcome(
        self,
        user_feedback: Optional[str],
        success_indicators: Optional[List[str]],
        failure_indicators: Optional[List[str]],
        emotional_marker: Optional[EmotionalMarker]
    ) -> Optional[InteractionOutcome]:
        """Determine the outcome of an interaction."""
        try:
            # Explicit success/failure indicators take precedence
            if success_indicators and not failure_indicators:
                return InteractionOutcome.SUCCESS
            elif failure_indicators and not success_indicators:
                return InteractionOutcome.FAILURE
            elif success_indicators and failure_indicators:
                return InteractionOutcome.PARTIAL_SUCCESS
            
            # Use emotional markers
            if emotional_marker:
                if emotional_marker.valence in [EmotionalValence.POSITIVE, EmotionalValence.VERY_POSITIVE]:
                    return InteractionOutcome.USER_SATISFIED
                elif emotional_marker.valence in [EmotionalValence.NEGATIVE, EmotionalValence.VERY_NEGATIVE]:
                    return InteractionOutcome.USER_FRUSTRATED
            
            # Analyze user feedback
            if user_feedback:
                feedback_lower = user_feedback.lower()
                if any(word in feedback_lower for word in ["complete", "done", "finished", "solved"]):
                    return InteractionOutcome.TASK_COMPLETED
                elif any(word in feedback_lower for word in ["give up", "quit", "stop", "cancel"]):
                    return InteractionOutcome.TASK_ABANDONED
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error determining interaction outcome: {e}")
            return None
    
    async def _calculate_user_satisfaction(
        self,
        emotional_marker: Optional[EmotionalMarker],
        interaction_outcome: Optional[InteractionOutcome],
        user_feedback: Optional[str]
    ) -> Optional[float]:
        """Calculate user satisfaction score (0.0 to 1.0)."""
        try:
            satisfaction_score = 0.5  # Default neutral
            
            # Emotional contribution
            if emotional_marker:
                valence_contribution = (emotional_marker.valence.value + 2) / 4.0  # Normalize -2,2 to 0,1
                arousal_weight = emotional_marker.arousal * emotional_marker.confidence
                satisfaction_score = (satisfaction_score + valence_contribution * arousal_weight) / 2
            
            # Outcome contribution
            if interaction_outcome:
                outcome_scores = {
                    InteractionOutcome.SUCCESS: 0.9,
                    InteractionOutcome.USER_SATISFIED: 0.8,
                    InteractionOutcome.TASK_COMPLETED: 0.85,
                    InteractionOutcome.PARTIAL_SUCCESS: 0.6,
                    InteractionOutcome.FAILURE: 0.2,
                    InteractionOutcome.USER_FRUSTRATED: 0.1,
                    InteractionOutcome.TASK_ABANDONED: 0.15
                }
                outcome_score = outcome_scores.get(interaction_outcome, 0.5)
                satisfaction_score = (satisfaction_score + outcome_score) / 2
            
            return max(0.0, min(1.0, satisfaction_score))
        
        except Exception as e:
            self.logger.error(f"Error calculating user satisfaction: {e}")
            return None
    
    async def _persist_memory(self, memory: EpisodicMemory):
        """Persist memory to storage."""
        try:
            # In a real implementation, this would save to a database
            # For now, we'll save to a JSON file
            import os
            
            user_dir = os.path.join(self.storage_path, memory.user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            memory_file = os.path.join(user_dir, f"{memory.memory_id}.json")
            with open(memory_file, 'w') as f:
                json.dump(memory.to_dict(), f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Failed to persist memory {memory.memory_id}: {e}")
    
    async def _learn_patterns_from_memory(self, memory: EpisodicMemory):
        """Learn interaction patterns from the new memory."""
        try:
            user_id = memory.user_id
            
            # Get user's existing patterns
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = []
            
            patterns = self.user_patterns[user_id]
            
            # Analyze for communication style patterns
            await self._detect_communication_style_pattern(memory, patterns)
            
            # Analyze for preference patterns
            await self._detect_preference_patterns(memory, patterns)
            
            # Analyze for behavioral patterns
            await self._detect_behavioral_patterns(memory, patterns)
            
            # Update pattern frequencies and confidence
            await self._update_pattern_statistics(memory, patterns)
        
        except Exception as e:
            self.logger.error(f"Error learning patterns from memory: {e}")
    
    async def _detect_communication_style_pattern(
        self, 
        memory: EpisodicMemory, 
        patterns: List[InteractionPattern]
    ):
        """Detect communication style patterns."""
        try:
            content = memory.content.lower()
            
            # Detect politeness pattern
            polite_indicators = ["please", "thank", "sorry", "excuse me", "pardon"]
            if any(indicator in content for indicator in polite_indicators):
                await self._update_or_create_pattern(
                    patterns, "communication_style", "polite",
                    "User tends to use polite language in interactions",
                    memory, ["politeness"]
                )
            
            # Detect directness pattern
            direct_indicators = ["just", "simply", "quickly", "need", "want"]
            if any(indicator in content for indicator in direct_indicators):
                await self._update_or_create_pattern(
                    patterns, "communication_style", "direct",
                    "User prefers direct, concise communication",
                    memory, ["directness"]
                )
            
            # Detect technical level
            technical_indicators = ["function", "class", "method", "api", "database", "algorithm"]
            if any(indicator in content for indicator in technical_indicators):
                await self._update_or_create_pattern(
                    patterns, "communication_style", "technical",
                    "User communicates at a technical level",
                    memory, ["technical_language"]
                )
        
        except Exception as e:
            self.logger.error(f"Error detecting communication style patterns: {e}")
    
    async def _detect_preference_patterns(
        self, 
        memory: EpisodicMemory, 
        patterns: List[InteractionPattern]
    ):
        """Detect user preference patterns."""
        try:
            # Detect response format preferences
            if memory.emotional_marker and memory.emotional_marker.valence.value > 0:
                # User was satisfied - learn from what worked
                if "code" in memory.content.lower():
                    await self._update_or_create_pattern(
                        patterns, "preference", "code_examples",
                        "User appreciates code examples in responses",
                        memory, ["code_preference"]
                    )
                
                if any(word in memory.content.lower() for word in ["step", "steps", "guide"]):
                    await self._update_or_create_pattern(
                        patterns, "preference", "step_by_step",
                        "User prefers step-by-step instructions",
                        memory, ["structured_guidance"]
                    )
        
        except Exception as e:
            self.logger.error(f"Error detecting preference patterns: {e}")
    
    async def _detect_behavioral_patterns(
        self, 
        memory: EpisodicMemory, 
        patterns: List[InteractionPattern]
    ):
        """Detect behavioral patterns."""
        try:
            # Detect session timing patterns
            if memory.timestamp.hour < 9:
                await self._update_or_create_pattern(
                    patterns, "behavior", "early_morning_user",
                    "User is active in early morning hours",
                    memory, ["timing", "early_morning"]
                )
            elif memory.timestamp.hour > 18:
                await self._update_or_create_pattern(
                    patterns, "behavior", "evening_user",
                    "User is active in evening hours",
                    memory, ["timing", "evening"]
                )
            
            # Detect interaction frequency patterns
            if memory.time_since_last_interaction:
                if memory.time_since_last_interaction.total_seconds() < 300:  # 5 minutes
                    await self._update_or_create_pattern(
                        patterns, "behavior", "rapid_interaction",
                        "User tends to have rapid back-and-forth interactions",
                        memory, ["interaction_frequency", "rapid"]
                    )
        
        except Exception as e:
            self.logger.error(f"Error detecting behavioral patterns: {e}")
    
    async def _update_or_create_pattern(
        self,
        patterns: List[InteractionPattern],
        pattern_type: str,
        pattern_key: str,
        description: str,
        memory: EpisodicMemory,
        tags: List[str]
    ):
        """Update existing pattern or create new one."""
        try:
            # Find existing pattern
            existing_pattern = None
            for pattern in patterns:
                if pattern.pattern_type == pattern_type and pattern_key in pattern.pattern_id:
                    existing_pattern = pattern
                    break
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.frequency += 1
                existing_pattern.last_observed = memory.timestamp
                existing_pattern.confidence = min(existing_pattern.frequency / 10.0, 1.0)
                existing_pattern.examples.append(memory.content[:100])
                if len(existing_pattern.examples) > 5:
                    existing_pattern.examples = existing_pattern.examples[-5:]
            else:
                # Create new pattern
                pattern_id = f"{pattern_type}_{pattern_key}_{memory.user_id}"
                new_pattern = InteractionPattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_type,
                    description=description,
                    confidence=0.1,  # Start with low confidence
                    frequency=1,
                    last_observed=memory.timestamp,
                    context_tags=tags,
                    examples=[memory.content[:100]]
                )
                patterns.append(new_pattern)
        
        except Exception as e:
            self.logger.error(f"Error updating/creating pattern: {e}")
    
    async def _update_pattern_statistics(
        self, 
        memory: EpisodicMemory, 
        patterns: List[InteractionPattern]
    ):
        """Update pattern statistics and confidence scores."""
        try:
            for pattern in patterns:
                # Increase confidence for patterns that lead to positive outcomes
                if (memory.emotional_marker and 
                    memory.emotional_marker.valence.value > 0 and
                    any(tag in memory.tags for tag in pattern.context_tags)):
                    
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)
                
                # Decrease confidence for patterns that lead to negative outcomes
                elif (memory.emotional_marker and 
                      memory.emotional_marker.valence.value < 0 and
                      any(tag in memory.tags for tag in pattern.context_tags)):
                    
                    pattern.confidence = max(pattern.confidence - 0.02, 0.0)
        
        except Exception as e:
            self.logger.error(f"Error updating pattern statistics: {e}")
    
    async def _update_memory_relationships(self, memory: EpisodicMemory):
        """Update relationships between memories."""
        try:
            user_id = memory.user_id
            
            if user_id not in self.recent_memories:
                return
            
            recent_memories = self.recent_memories[user_id]
            
            # Find related memories based on content similarity and temporal proximity
            for other_memory in recent_memories[-10:]:  # Check last 10 memories
                if other_memory.memory_id == memory.memory_id:
                    continue
                
                # Simple content similarity (can be enhanced with embeddings)
                similarity = await self._calculate_content_similarity(
                    memory.content, other_memory.content
                )
                
                # Temporal proximity bonus
                time_diff = abs((memory.timestamp - other_memory.timestamp).total_seconds())
                temporal_bonus = max(0, 1.0 - time_diff / (24 * 3600))  # Bonus for same day
                
                # Combined relationship score
                relationship_score = similarity + temporal_bonus * 0.3
                
                if relationship_score > 0.5:
                    memory.related_memories.append(other_memory.memory_id)
                    other_memory.related_memories.append(memory.memory_id)
        
        except Exception as e:
            self.logger.error(f"Error updating memory relationships: {e}")
    
    async def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity between two texts."""
        try:
            # Simple word overlap similarity (can be enhanced with embeddings)
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())
            
            # Remove common stop words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            words1 -= stop_words
            words2 -= stop_words
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1 & words2
            union = words1 | words2
            
            return len(intersection) / len(union) if union else 0.0
        
        except Exception as e:
            self.logger.error(f"Error calculating content similarity: {e}")
            return 0.0
    
    async def get_user_patterns(self, user_id: str) -> List[InteractionPattern]:
        """Get learned patterns for a user."""
        return self.user_patterns.get(user_id, [])
    
    async def get_contextual_memories(
        self, 
        user_id: str, 
        query_context: str, 
        max_memories: int = 10,
        importance_threshold: float = 0.3
    ) -> List[EpisodicMemory]:
        """Get contextually relevant memories for a user."""
        try:
            if user_id not in self.recent_memories:
                return []
            
            memories = self.recent_memories[user_id]
            
            # Filter by current importance and relevance
            relevant_memories = []
            for memory in memories:
                current_importance = memory.calculate_current_importance()
                
                if current_importance >= importance_threshold:
                    # Calculate relevance to query context
                    relevance = await self._calculate_content_similarity(
                        query_context, memory.content
                    )
                    
                    if relevance > 0.2:  # Minimum relevance threshold
                        relevant_memories.append((memory, current_importance + relevance))
            
            # Sort by combined importance and relevance
            relevant_memories.sort(key=lambda x: x[1], reverse=True)
            
            return [memory for memory, _ in relevant_memories[:max_memories]]
        
        except Exception as e:
            self.logger.error(f"Error getting contextual memories: {e}")
            return []
    
    async def update_memory_feedback(
        self, 
        memory_id: str, 
        user_feedback: str, 
        outcome: InteractionOutcome
    ):
        """Update memory with user feedback and outcome."""
        try:
            # Find memory in cache
            memory = None
            for user_memories in self.recent_memories.values():
                for mem in user_memories:
                    if mem.memory_id == memory_id:
                        memory = mem
                        break
                if memory:
                    break
            
            if not memory:
                self.logger.warning(f"Memory {memory_id} not found for feedback update")
                return
            
            # Update memory with feedback
            memory.interaction_outcome = outcome
            memory.user_satisfaction = await self._calculate_user_satisfaction(
                memory.emotional_marker, outcome, user_feedback
            )
            
            # Re-detect emotional markers with new feedback
            memory.emotional_marker = await self._detect_emotional_markers(
                memory.content, user_feedback, 
                memory.success_indicators, memory.failure_indicators
            )
            
            # Adjust importance based on feedback
            if outcome in [InteractionOutcome.SUCCESS, InteractionOutcome.USER_SATISFIED]:
                memory.importance_score = min(memory.importance_score + 0.1, 1.0)
            elif outcome in [InteractionOutcome.FAILURE, InteractionOutcome.USER_FRUSTRATED]:
                memory.importance_score = min(memory.importance_score + 0.15, 1.0)  # Failures are important
            
            # Persist updated memory
            await self._persist_memory(memory)
            
            self.logger.info(f"Updated memory {memory_id} with feedback")
        
        except Exception as e:
            self.logger.error(f"Error updating memory feedback: {e}")
    
    async def cleanup_old_memories(self):
        """Clean up old, low-importance memories."""
        try:
            cleaned_count = 0
            
            for user_id, memories in self.recent_memories.items():
                # Filter out memories that are too old and unimportant
                filtered_memories = []
                
                for memory in memories:
                    current_importance = memory.calculate_current_importance()
                    
                    # Keep memory if it's important or recent
                    age_days = (datetime.utcnow() - memory.timestamp).days
                    
                    if (current_importance >= self.importance_threshold or 
                        age_days < 7 or  # Keep memories from last week
                        memory.context_importance.value >= 4):  # Keep high-importance context
                        
                        filtered_memories.append(memory)
                    else:
                        cleaned_count += 1
                
                self.recent_memories[user_id] = filtered_memories
            
            self.logger.info(f"Cleaned up {cleaned_count} old memories")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old memories: {e}")
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about episodic memory usage."""
        try:
            total_memories = sum(len(memories) for memories in self.recent_memories.values())
            total_patterns = sum(len(patterns) for patterns in self.user_patterns.values())
            
            # Calculate average importance
            all_memories = []
            for memories in self.recent_memories.values():
                all_memories.extend(memories)
            
            avg_importance = 0.0
            if all_memories:
                avg_importance = sum(m.calculate_current_importance() for m in all_memories) / len(all_memories)
            
            return {
                "total_users": len(self.recent_memories),
                "total_memories": total_memories,
                "total_patterns": total_patterns,
                "average_importance": avg_importance,
                "memory_cleanup_threshold": self.importance_threshold,
                "pattern_detection_enabled": self.pattern_detection_enabled,
                "emotion_detection_enabled": self.emotion_detection_enabled
            }
        
        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {e}")
            return {}