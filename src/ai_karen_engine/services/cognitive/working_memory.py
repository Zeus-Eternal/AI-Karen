"""
Working Memory Service - Active Context Management

This module implements working memory patterns for active context management,
including attention mechanisms, limited context windows, and real-time
context updates as user interactions and system state changes occur.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import heapq
from collections import deque
import threading


class AttentionType(Enum):
    """Types of attention mechanisms."""
    FOCUSED = "focused"  # Single task focus
    DIVIDED = "divided"  # Multiple tasks
    SELECTIVE = "selective"  # Filter relevant information
    SUSTAINED = "sustained"  # Long-term focus maintenance


class ContextPriority(Enum):
    """Priority levels for context items."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class ContextType(Enum):
    """Types of context information."""
    USER_INPUT = "user_input"
    SYSTEM_STATE = "system_state"
    CONVERSATION_HISTORY = "conversation_history"
    TASK_CONTEXT = "task_context"
    ENVIRONMENTAL = "environmental"
    MEMORY_RECALL = "memory_recall"
    ACTIVE_OPERATION = "active_operation"


@dataclass
class ContextItem:
    """Represents a single item in working memory."""
    item_id: str
    content: Any
    context_type: ContextType
    priority: ContextPriority
    
    # Temporal properties
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    
    # Attention properties
    attention_weight: float = 1.0  # 0.0 to 1.0
    access_frequency: int = 0
    relevance_score: float = 0.5  # 0.0 to 1.0
    
    # Relationships
    related_items: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_activation_level(self) -> float:
        """Calculate current activation level based on recency, frequency, and priority."""
        # Recency component (more recent = higher activation)
        age_seconds = (datetime.utcnow() - self.last_accessed).total_seconds()
        recency_factor = max(0.1, 1.0 - (age_seconds / 3600))  # Decay over 1 hour
        
        # Frequency component (more accessed = higher activation)
        frequency_factor = min(1.0, self.access_frequency / 10.0)
        
        # Priority component
        priority_factor = self.priority.value / 5.0
        
        # Attention weight
        attention_factor = self.attention_weight
        
        # Combined activation level
        activation = (
            recency_factor * 0.3 +
            frequency_factor * 0.2 +
            priority_factor * 0.3 +
            attention_factor * 0.2
        )
        
        return min(1.0, activation)
    
    def access(self):
        """Mark item as accessed, updating frequency and timestamp."""
        self.last_accessed = datetime.utcnow()
        self.access_frequency += 1
    
    def is_expired(self) -> bool:
        """Check if context item has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": self.content if isinstance(self.content, (str, int, float, bool, list, dict)) else str(self.content),
            "context_type": self.context_type.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "attention_weight": self.attention_weight,
            "access_frequency": self.access_frequency,
            "relevance_score": self.relevance_score,
            "related_items": list(self.related_items),
            "dependencies": list(self.dependencies),
            "tags": self.tags,
            "metadata": self.metadata,
            "activation_level": self.calculate_activation_level()
        }


@dataclass
class ContextWindow:
    """Represents a limited context window with capacity constraints."""
    window_id: str
    max_items: int
    max_total_size: int  # Maximum total size in characters/tokens
    
    # Current state
    items: Dict[str, ContextItem] = field(default_factory=dict)
    item_order: deque = field(default_factory=deque)  # LRU ordering
    current_size: int = 0
    
    # Window properties
    attention_type: AttentionType = AttentionType.SELECTIVE
    focus_threshold: float = 0.5  # Minimum activation for inclusion
    
    def add_item(self, item: ContextItem) -> bool:
        """Add item to context window, managing capacity constraints."""
        # Check if item already exists
        if item.item_id in self.items:
            self._update_existing_item(item)
            return True
        
        # Calculate item size
        item_size = self._calculate_item_size(item)
        
        # Make room if necessary
        if not self._make_room_for_item(item_size, item.priority):
            return False
        
        # Add item
        self.items[item.item_id] = item
        self.item_order.append(item.item_id)
        self.current_size += item_size
        
        return True
    
    def _update_existing_item(self, item: ContextItem):
        """Update existing item and move to front of LRU."""
        self.items[item.item_id] = item
        
        # Move to front of LRU order
        if item.item_id in self.item_order:
            self.item_order.remove(item.item_id)
        self.item_order.append(item.item_id)
    
    def _calculate_item_size(self, item: ContextItem) -> int:
        """Calculate approximate size of context item."""
        content_str = str(item.content)
        return len(content_str) + len(str(item.metadata))
    
    def _make_room_for_item(self, item_size: int, item_priority: ContextPriority) -> bool:
        """Make room for new item by removing low-priority or old items."""
        # Check if we have space
        if (len(self.items) < self.max_items and 
            self.current_size + item_size <= self.max_total_size):
            return True
        
        # Need to remove items - start with lowest activation items
        items_by_activation = sorted(
            self.items.values(),
            key=lambda x: (x.calculate_activation_level(), x.priority.value)
        )
        
        space_freed = 0
        items_to_remove = []
        
        for candidate in items_by_activation:
            # Don't remove items with higher priority than the new item
            if candidate.priority.value >= item_priority.value:
                continue
            
            # Don't remove critical items
            if candidate.priority == ContextPriority.CRITICAL:
                continue
            
            candidate_size = self._calculate_item_size(candidate)
            items_to_remove.append(candidate.item_id)
            space_freed += candidate_size
            
            # Check if we have enough space now
            remaining_items = len(self.items) - len(items_to_remove)
            remaining_size = self.current_size - space_freed
            
            if (remaining_items < self.max_items and 
                remaining_size + item_size <= self.max_total_size):
                break
        
        # Remove selected items
        for item_id in items_to_remove:
            self.remove_item(item_id)
        
        # Check if we successfully made room
        return (len(self.items) < self.max_items and 
                self.current_size + item_size <= self.max_total_size)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from context window."""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        item_size = self._calculate_item_size(item)
        
        del self.items[item_id]
        if item_id in self.item_order:
            self.item_order.remove(item_id)
        self.current_size -= item_size
        
        return True
    
    def get_active_items(self, min_activation: Optional[float] = None) -> List[ContextItem]:
        """Get items above activation threshold, sorted by activation level."""
        threshold = min_activation or self.focus_threshold
        
        active_items = [
            item for item in self.items.values()
            if item.calculate_activation_level() >= threshold
        ]
        
        # Sort by activation level (descending)
        active_items.sort(key=lambda x: x.calculate_activation_level(), reverse=True)
        
        return active_items
    
    def cleanup_expired_items(self):
        """Remove expired items from the window."""
        expired_items = [
            item_id for item_id, item in self.items.items()
            if item.is_expired()
        ]
        
        for item_id in expired_items:
            self.remove_item(item_id)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of context window state."""
        return {
            "window_id": self.window_id,
            "item_count": len(self.items),
            "max_items": self.max_items,
            "current_size": self.current_size,
            "max_size": self.max_total_size,
            "utilization": len(self.items) / self.max_items,
            "size_utilization": self.current_size / self.max_total_size,
            "attention_type": self.attention_type.value,
            "focus_threshold": self.focus_threshold,
            "active_items": len(self.get_active_items())
        }


class AttentionMechanism:
    """
    Implements attention mechanisms for focusing on relevant context items.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Attention configuration
        self.attention_decay_rate = 0.1  # How fast attention decays
        self.focus_boost_factor = 1.5  # Boost for focused items
        self.relevance_threshold = 0.3  # Minimum relevance for attention
        
        # Attention state
        self.current_focus: Optional[str] = None  # Currently focused item
        self.attention_weights: Dict[str, float] = {}  # item_id -> weight
        self.attention_history: List[Tuple[str, datetime]] = []  # Focus history
    
    def focus_on_item(self, item_id: str, boost_factor: float = None):
        """Focus attention on a specific item."""
        boost = boost_factor or self.focus_boost_factor
        
        # Set current focus
        self.current_focus = item_id
        
        # Boost attention weight
        self.attention_weights[item_id] = min(1.0, 
            self.attention_weights.get(item_id, 0.5) + boost
        )
        
        # Record in history
        self.attention_history.append((item_id, datetime.utcnow()))
        
        # Limit history size
        if len(self.attention_history) > 100:
            self.attention_history = self.attention_history[-100:]
        
        self.logger.debug(f"Focused attention on item {item_id}")
    
    def shift_attention(self, from_item: str, to_item: str):
        """Shift attention from one item to another."""
        # Reduce attention on previous item
        if from_item in self.attention_weights:
            self.attention_weights[from_item] *= 0.7
        
        # Focus on new item
        self.focus_on_item(to_item)
        
        self.logger.debug(f"Shifted attention from {from_item} to {to_item}")
    
    def update_attention_weights(self, context_items: Dict[str, ContextItem]):
        """Update attention weights based on item relevance and recency."""
        current_time = datetime.utcnow()
        
        for item_id, item in context_items.items():
            # Calculate base attention weight
            base_weight = item.relevance_score
            
            # Apply recency boost
            age_seconds = (current_time - item.last_accessed).total_seconds()
            recency_boost = max(0.1, 1.0 - (age_seconds / 1800))  # 30-minute window
            
            # Apply priority boost
            priority_boost = item.priority.value / 5.0
            
            # Calculate final weight
            final_weight = base_weight * recency_boost * priority_boost
            
            # Apply focus boost if this is the focused item
            if item_id == self.current_focus:
                final_weight *= self.focus_boost_factor
            
            # Update attention weight
            self.attention_weights[item_id] = min(1.0, final_weight)
            
            # Update item's attention weight
            item.attention_weight = self.attention_weights[item_id]
        
        # Decay attention weights over time
        self._decay_attention_weights()
    
    def _decay_attention_weights(self):
        """Apply decay to attention weights over time."""
        for item_id in list(self.attention_weights.keys()):
            self.attention_weights[item_id] *= (1.0 - self.attention_decay_rate)
            
            # Remove very low weights
            if self.attention_weights[item_id] < 0.01:
                del self.attention_weights[item_id]
    
    def get_attention_summary(self) -> Dict[str, Any]:
        """Get summary of current attention state."""
        return {
            "current_focus": self.current_focus,
            "active_attention_items": len(self.attention_weights),
            "attention_history_length": len(self.attention_history),
            "recent_focus_changes": len([
                h for h in self.attention_history 
                if (datetime.utcnow() - h[1]).total_seconds() < 300
            ])
        }


class WorkingMemoryService:
    """
    Service for managing working memory with attention mechanisms,
    limited context windows, and real-time context updates.
    """
    
    def __init__(self, max_context_items: int = 50, max_context_size: int = 100000):
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_context_items = max_context_items
        self.max_context_size = max_context_size
        self.context_cleanup_interval = 60  # seconds
        self.attention_update_interval = 10  # seconds
        
        # Core components
        self.context_window = ContextWindow(
            window_id="main_context",
            max_items=max_context_items,
            max_total_size=max_context_size
        )
        
        self.attention_mechanism = AttentionMechanism()
        
        # Active tasks and operations
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_contexts: Dict[str, str] = {}  # task_id -> context_window_id
        
        # Context change listeners
        self.context_listeners: List[Callable[[str, ContextItem], None]] = []
        
        # Real-time update tracking
        self.pending_updates: deque = deque()
        self.update_lock = threading.Lock()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for maintenance."""
        asyncio.create_task(self._context_cleanup_loop())
        asyncio.create_task(self._attention_update_loop())
        asyncio.create_task(self._process_pending_updates())
    
    async def _context_cleanup_loop(self):
        """Background task for cleaning up expired context items."""
        while True:
            try:
                await asyncio.sleep(self.context_cleanup_interval)
                await self.cleanup_expired_context()
            except Exception as e:
                self.logger.error(f"Error in context cleanup loop: {e}")
    
    async def _attention_update_loop(self):
        """Background task for updating attention weights."""
        while True:
            try:
                await asyncio.sleep(self.attention_update_interval)
                await self.update_attention_weights()
            except Exception as e:
                self.logger.error(f"Error in attention update loop: {e}")
    
    async def _process_pending_updates(self):
        """Process pending real-time updates."""
        while True:
            try:
                if self.pending_updates:
                    with self.update_lock:
                        update = self.pending_updates.popleft()
                    
                    await self._apply_context_update(update)
                else:
                    await asyncio.sleep(0.1)  # Short sleep when no updates
            except Exception as e:
                self.logger.error(f"Error processing pending updates: {e}")
    
    async def add_context_item(
        self,
        content: Any,
        context_type: ContextType,
        priority: ContextPriority = ContextPriority.MEDIUM,
        expires_in: Optional[timedelta] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        related_items: Optional[Set[str]] = None
    ) -> str:
        """Add a new context item to working memory."""
        try:
            item_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Create context item
            item = ContextItem(
                item_id=item_id,
                content=content,
                context_type=context_type,
                priority=priority,
                created_at=current_time,
                last_accessed=current_time,
                expires_at=current_time + expires_in if expires_in else None,
                tags=tags or [],
                metadata=metadata or {},
                related_items=related_items or set()
            )
            
            # Calculate initial relevance score
            item.relevance_score = await self._calculate_relevance_score(item)
            
            # Add to context window
            success = self.context_window.add_item(item)
            
            if success:
                # Update attention if this is high priority
                if priority.value >= 4:
                    self.attention_mechanism.focus_on_item(item_id)
                
                # Notify listeners
                await self._notify_context_listeners("added", item)
                
                self.logger.debug(f"Added context item {item_id} of type {context_type.value}")
                return item_id
            else:
                self.logger.warning(f"Failed to add context item - capacity constraints")
                return None
        
        except Exception as e:
            self.logger.error(f"Error adding context item: {e}")
            return None
    
    async def update_context_item(
        self,
        item_id: str,
        content: Optional[Any] = None,
        priority: Optional[ContextPriority] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing context item."""
        try:
            if item_id not in self.context_window.items:
                return False
            
            item = self.context_window.items[item_id]
            
            # Update fields
            if content is not None:
                item.content = content
            if priority is not None:
                item.priority = priority
            if tags is not None:
                item.tags = tags
            if metadata is not None:
                item.metadata.update(metadata)
            
            # Mark as accessed
            item.access()
            
            # Recalculate relevance
            item.relevance_score = await self._calculate_relevance_score(item)
            
            # Update attention if priority changed
            if priority and priority.value >= 4:
                self.attention_mechanism.focus_on_item(item_id)
            
            # Notify listeners
            await self._notify_context_listeners("updated", item)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating context item {item_id}: {e}")
            return False
    
    async def remove_context_item(self, item_id: str) -> bool:
        """Remove a context item from working memory."""
        try:
            if item_id not in self.context_window.items:
                return False
            
            item = self.context_window.items[item_id]
            
            # Remove from context window
            success = self.context_window.remove_item(item_id)
            
            if success:
                # Remove from attention
                if item_id in self.attention_mechanism.attention_weights:
                    del self.attention_mechanism.attention_weights[item_id]
                
                # Clear focus if this was the focused item
                if self.attention_mechanism.current_focus == item_id:
                    self.attention_mechanism.current_focus = None
                
                # Notify listeners
                await self._notify_context_listeners("removed", item)
                
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Error removing context item {item_id}: {e}")
            return False
    
    async def get_context_item(self, item_id: str) -> Optional[ContextItem]:
        """Get a specific context item."""
        if item_id in self.context_window.items:
            item = self.context_window.items[item_id]
            item.access()  # Mark as accessed
            return item
        return None
    
    async def get_active_context(
        self,
        context_types: Optional[List[ContextType]] = None,
        min_priority: Optional[ContextPriority] = None,
        max_items: Optional[int] = None
    ) -> List[ContextItem]:
        """Get currently active context items based on attention and filters."""
        try:
            # Get active items from context window
            active_items = self.context_window.get_active_items()
            
            # Apply filters
            if context_types:
                active_items = [
                    item for item in active_items 
                    if item.context_type in context_types
                ]
            
            if min_priority:
                active_items = [
                    item for item in active_items 
                    if item.priority.value >= min_priority.value
                ]
            
            # Limit number of items
            if max_items:
                active_items = active_items[:max_items]
            
            # Mark items as accessed
            for item in active_items:
                item.access()
            
            return active_items
        
        except Exception as e:
            self.logger.error(f"Error getting active context: {e}")
            return []
    
    async def focus_on_context(self, item_id: str) -> bool:
        """Focus attention on a specific context item."""
        try:
            if item_id not in self.context_window.items:
                return False
            
            # Focus attention
            self.attention_mechanism.focus_on_item(item_id)
            
            # Mark item as accessed
            item = self.context_window.items[item_id]
            item.access()
            
            # Boost priority temporarily
            if item.priority.value < 4:
                item.priority = ContextPriority.HIGH
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error focusing on context {item_id}: {e}")
            return False
    
    async def start_task_context(
        self,
        task_id: str,
        task_description: str,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Start a new task context for focused work."""
        try:
            # Create task record
            self.active_tasks[task_id] = {
                "description": task_description,
                "started_at": datetime.utcnow(),
                "context_items": [],
                "status": "active"
            }
            
            # Add task context item
            task_context_id = await self.add_context_item(
                content=f"Active Task: {task_description}",
                context_type=ContextType.TASK_CONTEXT,
                priority=ContextPriority.HIGH,
                tags=["task", task_id],
                metadata={"task_id": task_id}
            )
            
            if task_context_id:
                self.active_tasks[task_id]["context_items"].append(task_context_id)
                
                # Focus on task
                await self.focus_on_context(task_context_id)
                
                # Add initial context items
                if initial_context:
                    for ctx_data in initial_context:
                        ctx_id = await self.add_context_item(
                            content=ctx_data.get("content"),
                            context_type=ContextType(ctx_data.get("type", "task_context")),
                            priority=ContextPriority(ctx_data.get("priority", 3)),
                            tags=["task", task_id] + ctx_data.get("tags", []),
                            metadata={"task_id": task_id}
                        )
                        if ctx_id:
                            self.active_tasks[task_id]["context_items"].append(ctx_id)
                
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Error starting task context {task_id}: {e}")
            return False
    
    async def end_task_context(self, task_id: str) -> bool:
        """End a task context and clean up associated items."""
        try:
            if task_id not in self.active_tasks:
                return False
            
            task = self.active_tasks[task_id]
            
            # Remove task context items
            for item_id in task["context_items"]:
                await self.remove_context_item(item_id)
            
            # Mark task as completed
            task["status"] = "completed"
            task["completed_at"] = datetime.utcnow()
            
            # Remove from active tasks
            del self.active_tasks[task_id]
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error ending task context {task_id}: {e}")
            return False
    
    async def switch_task_context(self, from_task: str, to_task: str) -> bool:
        """Switch focus between task contexts."""
        try:
            # Validate tasks exist
            if to_task not in self.active_tasks:
                return False
            
            # Reduce attention on previous task items
            if from_task in self.active_tasks:
                for item_id in self.active_tasks[from_task]["context_items"]:
                    if item_id in self.attention_mechanism.attention_weights:
                        self.attention_mechanism.attention_weights[item_id] *= 0.5
            
            # Focus on new task items
            for item_id in self.active_tasks[to_task]["context_items"]:
                self.attention_mechanism.focus_on_item(item_id, boost_factor=1.2)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error switching task context: {e}")
            return False
    
    async def queue_context_update(self, update_data: Dict[str, Any]):
        """Queue a real-time context update for processing."""
        with self.update_lock:
            self.pending_updates.append(update_data)
    
    async def _apply_context_update(self, update_data: Dict[str, Any]):
        """Apply a real-time context update."""
        try:
            update_type = update_data.get("type")
            
            if update_type == "user_input":
                await self._handle_user_input_update(update_data)
            elif update_type == "system_state":
                await self._handle_system_state_update(update_data)
            elif update_type == "operation_status":
                await self._handle_operation_status_update(update_data)
            
        except Exception as e:
            self.logger.error(f"Error applying context update: {e}")
    
    async def _handle_user_input_update(self, update_data: Dict[str, Any]):
        """Handle user input context updates."""
        content = update_data.get("content")
        if content:
            await self.add_context_item(
                content=content,
                context_type=ContextType.USER_INPUT,
                priority=ContextPriority.HIGH,
                expires_in=timedelta(minutes=30),
                tags=["user_input", "recent"],
                metadata=update_data.get("metadata", {})
            )
    
    async def _handle_system_state_update(self, update_data: Dict[str, Any]):
        """Handle system state context updates."""
        state_info = update_data.get("state")
        if state_info:
            await self.add_context_item(
                content=state_info,
                context_type=ContextType.SYSTEM_STATE,
                priority=ContextPriority.MEDIUM,
                expires_in=timedelta(minutes=10),
                tags=["system_state"],
                metadata=update_data.get("metadata", {})
            )
    
    async def _handle_operation_status_update(self, update_data: Dict[str, Any]):
        """Handle active operation status updates."""
        operation_info = update_data.get("operation")
        if operation_info:
            await self.add_context_item(
                content=operation_info,
                context_type=ContextType.ACTIVE_OPERATION,
                priority=ContextPriority.HIGH,
                expires_in=timedelta(hours=1),
                tags=["operation", "active"],
                metadata=update_data.get("metadata", {})
            )
    
    async def _calculate_relevance_score(self, item: ContextItem) -> float:
        """Calculate relevance score for a context item."""
        try:
            base_score = 0.5
            
            # Priority boost
            priority_boost = item.priority.value / 5.0
            
            # Type-based relevance
            type_relevance = {
                ContextType.USER_INPUT: 0.9,
                ContextType.TASK_CONTEXT: 0.8,
                ContextType.ACTIVE_OPERATION: 0.7,
                ContextType.SYSTEM_STATE: 0.6,
                ContextType.CONVERSATION_HISTORY: 0.5,
                ContextType.MEMORY_RECALL: 0.4,
                ContextType.ENVIRONMENTAL: 0.3
            }
            
            type_score = type_relevance.get(item.context_type, 0.5)
            
            # Recency boost
            age_minutes = (datetime.utcnow() - item.created_at).total_seconds() / 60
            recency_score = max(0.1, 1.0 - (age_minutes / 60))  # Decay over 1 hour
            
            # Combined score
            relevance = (base_score + priority_boost + type_score + recency_score) / 4
            
            return min(1.0, relevance)
        
        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.5
    
    async def update_attention_weights(self):
        """Update attention weights for all context items."""
        try:
            self.attention_mechanism.update_attention_weights(
                self.context_window.items
            )
        except Exception as e:
            self.logger.error(f"Error updating attention weights: {e}")
    
    async def cleanup_expired_context(self):
        """Clean up expired context items."""
        try:
            self.context_window.cleanup_expired_items()
        except Exception as e:
            self.logger.error(f"Error cleaning up expired context: {e}")
    
    def add_context_listener(self, listener: Callable[[str, ContextItem], None]):
        """Add a listener for context changes."""
        self.context_listeners.append(listener)
    
    def remove_context_listener(self, listener: Callable[[str, ContextItem], None]):
        """Remove a context change listener."""
        if listener in self.context_listeners:
            self.context_listeners.remove(listener)
    
    async def _notify_context_listeners(self, event_type: str, item: ContextItem):
        """Notify all context listeners of changes."""
        for listener in self.context_listeners:
            try:
                listener(event_type, item)
            except Exception as e:
                self.logger.error(f"Error notifying context listener: {e}")
    
    async def get_working_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of working memory state."""
        try:
            context_summary = self.context_window.get_summary()
            attention_summary = self.attention_mechanism.get_attention_summary()
            
            return {
                "context_window": context_summary,
                "attention_mechanism": attention_summary,
                "active_tasks": len(self.active_tasks),
                "pending_updates": len(self.pending_updates),
                "context_listeners": len(self.context_listeners),
                "memory_utilization": {
                    "items": f"{context_summary['item_count']}/{context_summary['max_items']}",
                    "size": f"{context_summary['current_size']}/{context_summary['max_size']}",
                    "utilization_percent": round(context_summary['utilization'] * 100, 1)
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error getting working memory summary: {e}")
            return {}