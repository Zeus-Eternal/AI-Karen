"""
Migration executor for directory structure reorganization.

This module provides safe execution of directory structure migrations
with rollback capabilities and validation.
"""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging


logger = logging.getLogger(__name__)
import json
from datetime import datetime

from .migration_tools import (
    MigrationPlan, FileMove, ImportUpdate, MigrationStatus,
    MigrationValidator
)


@dataclass
class MigrationState:
    """Tracks the state of a migration execution."""
    plan: MigrationPlan
    status: MigrationStatus = MigrationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    completed_moves: List[FileMove] = None
    completed_imports: List[ImportUpdate] = None
    backup_path: Optional[Path] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.completed_moves is None:
            self.completed_moves = []
        if self.completed_imports is None:
            self.completed_imports = []
        if self.errors is None:
            self.errors = []


class MigrationExecutor:
    """Executes directory structure migrations safely."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.logger = logging.getLogger("migration.executor")
        self.validator = MigrationValidator(root_path)
        
    def execute_migration(self, plan: MigrationPlan, dry_run: bool = False) -> MigrationState:
        """
        Execute a migration plan.
        
        Args:
            plan: Migration plan to execute
            dry_run: If True, only simulate the migration
            
        Returns:
            Migration state with results
        """
        state = MigrationState(plan=plan)
        state.start_time = datetime.now()
        state.status = MigrationStatus.IN_PROGRESS
        
        self.logger.info(f"Starting migration execution (dry_run={dry_run})")
        
        try:
            # Validate plan before execution
            is_valid, errors = self.validator.validate_plan(plan)
            if not is_valid:
                state.errors.extend(errors)
                state.status = MigrationStatus.FAILED
                return state
            
            # Create backup if not dry run
            if not dry_run:
                state.backup_path = self._create_backup()
                self.logger.info(f"Created backup at {state.backup_path}")
            
            # Execute file moves
            self._execute_file_moves(plan.file_moves, state, dry_run)
            
            # Execute import updates
            self._execute_import_updates(plan.import_updates, state, dry_run)
            
            # Create new plugin system structure
            if not dry_run:
                self._create_plugin_system_structure()
            
            # Validate post-migration state
            if not dry_run:
                is_valid, errors = self.validator.validate_post_migration()
                if not is_valid:
                    state.errors.extend(errors)
                    self.logger.warning("Post-migration validation failed")
            
            state.status = MigrationStatus.COMPLETED
            self.logger.info("Migration completed successfully")
            
        except Exception as e:
            state.errors.append(str(e))
            state.status = MigrationStatus.FAILED
            self.logger.error(f"Migration failed: {e}")
            
            # Attempt rollback if not dry run
            if not dry_run and state.backup_path:
                self.logger.info("Attempting rollback...")
                try:
                    self._rollback_migration(state)
                    state.status = MigrationStatus.ROLLED_BACK
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
                    state.errors.append(f"Rollback failed: {rollback_error}")
        
        finally:
            state.end_time = datetime.now()
        
        return state
    
    def _create_backup(self) -> Path:
        """Create a backup of the current state."""
        backup_dir = Path(tempfile.mkdtemp(prefix="kari_migration_backup_"))
        
        # Backup key directories and files
        backup_items = [
            "src/ai_karen_engine/plugin_manager.py",
            "src/ai_karen_engine/plugin_router.py", 
            "src/ai_karen_engine/plugins/",
            "src/ai_karen_engine/__init__.py",
        ]
        
        for item in backup_items:
            source = self.root_path / item
            if source.exists():
                target = backup_dir / item
                target.parent.mkdir(parents=True, exist_ok=True)
                
                if source.is_file():
                    shutil.copy2(source, target)
                else:
                    shutil.copytree(source, target)
        
        # Save backup metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "root_path": str(self.root_path),
            "backed_up_items": backup_items
        }
        
        with open(backup_dir / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return backup_dir
    
    def _execute_file_moves(self, file_moves: List[FileMove], state: MigrationState, dry_run: bool) -> None:
        """Execute file move operations."""
        self.logger.info(f"Executing {len(file_moves)} file moves (dry_run={dry_run})")
        
        for move in file_moves:
            try:
                self.logger.debug(f"Moving {move.source_path} -> {move.target_path}")
                
                if not dry_run:
                    # Create target directory
                    move.target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file or directory
                    if move.source_path.is_file():
                        shutil.move(str(move.source_path), str(move.target_path))
                    else:
                        shutil.move(str(move.source_path), str(move.target_path))
                
                state.completed_moves.append(move)
                
            except Exception as e:
                error_msg = f"Failed to move {move.source_path} to {move.target_path}: {e}"
                self.logger.error(error_msg)
                state.errors.append(error_msg)
                raise
    
    def _execute_import_updates(self, import_updates: List[ImportUpdate], state: MigrationState, dry_run: bool) -> None:
        """Execute import statement updates."""
        self.logger.info(f"Executing {len(import_updates)} import updates (dry_run={dry_run})")
        
        # Group updates by file
        updates_by_file = {}
        for update in import_updates:
            file_path = update.file_path
            if file_path not in updates_by_file:
                updates_by_file[file_path] = []
            updates_by_file[file_path].append(update)
        
        # Process each file
        for file_path, updates in updates_by_file.items():
            try:
                self._update_imports_in_file(file_path, updates, dry_run)
                state.completed_imports.extend(updates)
                
            except Exception as e:
                error_msg = f"Failed to update imports in {file_path}: {e}"
                self.logger.error(error_msg)
                state.errors.append(error_msg)
                raise
    
    def _update_imports_in_file(self, file_path: Path, updates: List[ImportUpdate], dry_run: bool) -> None:
        """Update import statements in a single file."""
        if not file_path.exists():
            self.logger.warning(f"File does not exist: {file_path}")
            return
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Apply updates (in reverse line order to maintain line numbers)
        updates_sorted = sorted(updates, key=lambda u: u.line_number, reverse=True)
        
        for update in updates_sorted:
            line_idx = update.line_number - 1  # Convert to 0-based index
            
            if 0 <= line_idx < len(lines):
                old_line = lines[line_idx].rstrip()
                
                # Replace the import statement
                new_line = old_line.replace(update.old_import, update.new_import)
                lines[line_idx] = new_line + '\n'
                
                self.logger.debug(f"Updated line {update.line_number}: {old_line} -> {new_line}")
            else:
                self.logger.warning(f"Line number {update.line_number} out of range in {file_path}")
        
        # Write updated content
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
    
    def _create_plugin_system_structure(self) -> None:
        """Create the new plugin system directory structure."""
        plugin_system_dir = self.root_path / "src" / "ai_karen_engine" / "plugins"
        plugin_system_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py for plugin system
        init_content = '''"""
Plugin system for Kari AI.

This module provides the core plugin system functionality including
plugin discovery, routing, execution, and management.
"""

from .manager import PluginManager, get_plugin_manager
from .router import PluginRouter, PluginRecord, AccessDenied, get_plugin_router
from .sandbox import PluginSandbox
from .sandbox_runner import run_in_sandbox

__all__ = [
    "PluginManager",
    "PluginRouter",
    "PluginRecord",
    "AccessDenied",
    "PluginSandbox",
    "get_plugin_manager",
    "get_plugin_router",
    "run_in_sandbox",
]
'''
        
        init_file = plugin_system_dir / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        # Create plugin marketplace structure
        plugin_marketplace = self.root_path / "plugins"
        plugin_marketplace.mkdir(exist_ok=True)
        
        # Create category directories
        categories = ["examples", "core", "automation", "ai", "integrations"]
        for category in categories:
            category_dir = plugin_marketplace / category
            category_dir.mkdir(exist_ok=True)
            
            # Create category __init__.py
            category_init = category_dir / "__init__.py"
            with open(category_init, 'w', encoding='utf-8') as f:
                f.write(f'"""Plugins in the {category} category."""\n')
        
        # Create plugin marketplace README
        readme_content = '''# Kari AI Plugin Marketplace

This directory contains plugins for the Kari AI platform. Plugins are organized by category:

- `examples/` - Example plugins for learning and testing
- `core/` - Core functionality plugins
- `automation/` - Automation and workflow plugins  
- `ai/` - AI and machine learning plugins
- `integrations/` - Third-party service integrations

## Plugin Development

Each plugin should have its own directory with:
- `__init__.py` - Plugin entry point
- `handler.py` - Main plugin logic
- `plugin_manifest.json` - Plugin metadata
- `README.md` - Plugin documentation

See the examples directory for reference implementations.
'''
        
        readme_file = plugin_marketplace / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _rollback_migration(self, state: MigrationState) -> None:
        """Rollback a failed migration."""
        if not state.backup_path or not state.backup_path.exists():
            raise RuntimeError("No backup available for rollback")
        
        self.logger.info(f"Rolling back migration from backup {state.backup_path}")
        
        # Restore backed up files
        for item in state.backup_path.rglob("*"):
            if item.is_file() and item.name != "backup_metadata.json":
                # Calculate relative path from backup
                rel_path = item.relative_to(state.backup_path)
                target_path = self.root_path / rel_path
                
                # Create target directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Restore file
                shutil.copy2(item, target_path)
        
        # Remove newly created directories if they're empty
        new_dirs = [
            self.root_path / "plugins",
            self.root_path / "src" / "ai_karen_engine" / "plugins"
        ]
        
        for dir_path in new_dirs:
            if dir_path.exists():
                try:
                    # Remove if empty
                    dir_path.rmdir()
                except OSError:
                    # Directory not empty, leave it
                    pass
    
    def cleanup_backup(self, backup_path: Path) -> None:
        """Clean up migration backup."""
        if backup_path and backup_path.exists():
            shutil.rmtree(backup_path)
            self.logger.info(f"Cleaned up backup at {backup_path}")


def main():
    """CLI interface for migration executor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute directory structure migration")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root directory path")
    parser.add_argument("--plan", type=Path, required=True, help="Migration plan file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without changes")
    parser.add_argument("--force", action="store_true", help="Execute without confirmation")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load migration plan
    if not args.plan.exists():
        logger.warning("❌ Migration plan file not found: %s", args.plan)
        return 1
    
    # For now, we'll create a plan programmatically
    # In a real implementation, you'd load from the plan file
    from .migration_tools import MigrationPlanner
    planner = MigrationPlanner(args.root)
    plan = planner.create_migration_plan()
    
    # Confirm execution
    if not args.force and not args.dry_run:
        logger.warning(
            "⚠️  This will reorganize the directory structure of %s", args.root
        )
        logger.info("   - %d files will be moved", len(plan.file_moves))
        logger.info("   - %d import statements will be updated", len(plan.import_updates))
        
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Migration cancelled")
            return 0
    
    # Execute migration
    executor = MigrationExecutor(args.root)
    state = executor.execute_migration(plan, dry_run=args.dry_run)
    
    # Report results
    if state.status == MigrationStatus.COMPLETED:
        logger.info("✅ Migration completed successfully")
        logger.info("   - Moved %d files", len(state.completed_moves))
        logger.info("   - Updated %d import statements", len(state.completed_imports))
        
        if state.backup_path:
            logger.info("   - Backup created at %s", state.backup_path)
            
            # Ask about cleanup
            if not args.force:
                response = input("Remove backup? (y/N): ")
                if response.lower() == 'y':
                    executor.cleanup_backup(state.backup_path)
    
    elif state.status == MigrationStatus.FAILED:
        logger.error("❌ Migration failed")
        for error in state.errors:
            logger.error("   - %s", error)
        
        if state.status == MigrationStatus.ROLLED_BACK:
            logger.warning("🔄 Migration was rolled back")
        
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())