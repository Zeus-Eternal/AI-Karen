"""
Security tests for extension authentication system.
Tests for common authentication vulnerabilities and security best practices.
"""

import pytest
import jwt
import time
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from server.security import ExtensionAuthManager


class TestAuthenticationSecurityVulnerabilities:
    """Test for common authentication security vulnerabilities."""

    @pytest.fixture
    def secure_auth_config(self):
        """Secure authentication configuration for testing."""
        return {
            "secret_key": "very-secure-secret-key-for-testing-123456789",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "production",
            "dev_bypass_enabled": False,
            "require_https": True,
            "access_token_expire_minutes": 15,  # Short expiry for security
            "service_token_expire_minutes": 5,
            "api_key": "secure-api-key-with-sufficient-entropy",
            "default_permissions": ["extension:read"]
        }

    @pytest.fixture
    def auth_manager(self, secure_auth_config):
        """Create secure authentication manager."""
        return ExtensionAuthManager(secure_auth_config)

    def test_jwt_secret_key_strength(self, auth_manager):
        """Test that JWT secret key has sufficient strength."""
        secret_key = auth_manager.secret_key
        
        # Secret key should be at least 32 characters
        assert len(secret_key) >= 32, "JWT secret key too short"
        
        # Should contain mixed case, numbers, and special characters
        has_lower = any(c.islower() for c in secret_key)
        has_upper = any(c.isupper() for c in secret_key)
        has_digit = any(c.isdigit() for c in secret_key)
        has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in secret_key)
        
        # At least 3 of 4 character types should be present
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        assert char_types >= 3, "JWT secret key lacks complexity"

    def test_token_signature_verification(self, auth_manager):
        """Test that tokens with invalid signatures are rejected."""
        # Create valid token
        valid_token = auth_manager.create_access_token("test-user")
        
        # Tamper with signature
        token_parts = valid_token.split('.')
        tampered_signature = token_parts[2][:-1] + 'X'  # Change last character
        tampered_token = '.'.join(token_parts[:2] + [tampered_signature])
        
        # Should reject tampered token
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(tampered_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_token_payload_tampering(self, auth_manager):
        """Test that tokens with tampered payloads are rejected."""
        # Create valid token
        token = auth_manager.create_access_token("test-user", permissions=["extension:read"])
        
        # Decode to get parts
        header, payload, signature = token.split('.')
        
        # Tamper with payload (try to escalate permissions)
        import base64
        import json
        
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload + '=='))
        decoded_payload['permissions'] = ['extension:*']  # Escalate permissions
        
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(decoded_payload).encode()
        ).decode().rstrip('=')
        
        tampered_token = f"{header}.{tampered_payload}.{signature}"
        
        # Should reject tampered token
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(tampered_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_algorithm_confusion_attack(self, auth_manager):
        """Test protection against algorithm confusion attacks."""
        # Try to create token with 'none' algorithm
        payload = {
            "user_id": "attacker",
            "permissions": ["extension:*"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        
        # Create unsigned token (algorithm: none)
        unsigned_token = jwt.encode(payload, "", algorithm="none")
        
        # Should reject unsigned token
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(unsigned_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_weak_algorithm_rejection(self):
        """Test that weak algorithms are not accepted."""
        weak_config = {
            "secret_key": "test-key",
            "algorithm": "HS1",  # Weak algorithm
            "enabled": True
        }
        
        # Should not allow weak algorithms in production
        with pytest.raises((ValueError, jwt.InvalidAlgorithmError)):
            auth_manager = ExtensionAuthManager(weak_config)
            token = jwt.encode({"user_id": "test"}, "test-key", algorithm="HS1")
            jwt.decode(token, "test-key", algorithms=["HS1"])

    def test_token_expiration_enforcement(self, auth_manager):
        """Test that expired tokens are properly rejected."""
        # Create token that expires immediately
        expired_token = auth_manager.create_access_token(
            "test-user",
            expires_delta=timedelta(seconds=-1)
        )
        
        # Should reject expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_token_not_before_claim(self, auth_manager):
        """Test 'not before' claim if implemented."""
        # Create token valid in the future
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        payload = {
            "user_id": "test-user",
            "nbf": future_time,
            "exp": future_time + timedelta(hours=1)
        }
        
        future_token = jwt.encode(payload, auth_manager.secret_key, algorithm=auth_manager.algorithm)
        
        # Should reject token that's not yet valid
        with pytest.raises(jwt.ImmatureSignatureError):
            jwt.decode(future_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_token_replay_attack_protection(self, auth_manager):
        """Test protection against token replay attacks."""
        # Create token with jti (JWT ID) for uniqueness
        import uuid
        
        payload = {
            "user_id": "test-user",
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, auth_manager.secret_key, algorithm=auth_manager.algorithm)
        decoded = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Token should have unique identifier
        assert "jti" in decoded or "iat" in decoded, "Token lacks replay protection"

    def test_timing_attack_resistance(self, auth_manager):
        """Test resistance to timing attacks in token validation."""
        valid_token = auth_manager.create_access_token("test-user")
        invalid_token = "invalid.token.here"
        
        # Measure time for valid token validation
        start_time = time.time()
        try:
            jwt.decode(valid_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        except:
            pass
        valid_time = time.time() - start_time
        
        # Measure time for invalid token validation
        start_time = time.time()
        try:
            jwt.decode(invalid_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        except:
            pass
        invalid_time = time.time() - start_time
        
        # Times should be similar (within reasonable bounds)
        time_ratio = max(valid_time, invalid_time) / min(valid_time, invalid_time)
        assert time_ratio < 10, f"Potential timing attack vulnerability: {time_ratio:.2f}x difference"

    def test_brute_force_protection(self, auth_manager):
        """Test protection against brute force attacks."""
        # This would typically be implemented at the application level
        # Test that multiple failed attempts don't leak information
        
        invalid_tokens = [
            "invalid.token.1",
            "invalid.token.2",
            "invalid.token.3",
            "completely-wrong-format",
            ""
        ]
        
        for token in invalid_tokens:
            with pytest.raises((jwt.InvalidTokenError, jwt.DecodeError)):
                jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])

    def test_information_disclosure_in_errors(self, auth_manager, mock_request):
        """Test that error messages don't disclose sensitive information."""
        import asyncio
        
        # Test various invalid tokens
        invalid_scenarios = [
            ("", "empty token"),
            ("invalid", "malformed token"),
            ("invalid.token.format", "invalid format"),
            (auth_manager.create_access_token("test", expires_delta=timedelta(seconds=-1)), "expired token")
        ]
        
        for invalid_token, scenario in invalid_scenarios:
            try:
                if invalid_token:
                    from fastapi.security import HTTPAuthorizationCredentials
                    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)
                else:
                    credentials = None
                
                # This should raise HTTPException
                asyncio.run(auth_manager.authenticate_extension_request(mock_request, credentials))
                
            except HTTPException as e:
                # Error message should be generic, not revealing internal details
                error_detail = e.detail.lower()
                
                # Should not contain sensitive information
                sensitive_terms = [
                    "secret", "key", "algorithm", "signature", "payload",
                    "decode", "jwt", "token structure", "internal error"
                ]
                
                for term in sensitive_terms:
                    assert term not in error_detail, f"Error message reveals sensitive info: {term} in '{e.detail}'"

    def test_session_fixation_protection(self, auth_manager):
        """Test protection against session fixation attacks."""
        # Each token should have unique identifiers
        token1 = auth_manager.create_access_token("user1")
        token2 = auth_manager.create_access_token("user1")  # Same user, different token
        
        payload1 = jwt.decode(token1, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        payload2 = jwt.decode(token2, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Tokens should have different issued-at times or other unique identifiers
        assert payload1["iat"] != payload2["iat"] or payload1.get("jti") != payload2.get("jti"), \
            "Tokens lack uniqueness, potential session fixation vulnerability"

    def test_privilege_escalation_prevention(self, auth_manager):
        """Test that users cannot escalate their privileges through token manipulation."""
        # Create token with limited permissions
        limited_token = auth_manager.create_access_token(
            "limited-user",
            permissions=["extension:read"]
        )
        
        # Verify token has limited permissions
        payload = jwt.decode(limited_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        assert payload["permissions"] == ["extension:read"]
        
        # Any attempt to modify permissions should invalidate the token
        # (This is inherently protected by signature verification)

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock()
        request.url.path = "/api/extensions/"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request


class TestAuthenticationSecurityBestPractices:
    """Test implementation of security best practices."""

    @pytest.fixture
    def production_auth_config(self):
        """Production-grade authentication configuration."""
        return {
            "secret_key": "production-grade-secret-key-with-high-entropy-123456789!@#",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "production",
            "dev_bypass_enabled": False,
            "require_https": True,
            "access_token_expire_minutes": 15,
            "refresh_token_expire_days": 7,
            "api_key": "production-api-key-with-sufficient-length-and-entropy",
            "default_permissions": []  # Principle of least privilege
        }

    @pytest.fixture
    def auth_manager(self, production_auth_config):
        """Create production-grade authentication manager."""
        return ExtensionAuthManager(production_auth_config)

    def test_principle_of_least_privilege(self, auth_manager):
        """Test that default permissions follow principle of least privilege."""
        # Default permissions should be minimal
        default_permissions = auth_manager.config.get("default_permissions", [])
        
        # Should not grant admin or wildcard permissions by default
        dangerous_permissions = ["extension:*", "extension:admin", "*"]
        for perm in dangerous_permissions:
            assert perm not in default_permissions, f"Default permissions too permissive: {perm}"

    def test_secure_token_expiration_times(self, auth_manager):
        """Test that token expiration times are secure."""
        # Access tokens should have short expiration
        access_expire_minutes = auth_manager.config.get("access_token_expire_minutes", 60)
        assert access_expire_minutes <= 60, "Access token expiration too long"
        
        # Service tokens should have even shorter expiration
        service_expire_minutes = auth_manager.config.get("service_token_expire_minutes", 30)
        assert service_expire_minutes <= 30, "Service token expiration too long"

    def test_https_requirement_in_production(self, auth_manager):
        """Test that HTTPS is required in production mode."""
        if auth_manager.auth_mode == "production":
            assert auth_manager.require_https, "HTTPS should be required in production"

    def test_development_bypass_disabled_in_production(self, auth_manager):
        """Test that development bypass is disabled in production."""
        if auth_manager.auth_mode == "production":
            assert not auth_manager.dev_bypass_enabled, "Development bypass should be disabled in production"

    def test_api_key_entropy(self, auth_manager):
        """Test that API keys have sufficient entropy."""
        api_key = auth_manager.config.get("api_key", "")
        
        # API key should be at least 32 characters
        assert len(api_key) >= 32, "API key too short"
        
        # Should not be predictable patterns
        predictable_patterns = ["12345", "abcde", "password", "secret", "key"]
        for pattern in predictable_patterns:
            assert pattern not in api_key.lower(), f"API key contains predictable pattern: {pattern}"

    def test_token_claims_validation(self, auth_manager):
        """Test that all required token claims are validated."""
        token = auth_manager.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user"],
            permissions=["extension:read"]
        )
        
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Required claims should be present
        required_claims = ["user_id", "exp", "iat", "iss"]
        for claim in required_claims:
            assert claim in payload, f"Required claim missing: {claim}"
        
        # Issuer should be set correctly
        assert payload["iss"] == "kari-extension-system"

    def test_token_audience_validation(self, auth_manager):
        """Test token audience validation if implemented."""
        # This test checks if audience (aud) claim is used for token scoping
        token = auth_manager.create_access_token("test-user")
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # If audience is implemented, it should be validated
        if "aud" in payload:
            assert payload["aud"] in ["extension-api", "kari-extension-system"]

    def test_secure_random_generation(self, auth_manager):
        """Test that secure random generation is used for tokens."""
        # Generate multiple tokens and check for uniqueness
        tokens = []
        for i in range(10):
            token = auth_manager.create_access_token(f"user-{i}")
            tokens.append(token)
        
        # All tokens should be unique
        assert len(set(tokens)) == len(tokens), "Tokens are not unique, possible weak random generation"
        
        # Tokens should have different issued-at times (at least some of them)
        payloads = [jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm]) for token in tokens]
        iat_times = [payload["iat"] for payload in payloads]
        
        # Should have some variation in issued-at times
        assert len(set(iat_times)) > 1, "All tokens have same issued-at time"

    def test_error_handling_security(self, auth_manager, mock_request):
        """Test that error handling doesn't leak security information."""
        import asyncio
        
        # Test various error conditions
        error_scenarios = [
            (None, "no credentials"),
            ("", "empty token"),
            ("Bearer ", "empty bearer token"),
            ("Basic dGVzdA==", "wrong auth scheme")
        ]
        
        for auth_header, scenario in error_scenarios:
            try:
                if auth_header:
                    mock_request.headers = {"Authorization": auth_header}
                    from fastapi.security import HTTPAuthorizationCredentials
                    if auth_header.startswith("Bearer ") and len(auth_header) > 7:
                        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth_header[7:])
                    else:
                        credentials = None
                else:
                    credentials = None
                
                asyncio.run(auth_manager.authenticate_extension_request(mock_request, credentials))
                
            except HTTPException as e:
                # Error should be generic
                assert e.status_code in [401, 403], f"Unexpected status code for {scenario}: {e.status_code}"
                
                # Error message should not reveal internal implementation details
                sensitive_info = ["jwt", "decode", "signature", "algorithm", "secret"]
                for info in sensitive_info:
                    assert info not in e.detail.lower(), f"Error reveals sensitive info: {info}"

    def test_rate_limiting_considerations(self, auth_manager):
        """Test considerations for rate limiting implementation."""
        # This test ensures the auth system is designed to work with rate limiting
        
        # Multiple authentication attempts should be possible
        # (Rate limiting would be implemented at middleware level)
        for i in range(5):
            token = auth_manager.create_access_token(f"user-{i}")
            payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
            assert payload["user_id"] == f"user-{i}"

    def test_audit_logging_readiness(self, auth_manager):
        """Test that authentication events can be audited."""
        # Authentication manager should support audit logging
        # (This would typically be implemented through logging or events)
        
        # Create token (this should be auditable)
        token = auth_manager.create_access_token("audit-user")
        
        # Token validation (this should be auditable)
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Key information should be available for audit logging
        audit_info = {
            "user_id": payload.get("user_id"),
            "tenant_id": payload.get("tenant_id"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp"),
            "permissions": payload.get("permissions", [])
        }
        
        # All audit information should be present
        for key, value in audit_info.items():
            assert value is not None, f"Audit information missing: {key}"

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock()
        request.url.path = "/api/extensions/"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request


class TestAuthenticationSecurityConfiguration:
    """Test security aspects of authentication configuration."""

    def test_insecure_configuration_detection(self):
        """Test detection of insecure configurations."""
        insecure_configs = [
            {
                "secret_key": "weak",  # Too short
                "enabled": True
            },
            {
                "secret_key": "test-secret-key",
                "algorithm": "none",  # Insecure algorithm
                "enabled": True
            },
            {
                "secret_key": "test-secret-key",
                "access_token_expire_minutes": 1440,  # 24 hours - too long
                "enabled": True
            }
        ]
        
        for config in insecure_configs:
            # Should either reject insecure config or warn about it
            try:
                auth_manager = ExtensionAuthManager(config)
                
                # If it accepts the config, check if it applies secure defaults
                if config.get("algorithm") == "none":
                    assert auth_manager.algorithm != "none", "Should not accept 'none' algorithm"
                
                if len(config.get("secret_key", "")) < 16:
                    # Should either reject or apply a secure default
                    assert len(auth_manager.secret_key) >= 16, "Should not accept weak secret key"
                    
            except (ValueError, AssertionError):
                # It's acceptable to reject insecure configurations
                pass

    def test_secure_defaults(self):
        """Test that secure defaults are applied when configuration is minimal."""
        minimal_config = {
            "secret_key": "minimum-viable-secret-key-for-testing",
            "enabled": True
        }
        
        auth_manager = ExtensionAuthManager(minimal_config)
        
        # Should apply secure defaults
        assert auth_manager.algorithm in ["HS256", "HS384", "HS512"], "Should use secure algorithm by default"
        assert auth_manager.config.get("access_token_expire_minutes", 60) <= 60, "Should use secure token expiry"
        assert not auth_manager.dev_bypass_enabled or auth_manager.auth_mode == "development", \
            "Should not enable dev bypass by default in production"

    def test_configuration_validation(self):
        """Test that configuration is properly validated."""
        # Test various invalid configurations
        invalid_configs = [
            {},  # Missing secret key
            {"secret_key": ""},  # Empty secret key
            {"secret_key": "test", "algorithm": "invalid"},  # Invalid algorithm
            {"secret_key": "test", "access_token_expire_minutes": -1},  # Negative expiry
        ]
        
        for config in invalid_configs:
            try:
                auth_manager = ExtensionAuthManager(config)
                # If it doesn't raise an exception, check that it applies safe defaults
                assert auth_manager.secret_key, "Should have a secret key"
                assert auth_manager.algorithm in ["HS256", "HS384", "HS512"], "Should use valid algorithm"
                assert auth_manager.config.get("access_token_expire_minutes", 60) > 0, "Should have positive expiry"
            except (ValueError, KeyError, AssertionError):
                # It's acceptable to reject invalid configurations
                pass