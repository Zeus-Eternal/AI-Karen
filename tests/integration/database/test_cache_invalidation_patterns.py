"""
Cache Invalidation Pattern Validation Tests

Comprehensive tests for cache invalidation patterns and validation across Redis and PostgreSQL.
Tests various cache invalidation scenarios, consistency patterns, and edge cases.

Requirements: 2.2, 2.3
"""

import asyncio
import pytest
import time
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional, Set
import threading
import random

from ai_karen_engine.services.redis_connection_manager import get_redis_manager
from ai_karen_engine.services.database_connection_manager import get_database_manager
from ai_karen_engine.services.database_consistency_validator import DatabaseConsistencyValidator


class TestCacheInvalidationPatterns:
    """Test various cache invalidation patterns"""

    @pytest.fixture
    async def cache_environment(self):
        """Set up cache testing environment"""
        # Mock cache storage
        cache_data = {}
        cache_ttl = {}
        cache_access_log = []
        cache_lock = threading.Lock()
        
        # Mock Redis manager
        mock_redis_manager = AsyncMock()
        
        async def mock_get(key: str):
            with cache_lock:
                cache_access_log.append({"operation": "get", "key": key, "timestamp": time.time()})
                if key in cache_data:
                    # Check TTL
                    if key in cache_ttl and time.time() > cache_ttl[key]:
                        del cache_data[key]
                        del cache_ttl[key]
                        return None
                    return cache_data[key]
                return None
        
        async def mock_set(key: str, value: str, ex: Optional[int] = None, **kwargs):
            with cache_lock:
                cache_access_log.append({"operation": "set", "key": key, "timestamp": time.time()})
                cache_data[key] = value
                if ex:
                    cache_ttl[key] = time.time() + ex
                return True
        
        async def mock_delete(key: str):
            with cache_lock:
                cache_access_log.append({"operation": "delete", "key": key, "timestamp": time.time()})
                deleted = key in cache_data
                if deleted:
                    del cache_data[key]
                if key in cache_ttl:
                    del cache_ttl[key]
                return deleted
        
        async def mock_exists(key: str):
            with cache_lock:
                return key in cache_data
        
        async def mock_keys(pattern: str):
            with cache_lock:
                if pattern.endswith("*"):
                    prefix = pattern[:-1]
                    return [key for key in cache_data.keys() if key.startswith(prefix)]
                return [key for key in cache_data.keys() if key == pattern]
        
        mock_redis_manager.get = mock_get
        mock_redis_manager.set = mock_set
        mock_redis_manager.delete = mock_delete
        mock_redis_manager.exists = mock_exists
        mock_redis_manager.keys = mock_keys
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {
            "memory_cache_size": lambda: len(cache_data),
            "connection_failures": 0,
        }
        
        # Mock database manager
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        mock_db_manager.is_degraded.return_value = False
        
        return {
            "redis_manager": mock_redis_manager,
            "db_manager": mock_db_manager,
            "session": mock_session,
            "cache_data": cache_data,
            "cache_ttl": cache_ttl,
            "cache_access_log": cache_access_log,
        }

    @pytest.mark.asyncio
    async def test_write_through_cache_invalidation(self, cache_environment):
        """Test write-through cache invalidation pattern"""
        redis_manager = cache_environment["redis_manager"]
        db_manager = cache_environment["db_manager"]
        session = cache_environment["session"]
        cache_data = cache_environment["cache_data"]
        
        # Simulate write-through cache pattern
        user_id = "user:123"
        user_data = {"id": 123, "name": "John Doe", "email": "john@example.com"}
        cache_key = f"user:{user_id}"
        
        # Step 1: Write to cache
        await redis_manager.set(cache_key, json.dumps(user_data))
        
        # Step 2: Write to database (simulated)
        session.execute.return_value = Mock()
        session.commit.return_value = None
        
        # Verify cache contains data
        cached_data = await redis_manager.get(cache_key)
        assert cached_data == json.dumps(user_data)
        
        # Step 3: Update data (should invalidate cache)
        updated_user_data = {"id": 123, "name": "John Updated", "email": "john.updated@example.com"}
        
        # Write-through: update database first, then invalidate cache
        await session.execute(text("UPDATE users SET name = :name WHERE id = :id"))
        await session.commit()
        
        # Invalidate cache
        await redis_manager.delete(cache_key)
        
        # Verify cache was invalidated
        cached_data_after_update = await redis_manager.get(cache_key)
        assert cached_data_after_update is None
        
        # Step 4: Next read should miss cache and reload from database
        # Simulate cache miss -> database read -> cache populate
        await redis_manager.set(cache_key, json.dumps(updated_user_data))
        
        # Verify updated data is now cached
        final_cached_data = await redis_manager.get(cache_key)
        assert final_cached_data == json.dumps(updated_user_data)

    @pytest.mark.asyncio
    async def test_write_behind_cache_invalidation(self, cache_environment):
        """Test write-behind (write-back) cache invalidation pattern"""
        redis_manager = cache_environment["redis_manager"]
        cache_data = cache_environment["cache_data"]
        cache_access_log = cache_environment["cache_access_log"]
        
        # Simulate write-behind cache pattern
        user_id = "user:456"
        cache_key = f"user:{user_id}"
        
        # Step 1: Write to cache immediately
        user_data = {"id": 456, "name": "Jane Doe", "email": "jane@example.com"}
        await redis_manager.set(cache_key, json.dumps(user_data))
        
        # Step 2: Mark for background database write (simulated with metadata)
        dirty_key = f"{cache_key}:dirty"
        await redis_manager.set(dirty_key, "1", ex=300)  # 5 minute TTL for dirty flag
        
        # Verify cache contains data and dirty flag
        cached_data = await redis_manager.get(cache_key)
        dirty_flag = await redis_manager.get(dirty_key)
        assert cached_data == json.dumps(user_data)
        assert dirty_flag == "1"
        
        # Step 3: Simulate background write to database
        await asyncio.sleep(0.1)  # Simulate async background process
        
        # After successful database write, remove dirty flag
        await redis_manager.delete(dirty_key)
        
        # Verify dirty flag was removed
        dirty_flag_after_write = await redis_manager.get(dirty_key)
        assert dirty_flag_after_write is None
        
        # Cache data should still be present
        cached_data_after_write = await redis_manager.get(cache_key)
        assert cached_data_after_write == json.dumps(user_data)
        
        # Verify access pattern in log
        write_operations = [op for op in cache_access_log if op["operation"] == "set"]
        delete_operations = [op for op in cache_access_log if op["operation"] == "delete"]
        
        assert len(write_operations) >= 2  # User data + dirty flag
        assert len(delete_operations) >= 1  # Dirty flag removal

    @pytest.mark.asyncio
    async def test_cache_aside_invalidation_pattern(self, cache_environment):
        """Test cache-aside (lazy loading) invalidation pattern"""
        redis_manager = cache_environment["redis_manager"]
        db_manager = cache_environment["db_manager"]
        session = cache_environment["session"]
        
        # Simulate cache-aside pattern
        user_id = "user:789"
        cache_key = f"user:{user_id}"
        
        # Step 1: Cache miss - data not in cache
        cached_data = await redis_manager.get(cache_key)
        assert cached_data is None
        
        # Step 2: Load from database
        user_data = {"id": 789, "name": "Bob Smith", "email": "bob@example.com"}
        
        # Mock database query result
        mock_result = Mock()
        mock_result.fetchone.return_value = (789, "Bob Smith", "bob@example.com")
        session.execute.return_value = mock_result
        
        # Simulate loading from database
        db_result = await session.execute(text("SELECT id, name, email FROM users WHERE id = :id"))
        db_row = db_result.fetchone()
        
        # Step 3: Populate cache with database data
        if db_row:
            await redis_manager.set(cache_key, json.dumps(user_data), ex=3600)  # 1 hour TTL
        
        # Verify cache was populated
        cached_data_after_load = await redis_manager.get(cache_key)
        assert cached_data_after_load == json.dumps(user_data)
        
        # Step 4: Update data in database
        updated_user_data = {"id": 789, "name": "Bob Updated", "email": "bob.updated@example.com"}
        
        # Update database
        await session.execute(text("UPDATE users SET name = :name WHERE id = :id"))
        await session.commit()
        
        # Step 5: Invalidate cache (cache-aside pattern)
        await redis_manager.delete(cache_key)
        
        # Verify cache was invalidated
        cached_data_after_invalidation = await redis_manager.get(cache_key)
        assert cached_data_after_invalidation is None
        
        # Step 6: Next read will be cache miss and reload from database
        mock_result.fetchone.return_value = (789, "Bob Updated", "bob.updated@example.com")
        
        # Simulate cache miss -> database load -> cache populate cycle
        cached_data = await redis_manager.get(cache_key)
        if cached_data is None:
            db_result = await session.execute(text("SELECT id, name, email FROM users WHERE id = :id"))
            db_row = db_result.fetchone()
            if db_row:
                await redis_manager.set(cache_key, json.dumps(updated_user_data), ex=3600)
        
        # Verify updated data is now cached
        final_cached_data = await redis_manager.get(cache_key)
        assert final_cached_data == json.dumps(updated_user_data)

    @pytest.mark.asyncio
    async def test_bulk_cache_invalidation_pattern(self, cache_environment):
        """Test bulk cache invalidation patterns"""
        redis_manager = cache_environment["redis_manager"]
        cache_data = cache_environment["cache_data"]
        
        # Set up multiple related cache entries
        user_ids = [100, 101, 102, 103, 104]
        cache_keys = []
        
        for user_id in user_ids:
            cache_key = f"user:{user_id}"
            cache_keys.append(cache_key)
            user_data = {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
            await redis_manager.set(cache_key, json.dumps(user_data))
            
            # Also set related cache entries
            profile_key = f"profile:{user_id}"
            await redis_manager.set(profile_key, json.dumps({"user_id": user_id, "bio": f"Bio for user {user_id}"}))
            cache_keys.append(profile_key)
        
        # Verify all entries are cached
        assert len(cache_data) == len(user_ids) * 2  # user + profile for each
        
        # Test pattern-based bulk invalidation
        # Invalidate all user-related cache entries
        user_keys = await redis_manager.keys("user:*")
        profile_keys = await redis_manager.keys("profile:*")
        
        # Bulk delete user entries
        for key in user_keys:
            await redis_manager.delete(key)
        
        # Verify user entries were deleted
        remaining_user_keys = await redis_manager.keys("user:*")
        assert len(remaining_user_keys) == 0
        
        # Profile entries should still exist
        remaining_profile_keys = await redis_manager.keys("profile:*")
        assert len(remaining_profile_keys) == len(user_ids)
        
        # Test bulk invalidation of all related entries
        for key in profile_keys:
            await redis_manager.delete(key)
        
        # Verify all entries were deleted
        assert len(cache_data) == 0

    @pytest.mark.asyncio
    async def test_ttl_based_cache_invalidation(self, cache_environment):
        """Test TTL-based cache invalidation patterns"""
        redis_manager = cache_environment["redis_manager"]
        cache_data = cache_environment["cache_data"]
        cache_ttl = cache_environment["cache_ttl"]
        
        # Test different TTL scenarios
        test_cases = [
            {"key": "short_ttl:1", "value": "data1", "ttl": 1},      # 1 second
            {"key": "medium_ttl:2", "value": "data2", "ttl": 2},     # 2 seconds
            {"key": "long_ttl:3", "value": "data3", "ttl": 5},       # 5 seconds
            {"key": "no_ttl:4", "value": "data4", "ttl": None},      # No TTL
        ]
        
        # Set cache entries with different TTLs
        for case in test_cases:
            if case["ttl"]:
                await redis_manager.set(case["key"], case["value"], ex=case["ttl"])
            else:
                await redis_manager.set(case["key"], case["value"])
        
        # Verify all entries are initially present
        for case in test_cases:
            cached_value = await redis_manager.get(case["key"])
            assert cached_value == case["value"]
        
        # Wait for short TTL to expire
        await asyncio.sleep(1.1)
        
        # Check TTL expiration
        short_ttl_value = await redis_manager.get("short_ttl:1")
        medium_ttl_value = await redis_manager.get("medium_ttl:2")
        long_ttl_value = await redis_manager.get("long_ttl:3")
        no_ttl_value = await redis_manager.get("no_ttl:4")
        
        assert short_ttl_value is None  # Should be expired
        assert medium_ttl_value == "data2"  # Should still exist
        assert long_ttl_value == "data3"   # Should still exist
        assert no_ttl_value == "data4"     # Should still exist
        
        # Wait for medium TTL to expire
        await asyncio.sleep(1.1)
        
        medium_ttl_value_after = await redis_manager.get("medium_ttl:2")
        long_ttl_value_after = await redis_manager.get("long_ttl:3")
        no_ttl_value_after = await redis_manager.get("no_ttl:4")
        
        assert medium_ttl_value_after is None  # Should be expired
        assert long_ttl_value_after == "data3"  # Should still exist
        assert no_ttl_value_after == "data4"    # Should still exist
        
        # Verify TTL tracking
        assert "short_ttl:1" not in cache_ttl  # Should be removed
        assert "medium_ttl:2" not in cache_ttl  # Should be removed
        assert "long_ttl:3" in cache_ttl        # Should still have TTL
        assert "no_ttl:4" not in cache_ttl      # Never had TTL

    @pytest.mark.asyncio
    async def test_cache_invalidation_race_conditions(self, cache_environment):
        """Test cache invalidation under race conditions"""
        redis_manager = cache_environment["redis_manager"]
        cache_data = cache_environment["cache_data"]
        cache_access_log = cache_environment["cache_access_log"]
        
        # Test concurrent cache operations
        cache_key = "race_test:item"
        initial_value = "initial_data"
        
        # Set initial value
        await redis_manager.set(cache_key, initial_value)
        
        # Simulate race condition: concurrent reads and invalidations
        async def reader_task(reader_id: int, iterations: int):
            """Task that reads from cache"""
            read_results = []
            for i in range(iterations):
                try:
                    value = await redis_manager.get(cache_key)
                    read_results.append({
                        "reader_id": reader_id,
                        "iteration": i,
                        "value": value,
                        "timestamp": time.time(),
                    })
                    await asyncio.sleep(0.01)  # Small delay
                except Exception as e:
                    read_results.append({
                        "reader_id": reader_id,
                        "iteration": i,
                        "error": str(e),
                        "timestamp": time.time(),
                    })
            return read_results
        
        async def writer_task(writer_id: int, iterations: int):
            """Task that writes to cache"""
            write_results = []
            for i in range(iterations):
                try:
                    new_value = f"data_{writer_id}_{i}"
                    await redis_manager.set(cache_key, new_value)
                    write_results.append({
                        "writer_id": writer_id,
                        "iteration": i,
                        "value": new_value,
                        "timestamp": time.time(),
                    })
                    await asyncio.sleep(0.02)  # Small delay
                except Exception as e:
                    write_results.append({
                        "writer_id": writer_id,
                        "iteration": i,
                        "error": str(e),
                        "timestamp": time.time(),
                    })
            return write_results
        
        async def invalidator_task(invalidator_id: int, iterations: int):
            """Task that invalidates cache"""
            invalidation_results = []
            for i in range(iterations):
                try:
                    deleted = await redis_manager.delete(cache_key)
                    invalidation_results.append({
                        "invalidator_id": invalidator_id,
                        "iteration": i,
                        "deleted": deleted,
                        "timestamp": time.time(),
                    })
                    await asyncio.sleep(0.03)  # Small delay
                except Exception as e:
                    invalidation_results.append({
                        "invalidator_id": invalidator_id,
                        "iteration": i,
                        "error": str(e),
                        "timestamp": time.time(),
                    })
            return invalidation_results
        
        # Run concurrent tasks
        num_readers = 3
        num_writers = 2
        num_invalidators = 1
        iterations_per_task = 5
        
        tasks = []
        
        # Add reader tasks
        for i in range(num_readers):
            tasks.append(reader_task(i, iterations_per_task))
        
        # Add writer tasks
        for i in range(num_writers):
            tasks.append(writer_task(i, iterations_per_task))
        
        # Add invalidator tasks
        for i in range(num_invalidators):
            tasks.append(invalidator_task(i, iterations_per_task))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        reader_results = results[:num_readers]
        writer_results = results[num_readers:num_readers + num_writers]
        invalidator_results = results[num_readers + num_writers:]
        
        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Task failed with exception: {result}"
        
        # Verify operations completed
        total_reads = sum(len(r) for r in reader_results)
        total_writes = sum(len(r) for r in writer_results)
        total_invalidations = sum(len(r) for r in invalidator_results)
        
        assert total_reads > 0, "Should have completed read operations"
        assert total_writes > 0, "Should have completed write operations"
        assert total_invalidations > 0, "Should have completed invalidation operations"
        
        # Verify cache operations were logged
        total_logged_operations = len(cache_access_log)
        expected_operations = total_reads + total_writes + total_invalidations
        assert total_logged_operations >= expected_operations * 0.8, \
            f"Should have logged most operations: {total_logged_operations} >= {expected_operations * 0.8}"

    @pytest.mark.asyncio
    async def test_cache_consistency_validation_patterns(self, cache_environment):
        """Test cache consistency validation patterns"""
        redis_manager = cache_environment["redis_manager"]
        db_manager = cache_environment["db_manager"]
        session = cache_environment["session"]
        
        # Create consistency validator
        validator = DatabaseConsistencyValidator()
        
        # Set up test data with inconsistencies
        cache_entries = {
            "user:1": '{"id": 1, "name": "Alice", "version": 1}',
            "user:2": '{"id": 2, "name": "Bob", "version": 1}',
            "user:3": '{"id": 3, "name": "Charlie", "version": 2}',  # Newer version in cache
            "user:4": '{"id": 4, "name": "David", "version": 1}',    # User deleted from DB
        }
        
        # Populate cache
        for key, value in cache_entries.items():
            await redis_manager.set(key, value)
        
        # Mock database data (different from cache to simulate inconsistency)
        db_users = [
            {"id": 1, "name": "Alice Updated", "version": 2},  # Newer in DB
            {"id": 2, "name": "Bob", "version": 1},            # Consistent
            {"id": 3, "name": "Charlie Old", "version": 1},    # Older in DB
            # User 4 deleted from DB
        ]
        
        # Mock database queries
        def execute_side_effect(query, *args, **kwargs):
            result = Mock()
            if "SELECT" in str(query) and "users" in str(query):
                result.fetchall.return_value = [
                    (user["id"], user["name"], user["version"]) for user in db_users
                ]
            else:
                result.fetchall.return_value = []
                result.scalar.return_value = 0
            return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(validator, 'redis_manager', redis_manager), \
             patch.object(validator, 'db_manager', db_manager):
            
            # Perform consistency validation
            inconsistencies = []
            
            # Check each cached user against database
            for cache_key, cache_value in cache_entries.items():
                user_id = int(cache_key.split(":")[1])
                cached_user = json.loads(cache_value)
                
                # Find corresponding DB user
                db_user = next((u for u in db_users if u["id"] == user_id), None)
                
                if not db_user:
                    inconsistencies.append({
                        "type": "orphaned_cache",
                        "key": cache_key,
                        "issue": "Cache entry exists but no corresponding DB record",
                    })
                elif cached_user["version"] != db_user["version"]:
                    inconsistencies.append({
                        "type": "version_mismatch",
                        "key": cache_key,
                        "cache_version": cached_user["version"],
                        "db_version": db_user["version"],
                        "issue": "Cache and DB versions don't match",
                    })
                elif cached_user["name"] != db_user["name"]:
                    inconsistencies.append({
                        "type": "data_mismatch",
                        "key": cache_key,
                        "cache_name": cached_user["name"],
                        "db_name": db_user["name"],
                        "issue": "Cache and DB data don't match",
                    })
            
            # Verify inconsistencies were detected
            assert len(inconsistencies) > 0, "Should detect cache inconsistencies"
            
            # Check specific inconsistency types
            orphaned_cache = [i for i in inconsistencies if i["type"] == "orphaned_cache"]
            version_mismatches = [i for i in inconsistencies if i["type"] == "version_mismatch"]
            data_mismatches = [i for i in inconsistencies if i["type"] == "data_mismatch"]
            
            assert len(orphaned_cache) == 1, "Should detect orphaned cache entry (user:4)"
            assert len(version_mismatches) >= 1, "Should detect version mismatches"
            
            # Test consistency repair patterns
            for inconsistency in inconsistencies:
                if inconsistency["type"] == "orphaned_cache":
                    # Remove orphaned cache entry
                    await redis_manager.delete(inconsistency["key"])
                elif inconsistency["type"] == "version_mismatch":
                    # Update cache with DB data (assuming DB is authoritative)
                    user_id = int(inconsistency["key"].split(":")[1])
                    db_user = next((u for u in db_users if u["id"] == user_id), None)
                    if db_user:
                        await redis_manager.set(inconsistency["key"], json.dumps(db_user))
            
            # Verify repairs
            orphaned_key = "user:4"
            orphaned_value = await redis_manager.get(orphaned_key)
            assert orphaned_value is None, "Orphaned cache entry should be removed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])