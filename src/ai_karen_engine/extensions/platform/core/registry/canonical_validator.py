"""
Canonical Structure Validator for Karen Plugin System

This module enforces the canonical plugin structure defined in the authority model.
It validates that all plugins follow the standardized path structure and manifest locations.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationResultType(Enum):
    """Types of validation results."""

    STRUCTURE = "structure"
    MANIFEST = "manifest"
    CATEGORY = "category"
    PATH = "path"
    CONTENT = "content"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    plugin_id: str
    severity: ValidationSeverity
    type: ValidationResultType
    message: str
    path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class PluginValidationReport:
    """Complete validation report for a plugin."""

    plugin_id: str
    category: str
    canonical_path: str
    is_valid: bool
    errors: List[ValidationResult]
    warnings: List[ValidationResult]
    infos: List[ValidationResult]


class CanonicalStructureValidator:
    """Validates that plugins follow the canonical structure."""

    # Valid categories according to authority model
    VALID_CATEGORIES = {"plugins", "sys_extensions", "channels"}

    # Required canonical paths
    CANONICAL_PATHS = {
        "root_manifest": "plugin_manifest.json",
        "gui_manifest": "manifest.json",
        "entry_file": "{plugin_name}.tsx",
        "prompts": "prompts/prompt.json",
        "plugin_dir": "./",
    }

    def __init__(self, extensions_root: str = "src/ai_karen_engine/extensions/plugins"):
        self.extensions_root = Path(extensions_root)
        self.validation_reports: Dict[str, PluginValidationReport] = {}

    def validate_plugin_category(self, category: str) -> bool:
        """Validate that a category is allowed."""
        return category in self.VALID_CATEGORIES

    def get_canonical_path(
        self, category: str, plugin_name: str, path_type: str
    ) -> Path:
        """Get the canonical path for a given path type."""
        if path_type not in self.CANONICAL_PATHS:
            raise ValueError(f"Unknown path type: {path_type}")

        template = self.CANONICAL_PATHS[path_type]
        relative_path = template.replace("{plugin_name}", plugin_name)
        return self.extensions_root / plugin_name / relative_path

    def validate_manifest_structure(
        self, manifest_path: Path, is_gui_manifest: bool = False
    ) -> List[ValidationResult]:
        """Validate the structure and content of a manifest file."""
        results = []

        if not manifest_path.exists():
            results.append(
                ValidationResult(
                    plugin_id=manifest_path.parent.name,
                    severity=ValidationSeverity.ERROR,
                    type=ValidationResultType.MANIFEST,
                    message=f"Manifest file not found: {manifest_path}",
                    path=str(manifest_path),
                    suggestion=f"Create {manifest_path} with proper manifest structure",
                )
            )
            return results

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            results.append(
                ValidationResult(
                    plugin_id=manifest_path.parent.name,
                    severity=ValidationSeverity.ERROR,
                    type=ValidationResultType.MANIFEST,
                    message=f"Invalid JSON in manifest: {e}",
                    path=str(manifest_path),
                    suggestion="Fix JSON syntax errors",
                )
            )
            return results

        # Validate required fields
        required_fields = ["id", "name", "version"]
        if is_gui_manifest:
            required_fields.extend(["plugin_id", "category", "gui_manifest_version"])

        for field in required_fields:
            if field not in manifest:
                results.append(
                    ValidationResult(
                        plugin_id=manifest_path.parent.name,
                        severity=ValidationSeverity.ERROR,
                        type=ValidationResultType.MANIFEST,
                        message=f"Missing required field '{field}' in manifest",
                        path=str(manifest_path),
                        suggestion=f"Add '{field}' field to manifest",
                    )
                )

        # Validate category consistency
        if "category" in manifest:
            if not self.validate_plugin_category(manifest["category"]):
                results.append(
                    ValidationResult(
                        plugin_id=manifest_path.parent.name,
                        severity=ValidationSeverity.ERROR,
                        type=ValidationResultType.CATEGORY,
                        message=f"Invalid category '{manifest['category']}'",
                        path=str(manifest_path),
                        suggestion=f"Use one of: {', '.join(self.VALID_CATEGORIES)}",
                    )
                )

        return results

    def validate_plugin_structure(
        self, category: str, plugin_name: str
    ) -> PluginValidationReport:
        """Validate the complete structure of a plugin."""
        # Handle category to avoid double "plugins" in path
        if category == "plugins":
            canonical_path = self.extensions_root / plugin_name
        else:
            canonical_path = self.extensions_root / category / plugin_name

        # Initialize report
        report = PluginValidationReport(
            plugin_id=plugin_name,
            category=category,
            canonical_path=str(canonical_path),
            is_valid=True,
            errors=[],
            warnings=[],
            infos=[],
        )

        # Validate category first
        if not self.validate_plugin_category(category):
            report.errors.append(
                ValidationResult(
                    plugin_id=plugin_name,
                    severity=ValidationSeverity.ERROR,
                    type=ValidationResultType.CATEGORY,
                    message=f"Invalid category '{category}'",
                    path=str(canonical_path),
                    suggestion=f"Use one of: {', '.join(self.VALID_CATEGORIES)}",
                )
            )
            report.is_valid = False
            return report

        # Check if plugin directory exists
        if not canonical_path.exists():
            report.errors.append(
                ValidationResult(
                    plugin_id=plugin_name,
                    severity=ValidationSeverity.ERROR,
                    type=ValidationResultType.STRUCTURE,
                    message=f"Plugin directory not found: {canonical_path}",
                    path=str(canonical_path),
                    suggestion="Create plugin directory at canonical location",
                )
            )
            report.is_valid = False
            return report

        # Validate root manifest
        root_manifest_path = self.get_canonical_path(
            category, plugin_name, "root_manifest"
        )
        manifest_results = self.validate_manifest_structure(root_manifest_path)
        report.errors.extend(
            [r for r in manifest_results if r.severity == ValidationSeverity.ERROR]
        )
        report.warnings.extend(
            [r for r in manifest_results if r.severity == ValidationSeverity.WARNING]
        )
        report.infos.extend(
            [r for r in manifest_results if r.severity == ValidationSeverity.INFO]
        )

        # Validate GUI manifest if it exists
        gui_manifest_path = self.get_canonical_path(
            category, plugin_name, "gui_manifest"
        )
        if gui_manifest_path.exists():
            gui_results = self.validate_manifest_structure(
                gui_manifest_path, is_gui_manifest=True
            )
            report.errors.extend(
                [r for r in gui_results if r.severity == ValidationSeverity.ERROR]
            )
            report.warnings.extend(
                [r for r in gui_results if r.severity == ValidationSeverity.WARNING]
            )
            report.infos.extend(
                [r for r in gui_results if r.severity == ValidationSeverity.INFO]
            )

        # Validate entry file if GUI manifest exists
        if gui_manifest_path.exists():
            entry_file_path = self.get_canonical_path(
                category, plugin_name, "entry_file"
            )
            if not entry_file_path.exists():
                report.warnings.append(
                    ValidationResult(
                        plugin_id=plugin_name,
                        severity=ValidationSeverity.WARNING,
                        type=ValidationResultType.STRUCTURE,
                        message=f"Entry file not found: {entry_file_path}",
                        path=str(entry_file_path),
                        suggestion="Create entry file for GUI component",
                    )
                )

        # Validate prompts location
        prompts_path = self.get_canonical_path(category, plugin_name, "prompts")
        if prompts_path.exists():
            prompt_json_path = prompts_path / "prompt.json"
            if not prompt_json_path.exists():
                report.warnings.append(
                    ValidationResult(
                        plugin_id=plugin_name,
                        severity=ValidationSeverity.WARNING,
                        type=ValidationResultType.STRUCTURE,
                        message=f"Prompt file not found: {prompt_json_path}",
                        path=str(prompt_json_path),
                        suggestion="Create prompt.json in prompts directory",
                    )
                )

        # Update overall validity
        report.is_valid = len(report.errors) == 0

        # Store report
        self.validation_reports[plugin_name] = report

        return report

    def validate_all_plugins(self) -> Dict[str, PluginValidationReport]:
        """Validate all plugins in the extensions directory."""
        all_reports = {}

        # Check each plugin directory directly under extensions_root
        for plugin_dir in self.extensions_root.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("."):
                plugin_name = plugin_dir.name

                # Extract category from manifest if possible, else default to "plugins"
                category = "plugins"
                manifest_path = plugin_dir / "plugin_manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        category = manifest.get("category", "plugins")
                    except Exception:
                        pass

                report = self.validate_plugin_structure(category, plugin_name)
                all_reports[plugin_name] = report

        return all_reports

    def get_validation_summary(self) -> Dict[str, Union[int, List[str]]]:
        """Get a summary of all validation results."""
        total_plugins = len(self.validation_reports)
        valid_plugins = sum(
            1 for report in self.validation_reports.values() if report.is_valid
        )
        invalid_plugins = total_plugins - valid_plugins

        errors = []
        warnings = []
        infos = []

        for report in self.validation_reports.values():
            for error in report.errors:
                errors.append(f"{report.plugin_id}: {error.message}")
            for warning in report.warnings:
                warnings.append(f"{report.plugin_id}: {warning.message}")
            for info in report.infos:
                infos.append(f"{report.plugin_id}: {info.message}")

        return {
            "total_plugins": total_plugins,
            "valid_plugins": valid_plugins,
            "invalid_plugins": invalid_plugins,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
        }

    def fix_canonical_structure(self, category: str, plugin_name: str) -> bool:
        """Attempt to fix canonical structure issues for a plugin."""
        canonical_path = self.extensions_root / plugin_name
        fixed_issues = 0

        # Ensure plugin directory exists
        if not canonical_path.exists():
            canonical_path.mkdir(parents=True, exist_ok=True)
            fixed_issues += 1

        # Create root manifest if missing
        root_manifest_path = self.get_canonical_path(
            "plugins", plugin_name, "root_manifest"
        )
        if not root_manifest_path.exists():
            basic_manifest = {
                "id": plugin_name,
                "name": plugin_name,
                "version": "1.0.0",
                "category": "plugins",
                "display_name": plugin_name.replace("-", " ").title(),
                "description": f"Auto-generated manifest for {plugin_name}",
                "extension_type": "tool_plugin",
                "source_type": "local",
                "entrypoint": "handler:MainExtension",
                "capabilities": {
                    "provides_ui": False,
                    "provides_api": True,
                    "provides_background_tasks": False,
                    "provides_webhooks": False,
                },
                "permissions": {
                    "memory_read": False,
                    "memory_write": False,
                    "tools": [],
                    "user_data_read": False,
                    "user_data_write": False,
                    "system_config_read": False,
                    "system_config_write": False,
                    "data_access": [],
                    "plugin_access": [],
                    "system_access": [],
                    "network_access": [],
                },
                "rbac": {
                    "allowed_roles": ["user", "admin", "developer"],
                    "default_enabled": True,
                },
                "dependencies": {
                    "plugins": [],
                    "extensions": [],
                    "system_services": [],
                },
            }

            with open(root_manifest_path, "w", encoding="utf-8") as f:
                json.dump(basic_manifest, f, indent=2)
            fixed_issues += 1

        # Create prompts directory and prompt file if missing
        prompts_path = self.get_canonical_path(category, plugin_name, "prompts")
        prompts_path.mkdir(exist_ok=True)

        prompt_json_path = prompts_path / "prompt.json"
        if not prompt_json_path.exists():
            basic_prompt = {
                "system_prompt": f"You are a {plugin_name} plugin. Help users with their requests.",
                "user_prompt": "Please help me with my request.",
                "examples": [],
            }

            with open(prompt_json_path, "w", encoding="utf-8") as f:
                json.dump(basic_prompt, f, indent=2)
            fixed_issues += 1

        return fixed_issues > 0


# Global validator instance
_validator: Optional[CanonicalStructureValidator] = None


def get_validator() -> CanonicalStructureValidator:
    """Get the global validator instance."""
    global _validator
    if _validator is None:
        _validator = CanonicalStructureValidator()
    return _validator


def validate_plugin(category: str, plugin_name: str) -> PluginValidationReport:
    """Validate a single plugin."""
    validator = get_validator()
    return validator.validate_plugin_structure(category, plugin_name)


def validate_all_plugins() -> Dict[str, PluginValidationReport]:
    """Validate all plugins."""
    validator = get_validator()
    return validator.validate_all_plugins()


def get_validation_summary() -> Dict[str, Union[int, List[str]]]:
    """Get validation summary."""
    validator = get_validator()
    return validator.get_validation_summary()


def fix_plugin_structure(category: str, plugin_name: str) -> bool:
    """Fix canonical structure for a plugin."""
    validator = get_validator()
    return validator.fix_canonical_structure(category, plugin_name)
