#!/usr/bin/env python3
"""
Test script to verify plugin discovery functionality.
This script can be run manually to test if the extension system is working.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_extension_discovery():
    """Test if extension discovery is working."""
    try:
        # Import the extension manager
        from ai_karen_engine.extensions.platform.core.manager import (
            get_extension_core_manager,
        )

        logger = logging.getLogger(__name__)
        logger.info("Getting extension manager...")
        manager = get_extension_core_manager()

        if not manager:
            logger.error("Extension manager is not available")
            return False

        logger.info("Initializing extension manager...")
        await manager.initialize()

        logger.info("Refreshing extensions...")
        await manager.refresh_extensions()

        # Get discovered extensions
        discovered = manager.registry.list_discovered()
        loaded = manager.registry.list_extensions()

        logger.info(f"Discovered {len(discovered)} extensions: {discovered}")
        logger.info(f"Loaded {len(loaded)} extensions: {loaded}")

        # Get detailed status for each extension
        for ext_name in discovered:
            status = manager.get_extension_status(ext_name)
            if status:
                logger.info(f"Extension {ext_name}: {status}")
            else:
                logger.warning(f"Could not get status for {ext_name}")

        return len(discovered) > 0

    except Exception as e:
        print(f"Error testing extension discovery: {e}")
        return False

        logger.info("Initializing extension manager...")
        await manager.initialize()

        logger.info("Refreshing extensions...")
        await manager.refresh_extensions()

        # Get discovered extensions
        discovered = manager.registry.list_discovered()
        loaded = manager.registry.list_extensions()

        logger.info(f"Discovered {len(discovered)} extensions: {discovered}")
        logger.info(f"Loaded {len(loaded)} extensions: {loaded}")

        # Get detailed status for each extension
        for ext_name in discovered:
            status = manager.get_extension_status(ext_name)
            if status:
                logger.info(f"Extension {ext_name}: {status}")
            else:
                logger.warning(f"Could not get status for {ext_name}")

        return len(discovered) > 0

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error testing extension discovery: {e}")
        return False

        logger.info("Initializing extension manager...")
        await manager.initialize()

        logger.info("Refreshing extensions...")
        await manager.refresh_extensions()

        # Get discovered extensions
        discovered = manager.registry.list_discovered()
        loaded = manager.registry.list_extensions()

        logger.info(f"Discovered {len(discovered)} extensions: {discovered}")
        logger.info(f"Loaded {len(loaded)} extensions: {loaded}")

        # Get detailed status for each extension
        for ext_name in discovered:
            status = manager.get_extension_status(ext_name)
            if status:
                logger.info(f"Extension {ext_name}: {status}")
            else:
                logger.warning(f"Could not get status for {ext_name}")

        return len(discovered) > 0

    except Exception as e:
        logger.error(f"Error testing extension discovery: {e}")
        return False


async def test_plugin_manifests():
    """Test if plugin manifests are valid."""
    import json
    from pathlib import Path

    try:
        logger = logging.getLogger(__name__)

        plugins_dir = Path("src/ai_karen_engine/extensions/plugins")

        if not plugins_dir.exists():
            logger.error(f"Plugins directory does not exist: {plugins_dir}")
            return False

        valid_manifests = 0
        invalid_manifests = 0

        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "manifest.json"
                if not manifest_file.exists():
                    manifest_file = plugin_dir / "plugin_manifest.json"

                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r") as f:
                            manifest = json.load(f)

                        # Check required fields
                        required_fields = ["name", "version", "description"]
                        missing_fields = [
                            field for field in required_fields if field not in manifest
                        ]

                        if missing_fields:
                            logger.warning(
                                f"Plugin {plugin_dir.name} missing fields: {missing_fields}"
                            )
                            invalid_manifests += 1
                        else:
                            logger.info(
                                f"Valid manifest for {plugin_dir.name}: {manifest['name']} v{manifest['version']}"
                            )
                            valid_manifests += 1

                    except Exception as e:
                        logger.error(
                            f"Error reading manifest for {plugin_dir.name}: {e}"
                        )
                        invalid_manifests += 1
                else:
                    logger.warning(f"No manifest found for {plugin_dir.name}")
                    invalid_manifests += 1

        logger.info(
            f"Manifest validation complete: {valid_manifests} valid, {invalid_manifests} invalid"
        )
        return invalid_manifests == 0
    except Exception as e:
        print(f"Error in test_plugin_manifests: {e}")
        return False


async def main():
    """Main test function."""
    try:
        logger = logging.getLogger(__name__)

        logger.info("Starting plugin discovery test...")

        # Test 1: Check manifest files
        logger.info("=== Test 1: Plugin Manifest Validation ===")
        manifests_ok = await test_plugin_manifests()

        # Test 2: Check extension discovery
        logger.info("=== Test 2: Extension Discovery ===")
        discovery_ok = await test_extension_discovery()

        # Summary
        logger.info("=== Test Summary ===")
        logger.info(f"Manifest validation: {'PASS' if manifests_ok else 'FAIL'}")
        logger.info(f"Extension discovery: {'PASS' if discovery_ok else 'FAIL'}")

        if manifests_ok and discovery_ok:
            logger.info("All tests passed! Plugin discovery should be working.")
            return 0
        else:
            logger.error(
                "Some tests failed. Plugin discovery may not be working properly."
            )
            return 1
    except Exception as e:
        print(f"Error in main test function: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
