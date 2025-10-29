"""
Tests for extension API integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from src.extensions.api_integration import ExtensionAPIIntegration
from src.extensions.models import (
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionStatus,
    ExtensionCapabilities,
    ExtensionAPI,
    ExtensionAPIEndpoint
)
from src.extensions.base import BaseExtension


class MockExtension(BaseExtension):
    """Mock extension for testing."""
    
    async def _initialize(self):
        pass
    
    async def _shutdown(self):
        pass
    
    def create_api_router(self):
        from fastapi import APIRouter
        
        router = APIRouter()
        
        @router.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @router.post("/test")
        async def test_post():
            return {"message": "test post"}
        
        return router


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return FastAPI(title="Test App")


@pytest.fixture
def api_integration(app):
    """Create API integration instance."""
    return ExtensionAPIIntegration(app)


@pytest.fixture
def mock_manifest():
    """Create mock extension manifest."""
    return ExtensionManifest(
        name="test-extension",
        version="1.0.0",
        display_name="Test Extension",
        description="Test extension for API integration",
        author="Test Author",
        license="MIT",
        category="test",
        capabilities=ExtensionCapabilities(
            provides_api=True,
            provides_ui=False,
            provides_background_tasks=False,
            provides_webhooks=False
        ),
        api=ExtensionAPI(
            endpoints=[
                ExtensionAPIEndpoint(
                    path="/test",
                    methods=["GET", "POST"],
                    permissions=["user"]
                )
            ],
            prefix="/api/extensions/test-extension",
            tags=["test-extension"]
        )
    )


@pytest.fixture
def mock_extension_record(mock_manifest):
    """Create mock extension record."""
    from src.extensions.models import ExtensionContext
    
    context = ExtensionContext(extension_name="test-extension")
    instance = MockExtension(mock_manifest, context)
    
    return ExtensionRecord(
        manifest=mock_manifest,
        status=ExtensionStatus.ACTIVE,
        instance=instance
    )


class TestExtensionAPIIntegration:
    """Test extension API integration functionality."""
    
    @pytest.mark.asyncio
    async def test_register_extension_api_success(self, api_integration, mock_extension_record):
        """Test successful extension API registration."""
        # Register the extension API
        success = await api_integration.register_extension_api(mock_extension_record)
        
        assert success is True
        assert "test-extension" in api_integration.registered_extensions
        assert "test-extension" in api_integration.extension_routers
    
    @pytest.mark.asyncio
    async def test_register_extension_api_no_capability(self, api_integration, mock_extension_record):
        """Test registration when extension doesn't provide API."""
        # Disable API capability
        mock_extension_record.manifest.capabilities.provides_api = False
        
        success = await api_integration.register_extension_api(mock_extension_record)
        
        assert success is True  # Should succeed but not register anything
        assert "test-extension" not in api_integration.extension_routers
    
    @pytest.mark.asyncio
    async def test_register_extension_api_no_instance(self, api_integration, mock_extension_record):
        """Test registration when extension has no instance."""
        # Remove instance
        mock_extension_record.instance = None
        
        success = await api_integration.register_extension_api(mock_extension_record)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_unregister_extension_api(self, api_integration, mock_extension_record):
        """Test extension API unregistration."""
        # First register
        await api_integration.register_extension_api(mock_extension_record)
        assert "test-extension" in api_integration.registered_extensions
        
        # Then unregister
        success = await api_integration.unregister_extension_api("test-extension")
        
        assert success is True
        assert "test-extension" not in api_integration.registered_extensions
        assert "test-extension" not in api_integration.extension_routers
    
    @pytest.mark.asyncio
    async def test_get_extension_routes(self, api_integration, mock_extension_record):
        """Test getting extension routes."""
        # Register extension
        await api_integration.register_extension_api(mock_extension_record)
        
        # Get routes
        routes = api_integration.get_extension_routes("test-extension")
        
        assert len(routes) > 0
        assert all(route.extension_name == "test-extension" for route in routes)
    
    @pytest.mark.asyncio
    async def test_is_extension_registered(self, api_integration, mock_extension_record):
        """Test checking if extension is registered."""
        # Initially not registered
        assert not api_integration.is_extension_registered("test-extension")
        
        # Register extension
        await api_integration.register_extension_api(mock_extension_record)
        
        # Now should be registered
        assert api_integration.is_extension_registered("test-extension")
    
    @pytest.mark.asyncio
    async def test_health_check(self, api_integration, mock_extension_record):
        """Test API integration health check."""
        # Register extension
        await api_integration.register_extension_api(mock_extension_record)
        
        # Check health
        health = await api_integration.health_check()
        
        assert health["status"] == "healthy"
        assert health["registered_extensions"] == 1
        assert health["total_routes"] > 0
        assert health["active_routers"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_openapi_schema(self, api_integration, mock_extension_record):
        """Test OpenAPI schema generation."""
        # Register extension
        await api_integration.register_extension_api(mock_extension_record)
        
        # Generate schema
        schema = await api_integration.generate_extension_openapi_schema()
        
        assert isinstance(schema, dict)
        assert "paths" in schema or len(schema) == 0  # May be empty in test environment


class TestExtensionAPIEndpoints:
    """Test extension API endpoints work correctly."""
    
    @pytest.mark.asyncio
    async def test_extension_endpoints_accessible(self, app, mock_extension_record):
        """Test that extension endpoints are accessible through FastAPI."""
        # Create API integration and register extension
        api_integration = ExtensionAPIIntegration(app)
        await api_integration.register_extension_api(mock_extension_record)
        
        # Create test client
        client = TestClient(app)
        
        # Test GET endpoint
        response = client.get("/api/extensions/test-extension/test")
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Test POST endpoint
        response = client.post("/api/extensions/test-extension/test")
        assert response.status_code == 200
        assert response.json() == {"message": "test post"}
    
    @pytest.mark.asyncio
    async def test_extension_health_endpoint(self, app, mock_extension_record):
        """Test extension health endpoint."""
        # Initialize the mock extension
        await mock_extension_record.instance.initialize()
        
        # Create API integration and register extension
        api_integration = ExtensionAPIIntegration(app)
        await api_integration.register_extension_api(mock_extension_record)
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint (provided by base extension)
        response = client.get("/api/extensions/test-extension/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["extension"] == "test-extension"
        assert data["version"] == "1.0.0"
        assert "healthy" in data


if __name__ == "__main__":
    pytest.main([__file__])