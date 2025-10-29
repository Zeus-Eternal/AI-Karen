"""
Integration tests for extension API authentication.
Tests the full authentication flow with real FastAPI endpoints.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from server.security import (
    ExtensionAuthManager,
    require_extension_read,
    require_extension_write,
    require_extension_admin,
    require_background_tasks
)


class TestExtensionAPIAuthentication:
    """Integration tests for extension API authentication."""

    @pytest.fixture
    def auth_config(self):
        """Authentication configuration for testing."""
        return {
            "secret_key": "test-integration-secret",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "production",
            "dev_bypass_enabled": False,
            "api_key": "test-integration-api-key",
            "access_token_expire_minutes": 60,
            "default_permissions": ["extension:read", "extension:write"]
        }

    @pytest.fixture
    def auth_manager(self, auth_config):
        """Create authentication manager for integration testing."""
        return ExtensionAuthManager(auth_config)

    @pytest.fixture
    def test_app(self, auth_manager):
        """Create test FastAPI application with authentication."""
        app = FastAPI()

        # Mock extension manager for testing
        mock_extension_manager = Mock()
        mock_extension_manager.registry.get_all_extensions.return_value = {
            "test-extension": {
                "name": "test-extension",
                "version": "1.0.0",
                "status": "active"
            }
        }

        @app.get("/api/extensions/")
        async def list_extensions(
            user_context: dict = Depends(require_extension_read)
        ):
            """Test endpoint requiring read permission."""
            return {
                "extensions": mock_extension_manager.registry.get_all_extensions(),
                "user_context": {
                    "user_id": user_context["user_id"],
                    "tenant_id": user_context["tenant_id"]
                }
            }

        @app.post("/api/extensions/")
        async def create_extension(
            extension_data: dict,
            user_context: dict = Depends(require_extension_write)
        ):
            """Test endpoint requiring write permission."""
            return {
                "message": "Extension created",
                "extension_data": extension_data,
                "created_by": user_context["user_id"]
            }

        @app.delete("/api/extensions/{extension_name}")
        async def delete_extension(
            extension_name: str,
            user_context: dict = Depends(require_extension_admin)
        ):
            """Test endpoint requiring admin permission."""
            return {
                "message": f"Extension {extension_name} deleted",
                "deleted_by": user_context["user_id"]
            }

        @app.post("/api/extensions/background-tasks/")
        async def register_background_task(
            task_data: dict,
            user_context: dict = Depends(require_background_tasks)
        ):
            """Test endpoint requiring background tasks permission."""
            return {
                "task_id": f"task_{user_context['user_id']}_{task_data.get('name')}",
                "message": "Background task registered",
                "registered_by": user_context["user_id"]
            }

        @app.get("/api/extensions/health")
        async def extension_health():
            """Public health endpoint (no authentication required)."""
            return {"status": "healthy"}

        # Override the global auth manager for testing
        with patch('server.security.get_extension_auth_manager', return_value=auth_manager):
            yield app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_list_extensions_with_valid_token(self, client, auth_manager):
        """Test listing extensions with valid authentication token."""
        # Create valid token
        token = auth_manager.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user"],
            permissions=["extension:read"]
        )

        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "extensions" in data
        assert data["user_context"]["user_id"] == "test-user"
        assert data["user_context"]["tenant_id"] == "test-tenant"

    def test_list_extensions_without_token(self, client):
        """Test listing extensions without authentication token."""
        response = client.get("/api/extensions/")
        
        assert response.status_code == 403
        assert "authentication required" in response.json()["detail"].lower()

    def test_list_extensions_with_expired_token(self, client, auth_manager):
        """Test listing extensions with expired token."""
        # Create expired token
        token = auth_manager.create_access_token(
            user_id="test-user",
            expires_delta=timedelta(seconds=-60)  # Already expired
        )

        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "expired" in response.json()["detail"].lower()

    def test_list_extensions_with_invalid_token(self, client):
        """Test listing extensions with invalid token."""
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 403
        assert "invalid" in response.json()["detail"].lower()

    def test_create_extension_with_write_permission(self, client, auth_manager):
        """Test creating extension with write permission."""
        token = auth_manager.create_access_token(
            user_id="test-user",
            permissions=["extension:write"]
        )

        extension_data = {
            "name": "new-extension",
            "version": "1.0.0"
        }

        response = client.post(
            "/api/extensions/",
            json=extension_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Extension created"
        assert data["created_by"] == "test-user"

    def test_create_extension_without_write_permission(self, client, auth_manager):
        """Test creating extension without write permission."""
        token = auth_manager.create_access_token(
            user_id="test-user",
            permissions=["extension:read"]  # Only read permission
        )

        extension_data = {
            "name": "new-extension",
            "version": "1.0.0"
        }

        response = client.post(
            "/api/extensions/",
            json=extension_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()

    def test_delete_extension_with_admin_permission(self, client, auth_manager):
        """Test deleting extension with admin permission."""
        token = auth_manager.create_access_token(
            user_id="admin-user",
            roles=["admin"],
            permissions=["extension:admin"]
        )

        response = client.delete(
            "/api/extensions/test-extension",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"]
        assert data["deleted_by"] == "admin-user"

    def test_delete_extension_without_admin_permission(self, client, auth_manager):
        """Test deleting extension without admin permission."""
        token = auth_manager.create_access_token(
            user_id="regular-user",
            permissions=["extension:read", "extension:write"]
        )

        response = client.delete(
            "/api/extensions/test-extension",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()

    def test_register_background_task_with_permission(self, client, auth_manager):
        """Test registering background task with proper permission."""
        token = auth_manager.create_access_token(
            user_id="task-user",
            permissions=["extension:background_tasks"]
        )

        task_data = {
            "name": "test-task",
            "schedule": "0 */6 * * *"
        }

        response = client.post(
            "/api/extensions/background-tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["registered_by"] == "task-user"

    def test_register_background_task_without_permission(self, client, auth_manager):
        """Test registering background task without permission."""
        token = auth_manager.create_access_token(
            user_id="regular-user",
            permissions=["extension:read"]
        )

        task_data = {
            "name": "test-task",
            "schedule": "0 */6 * * *"
        }

        response = client.post(
            "/api/extensions/background-tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    def test_api_key_authentication(self, client):
        """Test authentication using API key."""
        response = client.get(
            "/api/extensions/",
            headers={"X-EXTENSION-API-KEY": "test-integration-api-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "extensions" in data

    def test_invalid_api_key_authentication(self, client):
        """Test authentication with invalid API key."""
        response = client.get(
            "/api/extensions/",
            headers={"X-EXTENSION-API-KEY": "invalid-api-key"}
        )

        assert response.status_code == 403

    def test_service_token_authentication(self, client, auth_manager):
        """Test authentication with service token."""
        service_token = auth_manager.create_service_token(
            service_name="test-service",
            permissions=["extension:background_tasks"]
        )

        task_data = {
            "name": "service-task",
            "service": "test-service"
        }

        response = client.post(
            "/api/extensions/background-tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {service_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "service:test-service" in data["registered_by"]

    def test_background_task_token_authentication(self, client, auth_manager):
        """Test authentication with background task token."""
        task_token = auth_manager.create_background_task_token(
            task_name="test-task",
            user_id="task-owner",
            service_name="task-service"
        )

        task_data = {
            "name": "background-task",
            "type": "scheduled"
        }

        response = client.post(
            "/api/extensions/background-tasks/",
            json=task_data,
            headers={"Authorization": f"Bearer {task_token}"}
        )

        assert response.status_code == 200

    def test_public_endpoint_no_auth_required(self, client):
        """Test public endpoint that doesn't require authentication."""
        response = client.get("/api/extensions/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_multiple_permissions_in_token(self, client, auth_manager):
        """Test token with multiple permissions."""
        token = auth_manager.create_access_token(
            user_id="multi-perm-user",
            permissions=[
                "extension:read",
                "extension:write",
                "extension:background_tasks"
            ]
        )

        # Test read endpoint
        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # Test write endpoint
        response = client.post(
            "/api/extensions/",
            json={"name": "test", "version": "1.0.0"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # Test background tasks endpoint
        response = client.post(
            "/api/extensions/background-tasks/",
            json={"name": "test-task"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_admin_role_has_all_permissions(self, client, auth_manager):
        """Test that admin role has access to all endpoints."""
        admin_token = auth_manager.create_access_token(
            user_id="admin-user",
            roles=["admin"],
            permissions=[]  # No explicit permissions, but admin role should grant access
        )

        # Test all endpoints with admin token
        endpoints = [
            ("GET", "/api/extensions/"),
            ("POST", "/api/extensions/", {"name": "test", "version": "1.0.0"}),
            ("DELETE", "/api/extensions/test-extension"),
            ("POST", "/api/extensions/background-tasks/", {"name": "test-task"})
        ]

        for method, url, *data in endpoints:
            if method == "GET":
                response = client.get(url, headers={"Authorization": f"Bearer {admin_token}"})
            elif method == "POST":
                response = client.post(url, json=data[0] if data else {}, headers={"Authorization": f"Bearer {admin_token}"})
            elif method == "DELETE":
                response = client.delete(url, headers={"Authorization": f"Bearer {admin_token}"})
            
            assert response.status_code == 200, f"Admin access failed for {method} {url}"

    def test_tenant_isolation_in_responses(self, client, auth_manager):
        """Test that tenant information is properly isolated in responses."""
        # Create tokens for different tenants
        tenant1_token = auth_manager.create_access_token(
            user_id="user1",
            tenant_id="tenant1",
            permissions=["extension:read"]
        )

        tenant2_token = auth_manager.create_access_token(
            user_id="user2",
            tenant_id="tenant2",
            permissions=["extension:read"]
        )

        # Test that each user gets their own tenant context
        response1 = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {tenant1_token}"}
        )
        assert response1.status_code == 200
        assert response1.json()["user_context"]["tenant_id"] == "tenant1"

        response2 = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {tenant2_token}"}
        )
        assert response2.status_code == 200
        assert response2.json()["user_context"]["tenant_id"] == "tenant2"

    def test_token_with_missing_required_fields(self, client, auth_manager):
        """Test token validation with missing required fields."""
        import jwt
        
        # Create token without user_id
        payload = {
            "tenant_id": "test-tenant",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        invalid_token = jwt.encode(payload, auth_manager.secret_key, algorithm=auth_manager.algorithm)

        response = client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == 403

    def test_concurrent_authentication_requests(self, client, auth_manager):
        """Test concurrent authentication requests."""
        import threading
        import time

        token = auth_manager.create_access_token(
            user_id="concurrent-user",
            permissions=["extension:read"]
        )

        results = []
        
        def make_request():
            response = client.get(
                "/api/extensions/",
                headers={"Authorization": f"Bearer {token}"}
            )
            results.append(response.status_code)

        # Create multiple threads to make concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10


class TestExtensionAPIAuthenticationDevelopmentMode:
    """Test extension API authentication in development mode."""

    @pytest.fixture
    def dev_auth_config(self):
        """Development authentication configuration."""
        return {
            "secret_key": "dev-secret",
            "enabled": True,
            "auth_mode": "development",
            "dev_bypass_enabled": True,
            "default_permissions": ["extension:read", "extension:write", "extension:admin"]
        }

    @pytest.fixture
    def dev_auth_manager(self, dev_auth_config):
        """Create development authentication manager."""
        return ExtensionAuthManager(dev_auth_config)

    @pytest.fixture
    def dev_test_app(self, dev_auth_manager):
        """Create test app with development authentication."""
        app = FastAPI()

        @app.get("/api/extensions/")
        async def list_extensions(
            user_context: dict = Depends(require_extension_read)
        ):
            return {
                "extensions": {},
                "user_context": user_context
            }

        with patch('server.security.get_extension_auth_manager', return_value=dev_auth_manager):
            yield app

    @pytest.fixture
    def dev_client(self, dev_test_app):
        """Create development test client."""
        return TestClient(dev_test_app)

    def test_development_mode_bypass(self, dev_client):
        """Test authentication bypass in development mode."""
        response = dev_client.get("/api/extensions/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_context"]["user_id"] == "dev-user"
        assert data["user_context"]["token_type"] == "development"

    def test_development_mode_with_token_still_works(self, dev_client, dev_auth_manager):
        """Test that tokens still work in development mode."""
        token = dev_auth_manager.create_access_token(
            user_id="real-user",
            permissions=["extension:read"]
        )

        response = dev_client.get(
            "/api/extensions/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should use the real token, not development bypass
        assert data["user_context"]["user_id"] == "real-user"


class TestExtensionAPIAuthenticationErrorHandling:
    """Test error handling in extension API authentication."""

    @pytest.fixture
    def error_test_app(self):
        """Create test app for error handling tests."""
        app = FastAPI()

        @app.get("/api/extensions/error-test")
        async def error_endpoint(
            user_context: dict = Depends(require_extension_read)
        ):
            # Simulate an error after authentication
            raise HTTPException(status_code=500, detail="Internal server error")

        return app

    @pytest.fixture
    def error_client(self, error_test_app):
        """Create client for error testing."""
        return TestClient(error_test_app)

    def test_authentication_error_vs_endpoint_error(self, error_client):
        """Test that authentication errors are distinguished from endpoint errors."""
        # Test authentication error (no token)
        response = error_client.get("/api/extensions/error-test")
        assert response.status_code == 403  # Authentication error

        # Test endpoint error (with valid token)
        from server.security import ExtensionAuthManager
        auth_manager = ExtensionAuthManager({"secret_key": "test", "enabled": True})
        token = auth_manager.create_access_token("test-user", permissions=["extension:read"])
        
        with patch('server.security.get_extension_auth_manager', return_value=auth_manager):
            response = error_client.get(
                "/api/extensions/error-test",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 500  # Endpoint error, not auth error