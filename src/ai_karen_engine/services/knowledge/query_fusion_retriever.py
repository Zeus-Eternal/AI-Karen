"""
Query Fusion Retriever

Advanced retrieval system that combines multiple search strategies for
comprehensive knowledge retrieval with citation tracking and confidence scoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import math

try:
    from llama_index.core import VectorStoreIndex
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import NodeWithScore
except ImportError:
    VectorStoreIndex = None
    BaseRetriever = None
    NodeWithScore = None

from .index_hub import KnowledgeQuery, KnowledgeResult, Citation


@dataclass
class RetrievalStrategy:
    """Configuration for a retrieval strategy."""
    name: str
    weight: float
    similarity_top_k: int
    min_score_threshold: float


class QueryFusionRetriever:
    """
    Advanced retriever that fuses results from multiple search strategies
    to provide comprehensive and accurate knowledge retrieval.
    """
    
    def __init__(self, indices: Dict[str, VectorStoreIndex]):
        self.indices = indices
        self.logger = logging.getLogger(__name__)
        
        # Define retrieval strategies
        self.strategies = [
            RetrievalStrategy(
                name="semantic_similarity",
                weight=0.4,
                similarity_top_k=15,
                min_score_threshold=0.3
            ),
            RetrievalStrategy(
                name="keyword_matching", 
                weight=0.3,
                similarity_top_k=10,
                min_score_threshold=0.4
            ),
            RetrievalStrategy(
                name="contextual_relevance",
                weight=0.3,
                similarity_top_k=8,
                min_score_threshold=0.5
            )
        ]
    
    async def retrieve(self, query: KnowledgeQuery) -> List[KnowledgeResult]:
        """
        Perform fusion retrieval across multiple strategies and indices.
        """
        if not self.indices:
            return []
        
        # Get target indices based on query context
        target_indices = self._filter_indices_by_context(query)
        
        if not target_indices:
            self.logger.warning("No indices match query context")
            return []
        
        # Collect results from all strategies and indices
        all_results = []
        
        for index_key, index in target_indices.items():
            for strategy in self.strategies:
                try:
                    strategy_results = await self._retrieve_with_strategy(
                        query, index, index_key, strategy
                    )
                    all_results.extend(strategy_results)
                
                except Exception as e:
                    self.logger.error(f"Error in strategy {strategy.name} for index {index_key}: {e}")
        
        # Fuse and rank results
        fused_results = await self._fuse_results(all_results, query)
        
        # Apply final filtering and ranking
        filtered_results = self._filter_and_rank_results(fused_results, query)
        
        return filtered_results[:query.max_results]
    
    def _filter_indices_by_context(self, query: KnowledgeQuery) -> Dict[str, VectorStoreIndex]:
        """Filter indices based on department/team context."""
        if not query.department and not query.team:
            return self.indices
        
        filtered = {}
        for key, index in self.indices.items():
            # Parse index key format: "department_team" or "department"
            parts = key.split('_')
            index_dept = parts[0] if parts else None
            index_team = parts[1] if len(parts) > 1 else None
            
            # Check if index matches query context
            if query.department and index_dept != query.department.value:
                continue
            if query.team and index_team != query.team.value:
                continue
            
            filtered[key] = index
        
        return filtered
    
    async def _retrieve_with_strategy(
        self, 
        query: KnowledgeQuery, 
        index: VectorStoreIndex, 
        index_key: str, 
        strategy: RetrievalStrategy
    ) -> List[Tuple[KnowledgeResult, str, float]]:
        """Retrieve results using a specific strategy."""
        results = []
        
        try:
            if strategy.name == "semantic_similarity":
                results = await self._semantic_similarity_retrieval(
                    query, index, index_key, strategy
                )
            elif strategy.name == "keyword_matching":
                results = await self._keyword_matching_retrieval(
                    query, index, index_key, strategy
                )
            elif strategy.name == "contextual_relevance":
                results = await self._contextual_relevance_retrieval(
                    query, index, index_key, strategy
                )
        
        except Exception as e:
            self.logger.error(f"Error in {strategy.name} retrieval: {e}")
        
        return results
    
    async def _semantic_similarity_retrieval(
        self, 
        query: KnowledgeQuery, 
        index: VectorStoreIndex, 
        index_key: str, 
        strategy: RetrievalStrategy
    ) -> List[Tuple[KnowledgeResult, str, float]]:
        """Perform semantic similarity-based retrieval."""
        if not index:
            return []
        
        try:
            # Use LlamaIndex's built-in retriever
            retriever = index.as_retriever(similarity_top_k=strategy.similarity_top_k)
            nodes = await asyncio.to_thread(retriever.retrieve, query.text)
            
            results = []
            for node in nodes:
                if hasattr(node, 'score') and node.score >= strategy.min_score_threshold:
                    result = self._node_to_knowledge_result(node, index_key)
                    if result:
                        # Apply strategy weight to score
                        weighted_score = node.score * strategy.weight
                        results.append((result, strategy.name, weighted_score))
            
            return results
        
        except Exception as e:
            self.logger.error(f"Semantic similarity retrieval error: {e}")
            return []
    
    async def _keyword_matching_retrieval(
        self, 
        query: KnowledgeQuery, 
        index: VectorStoreIndex, 
        index_key: str, 
        strategy: RetrievalStrategy
    ) -> List[Tuple[KnowledgeResult, str, float]]:
        """Perform keyword-based retrieval with TF-IDF scoring."""
        if not index:
            return []
        
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query.text)
            
            # Use retriever with keyword-enhanced query
            keyword_query = " ".join(keywords)
            retriever = index.as_retriever(similarity_top_k=strategy.similarity_top_k)
            nodes = await asyncio.to_thread(retriever.retrieve, keyword_query)
            
            results = []
            for node in nodes:
                # Calculate keyword matching score
                keyword_score = self._calculate_keyword_score(node.node.text, keywords)
                
                if keyword_score >= strategy.min_score_threshold:
                    result = self._node_to_knowledge_result(node, index_key)
                    if result:
                        # Apply strategy weight
                        weighted_score = keyword_score * strategy.weight
                        results.append((result, strategy.name, weighted_score))
            
            return results
        
        except Exception as e:
            self.logger.error(f"Keyword matching retrieval error: {e}")
            return []
    
    async def _contextual_relevance_retrieval(
        self, 
        query: KnowledgeQuery, 
        index: VectorStoreIndex, 
        index_key: str, 
        strategy: RetrievalStrategy
    ) -> List[Tuple[KnowledgeResult, str, float]]:
        """Perform context-aware retrieval considering source types and metadata."""
        if not index:
            return []
        
        try:
            # Create context-enhanced query
            context_query = self._enhance_query_with_context(query)
            
            retriever = index.as_retriever(similarity_top_k=strategy.similarity_top_k)
            nodes = await asyncio.to_thread(retriever.retrieve, context_query)
            
            results = []
            for node in nodes:
                # Calculate contextual relevance score
                context_score = self._calculate_contextual_score(node, query)
                
                if context_score >= strategy.min_score_threshold:
                    result = self._node_to_knowledge_result(node, index_key)
                    if result:
                        # Apply strategy weight
                        weighted_score = context_score * strategy.weight
                        results.append((result, strategy.name, weighted_score))
            
            return results
        
        except Exception as e:
            self.logger.error(f"Contextual relevance retrieval error: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from query text."""
        # Simple keyword extraction (can be enhanced with NLP)
        import re
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]{2,}\b', text.lower())
        
        # Filter out stop words and return unique keywords
        keywords = [word for word in words if word not in stop_words]
        return list(set(keywords))
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword matching score using TF-IDF-like approach."""
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        text_words = text_lower.split()
        
        # Calculate term frequency for each keyword
        keyword_scores = []
        for keyword in keywords:
            tf = text_lower.count(keyword) / len(text_words) if text_words else 0
            # Simple IDF approximation (can be enhanced with corpus statistics)
            idf = math.log(1 + 1 / (1 + tf)) if tf > 0 else 0
            keyword_scores.append(tf * idf)
        
        # Return average keyword score
        return sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0.0
    
    def _enhance_query_with_context(self, query: KnowledgeQuery) -> str:
        """Enhance query with contextual information."""
        enhanced = query.text
        
        # Add department context
        if query.department:
            enhanced += f" {query.department.value}"
        
        # Add team context
        if query.team:
            enhanced += f" {query.team.value}"
        
        # Add source type context
        if query.source_types:
            enhanced += f" {' '.join(query.source_types)}"
        
        return enhanced
    
    def _calculate_contextual_score(self, node: NodeWithScore, query: KnowledgeQuery) -> float:
        """Calculate contextual relevance score based on metadata and query context."""
        base_score = getattr(node, 'score', 0.0)
        
        if not hasattr(node.node, 'metadata'):
            return base_score
        
        metadata = node.node.metadata
        context_boost = 0.0
        
        # Boost for matching source types
        if query.source_types:
            source_type = metadata.get('source_type', '')
            if source_type in query.source_types:
                context_boost += 0.2
        
        # Boost for matching department/team
        if query.department:
            if metadata.get('department') == query.department.value:
                context_boost += 0.15
        
        if query.team:
            if metadata.get('team') == query.team.value:
                context_boost += 0.15
        
        # Boost for recent content
        if 'last_modified' in metadata:
            # Simple recency boost (can be enhanced)
            context_boost += 0.1
        
        return min(base_score + context_boost, 1.0)
    
    def _node_to_knowledge_result(self, node: NodeWithScore, index_key: str) -> Optional[KnowledgeResult]:
        """Convert LlamaIndex node to KnowledgeResult with citations."""
        try:
            # Extract citation information from node metadata
            metadata = getattr(node.node, 'metadata', {})
            
            citation = Citation(
                source_id=metadata.get('source_id', index_key),
                file_path=metadata.get('file_path'),
                line_start=metadata.get('line_start'),
                line_end=metadata.get('line_end'),
                table_name=metadata.get('table_name'),
                column_name=metadata.get('column_name'),
                confidence_score=getattr(node, 'score', 0.0),
                context_snippet=node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text
            )
            
            return KnowledgeResult(
                content=node.node.text,
                citations=[citation],
                confidence_score=getattr(node, 'score', 0.0),
                source_metadata=metadata,
                conceptual_relationships=metadata.get('relationships', [])
            )
        
        except Exception as e:
            self.logger.error(f"Error converting node to result: {e}")
            return None
    
    async def _fuse_results(
        self, 
        all_results: List[Tuple[KnowledgeResult, str, float]], 
        query: KnowledgeQuery
    ) -> List[KnowledgeResult]:
        """Fuse results from multiple strategies using score combination."""
        if not all_results:
            return []
        
        # Group results by content similarity (simple deduplication)
        content_groups = defaultdict(list)
        
        for result, strategy, score in all_results:
            # Use first 100 characters as grouping key (simple approach)
            content_key = result.content[:100].strip()
            content_groups[content_key].append((result, strategy, score))
        
        # Fuse grouped results
        fused_results = []
        
        for content_key, group in content_groups.items():
            if len(group) == 1:
                # Single result, use as-is
                result, strategy, score = group[0]
                result.confidence_score = score
                fused_results.append(result)
            else:
                # Multiple results, fuse them
                fused_result = await self._fuse_result_group(group, query)
                if fused_result:
                    fused_results.append(fused_result)
        
        return fused_results
    
    async def _fuse_result_group(
        self, 
        group: List[Tuple[KnowledgeResult, str, float]], 
        query: KnowledgeQuery
    ) -> Optional[KnowledgeResult]:
        """Fuse a group of similar results into a single result."""
        if not group:
            return None
        
        # Use the result with highest score as base
        base_result, _, _ = max(group, key=lambda x: x[2])
        
        # Combine scores using weighted average
        total_weight = sum(score for _, _, score in group)
        fused_score = total_weight / len(group)
        
        # Combine citations from all results
        all_citations = []
        all_relationships = set()
        
        for result, strategy, score in group:
            all_citations.extend(result.citations)
            all_relationships.update(result.conceptual_relationships)
        
        # Remove duplicate citations
        unique_citations = []
        seen_citations = set()
        
        for citation in all_citations:
            citation_key = (citation.source_id, citation.file_path, citation.line_start)
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                unique_citations.append(citation)
        
        return KnowledgeResult(
            content=base_result.content,
            citations=unique_citations,
            confidence_score=min(fused_score, 1.0),
            source_metadata=base_result.source_metadata,
            conceptual_relationships=list(all_relationships)
        )
    
    def _filter_and_rank_results(
        self, 
        results: List[KnowledgeResult], 
        query: KnowledgeQuery
    ) -> List[KnowledgeResult]:
        """Apply final filtering and ranking to results."""
        # Filter by minimum confidence
        filtered = [r for r in results if r.confidence_score >= query.min_confidence]
        
        # Filter by citation requirement
        if query.require_citations:
            filtered = [r for r in filtered if r.citations]
        
        # Sort by confidence score (descending)
        filtered.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return filtered