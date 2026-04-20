#!/usr/bin/env python3
"""
Enhanced Web Search Plugin Manifest Validation Script
Tests both plugin_manifest.json and manifest.json files with format-specific validation
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

# Add the project root to Python path
project_root = Path(__file__).parent


def validate_plugin_manifest(
    manifest: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    """Validate plugin_manifest.json format."""
    errors = []
    warnings = []

    # Required fields for plugin_manifest.json
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
    for field in required_fields:
        if field not in manifest or not manifest[field]:
            errors.append(f"Missing required field: {field}")

    # Validate specific fields
    if "name" in manifest:
        if (
            not isinstance(manifest["name"], str)
            or not manifest["name"].replace("-", "").replace("_", "").isalnum()
        ):
            errors.append("Name should be kebab-case alphanumeric")

    if "version" in manifest:
        if (
            not isinstance(manifest["version"], str)
            or not manifest["version"].replace(".", "").replace("v", "").isdigit()
        ):
            errors.append("Version should be in format x.y.z or vx.y.z")

    if "category" in manifest and manifest["category"] != "plugins":
        warnings.append(f"Category should be 'plugins' for plugin discovery")

    if "entrypoint" in manifest:
        entrypoint = manifest["entrypoint"]
        if not isinstance(entrypoint, str) or ":" not in entrypoint:
            errors.append("Entry point should be in format 'module:function'")
        elif "handler" not in entrypoint:
            warnings.append(
                "Entry point should reference 'handler' module for discoverability"
            )

    # Validate capabilities
    if "capabilities" in manifest:
        caps = manifest["capabilities"]
        if not isinstance(caps, dict):
            errors.append("Capabilities must be a dictionary")
        else:
            for cap, value in caps.items():
                if not isinstance(value, bool):
                    errors.append(f"Capability '{cap}' must be boolean")

    # Validate UI configuration
    if "ui" in manifest:
        ui = manifest["ui"]
        if not isinstance(ui, dict):
            errors.append("UI configuration must be a dictionary")
        elif "hook_zones" in ui:
            zones = ui["hook_zones"]
            if not isinstance(zones, list):
                errors.append("hook_zones must be a list")
            else:
                for zone in zones:
                    if not isinstance(zone, dict):
                        errors.append("Each hook zone must be a dictionary")
                    elif "zone" not in zone or "label" not in zone:
                        errors.append("hook_zone must have 'zone' and 'label' fields")

    # Validate settings
    if "settings" in manifest:
        settings = manifest["settings"]
        if not isinstance(settings, dict):
            errors.append("Settings must be a dictionary")
        elif "modes" in settings:
            modes = settings["modes"]
            if not isinstance(modes, dict):
                errors.append("modes must be a dictionary")

    return len(errors) == 0, errors, warnings


def validate_manifest_json(
    manifest: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    """Validate manifest.json format (GUI manifest)."""
    errors = []
    warnings = []

    # Required fields for manifest.json
    required_fields = [
        "id",
        "plugin_id",
        "category",
        "gui_manifest_version",
        "display_name",
        "description",
        "version",
    ]
    for field in required_fields:
        if field not in manifest or not manifest[field]:
            errors.append(f"Missing required field: {field}")

    # Validate specific fields
    if "id" in manifest:
        if (
            not isinstance(manifest["id"], str)
            or not manifest["id"].replace("-", "").replace("_", "").isalnum()
        ):
            errors.append("ID should be kebab-case alphanumeric")

    if "plugin_id" in manifest:
        if (
            not isinstance(manifest["plugin_id"], str)
            or not manifest["plugin_id"].replace("-", "").replace("_", "").isalnum()
        ):
            errors.append("Plugin ID should be kebab-case alphanumeric")

    if "category" in manifest and manifest["category"] != "plugins":
        warnings.append(f"Category should be 'plugins' for plugin discovery")

    if "gui_manifest_version" in manifest:
        valid_versions = ["1.0", "1.1"]
        if manifest["gui_manifest_version"] not in valid_versions:
            errors.append(f"gui_manifest_version should be one of: {valid_versions}")

    # Validate modes array
    if "modes" in manifest:
        modes = manifest["modes"]
        if not isinstance(modes, list):
            errors.append("modes must be a list")
        else:
            valid_modes = [
                "general",
                "news",
                "docs",
                "deep_research",
                "structured_extract",
                "weather",
                "stock_market",
            ]
            for mode in modes:
                if mode not in valid_modes:
                    warnings.append(f"Unknown mode: {mode}")

    # Validate UI menu
    if "ui" in manifest and "menu" in manifest["ui"]:
        menu = manifest["ui"]["menu"]
        if not isinstance(menu, list):
            errors.append("menu must be a list")
        else:
            for item in menu:
                if not isinstance(item, dict):
                    errors.append("Each menu item must be a dictionary")
                elif "placement" not in item or "label" not in item:
                    errors.append("menu item must have 'placement' and 'label' fields")

    return len(errors) == 0, errors, warnings


def check_discovery_issues(
    plugin_manifest: Dict[str, Any], manifest: Dict[str, Any]
) -> List[str]:
    """Check for issues that could prevent plugin discovery."""
    discovery_issues = []

    # Check plugin_manifest.json for discovery issues
    if plugin_manifest:
        # Check entrypoint format
        if "entrypoint" in plugin_manifest:
            entrypoint = plugin_manifest["entrypoint"]
            if ":" not in entrypoint:
                discovery_issues.append(
                    "plugin_manifest.json entrypoint format incorrect - should be 'module:function'"
                )
            elif "handler" not in entrypoint:
                discovery_issues.append(
                    "plugin_manifest.json entrypoint doesn't reference 'handler' module"
                )

        # Check for required discovery fields
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

    # Check manifest.json for discovery issues
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
        gui_version = manifest.get("gui_manifest_version")
        if gui_version not in ["1.0", "1.1"]:
            discovery_issues.append(
                f"manifest.json gui_manifest_version should be '1.0' or '1.1', got '{gui_version}'"
            )

        # Check consistency between plugin_manifest and manifest
        if plugin_manifest and manifest:
            # Check name consistency
            plugin_name = plugin_manifest.get("name")
            manifest_id = manifest.get("id")
            if plugin_name and manifest_id and plugin_name != manifest_id:
                discovery_issues.append(
                    f"Name inconsistency: plugin_manifest='{plugin_name}' vs manifest.json='{manifest_id}'"
                )

            # Check version consistency
            plugin_version = plugin_manifest.get("version")
            manifest_version = manifest.get("version")
            if (
                plugin_version
                and manifest_version
                and plugin_version != manifest_version
            ):
                discovery_issues.append(
                    f"Version inconsistency: plugin_manifest='{plugin_version}' vs manifest.json='{manifest_version}'"
                )

    return discovery_issues


def load_manifest(file_path: Path) -> Dict[str, Any]:
    """Load a JSON manifest file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def print_validation_results(
    file_name: str,
    validation_type: str,
    is_valid: bool,
    errors: List[str],
    warnings: List[str],
):
    """Print validation results."""
    print(f"\n{'=' * 60}")
    print(f"Validating {file_name} ({validation_type})")
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

    # Validate both manifests with format-specific validation
    plugin_valid, plugin_errors, plugin_warnings = validate_plugin_manifest(
        plugin_manifest
    )
    manifest_valid, manifest_errors, manifest_warnings = validate_manifest_json(
        manifest
    )

    # Print detailed results
    print_validation_results(
        "plugin_manifest.json",
        "Plugin Manifest",
        plugin_valid,
        plugin_errors,
        plugin_warnings,
    )
    print_validation_results(
        "manifest.json",
        "GUI Manifest",
        manifest_valid,
        manifest_errors,
        manifest_warnings,
    )

    # Discovery analysis
    print(f"\n🎯 Plugin Discovery Analysis")
    print(f"{'=' * 60}")

    discovery_issues = check_discovery_issues(plugin_manifest, manifest)

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
        print("   - Inconsistencies between plugin_manifest.json and manifest.json")
        return 1
    else:
        print(f"\n✅ Both manifests appear valid for plugin discovery!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
