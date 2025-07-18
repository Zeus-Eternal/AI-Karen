"""
Directory structure migration tools.

This module provides tools for analyzing, planning, and executing
the directory structure reorganization safely.
"""

import ast
import os
import re
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import logging


class MigrationStatus(Enum):
    """Status of a migration operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class FileMove:
    """Represents a file move operation."""
    source_path: Path
    target_path: Path
    file_type: str  # 'plugin_system', 'individual_plugin', 'metadata'
    category: Optional[str] = None  # For plugins: 'examples', 'core', 'automation', etc.


@dataclass
class ImportUpdate:
    """Represents an import statement update."""
    file_path: Path
    line_number: int
    old_import: str
    new_import: str
    import_type: str  # 'from', 'import', 'lazy'


@dataclass
class MigrationPlan:
    """Complete migration plan."""
    file_moves: List[FileMove] = field(default_factory=list)
    import_updates: List[ImportUpdate] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    rollback_steps: List[str] = field(default_factory=list)


class DirectoryAnalyzer:
    """Analyzes current directory structure and dependencies."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.logger = logging.getLogger("migration.analyzer")
        
        # Plugin system files that need to be moved
        self.plugin_system_files = {
            "plugin_manager.py": "manager.py",
            "plugin_router.py": "router.py",
            "plugins/sandbox.py": "sandbox.py",
            "plugins/sandbox_runner.py": "sandbox_runner.py",
        }
        
        # Individual plugins that need to be moved
        self.plugin_categories = {
            "examples": ["hello_world", "sandbox_fail"],
            "core": ["time_query", "tui_fallback"],
            "automation": ["autonomous_task_handler", "git_merge_safe"],
            "ai": ["hf_llm", "fine_tune_lnm", "llm_services"],
            "integrations": ["desktop_agent", "k8s_scale", "llm_manager"],
        }
        
        # Import path mappings
        self.plugin_system_mappings = {
            "ai_karen_engine.plugin_manager": "ai_karen_engine.plugins.manager",
            "ai_karen_engine.plugin_router": "ai_karen_engine.plugins.router",
            "ai_karen_engine.plugins.sandbox": "ai_karen_engine.plugins.sandbox",
            "ai_karen_engine.plugins.sandbox_runner": "ai_karen_engine.plugins.sandbox_runner",
        }
        
        self.plugin_mappings = {}
        for category, plugins in self.plugin_categories.items():
            for plugin in plugins:
                old_path = f"ai_karen_engine.plugins.{plugin}"
                new_path = f"plugins.{category}.{plugin.replace('_', '_')}"
                self.plugin_mappings[old_path] = new_path
    
    def scan_imports(self) -> Dict[str, List[ImportUpdate]]:
        """Scan all Python files for imports that need updating."""
        import_updates = {}
        
        # Scan all Python files
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            updates = self._analyze_file_imports(py_file)
            if updates:
                import_updates[str(py_file)] = updates
        
        return import_updates
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file_imports(self, file_path: Path) -> List[ImportUpdate]:
        """Analyze imports in a single file."""
        updates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to find import statements
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        old_import = alias.name
                        new_import = self._map_import_path(old_import)
                        if new_import and new_import != old_import:
                            updates.append(ImportUpdate(
                                file_path=file_path,
                                line_number=node.lineno,
                                old_import=f"import {old_import}",
                                new_import=f"import {new_import}",
                                import_type="import"
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        old_module = node.module
                        new_module = self._map_import_path(old_module)
                        if new_module and new_module != old_module:
                            # Reconstruct the from import
                            names = [alias.name for alias in node.names]
                            old_import = f"from {old_module} import {', '.join(names)}"
                            new_import = f"from {new_module} import {', '.join(names)}"
                            
                            updates.append(ImportUpdate(
                                file_path=file_path,
                                line_number=node.lineno,
                                old_import=old_import,
                                new_import=new_import,
                                import_type="from"
                            ))
        
        except Exception as e:
            self.logger.warning(f"Failed to analyze imports in {file_path}: {e}")
        
        return updates
    
    def _map_import_path(self, old_path: str) -> Optional[str]:
        """Map old import path to new import path."""
        # Check plugin system mappings
        if old_path in self.plugin_system_mappings:
            return self.plugin_system_mappings[old_path]
        
        # Check individual plugin mappings
        if old_path in self.plugin_mappings:
            return self.plugin_mappings[old_path]
        
        # Check for partial matches (e.g., submodules)
        for old_prefix, new_prefix in {**self.plugin_system_mappings, **self.plugin_mappings}.items():
            if old_path.startswith(old_prefix + "."):
                suffix = old_path[len(old_prefix):]
                return new_prefix + suffix
        
        return None
    
    def identify_plugin_files(self) -> List[FileMove]:
        """Identify all plugin files that need to be moved."""
        file_moves = []
        
        # Plugin system files
        src_engine = self.root_path / "src" / "ai_karen_engine"
        for old_rel_path, new_filename in self.plugin_system_files.items():
            old_path = src_engine / old_rel_path
            if old_path.exists():
                new_path = src_engine / "plugins" / new_filename
                file_moves.append(FileMove(
                    source_path=old_path,
                    target_path=new_path,
                    file_type="plugin_system"
                ))
        
        # Individual plugin directories
        plugins_dir = src_engine / "plugins"
        if plugins_dir.exists():
            for category, plugin_names in self.plugin_categories.items():
                for plugin_name in plugin_names:
                    plugin_dir = plugins_dir / plugin_name
                    if plugin_dir.exists():
                        # Convert underscores to hyphens for new naming convention
                        new_plugin_name = plugin_name.replace("_", "-")
                        new_path = self.root_path / "plugins" / category / new_plugin_name
                        
                        file_moves.append(FileMove(
                            source_path=plugin_dir,
                            target_path=new_path,
                            file_type="individual_plugin",
                            category=category
                        ))
        
        # Plugin metadata
        meta_dir = plugins_dir / "__meta"
        if meta_dir.exists():
            new_meta_path = self.root_path / "plugins" / "__meta"
            file_moves.append(FileMove(
                source_path=meta_dir,
                target_path=new_meta_path,
                file_type="metadata"
            ))
        
        return file_moves


class MigrationPlanner:
    """Creates comprehensive migration plans."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.analyzer = DirectoryAnalyzer(root_path)
        self.logger = logging.getLogger("migration.planner")
    
    def create_migration_plan(self) -> MigrationPlan:
        """Create a comprehensive migration plan."""
        self.logger.info("Creating migration plan...")
        
        plan = MigrationPlan()
        
        # Identify file moves
        plan.file_moves = self.analyzer.identify_plugin_files()
        self.logger.info(f"Identified {len(plan.file_moves)} file moves")
        
        # Identify import updates
        import_updates_by_file = self.analyzer.scan_imports()
        for file_path, updates in import_updates_by_file.items():
            plan.import_updates.extend(updates)
        self.logger.info(f"Identified {len(plan.import_updates)} import updates")
        
        # Create validation steps
        plan.validation_steps = self._create_validation_steps(plan)
        
        # Create rollback steps
        plan.rollback_steps = self._create_rollback_steps(plan)
        
        return plan
    
    def _create_validation_steps(self, plan: MigrationPlan) -> List[str]:
        """Create validation steps for the migration."""
        return [
            "Verify all source files exist before moving",
            "Check that target directories can be created",
            "Validate that no files will be overwritten",
            "Test import syntax after updates",
            "Run basic import tests",
            "Verify plugin discovery still works",
            "Test extension system integration",
            "Run core functionality tests",
        ]
    
    def _create_rollback_steps(self, plan: MigrationPlan) -> List[str]:
        """Create rollback steps for the migration."""
        return [
            "Restore original file locations",
            "Revert import statement changes",
            "Remove newly created directories if empty",
            "Restore original plugin discovery paths",
            "Verify system functionality after rollback",
        ]


class MigrationValidator:
    """Validates migration plans and operations."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.logger = logging.getLogger("migration.validator")
    
    def validate_plan(self, plan: MigrationPlan) -> Tuple[bool, List[str]]:
        """Validate a migration plan."""
        errors = []
        
        # Validate file moves
        for move in plan.file_moves:
            if not move.source_path.exists():
                errors.append(f"Source file does not exist: {move.source_path}")
            
            if move.target_path.exists():
                errors.append(f"Target path already exists: {move.target_path}")
            
            # Check if target directory can be created
            try:
                move.target_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create target directory {move.target_path.parent}: {e}")
        
        # Validate import updates
        for update in plan.import_updates:
            if not update.file_path.exists():
                errors.append(f"File for import update does not exist: {update.file_path}")
            
            # Basic syntax validation
            try:
                compile(update.new_import, '<string>', 'exec')
            except SyntaxError as e:
                errors.append(f"Invalid import syntax: {update.new_import} - {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_post_migration(self) -> Tuple[bool, List[str]]:
        """Validate system state after migration."""
        errors = []
        
        # Check that new plugin system structure exists
        plugin_system_dir = self.root_path / "src" / "ai_karen_engine" / "plugins"
        if not plugin_system_dir.exists():
            errors.append("Plugin system directory was not created")
        
        required_files = ["manager.py", "router.py", "sandbox.py", "__init__.py"]
        for filename in required_files:
            file_path = plugin_system_dir / filename
            if not file_path.exists():
                errors.append(f"Required plugin system file missing: {filename}")
        
        # Check that plugin marketplace structure exists
        plugin_marketplace = self.root_path / "plugins"
        if not plugin_marketplace.exists():
            errors.append("Plugin marketplace directory was not created")
        
        # Check basic import functionality
        try:
            import sys
            sys.path.insert(0, str(self.root_path / "src"))
            
            # Test plugin system imports
            from ai_karen_engine.plugins import manager, router
            self.logger.info("Plugin system imports successful")
            
        except ImportError as e:
            errors.append(f"Plugin system imports failed: {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors


class MigrationReporter:
    """Generates migration reports and documentation."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.logger = logging.getLogger("migration.reporter")
    
    def generate_plan_report(self, plan: MigrationPlan) -> str:
        """Generate a detailed migration plan report."""
        report = []
        report.append("# Directory Structure Migration Plan")
        report.append("")
        
        # File moves section
        report.append("## File Moves")
        report.append("")
        
        moves_by_type = {}
        for move in plan.file_moves:
            if move.file_type not in moves_by_type:
                moves_by_type[move.file_type] = []
            moves_by_type[move.file_type].append(move)
        
        for file_type, moves in moves_by_type.items():
            report.append(f"### {file_type.replace('_', ' ').title()}")
            report.append("")
            for move in moves:
                report.append(f"- `{move.source_path}` → `{move.target_path}`")
                if move.category:
                    report.append(f"  - Category: {move.category}")
            report.append("")
        
        # Import updates section
        report.append("## Import Updates")
        report.append("")
        
        updates_by_file = {}
        for update in plan.import_updates:
            file_key = str(update.file_path)
            if file_key not in updates_by_file:
                updates_by_file[file_key] = []
            updates_by_file[file_key].append(update)
        
        for file_path, updates in updates_by_file.items():
            report.append(f"### {file_path}")
            report.append("")
            for update in updates:
                report.append(f"- Line {update.line_number}: `{update.old_import}` → `{update.new_import}`")
            report.append("")
        
        # Validation steps
        report.append("## Validation Steps")
        report.append("")
        for i, step in enumerate(plan.validation_steps, 1):
            report.append(f"{i}. {step}")
        report.append("")
        
        # Rollback steps
        report.append("## Rollback Steps")
        report.append("")
        for i, step in enumerate(plan.rollback_steps, 1):
            report.append(f"{i}. {step}")
        
        return "\n".join(report)
    
    def save_plan_report(self, plan: MigrationPlan, output_path: Path) -> None:
        """Save migration plan report to file."""
        report = self.generate_plan_report(plan)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"Migration plan report saved to {output_path}")


# CLI interface for migration tools
def main():
    """Main CLI interface for migration tools."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Directory structure migration tools")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root directory path")
    parser.add_argument("--action", choices=["analyze", "plan", "validate"], required=True,
                       help="Action to perform")
    parser.add_argument("--output", type=Path, help="Output file for reports")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if args.action == "analyze":
        analyzer = DirectoryAnalyzer(args.root)
        
        print("Analyzing current directory structure...")
        file_moves = analyzer.identify_plugin_files()
        print(f"Found {len(file_moves)} files to move")
        
        import_updates = analyzer.scan_imports()
        total_updates = sum(len(updates) for updates in import_updates.values())
        print(f"Found {total_updates} import statements to update")
        
    elif args.action == "plan":
        planner = MigrationPlanner(args.root)
        plan = planner.create_migration_plan()
        
        reporter = MigrationReporter(args.root)
        if args.output:
            reporter.save_plan_report(plan, args.output)
        else:
            print(reporter.generate_plan_report(plan))
    
    elif args.action == "validate":
        validator = MigrationValidator(args.root)
        is_valid, errors = validator.validate_post_migration()
        
        if is_valid:
            print("✅ Migration validation passed")
        else:
            print("❌ Migration validation failed:")
            for error in errors:
                print(f"  - {error}")


if __name__ == "__main__":
    main()