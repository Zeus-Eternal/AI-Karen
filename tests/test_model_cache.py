#!/usr/bin/env python3
"""
Test script for model library caching functionality.

This script demonstrates the caching behavior of the model library service,
including cache validation, invalidation, and refresh functionality.
"""

import time
import json
from pathlib import Path
from src.ai_karen_engine.services.model_library_service import ModelLibraryService

def test_model_cache():
    """Test the model library caching functionality."""
    print("Testing Model Library Caching...")
    print("=" * 50)
    
    # Initialize service
    service = ModelLibraryService()
    
    # Test 1: Initial cache population
    print("\n1. Initial cache population:")
    start_time = time.time()
    models = service.get_available_models()
    initial_time = time.time() - start_time
    print(f"   First call took {initial_time:.3f} seconds")
    print(f"   Found {len(models)} models")
    
    # Test 2: Cached retrieval
    print("\n2. Cached retrieval:")
    start_time = time.time()
    models_cached = service.get_available_models()
    cached_time = time.time() - start_time
    print(f"   Second call took {cached_time:.3f} seconds")
    print(f"   Found {len(models_cached)} models")
    print(f"   Speed improvement: {initial_time / cached_time:.1f}x faster")
    
    # Test 3: Cache info
    print("\n3. Cache information:")
    cache_info = service.get_cache_info()
    print(f"   Cache valid: {cache_info['cache_valid']}")
    print(f"   Cache age: {cache_info['cache_age_seconds']:.1f} seconds")
    print(f"   Cache TTL: {cache_info['cache_ttl_seconds']} seconds")
    print(f"   Cached models: {cache_info['cached_model_count']}")
    
    # Test 4: Fast mode caching
    print("\n4. Fast mode caching:")
    start_time = time.time()
    models_fast = service.get_available_models_fast()
    fast_time = time.time() - start_time
    print(f"   Fast call took {fast_time:.3f} seconds")
    print(f"   Found {len(models_fast)} models")
    
    # Test 5: Cache refresh
    print("\n5. Cache refresh:")
    refresh_info = service.refresh_model_cache()
    print(f"   Cache refreshed: {refresh_info['cache_refreshed']}")
    print(f"   Old model count: {refresh_info['old_model_count']}")
    print(f"   New model count: {refresh_info['new_model_count']}")
    
    # Test 6: TTL configuration
    print("\n6. TTL configuration:")
    original_ttl = service._cache_ttl
    service.set_cache_ttl(60)  # 1 minute
    print(f"   TTL changed from {original_ttl} to {service._cache_ttl} seconds")
    
    # Test 7: Cache invalidation simulation
    print("\n7. Cache invalidation simulation:")
    print("   Simulating registry file modification...")
    
    # Touch the registry file to simulate modification
    registry_path = Path("model_registry.json")
    if registry_path.exists():
        registry_path.touch()
        time.sleep(0.1)  # Small delay to ensure mtime changes
        
        # Check if cache is now invalid
        cache_info_after = service.get_cache_info()
        print(f"   Cache valid after file touch: {cache_info_after['cache_valid']}")
        
        # Get models again (should rebuild cache)
        start_time = time.time()
        models_after_invalidation = service.get_available_models()
        rebuild_time = time.time() - start_time
        print(f"   Cache rebuild took {rebuild_time:.3f} seconds")
    else:
        print("   Registry file not found, skipping invalidation test")
    
    print("\n" + "=" * 50)
    print("Cache testing completed!")

if __name__ == "__main__":
    test_model_cache()