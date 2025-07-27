#!/usr/bin/env python3
"""
Run the AI Karen backend server with LLM routes
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Import the FastAPI app
        from ai_karen_engine.fastapi import app
        
        logger.info("Starting AI Karen backend server...")
        logger.info("Server will be available at: http://localhost:8000")
        logger.info("API docs available at: http://localhost:8000/docs")
        logger.info("LLM providers endpoint: http://localhost:8000/api/llm/providers")
        
        # Start the server
        import uvicorn
        uvicorn.run(
            app,
            host="127.0.0.1",  # Use 127.0.0.1 instead of 0.0.0.0
            port=8000,
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()