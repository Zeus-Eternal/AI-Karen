#!/usr/bin/env python3
"""
Simple Web Search Plugin Manifest Validation Script
Tests both plugin_manifest.json and manifest.json files without full module dependencies
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

# Add the project root to Python path
project_root = Path(__file__).parent


# Simple validation functions
def validate_required_fields(
    manifest: Dict[str, Any], required_fields: List[str]
) -> List[str]:
    """Validate required fields are present."""
    errors = []
    for field in required_fields:
        if field not in manifest or not manifest[field]:
            errors.append(f"Missing required field: {field}")
    return errors


def validate_version_format(version: str) -> List[str]:
    """Validate version format (basic check)."""
    errors = []
    if not version:
        errors.append("Version is empty")
    elif not isinstance(version, str):
        errors.append("Version must be a string")
    elif not version.replace(".", "").isdigit() and not version.startswith("v"):
        errors.append(f"Invalid version format: {version}")
    return errors


def validate_name_format(name: str) -> List[str]:
    """Validate name format (kebab-case)."""
    errors = []
    if not name:
        errors.append("Name is empty")
    elif not isinstance(name, str):
        errors.append("Name must be a string")
    elif not name.replace("-", "").replace("_", "").isalnum():
        errors.append(f"Name should be kebab-case: {name}")
    return errors


def validate_capabilities(capabilities: Dict[str, Any]) -> List[str]:
    """Validate capabilities structure."""
    errors = []
    if not isinstance(capabilities, dict):
        errors.append("Capabilities must be a dictionary")
        return errors

    valid_caps = [
        "provides_ui",
        "provides_api",
        "provides_background_tasks",
        "provides_webhooks",
        "web_search",
        "prompt_first",
    ]
    for cap, value in capabilities.items():
        if cap not in valid_caps:
            errors.append(f"Unknown capability: {cap}")
        elif not isinstance(value, bool):
            errors.append(f"Capability '{cap}' must be boolean")

    return errors


def validate_ui_config(ui: Dict[str, Any]) -> List[str]:
    """Validate UI configuration."""
    errors = []
    if not isinstance(ui, dict):
        errors.append("UI configuration must be a dictionary")
        return errors

    # Check for hook zones
    if "hook_zones" in ui:
        hook_zones = ui["hook_zones"]
        if not isinstance(hook_zones, list):
            errors.append("hook_zones must be a list")
        else:
            for zone in hook_zones:
                if not isinstance(zone, dict):
                    errors.append("Each hook zone must be a dictionary")
                    continue
                if "zone" not in zone:
                    errors.append("hook_zone missing 'zone' field")
                if "label" not in zone:
                    errors.append("hook_zone missing 'label' field")

    # Check for menu
    if "menu" in ui:
        menu = ui["menu"]
        if not isinstance(menu, list):
            errors.append("menu must be a list")
        else:
            for item in menu:
                if not isinstance(item, dict):
                    errors.append("Each menu item must be a dictionary")
                    continue
                if "placement" not in item:
                    errors.append("menu item missing 'placement' field")
                if "label" not in item:
                    errors.append("menu item missing 'label' field")

    return errors


def validate_rbac(rbac: Dict[str, Any]) -> List[str]:
    """Validate RBAC configuration."""
    errors = []
    if not isinstance(rbac, dict):
        errors.append("RBAC configuration must be a dictionary")
        return errors

    if "allowed_roles" in rbac:
        roles = rbac["allowed_roles"]
        if not isinstance(roles, list):
            errors.append("allowed_roles must be a list")
        else:
            valid_roles = ["user", "admin", "developer", "guest"]
            for role in roles:
                if role not in valid_roles:
                    errors.append(f"Invalid role: {role}")

    return errors


def validate_settings(settings: Dict[str, Any]) -> List[str]:
    """Validate settings configuration."""
    errors = []
    if not isinstance(settings, dict):
        errors.append("Settings must be a dictionary")
        return errors

    if "modes" in settings:
        modes = settings["modes"]
        if not isinstance(modes, dict):
            errors.append("modes must be a dictionary")
        else:
            for mode_name, mode_config in modes.items():
                if not isinstance(mode_config, dict):
                    errors.append(
                        f"Mode '{mode_name}' configuration must be a dictionary"
                    )
                    continue

                # Validate mode-specific settings
                if mode_name in [
                    "general",
                    "news",
                    "docs",
                    "deep_research",
                    "structured_extract",
                    "stock_market",
                ]:
                    required_fields = ["display_name", "description"]
                    for field in required_fields:
                        if field not in mode_config:
                            errors.append(
                                f"Mode '{mode_name}' missing required field: {field}"
                            )

                elif mode_name == "weather":
                    required_fields = ["display_name", "description"]
                    for field in required_fields:
                        if field not in mode_config:
                            errors.append(
                                f"Mode '{mode_name}' missing required field: {field}"
                            )

    return errors


def validate_manifest_basic(
    manifest: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    """Basic manifest validation."""
    errors = []
    warnings = []

    # Required fields
    required_fields = [
        "name",
        "version",
        "display_name",
        "description",
        "author",
        "license",
        "category",
        "entrypoint",
    ]
    errors.extend(validate_required_fields(manifest, required_fields))

    # Validate specific fields
    if "name" in manifest:
        errors.extend(validate_name_format(manifest["name"]))

    if "version" in manifest:
        errors.extend(validate_version_format(manifest["version"]))

    # Validate capabilities
    if "capabilities" in manifest:
        errors.extend(validate_capabilities(manifest["capabilities"]))

    # Validate UI config
    if "ui" in manifest:
        errors.extend(validate_ui_config(manifest["ui"]))

    # Validate RBAC
    if "rbac" in manifest:
        errors.extend(validate_rbac(manifest["rbac"]))

    # Validate settings
    if "settings" in manifest:
        errors.extend(validate_settings(manifest["settings"]))

    # Check for potential discovery issues
    if "entrypoint" in manifest:
        entrypoint = manifest["entrypoint"]
        if not isinstance(entrypoint, str) or ":" not in entrypoint:
            warnings.append(
                "Entry point should be in format 'module:function' for better discoverability"
            )

        if "handler" in entrypoint and "MainExtension" not in entrypoint:
            warnings.append(
                "Entry point references 'handler' but 'MainExtension' not found - may indicate discovery issues"
            )

    if "category" in manifest and manifest["category"] != "plugins":
        warnings.append(
            f"Category is '{manifest['category']}' but expected 'plugins' for plugin discovery"
        )

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def load_manifest(file_path: Path) -> Dict[str, Any]:
    """Load a JSON manifest file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def print_validation_results(
    file_name: str, is_valid: bool, errors: List[str], warnings: List[str]
):
    """Print validation results."""
    print(f"\n{'=' * 60}")
    print(f"Validating {file_name}")
    print(f"{'=' * 60}")

    print(f"🔍 Validation Results:")
    print(f"   Valid: {'✅ YES' if is_valid else '❌ NO'}")

    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")


def main():
    """Main validation function."""
    print("🔍 Web Search Plugin Manifest Validation")
    print("=" * 60)

    # Define manifest paths
    plugin_manifest_path = (
        project_root
        / "src"
        / "ai_karen_engine"
        / "extensions"
        / "plugins"
        / "web-search"
        / "plugin_manifest.json"
    )
    manifest_path = (
        project_root
        / "src"
        / "ai_karen_engine"
        / "extensions"
        / "plugins"
        / "web-search"
        / "manifest.json"
    )

    # Load manifests
    plugin_manifest = load_manifest(plugin_manifest_path)
    manifest = load_manifest(manifest_path)

    if plugin_manifest is None or manifest is None:
        print("❌ Failed to load one or both manifest files")
        return 1

    # Validate both manifests
    plugin_valid, plugin_errors, plugin_warnings = validate_manifest_basic(
        plugin_manifest
    )
    manifest_valid, manifest_errors, manifest_warnings = validate_manifest_basic(
        manifest
    )

    # Print detailed results
    print_validation_results(
        "plugin_manifest.json", plugin_valid, plugin_errors, plugin_warnings
    )
    print_validation_results(
        "manifest.json", manifest_valid, manifest_errors, manifest_warnings
    )

    # Discovery analysis
    print(f"\n🎯 Plugin Discovery Analysis")
    print(f"{'=' * 60}")

    # Check for common discovery issues
    discovery_issues = []

    # Check plugin_manifest.json
    if plugin_manifest:
        # Check entrypoint format
        if "entrypoint" in plugin_manifest:
            entrypoint = plugin_manifest["entrypoint"]
            if ":" not in entrypoint:
                discovery_issues.append(
                    "plugin_manifest.json entrypoint format incorrect"
                )
            elif "handler" not in entrypoint:
                discovery_issues.append(
                    "plugin_manifest.json entrypoint doesn't reference handler module"
                )

        # Check for required fields
        required_discovery_fields = ["name", "category", "entrypoint"]
        for field in required_discovery_fields:
            if field not in plugin_manifest:
                discovery_issues.append(
                    f"plugin_manifest.json missing discovery field: {field}"
                )

        # Check category
        if plugin_manifest.get("category") != "plugins":
            discovery_issues.append(
                f"plugin_manifest.json category should be 'plugins', got '{plugin_manifest.get('category')}'"
            )

    # Check manifest.json
    if manifest:
        # Check for plugin_id
        if "plugin_id" not in manifest:
            discovery_issues.append("manifest.json missing plugin_id field")

        # Check category
        if manifest.get("category") != "plugins":
            discovery_issues.append(
                f"manifest.json category should be 'plugins', got '{manifest.get('category')}'"
            )

        # Check GUI manifest version
        if manifest.get("gui_manifest_version") not in ["1.0", "1.1"]:
            discovery_issues.append(
                f"manifest.json gui_manifest_version should be '1.0' or '1.1', got '{manifest.get('gui_manifest_version')}'"
            )

    if discovery_issues:
        print(f"\n🚨 Discovery Issues Found:")
        for issue in discovery_issues:
            print(f"   - {issue}")
        print(
            f"\n💡 These issues could prevent the plugin from being discovered properly!"
        )
    else:
        print(f"\n✅ No obvious discovery issues found!")

    # Summary
    print(f"\n🎯 Final Summary")
    print(f"{'=' * 60}")
    print(f"plugin_manifest.json: {'✅ VALID' if plugin_valid else '❌ INVALID'}")
    print(f"manifest.json: {'✅ VALID' if manifest_valid else '❌ INVALID'}")

    if not plugin_valid or not manifest_valid or discovery_issues:
        print(f"\n🚨 Issues found that could prevent plugin discovery!")
        print("Common discovery issues:")
        print("   - Missing required fields in manifest")
        print("   - Invalid entrypoint format")
        print("   - Incorrect category specification")
        print("   - Missing plugin_id in manifest.json")
        print("   - Invalid GUI manifest version")
        return 1
    else:
        print(f"\n✅ Both manifests appear valid for plugin discovery!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
