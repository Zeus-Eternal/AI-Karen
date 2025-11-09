"""
Extension validator for compliance and best practices.
"""

import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception


class ExtensionValidator:
    """Validates extensions for compliance and best practices."""
    
    def __init__(self, config):
        self.config = config
        self.manifest_schema = self._get_manifest_schema()
    
    def validate_extension(self, extension_path: Path) -> Dict[str, Any]:
        """
        Validate an extension for compliance and best practices.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 100,
            "checks": {}
        }
        
        # Check required files
        self._check_required_files(extension_path, results)
        
        # Validate manifest
        self._validate_manifest(extension_path, results)
        
        # Check code quality
        self._check_code_quality(extension_path, results)
        
        # Check security
        self._check_security(extension_path, results)
        
        # Check documentation
        self._check_documentation(extension_path, results)
        
        # Check tests
        self._check_tests(extension_path, results)
        
        # Calculate final score
        results["score"] = max(0, results["score"] - len(results["errors"]) * 10 - len(results["warnings"]) * 5)
        results["valid"] = len(results["errors"]) == 0
        
        return results
    
    def _check_required_files(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Check for required files."""
        required_files = [
            "extension.json",
            "__init__.py",
            "README.md",
            "requirements.txt"
        ]
        
        missing_files = []
        for file_name in required_files:
            if not (extension_path / file_name).exists():
                missing_files.append(file_name)
        
        if missing_files:
            results["errors"].append(f"Missing required files: {', '.join(missing_files)}")
        
        results["checks"]["required_files"] = {
            "passed": len(missing_files) == 0,
            "missing": missing_files
        }
    
    def _validate_manifest(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Validate extension manifest."""
        manifest_path = extension_path / "extension.json"
        
        if not manifest_path.exists():
            results["errors"].append("extension.json not found")
            return
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Validate against schema if jsonschema is available
            if JSONSCHEMA_AVAILABLE:
                validate(instance=manifest, schema=self.manifest_schema)
            else:
                print("⚠️  JSON schema validation not available (jsonschema not installed)")
            
            # Additional validation checks
            self._validate_manifest_content(manifest, results)
            
            results["checks"]["manifest"] = {
                "passed": True,
                "manifest": manifest
            }
            
        except json.JSONDecodeError as e:
            results["errors"].append(f"Invalid JSON in extension.json: {e}")
        except ValidationError as e:
            results["errors"].append(f"Manifest validation error: {e.message}")
        except Exception as e:
            results["errors"].append(f"Manifest validation failed: {e}")
    
    def _validate_manifest_content(self, manifest: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Validate manifest content for best practices."""
        # Check version format
        version = manifest.get("version", "")
        if not re.match(r'^\d+\.\d+\.\d+', version):
            results["warnings"].append("Version should follow semantic versioning (x.y.z)")
        
        # Check description length
        description = manifest.get("description", "")
        if len(description) < 20:
            results["warnings"].append("Description should be at least 20 characters")
        
        # Check required fields
        required_fields = ["name", "version", "description", "author"]
        for field in required_fields:
            if not manifest.get(field):
                results["errors"].append(f"Missing required field in manifest: {field}")
        
        # Check permissions
        permissions = manifest.get("permissions", {})
        if not permissions:
            results["warnings"].append("No permissions declared - consider if extension needs any")
    
    def _check_code_quality(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Check code quality."""
        python_files = list(extension_path.rglob("*.py"))
        
        issues = []
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to check for syntax errors
                ast.parse(content)
                
                # Check for basic code quality issues
                if "print(" in content and "test" not in str(py_file):
                    issues.append(f"{py_file.name}: Uses print() instead of logging")
                
                if "TODO" in content:
                    results["warnings"].append(f"{py_file.name}: Contains TODO comments")
                
                # Check for proper imports
                if "from src.core.extensions" not in content and "__init__.py" in str(py_file):
                    results["warnings"].append(f"{py_file.name}: Should import from extension framework")
                
            except SyntaxError as e:
                results["errors"].append(f"Syntax error in {py_file.name}: {e}")
            except Exception as e:
                results["warnings"].append(f"Could not analyze {py_file.name}: {e}")
        
        results["checks"]["code_quality"] = {
            "passed": len(issues) == 0,
            "issues": issues,
            "files_checked": len(python_files)
        }
    
    def _check_security(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Check for security issues."""
        security_issues = []
        
        # Check for dangerous imports
        dangerous_imports = ["os.system", "subprocess.call", "eval", "exec"]
        python_files = list(extension_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for dangerous in dangerous_imports:
                    if dangerous in content:
                        security_issues.append(f"{py_file.name}: Uses potentially dangerous {dangerous}")
                
                # Check for hardcoded secrets
                if re.search(r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    security_issues.append(f"{py_file.name}: Possible hardcoded secret")
                
            except Exception as e:
                results["warnings"].append(f"Could not security scan {py_file.name}: {e}")
        
        if security_issues:
            results["errors"].extend(security_issues)
        
        results["checks"]["security"] = {
            "passed": len(security_issues) == 0,
            "issues": security_issues
        }
    
    def _check_documentation(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Check documentation quality."""
        readme_path = extension_path / "README.md"
        
        if not readme_path.exists():
            results["errors"].append("README.md is required")
            return
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Check README content
            required_sections = ["Description", "Installation", "Usage"]
            missing_sections = []
            
            for section in required_sections:
                if section.lower() not in readme_content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                results["warnings"].append(f"README missing sections: {', '.join(missing_sections)}")
            
            if len(readme_content) < 200:
                results["warnings"].append("README is quite short - consider adding more details")
            
            results["checks"]["documentation"] = {
                "passed": len(missing_sections) == 0,
                "missing_sections": missing_sections,
                "readme_length": len(readme_content)
            }
            
        except Exception as e:
            results["warnings"].append(f"Could not analyze README: {e}")
    
    def _check_tests(self, extension_path: Path, results: Dict[str, Any]) -> None:
        """Check test coverage and quality."""
        tests_dir = extension_path / "tests"
        
        if not tests_dir.exists():
            results["warnings"].append("No tests directory found")
            results["checks"]["tests"] = {"passed": False, "test_files": 0}
            return
        
        test_files = list(tests_dir.rglob("test_*.py"))
        
        if not test_files:
            results["warnings"].append("No test files found in tests directory")
        
        # Check test file quality
        test_issues = []
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "async def test_" not in content and "def test_" not in content:
                    test_issues.append(f"{test_file.name}: No test functions found")
                
                if "assert" not in content:
                    test_issues.append(f"{test_file.name}: No assertions found")
                
            except Exception as e:
                test_issues.append(f"Could not analyze {test_file.name}: {e}")
        
        if test_issues:
            results["warnings"].extend(test_issues)
        
        results["checks"]["tests"] = {
            "passed": len(test_files) > 0 and len(test_issues) == 0,
            "test_files": len(test_files),
            "issues": test_issues
        }
    
    def _get_manifest_schema(self) -> Dict[str, Any]:
        """Get JSON schema for extension manifest validation."""
        return {
            "type": "object",
            "required": ["name", "version", "description", "author"],
            "properties": {
                "name": {
                    "type": "string",
                    "pattern": "^[a-z0-9-]+$",
                    "minLength": 3,
                    "maxLength": 50
                },
                "version": {
                    "type": "string",
                    "pattern": r"^\d+\.\d+\.\d+.*$"
                },
                "display_name": {"type": "string"},
                "description": {
                    "type": "string",
                    "minLength": 10,
                    "maxLength": 500
                },
                "author": {"type": "string"},
                "license": {"type": "string"},
                "category": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "api_version": {"type": "string"},
                "kari_min_version": {"type": "string"},
                "capabilities": {
                    "type": "object",
                    "properties": {
                        "provides_ui": {"type": "boolean"},
                        "provides_api": {"type": "boolean"},
                        "provides_background_tasks": {"type": "boolean"},
                        "provides_webhooks": {"type": "boolean"}
                    }
                },
                "dependencies": {
                    "type": "object",
                    "properties": {
                        "plugins": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "extensions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "system_services": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "permissions": {
                    "type": "object",
                    "properties": {
                        "data_access": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["read", "write", "delete"]}
                        },
                        "plugin_access": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["execute"]}
                        },
                        "system_access": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["metrics", "logs", "config"]}
                        },
                        "network_access": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["inbound_http", "outbound_http", "websocket"]}
                        }
                    }
                },
                "resources": {
                    "type": "object",
                    "properties": {
                        "max_memory_mb": {"type": "integer", "minimum": 64, "maximum": 2048},
                        "max_cpu_percent": {"type": "integer", "minimum": 5, "maximum": 100},
                        "max_disk_mb": {"type": "integer", "minimum": 10, "maximum": 5120}
                    }
                },
                "ui": {"type": "object"},
                "api": {"type": "object"},
                "background_tasks": {"type": "array"},
                "marketplace": {"type": "object"}
            }
        }