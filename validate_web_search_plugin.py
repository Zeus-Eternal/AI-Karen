#!/usr/bin/env python3
"""
Web Search Plugin Manifest Validation Script
Tests both plugin_manifest.json and manifest.json files
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ai_karen_engine.extensions.platform.core.registry.validator import (
    ExtensionValidator,
)


def load_manifest(file_path):
    """Load a JSON manifest file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def validate_manifest_file(manifest_data, file_name, validator):
    """Validate a manifest file and print results."""
    print(f"\n{'=' * 60}")
    print(f"Validating {file_name}")
    print(f"{'=' * 60}")

    if manifest_data is None:
        print("❌ Failed to load manifest file")
        return False

    print("📄 Manifest content preview:")
    print(
        json.dumps(manifest_data, indent=2)[:500] + "..."
        if len(json.dumps(manifest_data)) > 500
        else json.dumps(manifest_data, indent=2)
    )

    # Perform validation
    is_valid, errors, warnings = validator.validate_manifest(manifest_data)

    # Print validation results
    print(f"\n🔍 Validation Results:")
    print(f"   Valid: {'✅ YES' if is_valid else '❌ NO'}")

    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

    # Enhanced validation
    print(f"\n🚀 Enhanced Validation Results:")
    is_valid_enhanced, errors_enhanced, warnings_enhanced, field_errors_enhanced = (
        validator.validate_manifest_enhanced(manifest_data)
    )

    print(f"   Enhanced Valid: {'✅ YES' if is_valid_enhanced else '❌ NO'}")

    if errors_enhanced:
        print(f"\n❌ Enhanced Errors ({len(errors_enhanced)}):")
        for error in errors_enhanced:
            print(f"   - {error}")

    if warnings_enhanced:
        print(f"\n⚠️  Enhanced Warnings ({len(warnings_enhanced)}):")
        for warning in warnings_enhanced:
            print(f"   - {warning}")

    if field_errors_enhanced:
        print(f"\n📝 Field Errors ({len(field_errors_enhanced)}):")
        for fe in field_errors_enhanced:
            if hasattr(fe, "dict"):
                print(f"   - {fe.dict()}")
            else:
                print(f"   - {fe}")

    # Get comprehensive validation report
    print(f"\n📊 Validation Report:")
    print(f"{'=' * 60}")

    # Convert to ExtensionManifest for report generation
    try:
        from src.ai_karen_engine.extensions.manifest import ExtensionManifest

        manifest_model = ExtensionManifest.from_dict(manifest_data)
        report = validator.get_validation_report(manifest_model)

        print(f"Manifest: {report['manifest_name']} v{report['manifest_version']}")
        print(f"Overall Score: {report['summary']['overall_score']}/100")
        print(f"Errors: {report['summary']['total_errors']}")
        print(f"Warnings: {report['summary']['total_warnings']}")
        print(f"Recommendations: {report['summary']['total_recommendations']}")

        print(f"\n📋 Compatibility:")
        for key, value in report["compatibility"].items():
            status = "✅" if value else "❌"
            print(f"   {status} {key.replace('_', ' ').title()}")

        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"   - {rec}")

        return is_valid_enhanced

    except Exception as e:
        print(f"Error generating report: {e}")
        return is_valid_enhanced


def main():
    """Main validation function."""
    print("🔍 Web Search Plugin Manifest Validation")
    print("=" * 60)

    # Initialize validator
    validator = ExtensionValidator()

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

    # Validate both manifests
    plugin_valid = validate_manifest_file(
        plugin_manifest, "plugin_manifest.json", validator
    )
    manifest_valid = validate_manifest_file(manifest, "manifest.json", validator)

    # Summary
    print(f"\n🎯 Final Summary")
    print(f"{'=' * 60}")
    print(f"plugin_manifest.json: {'✅ VALID' if plugin_valid else '❌ INVALID'}")
    print(f"manifest.json: {'✅ VALID' if manifest_valid else '❌ INVALID'}")

    if not plugin_valid or not manifest_valid:
        print(f"\n🚨 Issues found that could prevent plugin discovery!")
        print("Common discovery issues:")
        print("   - Missing required fields in manifest")
        print("   - Invalid entrypoint format")
        print("   - Missing or incorrect permissions")
        print("   - Invalid API endpoints")
        print("   - Resource limit violations")
        return 1
    else:
        print(f"\n✅ Both manifests appear valid for plugin discovery!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
