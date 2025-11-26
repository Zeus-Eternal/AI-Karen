"""
Agent Memory Fusion Service

This service provides memory fusion capabilities for agents, allowing them to
combine and integrate memories from different sources and agents.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Enumeration of memory types."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"
    LONG_TERM = "long_term"
    PROCEDURAL = "procedural"


class FusionStrategy(Enum):
    """Enumeration of memory fusion strategies."""
    MERGE = "merge"
    INTERLEAVE = "interleave"
    PRIORITIZE = "prioritize"
    CONFLICT_RESOLUTION = "conflict_resolution"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"


class ConflictResolutionStrategy(Enum):
    """Enumeration of conflict resolution strategies."""
    NEWEST = "newest"
    OLDEST = "oldest"
    HIGHEST_PRIORITY = "highest_priority"
    LOWEST_PRIORITY = "lowest_priority"
    MOST_RELEVANT = "most_relevant"
    MANUAL = "manual"


@dataclass
class MemoryFragment:
    """A fragment of memory."""
    id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0
    priority: int = 0
    tags: Set[str] = field(default_factory=set)
    source: Optional[str] = None


@dataclass
class FusedMemory:
    """A fused memory combining multiple memory fragments."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0
    priority: int = 0
    tags: Set[str] = field(default_factory=set)
    sources: Set[str] = field(default_factory=set)
    fusion_strategy: FusionStrategy = FusionStrategy.MERGE
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class MemoryFusionConfig:
    """Configuration for memory fusion."""
    default_strategy: FusionStrategy = FusionStrategy.MERGE
    default_conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.NEWEST
    max_fragments: int = 10
    relevance_threshold: float = 0.5
    temporal_weight: float = 0.3
    semantic_weight: float = 0.5
    priority_weight: float = 0.2
    enable_cross_agent_fusion: bool = True
    enable_type_based_fusion: bool = True
    enable_temporal_fusion: bool = True
    enable_semantic_fusion: bool = True


class AgentMemoryFusion:
    """
    Provides memory fusion capabilities for agents.
    
    This class is responsible for:
    - Fusing memories from different sources and agents
    - Resolving conflicts between memories
    - Providing different fusion strategies
    - Maintaining memory relationships and provenance
    """
    
    def __init__(self, config: Optional[MemoryFusionConfig] = None):
        self._config = config or MemoryFusionConfig()
        self._memory_fragments: Dict[str, MemoryFragment] = {}
        self._fused_memories: Dict[str, FusedMemory] = {}
        self._agent_memories: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> fragment_ids
        self._memory_relationships: Dict[str, Set[str]] = defaultdict(set)  # fragment_id -> related fragment_ids
        self._fusion_history: List[Dict[str, Any]] = []
        
        # Memory similarity cache
        self._similarity_cache: Dict[Tuple[str, str], float] = {}
        self._similarity_cache_size = 1000
        
        # Callbacks for fusion events
        self._on_memory_fused: Optional[Callable[[str, List[str]], None]] = None
        self._on_conflict_detected: Optional[Callable[[List[str]], None]] = None
        self._on_conflict_resolved: Optional[Callable[[List[str], Dict[str, Any]], None]] = None
    
    def add_memory_fragment(self, fragment: MemoryFragment) -> str:
        """
        Add a memory fragment.
        
        Args:
            fragment: Memory fragment to add
            
        Returns:
            ID of the added fragment
        """
        # Store fragment
        self._memory_fragments[fragment.id] = fragment
        
        # Update agent memories
        self._agent_memories[fragment.agent_id].add(fragment.id)
        
        # Update memory relationships
        for related_id in self._find_related_memories(fragment):
            self._memory_relationships[fragment.id].add(related_id)
            self._memory_relationships[related_id].add(fragment.id)
        
        logger.debug(f"Added memory fragment: {fragment.id} from agent {fragment.agent_id}")
        return fragment.id
    
    def get_memory_fragment(self, fragment_id: str) -> Optional[MemoryFragment]:
        """Get a memory fragment by ID."""
        return self._memory_fragments.get(fragment_id)
    
    def get_memory_fragments_for_agent(self, agent_id: str) -> List[MemoryFragment]:
        """Get all memory fragments for an agent."""
        fragment_ids = self._agent_memories.get(agent_id, set())
        return [self._memory_fragments[fragment_id] for fragment_id in fragment_ids if fragment_id in self._memory_fragments]
    
    def get_fused_memory(self, fused_id: str) -> Optional[FusedMemory]:
        """Get a fused memory by ID."""
        return self._fused_memories.get(fused_id)
    
    def fuse_memories(
        self,
        fragment_ids: List[str],
        strategy: Optional[FusionStrategy] = None,
        conflict_resolution: Optional[ConflictResolutionStrategy] = None
    ) -> FusedMemory:
        """
        Fuse multiple memory fragments.
        
        Args:
            fragment_ids: IDs of memory fragments to fuse
            strategy: Fusion strategy to use
            conflict_resolution: Conflict resolution strategy to use
            
        Returns:
            Fused memory
        """
        # Get fragments
        fragments = []
        for fragment_id in fragment_ids:
            fragment = self._memory_fragments.get(fragment_id)
            if fragment:
                fragments.append(fragment)
            else:
                logger.warning(f"Memory fragment not found: {fragment_id}")
        
        if not fragments:
            raise ValueError("No valid memory fragments to fuse")
        
        # Use default strategy if not specified
        fusion_strategy = strategy or self._config.default_strategy
        conflict_strategy = conflict_resolution or self._config.default_conflict_resolution
        
        # Check for conflicts
        conflicts = self._detect_conflicts(fragments)
        
        # Resolve conflicts
        if conflicts:
            resolved_fragments = self._resolve_conflicts(fragments, conflicts, conflict_strategy)
        else:
            resolved_fragments = fragments
        
        # Fuse memories based on strategy
        if fusion_strategy == FusionStrategy.MERGE:
            fused_memory = self._merge_memories(resolved_fragments)
        elif fusion_strategy == FusionStrategy.INTERLEAVE:
            fused_memory = self._interleave_memories(resolved_fragments)
        elif fusion_strategy == FusionStrategy.PRIORITIZE:
            fused_memory = self._prioritize_memories(resolved_fragments)
        elif fusion_strategy == FusionStrategy.TEMPORAL:
            fused_memory = self._temporal_fuse_memories(resolved_fragments)
        elif fusion_strategy == FusionStrategy.SEMANTIC:
            fused_memory = self._semantic_fuse_memories(resolved_fragments)
        else:
            raise ValueError(f"Unknown fusion strategy: {fusion_strategy}")
        
        # Set fusion strategy and conflicts
        fused_memory.fusion_strategy = fusion_strategy
        fused_memory.conflicts = conflicts
        
        # Store fused memory
        self._fused_memories[fused_memory.id] = fused_memory
        
        # Record fusion history
        self._fusion_history.append({
            "timestamp": datetime.now().isoformat(),
            "fragment_ids": fragment_ids,
            "fused_id": fused_memory.id,
            "strategy": fusion_strategy.value,
            "conflict_resolution": conflict_strategy.value if conflicts else None,
            "conflicts": conflicts
        })
        
        # Call memory fused callback if set
        if self._on_memory_fused:
            self._on_memory_fused(fused_memory.id, fragment_ids)
        
        logger.info(f"Fused {len(fragment_ids)} memory fragments into {fused_memory.id} using {fusion_strategy.value}")
        return fused_memory
    
    def fuse_agent_memories(
        self,
        agent_ids: List[str],
        memory_type: Optional[MemoryType] = None,
        strategy: Optional[FusionStrategy] = None,
        conflict_resolution: Optional[ConflictResolutionStrategy] = None
    ) -> List[FusedMemory]:
        """
        Fuse memories from multiple agents.
        
        Args:
            agent_ids: IDs of agents
            memory_type: Type of memories to fuse
            strategy: Fusion strategy to use
            conflict_resolution: Conflict resolution strategy to use
            
        Returns:
            List of fused memories
        """
        if not self._config.enable_cross_agent_fusion:
            raise ValueError("Cross-agent fusion is disabled")
        
        # Collect memory fragments from agents
        fragments = []
        for agent_id in agent_ids:
            agent_fragments = self.get_memory_fragments_for_agent(agent_id)
            if memory_type:
                agent_fragments = [f for f in agent_fragments if f.memory_type == memory_type]
            fragments.extend(agent_fragments)
        
        if not fragments:
            return []
        
        # Group fragments by similarity
        fragment_groups = self._group_similar_memories(fragments)
        
        # Fuse each group
        fused_memories = []
        for group in fragment_groups:
            if len(group) > 1:
                group_ids = [f.id for f in group]
                fused_memory = self.fuse_memories(group_ids, strategy, conflict_resolution)
                fused_memories.append(fused_memory)
            else:
                # Only one fragment, no fusion needed
                fragment = group[0]
                fused_memory = FusedMemory(
                    id=str(uuid.uuid4()),
                    content=fragment.content,
                    metadata=fragment.metadata,
                    timestamp=fragment.timestamp,
                    relevance_score=fragment.relevance_score,
                    priority=fragment.priority,
                    tags=fragment.tags,
                    sources={fragment.agent_id},
                    fusion_strategy=FusionStrategy.MERGE,
                    confidence=1.0
                )
                self._fused_memories[fused_memory.id] = fused_memory
                fused_memories.append(fused_memory)
        
        logger.info(f"Fused memories from {len(agent_ids)} agents into {len(fused_memories)} fused memories")
        return fused_memories
    
    def find_related_memories(self, fragment_id: str, threshold: float = 0.5) -> List[MemoryFragment]:
        """
        Find memories related to a given memory fragment.
        
        Args:
            fragment_id: ID of the memory fragment
            threshold: Similarity threshold
            
        Returns:
            List of related memory fragments
        """
        fragment = self._memory_fragments.get(fragment_id)
        if not fragment:
            return []
        
        # Get related fragment IDs
        related_ids = self._memory_relationships.get(fragment_id, set())
        
        # Get related fragments
        related_fragments = []
        for related_id in related_ids:
            related_fragment = self._memory_fragments.get(related_id)
            if related_fragment:
                similarity = self._calculate_similarity(fragment, related_fragment)
                if similarity >= threshold:
                    related_fragments.append(related_fragment)
        
        return related_fragments
    
    def get_fusion_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get fusion history."""
        return self._fusion_history[-limit:]
    
    def set_fusion_callbacks(
        self,
        on_memory_fused: Optional[Callable[[str, List[str]], None]] = None,
        on_conflict_detected: Optional[Callable[[List[str]], None]] = None,
        on_conflict_resolved: Optional[Callable[[List[str], Dict[str, Any]], None]] = None
    ) -> None:
        """Set callbacks for fusion events."""
        self._on_memory_fused = on_memory_fused
        self._on_conflict_detected = on_conflict_detected
        self._on_conflict_resolved = on_conflict_resolved
    
    def clear_cache(self) -> None:
        """Clear the similarity cache."""
        self._similarity_cache.clear()
        logger.debug("Cleared similarity cache")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about memory fusion.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_memory_fragments": len(self._memory_fragments),
            "total_fused_memories": len(self._fused_memories),
            "total_agents": len(self._agent_memories),
            "total_memory_relationships": sum(len(rels) for rels in self._memory_relationships.values()) // 2,
            "fusion_history_size": len(self._fusion_history),
            "similarity_cache_size": len(self._similarity_cache),
            "fragments_by_agent": {agent_id: len(fragment_ids) for agent_id, fragment_ids in self._agent_memories.items()},
            "fragments_by_type": {},
            "fusions_by_strategy": {}
        }
        
        # Count fragments by type
        for fragment in self._memory_fragments.values():
            memory_type = fragment.memory_type.value
            if memory_type not in stats["fragments_by_type"]:
                stats["fragments_by_type"][memory_type] = 0
            stats["fragments_by_type"][memory_type] += 1
        
        # Count fusions by strategy
        for entry in self._fusion_history:
            strategy = entry.get("strategy", "unknown")
            if strategy not in stats["fusions_by_strategy"]:
                stats["fusions_by_strategy"][strategy] = 0
            stats["fusions_by_strategy"][strategy] += 1
        
        return stats
    
    def _find_related_memories(self, fragment: MemoryFragment, threshold: float = 0.5) -> List[str]:
        """Find memory fragments related to a given fragment."""
        related_ids = []
        
        for other_id, other_fragment in self._memory_fragments.items():
            if other_id == fragment.id:
                continue
            
            # Check if already in cache
            cache_key = (fragment.id, other_id)
            if cache_key in self._similarity_cache:
                similarity = self._similarity_cache[cache_key]
            else:
                similarity = self._calculate_similarity(fragment, other_fragment)
                
                # Add to cache
                self._similarity_cache[cache_key] = similarity
                
                # Limit cache size
                if len(self._similarity_cache) > self._similarity_cache_size:
                    # Remove oldest entry
                    oldest_key = next(iter(self._similarity_cache))
                    del self._similarity_cache[oldest_key]
            
            if similarity >= threshold:
                related_ids.append(other_id)
        
        return related_ids
    
    def _calculate_similarity(self, fragment1: MemoryFragment, fragment2: MemoryFragment) -> float:
        """Calculate similarity between two memory fragments."""
        # Simple similarity calculation based on content, tags, and metadata
        # In a real implementation, this would use more sophisticated NLP techniques
        
        # Content similarity (simple word overlap)
        words1 = set(re.findall(r'\w+', fragment1.content.lower()))
        words2 = set(re.findall(r'\w+', fragment2.content.lower()))
        
        if not words1 or not words2:
            content_similarity = 0.0
        else:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            content_similarity = len(intersection) / len(union)
        
        # Tag similarity
        if fragment1.tags and fragment2.tags:
            tag_intersection = fragment1.tags.intersection(fragment2.tags)
            tag_union = fragment1.tags.union(fragment2.tags)
            tag_similarity = len(tag_intersection) / len(tag_union)
        else:
            tag_similarity = 0.0
        
        # Type similarity
        type_similarity = 1.0 if fragment1.memory_type == fragment2.memory_type else 0.0
        
        # Weighted combination
        similarity = (
            0.6 * content_similarity +
            0.2 * tag_similarity +
            0.2 * type_similarity
        )
        
        return similarity
    
    def _detect_conflicts(self, fragments: List[MemoryFragment]) -> List[Dict[str, Any]]:
        """Detect conflicts between memory fragments."""
        conflicts = []
        
        # Check for content conflicts
        for i in range(len(fragments)):
            for j in range(i + 1, len(fragments)):
                fragment1 = fragments[i]
                fragment2 = fragments[j]
                
                # Check for direct contradictions
                if self._are_contradictory(fragment1.content, fragment2.content):
                    conflicts.append({
                        "type": "contradiction",
                        "fragments": [fragment1.id, fragment2.id],
                        "description": f"Contradictory content between {fragment1.id} and {fragment2.id}"
                    })
                
                # Check for temporal conflicts
                if fragment1.timestamp != fragment2.timestamp:
                    # If content is similar but timestamps are different
                    similarity = self._calculate_similarity(fragment1, fragment2)
                    if similarity > 0.7:
                        conflicts.append({
                            "type": "temporal",
                            "fragments": [fragment1.id, fragment2.id],
                            "description": f"Similar content with different timestamps between {fragment1.id} and {fragment2.id}"
                        })
        
        # Call conflict detected callback if set
        if conflicts and self._on_conflict_detected:
            self._on_conflict_detected([f["fragments"] for f in conflicts])
        
        return conflicts
    
    def _are_contradictory(self, content1: str, content2: str) -> bool:
        """Check if two content strings are contradictory."""
        # Simple contradiction detection
        # In a real implementation, this would use more sophisticated NLP techniques
        
        # Check for negation patterns
        negation_patterns = [
            (r"not\s+(\w+)", r"\1"),
            (r"no\s+(\w+)", r"\1"),
            (r"never\s+(\w+)", r"\1"),
            (r"doesn't\s+(\w+)", r"\1"),
            (r"don't\s+(\w+)", r"\1"),
            (r"isn't\s+(\w+)", r"\1"),
            (r"aren't\s+(\w+)", r"\1"),
            (r"wasn't\s+(\w+)", r"\1"),
            (r"weren't\s+(\w+)", r"\1"),
        ]
        
        # Normalize content
        content1_norm = content1.lower().strip()
        content2_norm = content2.lower().strip()
        
        # Check for direct negation
        for pattern, replacement in negation_patterns:
            match1 = re.search(pattern, content1_norm)
            match2 = re.search(pattern, content2_norm)
            
            if match1 and not match2:
                # Check if the negated word appears in the second content
                negated_word = match1.group(1)
                if negated_word in content2_norm:
                    return True
            elif match2 and not match1:
                # Check if the negated word appears in the first content
                negated_word = match2.group(1)
                if negated_word in content1_norm:
                    return True
        
        return False
    
    def _resolve_conflicts(
        self,
        fragments: List[MemoryFragment],
        conflicts: List[Dict[str, Any]],
        strategy: ConflictResolutionStrategy
    ) -> List[MemoryFragment]:
        """Resolve conflicts between memory fragments."""
        # For now, we'll implement a simple resolution strategy
        # In a real implementation, this would be more sophisticated
        
        # Create a set of fragment IDs to keep
        keep_ids = set(fragment.id for fragment in fragments)
        
        for conflict in conflicts:
            conflict_ids = conflict["fragments"]
            
            if strategy == ConflictResolutionStrategy.NEWEST:
                # Keep the newest fragment
                newest_id = max(
                    conflict_ids,
                    key=lambda fid: self._memory_fragments[fid].timestamp
                )
                # Remove the others
                for conflict_id in conflict_ids:
                    if conflict_id != newest_id:
                        keep_ids.discard(conflict_id)
            
            elif strategy == ConflictResolutionStrategy.OLDEST:
                # Keep the oldest fragment
                oldest_id = min(
                    conflict_ids,
                    key=lambda fid: self._memory_fragments[fid].timestamp
                )
                # Remove the others
                for conflict_id in conflict_ids:
                    if conflict_id != oldest_id:
                        keep_ids.discard(conflict_id)
            
            elif strategy == ConflictResolutionStrategy.HIGHEST_PRIORITY:
                # Keep the highest priority fragment
                highest_id = max(
                    conflict_ids,
                    key=lambda fid: self._memory_fragments[fid].priority
                )
                # Remove the others
                for conflict_id in conflict_ids:
                    if conflict_id != highest_id:
                        keep_ids.discard(conflict_id)
            
            elif strategy == ConflictResolutionStrategy.LOWEST_PRIORITY:
                # Keep the lowest priority fragment
                lowest_id = min(
                    conflict_ids,
                    key=lambda fid: self._memory_fragments[fid].priority
                )
                # Remove the others
                for conflict_id in conflict_ids:
                    if conflict_id != lowest_id:
                        keep_ids.discard(conflict_id)
            
            elif strategy == ConflictResolutionStrategy.MOST_RELEVANT:
                # Keep the most relevant fragment
                most_relevant_id = max(
                    conflict_ids,
                    key=lambda fid: self._memory_fragments[fid].relevance_score
                )
                # Remove the others
                for conflict_id in conflict_ids:
                    if conflict_id != most_relevant_id:
                        keep_ids.discard(conflict_id)
            
            elif strategy == ConflictResolutionStrategy.MANUAL:
                # Manual resolution requires human intervention
                # For now, we'll keep all fragments
                pass
        
        # Return the fragments to keep
        resolved_fragments = [
            fragment for fragment in fragments
            if fragment.id in keep_ids
        ]
        
        # Call conflict resolved callback if set
        if self._on_conflict_resolved:
            self._on_conflict_resolved([f["fragments"] for f in conflicts], {"strategy": strategy.value})
        
        logger.debug(f"Resolved {len(conflicts)} conflicts using {strategy.value}")
        return resolved_fragments
    
    def _group_similar_memories(self, fragments: List[MemoryFragment]) -> List[List[MemoryFragment]]:
        """Group similar memories together."""
        groups = []
        ungrouped = fragments.copy()
        
        while ungrouped:
            # Start a new group with the first ungrouped fragment
            group = [ungrouped.pop(0)]
            
            # Find similar fragments
            i = 0
            while i < len(ungrouped):
                fragment = ungrouped[i]
                
                # Check if fragment is similar to any fragment in the group
                similar_to_group = False
                for group_fragment in group:
                    similarity = self._calculate_similarity(group_fragment, fragment)
                    if similarity >= self._config.relevance_threshold:
                        similar_to_group = True
                        break
                
                if similar_to_group:
                    # Add to group
                    group.append(fragment)
                    ungrouped.pop(i)
                else:
                    i += 1
            
            # Add group to groups
            groups.append(group)
        
        return groups
    
    def _merge_memories(self, fragments: List[MemoryFragment]) -> FusedMemory:
        """Merge memory fragments into a single fused memory."""
        if not fragments:
            raise ValueError("No fragments to merge")
        
        # Sort fragments by priority (descending)
        sorted_fragments = sorted(fragments, key=lambda f: f.priority, reverse=True)
        
        # Start with the highest priority fragment
        base_fragment = sorted_fragments[0]
        
        # Merge content
        merged_content = base_fragment.content
        
        # Merge metadata
        merged_metadata = base_fragment.metadata.copy()
        
        # Merge tags
        merged_tags = base_fragment.tags.copy()
        
        # Merge sources
        merged_sources = {base_fragment.agent_id}
        
        # Merge other fragments
        for fragment in sorted_fragments[1:]:
            # Append content with separator
            merged_content += f" [Also: {fragment.content}]"
            
            # Merge metadata
            for key, value in fragment.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
                elif isinstance(merged_metadata[key], dict) and isinstance(value, dict):
                    merged_metadata[key].update(value)
            
            # Merge tags
            merged_tags.update(fragment.tags)
            
            # Merge sources
            merged_sources.add(fragment.agent_id)
        
        # Calculate weighted relevance score
        relevance_score = sum(
            f.relevance_score * self._get_fragment_weight(f)
            for f in fragments
        ) / sum(
            self._get_fragment_weight(f)
            for f in fragments
        )
        
        # Calculate weighted priority
        priority = int(sum(
            f.priority * self._get_fragment_weight(f)
            for f in fragments
        ) / sum(
            self._get_fragment_weight(f)
            for f in fragments
        ))
        
        # Create fused memory
        fused_memory = FusedMemory(
            id=str(uuid.uuid4()),
            content=merged_content,
            metadata=merged_metadata,
            timestamp=base_fragment.timestamp,
            relevance_score=relevance_score,
            priority=priority,
            tags=merged_tags,
            sources=merged_sources,
            fusion_strategy=FusionStrategy.MERGE,
            confidence=min(1.0, 1.0 - (len(fragments) - 1) * 0.1)  # Confidence decreases with more fragments
        )
        
        return fused_memory
    
    def _interleave_memories(self, fragments: List[MemoryFragment]) -> FusedMemory:
        """Interleave memory fragments into a single fused memory."""
        if not fragments:
            raise ValueError("No fragments to interleave")
        
        # Sort fragments by timestamp (oldest first)
        sorted_fragments = sorted(fragments, key=lambda f: f.timestamp)
        
        # Interleave content
        interleaved_parts = []
        merged_metadata = {}
        merged_tags = set()
        merged_sources = set()
        
        for fragment in sorted_fragments:
            interleaved_parts.append(fragment.content)
            
            # Merge metadata
            for key, value in fragment.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
                elif isinstance(merged_metadata[key], dict) and isinstance(value, dict):
                    merged_metadata[key].update(value)
            
            # Merge tags
            merged_tags.update(fragment.tags)
            
            # Merge sources
            merged_sources.add(fragment.agent_id)
        
        # Join content with separators
        interleaved_content = " [Then: ".join(interleaved_parts) + "]"
        
        # Calculate weighted relevance score
        relevance_score = sum(
            f.relevance_score * self._get_fragment_weight(f)
            for f in fragments
        ) / sum(
            self._get_fragment_weight(f)
            for f in fragments
        )
        
        # Calculate weighted priority
        priority = int(sum(
            f.priority * self._get_fragment_weight(f)
            for f in fragments
        ) / sum(
            self._get_fragment_weight(f)
            for f in fragments
        ))
        
        # Create fused memory
        fused_memory = FusedMemory(
            id=str(uuid.uuid4()),
            content=interleaved_content,
            metadata=merged_metadata,
            timestamp=sorted_fragments[0].timestamp,
            relevance_score=relevance_score,
            priority=priority,
            tags=merged_tags,
            sources=merged_sources,
            fusion_strategy=FusionStrategy.INTERLEAVE,
            confidence=0.9
        )
        
        return fused_memory
    
    def _prioritize_memories(self, fragments: List[MemoryFragment]) -> FusedMemory:
        """Prioritize memory fragments into a single fused memory."""
        if not fragments:
            raise ValueError("No fragments to prioritize")
        
        # Sort fragments by priority (descending)
        sorted_fragments = sorted(fragments, key=lambda f: f.priority, reverse=True)
        
        # Use the highest priority fragment as the base
        base_fragment = sorted_fragments[0]
        
        # Merge metadata, tags, and sources from all fragments
        merged_metadata = {}
        merged_tags = set()
        merged_sources = set()
        
        for fragment in fragments:
            # Merge metadata
            for key, value in fragment.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
                elif isinstance(merged_metadata[key], dict) and isinstance(value, dict):
                    merged_metadata[key].update(value)
            
            # Merge tags
            merged_tags.update(fragment.tags)
            
            # Merge sources
            merged_sources.add(fragment.agent_id)
        
        # Create fused memory
        fused_memory = FusedMemory(
            id=str(uuid.uuid4()),
            content=base_fragment.content,
            metadata=merged_metadata,
            timestamp=base_fragment.timestamp,
            relevance_score=base_fragment.relevance_score,
            priority=base_fragment.priority,
            tags=merged_tags,
            sources=merged_sources,
            fusion_strategy=FusionStrategy.PRIORITIZE,
            confidence=1.0
        )
        
        return fused_memory
    
    def _temporal_fuse_memories(self, fragments: List[MemoryFragment]) -> FusedMemory:
        """Fuse memory fragments based on temporal order."""
        if not fragments:
            raise ValueError("No fragments to temporally fuse")
        
        # Sort fragments by timestamp (oldest first)
        sorted_fragments = sorted(fragments, key=lambda f: f.timestamp)
        
        # Create a timeline of events
        timeline = []
        merged_metadata = {}
        merged_tags = set()
        merged_sources = set()
        
        for fragment in sorted_fragments:
            # Add to timeline
            timeline.append({
                "timestamp": fragment.timestamp,
                "content": fragment.content,
                "agent": fragment.agent_id
            })
            
            # Merge metadata
            for key, value in fragment.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
                elif isinstance(merged_metadata[key], dict) and isinstance(value, dict):
                    merged_metadata[key].update(value)
            
            # Merge tags
            merged_tags.update(fragment.tags)
            
            # Merge sources
            merged_sources.add(fragment.agent_id)
        
        # Create content from timeline
        content_parts = []
        for event in timeline:
            content_parts.append(f"At {event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}, {event['agent']}: {event['content']}")
        
        timeline_content = " | ".join(content_parts)
        
        # Calculate weighted relevance score
        relevance_score = sum(
            f.relevance_score * self._get_temporal_weight(f, sorted_fragments)
            for f in fragments
        ) / sum(
            self._get_temporal_weight(f, sorted_fragments)
            for f in fragments
        )
        
        # Calculate weighted priority
        priority = int(sum(
            f.priority * self._get_temporal_weight(f, sorted_fragments)
            for f in fragments
        ) / sum(
            self._get_temporal_weight(f, sorted_fragments)
            for f in fragments
        ))
        
        # Create fused memory
        fused_memory = FusedMemory(
            id=str(uuid.uuid4()),
            content=timeline_content,
            metadata=merged_metadata,
            timestamp=sorted_fragments[0].timestamp,
            relevance_score=relevance_score,
            priority=priority,
            tags=merged_tags,
            sources=merged_sources,
            fusion_strategy=FusionStrategy.TEMPORAL,
            confidence=0.95
        )
        
        return fused_memory
    
    def _semantic_fuse_memories(self, fragments: List[MemoryFragment]) -> FusedMemory:
        """Fuse memory fragments based on semantic similarity."""
        if not fragments:
            raise ValueError("No fragments to semantically fuse")
        
        # Group by semantic similarity
        groups = self._group_similar_memories(fragments)
        
        # Create a summary for each group
        group_summaries = []
        merged_metadata = {}
        merged_tags = set()
        merged_sources = set()
        
        for group in groups:
            # Create a summary for the group
            if len(group) == 1:
                # Single fragment, use as is
                summary = group[0].content
            else:
                # Multiple fragments, create a summary
                # In a real implementation, this would use text summarization
                # For now, we'll just concatenate them
                summary = " and ".join(f.content for f in group)
            
            group_summaries.append(summary)
            
            # Merge metadata, tags, and sources
            for fragment in group:
                # Merge metadata
                for key, value in fragment.metadata.items():
                    if key not in merged_metadata:
                        merged_metadata[key] = value
                    elif isinstance(merged_metadata[key], dict) and isinstance(value, dict):
                        merged_metadata[key].update(value)
                
                # Merge tags
                merged_tags.update(fragment.tags)
                
                # Merge sources
                merged_sources.add(fragment.agent_id)
        
        # Create content from group summaries
        semantic_content = " [Related: ".join(group_summaries) + "]"
        
        # Calculate weighted relevance score
        relevance_score = sum(
            f.relevance_score * self._get_semantic_weight(f, fragments)
            for f in fragments
        ) / sum(
            self._get_semantic_weight(f, fragments)
            for f in fragments
        )
        
        # Calculate weighted priority
        priority = int(sum(
            f.priority * self._get_semantic_weight(f, fragments)
            for f in fragments
        ) / sum(
            self._get_semantic_weight(f, fragments)
            for f in fragments
        ))
        
        # Create fused memory
        fused_memory = FusedMemory(
            id=str(uuid.uuid4()),
            content=semantic_content,
            metadata=merged_metadata,
            timestamp=min(f.timestamp for f in fragments),
            relevance_score=relevance_score,
            priority=priority,
            tags=merged_tags,
            sources=merged_sources,
            fusion_strategy=FusionStrategy.SEMANTIC,
            confidence=0.85
        )
        
        return fused_memory
    
    def _get_fragment_weight(self, fragment: MemoryFragment) -> float:
        """Get the weight for a fragment based on its properties."""
        # Calculate weight based on relevance, priority, and recency
        recency_weight = 1.0  # In a real implementation, this would be based on age
        
        weight = (
            self._config.semantic_weight * fragment.relevance_score +
            self._config.priority_weight * (fragment.priority / 100.0) +
            self._config.temporal_weight * recency_weight
        )
        
        return weight
    
    def _get_temporal_weight(self, fragment: MemoryFragment, all_fragments: List[MemoryFragment]) -> float:
        """Get the temporal weight for a fragment."""
        # Find the oldest and newest timestamps
        oldest = min(f.timestamp for f in all_fragments)
        newest = max(f.timestamp for f in all_fragments)
        
        # Calculate normalized age (0.0 for newest, 1.0 for oldest)
        if oldest == newest:
            normalized_age = 0.5
        else:
            age = (fragment.timestamp - oldest).total_seconds()
            total_span = (newest - oldest).total_seconds()
            normalized_age = age / total_span
        
        # Temporal weight is higher for more recent fragments
        temporal_weight = 1.0 - normalized_age
        
        return temporal_weight
    
    def _get_semantic_weight(self, fragment: MemoryFragment, all_fragments: List[MemoryFragment]) -> float:
        """Get the semantic weight for a fragment."""
        # Calculate average similarity to other fragments
        similarities = []
        
        for other_fragment in all_fragments:
            if other_fragment.id == fragment.id:
                continue
            
            similarity = self._calculate_similarity(fragment, other_fragment)
            similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Semantic weight is the average similarity
        semantic_weight = sum(similarities) / len(similarities)
        
        return semantic_weight