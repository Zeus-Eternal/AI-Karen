#!/usr/bin/env python3
"""
Test script to check what models are returned by the model library API
"""

import requests
import json
import sys

def test_model_api():
    """Test the model library API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Model Library API...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/models/health", timeout=60)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"  Registry models: {health_data.get('registry_models', 'N/A')}")
            print(f"  Predefined models: {health_data.get('predefined_models', 'N/A')}")
        print()
    except Exception as e:
        print(f"Health check failed: {e}")
        print()
    
    # Test quick library endpoint
    try:
        response = requests.get(f"{base_url}/api/models/library?quick=true", timeout=60)
        print(f"Quick library: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"  Total models: {len(models)}")
            print(f"  Local count: {data.get('local_count', 0)}")
            print(f"  Available count: {data.get('available_count', 0)}")
            
            print("\n  Models found:")
            for model in models[:10]:  # Show first 10
                print(f"    - {model.get('name', 'N/A')} ({model.get('provider', 'N/A')}) [{model.get('status', 'N/A')}]")
            if len(models) > 10:
                print(f"    ... and {len(models) - 10} more")
        else:
            print(f"  Error: {response.text}")
        print()
    except Exception as e:
        print(f"Quick library failed: {e}")
        print()
    
    # Test full library endpoint
    try:
        response = requests.get(f"{base_url}/api/models/library", timeout=60)
        print(f"Full library: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"  Total models: {len(models)}")
            print(f"  Local count: {data.get('local_count', 0)}")
            print(f"  Available count: {data.get('available_count', 0)}")
            
            # Group by status
            by_status = {}
            for model in models:
                status = model.get('status', 'unknown')
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(model)
            
            print("\n  Models by status:")
            for status, status_models in by_status.items():
                print(f"    {status}: {len(status_models)}")
                for model in status_models[:3]:  # Show first 3 of each status
                    caps = model.get('capabilities', [])
                    caps_str = ', '.join(caps[:3]) if caps else 'none'
                    print(f"      - {model.get('name', 'N/A')} ({model.get('provider', 'N/A')}) [caps: {caps_str}]")
                if len(status_models) > 3:
                    print(f"      ... and {len(status_models) - 3} more")
        else:
            print(f"  Error: {response.text}")
        print()
    except Exception as e:
        print(f"Full library failed: {e}")
        print()

if __name__ == "__main__":
    test_model_api()