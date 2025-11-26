#!/usr/bin/env python3
"""
Test script for the new extension system.
This script verifies that the extension system can load and execute extensions correctly.
"""

import sys
import os
import json
import logging
import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the extension system components
from ai_karen_engine.extension_host import (
    ExtensionLoader, 
    ExtensionRegistry as ExtensionHostRegistry, 
    ExtensionRunner, 
    ExtensionConfigManager,
    ExtensionManager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_extension_loading():
    """Test that extensions can be loaded correctly."""
    logger.info("Testing extension loading...")
    
    # Initialize the extension system
    extensions_path = Path("src/extensions_hub")
    if not extensions_path.exists():
        logger.error(f"Extensions path {extensions_path} does not exist")
        return False
    
    config_manager = ExtensionConfigManager()
    loader = ExtensionLoader(extensions_dir=str(extensions_path), config_manager=config_manager)
    registry = ExtensionHostRegistry()
    runner = ExtensionRunner(registry=registry, default_timeout=config_manager.get_config().timeout_seconds)
    
    # Create the extension manager
    extension_manager = ExtensionManager(
        extension_root=extensions_path,
        use_new_architecture=True
    )
    
    # Load extensions
    try:
        loaded_extensions = await extension_manager.load_all_extensions()
        logger.info(f"Successfully loaded extensions from {extensions_path}")
    except Exception as e:
        logger.error(f"Failed to load extensions: {e}")
        return False
    
    # Check if extensions were loaded
    if not loaded_extensions:
        logger.error("No extensions were loaded")
        return False
    
    logger.info(f"Loaded {len(loaded_extensions)} extensions:")
    for ext_id, ext in loaded_extensions.items():
        logger.info(f"  - {ext_id}: {ext.manifest.name} (v{ext.manifest.version})")
    
    return True

async def test_extension_execution():
    """Test that extensions can be executed correctly."""
    logger.info("Testing extension execution...")
    
    # Initialize the extension system
    extensions_path = Path("src/extensions_hub")
    if not extensions_path.exists():
        logger.error(f"Extensions path {extensions_path} does not exist")
        return False
    
    config_manager = ExtensionConfigManager()
    loader = ExtensionLoader(extensions_dir=str(extensions_path), config_manager=config_manager)
    registry = ExtensionHostRegistry()
    runner = ExtensionRunner(registry=registry, default_timeout=config_manager.get_config().timeout_seconds)
    
    # Create the extension manager
    extension_manager = ExtensionManager(
        extension_root=extensions_path,
        use_new_architecture=True
    )
    
    # Load extensions
    try:
        loaded_extensions = await extension_manager.load_all_extensions()
    except Exception as e:
        logger.error(f"Failed to load extensions: {e}")
        return False
    
    # Test hook points
    hook_points = [
        "pre_intent_detection",
        "pre_memory_retrieval", 
        "post_memory_retrieval",
        "pre_llm_prompt",
        "post_llm_result",
        "post_response"
    ]
    
    # Create a mock context for testing
    class MockContext:
        def __init__(self):
            self.data = {}
            self.user_message = "Hello, how are you?"
            self.conversation_history = []
            self.memory_results = []
            self.llm_prompt = ""
            self.llm_response = ""
            self.final_response = ""
    
    context = MockContext()
    
    # Test each hook point
    for hook_point in hook_points:
        logger.info(f"Testing hook point: {hook_point}")
        
        try:
            # Execute extensions for this hook point
            results = await extension_manager.trigger_all_extension_hooks(
                hook_type=hook_point,
                data={"message": context.user_message},
                user_context={"user_id": "test_user", "user_role": "admin"}
            )
            
            if results:
                logger.info(f"  Executed {len(results)} extensions for {hook_point}")
                for ext_id, result in results.items():
                    if "error" in result:
                        logger.info(f"    - {ext_id}: Error - {result['error']}")
                    else:
                        logger.info(f"    - {ext_id}: Success")
            else:
                logger.info(f"  No extensions registered for {hook_point}")
                
        except Exception as e:
            logger.error(f"  Error executing {hook_point}: {e}")
            return False
    
    return True

async def main():
    """Main test function."""
    logger.info("Starting extension system tests...")
    
    # Test extension loading
    if not await test_extension_loading():
        logger.error("Extension loading test failed")
        return 1
    
    # Test extension execution
    if not await test_extension_execution():
        logger.error("Extension execution test failed")
        return 1
    
    logger.info("All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))