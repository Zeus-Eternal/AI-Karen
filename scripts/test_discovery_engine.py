#!/usr/bin/env python3
"""
Test script to check the discovery engine directly
"""

import sys
import os
sys.path.append('src')

def test_discovery_engine():
    """Test the discovery engine directly"""
    try:
        from ai_karen_engine.services.model_discovery_engine import ModelDiscoveryEngine
        
        print("Testing Model Discovery Engine...")
        print("=" * 50)
        
        # Initialize discovery engine
        discovery_engine = ModelDiscoveryEngine()
        
        # Get discovered models
        models = discovery_engine.get_discovered_models()
        print(f"Found {len(models)} discovered models")
        
        if models:
            print("\nDiscovered models:")
            for model in models[:10]:  # Show first 10
                print(f"  - {model.name} ({model.type}) [{model.status}]")
                if hasattr(model, 'capabilities') and model.capabilities:
                    caps = ', '.join(model.capabilities[:3])
                    print(f"    Capabilities: {caps}")
            if len(models) > 10:
                print(f"  ... and {len(models) - 10} more")
        else:
            print("No models found in discovery engine")
            
        # Check cache file
        cache_file = discovery_engine.discovery_cache_file
        print(f"\nCache file: {cache_file}")
        print(f"Cache file exists: {cache_file.exists()}")
        if cache_file.exists():
            print(f"Cache file size: {cache_file.stat().st_size} bytes")
        
    except Exception as e:
        print(f"Error testing discovery engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_discovery_engine()