#!/usr/bin/env python3
"""
Simple test script for llama.cpp backend integration
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add _server directory to Python path
server_path = Path(__file__).parent / "_server"
sys.path.insert(0, str(server_path))

try:
    # Import backend module directly
    import backend
    logger.info("Backend module imported successfully")
    
    # Test if llama-cpp-python is available
    if backend.LLAMA_CPP_AVAILABLE:
        logger.info("llama-cpp-python is available")
    else:
        logger.info("llama-cpp-python is not available, will use stub")
    
    # Create a test backend
    model_path = Path("test-model.gguf")  # This doesn't exist, will trigger fallback
    test_backend_instance = backend.LocalLlamaBackend(
        model_path=model_path,
        threads=4,
        low_vram=False,
        n_ctx=4096
    )
    
    async def test_backend_func():
        """Test the backend"""
        logger.info("Testing backend loading...")
        await test_backend_instance.load()
        
        if test_backend_instance.loaded:
            logger.info("Backend loaded successfully")
            
            logger.info("Testing backend inference...")
            response = await test_backend_instance.perform_inference(
                "Hello, this is a test prompt.",
                {"temperature": 0.7, "max_tokens": 100}
            )
            logger.info(f"Inference response: {response}")
            
            logger.info("Testing backend unloading...")
            await test_backend_instance.unload()
            logger.info("Backend unloaded successfully")
        else:
            logger.error("Failed to load backend")
    
    # Run the test
    asyncio.run(test_backend_func())
    logger.info("Test completed successfully")
    
except ImportError as e:
    logger.error(f"Import error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()