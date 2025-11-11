"""
UI-only extension template.
"""

from typing import Dict, Any
from .base import BaseTemplate


class UiOnlyTemplate(BaseTemplate):
    """UI-only extension template."""
    
    @property
    def name(self) -> str:
        return "ui-only"
    
    @property
    def description(self) -> str:
        return "UI-only extension without API"
    
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template."""
        if description is None:
            description = f"A UI-only extension: {self._get_display_name(extension_name)}"
        
        return {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": self._get_display_name(extension_name),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "ui",
            "tags": ["ui", "generated"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": True,
                "provides_api": False,
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
                "control_room_pages": [
                    {
                        "name": f"{self._get_display_name(extension_name)} Dashboard",
                        "path": f"/{extension_name}",
                        "icon": "🎨",
                        "permissions": ["user", "admin"]
                    }
                ],
            },
            "api": {
                "endpoints": [],
                "prefix": f"/api/extensions/{extension_name}",
                "tags": [extension_name]
            },
            "background_tasks": [],
            "marketplace": {
                "price": "free",
                "support_url": "",
                "documentation_url": "",
                "screenshots": [],
                "categories": ["ui"],
                "keywords": [extension_name, "ui"]
            }
        }
    
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates."""
        class_name = self._get_class_name(extension_name)
        display_name = self._get_display_name(extension_name)
        
        return {
            "__init__.py": f'''"""
{display_name} Extension

A UI-only extension for the Kari AI platform.
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
import logging


class {class_name}Extension(BaseExtension):
    """UI-only extension class for {extension_name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{extension_name}")
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {extension_name} UI extension")
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {extension_name} UI extension")
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router (none for UI-only)."""
        return None
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components for integration."""
        from .ui.components import get_components
        return get_components()
    
    def get_background_tasks(self) -> List[Dict[str, Any]]:
        """Return background tasks (none for UI-only)."""
        return []


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
''',
            "ui/__init__.py": '"""UI module for the extension."""\n',
            "ui/components.py": f'''"""
UI components for {extension_name} extension.
"""

from typing import Dict, Any


def get_components() -> Dict[str, Any]:
    """Return UI components for integration."""
    return {{
        "dashboard": {{
            "name": "{display_name} Dashboard",
            "path": "/{extension_name}",
            "component": "ExtensionDashboard",
            "props": {{
                "extension_name": "{extension_name}",
                "title": "{display_name}",
                "type": "ui-only"
            }}
        }}
    }}


def render_dashboard() -> str:
    """Render the main dashboard component."""
    return f"""
    <div class="extension-dashboard ui-only">
        <h1>{display_name} Extension</h1>
        <p>This is a UI-only extension with no API endpoints.</p>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>🎨 UI Components</h3>
                <p>Rich user interface components</p>
            </div>
            <div class="feature-card">
                <h3>📊 Dashboard</h3>
                <p>Interactive dashboard interface</p>
            </div>
        </div>
    </div>
    """
''',
            "tests/__init__.py": '"""Tests for the extension."""\n',
            "tests/test_extension.py": f'''"""
Tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{class_name}Extension:
    """Test cases for the UI-only extension."""
    
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
        assert router is None
    
    def test_get_ui_components(self, extension):
        components = extension.get_ui_components()
        assert isinstance(components, dict)
        assert "dashboard" in components
''',
            "README.md": f'''# {display_name} Extension

A UI-only extension for the Kari AI platform.

## Features

- Web UI components
- No API endpoints

## UI Components

- Dashboard at `/{extension_name}`

## License

MIT License
'''
        }
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure."""
        return {
            "ui": {},
            "tests": {}
        }