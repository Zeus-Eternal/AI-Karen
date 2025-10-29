#!/usr/bin/env python3
"""
Test script for Task 14: Extend existing health endpoints for extension monitoring

This script tests the implementation of:
- Extension status in /api/health/database/monitor endpoint
- Extension performance metrics collection
- Extension health in Prometheus metrics endpoint
- Extension status in degraded mode status reporting
"""

import asyncio
import logging
import requests
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # This should match your configured API key


async def test_database_monitor_extension():
    """Test that database monitor endpoint includes extension status"""
    logger.info("Testing database monitor extension integration")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/database/monitor")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for extension system information
            if "extension_system" in data:
                logger.info("✅ Extension system included in database monitor")
                ext_system = data["extension_system"]
                
                required_fields = ["status", "total_extensions", "healthy_extensions"]
                for field in required_fields:
                    if field in ext_system:
                        logger.info(f"✅ Extension system has {field}: {ext_system[field]}")
                    else:
                        logger.warning(f"❌ Extension system missing {field}")
                        return False
            else:
                logger.warning("❌ Extension system not found in database monitor response")
                return False
            
            # Check for extension performance metrics
            if "extension_performance" in data:
                logger.info("✅ Extension performance metrics included")
                perf_data = data["extension_performance"]
                
                expected_metrics = [
                    "database_query_performance",
                    "connection_pool_usage", 
                    "background_task_database_load",
                    "dependent_extensions_count"
                ]
                
                for metric in expected_metrics:
                    if metric in perf_data:
                        logger.info(f"✅ Performance metric {metric} present")
                    else:
                        logger.warning(f"❌ Performance metric {metric} missing")
                        return False
            else:
                logger.warning("❌ Extension performance metrics not found")
                return False
                
            logger.info("✅ Database monitor extension integration successful")
            return True
        else:
            logger.error(f"❌ Database monitor endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database monitor test failed: {e}")
        return False


async def test_prometheus_metrics_extension():
    """Test that Prometheus metrics include extension metrics"""
    logger.info("Testing Prometheus metrics extension integration")
    
    try:
        headers = {"X-API-KEY": API_KEY}
        response = requests.get(f"{BASE_URL}/metrics", headers=headers)
        
        if response.status_code == 200:
            metrics_text = response.text
            
            # Check for extension-specific metrics
            expected_metrics = [
                "kari_extension_health_status",
                "kari_extension_response_time_seconds",
                "kari_extension_background_tasks_total",
                "kari_extension_api_calls_total",
                "kari_extension_errors_total",
                "kari_extension_uptime_seconds"
            ]
            
            found_metrics = []
            for metric in expected_metrics:
                if metric in metrics_text:
                    found_metrics.append(metric)
                    logger.info(f"✅ Prometheus metric {metric} found")
                else:
                    logger.warning(f"❌ Prometheus metric {metric} not found")
            
            if len(found_metrics) >= len(expected_metrics) * 0.8:  # At least 80% of metrics
                logger.info("✅ Prometheus extension metrics integration successful")
                return True
            else:
                logger.warning(f"❌ Only {len(found_metrics)}/{len(expected_metrics)} extension metrics found")
                return False
        else:
            logger.error(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Prometheus metrics test failed: {e}")
        return False


async def test_overall_health_extension():
    """Test that overall health endpoint includes extension status"""
    logger.info("Testing overall health extension integration")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for extension system in response
            if "extension_system" in data:
                logger.info("✅ Extension system included in overall health")
                ext_system = data["extension_system"]
                
                if "status" in ext_system:
                    logger.info(f"✅ Extension system status: {ext_system['status']}")
                else:
                    logger.warning("❌ Extension system status missing")
                    return False
            else:
                logger.warning("❌ Extension system not found in overall health")
                return False
            
            # Check for extensions in services
            if "services" in data and "extensions" in data["services"]:
                logger.info("✅ Extensions included in services list")
                ext_service = data["services"]["extensions"]
                
                if "status" in ext_service:
                    logger.info(f"✅ Extension service status: {ext_service['status']}")
                else:
                    logger.warning("❌ Extension service status missing")
                    return False
            else:
                logger.warning("❌ Extensions not found in services list")
                return False
                
            logger.info("✅ Overall health extension integration successful")
            return True
        else:
            logger.error(f"❌ Overall health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Overall health test failed: {e}")
        return False


async def test_degraded_mode_extension():
    """Test that degraded mode includes extension status"""
    logger.info("Testing degraded mode extension integration")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/degraded-mode")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for extension system information
            if "extension_system" in data:
                logger.info("✅ Extension system included in degraded mode")
                ext_system = data["extension_system"]
                
                if "status" in ext_system:
                    logger.info(f"✅ Extension system status in degraded mode: {ext_system['status']}")
                else:
                    logger.warning("❌ Extension system status missing in degraded mode")
                    return False
            else:
                logger.warning("❌ Extension system not found in degraded mode")
                return False
            
            # Check for extension_degraded flag
            if "extension_degraded" in data:
                logger.info(f"✅ Extension degraded flag: {data['extension_degraded']}")
            else:
                logger.warning("❌ Extension degraded flag missing")
                return False
            
            # Check if extensions are in degraded components when appropriate
            degraded_components = data.get("degraded_components", [])
            if data.get("extension_degraded", False):
                if "extensions" in degraded_components:
                    logger.info("✅ Extensions properly included in degraded components")
                else:
                    logger.warning("❌ Extensions not in degraded components when degraded")
                    return False
                    
            logger.info("✅ Degraded mode extension integration successful")
            return True
        else:
            logger.error(f"❌ Degraded mode endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Degraded mode test failed: {e}")
        return False


async def test_extension_health_endpoints():
    """Test dedicated extension health endpoints"""
    logger.info("Testing dedicated extension health endpoints")
    
    try:
        # Test extension system health endpoint
        response = requests.get(f"{BASE_URL}/api/health/extensions")
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["status", "extensions", "supporting_services", "database_performance"]
            for field in required_fields:
                if field in data:
                    logger.info(f"✅ Extension health endpoint has {field}")
                else:
                    logger.warning(f"❌ Extension health endpoint missing {field}")
                    return False
            
            # Check database performance metrics
            db_perf = data.get("database_performance", {})
            if "dependent_extensions_count" in db_perf:
                logger.info(f"✅ Database performance metrics included: {db_perf['dependent_extensions_count']} dependent extensions")
            else:
                logger.warning("❌ Database performance metrics missing")
                return False
                
            logger.info("✅ Extension health endpoints working")
            return True
        else:
            logger.error(f"❌ Extension health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Extension health endpoints test failed: {e}")
        return False


async def main():
    """Run all tests for task 14 implementation"""
    logger.info("🚀 Starting Task 14 Implementation Tests")
    logger.info("Testing: Extend existing health endpoints for extension monitoring")
    
    tests = [
        test_database_monitor_extension,
        test_prometheus_metrics_extension,
        test_overall_health_extension,
        test_degraded_mode_extension,
        test_extension_health_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
                logger.info(f"✅ {test.__name__} PASSED")
            else:
                logger.error(f"❌ {test.__name__} FAILED")
        except Exception as e:
            logger.error(f"❌ {test.__name__} ERROR: {e}")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Task 14 implementation tests passed!")
        logger.info("✅ Extension health monitoring successfully integrated into existing endpoints")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)