#!/usr/bin/env python3
"""
Integration Health Test

Quick test to verify that the optimization integration system is working
and can be imported without errors.
"""

import sys
import traceback

def test_imports():
    """Test that all integration components can be imported."""
    print("Testing imports...")
    
    try:
        # Test core integration components
        from ai_karen_engine.services.intelligent_scaffolding_service import IntelligentScaffoldingService
        print("✓ IntelligentScaffoldingService imported successfully")
        
        from ai_karen_engine.services.optimization_integration_orchestrator import OptimizationIntegrationOrchestrator
        print("✓ OptimizationIntegrationOrchestrator imported successfully")
        
        from ai_karen_engine.services.integrated_model_management import IntegratedModelManager
        print("✓ IntegratedModelManager imported successfully")
        
        from ai_karen_engine.services.integrated_cache_system import IntegratedCacheSystem
        print("✓ IntegratedCacheSystem imported successfully")
        
        from ai_karen_engine.services.integrated_performance_monitoring import IntegratedPerformanceMonitor
        print("✓ IntegratedPerformanceMonitor imported successfully")
        
        from ai_karen_engine.services.optimization_configuration_manager import OptimizationConfigurationManager
        print("✓ OptimizationConfigurationManager imported successfully")
        
        # Test API routes
        from ai_karen_engine.api_routes.optimization_integration_routes import router
        print("✓ Optimization API routes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of key components."""
    print("\nTesting basic functionality...")
    
    try:
        # Test intelligent scaffolding service
        from ai_karen_engine.services.intelligent_scaffolding_service import get_intelligent_scaffolding_service
        scaffolding_service = get_intelligent_scaffolding_service()
        print("✓ Intelligent scaffolding service created successfully")
        
        # Test configuration manager
        from ai_karen_engine.services.optimization_configuration_manager import get_optimization_config_manager
        config_manager = get_optimization_config_manager()
        config_summary = config_manager.get_configuration_summary()
        print(f"✓ Configuration manager working: {len(config_summary)} config items")
        
        # Test orchestrator
        from ai_karen_engine.services.optimization_integration_orchestrator import get_optimization_integration_orchestrator
        orchestrator = get_optimization_integration_orchestrator()
        print("✓ Integration orchestrator created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing components."""
    print("\nTesting backward compatibility...")
    
    try:
        # Test reasoning preservation layer
        from ai_karen_engine.services.reasoning_preservation_layer import get_reasoning_preservation_layer
        preservation_layer = get_reasoning_preservation_layer()
        print("✓ Reasoning preservation layer created successfully")
        
        # Test that old method names still work
        if hasattr(preservation_layer, 'wrap_tinyllama_service'):
            print("✓ Backward compatibility method wrap_tinyllama_service exists")
        else:
            print("✗ Backward compatibility method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all health tests."""
    print("=== Integration Health Test ===\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Functionality Test", test_basic_functionality),
        ("Backward Compatibility Test", test_backward_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All integration health tests passed!")
        return 0
    else:
        print("❌ Some integration health tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())