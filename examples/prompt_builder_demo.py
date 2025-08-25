#!/usr/bin/env python3
"""
Demo script showing the PromptBuilder in action.

This demonstrates how the PromptBuilder creates structured prompts
with persona and context data injection using Jinja2 templates.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.response.prompt_builder import PromptBuilder


def demo_basic_prompt():
    """Demonstrate basic prompt building."""
    print("=== Basic Prompt Building ===")
    
    builder = PromptBuilder()
    
    result = builder.build_prompt(
        user_text="Help me optimize this slow database query",
        persona="ruthless_optimizer",
        context=[
            {"text": "User mentioned N+1 query problems earlier"},
            {"text": "Database is PostgreSQL with 1M+ records"}
        ],
        intent="optimize_code",
        mood="neutral"
    )
    
    print("System Message:")
    print(result[0]["content"])
    print("\nUser Message:")
    print(result[1]["content"])
    print("\n" + "="*50 + "\n")


def demo_onboarding_prompt():
    """Demonstrate onboarding with profile gaps."""
    print("=== Onboarding Prompt ===")
    
    builder = PromptBuilder()
    
    result = builder.build_prompt(
        user_text="I'm having trouble with my project",
        persona="calm_fixit",
        context=[],
        gaps=["project_context", "tech_stack"],
        intent="general_assist",
        mood="frustrated"
    )
    
    print("System Message:")
    print(result[0]["content"])
    print("\nUser Message:")
    print(result[1]["content"])
    print("\n" + "="*50 + "\n")


def demo_copilotkit_prompt():
    """Demonstrate CopilotKit enhanced prompt."""
    print("=== CopilotKit Enhanced Prompt ===")
    
    builder = PromptBuilder()
    
    result = builder.build_prompt(
        user_text="Show me how to structure this React component",
        persona="technical_writer",
        context=[
            {"text": "Working on a dashboard component"},
            {"text": "Using TypeScript and styled-components"}
        ],
        intent="documentation",
        mood="neutral",
        ui_caps={"copilotkit": True}
    )
    
    print("System Message:")
    print(result[0]["content"])
    print("\nUser Message:")
    print(result[1]["content"])
    print("\n" + "="*50 + "\n")


def demo_template_rendering():
    """Demonstrate direct template rendering."""
    print("=== Direct Template Rendering ===")
    
    builder = PromptBuilder()
    
    # Render system_base template directly
    system_prompt = builder.render_template(
        "system_base",
        persona="ruthless_optimizer",
        intent="debug_error",
        mood="frustrated",
        ui_caps={},
        copilotkit_enabled=False
    )
    
    print("System Base Template:")
    print(system_prompt)
    
    # Render onboarding template directly
    onboarding_prompt = builder.render_template(
        "onboarding",
        gaps=["project_context", "experience_level"],
        persona="calm_fixit",
        intent="general_assist",
        primary_gap="project_context"
    )
    
    print("\nOnboarding Template:")
    print(onboarding_prompt)
    print("\n" + "="*50 + "\n")


def main():
    """Run all demos."""
    print("PromptBuilder Demo")
    print("==================\n")
    
    try:
        demo_basic_prompt()
        demo_onboarding_prompt()
        demo_copilotkit_prompt()
        demo_template_rendering()
        
        print("✅ All demos completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()