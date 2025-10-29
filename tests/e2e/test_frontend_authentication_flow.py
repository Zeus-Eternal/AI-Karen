"""
End-to-end tests for frontend authentication flow.
Tests the complete authentication flow from frontend to backend.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from server.security import ExtensionAuthManager, require_extension_read


class TestFrontendAuthenticationFlow:
    """End-to-end tests for frontend authentication flow."""

    @pytest.fixture
    def auth_config(self):
        """Authentication configuration for E2E testing."""
        return {
            "secret_key": "e2e-test-secret-key",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "production",
            "dev_bypass_enabled": False,
            "require_https": False,
            "access_token_expire_minutes": 60,
            "refresh_token_expire_days": 7,
            "api_key": "e2e-test-api-key",
            "default_permissions": ["extension:read", "extension:write"]
        }

    @pytest.fixture
    def auth_manager(self, auth_config):
        """Create authentication manager for E2E testing."""
        return ExtensionAuthManager(auth_config)

    @pytest.fixture
    def full_test_app(self, auth_manager):
        """Create full test application simulating real backend."""
        app = FastAPI(title="Extension API E2E Test")

        # Add CORS middleware to simulate real deployment
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mock user database
        users_db = {
            "testuser": {
                "user_id": "testuser",
                "tenant_id": "test-tenant",
                "password_hash": "hashed_password",
                "roles": ["user"],
                "permissions": ["extension:read", "extension:write"]
            },
            "adminuser": {
                "user_id": "adminuser",
                "tenant_id": "admin-tenant",
                "password_hash": "admin_hashed_password",
                "roles": ["admin"],
                "permissions": ["extension:*"]
            }
        }

        # Mock extension data
        extensions_db = {
            "test-extension": {
                "name": "test-extension",
                "version": "1.0.0",
                "display_name": "Test Extension",
                "description": "A test extension",
                "status": "active",
                "capabilities": ["read", "write"]
            },
            "admin-extension": {
                "name": "admin-extension",
                "version": "2.0.0",
                "display_name": "Admin Extension",
                "description": "An admin-only extension",
                "status": "active",
                "capabilities": ["admin"]
            }
        }

        @app.post("/api/auth/login")
        async def login(credentials: dict):
            """Simulate login endpoint."""
            username = credentials.get("username")
            password = credentials.get("password")

            if username not in users_db or password != "correct_password":
                raise HTTPException(status_code=401, detail="Invalid credentials")

            user = users_db[username]
            
            # Generate tokens
            access_token = auth_manager.create_access_token(
                user_id=user["user_id"],
                tenant_id=user["tenant_id"],
                roles=user["roles"],
                permissions=user["permissions"]
            )

            refresh_token = auth_manager.create_access_token(
                user_id=user["user_id"],
                tenant_id=user["tenant_id"],
                roles=user["roles"],
                permissions=user["permissions"],
                expires_delta=timedelta(days=7)
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": user["user_id"],
                    "tenant_id": user["tenant_id"],
                    "roles": user["roles"]
                }
            }

        @app.post("/api/auth/refresh")
        async def refresh_token(refresh_data: dict):
            """Simulate token refresh endpoint."""
            refresh_token = refresh_data.get("refresh_token")
            
            if not refresh_token:
                raise HTTPException(status_code=400, detail="Refresh token required")

            try:
                # Validate refresh token
                import jwt
                payload = jwt.decode(refresh_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
                
                user_id = payload.get("user_id")
                if not user_id or user_id not in users_db:
                    raise HTTPException(status_code=401, detail="Invalid refresh token")

                user = users_db[user_id]
                
                # Generate new access token
                new_access_token = auth_manager.create_access_token(
                    user_id=user["user_id"],
                    tenant_id=user["tenant_id"],
                    roles=user["roles"],
                    permissions=user["permissions"]
                )

                return {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "expires_in": 3600
                }

            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Refresh token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

        @app.get("/api/extensions/")
        async def list_extensions(
            user_context: dict = Depends(require_extension_read)
        ):
            """List extensions with authentication."""
            # Filter extensions based on user permissions
            user_permissions = user_context.get("permissions", [])
            user_roles = user_context.get("roles", [])
            
            filtered_extensions = {}
            for name, ext in extensions_db.items():
                # Admin users see all extensions
                if "admin" in user_roles or "extension:*" in user_permissions:
                    filtered_extensions[name] = ext
                # Regular users see non-admin extensions
                elif "admin" not in ext.get("capabilities", []):
                    filtered_extensions[name] = ext

            return {
                "extensions": filtered_extensions,
                "total": len(filtered_extensions),
                "user_context": {
                    "user_id": user_context["user_id"],
                    "tenant_id": user_context["tenant_id"],
                    "roles": user_context["roles"]
                }
            }

        @app.post("/api/extensions/background-tasks/")
        async def register_background_task(
            task_data: dict,
            user_context: dict = Depends(require_extension_read)
        ):
            """Register background task."""
            return {
                "task_id": f"task_{int(time.time())}",
                "message": "Background task registered successfully",
                "task_data": task_data,
                "registered_by": user_context["user_id"],
                "tenant_id": user_context["tenant_id"]
            }

        @app.get("/api/extensions/health")
        async def extension_health():
            """Public health endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "extension_manager": "active",
                    "authentication": "active"
                }
            }

        # Override global auth manager for testing
        with patch('server.security.get_extension_auth_manager', return_value=auth_manager):
            yield app

    @pytest.fixture
    def client(self, full_test_app):
        """Create test client for E2E testing."""
        return TestClient(full_test_app)

    def test_complete_authentication_flow(self, client):
        """Test complete authentication flow from login to API access."""
        # Step 1: Login
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        assert login_response.status_code == 200
        login_data = login_response.json()
        
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert login_data["user"]["user_id"] == "testuser"

        access_token = login_data["access_token"]

        # Step 2: Use access token to access protected endpoint
        extensions_response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert extensions_response.status_code == 200
        extensions_data = extensions_response.json()
        
        assert "extensions" in extensions_data
        assert extensions_data["user_context"]["user_id"] == "testuser"
        assert extensions_data["user_context"]["tenant_id"] == "test-tenant"

        # Step 3: Register background task
        task_response = client.post(
            "/api/extensions/background-tasks/",
            json={"name": "test-task", "schedule": "0 */6 * * *"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert task_response.status_code == 200
        task_data = task_response.json()
        assert "task_id" in task_data
        assert task_data["registered_by"] == "testuser"

    def test_token_refresh_flow(self, client):
        """Test token refresh flow."""
        # Step 1: Login to get tokens
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Step 2: Use refresh token to get new access token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"

        new_access_token = refresh_data["access_token"]

        # Step 3: Use new access token
        extensions_response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        assert extensions_response.status_code == 200

    def test_expired_token_handling(self, client, auth_manager):
        """Test handling of expired tokens."""
        # Create expired token
        expired_token = auth_manager.create_access_token(
            user_id="testuser",
            expires_delta=timedelta(seconds=-60)  # Already expired
        )

        # Try to use expired token
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 403
        assert "expired" in response.json()["detail"].lower()

    def test_invalid_credentials_login(self, client):
        """Test login with invalid credentials."""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrong_password"
        })

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_missing_token_access(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/extensions/")
        
        assert response.status_code == 403
        assert "authentication required" in response.json()["detail"].lower()

    def test_admin_user_access(self, client):
        """Test admin user access to all extensions."""
        # Login as admin
        login_response = client.post("/api/auth/login", json={
            "username": "adminuser",
            "password": "correct_password"
        })

        admin_token = login_response.json()["access_token"]

        # Access extensions as admin
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        
        # Admin should see all extensions including admin-only ones
        assert "test-extension" in data["extensions"]
        assert "admin-extension" in data["extensions"]
        assert data["user_context"]["user_id"] == "adminuser"

    def test_regular_user_filtered_access(self, client):
        """Test regular user sees only appropriate extensions."""
        # Login as regular user
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        user_token = login_response.json()["access_token"]

        # Access extensions as regular user
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        
        # Regular user should not see admin-only extensions
        assert "test-extension" in data["extensions"]
        assert "admin-extension" not in data["extensions"]

    def test_tenant_isolation(self, client):
        """Test tenant isolation in responses."""
        # Login as testuser (test-tenant)
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        user_token = login_response.json()["access_token"]

        # Check tenant context in response
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_context"]["tenant_id"] == "test-tenant"

        # Login as adminuser (admin-tenant)
        admin_login_response = client.post("/api/auth/login", json={
            "username": "adminuser",
            "password": "correct_password"
        })

        admin_token = admin_login_response.json()["access_token"]

        # Check different tenant context
        admin_response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert admin_response.status_code == 200
        admin_data = admin_response.json()
        assert admin_data["user_context"]["tenant_id"] == "admin-tenant"

    def test_public_endpoint_access(self, client):
        """Test access to public endpoints without authentication."""
        response = client.get("/api/extensions/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_cors_headers_present(self, client):
        """Test CORS headers are present for frontend integration."""
        # Simulate preflight request
        response = client.options(
            "/api/extensions/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )

        # Should allow CORS
        assert response.status_code in [200, 204]

    def test_invalid_refresh_token(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-refresh-token"
        })

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_missing_refresh_token(self, client):
        """Test refresh without providing token."""
        response = client.post("/api/auth/refresh", json={})

        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    def test_concurrent_requests_with_same_token(self, client):
        """Test concurrent requests using the same token."""
        # Login to get token
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        token = login_response.json()["access_token"]

        # Make concurrent requests
        import threading
        results = []

        def make_request():
            response = client.get(
                "/api/extensions/",
                headers={"Authorization": f"Bearer {token}"}
            )
            results.append(response.status_code)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)

    def test_token_reuse_after_refresh(self, client):
        """Test that old token still works after refresh (until expiry)."""
        # Login to get tokens
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "correct_password"
        })

        login_data = login_response.json()
        old_access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Refresh to get new token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })

        new_access_token = refresh_response.json()["access_token"]

        # Both tokens should work (old one until it expires)
        old_response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert old_response.status_code == 200

        new_response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert new_response.status_code == 200


class TestFrontendAuthenticationErrorScenarios:
    """Test error scenarios in frontend authentication flow."""

    @pytest.fixture
    def error_test_app(self):
        """Create test app that simulates various error conditions."""
        app = FastAPI()

        @app.post("/api/auth/login")
        async def failing_login(credentials: dict):
            """Simulate login failures."""
            username = credentials.get("username")
            
            if username == "network_error":
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
            elif username == "server_error":
                raise HTTPException(status_code=500, detail="Internal server error")
            elif username == "rate_limited":
                raise HTTPException(status_code=429, detail="Too many requests")
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")

        @app.get("/api/extensions/")
        async def failing_extensions():
            """Simulate extension API failures."""
            raise HTTPException(status_code=503, detail="Extension service unavailable")

        return app

    @pytest.fixture
    def error_client(self, error_test_app):
        """Create client for error testing."""
        return TestClient(error_test_app)

    def test_network_error_during_login(self, error_client):
        """Test handling of network errors during login."""
        response = error_client.post("/api/auth/login", json={
            "username": "network_error",
            "password": "password"
        })

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    def test_server_error_during_login(self, error_client):
        """Test handling of server errors during login."""
        response = error_client.post("/api/auth/login", json={
            "username": "server_error",
            "password": "password"
        })

        assert response.status_code == 500

    def test_rate_limiting_during_login(self, error_client):
        """Test handling of rate limiting during login."""
        response = error_client.post("/api/auth/login", json={
            "username": "rate_limited",
            "password": "password"
        })

        assert response.status_code == 429
        assert "too many requests" in response.json()["detail"].lower()

    def test_extension_service_unavailable(self, error_client):
        """Test handling when extension service is unavailable."""
        response = error_client.get("/api/extensions/")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()


class TestFrontendAuthenticationPerformance:
    """Test performance aspects of frontend authentication."""

    @pytest.fixture
    def perf_test_app(self, auth_manager):
        """Create app for performance testing."""
        app = FastAPI()

        @app.get("/api/extensions/")
        async def list_extensions(
            user_context: dict = Depends(require_extension_read)
        ):
            return {"extensions": {}, "user_context": user_context}

        with patch('server.security.get_extension_auth_manager', return_value=auth_manager):
            yield app

    @pytest.fixture
    def perf_client(self, perf_test_app):
        """Create client for performance testing."""
        return TestClient(perf_test_app)

    def test_authentication_performance(self, perf_client, auth_manager):
        """Test authentication performance under load."""
        token = auth_manager.create_access_token(
            user_id="perf-user",
            permissions=["extension:read"]
        )

        import time
        
        # Measure authentication time
        start_time = time.time()
        
        for _ in range(100):
            response = perf_client.get(
                "/api/extensions/",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100

        # Authentication should be fast (less than 10ms per request on average)
        assert avg_time < 0.01, f"Authentication too slow: {avg_time:.4f}s per request"

    def test_token_validation_caching(self, perf_client, auth_manager):
        """Test that token validation is efficient for repeated requests."""
        token = auth_manager.create_access_token(
            user_id="cache-user",
            permissions=["extension:read"]
        )

        # First request (cold)
        start_time = time.time()
        response1 = perf_client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {token}"}
        )
        first_request_time = time.time() - start_time

        # Subsequent requests (should be faster if caching is working)
        times = []
        for _ in range(10):
            start_time = time.time()
            response = perf_client.get(
                "/api/extensions/",
                headers={"Authorization": f"Bearer {token}"}
            )
            times.append(time.time() - start_time)
            assert response.status_code == 200

        avg_subsequent_time = sum(times) / len(times)

        # Subsequent requests should be at least as fast as the first
        # (This test mainly ensures no performance regression)
        assert avg_subsequent_time <= first_request_time * 1.5