"""
Memory extraction and context retrieval system for chat orchestrator.

This module implements automatic fact extraction using spaCy entity recognition,
preference detection using linguistic patterns and embeddings, semantic similarity
search using DistilBERT embeddings and Milvus, and memory deduplication with
conflict resolution.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.services.spacy_service import ParsedMessage, SpacyService
from ai_karen_engine.services.distilbert_service import DistilBertService
from ai_karen_engine.database.memory_manager import MemoryManager, MemoryEntry, MemoryQuery

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of extracted memories."""
    ENTITY = "entity"
    PREFERENCE = "preference"
    FACT = "fact"
    RELATIONSHIP = "relationship"
    CONTEXT = "context"
    TEMPORAL = "temporal"


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted memories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractedMemory:
    """Represents a memory extracted from user input."""
    
    content: str
    memory_type: MemoryType
    confidence: ConfidenceLevel
    source_message: str
    user_id: str
    conversation_id: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_method: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RelevantMemory:
    """Represents a relevant memory retrieved for context."""
    
    id: str
    content: str
    memory_type: MemoryType
    similarity_score: float
    recency_score: float
    combined_score: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryContext:
    """Context built from relevant memories."""
    
    memories: List[RelevantMemory]
    entities: List[Dict[str, Any]]
    preferences: List[Dict[str, Any]]
    facts: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    context_summary: str
    retrieval_time: float
    total_memories_considered: int


class MemoryProcessor:
    """
    Production-ready memory processor with spaCy and DistilBERT integration.
    
    Features:
    - Automatic fact extraction using spaCy entity recognition
    - Preference detection using linguistic patterns and embeddings
    - Semantic similarity search using DistilBERT embeddings and Milvus
    - Memory deduplication and conflict resolution
    """
    
    def __init__(
        self,
        spacy_service: SpacyService,
        distilbert_service: DistilBertService,
        memory_manager: MemoryManager,
        similarity_threshold: float = 0.7,
        deduplication_threshold: float = 0.95,
        max_context_memories: int = 10,
        recency_weight: float = 0.3
    ):
        self.spacy_service = spacy_service
        self.distilbert_service = distilbert_service
        self.memory_manager = memory_manager
        self.similarity_threshold = similarity_threshold
        self.deduplication_threshold = deduplication_threshold
        self.max_context_memories = max_context_memories
        self.recency_weight = recency_weight
        
        # Preference detection patterns
        self.preference_patterns = [
            (r"I (like|love|prefer|enjoy|adore) (.+)", "positive_preference"),
            (r"I (don't like|hate|dislike|can't stand|despise) (.+)", "negative_preference"),
            (r"My favorite (.+) is (.+)", "favorite"),
            (r"I usually (.+)", "habit"),
            (r"I always (.+)", "habit"),
            (r"I never (.+)", "negative_habit"),
            (r"I tend to (.+)", "tendency"),
            (r"I'm (good|bad|terrible|excellent) at (.+)", "skill_assessment"),
            (r"I work (at|for|with) (.+)", "work_info"),
            (r"I live in (.+)", "location_info"),
            (r"My (.+) is (.+)", "personal_info"),
            (r"I am (.+)", "identity_info"),
            (r"I have (.+)", "possession_info"),
            (r"I want to (.+)", "goal"),
            (r"I need to (.+)", "need"),
            (r"I'm planning to (.+)", "plan"),
            (r"I'm interested in (.+)", "interest"),
            (r"I believe (.+)", "belief"),
            (r"I think (.+)", "opinion")
        ]
        
        # Fact extraction patterns
        self.fact_patterns = [
            (r"(.+) is (.+)", "is_relationship"),
            (r"(.+) has (.+)", "has_relationship"),
            (r"(.+) can (.+)", "capability"),
            (r"(.+) will (.+)", "future_fact"),
            (r"(.+) was (.+)", "past_fact"),
            (r"(.+) happened (.+)", "event"),
            (r"(.+) costs (.+)", "cost_info"),
            (r"(.+) takes (.+) time", "duration_info"),
            (r"(.+) is located (.+)", "location_fact")
        ]
        
        # Processing metrics
        self._extraction_count = 0
        self._retrieval_count = 0
        self._deduplication_count = 0
        self._conflict_resolution_count = 0
        
        logger.info("MemoryProcessor initialized with NLP integration")
    
    async def extract_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """
        Extract memories from user message using spaCy and DistilBERT.
        
        Args:
            message: Original user message
            parsed_data: spaCy parsed message data
            embeddings: DistilBERT embeddings for the message
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            List of extracted memories
        """
        start_time = time.time()
        extracted_memories = []
        
        try:
            # Extract entity-based memories
            entity_memories = await self._extract_entity_memories(
                message, parsed_data, embeddings, user_id, conversation_id
            )
            extracted_memories.extend(entity_memories)
            
            # Extract preference memories
            preference_memories = await self._extract_preference_memories(
                message, parsed_data, embeddings, user_id, conversation_id
            )
            extracted_memories.extend(preference_memories)
            
            # Extract fact memories
            fact_memories = await self._extract_fact_memories(
                message, parsed_data, embeddings, user_id, conversation_id
            )
            extracted_memories.extend(fact_memories)
            
            # Extract relationship memories from dependency parsing
            relationship_memories = await self._extract_relationship_memories(
                message, parsed_data, embeddings, user_id, conversation_id
            )
            extracted_memories.extend(relationship_memories)
            
            # Extract temporal memories
            temporal_memories = await self._extract_temporal_memories(
                message, parsed_data, embeddings, user_id, conversation_id
            )
            extracted_memories.extend(temporal_memories)
            
            # Deduplicate memories
            deduplicated_memories = await self._deduplicate_memories(
                extracted_memories, user_id
            )
            
            # Store memories
            stored_memories = []
            for memory in deduplicated_memories:
                try:
                    memory_id = await self._store_memory(memory)
                    if memory_id:
                        stored_memories.append(memory)
                except Exception as e:
                    logger.warning(f"Failed to store memory: {e}")
                    continue
            
            processing_time = time.time() - start_time
            self._extraction_count += 1
            
            logger.info(
                f"Extracted {len(stored_memories)} memories from message "
                f"in {processing_time:.3f}s (user: {user_id})"
            )
            
            return stored_memories
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}", exc_info=True)
            return []
    
    async def get_relevant_context(
        self,
        query_embedding: List[float],
        parsed_query: ParsedMessage,
        user_id: str,
        conversation_id: str,
        max_memories: Optional[int] = None
    ) -> MemoryContext:
        """
        Retrieve relevant context using semantic similarity search.
        
        Args:
            query_embedding: DistilBERT embedding of the query
            parsed_query: spaCy parsed query data
            user_id: User identifier
            conversation_id: Conversation identifier
            max_memories: Maximum number of memories to retrieve
            
        Returns:
            Memory context with relevant memories and structured data
        """
        start_time = time.time()
        max_memories = max_memories or self.max_context_memories
        
        try:
            # Build memory query
            query = MemoryQuery(
                text="",  # We're using embeddings directly
                user_id=user_id,
                top_k=max_memories * 2,  # Get more for filtering
                similarity_threshold=self.similarity_threshold,
                include_embeddings=False
            )
            
            # Add entity-based filtering if available
            if parsed_query.entities:
                entity_tags = [f"entity:{ent[1]}" for ent in parsed_query.entities]
                query.tags.extend(entity_tags)
            
            # Retrieve memories using semantic search
            memories = await self.memory_manager.query_memories("default_tenant", query)
            
            # Calculate semantic similarity scores
            relevant_memories = []
            for memory in memories:
                if memory.embedding:
                    similarity = await self._calculate_similarity(
                        query_embedding, memory.embedding
                    )
                    if similarity >= self.similarity_threshold:
                        # Calculate recency score
                        recency = self._calculate_recency_score(memory.timestamp)
                        
                        # Combined score
                        combined_score = (
                            similarity * (1 - self.recency_weight) +
                            recency * self.recency_weight
                        )
                        
                        relevant_memory = RelevantMemory(
                            id=memory.id,
                            content=memory.content,
                            memory_type=MemoryType(memory.metadata.get("type", "context")),
                            similarity_score=similarity,
                            recency_score=recency,
                            combined_score=combined_score,
                            created_at=datetime.fromtimestamp(memory.timestamp) if memory.timestamp else datetime.utcnow(),
                            metadata=memory.metadata
                        )
                        relevant_memories.append(relevant_memory)
            
            # Sort by combined score and limit results
            relevant_memories.sort(key=lambda m: m.combined_score, reverse=True)
            relevant_memories = relevant_memories[:max_memories]
            
            # Build structured context
            context = await self._build_memory_context(relevant_memories)
            
            processing_time = time.time() - start_time
            context.retrieval_time = processing_time
            context.total_memories_considered = len(memories)
            
            self._retrieval_count += 1
            
            logger.info(
                f"Retrieved {len(relevant_memories)} relevant memories "
                f"in {processing_time:.3f}s (user: {user_id})"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}", exc_info=True)
            return MemoryContext(
                memories=[],
                entities=[],
                preferences=[],
                facts=[],
                relationships=[],
                context_summary="",
                retrieval_time=time.time() - start_time,
                total_memories_considered=0
            )
    
    async def _extract_entity_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """Extract entity-based memories using spaCy NER."""
        memories = []
        
        for entity_text, entity_label in parsed_data.entities:
            # Skip common entities that are not informative
            if entity_label in ["DATE", "TIME", "CARDINAL", "ORDINAL"]:
                continue
            
            # Determine confidence based on entity type
            confidence = ConfidenceLevel.HIGH
            if entity_label in ["MISC", "NORP"]:
                confidence = ConfidenceLevel.MEDIUM
            
            memory = ExtractedMemory(
                content=f"{entity_label}: {entity_text}",
                memory_type=MemoryType.ENTITY,
                confidence=confidence,
                source_message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                embedding=embeddings,
                metadata={
                    "entity_text": entity_text,
                    "entity_label": entity_label,
                    "extraction_method": "spacy_ner"
                },
                extraction_method="spacy_ner"
            )
            memories.append(memory)
        
        return memories
    
    async def _extract_preference_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """Extract preference memories using linguistic patterns."""
        memories = []
        
        for pattern, preference_type in self.preference_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                # Extract the preference content
                if len(match.groups()) >= 2:
                    preference_content = match.group(2).strip()
                    full_match = match.group(0)
                else:
                    preference_content = match.group(1).strip()
                    full_match = match.group(0)
                
                # Skip very short or generic preferences
                if len(preference_content) < 3:
                    continue
                
                # Determine confidence based on pattern strength
                confidence = ConfidenceLevel.HIGH
                if preference_type in ["tendency", "opinion"]:
                    confidence = ConfidenceLevel.MEDIUM
                
                memory = ExtractedMemory(
                    content=full_match,
                    memory_type=MemoryType.PREFERENCE,
                    confidence=confidence,
                    source_message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    embedding=embeddings,
                    metadata={
                        "preference_type": preference_type,
                        "preference_content": preference_content,
                        "extraction_method": "pattern_matching"
                    },
                    extraction_method="pattern_matching"
                )
                memories.append(memory)
        
        return memories
    
    async def _extract_fact_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """Extract factual memories using linguistic patterns."""
        memories = []
        
        for pattern, fact_type in self.fact_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0).strip()
                
                # Skip very short facts
                if len(full_match) < 5:
                    continue
                
                # Extract subject and object if available
                subject = match.group(1).strip() if len(match.groups()) >= 1 else ""
                obj = match.group(2).strip() if len(match.groups()) >= 2 else ""
                
                # Determine confidence based on fact type
                if fact_type in ["is_relationship", "has_relationship"]:
                    confidence = ConfidenceLevel.HIGH
                elif fact_type in ["capability", "future_fact", "past_fact"]:
                    confidence = ConfidenceLevel.MEDIUM
                else:
                    confidence = ConfidenceLevel.MEDIUM
                
                memory = ExtractedMemory(
                    content=full_match,
                    memory_type=MemoryType.FACT,
                    confidence=confidence,
                    source_message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    embedding=embeddings,
                    metadata={
                        "fact_type": fact_type,
                        "subject": subject,
                        "object": obj,
                        "extraction_method": "pattern_matching"
                    },
                    extraction_method="pattern_matching"
                )
                memories.append(memory)
        
        return memories
    
    async def _extract_relationship_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """Extract relationship memories from dependency parsing."""
        memories = []
        
        if parsed_data.used_fallback:
            return memories  # Skip if spaCy fallback was used
        
        # Extract subject-verb-object relationships
        for dep in parsed_data.dependencies:
            if dep["dep"] in ["nsubj", "dobj", "pobj"] and dep["head"] != "ROOT":
                # Build relationship description
                relationship = f"{dep['text']} --{dep['dep']}--> {dep['head']}"
                
                memory = ExtractedMemory(
                    content=relationship,
                    memory_type=MemoryType.RELATIONSHIP,
                    confidence=ConfidenceLevel.MEDIUM,
                    source_message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    embedding=embeddings,
                    metadata={
                        "subject": dep["text"],
                        "relation": dep["dep"],
                        "object": dep["head"],
                        "pos_subject": dep["pos"],
                        "pos_object": dep["head_pos"],
                        "extraction_method": "dependency_parsing"
                    },
                    extraction_method="dependency_parsing"
                )
                memories.append(memory)
        
        return memories
    
    async def _extract_temporal_memories(
        self,
        message: str,
        parsed_data: ParsedMessage,
        embeddings: List[float],
        user_id: str,
        conversation_id: str
    ) -> List[ExtractedMemory]:
        """Extract temporal memories from time-related entities and patterns."""
        memories = []
        
        # Extract time-related entities
        temporal_entities = [
            (text, label) for text, label in parsed_data.entities
            if label in ["DATE", "TIME", "EVENT"]
        ]
        
        for entity_text, entity_label in temporal_entities:
            # Create temporal context
            temporal_context = f"Temporal reference: {entity_text} ({entity_label})"
            
            memory = ExtractedMemory(
                content=temporal_context,
                memory_type=MemoryType.TEMPORAL,
                confidence=ConfidenceLevel.MEDIUM,
                source_message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                embedding=embeddings,
                metadata={
                    "temporal_entity": entity_text,
                    "temporal_type": entity_label,
                    "extraction_method": "temporal_ner"
                },
                extraction_method="temporal_ner"
            )
            memories.append(memory)
        
        return memories
    
    async def _deduplicate_memories(
        self,
        memories: List[ExtractedMemory],
        user_id: str
    ) -> List[ExtractedMemory]:
        """Deduplicate memories using semantic similarity."""
        if not memories:
            return memories
        
        deduplicated = []
        
        for memory in memories:
            is_duplicate = False
            
            # Check against existing memories in the same extraction batch
            for existing in deduplicated:
                if await self._are_memories_similar(memory, existing):
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if memory.confidence.value > existing.confidence.value:
                        deduplicated.remove(existing)
                        deduplicated.append(memory)
                    break
            
            if not is_duplicate:
                # Check against stored memories
                is_stored_duplicate = await self._check_stored_duplicates(memory, user_id)
                if not is_stored_duplicate:
                    deduplicated.append(memory)
                else:
                    self._deduplication_count += 1
        
        return deduplicated
    
    async def _are_memories_similar(
        self,
        memory1: ExtractedMemory,
        memory2: ExtractedMemory
    ) -> bool:
        """Check if two memories are similar enough to be considered duplicates."""
        # Same type and very similar content
        if memory1.memory_type != memory2.memory_type:
            return False
        
        # Calculate content similarity
        if memory1.embedding and memory2.embedding:
            similarity = await self._calculate_similarity(
                memory1.embedding, memory2.embedding
            )
            return similarity >= self.deduplication_threshold
        
        # Fallback to string similarity
        content1 = memory1.content.lower().strip()
        content2 = memory2.content.lower().strip()
        
        # Simple string similarity
        if content1 == content2:
            return True
        
        # Check if one is contained in the other
        if content1 in content2 or content2 in content1:
            return True
        
        return False
    
    async def _check_stored_duplicates(
        self,
        memory: ExtractedMemory,
        user_id: str
    ) -> bool:
        """Check if memory is duplicate of stored memories."""
        try:
            # Query similar memories
            query = MemoryQuery(
                text=memory.content,
                user_id=user_id,
                top_k=5,
                similarity_threshold=self.deduplication_threshold,
                metadata_filter={"type": memory.memory_type.value}
            )
            
            similar_memories = await self.memory_manager.query_memories("default_tenant", query)
            
            # Check if any are too similar
            for stored_memory in similar_memories:
                if stored_memory.embedding and memory.embedding:
                    similarity = await self._calculate_similarity(
                        memory.embedding, stored_memory.embedding
                    )
                    if similarity >= self.deduplication_threshold:
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check stored duplicates: {e}")
            return False
    
    async def _store_memory(self, memory: ExtractedMemory) -> Optional[str]:
        """Store extracted memory in the memory manager."""
        try:
            metadata = {
                "type": memory.memory_type.value,
                "confidence": memory.confidence.value,
                "extraction_method": memory.extraction_method,
                "conversation_id": memory.conversation_id,
                **memory.metadata
            }
            
            memory_id = await self.memory_manager.store_memory(
                tenant_id="default_tenant",
                content=memory.content,
                user_id=memory.user_id,
                metadata=metadata,
                tags=[memory.memory_type.value, memory.confidence.value]
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return None
    
    async def _calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: Union[List[float], Any]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert embedding2 to list if needed
            if not isinstance(embedding2, list):
                embedding2 = embedding2.tolist() if hasattr(embedding2, 'tolist') else list(embedding2)
            
            if NUMPY_AVAILABLE and np is not None:
                # Use numpy for efficient calculation
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)
                
                # Calculate cosine similarity
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
            else:
                # Fallback to pure Python calculation
                # Calculate dot product
                dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
                
                # Calculate norms
                norm1 = math.sqrt(sum(a * a for a in embedding1))
                norm2 = math.sqrt(sum(b * b for b in embedding2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_recency_score(self, timestamp: float) -> float:
        """Calculate recency score based on timestamp."""
        current_time = time.time()
        age_hours = (current_time - timestamp) / 3600
        
        # Exponential decay with half-life of 24 hours
        half_life = 24.0
        decay_factor = 0.693 / half_life  # ln(2) / half_life
        
        if NUMPY_AVAILABLE and np is not None and hasattr(np, 'exp'):
            recency_score = np.exp(-decay_factor * age_hours)
        else:
            recency_score = math.exp(-decay_factor * age_hours)
        
        return float(recency_score)
    
    async def _build_memory_context(
        self,
        relevant_memories: List[RelevantMemory]
    ) -> MemoryContext:
        """Build structured memory context from relevant memories."""
        entities = []
        preferences = []
        facts = []
        relationships = []
        
        # Categorize memories
        for memory in relevant_memories:
            memory_data = {
                "content": memory.content,
                "similarity_score": memory.similarity_score,
                "recency_score": memory.recency_score,
                "combined_score": memory.combined_score,
                "metadata": memory.metadata
            }
            
            if memory.memory_type == MemoryType.ENTITY:
                entities.append(memory_data)
            elif memory.memory_type == MemoryType.PREFERENCE:
                preferences.append(memory_data)
            elif memory.memory_type == MemoryType.FACT:
                facts.append(memory_data)
            elif memory.memory_type == MemoryType.RELATIONSHIP:
                relationships.append(memory_data)
        
        # Build context summary
        context_parts = []
        if entities:
            context_parts.append(f"{len(entities)} relevant entities")
        if preferences:
            context_parts.append(f"{len(preferences)} user preferences")
        if facts:
            context_parts.append(f"{len(facts)} factual memories")
        if relationships:
            context_parts.append(f"{len(relationships)} relationships")
        
        context_summary = f"Retrieved {', '.join(context_parts)}" if context_parts else "No relevant memories found"
        
        return MemoryContext(
            memories=relevant_memories,
            entities=entities,
            preferences=preferences,
            facts=facts,
            relationships=relationships,
            context_summary=context_summary,
            retrieval_time=0.0,  # Will be set by caller
            total_memories_considered=0  # Will be set by caller
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get memory processing statistics."""
        return {
            "extraction_count": self._extraction_count,
            "retrieval_count": self._retrieval_count,
            "deduplication_count": self._deduplication_count,
            "conflict_resolution_count": self._conflict_resolution_count,
            "similarity_threshold": self.similarity_threshold,
            "deduplication_threshold": self.deduplication_threshold,
            "max_context_memories": self.max_context_memories,
            "recency_weight": self.recency_weight
        }
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._extraction_count = 0
        self._retrieval_count = 0
        self._deduplication_count = 0
        self._conflict_resolution_count = 0
        logger.info("MemoryProcessor statistics reset")