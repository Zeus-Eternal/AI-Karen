"""
NeuroVault Memory Types and Enhanced Data Models.
Extends existing memory types with tri-partite memory architecture.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import math

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ai_karen_engine.services.memory_service import MemoryType, WebUIMemoryEntry
else:
    # Define minimal types for runtime
    class MemoryType:
        GENERAL = "general"
        FACT = "fact"
        PREFERENCE = "preference"
        CONTEXT = "context"
        CONVERSATION = "conversation"
        INSIGHT = "insight"


class NeuroMemoryType(str, Enum):
    """Extended memory types for NeuroVault tri-partite memory architecture."""
    
    # Existing types (maintain backward compatibility)
    GENERAL = "general"
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"
    CONVERSATION = "conversation"
    INSIGHT = "insight"
    
    # New tri-partite memory types
    EPISODIC = "episodic"      # Time-stamped experiences and interactions
    SEMANTIC = "semantic"      # Distilled facts and knowledge
    PROCEDURAL = "procedural"  # Tool usage patterns and workflows
    
    @classmethod
    def get_legacy_types(cls) -> List[str]:
        """Get list of legacy memory types for backward compatibility."""
        return [
            cls.GENERAL.value,
            cls.FACT.value,
            cls.PREFERENCE.value,
            cls.CONTEXT.value,
            cls.CONVERSATION.value,
            cls.INSIGHT.value
        ]
    
    @classmethod
    def get_neuro_types(cls) -> List[str]:
        """Get list of new tri-partite memory types."""
        return [
            cls.EPISODIC.value,
            cls.SEMANTIC.value,
            cls.PROCEDURAL.value
        ]
    
    @classmethod
    def is_legacy_type(cls, memory_type: str) -> bool:
        """Check if a memory type is a legacy type."""
        return memory_type in cls.get_legacy_types()
    
    @classmethod
    def is_neuro_type(cls, memory_type: str) -> bool:
        """Check if a memory type is a new tri-partite type."""
        return memory_type in cls.get_neuro_types()
    
    @classmethod
    def from_legacy_type(cls, legacy_type) -> 'NeuroMemoryType':
        """Convert legacy MemoryType to NeuroMemoryType for compatibility."""
        # Handle both enum and string values
        if hasattr(legacy_type, 'value'):
            legacy_value = legacy_type.value
        else:
            legacy_value = str(legacy_type)
        
        # Map legacy types to NeuroMemoryType values
        legacy_mapping = {
            "general": cls.GENERAL,
            "fact": cls.FACT,
            "preference": cls.PREFERENCE,
            "context": cls.CONTEXT,
            "conversation": cls.CONVERSATION,
            "insight": cls.INSIGHT
        }
        return legacy_mapping.get(legacy_value, cls.GENERAL)
    
    def get_default_decay_lambda(self) -> float:
        """Get default decay lambda value for this memory type."""
        decay_rates = {
            # Legacy types use moderate decay
            self.GENERAL: 0.08,
            self.FACT: 0.04,
            self.PREFERENCE: 0.06,
            self.CONTEXT: 0.10,
            self.CONVERSATION: 0.12,
            self.INSIGHT: 0.05,
            
            # Tri-partite types use research-based decay rates
            self.EPISODIC: 0.12,    # Fastest decay - experiences fade quickly
            self.SEMANTIC: 0.04,    # Slowest decay - facts persist longer
            self.PROCEDURAL: 0.02   # Very slow decay - skills persist longest
        }
        return decay_rates.get(self, 0.08)


@dataclass
class NeuroMemoryEntry:
    """Enhanced memory entry with NeuroVault tri-partite memory capabilities."""
    
    # Base memory fields (from MemoryEntry and WebUIMemoryEntry)
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    ttl: Optional[int] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    similarity_score: Optional[float] = None
    
    # WebUI-specific fields
    ui_source: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_type: Optional[str] = None  # Legacy field for compatibility
    importance_score: int = 5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    ai_generated: bool = False
    user_confirmed: bool = True
    
    # NeuroVault-specific fields
    neuro_type: NeuroMemoryType = NeuroMemoryType.EPISODIC
    decay_lambda: float = 0.1
    reflection_count: int = 0
    source_memories: List[str] = field(default_factory=list)
    derived_memories: List[str] = field(default_factory=list)
    importance_decay: float = 1.0
    last_reflection: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize NeuroMemoryEntry with proper defaults."""
        super().__post_init__() if hasattr(super(), '__post_init__') else None
        
        # Set default decay lambda based on memory type
        if self.decay_lambda == 0.1:  # Only set if using default
            self.decay_lambda = self.neuro_type.get_default_decay_lambda()
        
        # Ensure backward compatibility with legacy memory_type
        if hasattr(self, 'memory_type') and self.memory_type:
            # If legacy memory_type is set, convert to neuro_type
            if isinstance(self.memory_type, MemoryType):
                self.neuro_type = NeuroMemoryType.from_legacy_type(self.memory_type)
            elif isinstance(self.memory_type, str):
                try:
                    self.neuro_type = NeuroMemoryType(self.memory_type)
                except ValueError:
                    # If conversion fails, default to EPISODIC
                    self.neuro_type = NeuroMemoryType.EPISODIC
    
    def calculate_current_importance(self, current_time: Optional[datetime] = None) -> float:
        """
        Calculate current importance score with decay applied.
        
        Args:
            current_time: Current time for decay calculation (defaults to now)
            
        Returns:
            Current importance score after applying decay
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        if not self.timestamp:
            return float(self.importance_score)
        
        # Calculate time difference in days
        if isinstance(self.timestamp, datetime):
            time_diff = (current_time - self.timestamp).total_seconds() / 86400  # Convert to days
        elif isinstance(self.timestamp, (int, float)):
            # Handle Unix timestamp (milliseconds)
            timestamp_dt = datetime.fromtimestamp(self.timestamp / 1000)
            time_diff = (current_time - timestamp_dt).total_seconds() / 86400
        elif isinstance(self.timestamp, str):
            # Handle ISO format string
            try:
                timestamp_dt = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                time_diff = (current_time - timestamp_dt).total_seconds() / 86400
            except ValueError:
                # If parsing fails, assume no decay
                return float(self.importance_score)
        else:
            # Unknown timestamp format, assume no decay
            return float(self.importance_score)
        
        # Apply exponential decay: importance * e^(-lambda * time)
        decayed_importance = self.importance_score * math.exp(-self.decay_lambda * time_diff)
        
        # Apply additional importance decay factor
        final_importance = decayed_importance * self.importance_decay
        
        return max(0.0, final_importance)  # Ensure non-negative
    
    def calculate_decay_score(self, current_time: Optional[datetime] = None) -> float:
        """
        Calculate decay score (0-1) representing how much the memory has decayed.
        
        Args:
            current_time: Current time for decay calculation (defaults to now)
            
        Returns:
            Decay score where 1.0 = no decay, 0.0 = completely decayed
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        current_importance = self.calculate_current_importance(current_time)
        original_importance = float(self.importance_score)
        
        if original_importance == 0:
            return 0.0
        
        return min(1.0, current_importance / original_importance)
    
    def is_expired(self, threshold: float = 0.1, current_time: Optional[datetime] = None) -> bool:
        """
        Check if memory has decayed below the threshold and should be considered expired.
        
        Args:
            threshold: Minimum importance threshold (default 0.1)
            current_time: Current time for decay calculation (defaults to now)
            
        Returns:
            True if memory is expired (below threshold)
        """
        current_importance = self.calculate_current_importance(current_time)
        return current_importance < threshold
    
    def needs_reflection(self, reflection_interval_days: int = 7) -> bool:
        """
        Check if memory needs reflection processing.
        
        Args:
            reflection_interval_days: Days between reflection cycles
            
        Returns:
            True if memory needs reflection
        """
        if self.neuro_type != NeuroMemoryType.EPISODIC:
            return False  # Only episodic memories need reflection
        
        if self.last_reflection is None:
            return True  # Never reflected
        
        days_since_reflection = (datetime.utcnow() - self.last_reflection).days
        return days_since_reflection >= reflection_interval_days
    
    def add_source_memory(self, source_memory_id: str) -> None:
        """Add a source memory ID to track derivation relationships."""
        if source_memory_id not in self.source_memories:
            self.source_memories.append(source_memory_id)
    
    def add_derived_memory(self, derived_memory_id: str) -> None:
        """Add a derived memory ID to track what was created from this memory."""
        if derived_memory_id not in self.derived_memories:
            self.derived_memories.append(derived_memory_id)
    
    def increment_reflection_count(self) -> None:
        """Increment reflection count and update last reflection time."""
        self.reflection_count += 1
        self.last_reflection = datetime.utcnow()
    
    def update_importance_decay(self, decay_factor: float) -> None:
        """
        Update importance decay factor based on reflection results.
        
        Args:
            decay_factor: New decay factor (0.0 to 1.0)
        """
        self.importance_decay = max(0.0, min(1.0, decay_factor))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with NeuroVault fields included."""
        # Build base dictionary from all fields
        base_dict = {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "ttl": self.ttl,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "similarity_score": self.similarity_score,
            "ui_source": self.ui_source,
            "conversation_id": self.conversation_id,
            "memory_type": self.memory_type,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "ai_generated": self.ai_generated,
            "user_confirmed": self.user_confirmed
        }
        
        # Add NeuroVault-specific fields
        neuro_dict = {
            "neuro_type": self.neuro_type.value,
            "decay_lambda": self.decay_lambda,
            "reflection_count": self.reflection_count,
            "source_memories": self.source_memories,
            "derived_memories": self.derived_memories,
            "importance_decay": self.importance_decay,
            "last_reflection": self.last_reflection.isoformat() if self.last_reflection else None,
            
            # Calculated fields
            "current_importance": self.calculate_current_importance(),
            "decay_score": self.calculate_decay_score(),
            "is_expired": self.is_expired(),
            "needs_reflection": self.needs_reflection()
        }
        
        base_dict.update(neuro_dict)
        return base_dict
    
    @classmethod
    def from_web_ui_memory(
        cls, 
        web_ui_memory,  # Accept any object with memory fields
        neuro_type: Optional[NeuroMemoryType] = None,
        decay_lambda: Optional[float] = None,
        **kwargs
    ) -> 'NeuroMemoryEntry':
        """
        Create NeuroMemoryEntry from existing WebUIMemoryEntry.
        
        Args:
            web_ui_memory: Existing WebUIMemoryEntry to convert
            neuro_type: Override neuro memory type
            decay_lambda: Override decay lambda
            **kwargs: Additional NeuroVault-specific fields
            
        Returns:
            New NeuroMemoryEntry instance
        """
        # Extract all fields from WebUIMemoryEntry
        if hasattr(web_ui_memory, 'to_dict'):
            web_ui_dict = web_ui_memory.to_dict()
        else:
            # Fallback: extract fields manually
            web_ui_dict = {
                'id': getattr(web_ui_memory, 'id', ''),
                'content': getattr(web_ui_memory, 'content', ''),
                'timestamp': getattr(web_ui_memory, 'timestamp', None),
                'importance_score': getattr(web_ui_memory, 'importance_score', 5),
                'tags': getattr(web_ui_memory, 'tags', []),
                'metadata': getattr(web_ui_memory, 'metadata', {}),
                'user_id': getattr(web_ui_memory, 'user_id', None),
                'session_id': getattr(web_ui_memory, 'session_id', None),
                'ui_source': getattr(web_ui_memory, 'ui_source', None),
                'conversation_id': getattr(web_ui_memory, 'conversation_id', None),
                'access_count': getattr(web_ui_memory, 'access_count', 0),
                'ai_generated': getattr(web_ui_memory, 'ai_generated', False),
                'user_confirmed': getattr(web_ui_memory, 'user_confirmed', True),
            }
        
        # Remove fields that might conflict
        web_ui_dict.pop('memory_type', None)  # Will be handled by neuro_type
        
        # Determine neuro_type
        if neuro_type is None:
            if hasattr(web_ui_memory, 'memory_type') and web_ui_memory.memory_type:
                neuro_type = NeuroMemoryType.from_legacy_type(web_ui_memory.memory_type)
            else:
                neuro_type = NeuroMemoryType.EPISODIC
        
        # Set decay_lambda if not provided
        if decay_lambda is None:
            decay_lambda = neuro_type.get_default_decay_lambda()
        
        # Create NeuroMemoryEntry
        return cls(
            neuro_type=neuro_type,
            decay_lambda=decay_lambda,
            **web_ui_dict,
            **kwargs
        )
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary compatible with legacy WebUIMemoryEntry.
        
        Returns:
            Dictionary with legacy-compatible fields
        """
        # Get base dictionary
        base_dict = self.to_dict()
        
        # Remove NeuroVault-specific fields
        neuro_fields = [
            'neuro_type', 'decay_lambda', 'reflection_count', 
            'source_memories', 'derived_memories', 'importance_decay',
            'last_reflection', 'current_importance', 'decay_score',
            'is_expired', 'needs_reflection'
        ]
        
        for field in neuro_fields:
            base_dict.pop(field, None)
        
        # Map neuro_type back to memory_type for compatibility
        if NeuroMemoryType.is_legacy_type(self.neuro_type.value):
            base_dict['memory_type'] = self.neuro_type.value
        else:
            # Map tri-partite types to closest legacy type
            type_mapping = {
                NeuroMemoryType.EPISODIC: "conversation",
                NeuroMemoryType.SEMANTIC: "fact",
                NeuroMemoryType.PROCEDURAL: "insight"
            }
            base_dict['memory_type'] = type_mapping.get(self.neuro_type, "general")
        
        return base_dict