#!/usr/bin/env python3
"""
Script to analyze web-search plugin validation issues.
"""

import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ai_karen_engine.extensions.platform.core.registry.validator import (
    ExtensionValidator,
)
from src.ai_karen_engine.extensions.platform.core.manifest import ExtensionManifest


def load_manifest(file_path: Path) -> dict:
    """Load manifest from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest_file(file_path: Path, manifest_name: str) -> None:
    """Validate a manifest file and report results."""
    print(f"\n{'=' * 60}")
    print(f"Validating {manifest_name}: {file_path}")
    print(f"{'=' * 60}")

    try:
        # Load manifest data
        manifest_data = load_manifest(file_path)
        print(f"✓ Manifest loaded successfully")

        # Show manifest structure
        print(f"\nManifest keys: {list(manifest_data.keys())}")

        # Try to create ExtensionManifest object
        try:
            manifest = ExtensionManifest.from_dict(manifest_data)
            print(f"✓ ExtensionManifest created successfully")
            print(f"  - Name: {manifest.name}")
            print(f"  - Version: {manifest.version}")
            print(f"  - Display Name: {manifest.display_name}")
            print(f"  - Category: {manifest.category}")
            print(f"  - API Version: {manifest.api_version}")
            print(f"  - Entrypoint: {manifest.entrypoint}")
        except Exception as e:
            print(f"✗ Failed to create ExtensionManifest: {e}")
            return

        # Validate using ExtensionValidator
        validator = ExtensionValidator()
        is_valid, errors, warnings = validator.validate_manifest(manifest)

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

        # Test enhanced validation
        print(f"\nEnhanced Validation:")
        is_valid_enhanced, errors_enhanced, warnings_enhanced, field_errors_enhanced = (
            validator.validate_manifest_enhanced(manifest_data)
        )
        print(f"  - Valid: {is_valid_enhanced}")
        print(f"  - Errors: {len(errors_enhanced)}")
        print(f"  - Warnings: {len(warnings_enhanced)}")
        print(f"  - Field Errors: {len(field_errors_enhanced)}")

        if errors_enhanced:
            print(f"\nEnhanced Errors:")
            for error in errors_enhanced:
                print(f"  ✗ {error}")

        if warnings_enhanced:
            print(f"\nEnhanced Warnings:")
            for warning in warnings_enhanced:
                print(f"  ⚠ {warning}")

        if field_errors_enhanced:
            print(f"\nField Errors:")
            for field_error in field_errors_enhanced:
                print(f"  ✗ {field_error}")

    except Exception as e:
        print(f"✗ Failed to validate {manifest_name}: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main analysis function."""
    print("Web-Search Plugin Validation Analysis")
    print("=" * 60)

    # Path to web-search plugin directory
    web_search_dir = (
        project_root
        / "src"
        / "ai_karen_engine"
        / "extensions"
        / "plugins"
        / "web-search"
    )

    if not web_search_dir.exists():
        print(f"✗ Web-search plugin directory not found: {web_search_dir}")
        return

    print(f"Analyzing web-search plugin directory: {web_search_dir}")

    # Check both manifest files
    plugin_manifest = web_search_dir / "plugin_manifest.json"
    manifest_json = web_search_dir / "manifest.json"

    # Test plugin_manifest.json
    if plugin_manifest.exists():
        validate_manifest_file(plugin_manifest, "plugin_manifest.json")
    else:
        print(f"✗ plugin_manifest.json not found")

    # Test manifest.json
    if manifest_json.exists():
        validate_manifest_file(manifest_json, "manifest.json")
    else:
        print(f"✗ manifest.json not found")

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
