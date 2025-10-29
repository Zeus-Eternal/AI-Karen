#!/usr/bin/env python3
"""
Test script for extension health monitoring endpoints integration.

This script tests the implementation of task 14: extending existing health endpoints
for extension monitoring.

Requirements tested: 5.3, 5.4, 5.5, 10.1, 10.2
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_KEY = "test-secret-key"  # This should match your server configuration

def test_database_monitor_extension_integration():
    """Test that the database monitor endpoint includes extension status"""
    print("\n=== Testing Database Monitor Extension Integration ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/database/monitor")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Database monitor endpoint accessible")
            
            # Check for extension system information
            if "extension_system" in data:
                ext_system = data["extension_system"]
                print(f"✅ Extension system status included: {ext_system.get('status', 'unknown')}")
                
                # Check required fields
                required_fields = [
                    "status", "total_extensions", "healthy_extensions", 
                    "degraded_extensions", "unhealthy_extensions"
                ]
                
                missing_fields = [field for field in required_fields if field not in ext_system]
                if not missing_fields:
                    print("✅ All required extension fields present")
                else:
                    print(f"❌ Missing extension fields: {missing_fields}")
                
                # Check database-dependent extensions
                if "database_dependent_extensions" in ext_system:
                    db_deps = ext_system["database_dependent_extensions"]
                    print(f"✅ Database-dependent extensions tracked: {len(db_deps)} extensions")
                else:
                    print("⚠️  Database-dependent extensions not tracked")
                
                # Check supporting services
                if "authentication_healthy" in ext_system:
                    auth_status = ext_system["authentication_healthy"]
                    print(f"✅ Extension authentication health: {auth_status}")
                else:
                    print("⚠️  Extension authentication health not reported")
                
            else:
                print("❌ Extension system information not included in database monitor")
            
            # Check original database health information is still present
            if "monitor" in data and "pool_status" in data:
                print("✅ Original database health information preserved")
            else:
                print("❌ Original database health information missing")
                
        else:
            print(f"❌ Database monitor endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Database monitor test failed: {e}")

def test_prometheus_metrics_extension_integration():
    """Test that Prometheus metrics endpoint includes extension metrics"""
    print("\n=== Testing Prometheus Metrics Extension Integration ===")
    
    try:
        headers = {"X-API-KEY": API_KEY}
        response = requests.get(f"{BASE_URL}/metrics", headers=headers)
        
        if response.status_code == 200:
            metrics_text = response.text
            print("✅ Prometheus metrics endpoint accessible")
            
            # Check for extension-specific metrics
            extension_metrics = [
                "kari_extension_health_status",
                "kari_extension_response_time_seconds",
                "kari_extension_background_tasks_total",
                "kari_extension_api_calls_total",
                "kari_extension_errors_total",
                "kari_extension_uptime_seconds"
            ]
            
            found_metrics = []
            for metric in extension_metrics:
                if metric in metrics_text:
                    found_metrics.append(metric)
                    print(f"✅ Extension metric found: {metric}")
                else:
                    print(f"⚠️  Extension metric not found: {metric}")
            
            if len(found_metrics) >= 3:  # At least half the metrics should be present
                print(f"✅ Extension metrics integration successful ({len(found_metrics)}/{len(extension_metrics)} metrics)")
            else:
                print(f"❌ Insufficient extension metrics ({len(found_metrics)}/{len(extension_metrics)} metrics)")
                
        elif response.status_code == 401:
            print("⚠️  Metrics endpoint requires authentication (expected)")
            print("   Try setting the correct API key in the test script")
        elif response.status_code == 501:
            print("⚠️  Prometheus metrics not enabled on server")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Prometheus metrics test failed: {e}")

def test_degraded_mode_extension_integration():
    """Test that degraded mode status includes extension information"""
    print("\n=== Testing Degraded Mode Extension Integration ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/degraded-mode")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Degraded mode endpoint accessible")
            
            # Check for extension system information
            if "extension_system" in data:
                ext_system = data["extension_system"]
                print(f"✅ Extension system status included: {ext_system.get('status', 'unknown')}")
                
                # Check required fields for degraded mode
                required_fields = [
                    "status", "total_extensions", "healthy_extensions", 
                    "degraded_extensions", "unhealthy_extensions"
                ]
                
                present_fields = [field for field in required_fields if field in ext_system]
                if len(present_fields) >= 3:  # At least most fields should be present
                    print(f"✅ Extension degraded mode fields present: {len(present_fields)}/{len(required_fields)}")
                else:
                    print(f"⚠️  Limited extension degraded mode fields: {len(present_fields)}/{len(required_fields)}")
                
                # Check for degraded extension names
                if "degraded_extension_names" in ext_system:
                    degraded_names = ext_system["degraded_extension_names"]
                    print(f"✅ Degraded extension names tracked: {len(degraded_names)} extensions")
                else:
                    print("⚠️  Degraded extension names not tracked")
                
                # Check supporting services health
                service_fields = ["authentication_healthy", "database_healthy", "background_tasks_healthy"]
                service_present = [field for field in service_fields if field in ext_system]
                if service_present:
                    print(f"✅ Extension supporting services health: {len(service_present)}/{len(service_fields)} services")
                else:
                    print("⚠️  Extension supporting services health not reported")
                
            else:
                print("❌ Extension system information not included in degraded mode")
            
            # Check that degraded mode logic considers extensions
            degraded_components = data.get("degraded_components", [])
            extension_related = [comp for comp in degraded_components if "extension" in comp.lower()]
            if extension_related:
                print(f"✅ Extension-related degraded components: {extension_related}")
            else:
                print("⚠️  No extension-related degraded components (may be healthy)")
                
        else:
            print(f"❌ Degraded mode endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Degraded mode test failed: {e}")

def test_extension_specific_health_endpoint():
    """Test extension-specific health endpoints"""
    print("\n=== Testing Extension-Specific Health Endpoints ===")
    
    try:
        # Test general extension health endpoint
        response = requests.get(f"{BASE_URL}/api/health/extensions")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Extension health endpoint accessible")
            
            # Check response structure
            if "status" in data and "extensions" in data:
                print(f"✅ Extension health structure valid")
                print(f"   Status: {data['status']}")
                print(f"   Total extensions: {data['extensions'].get('total', 0)}")
                print(f"   Healthy: {data['extensions'].get('healthy', 0)}")
                print(f"   Degraded: {data['extensions'].get('degraded', 0)}")
                print(f"   Unhealthy: {data['extensions'].get('unhealthy', 0)}")
            else:
                print("❌ Extension health response structure invalid")
                
        else:
            print(f"❌ Extension health endpoint failed: {response.status_code}")
            
        # Test specific extension health (try a common extension name)
        test_extensions = ["analytics-dashboard", "system-monitor"]
        for ext_name in test_extensions:
            response = requests.get(f"{BASE_URL}/api/health/extensions/{ext_name}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Specific extension health accessible: {ext_name}")
                print(f"   Status: {data.get('status', 'unknown')}")
            elif response.status_code == 404:
                print(f"⚠️  Extension not found: {ext_name} (expected if not installed)")
            else:
                print(f"❌ Specific extension health failed for {ext_name}: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Extension-specific health test failed: {e}")

def test_comprehensive_health_extension_integration():
    """Test that comprehensive health endpoint includes extension information"""
    print("\n=== Testing Comprehensive Health Extension Integration ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Comprehensive health endpoint accessible")
            
            # Check for extension system in services
            if "services" in data and "extension_system" in data["services"]:
                ext_service = data["services"]["extension_system"]
                print(f"✅ Extension system included in services: {ext_service.get('status', 'unknown')}")
                
                # Check extension metrics
                if "total_extensions" in ext_service:
                    print(f"   Total extensions: {ext_service['total_extensions']}")
                    print(f"   Healthy: {ext_service.get('healthy_extensions', 0)}")
                    print(f"   Degraded: {ext_service.get('degraded_extensions', 0)}")
                    print(f"   Unhealthy: {ext_service.get('unhealthy_extensions', 0)}")
                
                # Check supporting services
                if "supporting_services" in ext_service:
                    services = ext_service["supporting_services"]
                    print(f"   Authentication: {services.get('authentication', {}).get('healthy', 'unknown')}")
                    print(f"   Database: {services.get('database', {}).get('healthy', 'unknown')}")
                    print(f"   Background tasks: {services.get('background_tasks', {}).get('healthy', 'unknown')}")
                
            else:
                print("❌ Extension system not included in comprehensive health")
            
            # Check overall status considers extensions
            overall_status = data.get("status", "unknown")
            print(f"✅ Overall health status: {overall_status}")
            
            # Check summary includes extension services
            if "summary" in data:
                summary = data["summary"]
                total_services = summary.get("total_services", 0)
                print(f"✅ Total services (including extensions): {total_services}")
                
        else:
            print(f"❌ Comprehensive health endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Comprehensive health test failed: {e}")

def run_all_tests():
    """Run all extension health endpoint tests"""
    print("🔍 Testing Extension Health Endpoints Integration")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run all tests
    test_database_monitor_extension_integration()
    test_prometheus_metrics_extension_integration()
    test_degraded_mode_extension_integration()
    test_extension_specific_health_endpoint()
    test_comprehensive_health_extension_integration()
    
    print("\n" + "=" * 60)
    print("🏁 Extension Health Endpoints Integration Tests Complete")
    print("\nNote: Some warnings are expected if:")
    print("- Extensions are not fully loaded yet")
    print("- Prometheus metrics are disabled")
    print("- API key authentication is required")
    print("- Server is still starting up")

if __name__ == "__main__":
    run_all_tests()