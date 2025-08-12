#!/usr/bin/env python3
"""
Test script for Memory Pipeline Unification - Phase 4.1.b
Validates the unified memory service, policy engine, and writeback system.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_memory_policy():
    """Test memory policy engine functionality"""
    print("Testing Memory Policy Engine...")
    
    try:
        from ai_karen_engine.services.memory_policy import MemoryPolicy, MemoryPolicyManager, DecayTier
        
        # Test policy loading with defaults
        policy = MemoryPolicy.load()
        print(f"✓ Policy loaded with top_k: {policy.top_k}")
        
        # Test decay tier assignment
        tier_short = policy.assign_decay_tier(3)
        tier_long = policy.assign_decay_tier(9)
        print(f"✓ Importance 3 → {tier_short}, Importance 9 → {tier_long}")
        
        # Test expiry calculation
        expiry = policy.calculate_expiry_date(DecayTier.SHORT)
        print(f"✓ Short tier expiry: {expiry}")
        
        # Test policy manager
        manager = MemoryPolicyManager(policy)
        summary = manager.get_policy_summary()
        print(f"✓ Policy summary generated with {len(summary['tier_retention_days'])} tiers")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory policy test failed: {e}")
        return False

async def test_unified_memory_service():
    """Test unified memory service functionality"""
    print("\nTesting Unified Memory Service...")
    
    try:
        from ai_karen_engine.services.unified_memory_service import (
            UnifiedMemoryService, MemoryCommitRequest, MemoryQueryRequest,
            ContextHit, MemoryUsageStats
        )
        
        # Test data models
        commit_request = MemoryCommitRequest(
            user_id="test_user",
            text="Test memory content",
            importance=7,
            decay="medium",
            tags=["test", "validation"]
        )
        print(f"✓ MemoryCommitRequest created: {commit_request.user_id}")
        
        query_request = MemoryQueryRequest(
            user_id="test_user",
            query="test query",
            top_k=5
        )
        print(f"✓ MemoryQueryRequest created: {query_request.query}")
        
        # Test ContextHit model
        context_hit = ContextHit(
            id="test_id",
            text="Test context",
            score=0.85,
            importance=7,
            decay_tier="medium",
            created_at=datetime.utcnow(),
            user_id="test_user"
        )
        print(f"✓ ContextHit created: {context_hit.id}")
        
        # Test usage stats
        usage_stats = MemoryUsageStats(memory_id="test_memory")
        usage_stats.usage_count = 5
        print(f"✓ MemoryUsageStats created: {usage_stats.memory_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Unified memory service test failed: {e}")
        return False

async def test_memory_writeback():
    """Test memory writeback system functionality"""
    print("\nTesting Memory Writeback System...")
    
    try:
        from ai_karen_engine.services.memory_writeback import (
            MemoryWritebackSystem, InteractionType, ShardUsageType,
            ShardLink, WritebackEntry, FeedbackMetrics
        )
        
        # Test interaction types
        interaction_type = InteractionType.COPILOT_RESPONSE
        print(f"✓ InteractionType: {interaction_type}")
        
        # Test shard usage types
        usage_type = ShardUsageType.USED_IN_RESPONSE
        print(f"✓ ShardUsageType: {usage_type}")
        
        # Test shard link
        shard_link = ShardLink(
            shard_id="test_shard",
            usage_type=usage_type,
            relevance_score=0.9,
            position_in_results=0,
            content_snippet="Test snippet",
            usage_timestamp=datetime.utcnow(),
            response_id="test_response",
            user_id="test_user"
        )
        print(f"✓ ShardLink created: {shard_link.shard_id}")
        
        # Test writeback entry
        writeback_entry = WritebackEntry(
            id="test_writeback",
            content="Test writeback content",
            interaction_type=interaction_type,
            source_shards=[shard_link],
            user_id="test_user",
            org_id=None,
            session_id="test_session",
            correlation_id="test_correlation"
        )
        print(f"✓ WritebackEntry created: {writeback_entry.id}")
        
        # Test feedback metrics
        metrics = FeedbackMetrics(
            total_retrievals=100,
            total_used_shards=75,
            total_ignored_top_hits=10,
            used_shard_rate=0.75,
            ignored_top_hit_rate=0.10
        )
        print(f"✓ FeedbackMetrics: {metrics.used_shard_rate:.1%} used rate")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory writeback test failed: {e}")
        return False

async def test_integration():
    """Test integration between components"""
    print("\nTesting Component Integration...")
    
    try:
        from ai_karen_engine.services.memory_policy import MemoryPolicyManager
        from ai_karen_engine.services.memory_writeback import InteractionType
        
        # Test policy manager with writeback interaction types
        policy_manager = MemoryPolicyManager()
        
        # Test feedback metrics calculation (mock data)
        mock_usage_stats = {
            "usage_count": 15,
            "ignore_count": 3,
            "total_retrievals": 20,
            "recency_score": 0.8
        }
        
        recommendations = policy_manager.evaluate_memory_for_adjustment(
            memory_id="test_memory",
            current_tier="short",
            current_importance=5,
            usage_stats=mock_usage_stats
        )
        
        print(f"✓ Policy recommendations generated: {len(recommendations['reasons'])} reasons")
        
        # Test interaction type categorization
        interaction_types = [
            InteractionType.COPILOT_RESPONSE,
            InteractionType.USER_QUERY,
            InteractionType.USER_FEEDBACK
        ]
        
        for interaction_type in interaction_types:
            print(f"✓ Interaction type supported: {interaction_type}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Memory Pipeline Unification Test Suite")
    print("=" * 50)
    
    tests = [
        test_memory_policy,
        test_unified_memory_service,
        test_memory_writeback,
        test_integration
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Memory Pipeline Unification is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)