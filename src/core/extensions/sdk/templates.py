"""
Extension templates for scaffolding new extensions.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from string import Template


class ExtensionTemplates:
    """Manages extension templates for scaffolding."""
    
    def __init__(self, config):
        self.config = config
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize built-in templates."""
        templates = {
            "basic": self._create_basic_template,
            "api": self._create_api_template,
            "ui": self._create_ui_template,
            "automation": self._create_automation_template,
            "data": self._create_data_template
        }
        
        for template_name, creator in templates.items():
            template_dir = self.templates_dir / template_name
            if not template_dir.exists():
                creator(template_dir)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available extension templates."""
        templates = []
        
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                info_file = template_dir / "template.json"
                if info_file.exists():
                    with open(info_file) as f:
                        template_info = json.load(f)
                    templates.append(template_info)
                else:
                    # Default template info
                    templates.append({
                        "name": template_dir.name,
                        "description": f"{template_dir.name.title()} extension template",
                        "category": "general"
                    })
        
        return templates
    
    def create_from_template(
        self,
        template_name: str,
        extension_name: str,
        output_path: Path,
        **kwargs
    ) -> None:
        """
        Create extension from template.
        
        Args:
            template_name: Name of template to use
            extension_name: Name of new extension
            output_path: Where to create the extension
            **kwargs: Template variables
        """
        template_dir = self.templates_dir / template_name
        if not template_dir.exists():
            raise ValueError(f"Template '{template_name}' not found")
        
        # Prepare template variables
        variables = {
            "extension_name": extension_name,
            "extension_class": self._to_class_name(extension_name),
            "extension_module": self._to_module_name(extension_name),
            **kwargs
        }
        
        # Copy template files
        self._copy_template_files(template_dir, output_path, variables)
        
        print(f"✅ Created extension '{extension_name}' from '{template_name}' template")
    
    def _copy_template_files(
        self,
        template_dir: Path,
        output_path: Path,
        variables: Dict[str, Any]
    ) -> None:
        """Copy and process template files."""
        output_path.mkdir(parents=True, exist_ok=True)
        
        for item in template_dir.iterdir():
            if item.name == "template.json":
                continue  # Skip template metadata
            
            dest_path = output_path / item.name
            
            if item.is_dir():
                self._copy_template_files(item, dest_path, variables)
            else:
                # Process template file
                if item.suffix in ['.py', '.json', '.md', '.tsx', '.ts', '.yaml', '.yml']:
                    self._process_template_file(item, dest_path, variables)
                else:
                    # Copy binary files as-is
                    shutil.copy2(item, dest_path)
    
    def _process_template_file(
        self,
        template_file: Path,
        output_file: Path,
        variables: Dict[str, Any]
    ) -> None:
        """Process a template file with variable substitution."""
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use Python's Template class for safe substitution
        template = Template(content)
        processed_content = template.safe_substitute(variables)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
    
    def _to_class_name(self, extension_name: str) -> str:
        """Convert extension name to class name."""
        return ''.join(word.capitalize() for word in extension_name.replace('-', '_').split('_'))
    
    def _to_module_name(self, extension_name: str) -> str:
        """Convert extension name to module name."""
        return extension_name.replace('-', '_').lower()
    
    def _create_basic_template(self, template_dir: Path) -> None:
        """Create basic extension template."""
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Template metadata
        template_info = {
            "name": "basic",
            "description": "Basic extension template with minimal functionality",
            "category": "starter",
            "features": ["manifest", "basic_structure", "tests"]
        }
        
        with open(template_dir / "template.json", 'w') as f:
            json.dump(template_info, f, indent=2)
        
        # Extension manifest
        manifest = {
            "name": "${extension_name}",
            "version": "1.0.0",
            "display_name": "${extension_name}",
            "description": "A basic Kari extension",
            "author": "Extension Developer",
            "license": "MIT",
            "category": "general",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": False,
                "provides_api": False,
                "provides_background_tasks": False
            },
            "permissions": {
                "data_access": [],
                "plugin_access": [],
                "system_access": [],
                "network_access": []
            }
        }
        
        with open(template_dir / "extension.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Main extension file
        extension_code = '''"""
${extension_name} extension for Kari AI platform.
"""

from src.core.extensions.base import BaseExtension
from src.core.extensions.models import ExtensionManifest, ExtensionContext


class ${extension_class}Extension(BaseExtension):
    """${extension_name} extension implementation."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing ${extension_name} extension")
        # Add initialization logic here
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down ${extension_name} extension")
        # Add cleanup logic here
'''
        
        with open(template_dir / "__init__.py", 'w') as f:
            f.write(extension_code)
        
        # Tests directory
        tests_dir = template_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        test_code = '''"""
Tests for ${extension_name} extension.
"""

import pytest
from unittest.mock import Mock

from .. import ${extension_class}Extension


class Test${extension_class}Extension:
    """Test cases for ${extension_class}Extension."""
    
    @pytest.fixture
    def extension(self):
        """Create extension instance for testing."""
        manifest = Mock()
        context = Mock()
        return ${extension_class}Extension(manifest, context)
    
    async def test_initialize(self, extension):
        """Test extension initialization."""
        await extension.initialize()
        # Add assertions here
    
    async def test_shutdown(self, extension):
        """Test extension shutdown."""
        await extension.shutdown()
        # Add assertions here
'''
        
        with open(tests_dir / "test_extension.py", 'w') as f:
            f.write(test_code)
        
        # Requirements file
        requirements = '''# Core dependencies
fastapi>=0.68.0
pydantic>=1.8.0

# Testing dependencies
pytest>=6.0.0
pytest-asyncio>=0.15.0
'''
        
        with open(template_dir / "requirements.txt", 'w') as f:
            f.write(requirements)
        
        # README template
        readme = '''# ${extension_name}

## Description

A basic Kari extension.

## Installation

```bash
kari-ext install ${extension_name}
```

## Usage

*Add usage instructions here.*

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
kari-ext dev --watch
```
'''
        
        with open(template_dir / "README.md", 'w') as f:
            f.write(readme)
    
    def _create_api_template(self, template_dir: Path) -> None:
        """Create API extension template."""
        # First create basic template
        self._create_basic_template(template_dir)
        
        # Update manifest for API capabilities
        manifest_path = template_dir / "extension.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        manifest["capabilities"]["provides_api"] = True
        manifest["permissions"]["data_access"] = ["read", "write"]
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Add API directory
        api_dir = template_dir / "api"
        api_dir.mkdir(exist_ok=True)
        
        # API routes
        routes_code = '''"""
API routes for ${extension_name} extension.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.core.extensions.auth import get_current_user
from src.core.extensions.models import User

router = APIRouter(prefix="/${extension_module}", tags=["${extension_name}"])


class ItemModel(BaseModel):
    """Example data model."""
    id: int
    name: str
    description: str


@router.get("/items", response_model=List[ItemModel])
async def get_items(user: User = Depends(get_current_user)):
    """Get all items."""
    # Add your logic here
    return []


@router.post("/items", response_model=ItemModel)
async def create_item(
    item: ItemModel,
    user: User = Depends(get_current_user)
):
    """Create a new item."""
    # Add your logic here
    return item


@router.get("/items/{item_id}", response_model=ItemModel)
async def get_item(
    item_id: int,
    user: User = Depends(get_current_user)
):
    """Get item by ID."""
    # Add your logic here
    raise HTTPException(status_code=404, detail="Item not found")
'''
        
        with open(api_dir / "routes.py", 'w') as f:
            f.write(routes_code)
        
        # Update main extension file to include API
        extension_code = '''"""
${extension_name} extension for Kari AI platform.
"""

from fastapi import APIRouter
from src.core.extensions.base import BaseExtension
from src.core.extensions.models import ExtensionManifest, ExtensionContext

from .api.routes import router as api_router


class ${extension_class}Extension(BaseExtension):
    """${extension_name} extension implementation."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Initializing ${extension_name} extension")
        # Add initialization logic here
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Shutting down ${extension_name} extension")
        # Add cleanup logic here
    
    def get_api_router(self) -> APIRouter:
        """Return API router for this extension."""
        return api_router
'''
        
        with open(template_dir / "__init__.py", 'w') as f:
            f.write(extension_code)
    
    def _create_ui_template(self, template_dir: Path) -> None:
        """Create UI extension template."""
        # First create basic template
        self._create_basic_template(template_dir)
        
        # Update manifest for UI capabilities
        manifest_path = template_dir / "extension.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        manifest["capabilities"]["provides_ui"] = True
        manifest["ui"] = {
            "control_room_pages": [
                {
                    "name": "${extension_name}",
                    "path": "/${extension_module}",
                    "icon": "🔧",
                    "permissions": ["user"]
                }
            ]
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Add UI directory
        ui_dir = template_dir / "ui"
        ui_dir.mkdir(exist_ok=True)
        
        # React component
        component_code = '''import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ${extension_class}PageProps {
  extensionName: string;
}

export const ${extension_class}Page: React.FC<${extension_class}PageProps> = ({ 
  extensionName 
}) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Add your data loading logic here
      const response = await fetch(`/api/extensions/${extensionName}/data`);
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <CardTitle>${extension_name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Button onClick={loadData} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh Data'}
            </Button>
            
            {data.length > 0 ? (
              <div className="grid gap-4">
                {data.map((item, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <pre>{JSON.stringify(item, null, 2)}</pre>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No data available</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ${extension_class}Page;
'''
        
        with open(ui_dir / "ExtensionPage.tsx", 'w') as f:
            f.write(component_code)
    
    def _create_automation_template(self, template_dir: Path) -> None:
        """Create automation extension template."""
        # Create API template as base
        self._create_api_template(template_dir)
        
        # Update manifest for automation capabilities
        manifest_path = template_dir / "extension.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        manifest["capabilities"]["provides_background_tasks"] = True
        manifest["permissions"]["plugin_access"] = ["execute"]
        manifest["background_tasks"] = [
            {
                "name": "automation_task",
                "schedule": "*/5 * * * *",
                "function": "tasks.automation_task"
            }
        ]
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Add tasks directory
        tasks_dir = template_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        # Background tasks
        tasks_code = '''"""
Background tasks for ${extension_name} extension.
"""

import asyncio
from typing import Dict, Any
from src.core.extensions.orchestration import PluginOrchestrator


async def automation_task(context: Dict[str, Any]) -> None:
    """Example automation task."""
    orchestrator = PluginOrchestrator(context["plugin_router"])
    
    try:
        # Example: Execute a plugin workflow
        workflow = [
            {"plugin": "time_query", "params": {}},
            {"plugin": "hello_world", "params": {"message": "Automation running"}}
        ]
        
        result = await orchestrator.execute_workflow(workflow, context["user_context"])
        print(f"Automation task completed: {result}")
        
    except Exception as e:
        print(f"Automation task failed: {e}")
'''
        
        with open(tasks_dir / "__init__.py", 'w') as f:
            f.write(tasks_code)
    
    def _create_data_template(self, template_dir: Path) -> None:
        """Create data-focused extension template."""
        # Create API template as base
        self._create_api_template(template_dir)
        
        # Add data directory
        data_dir = template_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Data models
        models_code = '''"""
Data models for ${extension_name} extension.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

Base = declarative_base()


class ${extension_class}Item(Base):
    """Database model for ${extension_name} items."""
    
    __tablename__ = "${extension_module}_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Tenant isolation
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)


class ${extension_class}ItemCreate(BaseModel):
    """Pydantic model for creating items."""
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ${extension_class}ItemResponse(BaseModel):
    """Pydantic model for item responses."""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
'''
        
        with open(data_dir / "models.py", 'w') as f:
            f.write(models_code)
        
        # Database migrations
        migrations_dir = data_dir / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        
        migration_sql = '''-- Create ${extension_name} tables
CREATE TABLE IF NOT EXISTS ${extension_module}_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_${extension_module}_items_tenant 
ON ${extension_module}_items(tenant_id);

CREATE INDEX IF NOT EXISTS idx_${extension_module}_items_user 
ON ${extension_module}_items(user_id);

CREATE INDEX IF NOT EXISTS idx_${extension_module}_items_name 
ON ${extension_module}_items(name);
'''
        
        with open(migrations_dir / "001_create_tables.sql", 'w') as f:
            f.write(migration_sql)