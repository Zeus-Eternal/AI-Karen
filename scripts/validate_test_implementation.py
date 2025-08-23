#!/usr/bin/env python3
"""
Test Implementation Validation Script

Validates that all required tests for task 15 have been implemented correctly.
Checks for test coverage, file structure, and implementation completeness.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import json


class TestImplementationValidator:
    """Validates the comprehensive test implementation."""
    
    def __init__(self):
        self.validation_results = {
            "e2e_tests": {"required": [], "found": [], "missing": []},
            "integration_tests": {"required": [], "found": [], "missing": []},
            "load_tests": {"required": [], "found": [], "missing": []},
            "documentation": {"required": [], "found": [], "missing": []},
            "test_runner": {"required": [], "found": [], "missing": []}
        }
        
        # Define required test implementations
        self.required_implementations = {
            "e2e_tests": [
                "test_complete_login_to_logout_journey",
                "test_session_persistence_across_page_refresh", 
                "test_automatic_token_refresh_flow",
                "test_session_expiry_with_intelligent_error",
                "test_multiple_concurrent_requests_with_refresh",
                "test_admin_access_with_role_validation",
                "test_api_key_missing_error_response",
                "test_rate_limit_error_response",
                "test_database_error_response",
                "test_session_performance_under_load",
                "test_graceful_degradation_on_service_failure"
            ],
            "integration_tests": [
                "test_openai_api_key_classification_accuracy",
                "test_anthropic_api_key_classification_accuracy",
                "test_session_expiry_classification_accuracy",
                "test_rate_limit_classification_accuracy",
                "test_database_error_classification_accuracy",
                "test_provider_unavailable_classification_accuracy",
                "test_network_error_classification_accuracy",
                "test_validation_error_classification_accuracy",
                "test_response_completeness",
                "test_next_steps_quality",
                "test_response_tone_consistency",
                "test_response_specificity",
                "test_provider_health_context_integration",
                "test_ai_enhanced_response_generation",
                "test_deterministic_classification",
                "test_response_stability_over_time"
            ],
            "load_tests": [
                "test_concurrent_login_requests",
                "test_login_endpoint_sustained_load",
                "test_concurrent_token_refresh",
                "test_token_refresh_memory_usage",
                "test_concurrent_protected_requests",
                "test_mixed_workload_performance",
                "test_memory_leak_detection",
                "test_cpu_usage_under_load"
            ],
            "documentation": [
                "authentication_api.md",
                "authentication_troubleshooting.md"
            ],
            "test_runner": [
                "run_comprehensive_tests.py",
                "validate_test_implementation.py"
            ]
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Validating Test Implementation")
        print("=" * 50)
        
        # Validate each category
        self._validate_e2e_tests()
        self._validate_integration_tests()
        self._validate_load_tests()
        self._validate_documentation()
        self._validate_test_runner()
        
        # Generate summary
        return self._generate_validation_summary()
    
    def _validate_e2e_tests(self):
        """Validate end-to-end tests implementation."""
        print("\n📋 Validating E2E Tests...")
        
        e2e_file = "tests/e2e/test_session_persistence_e2e.py"
        required_tests = self.required_implementations["e2e_tests"]
        
        if not os.path.exists(e2e_file):
            print(f"❌ E2E test file not found: {e2e_file}")
            self.validation_results["e2e_tests"]["missing"] = required_tests
            return
        
        # Parse the test file
        found_tests = self._extract_test_functions(e2e_file)
        self.validation_results["e2e_tests"]["found"] = found_tests
        self.validation_results["e2e_tests"]["required"] = required_tests
        
        # Check for missing tests
        missing_tests = set(required_tests) - set(found_tests)
        self.validation_results["e2e_tests"]["missing"] = list(missing_tests)
        
        print(f"  ✅ Found {len(found_tests)} test functions")
        print(f"  📋 Required {len(required_tests)} test functions")
        
        if missing_tests:
            print(f"  ❌ Missing {len(missing_tests)} required tests:")
            for test in missing_tests:
                print(f"    - {test}")
        else:
            print("  ✅ All required E2E tests implemented")
    
    def _validate_integration_tests(self):
        """Validate integration tests implementation."""
        print("\n🔗 Validating Integration Tests...")
        
        integration_file = "tests/integration/test_intelligent_response_quality.py"
        required_tests = self.required_implementations["integration_tests"]
        
        if not os.path.exists(integration_file):
            print(f"❌ Integration test file not found: {integration_file}")
            self.validation_results["integration_tests"]["missing"] = required_tests
            return
        
        # Parse the test file
        found_tests = self._extract_test_functions(integration_file)
        self.validation_results["integration_tests"]["found"] = found_tests
        self.validation_results["integration_tests"]["required"] = required_tests
        
        # Check for missing tests
        missing_tests = set(required_tests) - set(found_tests)
        self.validation_results["integration_tests"]["missing"] = list(missing_tests)
        
        print(f"  ✅ Found {len(found_tests)} test functions")
        print(f"  📋 Required {len(required_tests)} test functions")
        
        if missing_tests:
            print(f"  ❌ Missing {len(missing_tests)} required tests:")
            for test in missing_tests:
                print(f"    - {test}")
        else:
            print("  ✅ All required integration tests implemented")
    
    def _validate_load_tests(self):
        """Validate load tests implementation."""
        print("\n⚡ Validating Load Tests...")
        
        load_file = "tests/load/test_auth_load_testing.py"
        required_tests = self.required_implementations["load_tests"]
        
        if not os.path.exists(load_file):
            print(f"❌ Load test file not found: {load_file}")
            self.validation_results["load_tests"]["missing"] = required_tests
            return
        
        # Parse the test file
        found_tests = self._extract_test_functions(load_file)
        self.validation_results["load_tests"]["found"] = found_tests
        self.validation_results["load_tests"]["required"] = required_tests
        
        # Check for missing tests
        missing_tests = set(required_tests) - set(found_tests)
        self.validation_results["load_tests"]["missing"] = list(missing_tests)
        
        print(f"  ✅ Found {len(found_tests)} test functions")
        print(f"  📋 Required {len(required_tests)} test functions")
        
        if missing_tests:
            print(f"  ❌ Missing {len(missing_tests)} required tests:")
            for test in missing_tests:
                print(f"    - {test}")
        else:
            print("  ✅ All required load tests implemented")
        
        # Check for performance metrics collection
        if os.path.exists(load_file):
            with open(load_file, 'r') as f:
                content = f.read()
                
            performance_indicators = [
                "LoadTestMetrics",
                "response_times",
                "memory_usage",
                "cpu_usage",
                "requests_per_second"
            ]
            
            found_indicators = [ind for ind in performance_indicators if ind in content]
            print(f"  📊 Performance metrics: {len(found_indicators)}/{len(performance_indicators)}")
    
    def _validate_documentation(self):
        """Validate documentation implementation."""
        print("\n📚 Validating Documentation...")
        
        required_docs = self.required_implementations["documentation"]
        found_docs = []
        missing_docs = []
        
        for doc in required_docs:
            if doc == "authentication_api.md":
                doc_path = "docs/api/authentication_api.md"
            elif doc == "authentication_troubleshooting.md":
                doc_path = "docs/user/authentication_troubleshooting.md"
            else:
                doc_path = f"docs/{doc}"
            
            if os.path.exists(doc_path):
                found_docs.append(doc)
                print(f"  ✅ Found: {doc_path}")
                
                # Check documentation quality
                self._validate_documentation_quality(doc_path, doc)
            else:
                missing_docs.append(doc)
                print(f"  ❌ Missing: {doc_path}")
        
        self.validation_results["documentation"]["found"] = found_docs
        self.validation_results["documentation"]["required"] = required_docs
        self.validation_results["documentation"]["missing"] = missing_docs
    
    def _validate_documentation_quality(self, doc_path: str, doc_name: str):
        """Validate the quality and completeness of documentation."""
        with open(doc_path, 'r') as f:
            content = f.read()
        
        if doc_name == "authentication_api.md":
            required_sections = [
                "Authentication Flow",
                "POST /auth/login",
                "POST /auth/refresh", 
                "GET /auth/me",
                "POST /auth/logout",
                "Error Response Format",
                "Security Features",
                "Client Integration"
            ]
        elif doc_name == "authentication_troubleshooting.md":
            required_sections = [
                "Getting Logged Out When Refreshing",
                "API Key Missing",
                "Rate Limit Exceeded",
                "Invalid Login Credentials",
                "Database Connection Errors",
                "Service Temporarily Unavailable",
                "Getting Help"
            ]
        else:
            required_sections = []
        
        found_sections = [section for section in required_sections if section in content]
        missing_sections = set(required_sections) - set(found_sections)
        
        print(f"    📋 Sections: {len(found_sections)}/{len(required_sections)}")
        if missing_sections:
            print(f"    ❌ Missing sections: {', '.join(missing_sections)}")
    
    def _validate_test_runner(self):
        """Validate test runner implementation."""
        print("\n🏃 Validating Test Runner...")
        
        required_files = self.required_implementations["test_runner"]
        found_files = []
        missing_files = []
        
        for file_name in required_files:
            file_path = f"scripts/{file_name}"
            
            if os.path.exists(file_path):
                found_files.append(file_name)
                print(f"  ✅ Found: {file_path}")
                
                # Check if executable
                if os.access(file_path, os.X_OK):
                    print(f"    ✅ Executable permissions set")
                else:
                    print(f"    ⚠️  Not executable (run: chmod +x {file_path})")
                
                # Check for key functionality
                if file_name == "run_comprehensive_tests.py":
                    self._validate_test_runner_functionality(file_path)
                    
            else:
                missing_files.append(file_name)
                print(f"  ❌ Missing: {file_path}")
        
        self.validation_results["test_runner"]["found"] = found_files
        self.validation_results["test_runner"]["required"] = required_files
        self.validation_results["test_runner"]["missing"] = missing_files
    
    def _validate_test_runner_functionality(self, file_path: str):
        """Validate test runner functionality."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        required_features = [
            "TestRunner",
            "run_all_tests",
            "unit_tests",
            "integration_tests", 
            "e2e_tests",
            "load_tests",
            "coverage",
            "json_report"
        ]
        
        found_features = [feature for feature in required_features if feature in content]
        print(f"    📋 Features: {len(found_features)}/{len(required_features)}")
        
        missing_features = set(required_features) - set(found_features)
        if missing_features:
            print(f"    ❌ Missing features: {', '.join(missing_features)}")
    
    def _extract_test_functions(self, file_path: str) -> List[str]:
        """Extract test function names from a Python test file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            test_functions = []
            
            # Walk through all nodes to find test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef) and node.name.startswith('test_'):
                    test_functions.append(node.name)
            
            # Also check for test methods inside classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith('test_'):
                            test_functions.append(item.name)
            
            return list(set(test_functions))  # Remove duplicates
            
        except Exception as e:
            print(f"    ⚠️  Error parsing {file_path}: {e}")
            return []
    
    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        total_required = 0
        total_found = 0
        total_missing = 0
        
        categories_status = {}
        
        for category, results in self.validation_results.items():
            required = len(results["required"])
            found = len(results["found"])
            missing = len(results["missing"])
            
            total_required += required
            total_found += found
            total_missing += missing
            
            status = "✅" if missing == 0 else "❌"
            completion_rate = (found / required * 100) if required > 0 else 100
            
            categories_status[category] = {
                "status": status,
                "completion_rate": completion_rate,
                "found": found,
                "required": required,
                "missing": missing
            }
            
            print(f"{status} {category.replace('_', ' ').title()}: {found}/{required} ({completion_rate:.1f}%)")
        
        overall_completion = (total_found / total_required * 100) if total_required > 0 else 100
        overall_status = "✅" if total_missing == 0 else "❌"
        
        print(f"\n{overall_status} Overall Completion: {total_found}/{total_required} ({overall_completion:.1f}%)")
        
        # Detailed missing items
        if total_missing > 0:
            print(f"\n❌ Missing Items ({total_missing} total):")
            for category, results in self.validation_results.items():
                if results["missing"]:
                    print(f"  {category.replace('_', ' ').title()}:")
                    for item in results["missing"]:
                        print(f"    - {item}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if total_missing > 0:
            print("   - Implement missing test functions and documentation")
            print("   - Run the comprehensive test suite to verify functionality")
        else:
            print("   - All required implementations are present")
            print("   - Run tests to verify functionality: python scripts/run_comprehensive_tests.py")
        
        # Save validation report
        validation_report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "overall_completion": overall_completion,
            "categories": categories_status,
            "details": self.validation_results
        }
        
        os.makedirs("reports", exist_ok=True)
        report_file = "reports/validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        print(f"\n📄 Validation report saved to: {report_file}")
        
        return validation_report


def main():
    """Main entry point."""
    validator = TestImplementationValidator()
    results = validator.validate_all()
    
    # Exit with appropriate code
    overall_completion = results.get("overall_completion", 0)
    if overall_completion >= 100:
        print("\n✅ All required implementations are complete!")
        sys.exit(0)
    else:
        print(f"\n❌ Implementation is {overall_completion:.1f}% complete")
        sys.exit(1)


if __name__ == "__main__":
    main()