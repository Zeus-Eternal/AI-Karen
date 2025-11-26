#!/usr/bin/env python3
"""
Comprehensive test script for the new services architecture.
This script validates that all services are working correctly with the new facade pattern.
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_import_service(service_path: str, facade_name: str) -> bool:
    """Test importing a service facade."""
    try:
        module = importlib.import_module(service_path)
        facade = getattr(module, facade_name, None)
        if facade is None:
            print(f"❌ Failed to import facade '{facade_name}' from '{service_path}'")
            return False
        print(f"✅ Successfully imported '{facade_name}' from '{service_path}'")
        return True
    except Exception as e:
        print(f"❌ Failed to import '{service_path}': {str(e)}")
        traceback.print_exc()
        return False

def test_service_initialization(service_path: str, facade_name: str) -> bool:
    """Test initializing a service facade."""
    try:
        module = importlib.import_module(service_path)
        facade_class = getattr(module, facade_name)
        facade_instance = facade_class()
        print(f"✅ Successfully initialized '{facade_name}' from '{service_path}'")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize '{facade_name}' from '{service_path}': {str(e)}")
        traceback.print_exc()
        return False

def test_service_methods(service_path: str, facade_name: str, methods: list) -> bool:
    """Test that a service facade has the expected methods."""
    try:
        module = importlib.import_module(service_path)
        facade_class = getattr(module, facade_name)
        facade_instance = facade_class()
        
        missing_methods = []
        for method_name in methods:
            if not hasattr(facade_instance, method_name):
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"❌ Facade '{facade_name}' is missing methods: {', '.join(missing_methods)}")
            return False
        
        print(f"✅ Facade '{facade_name}' has all expected methods")
        return True
    except Exception as e:
        print(f"❌ Failed to test methods of '{facade_name}': {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 Testing Services Architecture")
    print("=" * 50)
    
    # Define services to test
    services_to_test = [
        {
            "path": "ai_karen_engine.services.memory.unified_memory_service",
            "facade": "UnifiedMemoryService",
            "methods": ["query_memories", "store_memory", "update_memory", "delete_memory"]
        },
        {
            "path": "ai_karen_engine.services.monitoring.structured_logging_service",
            "facade": "StructuredLoggingService",
            "methods": ["log_structured_event", "log_memory_access", "log_api_request"]
        },
        {
            "path": "ai_karen_engine.services.monitoring.metrics_service",
            "facade": "MetricsService",
            "methods": ["record_timing", "increment_counter", "set_gauge", "get_metric_summary"]
        },
        {
            "path": "ai_karen_engine.services.monitoring.correlation_service",
            "facade": "CorrelationService",
            "methods": ["get_or_create_correlation_id", "set_correlation_id", "start_trace", "end_trace"]
        },
        {
            "path": "ai_karen_engine.services.models.model_orchestrator_service",
            "facade": "ModelOrchestratorService",
            "methods": ["list_models", "get_model_info", "download_model", "remove_model"]
        },
        {
            "path": "ai_karen_engine.services.agents.agent_orchestrator",
            "facade": "AgentOrchestrator",
            "methods": ["register_agent", "submit_task", "execute_task", "get_task_status"]
        },
        {
            "path": "ai_karen_engine.services.extensions.extension_registry",
            "facade": "ExtensionRegistry",
            "methods": ["get_extension", "get_extensions", "load_extension", "unload_extension"]
        },
        {
            "path": "ai_karen_engine.services.extensions.extension_loader",
            "facade": "ExtensionLoader",
            "methods": ["load_extension", "load_extension_from_url", "load_extension_from_file", "get_task"]
        }
    ]
    
    # Test each service
    passed_tests = 0
    total_tests = 0
    
    for service in services_to_test:
        print(f"\n🔍 Testing {service['path']}")
        print("-" * 30)
        
        # Test import
        total_tests += 1
        if test_import_service(service["path"], service["facade"]):
            passed_tests += 1
        
        # Test initialization
        total_tests += 1
        if test_service_initialization(service["path"], service["facade"]):
            passed_tests += 1
        
        # Test methods
        total_tests += 1
        if test_service_methods(service["path"], service["facade"], service["methods"]):
            passed_tests += 1
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The services architecture is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)