"""
Advanced conversation search service with full-text and semantic search capabilities.
Supports hybrid search combining text matching and semantic similarity.
"""

import asyncio
import logging
import re
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta

from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import TenantConversation
from ai_karen_engine.chat.conversation_models import (
    Conversation, ChatMessage, ConversationFilters, ConversationSearchResult,
    MessageRole, MessageType, ConversationStatus
)

logger = logging.getLogger(__name__)


class ConversationSearchService:
    """Advanced search service for conversations with multiple search strategies."""
    
    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        distilbert_service=None,
        milvus_client=None
    ):
        """Initialize search service."""
        self.db_client = db_client
        self.distilbert_service = distilbert_service
        self.milvus_client = milvus_client
        
        # Search configuration
        self.max_results = 100
        self.min_similarity_score = 0.6
        self.text_search_weight = 0.4
        self.semantic_search_weight = 0.6
        
        # Performance tracking
        self.search_metrics = {
            "total_searches": 0,
            "text_searches": 0,
            "semantic_searches": 0,
            "hybrid_searches": 0,
            "avg_search_time": 0.0
        }
    
    async def hybrid_search(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        text_query: str,
        embedding_query: Optional[List[float]] = None,
        filters: Optional[ConversationFilters] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ConversationSearchResult]:
        """
        Perform hybrid search combining full-text and semantic search.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            text_query: Text query for full-text search
            embedding_query: Query embedding for semantic search
            filters: Additional filters to apply
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of search results with relevance scores
        """
        start_time = datetime.utcnow()
        
        try:
            # Perform text search
            text_results = await self._full_text_search(
                tenant_id, user_id, text_query, filters, limit * 2
            )
            
            # Perform semantic search if embedding is available
            semantic_results = []
            if embedding_query and self.milvus_client:
                semantic_results = await self._semantic_search(
                    tenant_id, user_id, embedding_query, filters, limit * 2
                )
            
            # Combine and rank results
            combined_results = await self._combine_search_results(
                text_results, semantic_results, text_query
            )
            
            # Apply final filtering and pagination
            filtered_results = self._apply_final_filters(
                combined_results, filters, limit, offset
            )
            
            # Update metrics
            self.search_metrics["total_searches"] += 1
            if semantic_results:
                self.search_metrics["hybrid_searches"] += 1
            else:
                self.search_metrics["text_searches"] += 1
            
            search_time = (datetime.utcnow() - start_time).total_seconds()
            self.search_metrics["avg_search_time"] = (
                self.search_metrics["avg_search_time"] * 0.9 + search_time * 0.1
            )
            
            logger.info(f"Hybrid search completed: {len(filtered_results)} results in {search_time:.3f}s")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    async def _full_text_search(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        query: str,
        filters: Optional[ConversationFilters] = None,
        limit: int = 50
    ) -> List[Tuple[Conversation, float, List[ChatMessage]]]:
        """
        Perform full-text search across conversation titles and message content.
        
        Returns:
            List of tuples (conversation, relevance_score, matched_messages)
        """
        try:
            # Prepare search terms
            search_terms = self._prepare_search_terms(query)
            if not search_terms:
                return []
            
            results = []
            
            async with self.db_client.get_async_session() as session:
                # Search in conversation titles and messages
                query_obj = (
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                )
                
                # Apply basic filters
                if filters:
                    query_obj = self._apply_database_filters(query_obj, filters)
                
                result = await session.execute(query_obj)
                conversations = result.scalars().all()
                
                for db_conv in conversations:
                    relevance_score = 0.0
                    matched_messages = []
                    
                    # Search in conversation title
                    title_score = self._calculate_text_relevance(
                        db_conv.title or "", search_terms
                    )
                    relevance_score += title_score * 0.3  # Title weight
                    
                    # Search in messages
                    messages_data = db_conv.messages or []
                    for msg_data in messages_data:
                        try:
                            message = ChatMessage(**msg_data)
                            msg_score = self._calculate_text_relevance(
                                message.content, search_terms
                            )
                            
                            if msg_score > 0:
                                relevance_score += msg_score * 0.7  # Message weight
                                matched_messages.append(message)
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse message: {e}")
                            continue
                    
                    # Only include conversations with some relevance
                    if relevance_score > 0.1:
                        # Convert to conversation object
                        metadata = db_conv.conversation_metadata or {}
                        conversation = Conversation(
                            id=str(db_conv.id),
                            user_id=str(db_conv.user_id),
                            title=db_conv.title or "Untitled Conversation",
                            description=metadata.get("description"),
                            status=ConversationStatus(metadata.get("status", "active")),
                            folder_id=metadata.get("folder_id"),
                            tags=metadata.get("tags", []),
                            is_favorite=metadata.get("is_favorite", False),
                            priority=metadata.get("priority", 0),
                            message_count=len(messages_data),
                            created_at=db_conv.created_at,
                            updated_at=db_conv.updated_at,
                            metadata=metadata
                        )
                        
                        results.append((conversation, relevance_score, matched_messages))
                
                # Sort by relevance score
                results.sort(key=lambda x: x[1], reverse=True)
                
                return results[:limit]
                
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            return []
    
    async def _semantic_search(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        query_embedding: List[float],
        filters: Optional[ConversationFilters] = None,
        limit: int = 50
    ) -> List[Tuple[Conversation, float, List[ChatMessage]]]:
        """
        Perform semantic search using vector embeddings.
        
        Returns:
            List of tuples (conversation, similarity_score, matched_messages)
        """
        try:
            if not self.milvus_client:
                return []
            
            # Search for similar message embeddings
            collection_name = f"conversations_{user_id}"
            
            search_results = await self.milvus_client.search(
                collection=collection_name,
                query_embeddings=[query_embedding],
                top_k=limit,
                params={"metric_type": "IP", "params": {"nprobe": 10}}
            )
            
            if not search_results or not search_results[0]:
                return []
            
            # Get conversation details for matched embeddings
            results = []
            conversation_scores = {}  # conversation_id -> max_similarity
            
            for hit in search_results[0]:
                if hit.distance < self.min_similarity_score:
                    continue
                
                # Extract conversation_id and message_id from hit metadata
                conversation_id = hit.entity.get("conversation_id")
                message_id = hit.entity.get("message_id")
                
                if not conversation_id:
                    continue
                
                # Track best similarity score per conversation
                if conversation_id not in conversation_scores:
                    conversation_scores[conversation_id] = hit.distance
                else:
                    conversation_scores[conversation_id] = max(
                        conversation_scores[conversation_id], hit.distance
                    )
            
            # Fetch conversation details
            async with self.db_client.get_async_session() as session:
                for conv_id, similarity_score in conversation_scores.items():
                    try:
                        result = await session.execute(
                            select(TenantConversation)
                            .where(TenantConversation.id == uuid.UUID(conv_id))
                        )
                        
                        db_conv = result.scalar_one_or_none()
                        if not db_conv:
                            continue
                        
                        # Convert to conversation object
                        metadata = db_conv.conversation_metadata or {}
                        conversation = Conversation(
                            id=str(db_conv.id),
                            user_id=str(db_conv.user_id),
                            title=db_conv.title or "Untitled Conversation",
                            description=metadata.get("description"),
                            status=ConversationStatus(metadata.get("status", "active")),
                            folder_id=metadata.get("folder_id"),
                            tags=metadata.get("tags", []),
                            is_favorite=metadata.get("is_favorite", False),
                            priority=metadata.get("priority", 0),
                            message_count=len(db_conv.messages or []),
                            created_at=db_conv.created_at,
                            updated_at=db_conv.updated_at,
                            metadata=metadata
                        )
                        
                        # Find matched messages (simplified - would need better matching)
                        matched_messages = []
                        messages_data = db_conv.messages or []
                        for msg_data in messages_data[:5]:  # Limit to first few messages
                            try:
                                message = ChatMessage(**msg_data)
                                matched_messages.append(message)
                            except Exception:
                                continue
                        
                        results.append((conversation, similarity_score, matched_messages))
                        
                    except Exception as e:
                        logger.warning(f"Failed to fetch conversation {conv_id}: {e}")
                        continue
            
            # Sort by similarity score
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _combine_search_results(
        self,
        text_results: List[Tuple[Conversation, float, List[ChatMessage]]],
        semantic_results: List[Tuple[Conversation, float, List[ChatMessage]]],
        original_query: str
    ) -> List[ConversationSearchResult]:
        """
        Combine and rank results from text and semantic search.
        
        Args:
            text_results: Results from full-text search
            semantic_results: Results from semantic search
            original_query: Original search query
            
        Returns:
            Combined and ranked search results
        """
        combined = {}  # conversation_id -> ConversationSearchResult
        
        # Process text search results
        for conversation, text_score, matched_messages in text_results:
            search_result = ConversationSearchResult(
                conversation=conversation,
                relevance_score=text_score * self.text_search_weight,
                matched_messages=matched_messages,
                highlight_snippets=self._generate_highlights(
                    matched_messages, original_query
                ),
                search_metadata={
                    "text_score": text_score,
                    "semantic_score": 0.0,
                    "search_type": "text"
                }
            )
            combined[conversation.id] = search_result
        
        # Process semantic search results
        for conversation, semantic_score, matched_messages in semantic_results:
            if conversation.id in combined:
                # Update existing result
                existing = combined[conversation.id]
                existing.relevance_score += semantic_score * self.semantic_search_weight
                existing.search_metadata["semantic_score"] = semantic_score
                existing.search_metadata["search_type"] = "hybrid"
                
                # Merge matched messages (avoid duplicates)
                existing_msg_ids = {msg.id for msg in existing.matched_messages}
                for msg in matched_messages:
                    if msg.id not in existing_msg_ids:
                        existing.matched_messages.append(msg)
            else:
                # Create new result
                search_result = ConversationSearchResult(
                    conversation=conversation,
                    relevance_score=semantic_score * self.semantic_search_weight,
                    matched_messages=matched_messages,
                    highlight_snippets=self._generate_highlights(
                        matched_messages, original_query
                    ),
                    search_metadata={
                        "text_score": 0.0,
                        "semantic_score": semantic_score,
                        "search_type": "semantic"
                    }
                )
                combined[conversation.id] = search_result
        
        # Convert to list and sort by relevance
        results = list(combined.values())
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results
    
    def _prepare_search_terms(self, query: str) -> List[str]:
        """Prepare search terms from query string."""
        # Remove special characters and split into terms
        cleaned_query = re.sub(r'[^\w\s]', ' ', query.lower())
        terms = [term.strip() for term in cleaned_query.split() if len(term.strip()) > 2]
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        return [term for term in terms if term not in stop_words]
    
    def _calculate_text_relevance(self, text: str, search_terms: List[str]) -> float:
        """Calculate text relevance score based on term matching."""
        if not text or not search_terms:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        for term in search_terms:
            # Exact match
            if term in text_lower:
                score += 1.0
            
            # Partial match (fuzzy)
            elif any(term in word for word in text_lower.split()):
                score += 0.5
        
        # Normalize by number of terms
        return score / len(search_terms)
    
    def _apply_database_filters(
        self,
        query,
        filters: ConversationFilters
    ):
        """Apply database-level filters to the query."""
        if filters.date_from:
            query = query.where(TenantConversation.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.where(TenantConversation.created_at <= filters.date_to)
        
        if filters.status:
            # Would need JSON query for metadata filtering
            pass
        
        return query
    
    def _apply_final_filters(
        self,
        results: List[ConversationSearchResult],
        filters: Optional[ConversationFilters],
        limit: int,
        offset: int
    ) -> List[ConversationSearchResult]:
        """Apply final filters and pagination to search results."""
        if not filters:
            return results[offset:offset + limit]
        
        filtered_results = []
        
        for result in results:
            conversation = result.conversation
            
            # Apply filters
            if filters.folder_ids and conversation.folder_id not in filters.folder_ids:
                continue
            
            if filters.tags:
                if not any(tag in conversation.tags for tag in filters.tags):
                    continue
            
            if filters.is_favorite is not None and conversation.is_favorite != filters.is_favorite:
                continue
            
            if filters.status and conversation.status != filters.status:
                continue
            
            if filters.min_messages and conversation.message_count < filters.min_messages:
                continue
            
            if filters.max_messages and conversation.message_count > filters.max_messages:
                continue
            
            if filters.has_attachments is not None:
                has_attachments = any(
                    msg.attachments for msg in result.matched_messages
                )
                if has_attachments != filters.has_attachments:
                    continue
            
            filtered_results.append(result)
        
        return filtered_results[offset:offset + limit]
    
    def _generate_highlights(
        self,
        messages: List[ChatMessage],
        query: str
    ) -> List[str]:
        """Generate highlight snippets from matched messages."""
        highlights = []
        search_terms = self._prepare_search_terms(query)
        
        for message in messages[:3]:  # Limit to first 3 messages
            content = message.content
            
            # Find best snippet containing search terms
            snippet = self._extract_snippet(content, search_terms)
            if snippet:
                highlights.append(snippet)
        
        return highlights
    
    def _extract_snippet(self, text: str, search_terms: List[str], max_length: int = 150) -> str:
        """Extract a snippet containing search terms."""
        if not text or not search_terms:
            return ""
        
        text_lower = text.lower()
        
        # Find the first occurrence of any search term
        best_pos = len(text)
        for term in search_terms:
            pos = text_lower.find(term)
            if pos != -1 and pos < best_pos:
                best_pos = pos
        
        if best_pos == len(text):
            # No terms found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Extract snippet around the found term
        start = max(0, best_pos - max_length // 3)
        end = min(len(text), start + max_length)
        
        snippet = text[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    async def get_search_suggestions(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = []
            
            # Get common tags and titles for suggestions
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(TenantConversation)
                    .where(TenantConversation.user_id == uuid.UUID(user_id))
                    .limit(100)  # Limit for performance
                )
                
                conversations = result.scalars().all()
                
                # Collect titles and tags
                titles = []
                tags = set()
                
                for conv in conversations:
                    if conv.title:
                        titles.append(conv.title)
                    
                    metadata = conv.conversation_metadata or {}
                    conv_tags = metadata.get("tags", [])
                    tags.update(conv_tags)
                
                # Find matching suggestions
                partial_lower = partial_query.lower()
                
                # Match titles
                for title in titles:
                    if partial_lower in title.lower():
                        suggestions.append(title)
                
                # Match tags
                for tag in tags:
                    if partial_lower in tag.lower():
                        suggestions.append(f"tag:{tag}")
                
                # Sort by relevance and limit
                suggestions = sorted(set(suggestions))[:limit]
                
                return suggestions
                
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    def get_search_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics."""
        return self.search_metrics.copy()