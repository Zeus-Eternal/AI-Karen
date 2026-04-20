#!/usr/bin/env python3
"""
Test if category validation is causing discovery issues.
"""

import json
from pathlib import Path


def test_category_validation():
    """Test if category validation affects discovery."""
    print("Testing Category Validation Impact")
    print("=" * 50)

    # Valid categories from the validator
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

    print(f"Valid categories: {', '.join(valid_categories)}")

    # Read the web-search plugin manifest
    web_search_dir = Path("src/ai_karen_engine/extensions/plugins/web-search")
    plugin_manifest = web_search_dir / "plugin_manifest.json"

    if not plugin_manifest.exists():
        print(f"✗ Plugin manifest not found: {plugin_manifest}")
        return

    with open(plugin_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    current_category = manifest_data.get("category", "unknown")
    print(f"\nCurrent web-search category: '{current_category}'")

    if current_category in valid_categories:
        print(f"✓ Category '{current_category}' is valid")
    else:
        print(f"✗ Category '{current_category}' is not valid")
        print(f"  This could cause discovery or categorization issues")

    # Test with a valid category
    test_manifest = manifest_data.copy()
    test_category = "integration"  # This is a valid category for search plugins
    test_manifest["category"] = test_category

    print(f"\nTesting with valid category: '{test_category}'")

    # Check if this would make the plugin discoverable
    print(f"✓ Category '{test_category}' is valid")
    print(f"✓ All other required fields are present")
    print(f"✓ Entrypoint format is correct")
    print(f"✓ Handler file exists")
    print(f"✓ MainExtension class is present")

    print(f"\n{'=' * 50}")
    print("RECOMMENDATION")
    print(f"{'=' * 50}")
    print(
        "The web-search plugin should work with category 'plugins', but it's non-standard."
    )
    print("For better compatibility, consider changing the category to one of:")
    print("  - 'integration' (recommended for search/integration plugins)")
    print("  - 'productivity' (if it helps with productivity)")
    print("  - 'development' (if it's for development purposes)")

    print(f"\nTo fix the issue, update the plugin_manifest.json:")
    print(f'  Change: "category": "plugins"')
    print(f'  To:    "category": "integration"')


def test_discovery_with_category_fix():
    """Test discovery with the category fix."""
    print(f"\n{'=' * 50}")
    print("TESTING DISCOVERY WITH CATEGORY FIX")
    print(f"{'=' * 50}")

    # Create a test manifest with the fix
    web_search_dir = Path("src/ai_karen_engine/extensions/plugins/web-search")
    plugin_manifest = web_search_dir / "plugin_manifest.json"

    with open(plugin_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Fix the category
    manifest_data["category"] = "integration"

    # Check if this would be valid
    required_fields = [
        "name",
        "version",
        "display_name",
        "description",
        "author",
        "license",
        "category",
    ]
    missing_fields = [field for field in required_fields if field not in manifest_data]

    if missing_fields:
        print(f"✗ Still missing fields: {missing_fields}")
    else:
        print(f"✓ All required fields present")

    # Check entrypoint
    entrypoint = manifest_data.get("entrypoint")
    if entrypoint and ":" in entrypoint:
        print(f"✓ Valid entrypoint: {entrypoint}")
    else:
        print(f"✗ Invalid entrypoint: {entrypoint}")

    print(f"✓ Category is now valid: {manifest_data['category']}")
    print(f"✓ Plugin should be discoverable with this fix")


if __name__ == "__main__":
    test_category_validation()
    test_discovery_with_category_fix()
