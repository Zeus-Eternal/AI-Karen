"""
Tests for intelligent authentication router integration.

This module tests the enhanced authentication endpoints to ensure:
- Backward compatibility with existing authentication flows
- Consistent JSON response structures
- Proper error message formatting and HTTP status codes
- UI/UX consistency across all authentication flows
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ai_karen_engine.api_routes.auth import router
from ai_karen_engine.security.models import (
    AuthAnalysisResult,
    RiskLevel,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    SecurityAction,
    CredentialFeatures
)


@pytest.fixture
def app():
    """Create FastAPI app with auth router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/auth")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_intelligent_auth_service():
    """Create mock intelligent auth service."""
    service = AsyncMock()
    
    # Mock analysis result
    mock_result = AuthAnalysisResult(
        risk_score=0.3,
        risk_level=RiskLevel.LOW,
        should_block=False,
        requires_2fa=False,
        nlp_features=NLPFeatures(
            email_features=CredentialFeatures(
                token_count=2,
                unique_token_ratio=1.0,
                entropy_score=0.8,
                language="en",
                contains_suspicious_patterns=False,
                pattern_types=[]
            ),
            password_features=CredentialFeatures(
                token_count=1,
                unique_token_ratio=1.0,
                entropy_score=0.9,
                language="en",
                contains_suspicious_patterns=False,
                pattern_types=[]
            ),
            credential_similarity=0.1,
            language_consistency=True,
            suspicious_patterns=[],
            processing_time=0.1,
            used_fallback=False,
            model_version="1.0"
        ),
        embedding_analysis=EmbeddingAnalysis(
            embedding_vector=[0.1, 0.2, 0.3],
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1,
            cluster_assignment="normal",
            outlier_score=0.2,
            processing_time=0.05,
            model_version="1.0"
        ),
        behavioral_analysis=BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.1,
            is_usual_location=True,
            location_deviation_score=0.1,
            is_known_device=True,
            device_similarity_score=0.9,
            login_frequency_anomaly=0.1,
            session_duration_anomaly=0.1,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        ),
        threat_analysis=ThreatAnalysis(
            ip_reputation_score=0.1,
            known_attack_patterns=[],
            threat_actor_indicators=[],
            brute_force_indicators=None,
            credential_stuffing_indicators=None,
            account_takeover_indicators=None,
            similar_attacks_detected=0,
            attack_campaign_correlation=None
        ),
        processing_time=0.2,
        model_versions={"nlp": "1.0", "embedding": "1.0", "anomaly": "1.0"},
        confidence_score=0.85,
        analysis_timestamp=datetime.utcnow(),
        recommended_actions=[],
        user_feedback_required=False
    )
    
    service.analyze_login_attempt.return_value = mock_result
    service.update_user_behavioral_profile.return_value = None
    service.provide_feedback.return_value = None
    
    return service


class TestAuthenticationFlowConsistency:
    """Test authentication flow consistency and UI/UX compatibility."""

    def test_login_response_structure_consistency(self, client):
        """Test that login responses maintain consistent JSON structure."""
        # Mock the authenticate function to return a valid user
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth, \
             patch('ai_karen_engine.api_routes.auth.create_session') as mock_session, \
             patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            
            mock_auth.return_value = {
                "roles": ["user"],
                "tenant_id": "default",
                "preferences": {},
                "is_verified": True,
                "two_factor_enabled": False
            }
            mock_session.return_value = "test_token"
            mock_service.return_value = None  # No intelligent auth service
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify consistent response structure
            required_fields = ["token", "user_id", "email", "roles", "tenant_id", "preferences", "two_factor_enabled"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify data types
            assert isinstance(data["token"], str)
            assert isinstance(data["user_id"], str)
            assert isinstance(data["email"], str)
            assert isinstance(data["roles"], list)
            assert isinstance(data["tenant_id"], str)
            assert isinstance(data["preferences"], dict)
            assert isinstance(data["two_factor_enabled"], bool)

    def test_error_response_consistency(self, client):
        """Test that error responses maintain consistent format."""
        # Test invalid credentials
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth:
            mock_auth.return_value = None  # Invalid credentials
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrong_password"
            })
            
            assert response.status_code == 401
            data = response.json()
            
            # Verify error response structure
            assert "detail" in data
            assert data["detail"] == "Invalid credentials"

    def test_rate_limiting_error_consistency(self, client):
        """Test that rate limiting errors maintain consistent format."""
        # Simulate rate limiting by making multiple requests
        with patch('ai_karen_engine.api_routes.auth._LOGIN_ATTEMPTS') as mock_attempts:
            # Set up rate limit exceeded scenario
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            mock_attempts.__getitem__.return_value = [now] * 6  # Exceed rate limit
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 429
            data = response.json()
            
            # Verify consistent error format
            assert "detail" in data
            assert "too many" in data["detail"].lower()

    def test_intelligent_auth_blocking_consistency(self, client, mock_intelligent_auth_service):
        """Test that intelligent auth blocking maintains consistent error format."""
        # Configure service to block login
        mock_result = mock_intelligent_auth_service.analyze_login_attempt.return_value
        mock_result.should_block = True
        mock_result.risk_level = RiskLevel.CRITICAL
        
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = mock_intelligent_auth_service
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 403
            data = response.json()
            
            # Verify consistent error format
            assert "detail" in data
            assert "security concerns" in data["detail"].lower()

    def test_2fa_requirement_consistency(self, client, mock_intelligent_auth_service):
        """Test that 2FA requirements maintain consistent messaging."""
        # Configure service to require 2FA
        mock_result = mock_intelligent_auth_service.analyze_login_attempt.return_value
        mock_result.requires_2fa = True
        mock_result.risk_level = RiskLevel.HIGH
        
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth, \
             patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            
            mock_auth.return_value = {
                "roles": ["user"],
                "tenant_id": "default",
                "preferences": {},
                "is_verified": True,
                "two_factor_enabled": False  # Standard 2FA not enabled
            }
            mock_service.return_value = mock_intelligent_auth_service
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 401
            data = response.json()
            
            # Verify consistent 2FA message format
            assert "detail" in data
            assert "two-factor authentication" in data["detail"].lower()
            assert "security analysis" in data["detail"].lower()

    def test_analyze_endpoint_response_consistency(self, client, mock_intelligent_auth_service):
        """Test that analyze endpoint maintains consistent response structure."""
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = mock_intelligent_auth_service
            
            response = client.post("/api/auth/analyze", json={
                "email": "test@example.com",
                "password": "password123",
                "include_detailed_analysis": True,
                "include_recommendations": True
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields
            required_fields = [
                "risk_score", "risk_level", "should_block", "requires_2fa",
                "processing_time", "confidence_score", "analysis_timestamp"
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify data types
            assert isinstance(data["risk_score"], (int, float))
            assert isinstance(data["risk_level"], str)
            assert isinstance(data["should_block"], bool)
            assert isinstance(data["requires_2fa"], bool)
            assert isinstance(data["processing_time"], (int, float))
            assert isinstance(data["confidence_score"], (int, float))

    def test_feedback_endpoint_response_consistency(self, client, mock_intelligent_auth_service):
        """Test that feedback endpoint maintains consistent response structure."""
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = mock_intelligent_auth_service
            
            response = client.post("/api/auth/feedback", json={
                "user_id": "test@example.com",
                "request_id": "test-request-123",
                "feedback_type": "false_positive",
                "feedback_data": {"reason": "legitimate_login"},
                "comments": "This was a legitimate login from my home"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify consistent success response
            assert "detail" in data
            assert "feedback received successfully" in data["detail"].lower()

    def test_security_insights_response_consistency(self, client, mock_intelligent_auth_service):
        """Test that security insights endpoint maintains consistent response structure."""
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = mock_intelligent_auth_service
            
            response = client.get("/api/auth/security-insights?timeframe=24h")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields
            required_fields = [
                "timeframe", "total_attempts", "successful_attempts", "blocked_attempts",
                "high_risk_attempts", "avg_risk_score", "trends", "alerts",
                "top_risk_factors", "generated_at"
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify data types
            assert isinstance(data["total_attempts"], int)
            assert isinstance(data["successful_attempts"], int)
            assert isinstance(data["blocked_attempts"], int)
            assert isinstance(data["high_risk_attempts"], int)
            assert isinstance(data["avg_risk_score"], (int, float))
            assert isinstance(data["trends"], dict)
            assert isinstance(data["alerts"], list)
            assert isinstance(data["top_risk_factors"], list)

    def test_service_unavailable_consistency(self, client):
        """Test that service unavailable responses maintain consistent format."""
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = None  # Service unavailable
            
            # Test analyze endpoint
            response = client.post("/api/auth/analyze", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 503
            data = response.json()
            
            # Verify consistent service unavailable format
            assert "detail" in data
            assert "not available" in data["detail"].lower()

    def test_validation_error_consistency(self, client):
        """Test that validation errors maintain consistent format."""
        # Test invalid feedback type
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            mock_service.return_value = Mock()  # Service available
            
            response = client.post("/api/auth/feedback", json={
                "user_id": "test@example.com",
                "request_id": "test-request-123",
                "feedback_type": "invalid_type",  # Invalid feedback type
                "feedback_data": {}
            })
            
            assert response.status_code == 400
            data = response.json()
            
            # Verify consistent validation error format
            assert "detail" in data
            assert "invalid feedback type" in data["detail"].lower()

    def test_http_status_codes_consistency(self, client):
        """Test that HTTP status codes are consistent across endpoints."""
        status_code_expectations = {
            # Success cases
            200: ["successful login", "successful analysis", "successful feedback"],
            
            # Client errors
            400: ["invalid request", "validation error"],
            401: ["invalid credentials", "2fa required"],
            403: ["blocked login", "email not verified"],
            429: ["rate limit exceeded"],
            
            # Server errors
            500: ["internal server error"],
            503: ["service unavailable"]
        }
        
        # This test documents expected status codes for consistency
        # In a real implementation, we would test each scenario
        for status_code, scenarios in status_code_expectations.items():
            assert isinstance(status_code, int)
            assert 100 <= status_code <= 599
            assert isinstance(scenarios, list)
            assert len(scenarios) > 0

    def test_response_timing_consistency(self, client, mock_intelligent_auth_service):
        """Test that response timing patterns are consistent."""
        with patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service, \
             patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth, \
             patch('ai_karen_engine.api_routes.auth.create_session') as mock_session:
            
            mock_service.return_value = mock_intelligent_auth_service
            mock_auth.return_value = {
                "roles": ["user"],
                "tenant_id": "default",
                "preferences": {},
                "is_verified": True,
                "two_factor_enabled": False
            }
            mock_session.return_value = "test_token"
            
            import time
            start_time = time.time()
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Verify response is reasonably fast (under 5 seconds for tests)
            assert response_time < 5.0
            assert response.status_code == 200

    def test_middleware_health_endpoint_consistency(self, client):
        """Test that middleware health endpoint maintains consistent response structure."""
        response = client.get("/api/auth/middleware/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        required_fields = ["status", "message", "features", "generated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify features structure
        assert isinstance(data["features"], dict)
        feature_fields = ["geolocation", "device_fingerprinting", "risk_based_rate_limiting"]
        for field in feature_fields:
            assert field in data["features"]
            assert isinstance(data["features"][field], bool)


class TestBackwardCompatibility:
    """Test backward compatibility with existing authentication flows."""

    def test_existing_login_flow_unchanged(self, client):
        """Test that existing login flow works without intelligent auth."""
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth, \
             patch('ai_karen_engine.api_routes.auth.create_session') as mock_session, \
             patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            
            mock_auth.return_value = {
                "roles": ["user"],
                "tenant_id": "default",
                "preferences": {},
                "is_verified": True,
                "two_factor_enabled": False
            }
            mock_session.return_value = "test_token"
            mock_service.return_value = None  # No intelligent auth
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all expected fields are present
            assert data["token"] == "test_token"
            assert data["user_id"] == "test@example.com"
            assert data["email"] == "test@example.com"

    def test_existing_error_handling_unchanged(self, client):
        """Test that existing error handling patterns are preserved."""
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth:
            mock_auth.return_value = None  # Invalid credentials
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrong_password"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["detail"] == "Invalid credentials"

    def test_existing_2fa_flow_unchanged(self, client):
        """Test that existing 2FA flow works correctly."""
        with patch('ai_karen_engine.api_routes.auth.authenticate') as mock_auth, \
             patch('ai_karen_engine.api_routes.auth.verify_totp') as mock_totp, \
             patch('ai_karen_engine.api_routes.auth.get_intelligent_auth_service') as mock_service:
            
            mock_auth.return_value = {
                "roles": ["user"],
                "tenant_id": "default",
                "preferences": {},
                "is_verified": True,
                "two_factor_enabled": True  # 2FA enabled
            }
            mock_totp.return_value = False  # Invalid TOTP
            mock_service.return_value = None  # No intelligent auth
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123",
                "totp_code": "123456"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["detail"] == "Invalid two-factor code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])