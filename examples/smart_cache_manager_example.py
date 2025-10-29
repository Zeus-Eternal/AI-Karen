#!/usr/bin/env python3
"""
SmartCacheManager Example

This example demonstrates the smart caching and computation reuse system
with intelligent caching, query similarity, context awareness, and predictive warming.
"""

import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, 'src')

try:
    from ai_karen_engine.services.smart_cache_manager import (
        SmartCacheManager,
        UsagePattern,
        CacheMetrics
    )
    FULL_IMPORT = True
except ImportError:
    print("Full import not available, using isolated version for demonstration")
    FULL_IMPORT = False
    # Use the isolated version from our test
    sys.path.insert(0, '.')
    from test_smart_cache_isolated import SmartCacheManagerIsolated as SmartCacheManager
    from test_smart_cache_isolated import UsagePattern, CacheMetrics


async def demonstrate_basic_caching():
    """Demonstrate basic caching functionality."""
    print("=== Basic Caching Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=10,
            max_entries=100,
            similarity_threshold=0.8,
            cache_dir=temp_dir
        )
        
        # Cache some responses
        queries_and_responses = [
            ("What is machine learning?", {
                "content": "Machine learning is a subset of AI that enables computers to learn without explicit programming.",
                "confidence": 0.95,
                "sources": ["wikipedia", "academic_papers"]
            }),
            ("How does neural network work?", {
                "content": "Neural networks work by processing data through interconnected nodes that mimic brain neurons.",
                "confidence": 0.92,
                "sources": ["research_papers", "textbooks"]
            }),
            ("What is deep learning?", {
                "content": "Deep learning uses neural networks with multiple layers to learn complex patterns in data.",
                "confidence": 0.94,
                "sources": ["academic_sources", "industry_reports"]
            })
        ]
        
        context = {"user_id": "demo_user", "session_type": "educational"}
        
        print("Caching responses...")
        for query, response in queries_and_responses:
            await cache_manager.cache_response_components(query, context, response)
            print(f"  ✓ Cached: {query[:40]}...")
        
        print(f"\nCache now contains {len(cache_manager.cache)} entries")
        
        # Test cache hits
        print("\nTesting cache retrieval...")
        for query, expected_response in queries_and_responses:
            cached_response = await cache_manager.check_cache_relevance(query, context)
            if cached_response:
                print(f"  ✓ Cache HIT for: {query[:40]}...")
            else:
                print(f"  ✗ Cache MISS for: {query[:40]}...")
        
        # Test cache miss
        new_query = "What is reinforcement learning?"
        cached_response = await cache_manager.check_cache_relevance(new_query, context)
        if cached_response:
            print(f"  ✓ Cache HIT for: {new_query[:40]}...")
        else:
            print(f"  ✗ Cache MISS for: {new_query[:40]}... (expected)")
        
        # Show metrics
        metrics = await cache_manager.get_cache_metrics()
        print(f"\nCache Metrics:")
        print(f"  - Total requests: {metrics.total_requests}")
        print(f"  - Cache hits: {metrics.cache_hits}")
        print(f"  - Cache misses: {metrics.cache_misses}")
        print(f"  - Hit rate: {metrics.hit_rate:.2%}")
        print(f"  - Memory usage: {metrics.memory_usage_bytes / 1024:.1f} KB")
        
    finally:
        shutil.rmtree(temp_dir)


async def demonstrate_component_caching():
    """Demonstrate component-based caching."""
    print("\n=== Component-Based Caching Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Cache response with reusable components
        query = "Analyze the stock market performance for tech companies"
        context = {"user_id": "trader_demo", "portfolio": "tech_focused"}
        
        response = {
            "summary": "Tech stocks showed strong performance with average gains of 12%",
            "recommendation": "Consider increasing tech allocation",
            "risk_level": "moderate"
        }
        
        # Reusable components that could be used in other queries
        components = {
            "stock_data": {
                "AAPL": {"price": 150.25, "change": "+2.5%"},
                "GOOGL": {"price": 2800.50, "change": "+1.8%"},
                "MSFT": {"price": 310.75, "change": "+3.2%"},
                "NVDA": {"price": 220.30, "change": "+5.1%"}
            },
            "market_indicators": {
                "VIX": 18.5,
                "RSI": 65,
                "MACD": "bullish",
                "moving_average_50": "above",
                "moving_average_200": "above"
            },
            "sector_analysis": {
                "technology": {"performance": "+12%", "outlook": "positive"},
                "healthcare": {"performance": "+8%", "outlook": "stable"},
                "finance": {"performance": "+6%", "outlook": "neutral"}
            }
        }
        
        print("Caching response with reusable components...")
        await cache_manager.cache_response_components(query, context, response, components)
        
        # Verify components were cached
        query_hash = cache_manager._hash_query(query)
        if query_hash in cache_manager.component_cache:
            cached_components = cache_manager.component_cache[query_hash]
            print(f"  ✓ Cached {len(cached_components)} components:")
            for comp_type in cached_components.keys():
                print(f"    - {comp_type}")
        
        print(f"\nComponent cache now contains data for {len(cache_manager.component_cache)} queries")
        
    finally:
        shutil.rmtree(temp_dir)


async def demonstrate_intelligent_invalidation():
    """Demonstrate intelligent cache invalidation."""
    print("\n=== Intelligent Cache Invalidation Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Create entries with different characteristics for invalidation testing
        current_time = datetime.now()
        
        test_entries = [
            {
                "query": "What was the weather yesterday?",
                "response": {"content": "Yesterday was sunny, 75°F"},
                "relevance": 0.2,  # Low relevance (outdated)
                "age_hours": 25    # Old
            },
            {
                "query": "What is the current stock price of AAPL?",
                "response": {"content": "AAPL is trading at $150.25"},
                "relevance": 0.9,  # High relevance
                "age_hours": 1     # Recent
            },
            {
                "query": "Random trivia question",
                "response": {"content": "Random answer"},
                "relevance": 0.1,  # Very low relevance
                "age_hours": 2     # Somewhat recent
            },
            {
                "query": "How to invest in stocks?",
                "response": {"content": "Comprehensive investment guide..."},
                "relevance": 0.8,  # High relevance
                "age_hours": 12    # Moderate age
            }
        ]
        
        context = {"user_id": "invalidation_demo"}
        
        print("Creating cache entries with different characteristics...")
        for i, entry_data in enumerate(test_entries):
            # Simulate different ages by adjusting timestamps
            timestamp = current_time - timedelta(hours=entry_data["age_hours"])
            
            await cache_manager.cache_response_components(
                entry_data["query"], context, entry_data["response"]
            )
            
            # Manually adjust entry characteristics for demonstration
            query_hash = cache_manager._hash_query(entry_data["query"])
            context_hash = cache_manager._hash_context(context)
            cache_key = f"{query_hash}:{context_hash}"
            
            if cache_key in cache_manager.cache:
                entry = cache_manager.cache[cache_key]
                entry.relevance_score = entry_data["relevance"]
                entry.timestamp = timestamp
                entry.last_accessed = timestamp
                
                print(f"  ✓ Entry {i+1}: relevance={entry_data['relevance']}, age={entry_data['age_hours']}h")
        
        print(f"\nBefore invalidation: {len(cache_manager.cache)} entries")
        
        # Run intelligent invalidation
        invalidation_criteria = {
            'min_relevance': 0.3,      # Remove entries with relevance < 0.3
            'max_days_unused': 1       # Remove entries unused for > 1 day
        }
        
        print(f"Running invalidation with criteria: {invalidation_criteria}")
        invalidated_count = await cache_manager.implement_intelligent_invalidation(invalidation_criteria)
        
        print(f"After invalidation: {len(cache_manager.cache)} entries")
        print(f"Invalidated {invalidated_count} entries")
        
        # Show remaining entries
        print("\nRemaining entries:")
        for key, entry in cache_manager.cache.items():
            print(f"  - Relevance: {entry.relevance_score:.1f}, Age: {(current_time - entry.timestamp).total_seconds() / 3600:.1f}h")
        
    finally:
        shutil.rmtree(temp_dir)


async def demonstrate_cache_warming():
    """Demonstrate predictive cache warming."""
    print("\n=== Cache Warming Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Create usage patterns for predictive warming
        current_time = datetime.now()
        current_hour = current_time.strftime("%H:%M")
        
        usage_patterns = [
            UsagePattern(
                query_pattern="weather forecast [LOCATION]",
                frequency=15,
                time_patterns=[current_hour, "08:00", "18:00"],  # Include current time
                context_patterns=["user:morning_commuter", "session:mobile"],
                user_patterns=["commuter_type"],
                prediction_confidence=0.85
            ),
            UsagePattern(
                query_pattern="stock market news",
                frequency=8,
                time_patterns=["09:30", "16:00"],  # Market hours, not current time
                context_patterns=["user:trader", "session:desktop"],
                user_patterns=["trader_type"],
                prediction_confidence=0.75
            ),
            UsagePattern(
                query_pattern="lunch recommendations [LOCATION]",
                frequency=12,
                time_patterns=[current_hour, "11:30", "12:00", "12:30"],  # Include current time
                context_patterns=["user:office_worker", "session:mobile"],
                user_patterns=["food_preferences"],
                prediction_confidence=0.80
            ),
            UsagePattern(
                query_pattern="traffic conditions",
                frequency=5,
                time_patterns=["23:00"],  # Not current time
                context_patterns=["user:night_shift"],
                user_patterns=[],
                prediction_confidence=0.60  # Below threshold
            )
        ]
        
        print("Usage patterns for warming:")
        for i, pattern in enumerate(usage_patterns, 1):
            matches_time = current_hour in pattern.time_patterns
            meets_confidence = pattern.prediction_confidence >= 0.7
            will_warm = matches_time and meets_confidence
            
            print(f"  {i}. {pattern.query_pattern}")
            print(f"     Frequency: {pattern.frequency}, Confidence: {pattern.prediction_confidence:.2f}")
            print(f"     Time match: {matches_time}, Confidence OK: {meets_confidence}")
            print(f"     Will warm: {'✓' if will_warm else '✗'}")
        
        print(f"\nBefore warming: {len(cache_manager.cache)} entries")
        
        # Perform cache warming
        warmed_count = await cache_manager.warm_cache_based_on_patterns(usage_patterns)
        
        print(f"After warming: {len(cache_manager.cache)} entries")
        print(f"Successfully warmed {warmed_count} entries")
        
        # Show warmed entries
        if cache_manager.cache:
            print("\nWarmed cache entries:")
            for key, entry in cache_manager.cache.items():
                if "warmed" in entry.tags:
                    print(f"  - Pattern: {entry.content.get('pattern', 'unknown')}")
                    print(f"    Confidence: {entry.content.get('confidence', 'unknown')}")
                    print(f"    Tags: {', '.join(entry.tags)}")
        
    finally:
        shutil.rmtree(temp_dir)


async def demonstrate_memory_optimization():
    """Demonstrate memory optimization."""
    print("\n=== Memory Optimization Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(
            max_memory_mb=1,  # Small limit to trigger optimization
            cache_dir=temp_dir
        )
        
        # Create entries with varying sizes and relevance
        print("Creating cache entries with different characteristics...")
        
        entries_data = [
            {"size": "small", "relevance": 0.9, "content": "Short answer"},
            {"size": "medium", "relevance": 0.7, "content": "Medium length answer with more details"},
            {"size": "large", "relevance": 0.5, "content": "Very long answer " + "x" * 1000},
            {"size": "huge", "relevance": 0.2, "content": "Extremely long answer " + "y" * 5000},
            {"size": "small", "relevance": 0.8, "content": "Another short answer"},
            {"size": "large", "relevance": 0.1, "content": "Another long answer " + "z" * 2000}
        ]
        
        context = {"user_id": "memory_demo"}
        
        for i, entry_data in enumerate(entries_data):
            query = f"Query {i+1} - {entry_data['size']} response"
            response = {
                "content": entry_data["content"],
                "size_category": entry_data["size"]
            }
            
            await cache_manager.cache_response_components(query, context, response)
            
            # Adjust relevance score
            query_hash = cache_manager._hash_query(query)
            context_hash = cache_manager._hash_context(context)
            cache_key = f"{query_hash}:{context_hash}"
            
            if cache_key in cache_manager.cache:
                cache_manager.cache[cache_key].relevance_score = entry_data["relevance"]
            
            print(f"  ✓ Entry {i+1}: {entry_data['size']} size, {entry_data['relevance']} relevance")
        
        # Show initial state
        initial_memory = cache_manager._calculate_memory_usage()
        print(f"\nInitial state:")
        print(f"  - Entries: {len(cache_manager.cache)}")
        print(f"  - Memory usage: {initial_memory / 1024:.1f} KB")
        
        # Run memory optimization
        print("\nRunning memory optimization...")
        optimization_results = await cache_manager.optimize_cache_memory_usage()
        
        # Show results
        print(f"\nOptimization results:")
        print(f"  - Initial entries: {optimization_results.get('initial_entries', 0)}")
        print(f"  - Final entries: {optimization_results.get('final_entries', 0)}")
        print(f"  - Evicted entries: {optimization_results.get('evicted_entries', 0)}")
        print(f"  - Memory saved: {optimization_results.get('memory_saved_bytes', 0) / 1024:.1f} KB")
        
        # Show remaining entries
        print(f"\nRemaining entries:")
        for key, entry in cache_manager.cache.items():
            print(f"  - Relevance: {entry.relevance_score:.1f}, Size: {entry.size_bytes} bytes")
        
    finally:
        shutil.rmtree(temp_dir)


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring and metrics."""
    print("\n=== Performance Monitoring Demonstration ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        cache_manager = SmartCacheManager(cache_dir=temp_dir)
        
        # Simulate various cache operations
        print("Simulating cache operations...")
        
        # Cache some responses
        for i in range(10):
            query = f"Performance test query {i}"
            context = {"user_id": f"perf_user_{i % 3}", "batch": i // 5}
            response = {"content": f"Response {i}", "data": "x" * (100 * i)}
            
            await cache_manager.cache_response_components(query, context, response)
        
        # Generate cache hits and misses
        hit_count = 0
        miss_count = 0
        
        # Test existing queries (should be hits)
        for i in range(10):
            query = f"Performance test query {i}"
            context = {"user_id": f"perf_user_{i % 3}", "batch": i // 5}
            cached_response = await cache_manager.check_cache_relevance(query, context)
            if cached_response:
                hit_count += 1
            else:
                miss_count += 1
        
        # Test new queries (should be misses)
        for i in range(5):
            query = f"New query {i}"
            context = {"user_id": "new_user"}
            cached_response = await cache_manager.check_cache_relevance(query, context)
            if cached_response:
                hit_count += 1
            else:
                miss_count += 1
        
        # Get comprehensive metrics
        metrics = await cache_manager.get_cache_metrics()
        
        print(f"\nPerformance Metrics:")
        print(f"  - Total requests: {metrics.total_requests}")
        print(f"  - Cache hits: {metrics.cache_hits}")
        print(f"  - Cache misses: {metrics.cache_misses}")
        print(f"  - Hit rate: {metrics.hit_rate:.2%}")
        print(f"  - Miss rate: {metrics.miss_rate:.2%}")
        print(f"  - Memory usage: {metrics.memory_usage_bytes / 1024:.1f} KB")
        print(f"  - Average response time: {metrics.average_response_time:.4f}s")
        print(f"  - Eviction count: {metrics.eviction_count}")
        
        # Performance analysis
        print(f"\nPerformance Analysis:")
        if metrics.hit_rate >= 0.8:
            print("  ✓ Excellent cache hit rate (≥80%)")
        elif metrics.hit_rate >= 0.6:
            print("  ✓ Good cache hit rate (≥60%)")
        else:
            print("  ⚠ Cache hit rate could be improved")
        
        if metrics.average_response_time < 0.01:
            print("  ✓ Excellent response time (<10ms)")
        elif metrics.average_response_time < 0.1:
            print("  ✓ Good response time (<100ms)")
        else:
            print("  ⚠ Response time could be improved")
        
        memory_mb = metrics.memory_usage_bytes / (1024 * 1024)
        if memory_mb < 1:
            print("  ✓ Efficient memory usage (<1MB)")
        elif memory_mb < 10:
            print("  ✓ Reasonable memory usage (<10MB)")
        else:
            print("  ⚠ High memory usage - consider optimization")
        
    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Run all demonstrations."""
    print("SmartCacheManager Comprehensive Demonstration")
    print("=" * 60)
    
    if not FULL_IMPORT:
        print("Note: Using isolated version for demonstration")
        print("=" * 60)
    
    try:
        await demonstrate_basic_caching()
        await demonstrate_component_caching()
        await demonstrate_intelligent_invalidation()
        await demonstrate_cache_warming()
        await demonstrate_memory_optimization()
        await demonstrate_performance_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSmartCacheManager Features Demonstrated:")
        print("✓ Intelligent caching based on query similarity")
        print("✓ Cache relevance checking with context and freshness")
        print("✓ Component-based caching for reusable response parts")
        print("✓ Intelligent cache invalidation based on content relevance")
        print("✓ Cache warming system based on usage patterns and predictive analysis")
        print("✓ Memory optimization system for cached content management")
        print("✓ Comprehensive performance monitoring and analytics")
        print("✓ Efficient computation reuse and resource optimization")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())