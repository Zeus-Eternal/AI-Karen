#!/usr/bin/env python3
"""
Response Core Orchestrator Demo

This example demonstrates how to use the ResponseOrchestrator with the
existing Karen AI infrastructure for local-first response generation.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.core.response import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    PipelineConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_basic_usage():
    """Demonstrate basic ResponseOrchestrator usage."""
    print("=== Basic ResponseOrchestrator Demo ===")
    
    # Create a local-only orchestrator
    orchestrator = create_local_only_orchestrator(user_id="demo_user")
    
    # Test different types of requests
    test_messages = [
        "Hello, can you help me optimize this Python code?",
        "I'm getting a frustrating error in my JavaScript",
        "How do I write documentation for this API?",
        "What's the best way to debug memory leaks?",
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        
        try:
            response = orchestrator.respond(message)
            
            print(f"Intent: {response['intent']}")
            print(f"Persona: {response['persona']}")
            print(f"Mood: {response['mood']}")
            print(f"Response: {response['content']}")
            print(f"Model Used: {response['metadata']['model_used']}")
            print(f"Processing Time: {response['metadata']['generation_time_ms']}ms")
            
            if 'onboarding' in response:
                print("Onboarding Suggestions:")
                for gap_type, gap_info in response['onboarding'].items():
                    print(f"  - {gap_info['question']} (Priority: {gap_info['priority']})")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 50)


def demo_custom_configuration():
    """Demonstrate custom configuration options."""
    print("\n=== Custom Configuration Demo ===")
    
    # Create custom configuration
    config = PipelineConfig(
        persona_default="technical_writer",
        local_only=False,  # Allow cloud acceleration
        enable_copilotkit=True,
        enable_onboarding=True,
        memory_recall_limit=3,
        enable_metrics=False  # Disable for demo
    )
    
    # Create orchestrator with custom config
    orchestrator = create_response_orchestrator(
        user_id="custom_user",
        config=config
    )
    
    # Test with a documentation request
    message = "Explain how to use this machine learning model"
    print(f"User: {message}")
    
    try:
        response = orchestrator.respond(message, ui_caps={
            "copilotkit": True,
            "project_name": "ML Documentation Project"
        })
        
        print(f"Intent: {response['intent']}")
        print(f"Persona: {response['persona']}")
        print(f"Response: {response['content']}")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_persona_selection():
    """Demonstrate persona selection logic."""
    print("\n=== Persona Selection Demo ===")
    
    orchestrator = create_local_only_orchestrator(user_id="persona_demo")
    
    # Test different intents and moods
    test_cases = [
        ("Make this code run faster", "Expected: ruthless_optimizer"),
        ("I'm so frustrated with this bug!", "Expected: calm_fixit"),
        ("How do I document this function?", "Expected: technical_writer"),
        ("This error is really annoying", "Expected: calm_fixit (mood override)"),
    ]
    
    for message, expected in test_cases:
        print(f"\nUser: {message}")
        print(f"{expected}")
        
        try:
            response = orchestrator.respond(message)
            print(f"Actual: {response['persona']} (intent: {response['intent']}, mood: {response['mood']})")
            
        except Exception as e:
            print(f"Error: {e}")


def demo_error_handling():
    """Demonstrate error handling and fallback behavior."""
    print("\n=== Error Handling Demo ===")
    
    # Create orchestrator that will likely fail (no real LLM available)
    orchestrator = create_local_only_orchestrator(user_id="error_demo")
    
    message = "This will likely trigger fallback behavior"
    print(f"User: {message}")
    
    try:
        response = orchestrator.respond(message)
        
        print(f"Response: {response['content']}")
        print(f"Fallback Used: {response['metadata'].get('fallback_used', False)}")
        
        if response['metadata'].get('error'):
            print(f"Error Details: {response['metadata']['error']}")
            
    except Exception as e:
        print(f"Unexpected Error: {e}")


def main():
    """Run all demos."""
    print("Response Core Orchestrator Demo")
    print("=" * 50)
    
    try:
        demo_basic_usage()
        demo_custom_configuration()
        demo_persona_selection()
        demo_error_handling()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()