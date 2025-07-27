#!/usr/bin/env python3
"""
Start the FastAPI server for testing LLM routes
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    from ai_karen_engine.fastapi import app
    
    print("Starting FastAPI server with LLM routes...")
    print("Server will be available at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("LLM providers endpoint: http://localhost:8000/api/llm/providers")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for testing
        log_level="info"
    )