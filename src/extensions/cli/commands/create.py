"""
Create command for generating extension scaffolding.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any

from .base import BaseCommand


class CreateCommand(BaseCommand):
    """Command to create new extension from template."""
    
    TEMPLATES = {
        "basic": "Basic extension with API and UI",
        "api-only": "API-only extension without UI",
        "ui-only": "UI-only extension without API",
        "background-task": "Extension with background tasks",
        "full": "Full-featured extension with all capabilities"
    }
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add create command arguments."""
        parser.add_argument(
            "name",
            help="Extension name (kebab-case recommended)"
        )
        parser.add_argument(
            "--template", "-t",
            choices=list(CreateCommand.TEMPLATES.keys()),
            default="basic",
            help="Extension template to use"
        )
        parser.add_argument(
            "--output-dir", "-o",
            type=Path,
            default=Path("./extensions"),
            help="Output directory for the extension"
        )
        parser.add_argument(
            "--author",
            default="Extension Developer",
            help="Extension author name"
        )
        parser.add_argument(
            "--description",
            help="Extension description"
        )
        parser.add_argument(
            "--force", "-f",
            action="store_true",
            help="Overwrite existing extension directory"
        )
    
    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the create command."""
        extension_name = args.name
        template = args.template
        output_dir = args.output_dir
        
        # Validate extension name
        if not CreateCommand._is_valid_extension_name(extension_name):
            CreateCommand.print_error(
                "Invalid extension name. Use lowercase letters, numbers, and hyphens only."
            )
            return 1
        
        # Create extension directory
        extension_dir = output_dir / extension_name
        
        if extension_dir.exists() and not args.force:
            CreateCommand.print_error(
                f"Extension directory '{extension_dir}' already exists. Use --force to overwrite."
            )
            return 1
        
        try:
            # Create directory structure
            CreateCommand._create_directory_structure(extension_dir, template)
            
            # Generate manifest
            manifest = CreateCommand._generate_manifest(
                extension_name, 
                template, 
                args.author, 
                args.description
            )
            
            # Write manifest file
            manifest_path = extension_dir / "extension.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            
            # Generate template files
            CreateCommand._generate_template_files(extension_dir, template, extension_name)
            
            CreateCommand.print_success(f"Extension '{extension_name}' created successfully!")
            CreateCommand.print_info(f"Location: {extension_dir}")
            CreateCommand.print_info(f"Template: {template}")
            CreateCommand.print_info("Next steps:")
            print("  1. cd " + str(extension_dir))
            print("  2. kari-ext validate .")
            print("  3. kari-ext dev-server . --watch")
            
            return 0
            
        except Exception as e:
            CreateCommand.print_error(f"Failed to create extension: {e}")
            return 1
    
    @staticmethod
    def _is_valid_extension_name(name: str) -> bool:
        """Validate extension name format."""
        import re
        return bool(re.match(r"^[a-z0-9-]+$", name))
    
    @staticmethod
    def _create_directory_structure(extension_dir: Path, template: str) -> None:
        """Create the extension directory structure."""
        extension_dir.mkdir(parents=True, exist_ok=True)
        
        # Common directories
        (extension_dir / "tests").mkdir(exist_ok=True)
        
        # Template-specific directories
        if template in ["basic", "api-only", "full"]:
            (extension_dir / "api").mkdir(exist_ok=True)
        
        if template in ["basic", "ui-only", "full"]:
            (extension_dir / "ui").mkdir(exist_ok=True)
        
        if template in ["background-task", "full"]:
            (extension_dir / "tasks").mkdir(exist_ok=True)
        
        if template == "full":
            (extension_dir / "data").mkdir(exist_ok=True)
            (extension_dir / "config").mkdir(exist_ok=True)
            (extension_dir / "plugins").mkdir(exist_ok=True)
    
    @staticmethod
    def _generate_manifest(
        name: str, 
        template: str, 
        author: str, 
        description: str = None
    ) -> Dict[str, Any]:
        """Generate extension manifest based on template."""
        
        if description is None:
            description = f"A {template} extension generated by kari-ext"
        
        # Base manifest
        manifest = {
            "name": name,
            "version": "1.0.0",
            "display_name": name.replace("-", " ").title(),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "custom",
            "tags": ["generated", template],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": template in ["basic", "ui-only", "full"],
                "provides_api": template in ["basic", "api-only", "full"],
                "provides_background_tasks": template in ["background-task", "full"],
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
                "control_room_pages": [],
                "streamlit_pages": []
            },
            "api": {
                "endpoints": [],
                "prefix": f"/api/extensions/{name}",
                "tags": [name]
            },
            "background_tasks": [],
            "marketplace": {
                "price": "free",
                "support_url": "",
                "documentation_url": "",
                "screenshots": [],
                "categories": ["custom"],
                "keywords": [name, template]
            }
        }
        
        # Template-specific configurations
        if template in ["basic", "ui-only", "full"]:
            manifest["ui"]["control_room_pages"] = [
                {
                    "name": f"{name.replace('-', ' ').title()} Dashboard",
                    "path": f"/{name}",
                    "icon": "🔧",
                    "permissions": ["user", "admin"]
                }
            ]
        
        if template in ["basic", "api-only", "full"]:
            manifest["api"]["endpoints"] = [
                {
                    "path": "/status",
                    "methods": ["GET"],
                    "permissions": ["user"],
                    "description": "Get extension status",
                    "tags": ["status"]
                }
            ]
        
        if template in ["background-task", "full"]:
            manifest["background_tasks"] = [
                {
                    "name": "example_task",
                    "schedule": "0 */6 * * *",  # Every 6 hours
                    "function": "tasks.example_task"
                }
            ]
        
        return manifest
    
    @staticmethod
    def _generate_template_files(extension_dir: Path, template: str, name: str) -> None:
        """Generate template files based on the selected template."""
        
        # Generate __init__.py
        init_content = CreateCommand._generate_init_file(name, template)
        with open(extension_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(init_content)
        
        # Generate API files
        if template in ["basic", "api-only", "full"]:
            CreateCommand._generate_api_files(extension_dir, name)
        
        # Generate UI files
        if template in ["basic", "ui-only", "full"]:
            CreateCommand._generate_ui_files(extension_dir, name)
        
        # Generate background task files
        if template in ["background-task", "full"]:
            CreateCommand._generate_task_files(extension_dir, name)
        
        # Generate test files
        CreateCommand._generate_test_files(extension_dir, name, template)
        
        # Generate README
        CreateCommand._generate_readme(extension_dir, name, template)
    
    @staticmethod
    def _generate_init_file(name: str, template: str) -> str:
        """Generate the main __init__.py file."""
        class_name = "".join(word.capitalize() for word in name.split("-"))
        
        return f'''"""
{name.replace("-", " ").title()} Extension

A {template} extension for the Kari AI platform.
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
import logging


class {class_name}Extension(BaseExtension):
    """Main extension class for {name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{name}")
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {name} extension")
        # Add initialization logic here
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {name} extension")
        # Add cleanup logic here
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension."""
        {"from .api.routes import router; return router" if template in ["basic", "api-only", "full"] else "return None"}
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components for integration."""
        {"from .ui.components import get_components; return get_components()" if template in ["basic", "ui-only", "full"] else "return {}"}
    
    def get_background_tasks(self) -> List[Dict[str, Any]]:
        """Return background tasks to be scheduled."""
        {"from .tasks.scheduler import get_tasks; return get_tasks()" if template in ["background-task", "full"] else "return []"}


# Extension factory function
def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
'''
    
    @staticmethod
    def _generate_api_files(extension_dir: Path, name: str) -> None:
        """Generate API-related files."""
        api_dir = extension_dir / "api"
        
        # __init__.py
        with open(api_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write('"""API module for the extension."""\n')
        
        # routes.py
        routes_content = f'''"""
API routes for {name} extension.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(f"extension.{name}.api")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get extension status."""
    return {{
        "status": "active",
        "extension": "{name}",
        "version": "1.0.0"
    }}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {{"status": "healthy"}}
'''
        
        with open(api_dir / "routes.py", "w", encoding="utf-8") as f:
            f.write(routes_content)
        
        # models.py
        models_content = '''"""
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
'''
        
        with open(api_dir / "models.py", "w", encoding="utf-8") as f:
            f.write(models_content)
    
    @staticmethod
    def _generate_ui_files(extension_dir: Path, name: str) -> None:
        """Generate UI-related files."""
        ui_dir = extension_dir / "ui"
        
        # __init__.py
        with open(ui_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write('"""UI module for the extension."""\n')
        
        # components.py
        components_content = f'''"""
UI components for {name} extension.
"""

from typing import Dict, Any


def get_components() -> Dict[str, Any]:
    """Return UI components for integration."""
    return {{
        "dashboard": {{
            "name": "{name.replace('-', ' ').title()} Dashboard",
            "path": "/{name}",
            "component": "ExtensionDashboard",
            "props": {{
                "extension_name": "{name}",
                "title": "{name.replace('-', ' ').title()}"
            }}
        }}
    }}


def render_dashboard() -> str:
    """Render the main dashboard component."""
    return f"""
    <div class="extension-dashboard">
        <h1>{name.replace('-', ' ').title()} Extension</h1>
        <p>Welcome to your custom extension dashboard!</p>
        <div class="status-card">
            <h3>Status</h3>
            <p>Extension is running successfully.</p>
        </div>
    </div>
    """
'''
        
        with open(ui_dir / "components.py", "w", encoding="utf-8") as f:
            f.write(components_content)
    
    @staticmethod
    def _generate_task_files(extension_dir: Path, name: str) -> None:
        """Generate background task files."""
        tasks_dir = extension_dir / "tasks"
        
        # __init__.py
        with open(tasks_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write('"""Background tasks module for the extension."""\n')
        
        # scheduler.py
        scheduler_content = f'''"""
Background task scheduler for {name} extension.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(f"extension.{name}.tasks")


def get_tasks() -> List[Dict[str, Any]]:
    """Return list of background tasks."""
    return [
        {{
            "name": "example_task",
            "schedule": "0 */6 * * *",  # Every 6 hours
            "function": example_task,
            "description": "Example background task"
        }}
    ]


async def example_task() -> None:
    """Example background task."""
    logger.info("Running example background task")
    
    # Add your task logic here
    # For example:
    # - Data processing
    # - Cleanup operations
    # - External API calls
    # - Report generation
    
    logger.info("Example background task completed")
'''
        
        with open(tasks_dir / "scheduler.py", "w", encoding="utf-8") as f:
            f.write(scheduler_content)
    
    @staticmethod
    def _generate_test_files(extension_dir: Path, name: str, template: str) -> None:
        """Generate test files."""
        tests_dir = extension_dir / "tests"
        
        # __init__.py
        with open(tests_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write('"""Tests for the extension."""\n')
        
        # test_extension.py
        test_content = f'''"""
Tests for {name} extension.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{name.replace("-", "").title()}Extension:
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
        {"assert router is not None" if template in ["basic", "api-only", "full"] else "assert router is None"}
    
    def test_get_ui_components(self, extension):
        """Test UI components retrieval."""
        components = extension.get_ui_components()
        {"assert isinstance(components, dict)" if template in ["basic", "ui-only", "full"] else "assert components == {}"}
    
    def test_get_background_tasks(self, extension):
        """Test background tasks retrieval."""
        tasks = extension.get_background_tasks()
        {"assert isinstance(tasks, list)" if template in ["background-task", "full"] else "assert tasks == []"}
'''
        
        with open(tests_dir / "test_extension.py", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Generate API tests if applicable
        if template in ["basic", "api-only", "full"]:
            api_test_content = f'''"""
API tests for {name} extension.
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
    assert data["extension"] == "{name}"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
'''
            
            with open(tests_dir / "test_api.py", "w", encoding="utf-8") as f:
                f.write(api_test_content)
    
    @staticmethod
    def _generate_readme(extension_dir: Path, name: str, template: str) -> None:
        """Generate README file."""
        readme_content = f'''# {name.replace("-", " ").title()} Extension

A {template} extension for the Kari AI platform.

## Description

This extension was generated using the `kari-ext create` command with the `{template}` template.

## Features

{"- REST API endpoints" if template in ["basic", "api-only", "full"] else ""}
{"- Web UI components" if template in ["basic", "ui-only", "full"] else ""}
{"- Background tasks" if template in ["background-task", "full"] else ""}

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

{"Available at `/api/extensions/" + name + "`:" if template in ["basic", "api-only", "full"] else "No API endpoints available."}

{"- `GET /status` - Get extension status" if template in ["basic", "api-only", "full"] else ""}
{"- `GET /health` - Health check" if template in ["basic", "api-only", "full"] else ""}

## UI Components

{"- Dashboard at `/" + name + "`" if template in ["basic", "ui-only", "full"] else "No UI components available."}

## Background Tasks

{"- `example_task` - Runs every 6 hours" if template in ["background-task", "full"] else "No background tasks configured."}

## Configuration

Extension configuration can be modified in the `extension.json` manifest file.

## License

MIT License - see LICENSE file for details.
'''
        
        with open(extension_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)