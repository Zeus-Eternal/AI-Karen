#!/usr/bin/env python3
"""
API Structure validation for LlamaCpp migration
Tests that the API routes and imports are correctly structured
"""

import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any

def test_plugin_import_structure():
    """Test that the plugin can be imported and has correct structure"""
    plugin_file = Path("plugin_marketplace/ai/llm-services/llama/llama_plugin.py")
    
    if not plugin_file.exists():
        return {"status": "SKIP", "reason": "Plugin file not found"}
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("llama_plugin", plugin_file)
        module = importlib.util.module_from_spec(spec)
        
        # Check if it has the required router
        if hasattr(module, 'router'):
            return {"status": "PASS", "summary": "Plugin has router attribute"}
        else:
            return {"status": "FAIL", "summary": "Plugin missing router attribute"}
            
    except Exception as e:
        return {"status": "FAIL", "error": str(e), "summary": "Import failed"}

def test_client_import_structure():
    """Test that the client can be imported and has correct structure"""
    client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
    
    if not client_file.exists():
        return {"status": "SKIP", "reason": "Client file not found"}
    
    try:
        # Add src to path temporarily
        sys.path.insert(0, str(Path.cwd() / "src"))
        
        # Load the module
        spec = importlib.util.spec_from_file_location("llama_client", client_file)
        module = importlib.util.module_from_spec(spec)
        
        # Check if it has the required classes and functions
        required_items = ['LlamaCppEngine', 'llamacpp_inprocess_client', 'health_check']
        missing_items = [item for item in required_items if not hasattr(module, item)]
        
        if not missing_items:
            return {"status": "PASS", "summary": "Client has all required items"}
        else:
            return {"status": "FAIL", "missing": missing_items, 
                   "summary": f"Client missing: {', '.join(missing_items)}"}
            
    except Exception as e:
        return {"status": "FAIL", "error": str(e), "summary": "Import failed"}
    finally:
        # Remove src from path
        if str(Path.cwd() / "src") in sys.path:
            sys.path.remove(str(Path.cwd() / "src"))

def test_route_definitions():
    """Test that routes are properly defined with llamacpp prefix"""
    plugin_file = Path("plugin_marketplace/ai/llm-services/llama/llama_plugin.py")
    
    if not plugin_file.exists():
        return {"status": "SKIP", "reason": "Plugin file not found"}
    
    content = plugin_file.read_text()
    
    # Expected routes
    expected_routes = [
        "/llm/llamacpp/health",
        "/llm/llamacpp/models", 
        "/llm/llamacpp/chat",
        "/llm/llamacpp/achat",
        "/llm/llamacpp/embedding",
        "/llm/llamacpp/switch"
    ]
    
    # Check for route decorators
    found_routes = []
    for route in expected_routes:
        route_name = route.split('/')[-1]  # Get the endpoint name
        if f'@router.get("/{route_name}"' in content or f'@router.post("/{route_name}"' in content:
            found_routes.append(route_name)
    
    if len(found_routes) >= 5:  # At least 5 out of 6 routes
        return {"status": "PASS", "found": found_routes, 
               "summary": f"Found {len(found_routes)} route definitions"}
    else:
        return {"status": "FAIL", "found": found_routes,
               "summary": f"Only found {len(found_routes)} route definitions"}

def test_backward_compatibility_structure():
    """Test if backward compatibility aliases are implemented"""
    plugin_file = Path("plugin_marketplace/ai/llm-services/llama/llama_plugin.py")
    
    if not plugin_file.exists():
        return {"status": "SKIP", "reason": "Plugin file not found"}
    
    content = plugin_file.read_text()
    
    # Look for legacy ollama route aliases or redirects
    has_ollama_routes = "/llm/ollama" in content
    has_redirect_logic = "redirect" in content.lower() or "alias" in content.lower()
    
    if has_ollama_routes or has_redirect_logic:
        return {"status": "PASS", "summary": "Backward compatibility implemented"}
    else:
        return {"status": "PENDING", "summary": "Backward compatibility not yet implemented"}

def main():
    """Run API structure validation tests"""
    print("🔧 Testing LlamaCpp API Structure")
    print("=" * 50)
    
    tests = [
        ("Plugin Import Structure", test_plugin_import_structure),
        ("Client Import Structure", test_client_import_structure),
        ("Route Definitions", test_route_definitions),
        ("Backward Compatibility", test_backward_compatibility_structure)
    ]
    
    results = {}
    passed = 0
    total = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = result["status"]
            summary = result.get("summary", "")
            
            print(f"  {status}: {test_name} - {summary}")
            
            if status == "PASS":
                passed += 1
            total += 1
            
        except Exception as e:
            print(f"  ERROR: {test_name} - {str(e)}")
            results[test_name] = {"status": "ERROR", "error": str(e)}
            total += 1
    
    print(f"\n📊 API Structure Summary:")
    print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ API Structure: VALID")
        return 0
    else:
        print("⚠️  API Structure: NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())