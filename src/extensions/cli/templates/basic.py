"""
Basic extension template with API and UI.
"""

from typing import Dict, Any
from .base import BaseTemplate


class BasicTemplate(BaseTemplate):
    """Basic extension template with API and UI capabilities."""
    
    @property
    def name(self) -> str:
        return "basic"
    
    @property
    def description(self) -> str:
        return "Basic extension with API and UI"
    
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template."""
        if description is None:
            description = f"A basic extension: {self._get_display_name(extension_name)}"
        
        return {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": self._get_display_name(extension_name),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "custom",
            "tags": ["basic", "generated"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": True,
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
                "max_memory_mb": 128,
                "max_cpu_percent": 10,
                "max_disk_mb": 256
            },
            "ui": {
                "control_room_pages": [
                    {
                        "name": f"{self._get_display_name(extension_name)} Dashboard",
                        "path": f"/{extension_name}",
                        "icon": "🔧",
                        "permissions": ["user", "admin"]
                    }
                ],
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
                "categories": ["custom"],
                "keywords": [extension_name, "basic"]
            }
        }
    
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates."""
        class_name = self._get_class_name(extension_name)
        display_name = self._get_display_name(extension_name)
        
        return {
            "__init__.py": f'''"""
{display_name} Extension

A basic extension for the Kari AI platform.
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
import logging


class {class_name}Extension(BaseExtension):
    """Main extension class for {extension_name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{extension_name}")
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {extension_name} extension")
        # Add initialization logic here
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {extension_name} extension")
        # Add cleanup logic here
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension."""
        from .api.routes import router
        return router
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components for integration."""
        from .ui.components import get_components
        return get_components()
    
    def get_background_tasks(self) -> List[Dict[str, Any]]:
        """Return background tasks to be scheduled."""
        return []


# Extension factory function
def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
''',
            "api/__init__.py": '"""API module for the extension."""\n',
            "api/routes.py": f'''"""
API routes for {extension_name} extension.
"""

from fastapi import APIRouter, Depends, HTTPException
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
        "version": "1.0.0"
    }}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {{"status": "healthy"}}
''',
            "api/models.py": '''"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    extension: str
    version: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
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
                "title": "{display_name}"
            }}
        }}
    }}


def render_dashboard() -> str:
    """Render the main dashboard component."""
    return f"""
    <div class="extension-dashboard">
        <h1>{display_name} Extension</h1>
        <p>Welcome to your custom extension dashboard!</p>
        <div class="status-card">
            <h3>Status</h3>
            <p>Extension is running successfully.</p>
        </div>
    </div>
    """
''',
            "tests/__init__.py": '"""Tests for the extension."""\n',
            "tests/test_extension.py": f'''"""
Tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{class_name}Extension:
    """Test cases for the main extension class."""
    
    @pytest.fixture
    def mock_manifest(self):
        """Mock extension manifest."""
        return Mock(spec=ExtensionManifest)
    
    @pytest.fixture
    def mock_context(self):
        """Mock extension context."""
        return Mock(spec=ExtensionContext)
    
    @pytest.fixture
    def extension(self, mock_manifest, mock_context):
        """Create extension instance for testing."""
        from .. import create_extension
        return create_extension(mock_manifest, mock_context)
    
    @pytest.mark.asyncio
    async def test_initialize(self, extension):
        """Test extension initialization."""
        await extension.initialize()
        # Add assertions here
    
    @pytest.mark.asyncio
    async def test_shutdown(self, extension):
        """Test extension shutdown."""
        await extension.shutdown()
        # Add assertions here
    
    def test_get_api_router(self, extension):
        """Test API router retrieval."""
        router = extension.get_api_router()
        assert router is not None
    
    def test_get_ui_components(self, extension):
        """Test UI components retrieval."""
        components = extension.get_ui_components()
        assert isinstance(components, dict)
    
    def test_get_background_tasks(self, extension):
        """Test background tasks retrieval."""
        tasks = extension.get_background_tasks()
        assert tasks == []
''',
            "tests/test_api.py": f'''"""
API tests for {extension_name} extension.
"""

import pytest
from fastapi.testclient import TestClient
from ..api.routes import router


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_status(client):
    """Test status endpoint."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["extension"] == "{extension_name}"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
''',
            "README.md": f'''# {display_name} Extension

A basic extension for the Kari AI platform.

## Description

This extension was generated using the `kari-ext create` command with the `basic` template.

## Features

- REST API endpoints
- Web UI components

## Development

### Prerequisites

- Python 3.11+
- Kari AI platform 0.4.0+

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Validate the extension:
   ```bash
   kari-ext validate .
   ```

3. Run tests:
   ```bash
   kari-ext test .
   ```

4. Start development server:
   ```bash
   kari-ext dev-server . --watch
   ```

### Testing

Run the test suite:

```bash
pytest tests/
```

### Packaging

Package the extension for distribution:

```bash
kari-ext package .
```

## API Endpoints

Available at `/api/extensions/{extension_name}`:

- `GET /status` - Get extension status
- `GET /health` - Health check

## UI Components

- Dashboard at `/{extension_name}`

## Configuration

Extension configuration can be modified in the `extension.json` manifest file.

## License

MIT License - see LICENSE file for details.
'''
        }
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure."""
        return {
            "api": {},
            "ui": {},
            "tests": {}
        }