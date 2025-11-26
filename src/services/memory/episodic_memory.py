"""
Episodic Memory Service

This service provides episodic memory functionality for storing and retrieving
episodic events and experiences.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class EpisodicEvent:
    """An episodic memory event."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    emotional_state: Dict[str, float] = field(default_factory=dict)
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)


class EpisodicMemory:
    """
    Episodic Memory provides storage and retrieval of episodic events
    and experiences.
    
    This service maintains a timeline of events with rich metadata
    and provides various ways to retrieve and relate events.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Episodic Memory.
        
        Args:
            config: Configuration for episodic memory
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self.events: Dict[str, EpisodicEvent] = {}
        
        # Indexes
        self.timeline: List[str] = []  # Ordered by timestamp
        self.participants_index: Dict[str, List[str]] = {}
        self.tags_index: Dict[str, List[str]] = {}
        self.importance_index: List[str] = []  # Ordered by importance
    
    async def store_event(self, event: EpisodicEvent) -> str:
        """
        Store an episodic event.
        
        Args:
            event: The event to store
            
        Returns:
            The ID of the stored event
        """
        # Store the event
        self.events[event.id] = event
        
        # Update timeline
        self._update_timeline(event.id, event.timestamp)
        
        # Update participants index
        for participant in event.participants:
            if participant not in self.participants_index:
                self.participants_index[participant] = []
            self.participants_index[participant].append(event.id)
        
        # Update tags index
        for tag in event.tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            self.tags_index[tag].append(event.id)
        
        # Update importance index
        self._update_importance_index(event.id, event.importance)
        
        return event.id
    
    def _update_timeline(self, event_id: str, timestamp: datetime):
        """Update the timeline index."""
        # Find insertion point
        i = 0
        while i < len(self.timeline) and self.events[self.timeline[i]].timestamp < timestamp:
            i += 1
        
        self.timeline.insert(i, event_id)
    
    def _update_importance_index(self, event_id: str, importance: float):
        """Update the importance index."""
        # Find insertion point
        i = 0
        while (i < len(self.importance_index) and 
               self.events[self.importance_index[i]].importance > importance):
            i += 1
        
        self.importance_index.insert(i, event_id)
    
    async def get_event(self, event_id: str) -> Optional[EpisodicEvent]:
        """
        Get an episodic event by ID.
        
        Args:
            event_id: The ID of the event
            
        Returns:
            The event if found, None otherwise
        """
        return self.events.get(event_id)
    
    async def get_events_by_timeframe(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[EpisodicEvent]:
        """
        Get events within a timeframe.
        
        Args:
            start_time: Start of the timeframe
            end_time: End of the timeframe
            
        Returns:
            List of events within the timeframe
        """
        events = []
        
        for event_id in self.timeline:
            event = self.events[event_id]
            if start_time <= event.timestamp <= end_time:
                events.append(event)
        
        return events
    
    async def get_events_by_participant(
        self, 
        participant: str
    ) -> List[EpisodicEvent]:
        """
        Get events involving a participant.
        
        Args:
            participant: The participant name
            
        Returns:
            List of events involving the participant
        """
        event_ids = self.participants_index.get(participant, [])
        return [self.events[event_id] for event_id in event_ids]
    
    async def get_events_by_tag(self, tag: str) -> List[EpisodicEvent]:
        """
        Get events with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of events with the tag
        """
        event_ids = self.tags_index.get(tag, [])
        return [self.events[event_id] for event_id in event_ids]
    
    async def get_most_important(self, limit: int = 10) -> List[EpisodicEvent]:
        """
        Get the most important events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of most important events
        """
        event_ids = self.importance_index[:limit]
        return [self.events[event_id] for event_id in event_ids]
    
    async def find_related_events(
        self, 
        event_id: str, 
        limit: int = 5
    ) -> List[EpisodicEvent]:
        """
        Find events related to the given event.
        
        Args:
            event_id: The ID of the reference event
            limit: Maximum number of events to return
            
        Returns:
            List of related events
        """
        event = await self.get_event(event_id)
        if not event:
            return []
        
        # Find related events by participants and tags
        related_event_ids = set()
        
        # Add events with same participants
        for participant in event.participants:
            related_event_ids.update(self.participants_index.get(participant, []))
        
        # Add events with same tags
        for tag in event.tags:
            related_event_ids.update(self.tags_index.get(tag, []))
        
        # Remove the reference event itself
        related_event_ids.discard(event_id)
        
        # Convert to events and sort by relevance
        related_events = [self.events[eid] for eid in related_event_ids]
        
        # Simple relevance scoring based on shared participants and tags
        def relevance_score(e):
            score = 0
            # Shared participants
            shared_participants = set(e.participants) & set(event.participants)
            score += len(shared_participants) * 2
            # Shared tags
            shared_tags = set(e.tags) & set(event.tags)
            score += len(shared_tags)
            return score
        
        related_events.sort(key=relevance_score, reverse=True)
        
        return related_events[:limit]
    
    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an episodic event.
        
        Args:
            event_id: The ID of the event to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if the event was updated, False otherwise
        """
        event = await self.get_event(event_id)
        if not event:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        return True
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete an episodic event.
        
        Args:
            event_id: The ID of the event to delete
            
        Returns:
            True if the event was deleted, False otherwise
        """
        event = await self.get_event(event_id)
        if not event:
            return False
        
        # Remove from storage
        del self.events[event_id]
        
        # Remove from timeline
        if event_id in self.timeline:
            self.timeline.remove(event_id)
        
        # Remove from participants index
        for participant in event.participants:
            if participant in self.participants_index:
                if event_id in self.participants_index[participant]:
                    self.participants_index[participant].remove(event_id)
        
        # Remove from tags index
        for tag in event.tags:
            if tag in self.tags_index:
                if event_id in self.tags_index[tag]:
                    self.tags_index[tag].remove(event_id)
        
        # Remove from importance index
        if event_id in self.importance_index:
            self.importance_index.remove(event_id)
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_events": len(self.events),
            "participants_count": len(self.participants_index),
            "tags_count": len(self.tags_index),
            "timeline_span": (
                self.events[self.timeline[0]].timestamp if self.timeline else None,
                self.events[self.timeline[-1]].timestamp if self.timeline else None
            )
        }
