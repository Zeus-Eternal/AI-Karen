"""
Persistent Memory - Relational storage using existing PostgresClient

Provides persistent storage for user data and interaction history.
Uses PostgreSQL for relational data with ACID guarantees.
Integrates with existing PostgresClient infrastructure.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class UserData:
    """Represents persistent user data."""
    user_id: str
    name: Optional[str]
    age: Optional[int]
    date_of_birth: Optional[str]
    preferences: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class InteractionRecord:
    """Represents a persistent interaction record."""
    id: int
    user_id: str
    session_id: str
    query: str
    result: str
    timestamp: str
    metadata: Dict[str, Any]


class PersistentMemory:
    """
    Persistent memory using existing PostgresClient.

    Features:
    - Relational storage with ACID guarantees
    - User profile management
    - Interaction history
    - Session tracking
    - Query capabilities
    """

    def __init__(
        self,
        user_id: str,
        postgres_client: Optional[Any] = None
    ):
        self.user_id = user_id
        self.postgres_client = postgres_client

        # Determine if using fallback
        self._using_fallback = postgres_client is None

        # Fallback: in-memory storage
        self._fallback_user_data: Optional[UserData] = None
        self._fallback_interactions: List[InteractionRecord] = []
        self._fallback_interaction_id = 0

        # Metrics
        self._total_writes = 0
        self._total_reads = 0

        logger.info(f"PersistentMemory initialized for user {user_id} (fallback={self._using_fallback})")

    async def store_user_data(
        self,
        name: Optional[str] = None,
        age: Optional[int] = None,
        date_of_birth: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserData:
        """
        Store or update user data.

        Args:
            name: User's name
            age: User's age
            date_of_birth: User's date of birth (ISO format)
            preferences: User preferences
            metadata: Additional metadata

        Returns:
            UserData object
        """
        now = datetime.utcnow().isoformat()

        user_data = UserData(
            user_id=self.user_id,
            name=name,
            age=age,
            date_of_birth=date_of_birth,
            preferences=preferences or {},
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )

        if self._using_fallback:
            await self._store_user_fallback(user_data)
        else:
            await self._store_user_postgres(user_data)

        self._total_writes += 1

        logger.debug(f"Stored user data for {self.user_id}")
        return user_data

    async def _store_user_postgres(self, user_data: UserData) -> None:
        """Store user data using PostgresClient."""
        loop = asyncio.get_event_loop()

        # Store in user_profiles table (would need to ensure table exists)
        # For now, use the generic memory table
        await loop.run_in_executor(
            None,
            self.postgres_client.store,
            0,  # vector_id (placeholder)
            "",  # tenant_id
            user_data.user_id,
            "",  # session_id
            json.dumps(asdict(user_data)),  # query field used for data
            "",  # result
            int(datetime.utcnow().timestamp())
        )

    async def _store_user_fallback(self, user_data: UserData) -> None:
        """Store user data in fallback storage."""
        self._fallback_user_data = user_data

    async def get_user_data(self) -> Optional[UserData]:
        """
        Retrieve user data.

        Returns:
            UserData object or None if not found
        """
        self._total_reads += 1

        if self._using_fallback:
            return self._fallback_user_data
        else:
            return await self._get_user_postgres()

    async def _get_user_postgres(self) -> Optional[UserData]:
        """Retrieve user data from PostgreSQL."""
        loop = asyncio.get_event_loop()

        try:
            # Query user data
            results = await loop.run_in_executor(
                None,
                self.postgres_client.retrieve,
                self.user_id,
                ""  # session_id
            )

            if results:
                # Parse the first result
                data_json = results[0].get("query", "{}")
                data_dict = json.loads(data_json)
                return UserData(**data_dict)

            return None

        except Exception as e:
            logger.error(f"Error retrieving user data: {e}")
            return None

    async def store_interaction(
        self,
        session_id: str,
        query: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InteractionRecord:
        """
        Store an interaction record.

        Args:
            session_id: Session identifier
            query: User query
            result: System result
            metadata: Additional metadata

        Returns:
            InteractionRecord object
        """
        if self._using_fallback:
            interaction = await self._store_interaction_fallback(
                session_id, query, result, metadata
            )
        else:
            interaction = await self._store_interaction_postgres(
                session_id, query, result, metadata
            )

        self._total_writes += 1

        logger.debug(f"Stored interaction for session {session_id}")
        return interaction

    async def _store_interaction_postgres(
        self,
        session_id: str,
        query: str,
        result: str,
        metadata: Optional[Dict[str, Any]]
    ) -> InteractionRecord:
        """Store interaction using PostgresClient."""
        loop = asyncio.get_event_loop()

        timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

        # Use PostgresClient's store method
        await loop.run_in_executor(
            None,
            self.postgres_client.store,
            timestamp_ms,  # vector_id (use timestamp as ID)
            "",  # tenant_id
            self.user_id,
            session_id,
            query,
            result,
            timestamp_ms
        )

        return InteractionRecord(
            id=timestamp_ms,
            user_id=self.user_id,
            session_id=session_id,
            query=query,
            result=result,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )

    async def _store_interaction_fallback(
        self,
        session_id: str,
        query: str,
        result: str,
        metadata: Optional[Dict[str, Any]]
    ) -> InteractionRecord:
        """Store interaction in fallback storage."""
        self._fallback_interaction_id += 1

        interaction = InteractionRecord(
            id=self._fallback_interaction_id,
            user_id=self.user_id,
            session_id=session_id,
            query=query,
            result=result,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )

        self._fallback_interactions.append(interaction)
        return interaction

    async def get_interactions(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[InteractionRecord]:
        """
        Retrieve interaction history.

        Args:
            session_id: Filter by session ID (None for all)
            limit: Maximum number of records to return

        Returns:
            List of InteractionRecord objects
        """
        self._total_reads += 1

        if self._using_fallback:
            return await self._get_interactions_fallback(session_id, limit)
        else:
            return await self._get_interactions_postgres(session_id, limit)

    async def _get_interactions_postgres(
        self,
        session_id: Optional[str],
        limit: int
    ) -> List[InteractionRecord]:
        """Retrieve interactions from PostgreSQL."""
        loop = asyncio.get_event_loop()

        try:
            # Retrieve from PostgresClient
            results = await loop.run_in_executor(
                None,
                self.postgres_client.retrieve,
                self.user_id,
                session_id or ""
            )

            interactions = []
            for result in results[:limit]:
                interactions.append(InteractionRecord(
                    id=result.get("vector_id", 0),
                    user_id=result.get("user_id", ""),
                    session_id=result.get("session_id", ""),
                    query=result.get("query", ""),
                    result=result.get("result", ""),
                    timestamp=datetime.fromtimestamp(result.get("timestamp", 0) / 1000).isoformat(),
                    metadata={}
                ))

            return interactions

        except Exception as e:
            logger.error(f"Error retrieving interactions: {e}")
            return []

    async def _get_interactions_fallback(
        self,
        session_id: Optional[str],
        limit: int
    ) -> List[InteractionRecord]:
        """Retrieve interactions from fallback storage."""
        interactions = self._fallback_interactions

        # Filter by session if specified
        if session_id:
            interactions = [i for i in interactions if i.session_id == session_id]

        # Sort by timestamp (most recent first)
        interactions.sort(key=lambda x: x.timestamp, reverse=True)

        return interactions[:limit]

    async def delete_user_data(self) -> bool:
        """
        Delete all user data (GDPR compliance).

        Returns:
            True if successful
        """
        if self._using_fallback:
            self._fallback_user_data = None
            self._fallback_interactions = []
            logger.info(f"Deleted user data for {self.user_id} (fallback)")
            return True
        else:
            # Would need PostgresClient delete method
            logger.warning("PostgresClient delete not yet implemented")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "user_id": self.user_id,
            "using_fallback": self._using_fallback,
            "metrics": {
                "total_writes": self._total_writes,
                "total_reads": self._total_reads
            }
        }

        if self._using_fallback:
            stats["has_user_data"] = self._fallback_user_data is not None
            stats["interaction_count"] = len(self._fallback_interactions)
        else:
            stats["has_user_data"] = False  # Would need to query
            stats["interaction_count"] = 0  # Would need to query

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health check results
        """
        healthy = True
        issues = []

        # Check PostgreSQL connection
        if not self._using_fallback and self.postgres_client:
            try:
                # Test connection
                conn = self.postgres_client.conn
                if conn.closed:
                    healthy = False
                    issues.append("PostgreSQL connection closed")
            except Exception as e:
                healthy = False
                issues.append(f"PostgreSQL connection error: {e}")

        return {
            "healthy": healthy,
            "using_fallback": self._using_fallback,
            "issues": issues,
            "statistics": await self.get_statistics()
        }


__all__ = [
    "PersistentMemory",
    "UserData",
    "InteractionRecord"
]
