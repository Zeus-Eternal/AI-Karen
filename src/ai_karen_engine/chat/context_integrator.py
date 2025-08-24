"""
Enhanced context integration for ChatOrchestrator.

This module provides sophisticated context integration from memory retrieval results,
relevance scoring, and context summarization to prevent token limit issues.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """Types of context that can be integrated."""
    MEMORY = "memory"
    CONVERSATION_HISTORY = "conversation_history"
    USER_PREFERENCES = "user_preferences"
    ENTITIES = "entities"
    FACTS = "facts"
    RELATIONSHIPS = "relationships"
    INSTRUCTIONS = "instructions"
    ATTACHMENTS = "attachments"


class RelevanceScore(str, Enum):
    """Relevance score categories."""
    VERY_HIGH = "very_high"  # 0.8-1.0
    HIGH = "high"           # 0.6-0.8
    MEDIUM = "medium"       # 0.4-0.6
    LOW = "low"            # 0.2-0.4
    VERY_LOW = "very_low"  # 0.0-0.2


@dataclass
class ContextItem:
    """Represents a single context item with relevance scoring."""
    id: str
    type: ContextType
    content: str
    relevance_score: float
    recency_score: float
    importance_score: float
    combined_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_relevance_category(self) -> RelevanceScore:
        """Get the relevance category based on combined score."""
        if self.combined_score >= 0.8:
            return RelevanceScore.VERY_HIGH
        elif self.combined_score >= 0.6:
            return RelevanceScore.HIGH
        elif self.combined_score >= 0.4:
            return RelevanceScore.MEDIUM
        elif self.combined_score >= 0.2:
            return RelevanceScore.LOW
        else:
            return RelevanceScore.VERY_LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "recency_score": self.recency_score,
            "importance_score": self.importance_score,
            "combined_score": self.combined_score,
            "relevance_category": self.get_relevance_category().value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class IntegratedContext:
    """Represents the final integrated context for LLM processing."""
    primary_context: str
    supporting_context: str
    context_summary: str
    token_count: int
    items_included: List[ContextItem]
    items_excluded: List[ContextItem]
    relevance_threshold: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "primary_context": self.primary_context,
            "supporting_context": self.supporting_context,
            "context_summary": self.context_summary,
            "token_count": self.token_count,
            "items_included_count": len(self.items_included),
            "items_excluded_count": len(self.items_excluded),
            "relevance_threshold": self.relevance_threshold,
            "included_by_type": self._count_by_type(self.items_included),
            "excluded_by_type": self._count_by_type(self.items_excluded),
            "metadata": self.metadata
        }
    
    def _count_by_type(self, items: List[ContextItem]) -> Dict[str, int]:
        """Count items by type."""
        counts = {}
        for item in items:
            type_key = item.type.value
            counts[type_key] = counts.get(type_key, 0) + 1
        return counts


class ContextIntegrator:
    """
    Enhanced context integrator for memory retrieval results.
    
    Features:
    - Relevance scoring for retrieved memories
    - Context summarization to prevent token limit issues
    - Intelligent context prioritization
    - Token-aware context building
    """
    
    def __init__(
        self,
        max_context_tokens: int = 2000,
        relevance_threshold: float = 0.3,
        recency_weight: float = 0.3,
        relevance_weight: float = 0.5,
        importance_weight: float = 0.2
    ):
        self.max_context_tokens = max_context_tokens
        self.relevance_threshold = relevance_threshold
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.importance_weight = importance_weight
        
        logger.info(f"ContextIntegrator initialized with max_tokens={max_context_tokens}")
    
    async def integrate_context(
        self,
        raw_context: Dict[str, Any],
        current_message: str,
        user_id: str,
        conversation_id: str
    ) -> IntegratedContext:
        """
        Integrate raw context from memory retrieval into structured context.
        
        Args:
            raw_context: Raw context from memory retrieval
            current_message: Current user message
            user_id: User ID
            conversation_id: Conversation ID
            
        Returns:
            IntegratedContext with scored and prioritized context
        """
        # Extract and score context items
        context_items = await self._extract_context_items(raw_context, current_message)
        
        # Score and rank context items
        scored_items = await self._score_context_items(context_items, current_message)
        
        # Filter by relevance threshold
        relevant_items = [
            item for item in scored_items
            if item.combined_score >= self.relevance_threshold
        ]
        
        # Sort by combined score (descending)
        relevant_items.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Build context within token limits
        integrated_context = await self._build_integrated_context(
            relevant_items,
            scored_items,
            current_message,
            user_id,
            conversation_id
        )
        
        logger.debug(
            f"Integrated context: {len(integrated_context.items_included)} included, "
            f"{len(integrated_context.items_excluded)} excluded, "
            f"{integrated_context.token_count} tokens"
        )
        
        return integrated_context
    
    async def _extract_context_items(
        self,
        raw_context: Dict[str, Any],
        current_message: str
    ) -> List[ContextItem]:
        """Extract context items from raw context data."""
        items = []
        
        # Extract memories
        memories = raw_context.get("memories", [])
        for memory in memories:
            if isinstance(memory, dict):
                item = ContextItem(
                    id=memory.get("id", f"memory_{len(items)}"),
                    type=ContextType.MEMORY,
                    content=memory.get("content", ""),
                    relevance_score=memory.get("similarity_score", 0.0),
                    recency_score=memory.get("recency_score", 0.0),
                    importance_score=memory.get("combined_score", 0.0),
                    combined_score=0.0,  # Will be calculated later
                    metadata={
                        "memory_type": memory.get("type", "unknown"),
                        "created_at": memory.get("created_at"),
                        "original_metadata": memory.get("metadata", {})
                    }
                )
                items.append(item)
        
        # Extract entities
        entities = raw_context.get("entities", [])
        if entities:
            entity_content = self._format_entities(entities)
            if entity_content:
                item = ContextItem(
                    id="entities_summary",
                    type=ContextType.ENTITIES,
                    content=entity_content,
                    relevance_score=0.7,  # Entities are generally relevant
                    recency_score=1.0,    # Current message entities
                    importance_score=0.6,
                    combined_score=0.0,
                    metadata={"entity_count": len(entities)}
                )
                items.append(item)
        
        # Extract preferences
        preferences = raw_context.get("preferences", [])
        for pref in preferences:
            if isinstance(pref, dict):
                item = ContextItem(
                    id=f"preference_{len(items)}",
                    type=ContextType.USER_PREFERENCES,
                    content=pref.get("content", str(pref)),
                    relevance_score=0.6,
                    recency_score=0.8,
                    importance_score=0.7,
                    combined_score=0.0,
                    metadata={"preference_type": pref.get("type", "general")}
                )
                items.append(item)
        
        # Extract facts
        facts = raw_context.get("facts", [])
        for fact in facts:
            if isinstance(fact, dict):
                item = ContextItem(
                    id=f"fact_{len(items)}",
                    type=ContextType.FACTS,
                    content=fact.get("content", str(fact)),
                    relevance_score=fact.get("confidence", 0.5),
                    recency_score=0.7,
                    importance_score=fact.get("importance", 0.5),
                    combined_score=0.0,
                    metadata={"fact_type": fact.get("type", "general")}
                )
                items.append(item)
        
        # Extract relationships
        relationships = raw_context.get("relationships", [])
        if relationships:
            relationship_content = self._format_relationships(relationships)
            if relationship_content:
                item = ContextItem(
                    id="relationships_summary",
                    type=ContextType.RELATIONSHIPS,
                    content=relationship_content,
                    relevance_score=0.5,
                    recency_score=0.6,
                    importance_score=0.6,
                    combined_score=0.0,
                    metadata={"relationship_count": len(relationships)}
                )
                items.append(item)
        
        # Extract attachment context
        attachments = raw_context.get("attachments", {})
        if attachments and attachments.get("total_files", 0) > 0:
            attachment_content = self._format_attachments(attachments)
            if attachment_content:
                item = ContextItem(
                    id="attachments_summary",
                    type=ContextType.ATTACHMENTS,
                    content=attachment_content,
                    relevance_score=0.8,  # Attachments are highly relevant
                    recency_score=1.0,    # Current message attachments
                    importance_score=0.7,
                    combined_score=0.0,
                    metadata={
                        "file_count": attachments.get("total_files", 0),
                        "has_extracted_content": bool(attachments.get("extracted_content")),
                        "has_multimedia": bool(attachments.get("multimedia_analysis"))
                    }
                )
                items.append(item)
        
        return items
    
    def _format_entities(self, entities: List[Any]) -> str:
        """Format entities for context inclusion."""
        if not entities:
            return ""
        
        formatted_entities = []
        for entity in entities:
            if isinstance(entity, dict):
                text = entity.get("text", "")
                label = entity.get("label", "UNKNOWN")
                if text:
                    formatted_entities.append(f"{label}: {text}")
            elif isinstance(entity, (list, tuple)) and len(entity) >= 2:
                formatted_entities.append(f"{entity[1]}: {entity[0]}")
        
        if formatted_entities:
            return f"Key entities: {', '.join(formatted_entities[:5])}"  # Limit to 5
        return ""
    
    def _format_relationships(self, relationships: List[Any]) -> str:
        """Format relationships for context inclusion."""
        if not relationships:
            return ""
        
        formatted_rels = []
        for rel in relationships[:3]:  # Limit to 3 most important
            if isinstance(rel, dict):
                formatted_rels.append(rel.get("description", str(rel)))
            else:
                formatted_rels.append(str(rel))
        
        if formatted_rels:
            return f"Related concepts: {'; '.join(formatted_rels)}"
        return ""
    
    def _format_attachments(self, attachments: Dict[str, Any]) -> str:
        """Format attachment information for context inclusion."""
        parts = []
        
        file_count = attachments.get("total_files", 0)
        if file_count > 0:
            parts.append(f"{file_count} file(s) attached")
        
        extracted_content = attachments.get("extracted_content", [])
        if extracted_content:
            content_preview = []
            for content in extracted_content[:2]:  # Limit to 2 files
                if isinstance(content, dict):
                    text = content.get("content", "")[:200]  # Limit content length
                    if text:
                        content_preview.append(f"File content: {text}...")
            
            if content_preview:
                parts.extend(content_preview)
        
        multimedia_analysis = attachments.get("multimedia_analysis", [])
        if multimedia_analysis:
            media_types = []
            for analysis in multimedia_analysis:
                if isinstance(analysis, dict):
                    media_type = analysis.get("media_type", "unknown")
                    media_types.append(media_type)
            
            if media_types:
                parts.append(f"Media files: {', '.join(set(media_types))}")
        
        return "; ".join(parts) if parts else ""
    
    async def _score_context_items(
        self,
        items: List[ContextItem],
        current_message: str
    ) -> List[ContextItem]:
        """Score context items for relevance and importance."""
        current_time = datetime.utcnow()
        message_lower = current_message.lower()
        
        for item in items:
            # Calculate recency score based on creation time
            if item.created_at:
                time_diff = current_time - item.created_at
                hours_old = time_diff.total_seconds() / 3600
                # Exponential decay: score decreases as content gets older
                item.recency_score = max(0.1, 1.0 * (0.9 ** (hours_old / 24)))
            
            # Enhance relevance score based on content similarity to current message
            content_lower = item.content.lower()
            
            # Simple keyword matching boost
            message_words = set(message_lower.split())
            content_words = set(content_lower.split())
            common_words = message_words.intersection(content_words)
            
            if common_words:
                keyword_boost = min(0.3, len(common_words) * 0.05)
                item.relevance_score = min(1.0, item.relevance_score + keyword_boost)
            
            # Type-specific scoring adjustments
            if item.type == ContextType.ENTITIES:
                # Entities are more relevant if they appear in current message
                if any(word in message_lower for word in content_lower.split()):
                    item.relevance_score = min(1.0, item.relevance_score + 0.2)
            
            elif item.type == ContextType.ATTACHMENTS:
                # Attachments are highly relevant for current message
                item.relevance_score = min(1.0, item.relevance_score + 0.1)
            
            elif item.type == ContextType.USER_PREFERENCES:
                # Preferences are moderately relevant but persistent
                item.importance_score = min(1.0, item.importance_score + 0.1)
            
            # Calculate combined score
            item.combined_score = (
                self.relevance_weight * item.relevance_score +
                self.recency_weight * item.recency_score +
                self.importance_weight * item.importance_score
            )
            
            # Ensure combined score is within bounds
            item.combined_score = max(0.0, min(1.0, item.combined_score))
        
        return items
    
    async def _build_integrated_context(
        self,
        relevant_items: List[ContextItem],
        all_items: List[ContextItem],
        current_message: str,
        user_id: str,
        conversation_id: str
    ) -> IntegratedContext:
        """Build integrated context within token limits."""
        included_items = []
        excluded_items = []
        current_tokens = 0
        
        # Reserve tokens for primary context structure
        reserved_tokens = 200
        available_tokens = self.max_context_tokens - reserved_tokens
        
        # Prioritize items by combined score and type importance
        prioritized_items = self._prioritize_items(relevant_items)
        
        # Include items within token limit
        for item in prioritized_items:
            item_tokens = self._estimate_tokens(item.content)
            
            if current_tokens + item_tokens <= available_tokens:
                included_items.append(item)
                current_tokens += item_tokens
            else:
                excluded_items.append(item)
        
        # Add remaining items to excluded
        excluded_items.extend([item for item in all_items if item not in included_items and item not in excluded_items])
        
        # Build context strings
        primary_context = self._build_primary_context(included_items)
        supporting_context = self._build_supporting_context(included_items)
        context_summary = self._build_context_summary(included_items, excluded_items)
        
        # Calculate final token count
        total_tokens = (
            self._estimate_tokens(primary_context) +
            self._estimate_tokens(supporting_context) +
            self._estimate_tokens(context_summary)
        )
        
        return IntegratedContext(
            primary_context=primary_context,
            supporting_context=supporting_context,
            context_summary=context_summary,
            token_count=total_tokens,
            items_included=included_items,
            items_excluded=excluded_items,
            relevance_threshold=self.relevance_threshold,
            metadata={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "current_message_length": len(current_message),
                "integration_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _prioritize_items(self, items: List[ContextItem]) -> List[ContextItem]:
        """Prioritize context items for inclusion."""
        # Define type priority order
        type_priority = {
            ContextType.ATTACHMENTS: 1,      # Highest priority
            ContextType.ENTITIES: 2,
            ContextType.INSTRUCTIONS: 3,
            ContextType.MEMORY: 4,
            ContextType.USER_PREFERENCES: 5,
            ContextType.FACTS: 6,
            ContextType.RELATIONSHIPS: 7,
            ContextType.CONVERSATION_HISTORY: 8  # Lowest priority
        }
        
        # Sort by type priority first, then by combined score
        return sorted(
            items,
            key=lambda x: (type_priority.get(x.type, 9), -x.combined_score)
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        if not text:
            return 0
        # Rough approximation: 1 token per 4 characters
        return max(1, len(text) // 4)
    
    def _build_primary_context(self, items: List[ContextItem]) -> str:
        """Build primary context string from high-priority items."""
        primary_items = [
            item for item in items
            if item.get_relevance_category() in [RelevanceScore.VERY_HIGH, RelevanceScore.HIGH]
        ]
        
        if not primary_items:
            return ""
        
        context_parts = []
        
        # Group by type for better organization
        by_type = {}
        for item in primary_items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
        
        # Add attachments first
        if ContextType.ATTACHMENTS in by_type:
            context_parts.append("CURRENT FILES:")
            for item in by_type[ContextType.ATTACHMENTS]:
                context_parts.append(f"- {item.content}")
        
        # Add entities
        if ContextType.ENTITIES in by_type:
            context_parts.append("KEY ENTITIES:")
            for item in by_type[ContextType.ENTITIES]:
                context_parts.append(f"- {item.content}")
        
        # Add high-relevance memories
        memories = by_type.get(ContextType.MEMORY, [])
        high_relevance_memories = [m for m in memories if m.combined_score >= 0.7]
        if high_relevance_memories:
            context_parts.append("RELEVANT CONTEXT:")
            for memory in high_relevance_memories[:3]:  # Limit to top 3
                context_parts.append(f"- {memory.content}")
        
        return "\n".join(context_parts)
    
    def _build_supporting_context(self, items: List[ContextItem]) -> str:
        """Build supporting context from medium-priority items."""
        supporting_items = [
            item for item in items
            if item.get_relevance_category() == RelevanceScore.MEDIUM
        ]
        
        if not supporting_items:
            return ""
        
        context_parts = []
        
        # Add preferences
        preferences = [item for item in supporting_items if item.type == ContextType.USER_PREFERENCES]
        if preferences:
            context_parts.append("USER PREFERENCES:")
            for pref in preferences[:2]:  # Limit to top 2
                context_parts.append(f"- {pref.content}")
        
        # Add facts
        facts = [item for item in supporting_items if item.type == ContextType.FACTS]
        if facts:
            context_parts.append("RELEVANT FACTS:")
            for fact in facts[:3]:  # Limit to top 3
                context_parts.append(f"- {fact.content}")
        
        # Add relationships
        relationships = [item for item in supporting_items if item.type == ContextType.RELATIONSHIPS]
        if relationships:
            for rel in relationships:
                context_parts.append(f"CONTEXT: {rel.content}")
        
        return "\n".join(context_parts)
    
    def _build_context_summary(
        self,
        included_items: List[ContextItem],
        excluded_items: List[ContextItem]
    ) -> str:
        """Build a summary of the context integration."""
        summary_parts = []
        
        if included_items:
            by_type = {}
            for item in included_items:
                if item.type not in by_type:
                    by_type[item.type] = 0
                by_type[item.type] += 1
            
            type_summary = []
            for context_type, count in by_type.items():
                type_summary.append(f"{count} {context_type.value}")
            
            summary_parts.append(f"Context includes: {', '.join(type_summary)}")
        
        if excluded_items:
            high_relevance_excluded = [
                item for item in excluded_items
                if item.combined_score >= 0.5
            ]
            if high_relevance_excluded:
                summary_parts.append(
                    f"Additional relevant context available ({len(high_relevance_excluded)} items)"
                )
        
        return "; ".join(summary_parts) if summary_parts else "No additional context"
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about context integration."""
        return {
            "max_context_tokens": self.max_context_tokens,
            "relevance_threshold": self.relevance_threshold,
            "scoring_weights": {
                "recency": self.recency_weight,
                "relevance": self.relevance_weight,
                "importance": self.importance_weight
            }
        }