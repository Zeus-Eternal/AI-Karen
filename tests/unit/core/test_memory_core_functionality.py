#!/usr/bin/env python3
"""
Simple test for Memory Pipeline Unification core functionality
Tests the core components without complex dependencies.
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_memory_policy_core():
    """Test core memory policy functionality"""
    print("Testing Memory Policy Core...")
    
    try:
        from ai_karen_engine.services.memory_policy import DecayTier, ImportanceLevel, MemoryPolicy
        
        # Test enums
        assert DecayTier.SHORT == "short"
        assert DecayTier.LONG == "long"
        assert ImportanceLevel.NORMAL == 5
        print("✓ Enums working correctly")
        
        # Test policy creation with defaults
        policy = MemoryPolicy()
        assert policy.top_k == 6
        assert policy.importance_long_threshold == 8
        print("✓ Default policy created")
        
        # Test decay tier assignment
        tier_low = policy.assign_decay_tier(3)
        tier_high = policy.assign_decay_tier(9)
        assert tier_low == DecayTier.SHORT
        assert tier_high == DecayTier.LONG
        print("✓ Decay tier assignment working")
        
        # Test expiry calculation
        expiry = policy.calculate_expiry_date(DecayTier.SHORT)
        assert expiry is not None
        print("✓ Expiry calculation working")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory policy core test failed: {e}")
        return False

def test_unified_memory_models():
    """Test unified memory service data models"""
    print("\nTesting Unified Memory Models...")
    
    try:
        from ai_karen_engine.services.unified_memory_service import (
            ContextHit, MemoryCommitRequest, MemoryQueryRequest
        )
        
        # Test ContextHit
        context_hit = ContextHit(
            id="test_id",
            text="Test context",
            score=0.85,
            importance=7,
            decay_tier="medium",
            created_at=datetime.utcnow(),
            user_id="test_user"
        )
        assert context_hit.id == "test_id"
        assert context_hit.score == 0.85
        print("✓ ContextHit model working")
        
        # Test MemoryCommitRequest
        commit_request = MemoryCommitRequest(
            user_id="test_user",
            text="Test memory content",
            importance=7,
            decay="medium",
            tags=["test", "validation"]
        )
        assert commit_request.user_id == "test_user"
        assert commit_request.importance == 7
        print("✓ MemoryCommitRequest model working")
        
        # Test MemoryQueryRequest
        query_request = MemoryQueryRequest(
            user_id="test_user",
            query="test query",
            top_k=5
        )
        assert query_request.user_id == "test_user"
        assert query_request.top_k == 5
        print("✓ MemoryQueryRequest model working")
        
        return True
        
    except Exception as e:
        print(f"✗ Unified memory models test failed: {e}")
        return False

def test_writeback_models():
    """Test memory writeback system models"""
    print("\nTesting Writeback Models...")
    
    try:
        from ai_karen_engine.services.memory_writeback import (
            InteractionType, ShardUsageType, ShardLink, WritebackEntry, FeedbackMetrics
        )
        
        # Test enums
        assert InteractionType.COPILOT_RESPONSE == "copilot_response"
        assert ShardUsageType.USED_IN_RESPONSE == "used_in_response"
        print("✓ Writeback enums working")
        
        # Test ShardLink
        shard_link = ShardLink(
            shard_id="test_shard",
            usage_type=ShardUsageType.USED_IN_RESPONSE,
            relevance_score=0.9,
            position_in_results=0,
            content_snippet="Test snippet",
            usage_timestamp=datetime.utcnow(),
            response_id="test_response",
            user_id="test_user"
        )
        assert shard_link.shard_id == "test_shard"
        assert shard_link.relevance_score == 0.9
        print("✓ ShardLink model working")
        
        # Test WritebackEntry
        writeback_entry = WritebackEntry(
            id="test_writeback",
            content="Test writeback content",
            interaction_type=InteractionType.COPILOT_RESPONSE,
            source_shards=[shard_link],
            user_id="test_user",
            org_id=None,
            session_id="test_session",
            correlation_id="test_correlation"
        )
        assert writeback_entry.id == "test_writeback"
        assert len(writeback_entry.source_shards) == 1
        print("✓ WritebackEntry model working")
        
        # Test FeedbackMetrics
        metrics = FeedbackMetrics(
            total_retrievals=100,
            total_used_shards=75,
            used_shard_rate=0.75
        )
        assert metrics.total_retrievals == 100
        assert metrics.used_shard_rate == 0.75
        print("✓ FeedbackMetrics model working")
        
        return True
        
    except Exception as e:
        print(f"✗ Writeback models test failed: {e}")
        return False

def test_policy_integration():
    """Test policy integration with writeback types"""
    print("\nTesting Policy Integration...")
    
    try:
        from ai_karen_engine.services.memory_policy import MemoryPolicyManager
        from ai_karen_engine.services.memory_writeback import InteractionType
        
        # Test policy manager creation
        policy_manager = MemoryPolicyManager()
        assert policy_manager.policy is not None
        print("✓ Policy manager created")
        
        # Test policy summary
        summary = policy_manager.get_policy_summary()
        assert "policy" in summary
        assert "tier_retention_days" in summary
        print("✓ Policy summary generated")
        
        # Test interaction types are available
        interaction_types = [
            InteractionType.COPILOT_RESPONSE,
            InteractionType.USER_QUERY,
            InteractionType.USER_FEEDBACK
        ]
        
        for interaction_type in interaction_types:
            assert isinstance(interaction_type.value, str)
        print("✓ Interaction types working")
        
        return True
        
    except Exception as e:
        print(f"✗ Policy integration test failed: {e}")
        return False

def main():
    """Run core functionality tests"""
    print("Memory Pipeline Unification - Core Functionality Test")
    print("=" * 60)
    
    tests = [
        test_memory_policy_core,
        test_unified_memory_models,
        test_writeback_models,
        test_policy_integration
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All core functionality tests passed!")
        print("✓ Memory Pipeline Unification implementation is working correctly.")
        return 0
    else:
        print("✗ Some core functionality tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)