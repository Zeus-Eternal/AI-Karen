"""
Extension Authentication Testing Utilities

This module provides utilities for testing extension authentication including:
- Test token generation
- Mock authentication middleware
- Integration test helpers
- Performance testing utilities
"""

import jwt
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

# Mock FastAPI classes for testing without FastAPI dependency
class MockRequest:
    def __init__(self):
        self.url = MockURL()
        self.method = "GET"
        self.headers = {}
        self.client = MockClient()

class MockURL:
    def __init__(self):
        self.path = "/test"

class MockClient:
    def __init__(self):
        self.host = "127.0.0.1"

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

class HTTPAuthorizationCredentials:
    def __init__(self, credentials: str = ""):
        self.credentials = credentials

logger = logging.getLogger(__name__)


class TestTokenGenerator:
    """Utility for generating test JWT tokens for authentication testing."""
    
    def __init__(self, secret_key: str = "test-secret-key", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_access_token(
        self,
        user_id: str = "test-user",
        tenant_id: str = "test-tenant",
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_in_minutes: int = 30,
        custom_claims: Dict[str, Any] = None
    ) -> str:
        """Generate a test access token with specified claims."""
        
        if roles is None:
            roles = ["user"]
        if permissions is None:
            permissions = ["extension:read", "extension:write"]
        if custom_claims is None:
            custom_claims = {}
        
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "roles": roles,
            "permissions": permissions,
            "token_type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=expires_in_minutes),
            "jti": str(uuid.uuid4()),
            **custom_claims
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(
        self,
        user_id: str = "test-user",
        tenant_id: str = "test-tenant",
        expires_in_days: int = 7
    ) -> str:
        """Generate a test refresh token."""
        
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=expires_in_days),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_expired_token(
        self,
        user_id: str = "test-user",
        tenant_id: str = "test-tenant"
    ) -> str:
        """Generate an expired token for testing expiration handling."""
        
        past_time = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "roles": ["user"],
            "permissions": ["extension:read"],
            "token_type": "access",
            "iat": past_time - timedelta(minutes=30),
            "exp": past_time,
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_invalid_token(self) -> str:
        """Generate an invalid token for testing error handling."""
        return "invalid.token.here"
    
    def generate_admin_token(
        self,
        user_id: str = "admin-user",
        tenant_id: str = "test-tenant",
        expires_in_minutes: int = 30
    ) -> str:
        """Generate an admin token with full permissions."""
        
        return self.generate_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=["admin", "user"],
            permissions=["*"],
            expires_in_minutes=expires_in_minutes
        )
    
    def generate_limited_token(
        self,
        user_id: str = "limited-user",
        tenant_id: str = "test-tenant",
        permissions: List[str] = None,
        expires_in_minutes: int = 30
    ) -> str:
        """Generate a token with limited permissions."""
        
        if permissions is None:
            permissions = ["extension:read"]
        
        return self.generate_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=["user"],
            permissions=permissions,
            expires_in_minutes=expires_in_minutes
        )
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode a token for inspection (useful for testing)."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")


class MockAuthMiddleware:
    """Mock authentication middleware for testing."""
    
    def __init__(self, 
                 default_user_context: Dict[str, Any] = None,
                 should_fail: bool = False,
                 failure_mode: str = "forbidden"):
        """
        Initialize mock auth middleware.
        
        Args:
            default_user_context: Default user context to return
            should_fail: Whether authentication should fail
            failure_mode: Type of failure ('forbidden', 'expired', 'invalid', 'service_error')
        """
        self.default_user_context = default_user_context or {
            'user_id': 'test-user',
            'tenant_id': 'test-tenant',
            'roles': ['user'],
            'permissions': ['extension:read', 'extension:write'],
            'token_type': 'access'
        }
        self.should_fail = should_fail
        self.failure_mode = failure_mode
        self.call_count = 0
        self.last_request = None
    
    async def authenticate_request(
        self,
        request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Dict[str, Any]:
        """Mock authentication method."""
        
        self.call_count += 1
        self.last_request = request
        
        if self.should_fail:
            if self.failure_mode == "forbidden":
                raise HTTPException(status_code=403, detail="Authentication failed")
            elif self.failure_mode == "expired":
                raise HTTPException(status_code=403, detail="Token expired")
            elif self.failure_mode == "invalid":
                raise HTTPException(status_code=403, detail="Invalid token")
            elif self.failure_mode == "service_error":
                raise HTTPException(status_code=500, detail="Authentication service error")
        
        return self.default_user_context.copy()
    
    def set_user_context(self, user_context: Dict[str, Any]):
        """Set the user context to return."""
        self.default_user_context = user_context
    
    def set_failure_mode(self, should_fail: bool, failure_mode: str = "forbidden"):
        """Set failure behavior."""
        self.should_fail = should_fail
        self.failure_mode = failure_mode
    
    def reset_stats(self):
        """Reset call statistics."""
        self.call_count = 0
        self.last_request = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get call statistics."""
        return {
            'call_count': self.call_count,
            'last_request_url': str(self.last_request.url) if self.last_request else None,
            'last_request_method': self.last_request.method if self.last_request else None
        }


class AuthTestHelper:
    """Helper class for integration testing with authentication."""
    
    def __init__(self, token_generator: TestTokenGenerator = None):
        self.token_generator = token_generator or TestTokenGenerator()
        self.default_headers = {
            "Content-Type": "application/json",
            "X-Client-Type": "test-client"
        }
    
    def get_auth_headers(self, token: str = None, **token_kwargs) -> Dict[str, str]:
        """Get authentication headers for requests."""
        
        if token is None:
            token = self.token_generator.generate_access_token(**token_kwargs)
        
        headers = self.default_headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def get_admin_headers(self) -> Dict[str, str]:
        """Get admin authentication headers."""
        token = self.token_generator.generate_admin_token()
        return self.get_auth_headers(token)
    
    def get_limited_headers(self, permissions: List[str] = None) -> Dict[str, str]:
        """Get limited permission headers."""
        token = self.token_generator.generate_limited_token(permissions=permissions)
        return self.get_auth_headers(token)
    
    def get_expired_headers(self) -> Dict[str, str]:
        """Get headers with expired token."""
        token = self.token_generator.generate_expired_token()
        return self.get_auth_headers(token)
    
    def get_invalid_headers(self) -> Dict[str, str]:
        """Get headers with invalid token."""
        token = self.token_generator.generate_invalid_token()
        return self.get_auth_headers(token)
    
    def get_no_auth_headers(self) -> Dict[str, str]:
        """Get headers without authentication."""
        return self.default_headers.copy()
    
    async def make_authenticated_request(
        self,
        client,
        method: str,
        url: str,
        token: str = None,
        json_data: Dict[str, Any] = None,
        **token_kwargs
    ):
        """Make an authenticated request using test client."""
        
        headers = self.get_auth_headers(token, **token_kwargs)
        
        request_kwargs = {"headers": headers}
        if json_data:
            request_kwargs["json"] = json_data
        
        if method.upper() == "GET":
            return await client.get(url, **request_kwargs)
        elif method.upper() == "POST":
            return await client.post(url, **request_kwargs)
        elif method.upper() == "PUT":
            return await client.put(url, **request_kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(url, **request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create common test scenarios for authentication testing."""
        
        return [
            {
                "name": "valid_user_token",
                "headers": self.get_auth_headers(),
                "expected_status": 200,
                "description": "Valid user token should succeed"
            },
            {
                "name": "admin_token",
                "headers": self.get_admin_headers(),
                "expected_status": 200,
                "description": "Admin token should succeed"
            },
            {
                "name": "limited_permissions",
                "headers": self.get_limited_headers(["extension:read"]),
                "expected_status": 200,  # or 403 depending on endpoint
                "description": "Limited permissions token"
            },
            {
                "name": "expired_token",
                "headers": self.get_expired_headers(),
                "expected_status": 403,
                "description": "Expired token should fail"
            },
            {
                "name": "invalid_token",
                "headers": self.get_invalid_headers(),
                "expected_status": 403,
                "description": "Invalid token should fail"
            },
            {
                "name": "no_auth",
                "headers": self.get_no_auth_headers(),
                "expected_status": 403,
                "description": "No authentication should fail"
            }
        ]


class AuthPerformanceTester:
    """Utility for testing authentication performance."""
    
    def __init__(self, token_generator: TestTokenGenerator = None):
        self.token_generator = token_generator or TestTokenGenerator()
        self.results = []
    
    async def measure_token_generation_performance(
        self,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Measure token generation performance."""
        
        start_time = time.time()
        tokens = []
        
        for i in range(iterations):
            token = self.token_generator.generate_access_token(
                user_id=f"user-{i}",
                tenant_id=f"tenant-{i % 10}"
            )
            tokens.append(token)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        result = {
            "operation": "token_generation",
            "iterations": iterations,
            "total_time_seconds": total_time,
            "average_time_ms": (total_time / iterations) * 1000,
            "tokens_per_second": iterations / total_time,
            "sample_token_length": len(tokens[0]) if tokens else 0
        }
        
        self.results.append(result)
        return result
    
    async def measure_token_validation_performance(
        self,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Measure token validation performance."""
        
        # Generate tokens to validate
        tokens = [
            self.token_generator.generate_access_token(user_id=f"user-{i}")
            for i in range(min(100, iterations))  # Reuse tokens for validation
        ]
        
        start_time = time.time()
        valid_count = 0
        
        for i in range(iterations):
            token = tokens[i % len(tokens)]
            try:
                payload = self.token_generator.decode_token(token)
                if payload.get('user_id'):
                    valid_count += 1
            except Exception:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        result = {
            "operation": "token_validation",
            "iterations": iterations,
            "valid_tokens": valid_count,
            "total_time_seconds": total_time,
            "average_time_ms": (total_time / iterations) * 1000,
            "validations_per_second": iterations / total_time
        }
        
        self.results.append(result)
        return result
    
    async def measure_auth_middleware_performance(
        self,
        auth_middleware,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Measure authentication middleware performance."""
        
        # Create mock request
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.url.path = "/api/extensions/"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        
        # Create mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = self.token_generator.generate_access_token()
        
        start_time = time.time()
        success_count = 0
        
        for i in range(iterations):
            try:
                user_context = await auth_middleware.authenticate_request(
                    mock_request, mock_credentials
                )
                if user_context.get('user_id'):
                    success_count += 1
            except Exception:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        result = {
            "operation": "auth_middleware",
            "iterations": iterations,
            "successful_auths": success_count,
            "total_time_seconds": total_time,
            "average_time_ms": (total_time / iterations) * 1000,
            "auths_per_second": iterations / total_time
        }
        
        self.results.append(result)
        return result
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all performance tests."""
        
        if not self.results:
            return {"message": "No performance tests run"}
        
        summary = {
            "total_tests": len(self.results),
            "tests": self.results,
            "recommendations": []
        }
        
        # Add performance recommendations
        for result in self.results:
            if result["operation"] == "token_generation":
                if result["average_time_ms"] > 10:
                    summary["recommendations"].append(
                        "Token generation is slow (>10ms). Consider caching or optimization."
                    )
            elif result["operation"] == "token_validation":
                if result["average_time_ms"] > 5:
                    summary["recommendations"].append(
                        "Token validation is slow (>5ms). Consider JWT library optimization."
                    )
            elif result["operation"] == "auth_middleware":
                if result["average_time_ms"] > 20:
                    summary["recommendations"].append(
                        "Auth middleware is slow (>20ms). Consider caching user contexts."
                    )
        
        return summary
    
    def reset_results(self):
        """Reset performance test results."""
        self.results = []


# Convenience instances for easy import
default_token_generator = TestTokenGenerator()
default_auth_helper = AuthTestHelper()
default_performance_tester = AuthPerformanceTester()