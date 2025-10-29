"""
Simple test for authentication testing utilities without external dependencies.
"""

import sys
import os
import asyncio
from unittest.mock import Mock

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_token_generator():
    """Test basic token generator functionality."""
    try:
        from extension_test_auth_utils import TestTokenGenerator
        
        generator = TestTokenGenerator()
        
        # Test token generation
        token = generator.generate_access_token()
        assert isinstance(token, str)
        assert len(token) > 0
        print("✓ Token generation works")
        
        # Test token decoding
        payload = generator.decode_token(token)
        assert payload['user_id'] == 'test-user'
        print("✓ Token decoding works")
        
        # Test admin token
        admin_token = generator.generate_admin_token()
        admin_payload = generator.decode_token(admin_token)
        assert 'admin' in admin_payload['roles']
        print("✓ Admin token generation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Token generator test failed: {e}")
        return False

async def test_mock_auth_middleware():
    """Test mock authentication middleware."""
    try:
        from extension_test_auth_utils import MockAuthMiddleware
        
        middleware = MockAuthMiddleware()
        
        # Test successful auth
        mock_request = Mock()
        mock_credentials = Mock()
        
        user_context = await middleware.authenticate_request(mock_request, mock_credentials)
        assert user_context['user_id'] == 'test-user'
        print("✓ Mock auth middleware works")
        
        # Test failure mode
        middleware.set_failure_mode(True, "forbidden")
        try:
            await middleware.authenticate_request(mock_request, mock_credentials)
            assert False, "Should have raised exception"
        except Exception:
            print("✓ Mock auth failure mode works")
        
        return True
        
    except Exception as e:
        print(f"✗ Mock auth middleware test failed: {e}")
        return False

def test_auth_helper():
    """Test authentication helper."""
    try:
        from extension_test_auth_utils import AuthTestHelper
        
        helper = AuthTestHelper()
        
        # Test header generation
        headers = helper.get_auth_headers()
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
        print("✓ Auth helper header generation works")
        
        # Test scenarios
        scenarios = helper.create_test_scenarios()
        assert len(scenarios) == 6
        print("✓ Auth helper scenarios work")
        
        return True
        
    except Exception as e:
        print(f"✗ Auth helper test failed: {e}")
        return False

async def test_performance_tester():
    """Test performance tester."""
    try:
        from extension_test_auth_utils import AuthPerformanceTester
        
        tester = AuthPerformanceTester()
        
        # Test token generation performance
        result = await tester.measure_token_generation_performance(iterations=10)
        assert result['operation'] == 'token_generation'
        assert result['tokens_per_second'] > 0
        print("✓ Performance tester works")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance tester test failed: {e}")
        return False

def test_default_instances():
    """Test default instances."""
    try:
        from extension_test_auth_utils import (
            default_token_generator,
            default_auth_helper,
            default_performance_tester
        )
        
        # Test default token generator
        token = default_token_generator.generate_access_token()
        assert len(token) > 0
        print("✓ Default token generator works")
        
        # Test default auth helper
        headers = default_auth_helper.get_auth_headers()
        assert 'Authorization' in headers
        print("✓ Default auth helper works")
        
        # Test default performance tester
        summary = default_performance_tester.get_performance_summary()
        assert isinstance(summary, dict)
        print("✓ Default performance tester works")
        
        return True
        
    except Exception as e:
        print(f"✗ Default instances test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing Extension Authentication Testing Utilities...")
    print("=" * 60)
    
    tests = [
        ("Token Generator", test_token_generator),
        ("Mock Auth Middleware", test_mock_auth_middleware),
        ("Auth Helper", test_auth_helper),
        ("Performance Tester", test_performance_tester),
        ("Default Instances", test_default_instances)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\nTesting {name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✓ {name} - PASSED")
            else:
                print(f"✗ {name} - FAILED")
                
        except Exception as e:
            print(f"✗ {name} - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All authentication testing utilities are working correctly!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)