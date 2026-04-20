#!/usr/bin/env python3
"""
Manual validation analysis for web-search plugin manifest.
"""

import json
import re
from pathlib import Path


def load_manifest(file_path: Path):
    """Load manifest from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest_basic(manifest_data: dict) -> tuple[bool, list[str], list[str]]:
    """Basic validation without importing complex modules."""
    errors = []
    warnings = []

    # Required fields check
    required_fields = [
        "name",
        "version",
        "display_name",
        "description",
        "author",
        "license",
        "category",
    ]
    for field in required_fields:
        if field not in manifest_data or not manifest_data[field]:
            errors.append(f"Missing required field: {field}")

    # Name validation (kebab-case)
    name = manifest_data.get("name", "")
    if name and not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name):
        errors.append(
            f"Name '{name}' must be kebab-case (letters, numbers, hyphens only)"
        )

    # Version validation (semantic versioning)
    version = manifest_data.get("version", "")
    if version and not re.match(
        r"^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?(\+[a-zA-Z0-9-]+)?$", version
    ):
        errors.append(f"Version '{version}' must be semantic versioning (e.g., 1.0.0)")

    # Entrypoint validation
    entrypoint = manifest_data.get("entrypoint")
    if entrypoint and ":" not in entrypoint:
        errors.append(f"Entrypoint '{entrypoint}' must be in format 'module:ClassName'")

    # Category validation
    category = manifest_data.get("category", "")
    valid_categories = [
        "analytics",
        "automation",
        "communication",
        "development",
        "experimental",
        "integration",
        "productivity",
        "security",
    ]
    if category and category not in valid_categories:
        warnings.append(
            f"Category '{category}' is not standard. Consider: {', '.join(valid_categories)}"
        )

    # API version validation
    api_version = manifest_data.get("api_version", "1.0")
    supported_versions = ["1.0", "1.1", "2.0"]
    if api_version not in supported_versions:
        warnings.append(
            f"API version '{api_version}' not supported. Supported: {', '.join(supported_versions)}"
        )

    # Check for required structure
    if "capabilities" not in manifest_data:
        warnings.append("Missing 'capabilities' field")

    if "ui" not in manifest_data:
        warnings.append("Missing 'ui' field")

    # Check for missing required fields in UI
    ui = manifest_data.get("ui", {})
    if ui and "hook_zones" not in ui:
        warnings.append("UI configuration missing 'hook_zones'")

    return len(errors) == 0, errors, warnings


def main():
    """Main analysis function."""
    print("Web-Search Plugin Manual Validation Analysis")
    print("=" * 60)

    # Path to web-search plugin directory
    web_search_dir = Path("src/ai_karen_engine/extensions/plugins/web-search")

    if not web_search_dir.exists():
        print(f"✗ Web-search plugin directory not found: {web_search_dir}")
        return

    print(f"Analyzing web-search plugin directory: {web_search_dir}")

    # Check both manifest files
    plugin_manifest = web_search_dir / "plugin_manifest.json"
    manifest_json = web_search_dir / "manifest.json"

    # Test plugin_manifest.json
    if plugin_manifest.exists():
        print(f"\n{'=' * 60}")
        print("Analyzing plugin_manifest.json")
        print(f"{'=' * 60}")

        try:
            manifest_data = load_manifest(plugin_manifest)
            print(f"✓ Manifest loaded successfully")

            # Show manifest structure
            print(f"\nManifest keys: {list(manifest_data.keys())}")

            # Basic validation
            is_valid, errors, warnings = validate_manifest_basic(manifest_data)

            print(f"\nValidation Results:")
            print(f"  - Valid: {is_valid}")
            print(f"  - Errors: {len(errors)}")
            print(f"  - Warnings: {len(warnings)}")

            if errors:
                print(f"\nErrors:")
                for error in errors:
                    print(f"  ✗ {error}")

            if warnings:
                print(f"\nWarnings:")
                for warning in warnings:
                    print(f"  ⚠ {warning}")

        except Exception as e:
            print(f"✗ Failed to analyze plugin_manifest.json: {e}")

    # Test manifest.json
    if manifest_json.exists():
        print(f"\n{'=' * 60}")
        print("Analyzing manifest.json")
        print(f"{'=' * 60}")

        try:
            manifest_data = load_manifest(manifest_json)
            print(f"✓ Manifest loaded successfully")

            # Show manifest structure
            print(f"\nManifest keys: {list(manifest_data.keys())}")

            # Basic validation
            is_valid, errors, warnings = validate_manifest_basic(manifest_data)

            print(f"\nValidation Results:")
            print(f"  - Valid: {is_valid}")
            print(f"  - Errors: {len(errors)}")
            print(f"  - Warnings: {len(warnings)}")

            if errors:
                print(f"\nErrors:")
                for error in errors:
                    print(f"  ✗ {error}")

            if warnings:
                print(f"\nWarnings:")
                for warning in warnings:
                    print(f"  ⚠ {warning}")

        except Exception as e:
            print(f"✗ Failed to analyze manifest.json: {e}")

    # Check if both files exist (potential conflict)
    if plugin_manifest.exists() and manifest_json.exists():
        print(f"\n{'=' * 60}")
        print("MANIFEST CONFLICT DETECTED!")
        print(f"{'=' * 60}")
        print(f"Both manifest files exist in the web-search plugin directory:")
        print(f"  - {plugin_manifest}")
        print(f"  - {manifest_json}")
        print(
            f"\nThis could cause discovery issues as the system may pick the wrong file."
        )
        print(
            f"The discovery system prioritizes: plugin_manifest.json -> manifest.json"
        )


if __name__ == "__main__":
    main()
