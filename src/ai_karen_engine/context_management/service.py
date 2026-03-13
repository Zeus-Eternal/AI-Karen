"""
Context Management Service

Main service for context persistence, retrieval, versioning, and sharing.
Integrates with existing database, memory, and file storage systems.
"""

import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ai_karen_engine.context_management.models import (
    ContextAccessLevel,
    ContextAccessLog,
    ContextEntry,
    ContextFileType,
    ContextFile,
    ContextQuery,
    ContextSearchResult,
    ContextShare,
    ContextStatus,
    ContextType,
    ContextVersion,
)
from ai_karen_engine.context_management.scoring import ContextRelevanceScorer
from ai_karen_engine.database.memory_manager import MemoryManager, MemoryQuery, MemoryItem
from ai_karen_engine.models.neuro_memory_types import NeuroMemoryType, NeuroMemoryEntry

logger = logging.getLogger(__name__)


class ContextManagementService:
    """
    Comprehensive context management service with storage, retrieval,
    versioning, sharing, and access control capabilities.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        storage_path: str = "/tmp/context_storage",
        max_file_size_mb: int = 100,
        supported_file_types: Optional[List[ContextFileType]] = None,
    ):
        """
        Initialize context management service.
        
        Args:
            memory_manager: Memory manager for vector storage and retrieval
            storage_path: Base path for file storage
            max_file_size_mb: Maximum file size in MB
            supported_file_types: List of supported file types
        """
        self.memory_manager = memory_manager
        self.storage_path = storage_path
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.supported_file_types = supported_file_types or list(ContextFileType)
        
        # Initialize relevance scorer
        self.relevance_scorer = ContextRelevanceScorer()
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        # In-memory storage for development (replace with database in production)
        self._contexts: Dict[str, ContextEntry] = {}
        self._files: Dict[str, ContextFile] = {}
        self._shares: Dict[str, ContextShare] = {}
        self._versions: Dict[str, List[ContextVersion]] = {}
        self._access_logs: List[ContextAccessLog] = []
        
        logger.info(f"ContextManagementService initialized with storage path: {storage_path}")

    # -------------------------------------------------------------------------
    # Context Storage and Retrieval
    # -------------------------------------------------------------------------

    async def create_context(
        self,
        user_id: str,
        title: str,
        content: str = "",
        context_type: ContextType = ContextType.CUSTOM,
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        access_level: ContextAccessLevel = ContextAccessLevel.PRIVATE,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance_score: float = 5.0,
        expires_in_days: Optional[int] = None,
    ) -> ContextEntry:
        """
        Create a new context entry.
        
        Args:
            user_id: User ID creating the context
            title: Context title
            content: Context content
            context_type: Type of context
            org_id: Organization ID
            session_id: Session ID
            conversation_id: Conversation ID
            access_level: Access level for the context
            metadata: Additional metadata
            tags: List of tags
            importance_score: Importance score (1-10)
            expires_in_days: Days until expiration (None for no expiration)
            
        Returns:
            Created context entry
        """
        start_time = time.time()
        
        try:
            # Create context entry
            context = ContextEntry(
                id=str(uuid.uuid4()),
                user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                conversation_id=conversation_id,
                title=title,
                content=content,
                context_type=context_type,
                access_level=access_level,
                importance_score=importance_score,
                metadata=metadata or {},
                tags=tags or [],
            )
            
            # Set expiration if provided
            if expires_in_days:
                context.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Generate embedding for content
            if content:
                try:
                    await self._ensure_embedding_manager()
                    embedding_raw = await self.memory_manager.embedding_manager.get_embedding(content)
                    context.embedding = np.array(embedding_raw)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for context {context.id}: {e}")
            
            # Store in memory system for vector search
            await self._store_context_in_memory(context)
            
            # Store locally
            self._contexts[context.id] = context
            
            # Log access
            await self._log_access(
                context_id=context.id,
                user_id=user_id,
                action="create",
                access_level=access_level,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            
            logger.info(f"Created context {context.id} for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create context for user {user_id}: {e}")
            raise

    async def get_context(
        self,
        context_id: str,
        user_id: str,
        include_content: bool = True,
        include_files: bool = False,
    ) -> Optional[ContextEntry]:
        """
        Retrieve a context entry by ID with access control.
        
        Args:
            context_id: Context ID to retrieve
            user_id: User ID requesting access
            include_content: Whether to include content
            include_files: Whether to include associated files
            
        Returns:
            Context entry if found and accessible, None otherwise
        """
        start_time = time.time()
        
        try:
            # Get context from storage
            context = self._contexts.get(context_id)
            if not context:
                return None
            
            # Check access permissions
            if not await self._check_access_permission(context, user_id, "read"):
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="read",
                    access_level=context.access_level,
                    success=False,
                    error_message="Access denied",
                )
                return None
            
            # Increment access count
            context.increment_access()
            
            # Include files if requested
            if include_files:
                context.file_ids = [
                    file_id for file_id in context.file_ids 
                    if file_id in self._files
                ]
            
            # Log successful access
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="read",
                access_level=context.access_level,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context {context_id} for user {user_id}: {e}")
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="read",
                access_level=ContextAccessLevel.PRIVATE,
                success=False,
                error_message=str(e),
            )
            return None

    async def update_context(
        self,
        context_id: str,
        user_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance_score: Optional[float] = None,
        create_version: bool = True,
        change_summary: Optional[str] = None,
    ) -> Optional[ContextEntry]:
        """
        Update a context entry with versioning support.
        
        Args:
            context_id: Context ID to update
            user_id: User ID making the update
            title: New title (None to keep current)
            content: New content (None to keep current)
            metadata: New metadata (None to keep current)
            tags: New tags (None to keep current)
            importance_score: New importance score (None to keep current)
            create_version: Whether to create a new version
            change_summary: Summary of changes
            
        Returns:
            Updated context entry if successful, None otherwise
        """
        start_time = time.time()
        
        try:
            # Get existing context
            context = self._contexts.get(context_id)
            if not context:
                return None
            
            # Check write permissions
            if not await self._check_access_permission(context, user_id, "write"):
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="write",
                    access_level=context.access_level,
                    success=False,
                    error_message="Write access denied",
                )
                return None
            
            # Create version snapshot if requested
            if create_version:
                version = ContextVersion(
                    version_id=str(uuid.uuid4()),
                    context_id=context_id,
                    version_number=context.version,
                    content=context.content,
                    title=context.title,
                    created_by=user_id,
                    change_summary=change_summary,
                    metadata=context.metadata.copy(),
                    tags=context.tags.copy(),
                )
                
                if context_id not in self._versions:
                    self._versions[context_id] = []
                self._versions[context_id].append(version)
            
            # Update fields
            if title is not None:
                context.title = title
            if content is not None:
                context.content = content
                # Regenerate embedding for new content
                if content:
                    try:
                        await self._ensure_embedding_manager()
                        embedding_raw = await self.memory_manager.embedding_manager.get_embedding(content)
                        context.embedding = np.array(embedding_raw)
                    except Exception as e:
                        logger.warning(f"Failed to regenerate embedding for context {context_id}: {e}")
            if metadata is not None:
                context.metadata.update(metadata)
            if tags is not None:
                context.tags = tags
            if importance_score is not None:
                context.importance_score = importance_score
            
            # Update timestamp
            context.updated_at = datetime.utcnow()
            
            # Update in memory system
            await self._store_context_in_memory(context)
            
            # Log access
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="write",
                access_level=context.access_level,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            
            logger.info(f"Updated context {context_id} for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to update context {context_id} for user {user_id}: {e}")
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="write",
                access_level=ContextAccessLevel.PRIVATE,
                success=False,
                error_message=str(e),
            )
            return None

    async def delete_context(
        self,
        context_id: str,
        user_id: str,
        permanent: bool = False,
    ) -> bool:
        """
        Delete a context entry (soft delete by default).
        
        Args:
            context_id: Context ID to delete
            user_id: User ID requesting deletion
            permanent: Whether to permanently delete (default: soft delete)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        start_time = time.time()
        
        try:
            # Get context
            context = self._contexts.get(context_id)
            if not context:
                return False
            
            # Check delete permissions
            if not await self._check_access_permission(context, user_id, "delete"):
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="delete",
                    access_level=context.access_level,
                    success=False,
                    error_message="Delete access denied",
                )
                return False
            
            if permanent:
                # Permanent deletion
                del self._contexts[context_id]
                
                # Delete from memory system
                await self.memory_manager.delete_memory(
                    tenant_id=user_id,
                    memory_id=context_id,
                )
                
                # Delete associated files
                for file_id in context.file_ids:
                    if file_id in self._files:
                        file_obj = self._files[file_id]
                        try:
                            os.remove(file_obj.storage_path)
                        except Exception as e:
                            logger.warning(f"Failed to delete file {file_id}: {e}")
                        del self._files[file_id]
                
                # Delete shares
                shares_to_delete = [
                    share_id for share_id, share in self._shares.items()
                    if share.context_id == context_id
                ]
                for share_id in shares_to_delete:
                    del self._shares[share_id]
                
                # Delete versions
                if context_id in self._versions:
                    del self._versions[context_id]
            else:
                # Soft delete
                context.status = ContextStatus.DELETED
            
            # Log access
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="delete",
                access_level=context.access_level,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )
            
            logger.info(f"{'Permanently deleted' if permanent else 'Soft deleted'} context {context_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete context {context_id} for user {user_id}: {e}")
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="delete",
                access_level=ContextAccessLevel.PRIVATE,
                success=False,
                error_message=str(e),
            )
            return False

    # -------------------------------------------------------------------------
    # Context Search and Querying
    # -------------------------------------------------------------------------

    async def search_contexts(
        self,
        query: ContextQuery,
        user_id: str,
    ) -> List[ContextSearchResult]:
        """
        Search for contexts based on query parameters.
        
        Args:
            query: Search query parameters
            user_id: User ID performing the search
            
        Returns:
            List of search results with relevance scores
        """
        start_time = time.time()
        
        try:
            # Build memory query for vector search
            memory_query = MemoryQuery(
                text=query.query_text,
                user_id=user_id,
                org_id=query.org_id,
                session_id=query.session_id,
                conversation_id=query.conversation_id,
                top_k=query.top_k,
                similarity_threshold=query.similarity_threshold,
                include_embeddings=True,
            )
            
            # Search in memory system
            memory_results = await self.memory_manager.query_memories(
                tenant_id=user_id,
                query=memory_query,
            )
            
            # Convert memory results to context entries
            search_results = []
            for memory_item in memory_results:
                context_id = memory_item.id
                context = self._contexts.get(context_id)
                
                if not context:
                    continue
                
                # Check access permissions
                if not await self._check_access_permission(context, user_id, "read"):
                    continue
                
                # Apply additional filters
                if not self._passes_filters(context, query):
                    continue
                
                # Calculate relevance score
                relevance_score = await self.relevance_scorer.calculate_relevance(
                    context=context,
                    query=query,
                    similarity_score=memory_item.similarity_score or 0.0,
                )
                
                # Create search result
                result = ContextSearchResult(
                    context=context,
                    similarity_score=memory_item.similarity_score or 0.0,
                    relevance_score=relevance_score,
                )
                
                search_results.append(result)
            
            # Sort results
            search_results = self._sort_search_results(search_results, query)
            
            # Log search
            await self._log_access(
                context_id="search",
                user_id=user_id,
                action="search",
                access_level=ContextAccessLevel.PRIVATE,
                processing_time_ms=int((time.time() - start_time) * 1000),
                metadata={
                    "query": query.to_dict(),
                    "results_count": len(search_results),
                },
            )
            
            return search_results[:query.top_k]
            
        except Exception as e:
            logger.error(f"Failed to search contexts for user {user_id}: {e}")
            await self._log_access(
                context_id="search",
                user_id=user_id,
                action="search",
                access_level=ContextAccessLevel.PRIVATE,
                success=False,
                error_message=str(e),
            )
            return []

    # -------------------------------------------------------------------------
    # Context Sharing
    # -------------------------------------------------------------------------

    async def share_context(
        self,
        context_id: str,
        user_id: str,
        shared_with: Optional[str] = None,
        access_level: ContextAccessLevel = ContextAccessLevel.SHARED,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> Optional[ContextShare]:
        """
        Share a context with another user or group.
        
        Args:
            context_id: Context ID to share
            user_id: User ID sharing the context
            shared_with: User ID to share with (None for team/org/public)
            access_level: Access level for the share
            permissions: List of permissions (read, write, share, delete)
            expires_in_days: Days until share expires (None for no expiration)
            
        Returns:
            Share object if successful, None otherwise
        """
        try:
            # Get context
            context = self._contexts.get(context_id)
            if not context:
                return None
            
            # Check share permissions
            if not await self._check_access_permission(context, user_id, "share"):
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="share",
                    access_level=context.access_level,
                    success=False,
                    error_message="Share access denied",
                )
                return None
            
            # Create share
            share = ContextShare(
                share_id=str(uuid.uuid4()),
                context_id=context_id,
                shared_by=user_id,
                shared_with=shared_with,
                access_level=access_level,
                permissions=permissions or ["read"],
            )
            
            # Set expiration if provided
            if expires_in_days:
                share.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Store share
            self._shares[share.share_id] = share
            
            # Log share
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="share",
                access_level=access_level,
                metadata={
                    "share_id": share.share_id,
                    "shared_with": shared_with,
                    "permissions": share.permissions,
                },
            )
            
            logger.info(f"Shared context {context_id} by user {user_id}")
            return share
            
        except Exception as e:
            logger.error(f"Failed to share context {context_id} for user {user_id}: {e}")
            await self._log_access(
                context_id=context_id,
                user_id=user_id,
                action="share",
                access_level=ContextAccessLevel.PRIVATE,
                success=False,
                error_message=str(e),
            )
            return None

    # -------------------------------------------------------------------------
    # Context Versioning
    # -------------------------------------------------------------------------

    async def get_context_versions(
        self,
        context_id: str,
        user_id: str,
    ) -> List[ContextVersion]:
        """
        Get all versions of a context.
        
        Args:
            context_id: Context ID
            user_id: User ID requesting versions
            
        Returns:
            List of context versions
        """
        try:
            # Check read permissions
            context = self._contexts.get(context_id)
            if not context:
                return []
            
            if not await self._check_access_permission(context, user_id, "read"):
                return []
            
            # Get versions
            versions = self._versions.get(context_id, [])
            return sorted(versions, key=lambda v: v.version_number, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get versions for context {context_id}: {e}")
            return []

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _ensure_embedding_manager(self) -> None:
        """Ensure embedding manager is available."""
        await self.memory_manager._ensure_embedding_manager()

    async def _store_context_in_memory(self, context: ContextEntry) -> None:
        """Store context in memory system for vector search."""
        try:
            # Convert to neuro memory entry for compatibility
            neuro_entry = NeuroMemoryEntry.from_web_ui_memory(
                context,
                neuro_type=NeuroMemoryType.EPISODIC,
            )
            
            # Store in memory system
            await self.memory_manager.store_memory(
                tenant_id=context.user_id,
                content=context.content,
                scope="context",
                kind=context.context_type.value,
                metadata={
                    "context_id": context.id,
                    "title": context.title,
                    "access_level": context.access_level.value,
                    "tags": context.tags,
                    **context.metadata,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to store context {context.id} in memory system: {e}")

    async def _check_access_permission(
        self,
        context: ContextEntry,
        user_id: str,
        action: str,
    ) -> bool:
        """
        Check if user has permission to perform action on context.
        
        Args:
            context: Context entry
            user_id: User ID to check
            action: Action to check (read, write, share, delete)
            
        Returns:
            True if user has permission, False otherwise
        """
        # Owner has all permissions
        if context.user_id == user_id:
            return True
        
        # Check access level
        if context.access_level == ContextAccessLevel.PRIVATE:
            return False
        elif context.access_level == ContextAccessLevel.SHARED:
            # Check if shared with this user
            for share in self._shares.values():
                if (share.context_id == context.id and 
                    share.shared_with == user_id and 
                    share.is_active and
                    action in share.permissions):
                    return True
            return False
        elif context.access_level == ContextAccessLevel.TEAM:
            # Check if same organization (simplified)
            return context.org_id and context.org_id == getattr(self._contexts.get(user_id), 'org_id', None)
        elif context.access_level == ContextAccessLevel.ORGANIZATION:
            # Check if same organization
            return context.org_id and context.org_id == getattr(self._contexts.get(user_id), 'org_id', None)
        elif context.access_level == ContextAccessLevel.PUBLIC:
            return True
        
        return False

    def _passes_filters(self, context: ContextEntry, query: ContextQuery) -> bool:
        """Check if context passes all query filters."""
        # Status filter
        if query.status and context.status not in query.status:
            return False
        
        # Type filter
        if query.context_types and context.context_type not in query.context_types:
            return False
        
        # Access level filter
        if query.access_levels and context.access_level not in query.access_levels:
            return False
        
        # Tags filter (all tags must be present)
        if query.tags:
            if not all(tag in context.tags for tag in query.tags):
                return False
        
        # Keywords filter
        if query.keywords:
            content_lower = context.content.lower()
            title_lower = context.title.lower()
            if not all(keyword.lower() in content_lower or keyword.lower() in title_lower 
                      for keyword in query.keywords):
                return False
        
        # Time filters
        if query.created_after and context.created_at < query.created_after:
            return False
        if query.created_before and context.created_at > query.created_before:
            return False
        if query.updated_after and context.updated_at < query.updated_after:
            return False
        if query.updated_before and context.updated_at > query.updated_before:
            return False
        
        # Metadata filter
        if query.metadata_filter:
            for key, value in query.metadata_filter.items():
                if context.metadata.get(key) != value:
                    return False
        
        return True

    def _sort_search_results(
        self,
        results: List[ContextSearchResult],
        query: ContextQuery,
    ) -> List[ContextSearchResult]:
        """Sort search results based on query parameters."""
        reverse = query.sort_order == "desc"
        
        if query.sort_by == "relevance":
            results.sort(key=lambda r: r.relevance_score, reverse=reverse)
        elif query.sort_by == "similarity":
            results.sort(key=lambda r: r.similarity_score, reverse=reverse)
        elif query.sort_by == "created_at":
            results.sort(key=lambda r: r.context.created_at, reverse=reverse)
        elif query.sort_by == "updated_at":
            results.sort(key=lambda r: r.context.updated_at, reverse=reverse)
        elif query.sort_by == "access_count":
            results.sort(key=lambda r: r.context.access_count, reverse=reverse)
        elif query.sort_by == "importance":
            results.sort(key=lambda r: r.context.importance_score, reverse=reverse)
        
        return results

    async def _log_access(
        self,
        context_id: str,
        user_id: str,
        action: str,
        access_level: ContextAccessLevel,
        success: bool = True,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log context access for auditing."""
        log_entry = ContextAccessLog(
            context_id=context_id,
            user_id=user_id,
            action=action,
            access_level=access_level,
            success=success,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            metadata=metadata or {},
        )
        
        self._access_logs.append(log_entry)
        
        # Keep only recent logs (last 10000)
        if len(self._access_logs) > 10000:
            self._access_logs = self._access_logs[-10000:]

    # -------------------------------------------------------------------------
    # Statistics and Monitoring
    # -------------------------------------------------------------------------

    async def get_context_stats(
        self,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get context statistics for a user or organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID (optional)
            
        Returns:
            Dictionary with statistics
        """
        try:
            user_contexts = [
                ctx for ctx in self._contexts.values()
                if ctx.user_id == user_id and ctx.status == ContextStatus.ACTIVE
            ]
            
            org_contexts = []
            if org_id:
                org_contexts = [
                    ctx for ctx in self._contexts.values()
                    if ctx.org_id == org_id and ctx.status == ContextStatus.ACTIVE
                ]
            
            # Calculate statistics
            stats = {
                "user_stats": {
                    "total_contexts": len(user_contexts),
                    "by_type": {
                        ctx_type.value: len([c for c in user_contexts if c.context_type == ctx_type])
                        for ctx_type in ContextType
                    },
                    "by_access_level": {
                        access_level.value: len([c for c in user_contexts if c.access_level == access_level])
                        for access_level in ContextAccessLevel
                    },
                    "total_files": sum(len(ctx.file_ids) for ctx in user_contexts),
                    "total_size_mb": sum(
                        self._files.get(file_id, ContextFile(file_id="", context_id="", filename="", file_type=ContextFileType.TXT, mime_type="", size_bytes=0, storage_path="", checksum="")).size_bytes
                        for ctx in user_contexts
                        for file_id in ctx.file_ids
                    ) / (1024 * 1024),
                    "avg_importance": sum(ctx.importance_score for ctx in user_contexts) / len(user_contexts) if user_contexts else 0,
                    "total_accesses": sum(ctx.access_count for ctx in user_contexts),
                },
                "org_stats": {
                    "total_contexts": len(org_contexts),
                    "shared_contexts": len([c for c in org_contexts if c.access_level != ContextAccessLevel.PRIVATE]),
                } if org_id else None,
                "system_stats": {
                    "total_contexts": len([c for c in self._contexts.values() if c.status == ContextStatus.ACTIVE]),
                    "total_files": len(self._files),
                    "total_shares": len(self._shares),
                    "total_versions": sum(len(versions) for versions in self._versions.values()),
                    "access_logs_count": len(self._access_logs),
                },
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get context stats for user {user_id}: {e}")
            return {"error": str(e)}