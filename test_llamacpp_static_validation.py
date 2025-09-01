#!/usr/bin/env python3
"""
Static validation test suite for Ollama to LlamaCpp migration
Tests implementation changes without requiring a running server
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

class StaticMigrationValidator:
    def __init__(self):
        self.results = {
            "code_changes": {},
            "configuration_changes": {},
            "documentation_changes": {},
            "logging_metrics_changes": {},
            "overall_status": "PENDING"
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all static validation tests"""
        print("🔍 Starting LlamaCpp Migration Static Validation")
        print("=" * 60)
        
        try:
            # Test 1: Code Changes
            print("\n💻 Validating Code Changes...")
            self.validate_code_changes()
            
            # Test 2: Configuration Changes
            print("\n⚙️  Validating Configuration Changes...")
            self.validate_configuration_changes()
            
            # Test 3: Documentation Changes
            print("\n📚 Validating Documentation Changes...")
            self.validate_documentation_changes()
            
            # Test 4: Logging and Metrics Changes
            print("\n📊 Validating Logging and Metrics Changes...")
            self.validate_logging_metrics_changes()
            
            # Overall assessment
            self.assess_overall_status()
            
        except Exception as e:
            print(f"❌ Critical error during validation: {e}")
            self.results["overall_status"] = "FAILED"
            
        return self.results
    
    def validate_code_changes(self):
        """Validate core code changes in llama client and plugin"""
        
        # Test llama_client.py changes
        client_result = self._validate_llama_client()
        self.results["code_changes"]["llama_client"] = client_result
        print(f"  {client_result['status']}: llama_client.py - {client_result.get('summary', '')}")
        
        # Test llama_plugin.py changes  
        plugin_result = self._validate_llama_plugin()
        self.results["code_changes"]["llama_plugin"] = plugin_result
        print(f"  {plugin_result['status']}: llama_plugin.py - {plugin_result.get('summary', '')}")
        
        # Test for any remaining ollama references
        ollama_refs = self._find_remaining_ollama_references()
        self.results["code_changes"]["remaining_ollama_refs"] = ollama_refs
        print(f"  {ollama_refs['status']}: Remaining Ollama references - {ollama_refs.get('summary', '')}")
    
    def validate_configuration_changes(self):
        """Validate configuration file changes"""
        
        # Test default provider configuration
        default_provider = self._validate_default_provider()
        self.results["configuration_changes"]["default_provider"] = default_provider
        print(f"  {default_provider['status']}: Default provider config - {default_provider.get('summary', '')}")
        
        # Test environment variables
        env_vars = self._validate_environment_variables()
        self.results["configuration_changes"]["environment_variables"] = env_vars
        print(f"  {env_vars['status']}: Environment variables - {env_vars.get('summary', '')}")
    
    def validate_documentation_changes(self):
        """Validate documentation updates"""
        
        # Test key documentation files
        doc_files = [
            "docs/LLM_FALLBACK_HIERARCHY_IMPLEMENTATION.md",
            "docs/side_by_side_openai_kari.md",
            "docs/AGENTS.md"
        ]
        
        for doc_file in doc_files:
            result = self._validate_documentation_file(doc_file)
            self.results["documentation_changes"][doc_file] = result
            print(f"  {result['status']}: {doc_file} - {result.get('summary', '')}")
    
    def validate_logging_metrics_changes(self):
        """Validate logging and metrics naming changes"""
        
        # Test logger names
        logger_result = self._validate_logger_names()
        self.results["logging_metrics_changes"]["logger_names"] = logger_result
        print(f"  {logger_result['status']}: Logger names - {logger_result.get('summary', '')}")
        
        # Test metric names
        metrics_result = self._validate_metric_names()
        self.results["logging_metrics_changes"]["metric_names"] = metrics_result
        print(f"  {metrics_result['status']}: Metric names - {metrics_result.get('summary', '')}")
        
        # Test log messages
        log_msgs_result = self._validate_log_messages()
        self.results["logging_metrics_changes"]["log_messages"] = log_msgs_result
        print(f"  {log_msgs_result['status']}: Log messages - {log_msgs_result.get('summary', '')}")
    
    def _validate_llama_client(self) -> Dict[str, Any]:
        """Validate llama_client.py has been properly updated"""
        client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
        
        if not client_file.exists():
            return {"status": "SKIP", "reason": "File not found", "summary": "File missing"}
        
        content = client_file.read_text()
        
        # Check for required changes
        checks = {
            "logger_name": "llamacpp_inprocess" in content,
            "metrics_prefix": "llamacpp_requests_total" in content,
            "no_ollama_refs": "ollama" not in content.lower(),
            "docstring_updated": "llama-cpp-python" in content,
            "log_messages": "[llamacpp_inprocess]" in content
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        if passed == total:
            return {"status": "PASS", "checks": checks, "summary": f"All {total} checks passed"}
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            return {"status": "FAIL", "checks": checks, "failed": failed_checks, 
                   "summary": f"{passed}/{total} checks passed"}
    
    def _validate_llama_plugin(self) -> Dict[str, Any]:
        """Validate llama_plugin.py has been properly updated"""
        plugin_file = Path("plugin_marketplace/ai/llm-services/llama/llama_plugin.py")
        
        if not plugin_file.exists():
            return {"status": "SKIP", "reason": "File not found", "summary": "File missing"}
        
        content = plugin_file.read_text()
        
        # Check for required changes
        checks = {
            "router_prefix": '"/llm/llamacpp"' in content,
            "router_tags": '"LlamaCpp (In-Process LLM)"' in content,
            "logger_name": '"llamacpp_plugin"' in content,
            "docstring_updated": "llama-cpp-python" in content,
            "no_ollama_refs": "ollama" not in content.lower()
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        if passed == total:
            return {"status": "PASS", "checks": checks, "summary": f"All {total} checks passed"}
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            return {"status": "FAIL", "checks": checks, "failed": failed_checks,
                   "summary": f"{passed}/{total} checks passed"}
    
    def _find_remaining_ollama_references(self) -> Dict[str, Any]:
        """Find any remaining ollama references in key files"""
        files_to_check = [
            "src/marketplace/ai/llm-services/llama/llama_client.py",
            "plugin_marketplace/ai/llm-services/llama/llama_plugin.py",
            "scripts/maintenance/fix_auth_schema.py"
        ]
        
        ollama_refs = []
        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                # Look for ollama references (case insensitive)
                matches = re.findall(r'\b[Oo]llama\b', content)
                if matches:
                    ollama_refs.append({"file": file_path, "matches": len(matches)})
        
        if not ollama_refs:
            return {"status": "PASS", "summary": "No ollama references found"}
        else:
            return {"status": "FAIL", "references": ollama_refs, 
                   "summary": f"Found ollama references in {len(ollama_refs)} files"}
    
    def _validate_default_provider(self) -> Dict[str, Any]:
        """Validate default provider is set to llamacpp"""
        schema_file = Path("scripts/maintenance/fix_auth_schema.py")
        
        if not schema_file.exists():
            return {"status": "SKIP", "reason": "Schema file not found", "summary": "File missing"}
        
        content = schema_file.read_text()
        
        # Look for preferredLLMProvider with llamacpp
        if 'preferredLLMProvider' in content and '"llamacpp"' in content:
            return {"status": "PASS", "summary": "Default provider set to llamacpp"}
        else:
            return {"status": "FAIL", "summary": "Default provider not set to llamacpp"}
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variables use LLAMACPP prefix"""
        client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
        
        if not client_file.exists():
            return {"status": "SKIP", "reason": "Client file not found", "summary": "File missing"}
        
        content = client_file.read_text()
        
        # Look for LLAMACPP environment variables
        llamacpp_vars = re.findall(r'LLAMACPP_\w+', content)
        
        if len(llamacpp_vars) >= 2:
            return {"status": "PASS", "vars": llamacpp_vars, 
                   "summary": f"Found {len(llamacpp_vars)} LLAMACPP env vars"}
        else:
            return {"status": "FAIL", "vars": llamacpp_vars,
                   "summary": f"Only found {len(llamacpp_vars)} LLAMACPP env vars"}
    
    def _validate_documentation_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a documentation file has been updated"""
        doc_file = Path(file_path)
        
        if not doc_file.exists():
            return {"status": "SKIP", "reason": "File not found", "summary": "File missing"}
        
        content = doc_file.read_text()
        
        # Check for llamacpp references and absence of ollama
        has_llamacpp = "llamacpp" in content.lower()
        has_ollama = "ollama" in content.lower()
        
        if has_llamacpp and not has_ollama:
            return {"status": "PASS", "summary": "Updated to use llamacpp"}
        elif has_llamacpp and has_ollama:
            return {"status": "PARTIAL", "summary": "Has llamacpp but still has ollama references"}
        elif not has_llamacpp and has_ollama:
            return {"status": "FAIL", "summary": "Still uses ollama, no llamacpp"}
        else:
            return {"status": "NEUTRAL", "summary": "No LLM provider references found"}
    
    def _validate_logger_names(self) -> Dict[str, Any]:
        """Validate logger names use llamacpp terminology"""
        files_to_check = [
            ("src/marketplace/ai/llm-services/llama/llama_client.py", "llamacpp_inprocess"),
            ("plugin_marketplace/ai/llm-services/llama/llama_plugin.py", "llamacpp_plugin")
        ]
        
        results = []
        for file_path, expected_logger in files_to_check:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                if expected_logger in content:
                    results.append({"file": file_path, "logger": expected_logger, "found": True})
                else:
                    results.append({"file": file_path, "logger": expected_logger, "found": False})
        
        found_count = sum(1 for r in results if r["found"])
        total_count = len(results)
        
        if found_count == total_count:
            return {"status": "PASS", "results": results, 
                   "summary": f"All {total_count} logger names updated"}
        else:
            return {"status": "FAIL", "results": results,
                   "summary": f"{found_count}/{total_count} logger names updated"}
    
    def _validate_metric_names(self) -> Dict[str, Any]:
        """Validate Prometheus metrics use llamacpp naming"""
        client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
        
        if not client_file.exists():
            return {"status": "SKIP", "reason": "Client file not found", "summary": "File missing"}
        
        content = client_file.read_text()
        
        expected_metrics = [
            "llamacpp_requests_total",
            "llamacpp_latency_seconds",
            "llamacpp_errors_total", 
            "llamacpp_inflight_requests"
        ]
        
        found_metrics = [metric for metric in expected_metrics if metric in content]
        
        if len(found_metrics) == len(expected_metrics):
            return {"status": "PASS", "found": found_metrics,
                   "summary": f"All {len(expected_metrics)} metrics updated"}
        else:
            missing = [m for m in expected_metrics if m not in found_metrics]
            return {"status": "FAIL", "found": found_metrics, "missing": missing,
                   "summary": f"{len(found_metrics)}/{len(expected_metrics)} metrics updated"}
    
    def _validate_log_messages(self) -> Dict[str, Any]:
        """Validate log messages use llamacpp terminology"""
        client_file = Path("src/marketplace/ai/llm-services/llama/llama_client.py")
        
        if not client_file.exists():
            return {"status": "SKIP", "reason": "Client file not found", "summary": "File missing"}
        
        content = client_file.read_text()
        
        # Look for log messages with llamacpp_inprocess prefix
        llamacpp_log_msgs = re.findall(r'\[llamacpp_inprocess\]', content)
        
        if len(llamacpp_log_msgs) >= 3:  # Should have several log messages
            return {"status": "PASS", "count": len(llamacpp_log_msgs),
                   "summary": f"Found {len(llamacpp_log_msgs)} llamacpp log messages"}
        else:
            return {"status": "FAIL", "count": len(llamacpp_log_msgs),
                   "summary": f"Only found {len(llamacpp_log_msgs)} llamacpp log messages"}
    
    def assess_overall_status(self):
        """Assess overall migration status based on test results"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        partial_tests = 0
        
        def count_results(category):
            nonlocal total_tests, passed_tests, failed_tests, skipped_tests, partial_tests
            for test_result in category.values():
                if isinstance(test_result, dict) and "status" in test_result:
                    total_tests += 1
                    status = test_result["status"]
                    if status == "PASS":
                        passed_tests += 1
                    elif status == "FAIL":
                        failed_tests += 1
                    elif status == "SKIP":
                        skipped_tests += 1
                    elif status == "PARTIAL":
                        partial_tests += 1
        
        for category in ["code_changes", "configuration_changes", "documentation_changes", "logging_metrics_changes"]:
            count_results(self.results[category])
        
        print(f"\n📊 Test Summary:")
        print(f"  Total: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Partial: {partial_tests}")
        print(f"  Skipped: {skipped_tests}")
        
        if failed_tests == 0 and passed_tests > 0:
            self.results["overall_status"] = "PASS"
            print(f"✅ Overall Status: PASS")
        elif failed_tests > 0:
            self.results["overall_status"] = "FAIL"
            print(f"❌ Overall Status: FAIL ({failed_tests} failures)")
        else:
            self.results["overall_status"] = "INCONCLUSIVE"
            print(f"⚠️  Overall Status: INCONCLUSIVE")

def main():
    """Main validation function"""
    validator = StaticMigrationValidator()
    results = validator.run_all_tests()
    
    # Save results to file
    results_file = Path("llamacpp_static_validation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Print detailed results for failures
    if results["overall_status"] == "FAIL":
        print(f"\n🔍 Detailed Failure Analysis:")
        for category, tests in results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and result.get("status") == "FAIL":
                        print(f"  ❌ {category}.{test_name}: {result.get('summary', 'No summary')}")
                        if "failed" in result:
                            print(f"     Failed checks: {result['failed']}")
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    elif results["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()