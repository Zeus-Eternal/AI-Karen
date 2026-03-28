"""
Context Management Service

Main service for context persistence, retrieval, versioning, and sharing.
Integrates with existing database, memory, and file storage systems.
"""

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy import text

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
            await self._persist_context(context)
            
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
            context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
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
            await self._persist_context(context)
            
            # Include files if requested
            if include_files:
                files = await self._load_files_for_context(context.id)
                context.file_ids = [file.file_id for file in files if file.status != ContextStatus.DELETED]
            
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
            context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
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
                await self._persist_version(version)
            
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
            await self._persist_context(context)
            
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
            context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
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
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="delete",
                    access_level=context.access_level,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )

                # Permanent deletion
                self._contexts.pop(context_id, None)
                await self._delete_context_from_db(context_id)
                
                # Delete from memory system
                memory_id = context.metadata.get("_memory_id")
                if self._is_uuid_like(memory_id):
                    await self.memory_manager.delete_memory(
                        tenant_id=user_id,
                        memory_id=memory_id,
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
                context.updated_at = datetime.utcnow()
                await self._persist_context(context)

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
            try:
                await self._log_access(
                    context_id=context_id,
                    user_id=user_id,
                    action="delete",
                    access_level=ContextAccessLevel.PRIVATE,
                    success=False,
                    error_message=str(e),
                )
            except Exception as log_error:
                logger.warning(
                    f"Failed to record delete audit log for context {context_id}: {log_error}"
                )
            return False

    # -------------------------------------------------------------------------
    # Context Search and Querying
    # -------------------------------------------------------------------------

    async def search_contexts(
        self,
        query: ContextQuery,
        user_id: Optional[str] = None,
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
            effective_user_id = user_id or query.user_id
            if not effective_user_id:
                raise ValueError("user_id is required to search contexts")

            # Build memory query for vector search
            metadata_filter: Dict[str, Any] = {}
            if query.org_id:
                metadata_filter["org_id"] = query.org_id

            memory_query = MemoryQuery(
                text=query.query_text,
                user_id=effective_user_id,
                session_id=query.session_id,
                conversation_id=query.conversation_id,
                metadata_filter=metadata_filter,
                top_k=query.top_k,
                similarity_threshold=query.similarity_threshold,
                include_embeddings=True,
            )
            
            # Search in memory system
            memory_results = await self.memory_manager.query_memories(
                tenant_id=effective_user_id,
                query=memory_query,
            )
            
            # Convert memory results to context entries
            search_results = []
            for memory_item in memory_results:
                context_id = (
                    memory_item.metadata.get("context_id")
                    if isinstance(memory_item.metadata, dict)
                    else None
                ) or memory_item.id
                context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
                
                if not context:
                    continue
                
                # Check access permissions
                if not await self._check_access_permission(context, effective_user_id, "read"):
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
                    match_highlights=self.relevance_scorer.calculate_match_highlights(
                        context,
                        query,
                    ),
                    explanation=self.relevance_scorer.calculate_explanation(
                        context,
                        query,
                        similarity_score=memory_item.similarity_score or 0.0,
                        relevance_score=relevance_score,
                    ),
                )
                
                search_results.append(result)
            
            # Sort results
            search_results = self._sort_search_results(search_results, query)
            
            # Log search
            await self._log_access(
                context_id="search",
                user_id=effective_user_id,
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
            effective_user_id = user_id or query.user_id or "unknown"
            logger.error(f"Failed to search contexts for user {effective_user_id}: {e}")
            await self._log_access(
                context_id="search",
                user_id=effective_user_id,
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
            context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
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
            await self._persist_share(share)
            
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
            context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
            if not context:
                return []
            
            if not await self._check_access_permission(context, user_id, "read"):
                return []
            
            # Get versions
            versions = self._versions.get(context_id)
            if versions is None:
                versions = await self._load_versions_from_db(context_id)
                if versions:
                    self._versions[context_id] = versions
            versions = versions or []
            return sorted(versions, key=lambda v: v.version_number, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get versions for context {context_id}: {e}")
            return []

    async def add_file_reference(
        self,
        context_id: str,
        file_id: str,
    ) -> bool:
        """Attach a file reference to a context and persist the change."""
        context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
        if not context:
            return False

        if file_id not in context.file_ids:
            context.file_ids.append(file_id)
            context.updated_at = datetime.utcnow()
            await self._persist_context(context)
        return True

    async def remove_file_reference(
        self,
        context_id: str,
        file_id: str,
    ) -> bool:
        """Detach a file reference from a context and persist the change."""
        context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
        if not context:
            return False

        if file_id in context.file_ids:
            context.file_ids.remove(file_id)
            context.updated_at = datetime.utcnow()
            await self._persist_context(context)
        return True

    async def list_context_files(
        self,
        context_id: str,
        user_id: str,
    ) -> List[ContextFile]:
        """Return the files attached to a context that the user can access."""
        context = self._contexts.get(context_id) or await self._load_context_from_db(context_id)
        if not context:
            return []

        if not await self._check_access_permission(context, user_id, "read"):
            return []

        return await self._load_files_for_context(context_id)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _ensure_embedding_manager(self) -> None:
        """Ensure embedding manager is available."""
        await self.memory_manager._ensure_embedding_manager()

    async def _store_context_in_memory(self, context: ContextEntry) -> None:
        """Store context in memory system for vector search."""
        try:
            previous_memory_id = context.metadata.get("_memory_id")
            if self._is_uuid_like(previous_memory_id):
                await self.memory_manager.delete_memory(
                    tenant_id=context.user_id,
                    memory_id=previous_memory_id,
                )

            memory_id = await self.memory_manager.store_memory(
                tenant_id=context.user_id,
                content=context.content,
                scope="context",
                kind=context.context_type.value,
                metadata={
                    "context_id": context.id,
                    "user_id": context.user_id,
                    "org_id": context.org_id,
                    "session_id": context.session_id,
                    "conversation_id": context.conversation_id,
                    "title": context.title,
                    "access_level": context.access_level.value,
                    "tags": context.tags,
                    **context.metadata,
                },
            )
            if memory_id:
                context.metadata["_memory_id"] = memory_id
        except Exception as e:
            logger.warning(f"Failed to store context {context.id} in memory system: {e}")

    def _get_db_client(self) -> Optional[Any]:
        """Return the underlying database client if available."""
        return getattr(self.memory_manager, "db_client", None)

    def _has_db_persistence(self) -> bool:
        """Whether context persistence can use the configured database."""
        db_client = self._get_db_client()
        return db_client is not None and hasattr(db_client, "get_async_session")

    def _is_uuid_like(self, value: str) -> bool:
        """Check whether a string can be parsed as a UUID."""
        try:
            uuid.UUID(str(value))
            return True
        except (TypeError, ValueError):
            return False

    def _serialize_json(self, value: Any) -> str:
        """Serialize a Python value for JSONB transport."""
        return json.dumps([] if value is None else value)

    def _row_to_context(self, row: Dict[str, Any]) -> ContextEntry:
        """Hydrate a ContextEntry from a database row mapping."""
        embedding = row.get("embedding")
        return ContextEntry(
            id=str(row["id"]),
            user_id=row["user_id"],
            org_id=row.get("org_id"),
            session_id=row.get("session_id"),
            conversation_id=str(row["conversation_id"]) if row.get("conversation_id") else None,
            title=row.get("title") or "",
            content=row.get("content") or "",
            context_type=ContextType(row.get("context_type") or ContextType.CUSTOM.value),
            access_level=ContextAccessLevel(row.get("access_level") or ContextAccessLevel.PRIVATE.value),
            status=ContextStatus(row.get("status") or ContextStatus.ACTIVE.value),
            embedding=np.array(embedding) if embedding else None,
            summary=row.get("summary"),
            keywords=list(row.get("keywords") or []),
            entities=list(row.get("entities") or []),
            relevance_score=float(row.get("relevance_score") or 0.0),
            importance_score=float(row.get("importance_score") or 5.0),
            access_count=int(row.get("access_count") or 0),
            last_accessed=row.get("last_accessed"),
            version=int(row.get("version") or 1),
            parent_context_id=str(row["parent_context_id"]) if row.get("parent_context_id") else None,
            child_context_ids=list(row.get("child_context_ids") or []),
            metadata=dict(row.get("metadata") or {}),
            tags=list(row.get("tags") or []),
            created_at=row.get("created_at") or datetime.utcnow(),
            updated_at=row.get("updated_at") or datetime.utcnow(),
            expires_at=row.get("expires_at"),
            file_ids=list(row.get("file_ids") or []),
        )

    async def _load_context_from_db(self, context_id: str) -> Optional[ContextEntry]:
        """Load a context entry from Postgres into the in-memory cache."""
        if not self._has_db_persistence() or not self._is_uuid_like(context_id):
            return None

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        id, user_id, org_id, session_id, conversation_id, title, content,
                        context_type, access_level, status, summary, keywords, entities,
                        relevance_score, importance_score, access_count, last_accessed,
                        version, parent_context_id, child_context_ids, metadata, tags,
                        created_at, updated_at, expires_at, file_ids
                    FROM context_entries
                    WHERE id = CAST(:context_id AS UUID)
                    """
                ),
                {"context_id": context_id},
            )
            row = result.mappings().first()

        if not row:
            return None

        context = self._row_to_context(dict(row))
        self._contexts[context.id] = context
        return context

    async def _load_user_scope(self, user_id: str) -> Dict[str, Optional[str]]:
        """Load tenant and organization scope for a user."""
        scope = {"tenant_id": None, "org_id": None}
        if not self._has_db_persistence() or not self._is_uuid_like(user_id):
            return scope

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT tenant_id
                    FROM auth_users
                    WHERE user_id = CAST(:user_id AS UUID)
                    """
                ),
                {"user_id": user_id},
            )
            row = result.mappings().first()

        if not row:
            return scope

        tenant_id = str(row["tenant_id"]) if row.get("tenant_id") else None
        return {
            "tenant_id": tenant_id,
            "org_id": tenant_id,
        }

    async def _persist_context(self, context: ContextEntry) -> None:
        """Persist a context entry to Postgres when the database is available."""
        if not self._has_db_persistence():
            return

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO context_entries (
                        id, user_id, org_id, session_id, conversation_id, title, content,
                        context_type, access_level, status, summary, keywords, entities,
                        relevance_score, importance_score, access_count, last_accessed,
                        version, parent_context_id, child_context_ids, metadata, tags,
                        created_at, updated_at, expires_at, file_ids
                    ) VALUES (
                        CAST(:id AS UUID), :user_id, :org_id, :session_id,
                        CAST(:conversation_id AS UUID), :title, :content, :context_type,
                        :access_level, :status, :summary, CAST(:keywords AS JSONB),
                        CAST(:entities AS JSONB), :relevance_score, :importance_score,
                        :access_count, :last_accessed, :version,
                        CAST(:parent_context_id AS UUID), CAST(:child_context_ids AS JSONB),
                        CAST(:metadata AS JSONB), CAST(:tags AS JSONB),
                        :created_at, :updated_at, :expires_at, CAST(:file_ids AS JSONB)
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        org_id = EXCLUDED.org_id,
                        session_id = EXCLUDED.session_id,
                        conversation_id = EXCLUDED.conversation_id,
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        context_type = EXCLUDED.context_type,
                        access_level = EXCLUDED.access_level,
                        status = EXCLUDED.status,
                        summary = EXCLUDED.summary,
                        keywords = EXCLUDED.keywords,
                        entities = EXCLUDED.entities,
                        relevance_score = EXCLUDED.relevance_score,
                        importance_score = EXCLUDED.importance_score,
                        access_count = EXCLUDED.access_count,
                        last_accessed = EXCLUDED.last_accessed,
                        version = EXCLUDED.version,
                        parent_context_id = EXCLUDED.parent_context_id,
                        child_context_ids = EXCLUDED.child_context_ids,
                        metadata = EXCLUDED.metadata,
                        tags = EXCLUDED.tags,
                        updated_at = EXCLUDED.updated_at,
                        expires_at = EXCLUDED.expires_at,
                        file_ids = EXCLUDED.file_ids
                    """
                ),
                {
                    "id": context.id,
                    "user_id": context.user_id,
                    "org_id": context.org_id,
                    "session_id": context.session_id,
                    "conversation_id": context.conversation_id,
                    "title": context.title,
                    "content": context.content,
                    "context_type": context.context_type.value,
                    "access_level": context.access_level.value,
                    "status": context.status.value,
                    "summary": context.summary,
                    "keywords": self._serialize_json(context.keywords),
                    "entities": self._serialize_json(context.entities),
                    "relevance_score": context.relevance_score,
                    "importance_score": context.importance_score,
                    "access_count": context.access_count,
                    "last_accessed": context.last_accessed,
                    "version": context.version,
                    "parent_context_id": context.parent_context_id,
                    "child_context_ids": self._serialize_json(context.child_context_ids),
                    "metadata": json.dumps(context.metadata or {}),
                    "tags": self._serialize_json(context.tags),
                    "created_at": context.created_at,
                    "updated_at": context.updated_at,
                    "expires_at": context.expires_at,
                    "file_ids": self._serialize_json(context.file_ids),
                },
            )
            await session.commit()

    async def _delete_context_from_db(self, context_id: str) -> None:
        """Delete a context entry from Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(context_id):
            return

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            await session.execute(
                text("DELETE FROM context_entries WHERE id = CAST(:context_id AS UUID)"),
                {"context_id": context_id},
            )
            await session.commit()

    async def _persist_version(self, version: ContextVersion) -> None:
        """Persist a context version row to Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(version.context_id):
            return

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO context_versions (
                        version_id, context_id, version_number, content, title,
                        created_by, change_summary, metadata, tags, created_at
                    ) VALUES (
                        CAST(:version_id AS UUID), CAST(:context_id AS UUID),
                        :version_number, :content, :title, :created_by,
                        :change_summary, CAST(:metadata AS JSONB), CAST(:tags AS JSONB),
                        :created_at
                    )
                    ON CONFLICT (version_id) DO NOTHING
                    """
                ),
                {
                    "version_id": version.version_id,
                    "context_id": version.context_id,
                    "version_number": version.version_number,
                    "content": version.content,
                    "title": version.title,
                    "created_by": version.created_by,
                    "change_summary": version.change_summary,
                    "metadata": json.dumps(version.metadata or {}),
                    "tags": self._serialize_json(version.tags),
                    "created_at": version.created_at,
                },
            )
            await session.commit()

    async def _load_versions_from_db(self, context_id: str) -> List[ContextVersion]:
        """Load context versions from Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(context_id):
            return []

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT version_id, context_id, version_number, content, title,
                           created_by, change_summary, metadata, tags, created_at
                    FROM context_versions
                    WHERE context_id = CAST(:context_id AS UUID)
                    ORDER BY version_number DESC
                    """
                ),
                {"context_id": context_id},
            )
            rows = result.mappings().all()

        return [
            ContextVersion(
                version_id=str(row["version_id"]),
                context_id=str(row["context_id"]),
                version_number=int(row["version_number"]),
                content=row["content"],
                title=row["title"],
                created_by=row["created_by"],
                change_summary=row.get("change_summary"),
                metadata=dict(row.get("metadata") or {}),
                tags=list(row.get("tags") or []),
                created_at=row.get("created_at") or datetime.utcnow(),
            )
            for row in rows
        ]

    async def _persist_share(self, share: ContextShare) -> None:
        """Persist a context share row to Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(share.context_id):
            return

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO context_shares (
                        share_id, context_id, shared_by, shared_with, access_level,
                        permissions, created_at, last_accessed, access_count, expires_at
                    ) VALUES (
                        CAST(:share_id AS UUID), CAST(:context_id AS UUID), :shared_by,
                        :shared_with, :access_level, CAST(:permissions AS JSONB),
                        :created_at, :last_accessed, :access_count, :expires_at
                    )
                    ON CONFLICT (share_id) DO UPDATE SET
                        shared_by = EXCLUDED.shared_by,
                        shared_with = EXCLUDED.shared_with,
                        access_level = EXCLUDED.access_level,
                        permissions = EXCLUDED.permissions,
                        last_accessed = EXCLUDED.last_accessed,
                        access_count = EXCLUDED.access_count,
                        expires_at = EXCLUDED.expires_at
                    """
                ),
                {
                    "share_id": share.share_id,
                    "context_id": share.context_id,
                    "shared_by": share.shared_by,
                    "shared_with": share.shared_with,
                    "access_level": share.access_level.value,
                    "permissions": self._serialize_json(share.permissions),
                    "created_at": share.created_at,
                    "last_accessed": share.last_accessed,
                    "access_count": share.access_count,
                    "expires_at": share.expires_at,
                },
            )
            await session.commit()

    async def _load_shares_for_context(self, context_id: str) -> List[ContextShare]:
        """Load shares for a given context from Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(context_id):
            return []

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT share_id, context_id, shared_by, shared_with, access_level,
                           permissions, created_at, last_accessed, access_count, expires_at
                    FROM context_shares
                    WHERE context_id = CAST(:context_id AS UUID)
                    """
                ),
                {"context_id": context_id},
            )
            rows = result.mappings().all()

        shares = [
            ContextShare(
                share_id=str(row["share_id"]),
                context_id=str(row["context_id"]),
                shared_by=row["shared_by"],
                shared_with=row.get("shared_with"),
                access_level=ContextAccessLevel(row["access_level"]),
                permissions=list(row.get("permissions") or []),
                created_at=row.get("created_at") or datetime.utcnow(),
                last_accessed=row.get("last_accessed"),
                access_count=int(row.get("access_count") or 0),
                expires_at=row.get("expires_at"),
            )
            for row in rows
        ]
        for share in shares:
            self._shares[share.share_id] = share
        return shares

    async def _load_files_for_context(self, context_id: str) -> List[ContextFile]:
        """Load all non-deleted files for a context from Postgres."""
        if not self._has_db_persistence() or not self._is_uuid_like(context_id):
            return [
                file
                for file in self._files.values()
                if file.context_id == context_id and file.status != ContextStatus.DELETED
            ]

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT file_id, context_id, filename, file_type, mime_type, size_bytes,
                           storage_path, checksum, extracted_text, extracted_metadata,
                           created_at, processed_at, status, error_message
                    FROM context_files
                    WHERE context_id = CAST(:context_id AS UUID)
                      AND status != 'deleted'
                    ORDER BY created_at ASC
                    """
                ),
                {"context_id": context_id},
            )
            rows = result.mappings().all()

        files = [
            ContextFile(
                file_id=str(row["file_id"]),
                context_id=str(row["context_id"]),
                filename=row["filename"],
                file_type=ContextFileType(row["file_type"]),
                mime_type=row["mime_type"],
                size_bytes=int(row["size_bytes"]),
                storage_path=row["storage_path"],
                checksum=row["checksum"],
                extracted_text=row.get("extracted_text"),
                extracted_metadata=dict(row.get("extracted_metadata") or {}),
                created_at=row.get("created_at") or datetime.utcnow(),
                processed_at=row.get("processed_at"),
                status=ContextStatus(row.get("status") or ContextStatus.PROCESSING.value),
                error_message=row.get("error_message"),
            )
            for row in rows
        ]

        for file in files:
            self._files[file.file_id] = file
        return files

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
            await self._load_shares_for_context(context.id)
            for share in self._shares.values():
                if (share.context_id == context.id and 
                    share.shared_with == user_id and 
                    share.is_active and
                    action in share.permissions):
                    return True
            return False
        elif context.access_level == ContextAccessLevel.TEAM:
            owner_scope = await self._load_user_scope(context.user_id)
            requester_scope = await self._load_user_scope(user_id)
            if not requester_scope["tenant_id"] or not owner_scope["tenant_id"]:
                return False

            if requester_scope["tenant_id"] == owner_scope["tenant_id"]:
                return True

            if context.org_id and requester_scope["org_id"] == context.org_id:
                return True
            return False
        elif context.access_level == ContextAccessLevel.ORGANIZATION:
            owner_scope = await self._load_user_scope(context.user_id)
            requester_scope = await self._load_user_scope(user_id)
            if not requester_scope["tenant_id"] or not owner_scope["tenant_id"]:
                return False

            if requester_scope["tenant_id"] == owner_scope["tenant_id"]:
                return True

            if context.org_id and requester_scope["org_id"] == context.org_id:
                return True
            return False
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
        await self._persist_access_log(log_entry)
        
        # Keep only recent logs (last 10000)
        if len(self._access_logs) > 10000:
            self._access_logs = self._access_logs[-10000:]

    async def _persist_access_log(self, log_entry: ContextAccessLog) -> None:
        """Persist audit logs when they reference a real context row."""
        if (
            not self._has_db_persistence()
            or not self._is_uuid_like(log_entry.context_id)
        ):
            return

        action = "write" if log_entry.action == "create" else log_entry.action

        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO context_access_log (
                        log_id, context_id, user_id, action, access_level, ip_address,
                        user_agent, success, error_message, processing_time_ms, metadata,
                        created_at
                    ) VALUES (
                        CAST(:log_id AS UUID), CAST(:context_id AS UUID), :user_id, :action,
                        :access_level, CAST(:ip_address AS INET), :user_agent, :success,
                        :error_message, :processing_time_ms, CAST(:metadata AS JSONB),
                        :created_at
                    )
                    """
                ),
                {
                    "log_id": log_entry.log_id,
                    "context_id": log_entry.context_id,
                    "user_id": log_entry.user_id,
                    "action": action,
                    "access_level": log_entry.access_level.value,
                    "ip_address": log_entry.ip_address,
                    "user_agent": log_entry.user_agent,
                    "success": log_entry.success,
                    "error_message": log_entry.error_message,
                    "processing_time_ms": log_entry.processing_time_ms,
                    "metadata": json.dumps(log_entry.metadata or {}),
                    "created_at": log_entry.created_at,
                },
            )
            await session.commit()

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
            if self._has_db_persistence():
                return await self._get_context_stats_from_db(user_id, org_id)

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

    async def _get_context_stats_from_db(
        self,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get context statistics directly from Postgres."""
        db_client = self._get_db_client()
        async with db_client.get_async_session() as session:
            user_summary = (
                await session.execute(
                    text(
                        """
                        SELECT
                            COUNT(*) AS total_contexts,
                            COALESCE(AVG(importance_score), 0) AS avg_importance,
                            COALESCE(SUM(access_count), 0) AS total_accesses,
                            COALESCE(SUM(jsonb_array_length(file_ids)), 0) AS total_files
                        FROM context_entries
                        WHERE user_id = :user_id
                          AND status = 'active'
                        """
                    ),
                    {"user_id": user_id},
                )
            ).mappings().first()

            by_type_rows = (
                await session.execute(
                    text(
                        """
                        SELECT context_type, COUNT(*) AS count
                        FROM context_entries
                        WHERE user_id = :user_id
                          AND status = 'active'
                        GROUP BY context_type
                        """
                    ),
                    {"user_id": user_id},
                )
            ).mappings().all()

            by_access_rows = (
                await session.execute(
                    text(
                        """
                        SELECT access_level, COUNT(*) AS count
                        FROM context_entries
                        WHERE user_id = :user_id
                          AND status = 'active'
                        GROUP BY access_level
                        """
                    ),
                    {"user_id": user_id},
                )
            ).mappings().all()

            file_summary = (
                await session.execute(
                    text(
                        """
                        SELECT COALESCE(SUM(cf.size_bytes), 0) AS total_size_bytes
                        FROM context_files cf
                        JOIN context_entries ce ON ce.id = cf.context_id
                        WHERE ce.user_id = :user_id
                          AND ce.status = 'active'
                          AND cf.status != 'deleted'
                        """
                    ),
                    {"user_id": user_id},
                )
            ).mappings().first()

            system_summary = (
                await session.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM context_entries WHERE status = 'active') AS total_contexts,
                            (SELECT COUNT(*) FROM context_files WHERE status != 'deleted') AS total_files,
                            (SELECT COUNT(*) FROM context_shares) AS total_shares,
                            (SELECT COUNT(*) FROM context_versions) AS total_versions,
                            (SELECT COUNT(*) FROM context_access_log) AS access_logs_count
                        """
                    )
                )
            ).mappings().first()

            org_summary = None
            if org_id:
                org_summary = (
                    await session.execute(
                        text(
                            """
                            SELECT
                                COUNT(*) AS total_contexts,
                                COUNT(*) FILTER (WHERE access_level != 'private') AS shared_contexts
                            FROM context_entries
                            WHERE org_id = :org_id
                              AND status = 'active'
                            """
                        ),
                        {"org_id": org_id},
                    )
                ).mappings().first()

        by_type = {ctx_type.value: 0 for ctx_type in ContextType}
        for row in by_type_rows:
            by_type[row["context_type"]] = int(row["count"])

        by_access = {level.value: 0 for level in ContextAccessLevel}
        for row in by_access_rows:
            by_access[row["access_level"]] = int(row["count"])

        return {
            "user_stats": {
                "total_contexts": int(user_summary["total_contexts"] or 0),
                "by_type": by_type,
                "by_access_level": by_access,
                "total_files": int(user_summary["total_files"] or 0),
                "total_size_mb": float(file_summary["total_size_bytes"] or 0) / (1024 * 1024),
                "avg_importance": float(user_summary["avg_importance"] or 0),
                "total_accesses": int(user_summary["total_accesses"] or 0),
            },
            "org_stats": {
                "total_contexts": int(org_summary["total_contexts"] or 0),
                "shared_contexts": int(org_summary["shared_contexts"] or 0),
            } if org_summary else None,
            "system_stats": {
                "total_contexts": int(system_summary["total_contexts"] or 0),
                "total_files": int(system_summary["total_files"] or 0),
                "total_shares": int(system_summary["total_shares"] or 0),
                "total_versions": int(system_summary["total_versions"] or 0),
                "access_logs_count": int(system_summary["access_logs_count"] or 0),
            },
        }
