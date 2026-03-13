"""
Context Relevance Scoring and Ranking

Implements sophisticated relevance scoring algorithms for context search results,
combining semantic similarity, recency, importance, and usage patterns.
"""

import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_karen_engine.context_management.models import ContextEntry, ContextQuery, ContextType


class ContextRelevanceScorer:
    """
    Advanced relevance scoring system for context search results.
    
    Combines multiple factors:
    - Semantic similarity (from embeddings)
    - Content relevance (text matching)
    - Recency (time decay)
    - Importance score
    - Usage patterns (access count)
    - Type-specific weighting
    """

    def __init__(
        self,
        semantic_weight: float = 0.4,
        content_weight: float = 0.3,
        recency_weight: float = 0.15,
        importance_weight: float = 0.1,
        usage_weight: float = 0.05,
        recency_half_life_days: float = 30.0,
    ):
        """
        Initialize relevance scorer with configurable weights.
        
        Args:
            semantic_weight: Weight for semantic similarity
            content_weight: Weight for content/text matching
            recency_weight: Weight for recency (time decay)
            importance_weight: Weight for importance score
            usage_weight: Weight for usage patterns
            recency_half_life_days: Half-life for recency decay
        """
        self.semantic_weight = semantic_weight
        self.content_weight = content_weight
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight
        self.usage_weight = usage_weight
        self.recency_half_life_days = recency_half_life_days
        
        # Type-specific weights
        self.type_weights = {
            ContextType.CONVERSATION: 1.0,
            ContextType.DOCUMENT: 1.2,
            ContextType.CODE: 1.1,
            ContextType.IMAGE: 0.8,
            ContextType.AUDIO: 0.7,
            ContextType.VIDEO: 0.7,
            ContextType.WEB_PAGE: 0.9,
            ContextType.NOTE: 1.0,
            ContextType.TASK: 1.1,
            ContextType.MEMORY: 1.0,
            ContextType.CUSTOM: 1.0,
        }

    async def calculate_relevance(
        self,
        context: ContextEntry,
        query: ContextQuery,
        similarity_score: float = 0.0,
    ) -> float:
        """
        Calculate comprehensive relevance score for a context.
        
        Args:
            context: Context entry to score
            query: Search query
            similarity_score: Semantic similarity score (0-1)
            
        Returns:
            Relevance score (0-1, higher is more relevant)
        """
        try:
            # Calculate individual components
            semantic_score = self._calculate_semantic_score(similarity_score)
            content_score = await self._calculate_content_score(context, query)
            recency_score = self._calculate_recency_score(context)
            importance_score = self._calculate_importance_score(context)
            usage_score = self._calculate_usage_score(context)
            type_score = self._calculate_type_score(context)
            
            # Combine scores with weights
            total_score = (
                semantic_score * self.semantic_weight +
                content_score * self.content_weight +
                recency_score * self.recency_weight +
                importance_score * self.importance_weight +
                usage_score * self.usage_weight
            ) * type_score
            
            # Ensure score is in valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            # Return default score on error
            return similarity_score * 0.5

    def _calculate_semantic_score(self, similarity_score: float) -> float:
        """Calculate semantic similarity score."""
        # Normalize similarity score to 0-1 range
        return max(0.0, min(1.0, similarity_score))

    async def _calculate_content_score(self, context: ContextEntry, query: ContextQuery) -> float:
        """Calculate content/text matching score."""
        if not query.query_text:
            return 0.0
        
        query_lower = query.query_text.lower()
        content_lower = context.content.lower()
        title_lower = context.title.lower()
        
        # Exact phrase matching
        exact_content = query_lower in content_lower
        exact_title = query_lower in title_lower
        
        # Word-level matching
        query_words = query_lower.split()
        content_words = content_lower.split()
        title_words = title_lower.split()
        
        # Calculate word overlap
        content_matches = sum(1 for word in query_words if word in content_words)
        title_matches = sum(1 for word in query_words if word in title_words)
        
        # Calculate scores
        content_score = content_matches / len(query_words) if query_words else 0.0
        title_score = title_matches / len(query_words) if query_words else 0.0
        
        # Title matches are weighted higher
        title_bonus = 1.5 if exact_title else 1.0
        content_bonus = 1.2 if exact_content else 1.0
        
        # Combine scores
        combined_score = (title_score * 2.0 + content_score) / 3.0
        return min(1.0, combined_score * title_bonus * content_bonus)

    def _calculate_recency_score(self, context: ContextEntry) -> float:
        """Calculate recency score using exponential decay."""
        now = datetime.utcnow()
        age_days = (now - context.created_at).total_seconds() / 86400.0
        
        # Exponential decay based on half-life
        decay_factor = math.exp(-age_days * math.log(2) / self.recency_half_life_days)
        
        # Boost for recently accessed contexts
        if context.last_accessed:
            access_age_days = (now - context.last_accessed).total_seconds() / 86400.0
            access_boost = math.exp(-access_age_days * math.log(2) / (self.recency_half_life_days / 4))
            decay_factor = max(decay_factor, access_boost)
        
        return max(0.0, min(1.0, decay_factor))

    def _calculate_importance_score(self, context: ContextEntry) -> float:
        """Calculate importance score."""
        # Normalize importance score (1-10) to 0-1
        normalized = (context.importance_score - 1.0) / 9.0
        return max(0.0, min(1.0, normalized))

    def _calculate_usage_score(self, context: ContextEntry) -> float:
        """Calculate usage pattern score."""
        # Logarithmic scaling for access count
        if context.access_count == 0:
            return 0.0
        
        # Use log to prevent excessive influence of very high counts
        log_access = math.log(context.access_count + 1)
        max_log = math.log(100)  # Cap at 100 accesses
        
        return min(1.0, log_access / max_log)

    def _calculate_type_score(self, context: ContextEntry) -> float:
        """Calculate type-specific weight."""
        return self.type_weights.get(context.context_type, 1.0)

    def calculate_match_highlights(
        self,
        context: ContextEntry,
        query: ContextQuery,
    ) -> List[str]:
        """
        Generate highlight snippets for search results.
        
        Args:
            context: Context entry
            query: Search query
            
        Returns:
            List of highlight strings
        """
        highlights = []
        
        if not query.query_text:
            return highlights
        
        query_lower = query.query_text.lower()
        content_lower = context.content.lower()
        
        # Find exact matches
        start_pos = content_lower.find(query_lower)
        if start_pos != -1:
            # Extract context around match
            start = max(0, start_pos - 50)
            end = min(len(context.content), start_pos + len(query.query_text) + 50)
            
            snippet = context.content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(context.content):
                snippet = snippet + "..."
            
            highlights.append(snippet)
        
        # Find individual word matches
        query_words = query_lower.split()
        for word in query_words:
            start_pos = content_lower.find(word)
            if start_pos != -1 and len(highlights) < 3:  # Limit highlights
                start = max(0, start_pos - 30)
                end = min(len(context.content), start_pos + len(word) + 30)
                
                snippet = context.content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(context.content):
                    snippet = snippet + "..."
                
                if snippet not in highlights:
                    highlights.append(snippet)
        
        return highlights[:3]  # Return max 3 highlights

    def calculate_explanation(
        self,
        context: ContextEntry,
        query: ContextQuery,
        similarity_score: float = 0.0,
        relevance_score: float = 0.0,
    ) -> str:
        """
        Generate explanation for relevance score.
        
        Args:
            context: Context entry
            query: Search query
            similarity_score: Semantic similarity score
            relevance_score: Final relevance score
            
        Returns:
            Explanation string
        """
        try:
            explanations = []
            
            # Semantic similarity explanation
            if similarity_score > 0.7:
                explanations.append("High semantic similarity")
            elif similarity_score > 0.4:
                explanations.append("Moderate semantic similarity")
            
            # Content matching explanation
            if query.query_text.lower() in context.content.lower():
                explanations.append("Contains exact query match")
            elif query.query_text.lower() in context.title.lower():
                explanations.append("Title matches query")
            
            # Recency explanation
            age_days = (datetime.utcnow() - context.created_at).total_seconds() / 86400.0
            if age_days < 1:
                explanations.append("Very recent")
            elif age_days < 7:
                explanations.append("Recent")
            
            # Importance explanation
            if context.importance_score > 7:
                explanations.append("High importance")
            
            # Usage explanation
            if context.access_count > 10:
                explanations.append("Frequently accessed")
            
            # Type explanation
            type_weight = self.type_weights.get(context.context_type, 1.0)
            if type_weight > 1.0:
                explanations.append(f"Preferred type ({context.context_type.value})")
            
            if not explanations:
                explanations.append("Basic relevance")
            
            return ", ".join(explanations)
            
        except Exception:
            return "Relevance calculated"

    def get_scorer_config(self) -> Dict[str, Any]:
        """Get current scorer configuration."""
        return {
            "semantic_weight": self.semantic_weight,
            "content_weight": self.content_weight,
            "recency_weight": self.recency_weight,
            "importance_weight": self.importance_weight,
            "usage_weight": self.usage_weight,
            "recency_half_life_days": self.recency_half_life_days,
            "type_weights": {k.value: v for k, v in self.type_weights.items()},
        }

    def update_config(
        self,
        semantic_weight: Optional[float] = None,
        content_weight: Optional[float] = None,
        recency_weight: Optional[float] = None,
        importance_weight: Optional[float] = None,
        usage_weight: Optional[float] = None,
        recency_half_life_days: Optional[float] = None,
    ) -> None:
        """Update scorer configuration."""
        if semantic_weight is not None:
            self.semantic_weight = semantic_weight
        if content_weight is not None:
            self.content_weight = content_weight
        if recency_weight is not None:
            self.recency_weight = recency_weight
        if importance_weight is not None:
            self.importance_weight = importance_weight
        if usage_weight is not None:
            self.usage_weight = usage_weight
        if recency_half_life_days is not None:
            self.recency_half_life_days = recency_half_life_days

    def validate_config(self) -> List[str]:
        """Validate scorer configuration and return any issues."""
        issues = []
        
        total_weight = (
            self.semantic_weight + self.content_weight + self.recency_weight +
            self.importance_weight + self.usage_weight
        )
        
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Weights sum to {total_weight:.3f}, should sum to 1.0")
        
        if self.semantic_weight < 0 or self.semantic_weight > 1:
            issues.append("Semantic weight must be between 0 and 1")
        
        if self.content_weight < 0 or self.content_weight > 1:
            issues.append("Content weight must be between 0 and 1")
        
        if self.recency_weight < 0 or self.recency_weight > 1:
            issues.append("Recency weight must be between 0 and 1")
        
        if self.importance_weight < 0 or self.importance_weight > 1:
            issues.append("Importance weight must be between 0 and 1")
        
        if self.usage_weight < 0 or self.usage_weight > 1:
            issues.append("Usage weight must be between 0 and 1")
        
        if self.recency_half_life_days <= 0:
            issues.append("Recency half-life must be positive")
        
        return issues