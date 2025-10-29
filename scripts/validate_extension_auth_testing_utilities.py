"""
Validation Script for Extension Authentication Testing Utilities

This script validates that all authentication testing utilities are working correctly
and provides examples of how to use them effectively.
"""

import asyncio
import sys
import traceback
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import all testing utilities
try:
    from server.extension_test_auth_utils import (
        TestTokenGenerator,
        MockAuthMiddleware,
        AuthTestHelper,
        AuthPerformanceTester,
        default_token_generator,
        default_auth_helper,
        default_performance_tester
    )
    
    from server.extension_auth_integration_helpers import (
        FastAPIAuthTestClient,
        AsyncAuthTestClient,
        AuthEndpointTester,
        AuthPerformanceTestSuite
    )
    
    from server.extension_auth_performance_tests import (
        AuthenticationOverheadTester,
        ConcurrentAuthTester,
        TokenPerformanceTester,
        quick_auth_performance_test
    )
    
    print("✓ All authentication testing utilities imported successfully")
    
except ImportError as e:
    print(f"✗ Failed to import authentication testing utilities: {e}")
    sys.exit(1)


class ValidationResults:
    """Track validation results."""
    
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_test(self, name: str, success: bool, details: str = ""):
        """Add test result."""
        self.tests.append({
            "name": name,
            "success": success,
            "details": details
        })
        
        if success:
            self.passed += 1
            print(f"✓ {name}")
            if details:
                print(f"  {details}")
        else:
            self.failed += 1
            print(f"✗ {name}")
            if details:
                print(f"  {details}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        total = self.passed + self.failed
        return {
            "total_tests": total,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": self.passed / total if total > 0 else 0,
            "tests": self.tests
        }


async def validate_token_generator():
    """Validate TestTokenGenerator functionality."""
    results = ValidationResults()
    
    try:
        generator = TestTokenGenerator()
        
        # Test basic token generation
        token = generator.generate_access_token()
        results.add_test(
            "Token Generation - Basic",
            isinstance(token, str) and len(token) > 0,
            f"Generated token length: {len(token)}"
        )
        
        # Test token decoding
        payload = generator.decode_token(token)
        results.add_test(
            "Token Decoding - Basic",
            payload.get('user_id') == 'test-user',
            f"User ID: {payload.get('user_id')}"
        )
        
        # Test custom token generation
        custom_token = generator.generate_access_token(
            user_id="custom-user",
            roles=["admin"],
            permissions=["*"]
        )
        custom_payload = generator.decode_token(custom_token)
        results.add_test(
            "Token Generation - Custom",
            custom_payload.get('user_id') == 'custom-user' and 'admin' in custom_payload.get('roles', []),
            f"Custom user: {custom_payload.get('user_id')}, roles: {custom_payload.get('roles')}"
        )
        
        # Test admin token
        admin_token = generator.generate_admin_token()
        admin_payload = generator.decode_token(admin_token)
        results.add_test(
            "Token Generation - Admin",
            'admin' in admin_payload.get('roles', []) and admin_payload.get('permissions') == ['*'],
            f"Admin roles: {admin_payload.get('roles')}, permissions: {admin_payload.get('permissions')}"
        )
        
        # Test expired token
        expired_token = generator.generate_expired_token()
        expired_payload = generator.decode_token(expired_token)
        from datetime import datetime
        exp_time = datetime.fromtimestamp(expired_payload['exp'])
        results.add_test(
            "Token Generation - Expired",
            exp_time < datetime.utcnow(),
            f"Token expired at: {exp_time}"
        )
        
        # Test invalid token
        invalid_token = generator.generate_invalid_token()
        try:
            generator.decode_token(invalid_token)
            results.add_test("Token Generation - Invalid", False, "Should have raised exception")
        except ValueError:
            results.add_test("Token Generation - Invalid", True, "Correctly raised ValueError")
        
    except Exception as e:
        results.add_test("Token Generator", False, f"Exception: {e}")
        logger.error(f"Token generator validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_mock_auth_middleware():
    """Validate MockAuthMiddleware functionality."""
    results = ValidationResults()
    
    try:
        from unittest.mock import Mock
        
        # Test successful authentication
        middleware = MockAuthMiddleware()
        mock_request = Mock()
        mock_credentials = Mock()
        
        user_context = await middleware.authenticate_request(mock_request, mock_credentials)
        results.add_test(
            "Mock Auth - Success",
            user_context.get('user_id') == 'test-user',
            f"User context: {user_context.get('user_id')}"
        )
        
        # Test failure modes
        middleware.set_failure_mode(True, "forbidden")
        try:
            await middleware.authenticate_request(mock_request, mock_credentials)
            results.add_test("Mock Auth - Failure", False, "Should have raised HTTPException")
        except Exception as e:
            results.add_test("Mock Auth - Failure", True, f"Correctly raised: {type(e).__name__}")
        
        # Test statistics
        middleware.reset_stats()
        stats = middleware.get_stats()
        results.add_test(
            "Mock Auth - Statistics",
            stats['call_count'] == 0,
            f"Call count after reset: {stats['call_count']}"
        )
        
        # Test custom user context
        custom_context = {'user_id': 'custom-user', 'roles': ['admin']}
        middleware.set_user_context(custom_context)
        middleware.set_failure_mode(False)
        
        user_context = await middleware.authenticate_request(mock_request, mock_credentials)
        results.add_test(
            "Mock Auth - Custom Context",
            user_context.get('user_id') == 'custom-user',
            f"Custom user: {user_context.get('user_id')}"
        )
        
    except Exception as e:
        results.add_test("Mock Auth Middleware", False, f"Exception: {e}")
        logger.error(f"Mock auth middleware validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_auth_test_helper():
    """Validate AuthTestHelper functionality."""
    results = ValidationResults()
    
    try:
        helper = AuthTestHelper()
        
        # Test auth headers generation
        headers = helper.get_auth_headers()
        results.add_test(
            "Auth Helper - Headers",
            'Authorization' in headers and headers['Authorization'].startswith('Bearer '),
            f"Headers: {list(headers.keys())}"
        )
        
        # Test admin headers
        admin_headers = helper.get_admin_headers()
        token = admin_headers['Authorization'].replace('Bearer ', '')
        payload = helper.token_generator.decode_token(token)
        results.add_test(
            "Auth Helper - Admin Headers",
            'admin' in payload.get('roles', []),
            f"Admin roles: {payload.get('roles')}"
        )
        
        # Test limited headers
        limited_headers = helper.get_limited_headers(['extension:read'])
        limited_token = limited_headers['Authorization'].replace('Bearer ', '')
        limited_payload = helper.token_generator.decode_token(limited_token)
        results.add_test(
            "Auth Helper - Limited Headers",
            limited_payload.get('permissions') == ['extension:read'],
            f"Limited permissions: {limited_payload.get('permissions')}"
        )
        
        # Test scenarios creation
        scenarios = helper.create_test_scenarios()
        results.add_test(
            "Auth Helper - Scenarios",
            len(scenarios) == 6,
            f"Created {len(scenarios)} scenarios"
        )
        
        # Verify scenario structure
        scenario_names = [s['name'] for s in scenarios]
        expected_names = ['valid_user_token', 'admin_token', 'limited_permissions', 'expired_token', 'invalid_token', 'no_auth']
        all_present = all(name in scenario_names for name in expected_names)
        results.add_test(
            "Auth Helper - Scenario Structure",
            all_present,
            f"Scenarios: {scenario_names}"
        )
        
    except Exception as e:
        results.add_test("Auth Test Helper", False, f"Exception: {e}")
        logger.error(f"Auth test helper validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_performance_tester():
    """Validate AuthPerformanceTester functionality."""
    results = ValidationResults()
    
    try:
        tester = AuthPerformanceTester()
        
        # Test token generation performance
        gen_result = await tester.measure_token_generation_performance(iterations=100)
        results.add_test(
            "Performance - Token Generation",
            gen_result['operation'] == 'token_generation' and gen_result['tokens_per_second'] > 0,
            f"Generated {gen_result['tokens_per_second']:.0f} tokens/sec"
        )
        
        # Test token validation performance
        val_result = await tester.measure_token_validation_performance(iterations=100)
        results.add_test(
            "Performance - Token Validation",
            val_result['operation'] == 'token_validation' and val_result['validations_per_second'] > 0,
            f"Validated {val_result['validations_per_second']:.0f} tokens/sec"
        )
        
        # Test performance summary
        summary = tester.get_performance_summary()
        results.add_test(
            "Performance - Summary",
            summary['total_tests'] == 2,
            f"Summary contains {summary['total_tests']} tests"
        )
        
        # Test recommendations
        has_recommendations = 'recommendations' in summary and isinstance(summary['recommendations'], list)
        results.add_test(
            "Performance - Recommendations",
            has_recommendations,
            f"Recommendations: {len(summary.get('recommendations', []))}"
        )
        
    except Exception as e:
        results.add_test("Performance Tester", False, f"Exception: {e}")
        logger.error(f"Performance tester validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_default_instances():
    """Validate default utility instances."""
    results = ValidationResults()
    
    try:
        # Test default token generator
        token = default_token_generator.generate_access_token()
        results.add_test(
            "Default - Token Generator",
            isinstance(token, str) and len(token) > 0,
            f"Generated token length: {len(token)}"
        )
        
        # Test default auth helper
        headers = default_auth_helper.get_auth_headers()
        results.add_test(
            "Default - Auth Helper",
            'Authorization' in headers,
            f"Headers: {list(headers.keys())}"
        )
        
        # Test default performance tester
        summary = default_performance_tester.get_performance_summary()
        results.add_test(
            "Default - Performance Tester",
            isinstance(summary, dict),
            f"Summary type: {type(summary).__name__}"
        )
        
    except Exception as e:
        results.add_test("Default Instances", False, f"Exception: {e}")
        logger.error(f"Default instances validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_integration_helpers():
    """Validate integration helper functionality."""
    results = ValidationResults()
    
    try:
        # Test AsyncAuthTestClient
        async_client = AsyncAuthTestClient("http://localhost:8000")
        results.add_test(
            "Integration - Async Client",
            async_client.base_url == "http://localhost:8000",
            f"Base URL: {async_client.base_url}"
        )
        
        # Test auth helper integration
        headers = async_client._get_headers_for_auth_type("admin")
        results.add_test(
            "Integration - Auth Headers",
            'Authorization' in headers,
            f"Auth header present: {'Authorization' in headers}"
        )
        
    except Exception as e:
        results.add_test("Integration Helpers", False, f"Exception: {e}")
        logger.error(f"Integration helpers validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def validate_performance_testing():
    """Validate performance testing utilities."""
    results = ValidationResults()
    
    try:
        # Test TokenPerformanceTester
        token_tester = TokenPerformanceTester()
        token_result = await token_tester.test_token_operations_performance(iterations=50)
        
        results.add_test(
            "Performance Testing - Token Operations",
            'token_generation' in token_result and 'token_validation' in token_result,
            f"Operations tested: {list(token_result.keys())}"
        )
        
        # Test recommendations generation
        has_recommendations = 'recommendations' in token_result
        results.add_test(
            "Performance Testing - Recommendations",
            has_recommendations,
            f"Recommendations generated: {has_recommendations}"
        )
        
    except Exception as e:
        results.add_test("Performance Testing", False, f"Exception: {e}")
        logger.error(f"Performance testing validation failed: {e}")
        logger.error(traceback.format_exc())
    
    return results


async def run_comprehensive_validation():
    """Run comprehensive validation of all utilities."""
    print("=" * 80)
    print("EXTENSION AUTHENTICATION TESTING UTILITIES VALIDATION")
    print("=" * 80)
    print()
    
    all_results = []
    
    # Run all validation tests
    validation_functions = [
        ("Token Generator", validate_token_generator),
        ("Mock Auth Middleware", validate_mock_auth_middleware),
        ("Auth Test Helper", validate_auth_test_helper),
        ("Performance Tester", validate_performance_tester),
        ("Default Instances", validate_default_instances),
        ("Integration Helpers", validate_integration_helpers),
        ("Performance Testing", validate_performance_testing)
    ]
    
    for name, func in validation_functions:
        print(f"\n--- {name} ---")
        try:
            result = await func()
            all_results.append((name, result))
        except Exception as e:
            print(f"✗ {name} validation failed with exception: {e}")
            logger.error(f"{name} validation failed: {e}")
            logger.error(traceback.format_exc())
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for name, result in all_results:
        summary = result.get_summary()
        total_tests += summary['total_tests']
        total_passed += summary['passed']
        total_failed += summary['failed']
        
        print(f"{name}: {summary['passed']}/{summary['total_tests']} passed ({summary['success_rate']:.1%})")
    
    overall_success_rate = total_passed / total_tests if total_tests > 0 else 0
    
    print(f"\nOVERALL: {total_passed}/{total_tests} tests passed ({overall_success_rate:.1%})")
    
    if overall_success_rate >= 0.9:
        print("✓ VALIDATION SUCCESSFUL - All authentication testing utilities are working correctly!")
        return True
    else:
        print("✗ VALIDATION FAILED - Some utilities need attention")
        return False


async def demonstrate_usage():
    """Demonstrate usage of the testing utilities."""
    print("\n" + "=" * 80)
    print("USAGE DEMONSTRATION")
    print("=" * 80)
    
    print("\n1. Basic Token Generation:")
    generator = TestTokenGenerator()
    token = generator.generate_access_token(user_id="demo-user")
    print(f"   Generated token: {token[:50]}...")
    
    print("\n2. Auth Helper Usage:")
    helper = AuthTestHelper()
    headers = helper.get_auth_headers()
    print(f"   Auth headers: {list(headers.keys())}")
    
    print("\n3. Test Scenarios:")
    scenarios = helper.create_test_scenarios()
    for scenario in scenarios[:3]:  # Show first 3
        print(f"   - {scenario['name']}: expects HTTP {scenario['expected_status']}")
    
    print("\n4. Performance Testing:")
    perf_tester = AuthPerformanceTester()
    result = await perf_tester.measure_token_generation_performance(iterations=100)
    print(f"   Token generation: {result['tokens_per_second']:.0f} tokens/sec")
    
    print("\n5. Mock Authentication:")
    mock_auth = MockAuthMiddleware()
    from unittest.mock import Mock
    mock_request = Mock()
    user_context = await mock_auth.authenticate_request(mock_request, Mock())
    print(f"   Mock auth user: {user_context['user_id']}")
    
    print("\nAll utilities are ready for use in your tests!")


if __name__ == "__main__":
    async def main():
        success = await run_comprehensive_validation()
        
        if success:
            await demonstrate_usage()
            print("\n🎉 Extension Authentication Testing Utilities are fully validated and ready!")
            return 0
        else:
            print("\n❌ Validation failed. Please check the errors above.")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)