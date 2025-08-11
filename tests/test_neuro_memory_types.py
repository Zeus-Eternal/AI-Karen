"""
Unit tests for NeuroVault Memory Types and Enhanced Data Models.
Tests the implementation of NeuroMemoryType enum and NeuroMemoryEntry dataclass.
"""

import pytest
import math
from datetime import datetime, timedelta
from typing import Dict, Any

from ai_karen_engine.models.neuro_memory_types import NeuroMemoryType, NeuroMemoryEntry


class TestNeuroMemoryType:
    """Test cases for NeuroMemoryType enum."""
    
    def test_enum_values(self):
        """Test that all enum values are correctly defined."""
        # Legacy types
        assert NeuroMemoryType.GENERAL == "general"
        assert NeuroMemoryType.FACT == "fact"
        assert NeuroMemoryType.PREFERENCE == "preference"
        assert NeuroMemoryType.CONTEXT == "context"
        assert NeuroMemoryType.CONVERSATION == "conversation"
        assert NeuroMemoryType.INSIGHT == "insight"
        
        # Tri-partite types
        assert NeuroMemoryType.EPISODIC == "episodic"
        assert NeuroMemoryType.SEMANTIC == "semantic"
        assert NeuroMemoryType.PROCEDURAL == "procedural"
    
    def test_legacy_type_detection(self):
        """Test legacy type detection methods."""
        # Legacy types
        assert NeuroMemoryType.is_legacy_type("general")
        assert NeuroMemoryType.is_legacy_type("fact")
        assert NeuroMemoryType.is_legacy_type("preference")
        
        # Tri-partite types
        assert not NeuroMemoryType.is_legacy_type("episodic")
        assert not NeuroMemoryType.is_legacy_type("semantic")
        assert not NeuroMemoryType.is_legacy_type("procedural")
    
    def test_neuro_type_detection(self):
        """Test tri-partite type detection methods."""
        # Tri-partite types
        assert NeuroMemoryType.is_neuro_type("episodic")
        assert NeuroMemoryType.is_neuro_type("semantic")
        assert NeuroMemoryType.is_neuro_type("procedural")
        
        # Legacy types
        assert not NeuroMemoryType.is_neuro_type("general")
        assert not NeuroMemoryType.is_neuro_type("fact")
    
    def test_legacy_type_conversion(self):
        """Test conversion from legacy types."""
        # Test string conversion
        assert NeuroMemoryType.from_legacy_type("fact") == NeuroMemoryType.FACT
        assert NeuroMemoryType.from_legacy_type("general") == NeuroMemoryType.GENERAL
        
        # Test unknown type defaults to GENERAL
        assert NeuroMemoryType.from_legacy_type("unknown") == NeuroMemoryType.GENERAL
    
    def test_decay_lambda_defaults(self):
        """Test default decay lambda values for different memory types."""
        # Tri-partite types have research-based decay rates
        assert NeuroMemoryType.EPISODIC.get_default_decay_lambda() == 0.12
        assert NeuroMemoryType.SEMANTIC.get_default_decay_lambda() == 0.04
        assert NeuroMemoryType.PROCEDURAL.get_default_decay_lambda() == 0.02
        
        # Legacy types have moderate decay rates
        assert NeuroMemoryType.FACT.get_default_decay_lambda() == 0.04
        assert NeuroMemoryType.GENERAL.get_default_decay_lambda() == 0.08
        
        # Verify ordering: episodic > semantic > procedural
        assert (NeuroMemoryType.EPISODIC.get_default_decay_lambda() > 
                NeuroMemoryType.SEMANTIC.get_default_decay_lambda() > 
                NeuroMemoryType.PROCEDURAL.get_default_decay_lambda())


class TestNeuroMemoryEntry:
    """Test cases for NeuroMemoryEntry dataclass."""
    
    def test_initialization_with_defaults(self):
        """Test that NeuroMemoryEntry initializes with correct defaults."""
        entry = NeuroMemoryEntry(
            id="test-123",
            content="Test content",
            timestamp=datetime.utcnow(),
            importance_score=8
        )
        
        # Test NeuroVault-specific defaults
        assert entry.neuro_type == NeuroMemoryType.EPISODIC
        assert entry.decay_lambda == 0.12  # Default for episodic
        assert entry.reflection_count == 0
        assert entry.source_memories == []
        assert entry.derived_memories == []
        assert entry.importance_decay == 1.0
        assert entry.last_reflection is None
        
        # Test base field defaults
        assert entry.importance_score == 8
        assert entry.access_count == 0
        assert entry.ai_generated is False
        assert entry.user_confirmed is True
    
    def test_decay_lambda_auto_setting(self):
        """Test that decay_lambda is automatically set based on memory type."""
        semantic_entry = NeuroMemoryEntry(
            id="semantic-test",
            content="Semantic content",
            neuro_type=NeuroMemoryType.SEMANTIC
        )
        assert semantic_entry.decay_lambda == 0.04
        
        procedural_entry = NeuroMemoryEntry(
            id="procedural-test", 
            content="Procedural content",
            neuro_type=NeuroMemoryType.PROCEDURAL
        )
        assert procedural_entry.decay_lambda == 0.02
    
    def test_decay_calculation_methods(self):
        """Test decay calculation methods."""
        # Create entry with known timestamp
        timestamp = datetime.utcnow() - timedelta(days=1)
        entry = NeuroMemoryEntry(
            id="decay-test",
            content="Decay test",
            timestamp=timestamp,
            importance_score=10,
            decay_lambda=0.1
        )
        
        # Test current importance calculation
        current_importance = entry.calculate_current_importance()
        assert isinstance(current_importance, float)
        assert 0 <= current_importance <= entry.importance_score
        assert current_importance < entry.importance_score  # Should decay
        
        # Test decay score calculation
        decay_score = entry.calculate_decay_score()
        assert isinstance(decay_score, float)
        assert 0.0 <= decay_score <= 1.0
        
        # Test with custom time
        future_time = datetime.utcnow() + timedelta(days=30)
        future_importance = entry.calculate_current_importance(future_time)
        assert future_importance < current_importance
    
    def test_expiration_logic(self):
        """Test memory expiration logic."""
        # Recent memory should not be expired
        recent_entry = NeuroMemoryEntry(
            id="recent",
            content="Recent memory",
            timestamp=datetime.utcnow(),
            importance_score=5
        )
        assert not recent_entry.is_expired()
        
        # Very old memory with low importance should be expired
        old_entry = NeuroMemoryEntry(
            id="old",
            content="Old memory",
            timestamp=datetime.utcnow() - timedelta(days=365),
            importance_score=1,
            decay_lambda=0.2
        )
        assert old_entry.is_expired()
        
        # Test custom threshold
        assert not old_entry.is_expired(threshold=0.001)  # Very low threshold
    
    def test_reflection_logic(self):
        """Test reflection-related methods."""
        # Episodic memory should need reflection
        episodic_entry = NeuroMemoryEntry(
            id="episodic",
            content="Episodic memory",
            neuro_type=NeuroMemoryType.EPISODIC
        )
        assert episodic_entry.needs_reflection()
        
        # Non-episodic memory should not need reflection
        semantic_entry = NeuroMemoryEntry(
            id="semantic",
            content="Semantic memory", 
            neuro_type=NeuroMemoryType.SEMANTIC
        )
        assert not semantic_entry.needs_reflection()
        
        # Test reflection increment
        initial_count = episodic_entry.reflection_count
        episodic_entry.increment_reflection_count()
        assert episodic_entry.reflection_count == initial_count + 1
        assert episodic_entry.last_reflection is not None
        
        # After reflection, should not need reflection immediately
        assert not episodic_entry.needs_reflection()
    
    def test_memory_relationships(self):
        """Test memory relationship management."""
        entry = NeuroMemoryEntry(
            id="relationship-test",
            content="Relationship test"
        )
        
        # Test adding source memories
        entry.add_source_memory("source-1")
        entry.add_source_memory("source-2")
        assert "source-1" in entry.source_memories
        assert "source-2" in entry.source_memories
        
        # Test duplicate prevention
        entry.add_source_memory("source-1")
        assert entry.source_memories.count("source-1") == 1
        
        # Test adding derived memories
        entry.add_derived_memory("derived-1")
        assert "derived-1" in entry.derived_memories
    
    def test_importance_decay_update(self):
        """Test importance decay factor updates."""
        entry = NeuroMemoryEntry(
            id="decay-update-test",
            content="Decay update test"
        )
        
        # Test normal update
        entry.update_importance_decay(0.8)
        assert entry.importance_decay == 0.8
        
        # Test bounds checking
        entry.update_importance_decay(-0.1)
        assert entry.importance_decay == 0.0
        
        entry.update_importance_decay(1.5)
        assert entry.importance_decay == 1.0
    
    def test_to_dict_serialization(self):
        """Test dictionary serialization."""
        entry = NeuroMemoryEntry(
            id="serialize-test",
            content="Serialization test",
            timestamp=datetime.utcnow(),
            importance_score=7,
            neuro_type=NeuroMemoryType.SEMANTIC,
            reflection_count=2,
            source_memories=["source-1"],
            tags=["test"]
        )
        
        entry_dict = entry.to_dict()
        
        # Check that all NeuroVault fields are included
        neuro_fields = [
            'neuro_type', 'decay_lambda', 'reflection_count',
            'source_memories', 'derived_memories', 'importance_decay',
            'last_reflection', 'current_importance', 'decay_score',
            'is_expired', 'needs_reflection'
        ]
        
        for field in neuro_fields:
            assert field in entry_dict
        
        # Check calculated fields
        assert isinstance(entry_dict['current_importance'], float)
        assert isinstance(entry_dict['decay_score'], float)
        assert isinstance(entry_dict['is_expired'], bool)
        assert isinstance(entry_dict['needs_reflection'], bool)
    
    def test_from_web_ui_memory_conversion(self):
        """Test conversion from WebUI memory objects."""
        # Create mock WebUI memory
        class MockWebUIMemory:
            def __init__(self):
                self.id = "mock-123"
                self.content = "Mock content"
                self.timestamp = datetime.utcnow()
                self.importance_score = 6
                self.memory_type = "fact"
                self.tags = ["mock"]
            
            def to_dict(self):
                return {
                    'id': self.id,
                    'content': self.content,
                    'timestamp': self.timestamp,
                    'importance_score': self.importance_score,
                    'tags': self.tags
                }
        
        mock_memory = MockWebUIMemory()
        neuro_entry = NeuroMemoryEntry.from_web_ui_memory(mock_memory)
        
        # Verify conversion
        assert neuro_entry.id == mock_memory.id
        assert neuro_entry.content == mock_memory.content
        assert neuro_entry.importance_score == mock_memory.importance_score
        assert neuro_entry.neuro_type == NeuroMemoryType.FACT
        assert neuro_entry.tags == mock_memory.tags
    
    def test_to_legacy_dict_conversion(self):
        """Test conversion to legacy dictionary format."""
        entry = NeuroMemoryEntry(
            id="legacy-test",
            content="Legacy test",
            timestamp=datetime.utcnow(),
            importance_score=8,
            neuro_type=NeuroMemoryType.EPISODIC,
            reflection_count=3
        )
        
        legacy_dict = entry.to_legacy_dict()
        
        # Check that NeuroVault fields are removed
        neuro_fields = [
            'neuro_type', 'decay_lambda', 'reflection_count',
            'source_memories', 'derived_memories', 'importance_decay',
            'last_reflection', 'current_importance', 'decay_score',
            'is_expired', 'needs_reflection'
        ]
        
        for field in neuro_fields:
            assert field not in legacy_dict
        
        # Check that memory_type is mapped correctly
        assert 'memory_type' in legacy_dict
        assert legacy_dict['memory_type'] == 'conversation'  # EPISODIC maps to conversation
    
    def test_timestamp_handling(self):
        """Test different timestamp formats are handled correctly."""
        # Test with datetime object
        dt_entry = NeuroMemoryEntry(
            id="dt-test",
            content="DateTime test",
            timestamp=datetime.utcnow(),
            importance_score=5
        )
        assert dt_entry.calculate_current_importance() > 0
        
        # Test with string timestamp
        str_entry = NeuroMemoryEntry(
            id="str-test",
            content="String test",
            timestamp=datetime.utcnow().isoformat(),
            importance_score=5
        )
        assert str_entry.calculate_current_importance() > 0
        
        # Test with Unix timestamp (milliseconds)
        unix_entry = NeuroMemoryEntry(
            id="unix-test",
            content="Unix test",
            timestamp=int(datetime.utcnow().timestamp() * 1000),
            importance_score=5
        )
        assert unix_entry.calculate_current_importance() > 0


if __name__ == "__main__":
    pytest.main([__file__])