"""
Full-featured extension template.
"""

from typing import Dict, Any
from .base import BaseTemplate


class FullTemplate(BaseTemplate):
    """Full-featured extension template with all capabilities."""
    
    @property
    def name(self) -> str:
        return "full"
    
    @property
    def description(self) -> str:
        return "Full-featured extension with all capabilities"
    
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template."""
        if description is None:
            description = f"A full-featured extension: {self._get_display_name(extension_name)}"
        
        return {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": self._get_display_name(extension_name),
            "description": description,
            "author": author,
            "license": "MIT",
            "category": "full-featured",
            "tags": ["full", "api", "ui", "background-tasks", "generated"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": True,
                "provides_api": True,
                "provides_background_tasks": True,
                "provides_webhooks": True
            },
            "dependencies": {
                "plugins": [],
                "extensions": [],
                "system_services": ["postgres", "redis"]
            },
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": ["logs", "metrics"],
                "network_access": ["outbound_http"]
            },
            "resources": {
                "max_memory_mb": 512,
                "max_cpu_percent": 25,
                "max_disk_mb": 1024
            },
            "ui": {
                "control_room_pages": [
                    {
                        "name": f"{self._get_display_name(extension_name)} Dashboard",
                        "path": f"/{extension_name}",
                        "icon": "🚀",
                        "permissions": ["user", "admin"]
                    },
                    {
                        "name": f"{self._get_display_name(extension_name)} Settings",
                        "path": f"/{extension_name}/settings",
                        "icon": "⚙️",
                        "permissions": ["admin"]
                    }
                ],
                "streamlit_pages": []
            },
            "api": {
                "endpoints": [
                    {
                        "path": "/status",
                        "methods": ["GET"],
                        "permissions": ["user"],
                        "description": "Get extension status",
                        "tags": ["status"]
                    },
                    {
                        "path": "/config",
                        "methods": ["GET", "POST"],
                        "permissions": ["admin"],
                        "description": "Manage extension configuration",
                        "tags": ["config"]
                    },
                    {
                        "path": "/data",
                        "methods": ["GET", "POST", "PUT", "DELETE"],
                        "permissions": ["user"],
                        "description": "Data management endpoints",
                        "tags": ["data"]
                    }
                ],
                "prefix": f"/api/extensions/{extension_name}",
                "tags": [extension_name]
            },
            "background_tasks": [
                {
                    "name": "data_sync",
                    "schedule": "0 */4 * * *",  # Every 4 hours
                    "function": "tasks.data_sync"
                },
                {
                    "name": "cleanup",
                    "schedule": "0 3 * * *",  # Daily at 3 AM
                    "function": "tasks.cleanup"
                }
            ],
            "marketplace": {
                "price": "free",
                "support_url": "",
                "documentation_url": "",
                "screenshots": [],
                "categories": ["full-featured"],
                "keywords": [extension_name, "full", "complete"]
            }
        }
    
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates."""
        class_name = self._get_class_name(extension_name)
        display_name = self._get_display_name(extension_name)
        
        return {
            "__init__.py": f'''"""
{display_name} Extension

A full-featured extension for the Kari AI platform.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import inspect
import logging

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from fastapi import APIRouter

from ai_karen_engine.extensions.data_manager import DataSchema

from .config.settings import ExtensionSettings
from .data.models import ExtensionConfig


class {class_name}Extension(BaseExtension):
    """Full-featured extension class for {extension_name}."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.logger = logging.getLogger(f"extension.{extension_name}")
        self.extension_path = Path(__file__).resolve().parent
        self.settings = ExtensionSettings(self.extension_path)
        self.config = ExtensionConfig(**self.settings.all())
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing {extension_name} full extension")
        
        # Initialize data manager
        await self._initialize_data_storage()
        
        # Load configuration
        await self._load_configuration()
        
        # Initialize plugins orchestration
        await self._initialize_plugins()
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down {extension_name} full extension")
        
        # Cleanup resources
        await self._cleanup_resources()
    
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
        from .tasks.scheduler import get_tasks
        return get_tasks()
    
    async def _initialize_data_storage(self) -> None:
        """Initialize data storage."""
        tenant_id = self.context.tenant_id or "global"

        if self.data_manager:
            schema = DataSchema(
                table_name="records",
                columns={{
                    "name": "STRING",
                    "value": "JSON",
                    "metadata": "JSON"
                }},
            )

            created = await self.data_manager.create_table("records", schema, tenant_id)
            if not created:
                raise RuntimeError("Failed to initialize persistent data storage for records table")
            return

        # Fall back to local JSON storage to ensure the extension remains functional
        data_path = self.extension_path / "data" / "records.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        if not data_path.exists():
            data_path.write_text("[]", encoding="utf-8")

    async def _load_configuration(self) -> None:
        """Load extension configuration."""
        self.settings.reload()
        self.config = ExtensionConfig(**self.settings.all())

        # Persist configuration snapshot when a data manager is available
        if self.data_manager:
            await self.store_data("configuration", self.config.model_dump())

    async def _initialize_plugins(self) -> None:
        """Initialize plugin orchestration."""
        if not self.plugin_orchestrator:
            self.logger.info("Plugin orchestrator not configured; skipping plugin initialization")
            return

        register_hook = None
        for candidate in ("register_extension", "initialize_extension", "initialize_for_extension"):
            if hasattr(self.plugin_orchestrator, candidate):
                register_hook = getattr(self.plugin_orchestrator, candidate)
                break

        if register_hook is None:
            self.logger.debug("Plugin orchestrator does not expose an initialization hook")
            return

        try:
            signature = inspect.signature(register_hook)
            if "context" in signature.parameters:
                result = register_hook(self.manifest, context=self.context)
            elif signature.parameters:
                result = register_hook(self.manifest)
            else:
                result = register_hook()

            if inspect.isawaitable(result):
                await result

            self.logger.info("Plugin orchestrator initialized for extension")
        except Exception as exc:
            self.logger.error("Failed to initialize plugin orchestrator", exc_info=exc)
            raise

    async def _cleanup_resources(self) -> None:
        """Cleanup extension resources."""
        if self.plugin_orchestrator and hasattr(self.plugin_orchestrator, "shutdown_extension"):
            shutdown_result = self.plugin_orchestrator.shutdown_extension(self.manifest.name)
            if inspect.isawaitable(shutdown_result):
                await shutdown_result

        if self.data_manager and hasattr(self.data_manager, "close"):
            close_result = self.data_manager.close()
            if inspect.isawaitable(close_result):
                await close_result

        await self.store_data("lifecycle_events", {{"event": "shutdown"}})


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
''',
            # API files
            "api/__init__.py": '"""API module for the extension."""\n',
            "api/routes.py": f'''"""
API routes for {extension_name} extension.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
import logging
from pydantic import ValidationError

from ..config.settings import ExtensionSettings
from ..data.models import ExtensionConfig
from .models import ConfigResponse, DataResponse, DataItem

router = APIRouter()
logger = logging.getLogger(f"extension.{extension_name}.api")

_EXTENSION_ROOT = Path(__file__).resolve().parents[1]
_SETTINGS = ExtensionSettings(_EXTENSION_ROOT)
_DATA_FILE = _EXTENSION_ROOT / "data" / "records.json"
_DATA_LOCK = asyncio.Lock()


async def _ensure_data_file() -> None:
    """Ensure the data file exists and is valid."""
    if not _DATA_FILE.exists():
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(_DATA_FILE.write_text, "[]", encoding="utf-8")


async def _read_records() -> List[DataItem]:
    """Read persisted data records."""
    await _ensure_data_file()

    async with _DATA_LOCK:
        raw = await asyncio.to_thread(_DATA_FILE.read_text, encoding="utf-8")

    try:
        payload = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError:
        logger.warning("Data store for {extension_name} is corrupt; resetting state")
        payload = []

    items: List[DataItem] = []
    for entry in payload:
        try:
            items.append(DataItem(**entry))
        except ValidationError as exc:
            logger.warning("Skipping invalid record in {extension_name} data store: %s", exc)

    return items


async def _write_records(items: List[DataItem]) -> None:
    """Persist data records to disk."""
    payload = [item.model_dump(mode="json") for item in items]

    async with _DATA_LOCK:
        await asyncio.to_thread(_DATA_FILE.write_text, json.dumps(payload, indent=2), encoding="utf-8")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get extension status."""
    return {{
        "status": "active",
        "extension": "{extension_name}",
        "version": "1.0.0",
        "type": "full-featured",
        "capabilities": ["api", "ui", "background-tasks"],
        "timestamp": datetime.utcnow().isoformat(),
    }}


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Get extension configuration."""
    config = ExtensionConfig(**_SETTINGS.all())
    return ConfigResponse(config=config.model_dump())


@router.post("/config", response_model=ConfigResponse)
async def update_config(config: Dict[str, Any]) -> ConfigResponse:
    """Update extension configuration."""
    merged = {{**_SETTINGS.all(), **config}}
    try:
        validated = ExtensionConfig(**merged)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    _SETTINGS.update(validated.model_dump())
    return ConfigResponse(config=validated.model_dump())


@router.get("/data", response_model=DataResponse)
async def get_data() -> DataResponse:
    """Get extension data."""
    items = await _read_records()
    return DataResponse(items=items, total=len(items))


@router.post("/data", response_model=DataItem, status_code=status.HTTP_201_CREATED)
async def create_data(data: Dict[str, Any]) -> DataItem:
    """Create new data entry."""
    payload = {{**data}}
    now = datetime.utcnow()
    payload.setdefault("id", str(uuid4()))
    payload.setdefault("created_at", now)
    payload.setdefault("updated_at", now)

    try:
        item = DataItem(**payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    items = await _read_records()
    items.append(item)
    await _write_records(items)
    return item


@router.put("/data/{{item_id}}", response_model=DataItem)
async def update_data(item_id: str, data: Dict[str, Any]) -> DataItem:
    """Update data entry."""
    items = await _read_records()

    for index, existing in enumerate(items):
        if existing.id == item_id:
            updated_payload = existing.model_dump()
            updated_payload.update(data)
            updated_payload["id"] = item_id
            updated_payload["updated_at"] = datetime.utcnow()

            try:
                updated_item = DataItem(**updated_payload)
            except ValidationError as exc:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

            items[index] = updated_item
            await _write_records(items)
            return updated_item

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {{item_id}} not found")


@router.delete("/data/{{item_id}}")
async def delete_data(item_id: str) -> Dict[str, str]:
    """Delete data entry."""
    items = await _read_records()
    filtered = [item for item in items if item.id != item_id]

    if len(filtered) == len(items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {{item_id}} not found")

    await _write_records(filtered)
    return {{"message": f"Data {{item_id}} deleted"}}
'''
,
            "api/models.py": '''"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    extension: str
    version: str
    type: str
    capabilities: List[str]


class ConfigResponse(BaseModel):
    """Configuration response model."""
    config: Dict[str, Any]


class DataItem(BaseModel):
    """Data item model."""
    id: Optional[str] = None
    name: str
    value: Any
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DataResponse(BaseModel):
    """Data response model."""
    items: List[DataItem]
    total: int
    page: int = 1
    per_page: int = 10
''',
            # UI files
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
            "component": "FullExtensionDashboard",
            "props": {{
                "extension_name": "{extension_name}",
                "title": "{display_name}",
                "type": "full-featured"
            }}
        }},
        "settings": {{
            "name": "{display_name} Settings",
            "path": "/{extension_name}/settings",
            "component": "FullExtensionSettings",
            "props": {{
                "extension_name": "{extension_name}",
                "title": "{display_name} Settings"
            }}
        }}
    }}


def render_dashboard() -> str:
    """Render the main dashboard component."""
    return f"""
    <div class="extension-dashboard full-featured">
        <header class="dashboard-header">
            <h1>{display_name} Extension</h1>
            <p>Full-featured extension with all capabilities</p>
        </header>
        
        <div class="capability-grid">
            <div class="capability-card">
                <h3>🌐 API Endpoints</h3>
                <p>RESTful API for data management</p>
                <ul>
                    <li>Status monitoring</li>
                    <li>Configuration management</li>
                    <li>Data CRUD operations</li>
                </ul>
            </div>
            
            <div class="capability-card">
                <h3>🎨 User Interface</h3>
                <p>Rich web interface components</p>
                <ul>
                    <li>Interactive dashboard</li>
                    <li>Settings panel</li>
                    <li>Data visualization</li>
                </ul>
            </div>
            
            <div class="capability-card">
                <h3>⏰ Background Tasks</h3>
                <p>Automated processing and maintenance</p>
                <ul>
                    <li>Data synchronization</li>
                    <li>Cleanup operations</li>
                    <li>Scheduled reports</li>
                </ul>
            </div>
            
            <div class="capability-card">
                <h3>🔧 Plugin Integration</h3>
                <p>Orchestrate other plugins</p>
                <ul>
                    <li>Plugin composition</li>
                    <li>Workflow automation</li>
                    <li>Data transformation</li>
                </ul>
            </div>
        </div>
        
        <div class="status-section">
            <h3>Extension Status</h3>
            <div class="status-indicators">
                <span class="status-indicator active">API: Active</span>
                <span class="status-indicator active">UI: Active</span>
                <span class="status-indicator active">Tasks: Running</span>
            </div>
        </div>
    </div>
    """


def render_settings() -> str:
    """Render the settings component."""
    return f"""
    <div class="extension-settings">
        <h2>{display_name} Settings</h2>
        <form class="settings-form">
            <div class="form-group">
                <label>Extension Name</label>
                <input type="text" value="{display_name}" readonly />
            </div>
            <div class="form-group">
                <label>Auto Sync</label>
                <input type="checkbox" checked />
            </div>
            <div class="form-group">
                <label>Sync Interval (hours)</label>
                <input type="number" value="4" min="1" max="24" />
            </div>
            <button type="submit">Save Settings</button>
        </form>
    </div>
    """
''',
            # Background tasks
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
            "name": "data_sync",
            "schedule": "0 */4 * * *",  # Every 4 hours
            "function": data_sync,
            "description": "Synchronize data with external sources"
        }},
        {{
            "name": "cleanup",
            "schedule": "0 3 * * *",  # Daily at 3 AM
            "function": cleanup,
            "description": "Clean up temporary data and logs"
        }}
    ]


async def data_sync() -> None:
    """Data synchronization background task."""
    logger.info("Starting data synchronization task")
    
    try:
        # Add data sync logic here
        # For example:
        # - Fetch data from external APIs
        # - Update local database
        # - Process and transform data
        # - Send notifications
        
        await asyncio.sleep(2)  # Simulate work
        
        logger.info("Data synchronization completed successfully")
        
    except Exception as e:
        logger.error(f"Data synchronization failed: {{e}}")
        raise


async def cleanup() -> None:
    """Cleanup background task."""
    logger.info("Starting cleanup task")
    
    try:
        # Add cleanup logic here
        # For example:
        # - Remove old temporary files
        # - Archive old data
        # - Clean up logs
        # - Update statistics
        
        current_time = datetime.now()
        logger.info(f"Cleanup completed at {{current_time}}")
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {{e}}")
        raise
''',
            # Plugin orchestration
            "plugins/__init__.py": '"""Plugin orchestration module."""\n',
            "plugins/orchestration.py": f'''"""
Plugin orchestration for {extension_name} extension.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(f"extension.{extension_name}.plugins")


class PluginOrchestrator:
    """Orchestrate plugin execution for the extension."""
    
    def __init__(self, plugin_router):
        self.plugin_router = plugin_router
        self.logger = logger
    
    async def execute_workflow(self, workflow_name: str, params: Dict[str, Any]) -> Any:
        """Execute a predefined workflow."""
        self.logger.info(f"Executing workflow: {{workflow_name}}")
        
        workflows = {{
            "data_processing": self._data_processing_workflow,
            "notification": self._notification_workflow,
            "analysis": self._analysis_workflow
        }}
        
        if workflow_name not in workflows:
            raise ValueError(f"Unknown workflow: {{workflow_name}}")
        
        return await workflows[workflow_name](params)
    
    async def _data_processing_workflow(self, params: Dict[str, Any]) -> Any:
        """Data processing workflow."""
        # Example workflow that chains multiple plugins
        results = []
        
        # Step 1: Data extraction
        # result1 = await self.plugin_router.execute("data_extractor", params)
        # results.append(result1)
        
        # Step 2: Data transformation
        # result2 = await self.plugin_router.execute("data_transformer", {{"data": result1}})
        # results.append(result2)
        
        # Step 3: Data storage
        # result3 = await self.plugin_router.execute("data_storage", {{"data": result2}})
        # results.append(result3)
        
        return results
    
    async def _notification_workflow(self, params: Dict[str, Any]) -> Any:
        """Notification workflow."""
        # Example notification workflow
        # await self.plugin_router.execute("email_notifier", params)
        # await self.plugin_router.execute("slack_notifier", params)
        return {{"status": "notifications_sent"}}
    
    async def _analysis_workflow(self, params: Dict[str, Any]) -> Any:
        """Analysis workflow."""
        # Example analysis workflow
        # result = await self.plugin_router.execute("data_analyzer", params)
        # report = await self.plugin_router.execute("report_generator", {{"analysis": result}})
        return {{"status": "analysis_complete"}}
''',
            # Data management
            "data/__init__.py": '"""Data management module."""\n',
            "data/models.py": f'''"""
Data models for {extension_name} extension.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ExtensionData(BaseModel):
    """Base data model for extension."""
    id: Optional[str] = None
    name: str
    value: Any
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExtensionConfig(BaseModel):
    """Configuration model for extension."""
    auto_sync: bool = True
    sync_interval_hours: int = 4
    max_data_age_days: int = 30
    notification_enabled: bool = True
    custom_settings: Optional[Dict[str, Any]] = None
''',
            # Configuration
            "config/__init__.py": '"""Configuration module."""\n',
            "config/settings.py": f'''"""
Settings for {extension_name} extension.
"""

from typing import Dict, Any
import json
from pathlib import Path


class ExtensionSettings:
    """Manage extension settings."""

    def __init__(self, extension_path: Path):
        self.extension_path = extension_path
        self.settings_file = extension_path / "config" / "settings.json"
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return {{
            "auto_sync": True,
            "sync_interval_hours": 4,
            "max_data_age_days": 30,
            "notification_enabled": True,
            "debug_mode": False,
        }}

    def reload(self) -> Dict[str, Any]:
        """Reload settings from disk and return the latest values."""
        self._settings = self._load_settings()
        return self.all()

    def all(self) -> Dict[str, Any]:
        """Return a copy of all settings."""
        return dict(self._settings)

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set setting value."""
        self._settings[key] = value
        self._save_settings()

    def update(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple settings at once."""
        self._settings.update(values)
        self._save_settings()
        return self.all()

    def _save_settings(self) -> None:
        """Save settings to file."""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(self._settings, f, indent=2)

''',
            "config/defaults.json": '''{{
  "auto_sync": true,
  "sync_interval_hours": 4,
  "max_data_age_days": 30,
  "notification_enabled": true,
  "debug_mode": false
}}''',
            # Tests
            "tests/__init__.py": '"""Tests for the extension."""\n',
            "tests/test_extension.py": f'''"""
Tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.extensions.models import ExtensionManifest, ExtensionContext


class Test{class_name}Extension:
    """Test cases for the full-featured extension."""
    
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
    
    @pytest.mark.asyncio
    async def test_shutdown(self, extension):
        await extension.shutdown()
    
    def test_get_api_router(self, extension):
        router = extension.get_api_router()
        assert router is not None
    
    def test_get_ui_components(self, extension):
        components = extension.get_ui_components()
        assert isinstance(components, dict)
        assert "dashboard" in components
        assert "settings" in components
    
    def test_get_background_tasks(self, extension):
        tasks = extension.get_background_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) >= 2
''',
            "README.md": f'''# {display_name} Extension

A full-featured extension for the Kari AI platform with all capabilities.

## Features

- 🌐 **REST API** - Complete CRUD operations and configuration management
- 🎨 **Web UI** - Interactive dashboard and settings interface  
- ⏰ **Background Tasks** - Automated data sync and cleanup
- 🔧 **Plugin Integration** - Orchestrate other plugins and workflows
- 💾 **Data Management** - Persistent storage with tenant isolation
- ⚙️ **Configuration** - Flexible settings and customization

## API Endpoints

Available at `/api/extensions/{extension_name}`:

- `GET /status` - Get extension status
- `GET /config` - Get configuration
- `POST /config` - Update configuration  
- `GET /data` - List data items
- `POST /data` - Create data item
- `PUT /data/{{id}}` - Update data item
- `DELETE /data/{{id}}` - Delete data item

## UI Components

- **Dashboard** at `/{extension_name}` - Main interface with status and controls
- **Settings** at `/{extension_name}/settings` - Configuration management

## Background Tasks

- `data_sync` - Runs every 4 hours to synchronize data
- `cleanup` - Runs daily at 3 AM for maintenance

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Validate extension
kari-ext validate .

# Run tests
kari-ext test .

# Start development server
kari-ext dev-server . --watch
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Packaging

```bash
kari-ext package .
```

## License

MIT License
'''
        }
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure."""
        return {
            "api": {},
            "ui": {},
            "tasks": {},
            "plugins": {},
            "data": {},
            "config": {},
            "tests": {}
        }