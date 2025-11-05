"""
API-only extension template.
"""

from typing import Dict, Any
from .base import BaseTemplate


class ApiOnlyTemplate(BaseTemplate):
    """API-only extension template."""
    
    @property
    def name(self) -> str:
        return "api-only"
    
    @property
    def description(self) -> str:
        return "API-only extension without UI"
    
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template."""
        if description is None:
            description = f"An API-only extension: {self._get_display_name(extension_name)}"
        
        return {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": self._get_display_name(extension_name),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "api",
            "tags": ["api", "generated"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": False,
                "provides_api": True,
                "provides_background_tasks": False,
                "provides_webhooks": False
            },
            "dependencies": {
                "plugins": [],
                "extensions": [],
                "system_services": []
            },
            "permissions": {
                "data_access": ["read"],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            },
            "resources": {
                "max_memory_mb": 64,
                "max_cpu_percent": 5,
                "max_disk_mb": 128
            },
            "ui": {
                "control_room_pages": [],
                # "streamlit_pages": [] # Streamlit no longer supported
            },
            "api": {
                "endpoints": [
                    {
                        "path": "/status",
                        "methods": ["GET"],
                        "permissions": ["user"],
                        "description": "Get extension status",
                        "tags": ["status"]
                    }
                ],
                "prefix": f"/api/extensions/{extension_name}",
                "tags": [extension_name]
            },
            "background_tasks": [],
            "marketplace": {
                "price": "free",
                "support_url": "",
                "documentation_url": "",
                "screenshots": [],
                "categories": ["api"],
                "keywords": [extension_name, "api"]
            }
        }
    
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates."""
        class_name = self._get_class_name(extension_name)
        display_name = self._get_display_name(extension_name)
        
        return {
            "__init__.py": f'''"""
{display_name} Extension

An API-only extension for the Kari AI platform.
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
import logging


class {class_name}Extension(BaseExtension):
    """API-only extension class for {extension_name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{extension_name}")
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {extension_name} API extension")
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {extension_name} API extension")
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension."""
        from .api.routes import router
        return router
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components (none for API-only)."""
        return {{}}
    
    def get_background_tasks(self) -> List[Dict[str, Any]]:
        """Return background tasks (none for API-only)."""
        return []


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
''',
            "api/__init__.py": '"""API module for the extension."""\n',
            "api/routes.py": f'''"""
API routes for {extension_name} extension.
"""

from fastapi import APIRouter
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(f"extension.{extension_name}.api")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get extension status."""
    return {{
        "status": "active",
        "extension": "{extension_name}",
        "version": "1.0.0",
        "type": "api-only"
    }}


@router.get("/info")
async def get_info() -> Dict[str, Any]:
    """Get extension information."""
    return {{
        "name": "{extension_name}",
        "display_name": "{display_name}",
        "type": "api-only",
        "capabilities": ["api"]
    }}
''',
            "tests/__init__.py": '"""Tests for the extension."""\n',
            "tests/test_extension.py": f'''"""
Tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{class_name}Extension:
    """Test cases for the API-only extension."""
    
    @pytest.fixture
    def mock_manifest(self):
        return Mock(spec=ExtensionManifest)
    
    @pytest.fixture
    def mock_context(self):
        return Mock(spec=ExtensionContext)
    
    @pytest.fixture
    def extension(self, mock_manifest, mock_context):
        from .. import create_extension
        return create_extension(mock_manifest, mock_context)
    
    @pytest.mark.asyncio
    async def test_initialize(self, extension):
        await extension.initialize()
    
    def test_get_api_router(self, extension):
        router = extension.get_api_router()
        assert router is not None
    
    def test_get_ui_components(self, extension):
        components = extension.get_ui_components()
        assert components == {{}}
''',
            "README.md": f'''# {display_name} Extension

An API-only extension for the Kari AI platform.

## Features

- REST API endpoints
- No UI components

## API Endpoints

Available at `/api/extensions/{extension_name}`:

- `GET /status` - Get extension status
- `GET /info` - Get extension information

## License

MIT License
'''
        }
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure."""
        return {
            "api": {},
            "tests": {}
        }