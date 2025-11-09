"""
Production Chat Memory System
Unified Redis hot storage + Vector DB semantic memory with automatic summarization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import redis
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ai_karen_engine.chat.summarizer import summarize_conversation
from ai_karen_engine.core.milvus_client import recall_vectors, store_vector
from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.core.embedding_manager import record_metric
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.database.client import get_db_session
from ai_karen_engine.database.models import ChatMemory
from cachetools import TTLCache

logger = get_logger(__name__)


class ProductionChatMemory:
    """Production chat memory system with Redis + Vector DB"""

    def __init__(self):
        self.redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url, max_connections=settings.chat_memory.redis_pool_size
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        self._semantic_cache: TTLCache[
            Tuple[str, str, Optional[str]], List[Dict[str, Any]]
        ] = TTLCache(
            maxsize=settings.chat_memory.cache_maxsize,
            ttl=settings.chat_memory.cache_ttl_seconds,
        )

    async def store_turn(
        self,
        chat_id: str,
        user_id: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store a chat turn in both Redis and vector DB"""

        try:
            # Get or create chat memory configuration
            chat_config = await self._get_chat_config(user_id, chat_id)

            # 1. Store turn in Redis hot storage
            turns_key = f"chat:{user_id}:{chat_id}:turns"
            summary_key = f"chat:{user_id}:{chat_id}:summary"

            turn_data = {
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            # Add to Redis list
            self.redis_client.rpush(turns_key, json.dumps(turn_data))
            self.redis_client.expire(
                turns_key, timedelta(days=chat_config.short_term_days)
            )

            # 2. Store in vector DB for semantic recall
            vector_text = f"User: {prompt}\nAssistant: {response}"
            vector_metadata = {
                "chat_id": chat_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "turn_type": "conversation",
                **(metadata or {}),
            }

            await store_vector(
                user_id=user_id, text=vector_text, metadata=vector_metadata
            )

            # 3. Check if summarization is needed
            current_length = self.redis_client.llen(turns_key)
            await self._update_chat_stats(user_id, chat_id, current_length)

            if current_length > chat_config.tail_turns:
                await self._summarize_if_needed(
                    user_id, chat_id, turns_key, summary_key, chat_config
                )

            logger.info(f"Stored chat turn for user {user_id}, chat {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store chat turn: {e}")
            return False

    async def get_chat_context(
        self,
        chat_id: str,
        user_id: str,
        include_summary: bool = True,
        max_turns: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get chat context from Redis hot storage"""

        turns_key = f"chat:{user_id}:{chat_id}:turns"
        summary_key = f"chat:{user_id}:{chat_id}:summary"

        # Get recent turns from Redis
        raw_turns = self.redis_client.lrange(turns_key, 0, -1)
        turns = [json.loads(turn) for turn in raw_turns]

        if max_turns:
            turns = turns[-max_turns:]

        context = {
            "chat_id": chat_id,
            "user_id": user_id,
            "turns": turns,
            "total_turns": len(turns),
        }

        # Get summary if requested
        if include_summary:
            summary_data = self.redis_client.get(summary_key)
            if summary_data:
                context["summary"] = summary_data.decode("utf-8")

        return context

    async def semantic_search(
        self,
        user_id: str,
        query: str,
        chat_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search chat history using vector similarity"""

        try:
            # Prepare filter for vector search
            vector_filter = {"user_id": user_id}
            if chat_id:
                vector_filter["chat_id"] = chat_id

            cache_key = (user_id, query, chat_id)
            cached = self._semantic_cache.get(cache_key)
            if cached is not None:
                record_metric("semantic_search_cache_hit", 1)
                self._record_pool_metrics()
                return cached

            record_metric("semantic_search_cache_miss", 1)
            results = await recall_vectors(
                user_id=user_id, query=query, top_k=limit, filter=vector_filter
            )

            # Filter by similarity threshold
            filtered_results = [
                result
                for result in results
                if result.get("similarity", 0) >= similarity_threshold
            ]

            self._semantic_cache[cache_key] = filtered_results
            logger.info(
                f"Semantic search returned {len(filtered_results)} results for user {user_id}"
            )
            self._record_pool_metrics()
            return filtered_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _record_pool_metrics(self) -> None:
        try:
            used = self.redis_pool._created_connections - len(  # type: ignore[attr-defined]
                self.redis_pool._available_connections  # type: ignore[attr-defined]
            )
            utilization = used / self.redis_pool.max_connections
            record_metric("redis_pool_utilization", utilization)
        except Exception:
            pass
        try:
            from ai_karen_engine.core.milvus_client import (
                _vector_stores,  # type: ignore[import-not-found]
            )

            for store in _vector_stores.values():
                util = getattr(store, "pool_utilization", lambda: 0.0)()
                record_metric("milvus_pool_utilization", util)
        except Exception:
            pass

    async def get_chat_reference(
        self, chat_id: str, user_id: str, query: Optional[str] = None, limit: int = 5
    ) -> Dict[str, Any]:
        """Get chat reference for context injection"""

        # If no query, return recent context
        if not query:
            return await self.get_chat_context(chat_id, user_id, include_summary=True)

        # Otherwise, perform semantic search
        semantic_results = await self.semantic_search(
            user_id=user_id, query=query, chat_id=chat_id, limit=limit
        )

        # Also get recent context
        recent_context = await self.get_chat_context(chat_id, user_id, max_turns=3)

        return {
            "chat_id": chat_id,
            "user_id": user_id,
            "query": query,
            "semantic_results": semantic_results,
            "recent_context": recent_context,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def cleanup_expired_memory(self, user_id: str) -> Dict[str, int]:
        """Clean up expired memory for a user"""

        cleaned_stats = {
            "redis_keys_cleaned": 0,
            "vector_entries_cleaned": 0,
            "chat_configs_updated": 0,
        }

        try:
            with get_db_session() as db:
                # Get all chat memories for user
                chat_memories = (
                    db.query(ChatMemory).filter(ChatMemory.user_id == user_id).all()
                )

                for chat_memory in chat_memories:
                    # Clean Redis keys
                    turns_key = f"chat:{user_id}:{chat_memory.chat_id}:turns"
                    summary_key = f"chat:{user_id}:{chat_memory.chat_id}:summary"

                    if self.redis_client.exists(turns_key):
                        # Check if should be expired based on user settings
                        ttl = self.redis_client.ttl(turns_key)
                        if ttl <= 0:
                            self.redis_client.delete(turns_key)
                            cleaned_stats["redis_keys_cleaned"] += 1

                    if self.redis_client.exists(summary_key):
                        ttl = self.redis_client.ttl(summary_key)
                        if ttl <= 0:
                            self.redis_client.delete(summary_key)
                            cleaned_stats["redis_keys_cleaned"] += 1

                    # Update chat config if needed
                    if chat_memory.updated_at < datetime.utcnow() - timedelta(days=1):
                        chat_memory.updated_at = datetime.utcnow()
                        cleaned_stats["chat_configs_updated"] += 1

                db.commit()

            logger.info(f"Cleaned up memory for user {user_id}: {cleaned_stats}")
            return cleaned_stats

        except Exception as e:
            logger.error(f"Memory cleanup failed for user {user_id}: {e}")
            return cleaned_stats

    async def update_user_memory_settings(
        self, user_id: str, chat_id: str, settings_update: Dict[str, Any]
    ) -> bool:
        """Update user's memory settings for a specific chat"""

        try:
            with get_db_session() as db:
                chat_memory = (
                    db.query(ChatMemory)
                    .filter(
                        and_(
                            ChatMemory.user_id == user_id, ChatMemory.chat_id == chat_id
                        )
                    )
                    .first()
                )

                if not chat_memory:
                    # Create new chat memory config
                    chat_memory = ChatMemory(user_id=user_id, chat_id=chat_id)
                    db.add(chat_memory)

                # Update settings
                if "short_term_days" in settings_update:
                    chat_memory.short_term_days = settings_update["short_term_days"]
                if "long_term_days" in settings_update:
                    chat_memory.long_term_days = settings_update["long_term_days"]
                if "tail_turns" in settings_update:
                    chat_memory.tail_turns = settings_update["tail_turns"]
                if "summarize_threshold_tokens" in settings_update:
                    chat_memory.summarize_threshold_tokens = settings_update[
                        "summarize_threshold_tokens"
                    ]

                chat_memory.updated_at = datetime.utcnow()
                db.commit()

                # Update Redis TTLs if needed
                await self._update_redis_ttls(user_id, chat_id, chat_memory)

                logger.info(
                    f"Updated memory settings for user {user_id}, chat {chat_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to update memory settings: {e}")
            return False

    async def _get_chat_config(self, user_id: str, chat_id: str) -> ChatMemory:
        """Get or create chat memory configuration"""

        with get_db_session() as db:
            chat_memory = (
                db.query(ChatMemory)
                .filter(
                    and_(ChatMemory.user_id == user_id, ChatMemory.chat_id == chat_id)
                )
                .first()
            )

            if not chat_memory:
                # Create with default settings
                chat_memory = ChatMemory(
                    user_id=user_id,
                    chat_id=chat_id,
                    short_term_days=settings.chat_memory.short_term_days,
                    long_term_days=settings.chat_memory.long_term_days,
                    tail_turns=settings.chat_memory.tail_turns,
                    summarize_threshold_tokens=settings.chat_memory.summarize_threshold_tokens,
                )
                db.add(chat_memory)
                db.commit()
                db.refresh(chat_memory)

            return chat_memory

    async def _summarize_if_needed(
        self,
        user_id: str,
        chat_id: str,
        turns_key: str,
        summary_key: str,
        chat_config: ChatMemory,
    ):
        """Summarize conversation if needed"""

        try:
            # Get all turns
            raw_turns = self.redis_client.lrange(turns_key, 0, -1)
            all_turns = [json.loads(turn) for turn in raw_turns]

            if len(all_turns) <= chat_config.tail_turns:
                return

            # Split into head (to summarize) and tail (to keep)
            head_turns = all_turns[: -chat_config.tail_turns]
            tail_turns = all_turns[-chat_config.tail_turns :]

            # Generate summary
            summary = await summarize_conversation(head_turns)

            # Store summary in Redis
            self.redis_client.setex(
                summary_key, timedelta(days=chat_config.short_term_days), summary
            )

            # Store summary in vector DB for semantic search
            await store_vector(
                user_id=user_id,
                text=f"Conversation Summary: {summary}",
                metadata={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "turn_type": "summary",
                    "summarized_turns": len(head_turns),
                },
            )

            # Replace Redis turns with just the tail
            self.redis_client.delete(turns_key)
            for turn in tail_turns:
                self.redis_client.rpush(turns_key, json.dumps(turn))
            self.redis_client.expire(
                turns_key, timedelta(days=chat_config.short_term_days)
            )

            # Update chat memory stats
            with get_db_session() as db:
                chat_memory = (
                    db.query(ChatMemory)
                    .filter(
                        and_(
                            ChatMemory.user_id == user_id, ChatMemory.chat_id == chat_id
                        )
                    )
                    .first()
                )

                if chat_memory:
                    chat_memory.last_summarized_at = datetime.utcnow()
                    chat_memory.updated_at = datetime.utcnow()
                    db.commit()

            logger.info(f"Summarized {len(head_turns)} turns for chat {chat_id}")

        except Exception as e:
            logger.error(f"Summarization failed: {e}")

    async def _update_chat_stats(self, user_id: str, chat_id: str, turn_count: int):
        """Update chat statistics"""

        try:
            with get_db_session() as db:
                chat_memory = (
                    db.query(ChatMemory)
                    .filter(
                        and_(
                            ChatMemory.user_id == user_id, ChatMemory.chat_id == chat_id
                        )
                    )
                    .first()
                )

                if chat_memory:
                    chat_memory.total_turns = turn_count
                    chat_memory.updated_at = datetime.utcnow()
                    db.commit()

        except Exception as e:
            logger.error(f"Failed to update chat stats: {e}")

    async def _update_redis_ttls(
        self, user_id: str, chat_id: str, chat_config: ChatMemory
    ):
        """Update Redis TTLs based on user settings"""

        turns_key = f"chat:{user_id}:{chat_id}:turns"
        summary_key = f"chat:{user_id}:{chat_id}:summary"

        # Update TTLs
        if self.redis_client.exists(turns_key):
            self.redis_client.expire(
                turns_key, timedelta(days=chat_config.short_term_days)
            )

        if self.redis_client.exists(summary_key):
            self.redis_client.expire(
                summary_key, timedelta(days=chat_config.short_term_days)
            )


# Global memory service instance
production_chat_memory = ProductionChatMemory()
