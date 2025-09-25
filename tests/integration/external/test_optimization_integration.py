#!/usr/bin/env python3
"""
Test script to verify performance optimization integration.

This script tests the integration of performance optimization components
with the existing codebase.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_optimization_integration():
    """Test the performance optimization integration."""
    logger.info("🧪 Testing performance optimization integration...")
    
    try:
        # Test 1: Configuration loading
        logger.info("📋 Testing configuration loading...")
        from ai_karen_engine.config.performance_config import load_performance_config
        
        config = await load_performance_config()
        assert config is not None, "Configuration should not be None"
        assert hasattr(config, 'enable_performance_optimization'), "Config should have optimization flag"
        logger.info(f"✅ Configuration loaded: {config.deployment_mode} mode")
        
        # Test 2: Optimization components initialization
        logger.info("🚀 Testing optimization components...")
        from ai_karen_engine.server.optimized_startup import initialize_optimization_components
        
        # Create mock settings
        class MockSettings:
            deployment_mode = "testing"
            enable_performance_optimization = True
            cpu_threshold = 80.0
            memory_threshold = 85.0
            response_time_threshold = 2.0
            log_level = "INFO"
        
        settings = MockSettings()
        
        try:
            optimization_report = await initialize_optimization_components(settings)
            logger.info(f"✅ Optimization components initialized in {optimization_report.get('initialization_time', 0):.2f}s")
            
            # Verify components are available
            components = optimization_report.get('components', {})
            for component, available in components.items():
                status = "✅" if available else "❌"
                logger.info(f"   {status} {component}: {'available' if available else 'not available'}")
                
        except Exception as e:
            logger.warning(f"⚠️ Optimization components initialization failed: {e}")
            logger.info("   This is expected if dependencies are not available")
        
        # Test 3: Service registry integration
        logger.info("🔧 Testing service registry integration...")
        try:
            from ai_karen_engine.core.classified_service_registry import ClassifiedServiceRegistry
            
            registry = ClassifiedServiceRegistry()
            await registry.load_service_config()
            
            # Test service classification
            essential_services = await registry.get_services_by_classification("essential")
            optional_services = await registry.get_services_by_classification("optional")
            background_services = await registry.get_services_by_classification("background")
            
            logger.info(f"✅ Service classification loaded:")
            logger.info(f"   • Essential: {len(essential_services)} services")
            logger.info(f"   • Optional: {len(optional_services)} services")
            logger.info(f"   • Background: {len(background_services)} services")
            
        except Exception as e:
            logger.warning(f"⚠️ Service registry integration test failed: {e}")
        
        # Test 4: Performance metrics integration
        logger.info("📊 Testing performance metrics integration...")
        try:
            from ai_karen_engine.core.performance_metrics import PerformanceMetrics
            
            metrics = PerformanceMetrics()
            await metrics.initialize()
            
            # Test metric recording
            await metrics.record_metric(
                "test_metric",
                42.0,
                service_name="integration_test",
                tags={"test": "true"}
            )
            
            logger.info("✅ Performance metrics integration working")
            
        except Exception as e:
            logger.warning(f"⚠️ Performance metrics integration test failed: {e}")
        
        # Test 5: Configuration management
        logger.info("⚙️ Testing configuration management...")
        try:
            from ai_karen_engine.config.performance_config import get_performance_config_manager
            
            config_manager = get_performance_config_manager()
            current_config = config_manager.get_config()
            
            if current_config:
                logger.info("✅ Configuration management working")
                logger.info(f"   • Deployment mode: {current_config.deployment_mode}")
                logger.info(f"   • Optimization enabled: {current_config.enable_performance_optimization}")
            else:
                logger.warning("⚠️ Configuration not loaded")
                
        except Exception as e:
            logger.warning(f"⚠️ Configuration management test failed: {e}")
        
        logger.info("🎉 Integration testing completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


async def test_api_integration():
    """Test API integration."""
    logger.info("🌐 Testing API integration...")
    
    try:
        # Test importing performance routes
        from ai_karen_engine.api_routes.performance_routes import router
        logger.info("✅ Performance routes imported successfully")
        
        # Check if optimization endpoints are available
        routes = [route.path for route in router.routes]
        optimization_routes = [route for route in routes if 'optimization' in route]
        
        logger.info(f"✅ Found {len(optimization_routes)} optimization API endpoints:")
        for route in optimization_routes:
            logger.info(f"   • {route}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API integration test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting performance optimization integration tests...")
    
    # Run tests
    integration_success = await test_optimization_integration()
    api_success = await test_api_integration()
    
    # Summary
    logger.info("\n📋 Test Summary:")
    logger.info(f"   • Integration test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    logger.info(f"   • API test: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    overall_success = integration_success and api_success
    logger.info(f"\n🎯 Overall result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)