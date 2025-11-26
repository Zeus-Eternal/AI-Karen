"""
Agent Memory Service

This service provides memory capabilities for agents, including short-term memory,
long-term memory, and memory management across agent sessions.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import json
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Enumeration of memory types."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    id: str
    agent_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    timestamp: datetime
    ttl: Optional[int] = None  # Time to live in seconds
    importance: float = 0.5  # Importance score (0.0 to 1.0)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class MemoryQuery:
    """Represents a query for memory entries."""
    agent_id: str
    memory_type: Optional[MemoryType] = None
    tags: Optional[List[str]] = None
    content_filter: Optional[Dict[str, Any]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    limit: int = 100
    offset: int = 0
    sort_by: str = "timestamp"
    sort_desc: bool = True


class AgentMemory:
    """
    Provides memory capabilities for agents.
    
    This class is responsible for:
    - Storing and retrieving memory entries
    - Managing different types of memory
    - Handling memory expiration and cleanup
    - Providing memory search and query capabilities
    """
    
    def __init__(self, max_entries: int = 10000):
        self._max_entries = max_entries
        self._memory_entries: Dict[str, MemoryEntry] = {}
        self._agent_memories: Dict[str, List[str]] = {}  # agent_id -> list of memory entry IDs
        
        # Indexes for faster querying
        self._memory_type_index: Dict[MemoryType, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
    
    def store_memory(self, memory_entry: MemoryEntry) -> str:
        """
        Store a memory entry.
        
        Args:
            memory_entry: The memory entry to store
            
        Returns:
            The ID of the stored memory entry
        """
        # Check if we need to make room
        if len(self._memory_entries) >= self._max_entries:
            self._cleanup_old_entries()
        
        # Store memory entry
        self._memory_entries[memory_entry.id] = memory_entry
        
        # Update agent memory index
        if memory_entry.agent_id not in self._agent_memories:
            self._agent_memories[memory_entry.agent_id] = []
        self._agent_memories[memory_entry.agent_id].append(memory_entry.id)
        
        # Update memory type index
        if memory_entry.memory_type not in self._memory_type_index:
            self._memory_type_index[memory_entry.memory_type] = []
        self._memory_type_index[memory_entry.memory_type].append(memory_entry.id)
        
        # Update tag index
        if memory_entry.tags:
            for tag in memory_entry.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(memory_entry.id)
        
        logger.debug(f"Stored memory entry {memory_entry.id} for agent {memory_entry.agent_id}")
        return memory_entry.id
    
    def create_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        content: Dict[str, Any],
        ttl: Optional[int] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create and store a new memory entry.
        
        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            content: Content of the memory
            ttl: Time to live in seconds
            importance: Importance score (0.0 to 1.0)
            tags: List of tags for the memory
            metadata: Additional metadata
            
        Returns:
            The ID of the created memory entry
        """
        memory_entry = MemoryEntry(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            timestamp=datetime.now(),
            ttl=ttl,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        return self.store_memory(memory_entry)
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get a memory entry by ID.
        
        Args:
            memory_id: ID of the memory entry
            
        Returns:
            The memory entry or None if not found
        """
        memory_entry = self._memory_entries.get(memory_id)
        
        # Check if memory has expired
        if memory_entry and self._is_expired(memory_entry):
            self._remove_memory(memory_id)
            return None
        
        return memory_entry
    
    def query_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Query memory entries based on the query parameters.
        
        Args:
            query: The query parameters
            
        Returns:
            List of matching memory entries
        """
        # Start with all memory entries for the agent
        candidate_ids = set(self._agent_memories.get(query.agent_id, []))
        
        # Filter by memory type
        if query.memory_type:
            type_ids = set(self._memory_type_index.get(query.memory_type, []))
            candidate_ids = candidate_ids.intersection(type_ids)
        
        # Filter by tags
        if query.tags:
            for tag in query.tags:
                if tag in self._tag_index:
                    tag_ids = set(self._tag_index[tag])
                    candidate_ids = candidate_ids.intersection(tag_ids)
                else:
                    # No memories with this tag
                    candidate_ids = set()
                    break
        
        # Get memory entries
        memories = []
        for memory_id in candidate_ids:
            memory_entry = self._memory_entries.get(memory_id)
            if memory_entry and not self._is_expired(memory_entry):
                # Apply content filter if specified
                if query.content_filter:
                    match = True
                    for key, value in query.content_filter.items():
                        if key not in memory_entry.content or memory_entry.content[key] != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # Apply time range filter if specified
                if query.time_range:
                    start_time, end_time = query.time_range
                    if memory_entry.timestamp < start_time or memory_entry.timestamp > end_time:
                        continue
                
                memories.append(memory_entry)
        
        # Sort memories
        if query.sort_by == "timestamp":
            memories.sort(key=lambda m: m.timestamp, reverse=query.sort_desc)
        elif query.sort_by == "importance":
            memories.sort(key=lambda m: m.importance, reverse=query.sort_desc)
        
        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return memories[start_idx:end_idx]
    
    def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """
        Get all memories for an agent, optionally filtered by memory type.
        
        Args:
            agent_id: ID of the agent
            memory_type: Optional memory type filter
            limit: Maximum number of memories to return
            
        Returns:
            List of memory entries
        """
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=memory_type,
            limit=limit
        )
        return self.query_memories(query)
    
    def get_working_memory(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the working memory for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Working memory content
        """
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=MemoryType.WORKING,
            limit=1
        )
        
        memories = self.query_memories(query)
        if memories:
            return memories[0].content
        else:
            return {}
    
    def update_working_memory(self, agent_id: str, content: Dict[str, Any]) -> str:
        """
        Update the working memory for an agent.
        
        Args:
            agent_id: ID of the agent
            content: New working memory content
            
        Returns:
            ID of the updated or created memory entry
        """
        # Check if working memory already exists
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=MemoryType.WORKING,
            limit=1
        )
        
        memories = self.query_memories(query)
        if memories:
            # Update existing working memory
            memory_entry = memories[0]
            memory_entry.content = content
            memory_entry.timestamp = datetime.now()
            return memory_entry.id
        else:
            # Create new working memory
            return self.create_memory(
                agent_id=agent_id,
                memory_type=MemoryType.WORKING,
                content=content,
                importance=1.0  # Working memory is highly important
            )
    
    def clear_working_memory(self, agent_id: str) -> bool:
        """
        Clear the working memory for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if working memory was cleared, False if not found
        """
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=MemoryType.WORKING,
            limit=1
        )
        
        memories = self.query_memories(query)
        if memories:
            return self._remove_memory(memories[0].id)
        else:
            return False
    
    def consolidate_memories(self, agent_id: str) -> int:
        """
        Consolidate short-term memories into long-term memories for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Number of memories consolidated
        """
        # Get short-term memories
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=MemoryType.SHORT_TERM
        )
        
        short_term_memories = self.query_memories(query)
        
        consolidated_count = 0
        
        for memory in short_term_memories:
            # Check if memory is important enough to consolidate
            if memory.importance >= 0.7:
                # Create long-term memory
                self.create_memory(
                    agent_id=agent_id,
                    memory_type=MemoryType.LONG_TERM,
                    content=memory.content,
                    importance=memory.importance,
                    tags=memory.tags,
                    metadata=memory.metadata
                )
                
                # Remove short-term memory
                self._remove_memory(memory.id)
                
                consolidated_count += 1
        
        logger.info(f"Consolidated {consolidated_count} memories for agent {agent_id}")
        return consolidated_count
    
    def forget_memories(self, agent_id: str, memory_type: Optional[MemoryType] = None) -> int:
        """
        Forget memories for an agent, optionally filtered by memory type.
        
        Args:
            agent_id: ID of the agent
            memory_type: Optional memory type filter
            
        Returns:
            Number of memories forgotten
        """
        # Get memories to forget
        query = MemoryQuery(
            agent_id=agent_id,
            memory_type=memory_type
        )
        
        memories = self.query_memories(query)
        
        forgotten_count = 0
        for memory in memories:
            if self._remove_memory(memory.id):
                forgotten_count += 1
        
        logger.info(f"Forgot {forgotten_count} memories for agent {agent_id}")
        return forgotten_count
    
    def get_memory_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about memory usage.
        
        Args:
            agent_id: Optional agent ID to filter statistics
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_memories": len(self._memory_entries),
            "by_memory_type": {},
            "by_agent": {}
        }
        
        # Count by memory type
        for memory_type, memory_ids in self._memory_type_index.items():
            # Filter out expired memories
            valid_ids = [mid for mid in memory_ids if not self._is_expired(self._memory_entries[mid])]
            stats["by_memory_type"][memory_type.value] = len(valid_ids)
        
        # Count by agent
        for aid, memory_ids in self._agent_memories.items():
            # Filter out expired memories
            valid_ids = [mid for mid in memory_ids if not self._is_expired(self._memory_entries[mid])]
            stats["by_agent"][aid] = len(valid_ids)
        
        # Filter by agent if specified
        if agent_id:
            agent_memories = self._agent_memories.get(agent_id, [])
            stats["total_memories"] = len(agent_memories)
            
            # Filter by memory type for this agent
            agent_stats = {}
            for memory_type, memory_ids in self._memory_type_index.items():
                agent_type_ids = set(memory_ids).intersection(set(agent_memories))
                valid_ids = [mid for mid in agent_type_ids if not self._is_expired(self._memory_entries[mid])]
                agent_stats[memory_type.value] = len(valid_ids)
            
            stats["by_memory_type"] = agent_stats
        
        return stats
    
    def export_memories(self, agent_id: str, file_path: str) -> bool:
        """
        Export memories for an agent to a file.
        
        Args:
            agent_id: ID of the agent
            file_path: Path to the export file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Get all memories for the agent
            query = MemoryQuery(agent_id=agent_id)
            memories = self.query_memories(query)
            
            # Convert to dictionaries for JSON serialization
            memory_dicts = []
            for memory in memories:
                memory_dict = asdict(memory)
                # Convert datetime to string
                memory_dict["timestamp"] = memory.timestamp.isoformat()
                memory_dicts.append(memory_dict)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(memory_dicts, f, indent=2)
            
            logger.info(f"Exported {len(memories)} memories for agent {agent_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export memories for agent {agent_id}: {str(e)}")
            return False
    
    def import_memories(self, agent_id: str, file_path: str) -> int:
        """
        Import memories for an agent from a file.
        
        Args:
            agent_id: ID of the agent
            file_path: Path to the import file
            
        Returns:
            Number of memories imported
        """
        try:
            # Read from file
            with open(file_path, 'r') as f:
                memory_dicts = json.load(f)
            
            imported_count = 0
            
            for memory_dict in memory_dicts:
                # Parse datetime
                memory_dict["timestamp"] = datetime.fromisoformat(memory_dict["timestamp"])
                
                # Override agent ID
                memory_dict["agent_id"] = agent_id
                
                # Create memory entry
                memory_entry = MemoryEntry(**memory_dict)
                self.store_memory(memory_entry)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} memories for agent {agent_id} from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import memories for agent {agent_id}: {str(e)}")
            return 0
    
    def _is_expired(self, memory_entry: MemoryEntry) -> bool:
        """Check if a memory entry has expired."""
        if memory_entry.ttl is None:
            return False
        
        now = datetime.now()
        expiry_time = memory_entry.timestamp.timestamp() + memory_entry.ttl
        return now.timestamp() > expiry_time
    
    def _remove_memory(self, memory_id: str) -> bool:
        """Remove a memory entry."""
        if memory_id not in self._memory_entries:
            return False
        
        memory_entry = self._memory_entries[memory_id]
        
        # Remove from main storage
        del self._memory_entries[memory_id]
        
        # Remove from agent memory index
        if memory_entry.agent_id in self._agent_memories:
            if memory_id in self._agent_memories[memory_entry.agent_id]:
                self._agent_memories[memory_entry.agent_id].remove(memory_id)
        
        # Remove from memory type index
        if memory_entry.memory_type in self._memory_type_index:
            if memory_id in self._memory_type_index[memory_entry.memory_type]:
                self._memory_type_index[memory_entry.memory_type].remove(memory_id)
        
        # Remove from tag index
        if memory_entry.tags:
            for tag in memory_entry.tags:
                if tag in self._tag_index:
                    if memory_id in self._tag_index[tag]:
                        self._tag_index[tag].remove(memory_id)
        
        logger.debug(f"Removed memory entry {memory_id}")
        return True
    
    def _cleanup_old_entries(self) -> None:
        """Remove old or expired memory entries to make room."""
        # Get all memory entries sorted by importance and timestamp
        memories = list(self._memory_entries.values())
        
        # Sort by importance (ascending) and then by timestamp (ascending)
        memories.sort(key=lambda m: (m.importance, m.timestamp))
        
        # Remove the least important entries until we're under the limit
        removed_count = 0
        while len(self._memory_entries) >= self._max_entries and memories:
            memory_entry = memories.pop(0)
            if self._remove_memory(memory_entry.id):
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old memory entries")