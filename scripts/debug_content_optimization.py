#!/usr/bin/env python3
"""
Debug ContentOptimizationEngine implementation
"""

import asyncio
import sys
import os
import importlib.util

# Import the engine class
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

spec = importlib.util.spec_from_file_location(
    "content_optimization_engine", 
    "src/ai_karen_engine/services/content_optimization_engine.py"
)
content_optimization_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content_optimization_module)

ContentOptimizationEngine = content_optimization_module.ContentOptimizationEngine
ContentType = content_optimization_module.ContentType

def debug_content_type_detection():
    """Debug content type detection"""
    engine = ContentOptimizationEngine()
    
    test_cases = [
        ("```python\ndef func():\n    pass\n```", "Should be CODE"),
        ("- First item\n- Second item", "Should be LIST"),
        ("def authenticate_user():", "Should be CODE"),
        ("function myFunc() {}", "Should be CODE"),
        ("import os", "Should be CODE"),
        ("| col1 | col2 |", "Should be TABLE"),
        ("API function returns JSON", "Should be TECHNICAL"),
        ("Hello world", "Should be CONVERSATIONAL")
    ]
    
    for content, expected in test_cases:
        detected_type = engine._detect_content_type(content)
        print(f"Content: {repr(content[:50])}")
        print(f"Expected: {expected}")
        print(f"Detected: {detected_type}")
        print(f"Match: {detected_type.name in expected}")
        print("-" * 50)

if __name__ == "__main__":
    debug_content_type_detection()