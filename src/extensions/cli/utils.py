"""
Utility functions for CLI commands.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


def is_valid_extension_name(name: str) -> bool:
    """Validate extension name format."""
    return bool(re.match(r"^[a-z0-9-]+$", name))


def is_valid_version(version: str) -> bool:
    """Validate semantic version format."""
    return bool(re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$", version))


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return None


def save_json_file(file_path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
        return True
    except (IOError, TypeError):
        return False


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory."""
    return list(directory.rglob("*.py"))


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    import hashlib
    
    hash_obj = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError:
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_extension_info(extension_path: Path) -> Dict[str, Any]:
    """Get basic information about an extension."""
    info = {
        "name": extension_path.name,
        "path": str(extension_path),
        "exists": extension_path.exists(),
        "is_directory": extension_path.is_dir() if extension_path.exists() else False,
        "has_manifest": False,
        "has_init": False,
        "has_tests": False,
        "python_files": 0,
        "total_size": 0
    }
    
    if not info["exists"] or not info["is_directory"]:
        return info
    
    # Check for key files
    info["has_manifest"] = (extension_path / "extension.json").exists()
    info["has_init"] = (extension_path / "__init__.py").exists()
    info["has_tests"] = (extension_path / "tests").exists()
    
    # Count Python files and calculate size
    try:
        python_files = find_python_files(extension_path)
        info["python_files"] = len(python_files)
        
        total_size = 0
        for file_path in extension_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except OSError:
                    pass
        info["total_size"] = total_size
    except Exception:
        pass
    
    return info


def create_directory_structure(base_path: Path, structure: Dict[str, Any]) -> None:
    """Create directory structure from a nested dictionary."""
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
            create_directory_structure(path, content)
        else:
            # It's a file
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is not None:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.touch()


def validate_manifest_schema(manifest: Dict[str, Any]) -> List[str]:
    """Validate manifest against expected schema."""
    errors = []
    
    # Required top-level fields
    required_fields = [
        "name", "version", "display_name", "description", "author",
        "api_version", "capabilities", "permissions", "resources"
    ]
    
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
    
    # Validate specific field types and values
    if "name" in manifest:
        if not isinstance(manifest["name"], str) or not is_valid_extension_name(manifest["name"]):
            errors.append("Invalid extension name format")
    
    if "version" in manifest:
        if not isinstance(manifest["version"], str) or not is_valid_version(manifest["version"]):
            errors.append("Invalid version format")
    
    if "capabilities" in manifest:
        caps = manifest["capabilities"]
        if not isinstance(caps, dict):
            errors.append("Capabilities must be an object")
        else:
            required_caps = ["provides_ui", "provides_api", "provides_background_tasks", "provides_webhooks"]
            for cap in required_caps:
                if cap not in caps or not isinstance(caps[cap], bool):
                    errors.append(f"Missing or invalid capability: {cap}")
    
    if "permissions" in manifest:
        perms = manifest["permissions"]
        if not isinstance(perms, dict):
            errors.append("Permissions must be an object")
        else:
            required_perms = ["data_access", "plugin_access", "system_access", "network_access"]
            for perm in required_perms:
                if perm not in perms or not isinstance(perms[perm], list):
                    errors.append(f"Missing or invalid permission: {perm}")
    
    if "resources" in manifest:
        resources = manifest["resources"]
        if not isinstance(resources, dict):
            errors.append("Resources must be an object")
        else:
            required_resources = ["max_memory_mb", "max_cpu_percent", "max_disk_mb"]
            for resource in required_resources:
                if resource not in resources:
                    errors.append(f"Missing resource limit: {resource}")
                elif not isinstance(resources[resource], (int, float)) or resources[resource] <= 0:
                    errors.append(f"Invalid resource limit for {resource}")
    
    return errors


def get_template_files() -> Dict[str, Dict[str, str]]:
    """Get template files for different extension types."""
    return {
        "basic": {
            "__init__.py": '''"""
Basic Extension Template
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext
from typing import Optional, Dict, Any
from fastapi import APIRouter


class BasicExtension(BaseExtension):
    """Basic extension with API and UI capabilities."""
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        self.logger.info("Basic extension initialized")
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        self.logger.info("Basic extension shutdown")
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router."""
        from .api.routes import router
        return router
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components."""
        return {
            "dashboard": {
                "name": "Basic Dashboard",
                "path": "/basic",
                "component": "BasicDashboard"
            }
        }


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> BasicExtension:
    """Create extension instance."""
    return BasicExtension(manifest, context)
''',
            "api/routes.py": '''"""
API routes for basic extension.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get extension status."""
    return {"status": "active", "extension": "basic"}
''',
            "tests/test_extension.py": '''"""
Tests for basic extension.
"""

import pytest


def test_extension_creation():
    """Test extension can be created."""
    assert True
'''
        }
    }


def print_colored(text: str, color: str = "white") -> None:
    """Print colored text to console."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    color_code = colors.get(color.lower(), colors["white"])
    reset_code = colors["reset"]
    print(f"{color_code}{text}{reset_code}")


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        if not response:
            return default
        return response in ["y", "yes", "true", "1"]
    except (KeyboardInterrupt, EOFError):
        return False