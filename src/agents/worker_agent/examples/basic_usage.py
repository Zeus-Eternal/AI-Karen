#!/usr/bin/env python3
"""
Basic usage example for the Worker Agent

This example demonstrates how to use the Worker Agent to execute tasks.
"""

import sys
import os
import json

# Add the agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ..handler import initialize, execute, finalize


def main():
    """Main function to demonstrate Worker Agent usage"""
    
    # Initialize the agent
    context = {
        "config": {
            "max_concurrent_tasks": 5,
            "default_timeout": 60,
            "log_level": "INFO"
        },
        "state": {
            "initialized": False
        }
    }
    
    print("Initializing Worker Agent...")
    initialize(context)
    print("Worker Agent initialized successfully")
    
    # Example 1: Data Processing Task
    print("\n--- Example 1: Data Processing Task ---")
    data_processing_task = {
        "type": "data_processing",
        "data": {
            "input": "Sample data to process",
            "parameters": {
                "format": "json",
                "options": {
                    "normalize": True
                }
            }
        },
        "priority": 5,
        "timeout": 30
    }
    
    print(f"Executing task: {json.dumps(data_processing_task, indent=2)}")
    result = execute(data_processing_task)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Example 2: Analysis Task
    print("\n--- Example 2: Analysis Task ---")
    analysis_task = {
        "type": "analysis",
        "data": {
            "input": "Sample data to analyze",
            "parameters": {
                "format": "text",
                "options": {
                    "depth": "detailed"
                }
            }
        },
        "priority": 7,
        "timeout": 45
    }
    
    print(f"Executing task: {json.dumps(analysis_task, indent=2)}")
    result = execute(analysis_task)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Example 3: Unknown Task Type (will result in error)
    print("\n--- Example 3: Unknown Task Type ---")
    unknown_task = {
        "type": "unknown",
        "data": {
            "input": "Sample data"
        }
    }
    
    print(f"Executing task: {json.dumps(unknown_task, indent=2)}")
    result = execute(unknown_task)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Finalize the agent
    print("\nFinalizing Worker Agent...")
    finalize(result)
    print("Worker Agent finalized successfully")


if __name__ == "__main__":
    main()