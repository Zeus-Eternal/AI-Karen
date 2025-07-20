# Directory Structure Reorganization Design

## Overview

This design outlines the reorganization of the Kari AI platform's directory structure to create clear separation between system code, extension development, and plugin development. The reorganization addresses current confusion and inconsistencies while maintaining backward compatibility during the migration.

## Architecture

### Current vs Target Structure

#### Current Structure (Problematic)
```
kari-ai/
├── extensions/                           # Extension development (good location)
│   ├── examples/hello-extension/
│   ├── automation/workflow-automation/
│   └── ...
├── src/ai_karen_engine/
│   ├── extensions/                       # Extension system code (good)
│   │   ├── manager.py
│   │   ├── base.py
│   │   └── ...
│   ├── plugins/                          # MIXED: System + Individual plugins
│   │   ├── hello_world/                 # Individual plugin
│   │   ├── time_query/                  # Individual plugin
│   │   ├── sandbox.py                   # System code (misplaced)
│   │   ├── sandbox_runner.py            # System code (misplaced)
│   │   └── ...
│   ├── plugin_manager.py                # Plugin system code (misplaced)
│   ├── plugin_router.py                 # Plugin system code (misplaced)
│   └── ...
└── ...
```

#### Target Structure (Clean)
```
kari-ai/
├── extensions/                           # Extension development/marketplace
│   ├── examples/                        # Example extensions
│   │   ├── hello-extension/
│   │   └── ...
│   ├── automation/                      # Automation category
│   │   ├── workflow-automation/
│   │   └── ...
│   ├── analytics/                       # Analytics category
│   ├── communication/                   # Communication category
│   └── ...
├── plugins/                             # Plugin development/marketplace
│   ├── examples/                        # Example plugins
│   │   ├── hello-world/
│   │   └── ...
│   ├── core/                           # Core functionality plugins
│   │   ├── time-query/
│   │   └── ...
│   ├── integrations/                   # Integration plugins
│   │   ├── github/
│   │   ├── slack/
│   │   └── ...
│   ├── automation/                     # Automation plugins
│   └── ...
├── src/ai_karen_engine/
│   ├── extensions/                     # Extension system code
│   │   ├── __init__.py
│   │   ├── manager.py                  # Extension manager
│   │   ├── base.py                     # Base extension class
│   │   ├── registry.py                 # Extension registry
│   │   ├── orchestrator.py             # Plugin orchestrator
│   │   ├── models.py                   # Extension models
│   │   ├── validator.py                # Extension validator
│   │   └── ...
│   ├── plugins/                        # Plugin system code
│   │   ├── __init__.py
│   │   ├── manager.py                  # Plugin manager
│   │   ├── router.py                   # Plugin router
│   │   ├── registry.py                 # Plugin registry
│   │   ├── sandbox.py                  # Plugin sandbox
│   │   ├── sandbox_runner.py           # Sandbox runner
│   │   └── ...
│   └── ...
└── ...
```

## Components and Interfaces

### 1. Extension System Organization

The extension system code will be consolidated in `src/ai_karen_engine/extensions/`:

```python
# src/ai_karen_engine/extensions/__init__.py
"""
Extension system for Kari AI.

This module provides the core extension system functionality including
extension discovery, loading, management, and orchestration.
"""

from .manager import ExtensionManager
from .base import BaseExtension
from .registry import ExtensionRegistry
from .models import ExtensionManifest, ExtensionRecord
from .orchestrator import PluginOrchestrator
from .validator import ExtensionValidator

__all__ = [
    "ExtensionManager",
    "BaseExtension", 
    "ExtensionRegistry",
    "ExtensionManifest",
    "ExtensionRecord",
    "PluginOrchestrator",
    "ExtensionValidator"
]
```

### 2. Plugin System Organization

The plugin system code will be consolidated in `src/ai_karen_engine/plugins/`:

```python
# src/ai_karen_engine/plugins/__init__.py
"""
Plugin system for Kari AI.

This module provides the core plugin system functionality including
plugin discovery, routing, execution, and management.
"""

from .manager import PluginManager
from .router import PluginRouter
from .registry import PluginRegistry
from .sandbox import PluginSandbox
from .models import PluginManifest, PluginRecord

__all__ = [
    "PluginManager",
    "PluginRouter",
    "PluginRegistry", 
    "PluginSandbox",
    "PluginManifest",
    "PluginRecord"
]
```

### 3. Extension Development Structure

Extensions will be organized by category in the root `extensions/` directory:

```
extensions/
├── README.md                    # Extension development guide
├── examples/                   # Example extensions for learning
│   ├── hello-extension/
│   │   ├── extension.json
│   │   ├── __init__.py
│   │   └── README.md
│   └── ...
├── automation/                 # Automation extensions
│   ├── workflow-automation/
│   ├── task-scheduler/
│   └── ...
├── analytics/                  # Analytics extensions
│   ├── dashboard/
│   ├── reporting/
│   └── ...
├── communication/              # Communication extensions
│   ├── slack-integration/
│   ├── email-automation/
│   └── ...
├── development/                # Developer tools
├── integration/                # Third-party integrations
├── productivity/               # Productivity tools
└── security/                   # Security extensions
```

### 4. Plugin Development Structure

Plugins will be organized by category in the root `plugins/` directory:

```
plugins/
├── README.md                   # Plugin development guide
├── examples/                   # Example plugins for learning
│   ├── hello-world/
│   │   ├── plugin.json
│   │   ├── __init__.py
│   │   └── README.md
│   └── ...
├── core/                      # Core functionality plugins
│   ├── time-query/
│   ├── math-calculator/
│   └── ...
├── integrations/              # Integration plugins
│   ├── github/
│   ├── slack/
│   ├── jira/
│   └── ...
├── automation/                # Automation plugins
│   ├── file-watcher/
│   ├── scheduler/
│   └── ...
├── data/                      # Data processing plugins
│   ├── csv-parser/
│   ├── json-transformer/
│   └── ...
└── ai/                        # AI/ML plugins
    ├── text-classifier/
    ├── sentiment-analyzer/
    └── ...
```

## Data Models

### Migration Tracking

```python
# src/ai_karen_engine/core/migration.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class MigrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DirectoryMigration:
    """Tracks directory structure migration progress."""
    source_path: str
    target_path: str
    status: MigrationStatus
    files_moved: List[str]
    imports_updated: List[str]
    errors: List[str]
    
class MigrationManager:
    """Manages directory structure migration."""
    
    def __init__(self):
        self.migrations: Dict[str, DirectoryMigration] = {}
    
    def plan_migration(self) -> List[DirectoryMigration]:
        """Plan the directory migration steps."""
        
    def execute_migration(self, migration: DirectoryMigration) -> bool:
        """Execute a single migration step."""
        
    def rollback_migration(self, migration: DirectoryMigration) -> bool:
        """Rollback a migration if needed."""
```

### Import Path Mapping

```python
# src/ai_karen_engine/core/import_mapper.py
from typing import Dict, List, Optional

class ImportPathMapper:
    """Maps old import paths to new import paths during migration."""
    
    # Mapping of old paths to new paths
    PATH_MAPPINGS = {
        # Plugin system mappings
        "ai_karen_engine.plugin_manager": "ai_karen_engine.plugins.manager",
        "ai_karen_engine.plugin_router": "ai_karen_engine.plugins.router", 
        "ai_karen_engine.plugins.sandbox": "ai_karen_engine.plugins.sandbox",
        
        # Individual plugin mappings
        "ai_karen_engine.plugins.hello_world": "plugins.examples.hello_world",
        "ai_karen_engine.plugins.time_query": "plugins.core.time_query",
        
        # Extension system mappings (these are already correct)
        "ai_karen_engine.extensions.manager": "ai_karen_engine.extensions.manager",
    }
    
    def map_import_path(self, old_path: str) -> Optional[str]:
        """Map an old import path to the new path."""
        return self.PATH_MAPPINGS.get(old_path)
    
    def update_imports_in_file(self, file_path: str) -> List[str]:
        """Update import statements in a file."""
        
    def generate_compatibility_imports(self) -> str:
        """Generate compatibility import statements."""
```

## Error Handling

### Migration Error Handling

```python
class MigrationError(Exception):
    """Base exception for migration errors."""
    pass

class FileMovementError(MigrationError):
    """Error moving files during migration."""
    pass

class ImportUpdateError(MigrationError):
    """Error updating import statements."""
    pass

class MigrationErrorHandler:
    """Handles errors during directory migration."""
    
    def handle_file_movement_error(self, error: FileMovementError) -> None:
        """Handle file movement errors with rollback."""
        
    def handle_import_update_error(self, error: ImportUpdateError) -> None:
        """Handle import update errors with fallback."""
        
    def create_migration_report(self) -> Dict[str, Any]:
        """Create a detailed migration report."""
```

### Backward Compatibility

```python
# src/ai_karen_engine/compatibility.py
"""
Backward compatibility layer for directory reorganization.

This module provides temporary compatibility imports to ensure
existing code continues to work during the migration period.
"""

import warnings
from typing import Any

def deprecated_import(old_path: str, new_path: str, removal_version: str = "0.5.0"):
    """Decorator to mark imports as deprecated."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"Import from '{old_path}' is deprecated. "
                f"Use '{new_path}' instead. "
                f"This will be removed in version {removal_version}.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Compatibility imports for plugin system
try:
    from ai_karen_engine.plugins.manager import PluginManager as _PluginManager
    from ai_karen_engine.plugins.router import PluginRouter as _PluginRouter
    
    @deprecated_import("ai_karen_engine.plugin_manager", "ai_karen_engine.plugins.manager")
    class PluginManager(_PluginManager):
        pass
    
    @deprecated_import("ai_karen_engine.plugin_router", "ai_karen_engine.plugins.router") 
    class PluginRouter(_PluginRouter):
        pass
        
except ImportError:
    # Fallback during migration
    pass
```

## Testing Strategy

### Migration Testing

```python
# tests/test_directory_migration.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestDirectoryMigration:
    """Test directory structure migration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_root = Path(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_plugin_system_migration(self):
        """Test migration of plugin system code."""
        # Create old structure
        old_plugins_dir = self.test_root / "src/ai_karen_engine/plugins"
        old_plugins_dir.mkdir(parents=True)
        
        # Create test files
        (old_plugins_dir / "sandbox.py").write_text("# Plugin sandbox code")
        (old_plugins_dir / "hello_world").mkdir()
        (old_plugins_dir / "hello_world/__init__.py").write_text("# Hello world plugin")
        
        # Run migration
        migration_manager = MigrationManager()
        migrations = migration_manager.plan_migration()
        
        for migration in migrations:
            success = migration_manager.execute_migration(migration)
            assert success
        
        # Verify new structure
        new_plugins_system = self.test_root / "src/ai_karen_engine/plugins/sandbox.py"
        new_plugins_marketplace = self.test_root / "plugins/examples/hello_world/__init__.py"
        
        assert new_plugins_system.exists()
        assert new_plugins_marketplace.exists()
    
    def test_import_path_updates(self):
        """Test import path updates during migration."""
        # Create test file with old imports
        test_file = self.test_root / "test_imports.py"
        test_file.write_text("""
from ai_karen_engine.plugin_manager import PluginManager
from ai_karen_engine.plugins.hello_world import HelloWorldPlugin
""")
        
        # Update imports
        mapper = ImportPathMapper()
        updated_imports = mapper.update_imports_in_file(str(test_file))
        
        # Verify updates
        updated_content = test_file.read_text()
        assert "ai_karen_engine.plugins.manager" in updated_content
        assert "plugins.examples.hello_world" in updated_content
    
    def test_backward_compatibility(self):
        """Test backward compatibility imports."""
        # Test that old imports still work with deprecation warnings
        with pytest.warns(DeprecationWarning):
            from ai_karen_engine.plugin_manager import PluginManager
```

### Integration Testing

```python
# tests/test_reorganized_structure.py
class TestReorganizedStructure:
    """Test the reorganized directory structure."""
    
    def test_extension_system_imports(self):
        """Test extension system imports work correctly."""
        from ai_karen_engine.extensions import ExtensionManager
        from ai_karen_engine.extensions import BaseExtension
        
        assert ExtensionManager is not None
        assert BaseExtension is not None
    
    def test_plugin_system_imports(self):
        """Test plugin system imports work correctly."""
        from ai_karen_engine.plugins import PluginManager
        from ai_karen_engine.plugins import PluginRouter
        
        assert PluginManager is not None
        assert PluginRouter is not None
    
    def test_extension_discovery(self):
        """Test extension discovery works with new structure."""
        from ai_karen_engine.extensions import ExtensionManager
        
        manager = ExtensionManager(extension_root=Path("extensions"))
        extensions = manager.discover_extensions()
        
        # Should find extensions in categorized directories
        assert len(extensions) > 0
    
    def test_plugin_discovery(self):
        """Test plugin discovery works with new structure."""
        from ai_karen_engine.plugins import PluginManager
        
        manager = PluginManager(plugin_root=Path("plugins"))
        plugins = manager.discover_plugins()
        
        # Should find plugins in categorized directories
        assert len(plugins) > 0
```

## Security Considerations

### Migration Security

1. **File Permissions**: Ensure file permissions are preserved during migration
2. **Sensitive Data**: Protect any sensitive configuration during moves
3. **Atomic Operations**: Use atomic file operations where possible
4. **Backup Strategy**: Create backups before major structural changes
5. **Rollback Capability**: Ensure ability to rollback if migration fails

### Access Control

```python
class MigrationSecurityManager:
    """Manages security aspects of directory migration."""
    
    def verify_file_permissions(self, file_path: str) -> bool:
        """Verify file permissions are appropriate."""
        
    def backup_sensitive_files(self, files: List[str]) -> str:
        """Create secure backup of sensitive files."""
        
    def validate_migration_safety(self, migration: DirectoryMigration) -> bool:
        """Validate that migration is safe to execute."""
```

## Performance Considerations

### Migration Performance

1. **Batch Operations**: Process files in batches to avoid overwhelming filesystem
2. **Progress Tracking**: Provide progress feedback for large migrations
3. **Parallel Processing**: Use parallel processing where safe
4. **Memory Management**: Avoid loading large files entirely into memory
5. **Incremental Migration**: Support incremental migration for large codebases

### Runtime Performance

1. **Import Caching**: Cache import path mappings for performance
2. **Lazy Loading**: Load compatibility layers only when needed
3. **Minimal Overhead**: Minimize performance impact of compatibility layer
4. **Clean Removal**: Remove compatibility code after migration period

This design provides a comprehensive approach to reorganizing the directory structure while maintaining system stability and developer productivity during the transition.