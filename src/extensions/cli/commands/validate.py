"""
Validate command for extension validation and testing.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .base import BaseCommand


class ValidateCommand(BaseCommand):
    """Command to validate extension manifest and structure."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add validate command arguments."""
        parser.add_argument(
            "path",
            type=Path,
            help="Path to extension directory"
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Enable strict validation mode"
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix common issues automatically"
        )
        parser.add_argument(
            "--output-format",
            choices=["text", "json"],
            default="text",
            help="Output format for validation results"
        )
    
    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the validate command."""
        extension_path = args.path
        
        if not extension_path.exists():
            ValidateCommand.print_error(f"Extension path '{extension_path}' does not exist")
            return 1
        
        if not extension_path.is_dir():
            ValidateCommand.print_error(f"Extension path '{extension_path}' is not a directory")
            return 1
        
        try:
            # Run validation
            results = ValidateCommand._validate_extension(extension_path, args.strict)
            
            # Apply fixes if requested
            if args.fix and results["fixable_issues"]:
                ValidateCommand._apply_fixes(extension_path, results["fixable_issues"])
                # Re-validate after fixes
                results = ValidateCommand._validate_extension(extension_path, args.strict)
            
            # Output results
            if args.output_format == "json":
                print(json.dumps(results, indent=2))
            else:
                ValidateCommand._print_validation_results(results)
            
            # Return appropriate exit code
            if results["errors"]:
                return 1
            elif results["warnings"] and args.strict:
                return 1
            else:
                return 0
                
        except Exception as e:
            ValidateCommand.print_error(f"Validation failed: {e}")
            return 1
    
    @staticmethod
    def _validate_extension(extension_path: Path, strict: bool = False) -> Dict[str, Any]:
        """Validate extension and return results."""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "fixable_issues": []
        }
        
        # Check manifest file
        manifest_results = ValidateCommand._validate_manifest(extension_path)
        results["errors"].extend(manifest_results["errors"])
        results["warnings"].extend(manifest_results["warnings"])
        results["fixable_issues"].extend(manifest_results["fixable_issues"])
        
        # Check directory structure
        structure_results = ValidateCommand._validate_structure(extension_path)
        results["errors"].extend(structure_results["errors"])
        results["warnings"].extend(structure_results["warnings"])
        results["fixable_issues"].extend(structure_results["fixable_issues"])
        
        # Check Python files
        python_results = ValidateCommand._validate_python_files(extension_path)
        results["errors"].extend(python_results["errors"])
        results["warnings"].extend(python_results["warnings"])
        
        # Check dependencies
        deps_results = ValidateCommand._validate_dependencies(extension_path)
        results["errors"].extend(deps_results["errors"])
        results["warnings"].extend(deps_results["warnings"])
        
        # Check permissions and security
        security_results = ValidateCommand._validate_security(extension_path)
        results["errors"].extend(security_results["errors"])
        results["warnings"].extend(security_results["warnings"])
        
        # Set overall validity
        results["valid"] = len(results["errors"]) == 0 and (not strict or len(results["warnings"]) == 0)
        
        return results
    
    @staticmethod
    def _validate_manifest(extension_path: Path) -> Dict[str, List[str]]:
        """Validate extension manifest file."""
        results = {"errors": [], "warnings": [], "fixable_issues": []}
        
        manifest_path = extension_path / "extension.json"
        
        # Check if manifest exists
        if not manifest_path.exists():
            results["errors"].append("Missing extension.json manifest file")
            results["fixable_issues"].append("create_manifest")
            return results
        
        try:
            # Load and parse manifest
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # Required fields
            required_fields = [
                "name", "version", "display_name", "description", "author",
                "api_version", "capabilities", "permissions", "resources"
            ]
            
            for field in required_fields:
                if field not in manifest:
                    results["errors"].append(f"Missing required field: {field}")
            
            # Validate name format
            if "name" in manifest:
                name = manifest["name"]
                if not ValidateCommand._is_valid_extension_name(name):
                    results["errors"].append(
                        f"Invalid extension name '{name}'. Use lowercase letters, numbers, and hyphens only."
                    )
            
            # Validate version format
            if "version" in manifest:
                version = manifest["version"]
                if not ValidateCommand._is_valid_version(version):
                    results["warnings"].append(f"Version '{version}' doesn't follow semantic versioning")
            
            # Validate capabilities
            if "capabilities" in manifest:
                caps = manifest["capabilities"]
                required_caps = ["provides_ui", "provides_api", "provides_background_tasks", "provides_webhooks"]
                for cap in required_caps:
                    if cap not in caps:
                        results["warnings"].append(f"Missing capability declaration: {cap}")
            
            # Validate permissions
            if "permissions" in manifest:
                perms = manifest["permissions"]
                required_perms = ["data_access", "plugin_access", "system_access", "network_access"]
                for perm in required_perms:
                    if perm not in perms:
                        results["warnings"].append(f"Missing permission declaration: {perm}")
            
            # Validate resources
            if "resources" in manifest:
                resources = manifest["resources"]
                required_resources = ["max_memory_mb", "max_cpu_percent", "max_disk_mb"]
                for resource in required_resources:
                    if resource not in resources:
                        results["warnings"].append(f"Missing resource limit: {resource}")
                    elif not isinstance(resources[resource], (int, float)) or resources[resource] <= 0:
                        results["errors"].append(f"Invalid resource limit for {resource}")
            
        except json.JSONDecodeError as e:
            results["errors"].append(f"Invalid JSON in manifest: {e}")
        except Exception as e:
            results["errors"].append(f"Error reading manifest: {e}")
        
        return results
    
    @staticmethod
    def _validate_structure(extension_path: Path) -> Dict[str, List[str]]:
        """Validate extension directory structure."""
        results = {"errors": [], "warnings": [], "fixable_issues": []}
        
        # Check for main __init__.py
        if not (extension_path / "__init__.py").exists():
            results["errors"].append("Missing main __init__.py file")
            results["fixable_issues"].append("create_init")
        
        # Check for tests directory
        if not (extension_path / "tests").exists():
            results["warnings"].append("Missing tests directory")
            results["fixable_issues"].append("create_tests_dir")
        
        # Check for README
        readme_files = ["README.md", "README.rst", "README.txt"]
        if not any((extension_path / readme).exists() for readme in readme_files):
            results["warnings"].append("Missing README file")
            results["fixable_issues"].append("create_readme")
        
        return results
    
    @staticmethod
    def _validate_python_files(extension_path: Path) -> Dict[str, List[str]]:
        """Validate Python files in the extension."""
        results = {"errors": [], "warnings": []}
        
        # Find all Python files
        python_files = list(extension_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                # Basic syntax check
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Try to compile the file
                compile(content, str(py_file), "exec")
                
            except SyntaxError as e:
                results["errors"].append(f"Syntax error in {py_file.relative_to(extension_path)}: {e}")
            except Exception as e:
                results["warnings"].append(f"Could not validate {py_file.relative_to(extension_path)}: {e}")
        
        return results
    
    @staticmethod
    def _validate_dependencies(extension_path: Path) -> Dict[str, List[str]]:
        """Validate extension dependencies."""
        results = {"errors": [], "warnings": []}
        
        # Check if requirements.txt exists for complex extensions
        requirements_path = extension_path / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, "r", encoding="utf-8") as f:
                    requirements = f.read().strip()
                if requirements:
                    results["info"] = [f"Found {len(requirements.splitlines())} dependencies"]
            except Exception as e:
                results["warnings"].append(f"Could not read requirements.txt: {e}")
        
        return results
    
    @staticmethod
    def _validate_security(extension_path: Path) -> Dict[str, List[str]]:
        """Validate security aspects of the extension."""
        results = {"errors": [], "warnings": []}
        
        # Check for potentially dangerous imports
        dangerous_imports = ["os.system", "subprocess.call", "eval", "exec"]
        python_files = list(extension_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                for dangerous in dangerous_imports:
                    if dangerous in content:
                        results["warnings"].append(
                            f"Potentially dangerous import '{dangerous}' found in {py_file.relative_to(extension_path)}"
                        )
            except Exception:
                pass  # Skip files that can't be read
        
        return results
    
    @staticmethod
    def _apply_fixes(extension_path: Path, fixable_issues: List[str]) -> None:
        """Apply automatic fixes for common issues."""
        for issue in fixable_issues:
            try:
                if issue == "create_init":
                    ValidateCommand._create_basic_init(extension_path)
                elif issue == "create_tests_dir":
                    (extension_path / "tests").mkdir(exist_ok=True)
                    (extension_path / "tests" / "__init__.py").touch()
                elif issue == "create_readme":
                    ValidateCommand._create_basic_readme(extension_path)
                elif issue == "create_manifest":
                    ValidateCommand._create_basic_manifest(extension_path)
            except Exception as e:
                ValidateCommand.print_warning(f"Could not fix {issue}: {e}")
    
    @staticmethod
    def _create_basic_init(extension_path: Path) -> None:
        """Create a basic __init__.py file."""
        extension_name = extension_path.name
        class_name = "".join(word.capitalize() for word in extension_name.split("-"))
        
        content = f'''"""
{extension_name.replace("-", " ").title()} Extension
"""

from src.extensions.base import BaseExtension
from src.extensions.models import ExtensionManifest, ExtensionContext


class {class_name}Extension(BaseExtension):
    """Main extension class."""
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        pass
    
    async def shutdown(self) -> None:
        """Cleanup extension resources."""
        pass


def create_extension(manifest: ExtensionManifest, context: ExtensionContext) -> {class_name}Extension:
    """Create and return the extension instance."""
    return {class_name}Extension(manifest, context)
'''
        
        with open(extension_path / "__init__.py", "w", encoding="utf-8") as f:
            f.write(content)
    
    @staticmethod
    def _create_basic_readme(extension_path: Path) -> None:
        """Create a basic README file."""
        extension_name = extension_path.name
        
        content = f'''# {extension_name.replace("-", " ").title()} Extension

A custom extension for the Kari AI platform.

## Installation

1. Place this extension in the `extensions/` directory
2. Restart the Kari platform
3. The extension will be automatically discovered and loaded

## Usage

[Add usage instructions here]

## License

[Add license information here]
'''
        
        with open(extension_path / "README.md", "w", encoding="utf-8") as f:
            f.write(content)
    
    @staticmethod
    def _create_basic_manifest(extension_path: Path) -> None:
        """Create a basic manifest file."""
        extension_name = extension_path.name
        
        manifest = {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": extension_name.replace("-", " ").title(),
            "description": f"A custom extension: {extension_name}",
            "author": "Extension Developer",
            "license": "MIT",
            "category": "custom",
            "tags": ["custom"],
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": False,
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
                "data_access": [],
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
                "control_room_pages": [],
                "streamlit_pages": []
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
                "categories": ["custom"],
                "keywords": [extension_name]
            }
        }
        
        with open(extension_path / "extension.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    @staticmethod
    def _print_validation_results(results: Dict[str, Any]) -> None:
        """Print validation results in a human-readable format."""
        if results["valid"]:
            ValidateCommand.print_success("Extension validation passed!")
        else:
            ValidateCommand.print_error("Extension validation failed!")
        
        if results["errors"]:
            print("\n❌ Errors:")
            for error in results["errors"]:
                print(f"  • {error}")
        
        if results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in results["warnings"]:
                print(f"  • {warning}")
        
        if results["info"]:
            print("\nℹ️  Information:")
            for info in results["info"]:
                print(f"  • {info}")
        
        if results["fixable_issues"]:
            print(f"\n🔧 {len(results['fixable_issues'])} issues can be automatically fixed with --fix")
    
    @staticmethod
    def _is_valid_extension_name(name: str) -> bool:
        """Validate extension name format."""
        import re
        return bool(re.match(r"^[a-z0-9-]+$", name))
    
    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Validate semantic version format."""
        import re
        return bool(re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$", version))