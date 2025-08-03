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
        """Build structured memory context from relevant memories with intelligent aggregation."""
        entities = []
        preferences = []
        facts = []
        relationships = []
        
        # Categorize and process memories
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
        
        # Resolve conflicts and aggregate preferences
        preferences = await self._resolve_preference_conflicts(preferences)
        facts = await self._resolve_fact_conflicts(facts)
        
        # Build intelligent context summary
        context_summary = await self._generate_context_summary(
            entities, preferences, facts, relationships
        )
        
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
    
    async def _resolve_preference_conflicts(
        self, 
        preferences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts in user preferences using recency and confidence."""
        if not preferences:
            return preferences
        
        # Group preferences by content/subject
        preference_groups = {}
        for pref in preferences:
            # Extract preference content from metadata
            pref_content = pref.get("metadata", {}).get("preference_content", "")
            
            # Use the preference content as the grouping key
            key = pref_content.lower() if pref_content else "general"
            
            if key not in preference_groups:
                preference_groups[key] = []
            preference_groups[key].append(pref)
        
        resolved_preferences = []
        
        for group_key, group_prefs in preference_groups.items():
            if len(group_prefs) == 1:
                resolved_preferences.extend(group_prefs)
            else:
                # Check for contradictory preferences (positive vs negative)
                positive_prefs = []
                negative_prefs = []
                
                for pref in group_prefs:
                    pref_type = pref.get("metadata", {}).get("preference_type", "")
                    if "negative" in pref_type or "don't" in pref.get("content", "").lower():
                        negative_prefs.append(pref)
                    else:
                        positive_prefs.append(pref)
                
                # If we have both positive and negative preferences, keep the most recent
                if positive_prefs and negative_prefs:
                    all_prefs = positive_prefs + negative_prefs
                    all_prefs.sort(key=lambda p: p.get("recency_score", 0), reverse=True)
                    resolved_preferences.append(all_prefs[0])
                    self._conflict_resolution_count += 1
                else:
                    # No conflict, keep the highest scoring preference
                    group_prefs.sort(key=lambda p: p.get("combined_score", 0), reverse=True)
                    resolved_preferences.append(group_prefs[0])
        
        return resolved_preferences
    
    async def _resolve_fact_conflicts(
        self, 
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts in factual memories using confidence and recency."""
        if not facts:
            return facts
        
        # Group facts by subject
        fact_groups = {}
        for fact in facts:
            subject = fact.get("metadata", {}).get("subject", "")
            if not subject:
                # Try to extract subject from content
                content = fact.get("content", "")
                subject = content.split()[0] if content else "unknown"
            
            if subject not in fact_groups:
                fact_groups[subject] = []
            fact_groups[subject].append(fact)
        
        resolved_facts = []
        
        for subject, group_facts in fact_groups.items():
            if len(group_facts) == 1:
                resolved_facts.extend(group_facts)
            else:
                # Check for contradictory facts about the same subject
                # Sort by confidence level (high > medium > low) and then by recency
                def sort_key(f):
                    confidence = f.get("metadata", {}).get("confidence", "low")
                    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(confidence, 1)
                    recency_score = f.get("recency_score", 0)
                    return (confidence_score, recency_score)
                
                group_facts.sort(key=sort_key, reverse=True)
                
                # Keep the most confident and recent fact
                resolved_facts.append(group_facts[0])
                
                # Log conflict resolution
                if len(group_facts) > 1:
                    self._conflict_resolution_count += 1
                    logger.info(f"Resolved fact conflict for subject '{subject}': kept most recent/confident fact")
        
        return resolved_facts
    
    async def _generate_context_summary(
        self,
        entities: List[Dict[str, Any]],
        preferences: List[Dict[str, Any]],
        facts: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> str:
        """Generate intelligent context summary with key insights."""
        summary_parts = []
        
        # Summarize entities
        if entities:
            entity_types = {}
            for entity in entities:
                entity_type = entity.get("metadata", {}).get("entity_label", "MISC")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            entity_summary = ", ".join([f"{count} {etype.lower()}" for etype, count in entity_types.items()])
            summary_parts.append(f"Entities: {entity_summary}")
        
        # Summarize preferences with insights
        if preferences:
            positive_prefs = []
            negative_prefs = []
            
            for pref in preferences:
                pref_type = pref.get("metadata", {}).get("preference_type", "")
                content = pref.get("content", "")
                
                if "negative" in pref_type or "don't" in content.lower():
                    negative_prefs.append(pref)
                else:
                    positive_prefs.append(pref)
            
            pref_summary = f"{len(positive_prefs)} likes"
            if negative_prefs:
                pref_summary += f", {len(negative_prefs)} dislikes"
            summary_parts.append(f"Preferences: {pref_summary}")
        
        # Summarize facts by type
        if facts:
            fact_types = {}
            for fact in facts:
                fact_type = fact.get("metadata", {}).get("fact_type", "general")
                fact_types[fact_type] = fact_types.get(fact_type, 0) + 1
            
            fact_summary = ", ".join([f"{count} {ftype.replace('_', ' ')}" for ftype, count in fact_types.items()])
            summary_parts.append(f"Facts: {fact_summary}")
        
        # Summarize relationships
        if relationships:
            summary_parts.append(f"Relationships: {len(relationships)} connections")
        
        if not summary_parts:
            return "No relevant context found"
        
        # Add confidence and recency insights
        all_memories = entities + preferences + facts + relationships
        if all_memories:
            avg_confidence = sum(1 for m in all_memories if m.get("metadata", {}).get("confidence") == "high") / len(all_memories)
            avg_recency = sum(m.get("recency_score", 0) for m in all_memories) / len(all_memories)
            
            confidence_note = "high confidence" if avg_confidence > 0.7 else "mixed confidence"
            recency_note = "recent" if avg_recency > 0.5 else "older"
            
            summary_parts.append(f"({confidence_note}, {recency_note} memories)")
        
        return f"Retrieved {', '.join(summary_parts)}"
    
    async def get_memory_analytics(
        self, 
        user_id: str, 
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive memory analytics and usage tracking."""
        try:
            # Build query for user's memories
            query = MemoryQuery(
                text="",
                user_id=user_id,
                top_k=1000,  # Get many memories for analysis
                similarity_threshold=0.0,  # Include all memories
                time_range=time_range
            )
            
            memories = await self.memory_manager.query_memories("default_tenant", query)
            
            if not memories:
                return {
                    "total_memories": 0,
                    "memory_types": {},
                    "confidence_distribution": {},
                    "temporal_distribution": {},
                    "extraction_methods": {},
                    "avg_similarity_scores": {},
                    "memory_growth": [],
                    "top_entities": [],
                    "preference_insights": {},
                    "fact_categories": {}
                }
            
            # Analyze memory types
            memory_types = {}
            confidence_dist = {"high": 0, "medium": 0, "low": 0}
            extraction_methods = {}
            temporal_dist = {}
            
            # Track entities and preferences for insights
            entities = {}
            preferences = {"positive": [], "negative": []}
            fact_categories = {}
            
            for memory in memories:
                # Memory type analysis
                mem_type = memory.metadata.get("type", "unknown")
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
                
                # Confidence analysis
                confidence = memory.metadata.get("confidence", "medium")
                confidence_dist[confidence] = confidence_dist.get(confidence, 0) + 1
                
                # Extraction method analysis
                method = memory.metadata.get("extraction_method", "unknown")
                extraction_methods[method] = extraction_methods.get(method, 0) + 1
                
                # Temporal analysis
                if memory.timestamp:
                    memory_date = datetime.fromtimestamp(memory.timestamp)
                    month_key = memory_date.strftime("%Y-%m")
                    temporal_dist[month_key] = temporal_dist.get(month_key, 0) + 1
                
                # Entity analysis
                if mem_type == "entity":
                    entity_label = memory.metadata.get("entity_label", "MISC")
                    entity_text = memory.metadata.get("entity_text", "")
                    if entity_text:
                        entities[entity_label] = entities.get(entity_label, [])
                        entities[entity_label].append(entity_text)
                
                # Preference analysis
                elif mem_type == "preference":
                    pref_type = memory.metadata.get("preference_type", "")
                    if "negative" in pref_type:
                        preferences["negative"].append(memory.content)
                    else:
                        preferences["positive"].append(memory.content)
                
                # Fact analysis
                elif mem_type == "fact":
                    fact_type = memory.metadata.get("fact_type", "general")
                    fact_categories[fact_type] = fact_categories.get(fact_type, 0) + 1
            
            # Calculate top entities
            top_entities = []
            for entity_type, entity_list in entities.items():
                entity_counts = {}
                for entity in entity_list:
                    entity_counts[entity] = entity_counts.get(entity, 0) + 1
                
                for entity, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    top_entities.append({
                        "entity": entity,
                        "type": entity_type,
                        "count": count
                    })
            
            # Memory growth analysis
            memory_growth = []
            sorted_months = sorted(temporal_dist.keys())
            cumulative = 0
            for month in sorted_months:
                cumulative += temporal_dist[month]
                memory_growth.append({
                    "month": month,
                    "new_memories": temporal_dist[month],
                    "total_memories": cumulative
                })
            
            # Preference insights
            preference_insights = {
                "total_preferences": len(preferences["positive"]) + len(preferences["negative"]),
                "positive_ratio": len(preferences["positive"]) / max(1, len(preferences["positive"]) + len(preferences["negative"])),
                "top_positive": preferences["positive"][:5],
                "top_negative": preferences["negative"][:5]
            }
            
            return {
                "total_memories": len(memories),
                "memory_types": memory_types,
                "confidence_distribution": confidence_dist,
                "temporal_distribution": temporal_dist,
                "extraction_methods": extraction_methods,
                "memory_growth": memory_growth,
                "top_entities": top_entities[:10],
                "preference_insights": preference_insights,
                "fact_categories": fact_categories,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "time_range": [t.isoformat() for t in time_range] if time_range else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate memory analytics: {e}")
            return {"error": str(e)}
    
    async def learn_user_preferences(
        self, 
        user_id: str, 
        conversation_history: List[str]
    ) -> Dict[str, Any]:
        """Learn and update user preferences from conversation patterns."""
        try:
            learned_patterns = {
                "communication_style": {},
                "topic_interests": {},
                "response_preferences": {},
                "interaction_patterns": {}
            }
            
            # Analyze conversation patterns
            for message in conversation_history:
                # Parse message for preference learning
                parsed_data = await self.spacy_service.parse_message(message)
                embeddings = await self.distilbert_service.get_embeddings(message)
                
                # Extract implicit preferences from communication style
                if len(message.split()) > 20:
                    learned_patterns["communication_style"]["verbose"] = learned_patterns["communication_style"].get("verbose", 0) + 1
                else:
                    learned_patterns["communication_style"]["concise"] = learned_patterns["communication_style"].get("concise", 0) + 1
                
                # Analyze question patterns
                if "?" in message:
                    learned_patterns["interaction_patterns"]["asks_questions"] = learned_patterns["interaction_patterns"].get("asks_questions", 0) + 1
                
                # Extract topic interests from entities
                for entity_text, entity_label in parsed_data.entities:
                    if entity_label in ["ORG", "PRODUCT", "WORK_OF_ART", "EVENT"]:
                        learned_patterns["topic_interests"][entity_text.lower()] = learned_patterns["topic_interests"].get(entity_text.lower(), 0) + 1
            
            # Store learned preferences as memories
            for category, patterns in learned_patterns.items():
                if patterns:
                    # Find the most common pattern in each category
                    top_pattern = max(patterns.items(), key=lambda x: x[1])
                    
                    # Create a preference memory
                    preference_content = f"User tends to {category.replace('_', ' ')}: {top_pattern[0]}"
                    
                    # Store as a learned preference
                    await self.memory_manager.store_memory(
                        tenant_id="default_tenant",
                        content=preference_content,
                        user_id=user_id,
                        metadata={
                            "type": "preference",
                            "preference_type": "learned_pattern",
                            "category": category,
                            "confidence": "medium",
                            "extraction_method": "pattern_learning",
                            "pattern_strength": top_pattern[1]
                        },
                        tags=["preference", "learned", category]
                    )
            
            logger.info(f"Learned {sum(len(p) for p in learned_patterns.values())} preference patterns for user {user_id}")
            
            return {
                "learned_patterns": learned_patterns,
                "total_patterns": sum(len(p) for p in learned_patterns.values()),
                "categories_analyzed": len([c for c, p in learned_patterns.items() if p]),
                "learning_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to learn user preferences: {e}")
            return {"error": str(e)}
    
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