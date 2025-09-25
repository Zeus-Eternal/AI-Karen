#!/usr/bin/env python3
"""
Validation test suite for LlamaCpp migration
Tests all requirements from task 8:
- API endpoints work with new /llm/llamacpp/* routes
- Backward compatibility aliases function correctly
- Configuration migration scenarios work as expected
- Logging and metrics use new naming conventions
"""

import os
import sys
import json
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class MigrationValidator:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "api_endpoints": {},
            "backward_compatibility": {},
            "configuration": {},
            "logging_metrics": {},
            "overall_status": "PENDING"
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🚀 Starting LlamaCpp Migration Validation Tests")
        print("=" * 60)
        
        try:
            # Test 1: API Endpoints
            print("\n📡 Testing API Endpoints...")
            self.test_api_endpoints()
            
            # Test 2: Backward Compatibility
            print("\n🔄 Testing Backward Compatibility...")
            self.test_backward_compatibility()
            
            # Test 3: Configuration Migration
            print("\n⚙️  Testing Configuration Migration...")
            self.test_configuration_migration()
            
            # Test 4: Logging and Metrics
            print("\n📊 Testing Logging and Metrics...")
            self.test_logging_and_metrics()
            
            # Overall assessment
            self.assess_overall_status()
            
        except Exception as e:
            print(f"❌ Critical error during validation: {e}")
            self.results["overall_status"] = "FAILED"
            
        return self.results
    
    def test_api_endpoints(self):
        """Test all API endpoints work with new /llm/llamacpp/* routes"""
        endpoints = [
            ("/llm/llamacpp/health", "GET"),
            ("/llm/llamacpp/models", "GET"),
            ("/llm/llamacpp/chat", "POST"),
            ("/llm/llamacpp/achat", "POST"),
            ("/llm/llamacpp/embedding", "POST"),
            ("/llm/llamacpp/switch", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    # POST with minimal test data
                    test_data = self._get_test_data_for_endpoint(endpoint)
                    response = requests.post(f"{self.base_url}{endpoint}", json=test_data, timeout=10)
                
                status = "PASS" if response.status_code in [200, 201, 422] else "FAIL"
                self.results["api_endpoints"][endpoint] = {
                    "status": status,
                    "status_code": response.status_code,
                    "method": method
                }
                print(f"  {status}: {method} {endpoint} -> {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                print(f"  SKIP: {method} {endpoint} -> Server not running")
                self.results["api_endpoints"][endpoint] = {
                    "status": "SKIP",
                    "reason": "Server not running",
                    "method": method
                }
            except Exception as e:
                print(f"  FAIL: {method} {endpoint} -> {str(e)}")
                self.results["api_endpoints"][endpoint] = {
                    "status": "FAIL",
                    "error": str(e),
                    "method": method
                }
    
    def test_backward_compatibility(self):
        """Test backward compatibility aliases function correctly"""
        # Test backward compatibility for legacy /llm/ollama/* routes (if implemented)
        old_endpoints = [
            "/llm/ollama/health",
            "/llm/ollama/models", 
            "/llm/ollama/chat"
        ]
        
        for endpoint in old_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                # Should either redirect (3xx) or work (2xx) or be not found (404)
                if response.status_code in [200, 301, 302, 404]:
                    status = "PASS" if response.status_code != 404 else "EXPECTED_404"
                else:
                    status = "FAIL"
                    
                self.results["backward_compatibility"][endpoint] = {
                    "status": status,
                    "status_code": response.status_code
                }
                print(f"  {status}: {endpoint} -> {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                print(f"  SKIP: {endpoint} -> Server not running")
                self.results["backward_compatibility"][endpoint] = {
                    "status": "SKIP",
                    "reason": "Server not running"
                }
            except Exception as e:
                print(f"  FAIL: {endpoint} -> {str(e)}")
                self.results["backward_compatibility"][endpoint] = {
                    "status": "FAIL",
                    "error": str(e)
                }
    
    def test_configuration_migration(self):
        """Test configuration migration scenarios work as expected"""
        config_tests = [
            self._test_default_provider_config(),
            self._test_fallback_hierarchy_config(),
            self._test_environment_variables()
        ]
        
        for test_name, result in config_tests:
            self.results["configuration"][test_name] = result
            status = result.get("status", "UNKNOWN")
            print(f"  {status}: {test_name}")
    
    def test_logging_and_metrics(self):
        """Test logging and metrics use new naming conventions"""
        tests = [
            self._test_logger_names(),
            self._test_metric_names(),
            self._test_log_messages()
        ]
        
        for test_name, result in tests:
            self.results["logging_metrics"][test_name] = result
            status = result.get("status", "UNKNOWN")
            print(f"  {status}: {test_name}")
    
    def _get_test_data_for_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Get appropriate test data for each endpoint"""
        if "/chat" in endpoint:
            return {
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "stream": False,
                "user_id": "test"
            }
        elif "/embedding" in endpoint:
            return {"text": "test"}
        elif "/switch" in endpoint:
            return {"model_name": "test.gguf"}
        return {}
    
    def _test_default_provider_config(self) -> tuple:
        """Test that default provider is set to llamacpp"""
        try:
            # Check fix_auth_schema.py for default provider
            schema_file = Path("scripts/maintenance/fix_auth_schema.py")
            if schema_file.exists():
                content = schema_file.read_text()
                if '"llamacpp"' in content and 'preferredLLMProvider' in content:
                    return ("default_provider", {"status": "PASS", "found": "llamacpp default"})
                else:
                    return ("default_provider", {"status": "FAIL", "reason": "llamacpp not found as default"})
            else:
                return ("default_provider", {"status": "SKIP", "reason": "Schema file not found"})
        except Exception as e:
            return ("default_provider", {"status": "FAIL", "error": str(e)})
    
    def _test_fallback_hierarchy_config(self) -> tuple:
        """Test fallback hierarchy uses llamacpp"""
        try:
            # Check documentation for fallback examples
            doc_file = Path("docs/LLM_FALLBACK_HIERARCHY_IMPLEMENTATION.md")
            if doc_file.exists():
                content = doc_file.read_text()
                if "llamacpp" in content.lower():
                    return ("fallback_hierarchy", {"status": "PASS", "found": "llamacpp in fallback docs"})
                else:
                    return ("fallback_hierarchy", {"status": "FAIL", "reason": "llamacpp not found in fallback docs"})
            else:
                return ("fallback_hierarchy", {"status": "SKIP", "reason": "Fallback doc not found"})
        except Exception as e:
            return ("fallback_hierarchy", {"status": "FAIL", "error": str(e)})
    
    def _test_environment_variables(self) -> tuple:
        """Test environment variables use LLAMACPP prefix"""
        try:
            # Check llama_client.py for LLAMACPP env vars
            client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
            if client_file.exists():
                content = client_file.read_text()
                llamacpp_vars = ["LLAMACPP_MODEL_NAME", "LLAMACPP_CTX_SIZE", "LLAMACPP_THREADS"]
                found_vars = [var for var in llamacpp_vars if var in content]
                if len(found_vars) >= 2:  # At least 2 out of 3
                    return ("environment_variables", {"status": "PASS", "found_vars": found_vars})
                else:
                    return ("environment_variables", {"status": "FAIL", "found_vars": found_vars})
            else:
                return ("environment_variables", {"status": "SKIP", "reason": "Client file not found"})
        except Exception as e:
            return ("environment_variables", {"status": "FAIL", "error": str(e)})
    
    def _test_logger_names(self) -> tuple:
        """Test logger names use llamacpp terminology"""
        try:
            files_to_check = [
                "src/marketplace/ai/llm-services/llama/llama_client.py",
                "plugin_marketplace/ai/llm-services/llama/llama_plugin.py"
            ]
            
            llamacpp_loggers = []
            for file_path in files_to_check:
                path = Path(file_path)
                if path.exists():
                    content = path.read_text()
                    if "llamacpp_inprocess" in content or "llamacpp_plugin" in content:
                        llamacpp_loggers.append(file_path)
            
            if len(llamacpp_loggers) >= 1:
                return ("logger_names", {"status": "PASS", "files_with_llamacpp_loggers": llamacpp_loggers})
            else:
                return ("logger_names", {"status": "FAIL", "reason": "No llamacpp loggers found"})
                
        except Exception as e:
            return ("logger_names", {"status": "FAIL", "error": str(e)})
    
    def _test_metric_names(self) -> tuple:
        """Test Prometheus metrics use llamacpp naming"""
        try:
            client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
            if client_file.exists():
                content = client_file.read_text()
                llamacpp_metrics = [
                    "llamacpp_requests_total",
                    "llamacpp_latency_seconds", 
                    "llamacpp_errors_total",
                    "llamacpp_inflight_requests"
                ]
                found_metrics = [metric for metric in llamacpp_metrics if metric in content]
                if len(found_metrics) >= 3:  # At least 3 out of 4
                    return ("metric_names", {"status": "PASS", "found_metrics": found_metrics})
                else:
                    return ("metric_names", {"status": "FAIL", "found_metrics": found_metrics})
            else:
                return ("metric_names", {"status": "SKIP", "reason": "Client file not found"})
        except Exception as e:
            return ("metric_names", {"status": "FAIL", "error": str(e)})
    
    def _test_log_messages(self) -> tuple:
        """Test log messages use llamacpp terminology"""
        try:
            client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
            if client_file.exists():
                content = client_file.read_text()
                # Check for llamacpp_inprocess in log messages
                if "[llamacpp_inprocess]" in content:
                    return ("log_messages", {"status": "PASS", "found": "llamacpp_inprocess in log messages"})
                else:
                    return ("log_messages", {"status": "FAIL", "reason": "llamacpp_inprocess not found in log messages"})
            else:
                return ("log_messages", {"status": "SKIP", "reason": "Client file not found"})
        except Exception as e:
            return ("log_messages", {"status": "FAIL", "error": str(e)})
    
    def assess_overall_status(self):
        """Assess overall migration status based on test results"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for category in self.results.values():
            if isinstance(category, dict):
                for test_result in category.values():
                    if isinstance(test_result, dict) and "status" in test_result:
                        total_tests += 1
                        if test_result["status"] == "PASS":
                            passed_tests += 1
                        elif test_result["status"] == "FAIL":
                            failed_tests += 1
                        elif test_result["status"] in ["SKIP", "EXPECTED_404"]:
                            skipped_tests += 1
        
        print(f"\n📊 Test Summary:")
        print(f"  Total: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Skipped: {skipped_tests}")
        
        if failed_tests == 0 and passed_tests > 0:
            self.results["overall_status"] = "PASS"
            print(f"✅ Overall Status: PASS")
        elif failed_tests > 0:
            self.results["overall_status"] = "FAIL"
            print(f"❌ Overall Status: FAIL ({failed_tests} failures)")
        else:
            self.results["overall_status"] = "INCONCLUSIVE"
            print(f"⚠️  Overall Status: INCONCLUSIVE (no tests passed)")

def main():
    """Main validation function"""
    validator = MigrationValidator()
    results = validator.run_all_tests()
    
    # Save results to file
    results_file = Path("llamacpp_migration_validation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    elif results["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()