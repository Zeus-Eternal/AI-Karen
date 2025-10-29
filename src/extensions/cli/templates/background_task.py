"""
Background task extension template.
"""

from typing import Dict, Any
from .base import BaseTemplate


class BackgroundTaskTemplate(BaseTemplate):
    """Background task extension template."""
    
    @property
    def name(self) -> str:
        return "background-task"
    
    @property
    def description(self) -> str:
        return "Extension with background tasks"
    
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template."""
        if description is None:
            description = f"A background task extension: {self._get_display_name(extension_name)}"
        
        return {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": self._get_display_name(extension_name),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "automation",
            "tags": ["background-tasks", "automation", "generated"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": False,
                "provides_api": False,
                "provides_background_tasks": True,
                "provides_webhooks": False
            },
            "dependencies": {
                "plugins": [],
                "extensions": [],
                "system_services": []
            },
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": [],
                "system_access": ["logs"],
                "network_access": []
            },
            "resources": {
                "max_memory_mb": 128,
                "max_cpu_percent": 15,
                "max_disk_mb": 256
            },
            "ui": {
                "control_room_pages": [],
                "streamlit_pages": []
            },
            "api": {
                "endpoints": [],
                "prefix": f"/api/extensions/{extension_name}",
                "tags": [extension_name]
            },
            "background_tasks": [
                {
                    "name": "example_task",
                    "schedule": "0 */6 * * *",  # Every 6 hours
                    "function": "tasks.example_task"
                },
                {
                    "name": "daily_cleanup",
                    "schedule": "0 2 * * *",  # Daily at 2 AM
                    "function": "tasks.daily_cleanup"
                }
            ],
            "marketplace": {
                "price": "free",
                "support_url": "",
                "documentation_url": "",
                "screenshots": [],
                "categories": ["automation"],
                "keywords": [extension_name, "background-tasks", "automation"]
            }
        }
    
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates."""
        class_name = self._get_class_name(extension_name)
        display_name = self._get_display_name(extension_name)
        
        return {
            "__init__.py": f'''"""
{display_name} Extension

A background task extension for the Kari AI platform.
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
import logging


class {class_name}Extension(BaseExtension):
    """Background task extension class for {extension_name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{extension_name}")
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {extension_name} background task extension")
        # Initialize any resources needed for background tasks
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {extension_name} background task extension")
        # Cleanup background task resources
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router (none for background task only)."""
        return None
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components (none for background task only)."""
        return {{}}
    
    def get_background_tasks(self) -> List[Dict[str, Any]]:
        """Return background tasks to be scheduled."""
        from .tasks.scheduler import get_tasks
        return get_tasks()


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
''',
            "tasks/__init__.py": '"""Background tasks module for the extension."""\n',
            "tasks/scheduler.py": f'''"""
Background task scheduler for {extension_name} extension.
"""

from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(f"extension.{extension_name}.tasks")


def get_tasks() -> List[Dict[str, Any]]:
    """Return list of background tasks."""
    return [
        {{
            "name": "example_task",
            "schedule": "0 */6 * * *",  # Every 6 hours
            "function": example_task,
            "description": "Example background task that runs every 6 hours"
        }},
        {{
            "name": "daily_cleanup",
            "schedule": "0 2 * * *",  # Daily at 2 AM
            "function": daily_cleanup,
            "description": "Daily cleanup task"
        }}
    ]


async def example_task() -> None:
    """Example background task."""
    logger.info("Starting example background task")
    
    try:
        # Simulate some work
        await asyncio.sleep(1)
        
        # Add your task logic here
        # For example:
        # - Data processing
        # - External API calls
        # - Report generation
        # - System maintenance
        
        logger.info("Example background task completed successfully")
        
    except Exception as e:
        logger.error(f"Example background task failed: {{e}}")
        raise


async def daily_cleanup() -> None:
    """Daily cleanup background task."""
    logger.info("Starting daily cleanup task")
    
    try:
        # Add cleanup logic here
        # For example:
        # - Clean temporary files
        # - Archive old data
        # - Update statistics
        # - Send reports
        
        current_time = datetime.now()
        logger.info(f"Daily cleanup completed at {{current_time}}")
        
    except Exception as e:
        logger.error(f"Daily cleanup task failed: {{e}}")
        raise


async def custom_task(task_name: str, **kwargs) -> None:
    """Custom task that can be configured dynamically."""
    logger.info(f"Starting custom task: {{task_name}}")
    
    try:
        # Process kwargs and execute custom logic
        for key, value in kwargs.items():
            logger.info(f"Task parameter {{key}}: {{value}}")
        
        # Add custom task logic here
        
        logger.info(f"Custom task {{task_name}} completed")
        
    except Exception as e:
        logger.error(f"Custom task {{task_name}} failed: {{e}}")
        raise
''',
            "tests/__init__.py": '"""Tests for the extension."""\n',
            "tests/test_extension.py": f'''"""
Tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{class_name}Extension:
    """Test cases for the background task extension."""
    
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
    
    def test_get_background_tasks(self, extension):
        tasks = extension.get_background_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        
        # Check task structure
        for task in tasks:
            assert "name" in task
            assert "schedule" in task
            assert "function" in task
''',
            "tests/test_tasks.py": f'''"""
Tests for background tasks.
"""

import pytest
from ..tasks.scheduler import example_task, daily_cleanup, get_tasks


class TestBackgroundTasks:
    """Test cases for background tasks."""
    
    @pytest.mark.asyncio
    async def test_example_task(self):
        """Test example background task."""
        # Should not raise an exception
        await example_task()
    
    @pytest.mark.asyncio
    async def test_daily_cleanup(self):
        """Test daily cleanup task."""
        # Should not raise an exception
        await daily_cleanup()
    
    def test_get_tasks(self):
        """Test task list retrieval."""
        tasks = get_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) >= 2
        
        task_names = [task["name"] for task in tasks]
        assert "example_task" in task_names
        assert "daily_cleanup" in task_names
''',
            "README.md": f'''# {display_name} Extension

A background task extension for the Kari AI platform.

## Features

- Scheduled background tasks
- Automated processing
- System maintenance

## Background Tasks

- `example_task` - Runs every 6 hours
- `daily_cleanup` - Runs daily at 2 AM

## Configuration

Tasks can be configured in the `extension.json` manifest file under the `background_tasks` section.

## License

MIT License
'''
        }
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure."""
        return {
            "tasks": {},
            "tests": {}
        }