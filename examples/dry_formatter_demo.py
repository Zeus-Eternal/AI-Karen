#!/usr/bin/env python3
"""
Demo script for the DRY Formatter with CopilotKit hooks.

This script demonstrates the key features of the DRYFormatter:
- Consistent output structure (headings, code blocks, bullets)
- Optional CopilotKit enhancements as purely additive features
- Graceful degradation when CopilotKit is unavailable
- DRY reusable logic and formatting
"""

import sys
import os
import json
from typing import Dict, Any

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.core.response.formatter import (
    DRYFormatter,
    FormattingOptions,
    create_formatter
)
from ai_karen_engine.core.response.config import PipelineConfig


def demo_basic_formatting():
    """Demonstrate basic formatting capabilities."""
    print("=" * 60)
    print("DEMO: Basic Formatting")
    print("=" * 60)
    
    formatter = create_formatter()
    
    raw_response = """Here's how to optimize your code:

# Main Steps

- First, profile your application
* Then identify bottlenecks
+ Finally, implement optimizations

```python
def optimized_function(data):
    # Use list comprehension for better performance
    return [item.process() for item in data if item.is_valid()]
```

This should improve performance significantly."""
    
    result = formatter.format_response(
        raw_response,
        intent="optimize_code",
        persona="ruthless_optimizer"
    )
    
    print("Raw Response:")
    print(raw_response)
    print("\nFormatted Response:")
    print(result["content"])
    print(f"\nCode Blocks Found: {len(result['code_blocks'])}")
    print(f"Sections Found: {list(result['sections'].keys())}")
    print(f"CopilotKit Enabled: {result['metadata']['copilotkit_enabled']}")


def demo_onboarding_sections():
    """Demonstrate onboarding section extraction and formatting."""
    print("\n" + "=" * 60)
    print("DEMO: Onboarding Sections")
    print("=" * 60)
    
    formatter = create_formatter()
    
    raw_response = """## Quick Plan
Set up your development environment and install dependencies.

## Next Action
Run `pip install -r requirements.txt` to install all required packages.

## Optional Boost
Consider using Docker for a consistent development environment across team members."""
    
    result = formatter.format_response(
        raw_response,
        intent="general_assist",
        persona="ruthless_optimizer"
    )
    
    print("Raw Response:")
    print(raw_response)
    print("\nExtracted Sections:")
    for section_name, content in result["sections"].items():
        print(f"  {section_name}: {content}")
    
    print("\nFormatted Content:")
    print(result["content"])


def demo_copilotkit_enhancements():
    """Demonstrate CopilotKit enhancements when available."""
    print("\n" + "=" * 60)
    print("DEMO: CopilotKit Enhancements")
    print("=" * 60)
    
    # Create formatter with CopilotKit enabled
    config = PipelineConfig(enable_copilotkit=True)
    formatter = DRYFormatter(config)
    
    raw_response = """Here's the debugging approach:

```python
import logging

def debug_function(data):
    logging.debug(f"Processing {len(data)} items")
    try:
        result = process_data(data)
        logging.info("Processing completed successfully")
        return result
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise
```

Add proper logging to track the issue."""
    
    result = formatter.format_response(
        raw_response,
        intent="debug_error",
        persona="calm_fixit"
    )
    
    print("Raw Response:")
    print(raw_response)
    print("\nFormatted Response:")
    print(result["content"])
    
    if result["metadata"]["copilotkit_enabled"] and "copilotkit" in result:
        print("\nCopilotKit Enhancements:")
        copilot_data = result["copilotkit"]
        
        if "inline_suggestions" in copilot_data:
            print("  Inline Suggestions:")
            for suggestion in copilot_data["inline_suggestions"]:
                print(f"    - {suggestion['type']}: {suggestion['text']}")
        
        if "ui_hints" in copilot_data:
            print("  UI Hints:")
            ui_hints = copilot_data["ui_hints"]
            if ui_hints["suggested_actions"]:
                print(f"    Suggested Actions: {', '.join(ui_hints['suggested_actions'])}")
        
        if "performance_metrics" in copilot_data:
            metrics = copilot_data["performance_metrics"]
            print(f"  Performance Metrics:")
            print(f"    Complexity: {metrics['estimated_complexity']}")
            print(f"    Code Blocks: {metrics['code_blocks_count']}")
            print(f"    Sections: {metrics['sections_count']}")
    else:
        print("\nCopilotKit enhancements not available or disabled")


def demo_graceful_degradation():
    """Demonstrate graceful degradation when formatting fails."""
    print("\n" + "=" * 60)
    print("DEMO: Graceful Degradation")
    print("=" * 60)
    
    # Create formatter with CopilotKit disabled
    config = PipelineConfig(enable_copilotkit=False)
    formatter = DRYFormatter(config)
    
    raw_response = """Simple response without special formatting."""
    
    result = formatter.format_response(
        raw_response,
        intent="general_assist",
        persona="ruthless_optimizer"
    )
    
    print("Raw Response:")
    print(raw_response)
    print("\nFormatted Response:")
    print(result["content"])
    print(f"\nCopilotKit Enabled: {result['metadata']['copilotkit_enabled']}")
    print(f"Formatting Applied: {result['metadata']['formatting_applied']}")


def demo_custom_formatting_options():
    """Demonstrate custom formatting options."""
    print("\n" + "=" * 60)
    print("DEMO: Custom Formatting Options")
    print("=" * 60)
    
    formatter = create_formatter()
    
    raw_response = """# Custom Formatting

- First point
- Second point
- Third point"""
    
    # Use custom formatting options
    result = formatter.format_response(
        raw_response,
        intent="documentation",
        persona="technical_writer",
        bullet_style="→",
        heading_style="###"
    )
    
    print("Raw Response:")
    print(raw_response)
    print("\nFormatted with Custom Options:")
    print(result["content"])


def demo_code_block_truncation():
    """Demonstrate code block truncation for long code."""
    print("\n" + "=" * 60)
    print("DEMO: Code Block Truncation")
    print("=" * 60)
    
    formatter = create_formatter()
    
    # Create a long code block
    long_code = "\n".join([f"line_{i} = {i}" for i in range(20)])
    raw_response = f"""Here's a long code example:

```python
{long_code}
```

This code is quite long."""
    
    result = formatter.format_response(
        raw_response,
        intent="optimize_code",
        persona="ruthless_optimizer",
        max_code_block_lines=5  # Truncate after 5 lines
    )
    
    print("Raw Response (truncated for display):")
    print(raw_response[:200] + "...")
    print("\nFormatted Response with Truncation:")
    print(result["content"])
    print(f"\nOriginal Code Block Lines: {result['code_blocks'][0]['line_count']}")


def main():
    """Run all demos."""
    print("DRY Formatter with CopilotKit Hooks - Demo")
    print("This demo shows the key features of the DRYFormatter")
    
    try:
        demo_basic_formatting()
        demo_onboarding_sections()
        demo_copilotkit_enhancements()
        demo_graceful_degradation()
        demo_custom_formatting_options()
        demo_code_block_truncation()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("Key Features Demonstrated:")
        print("✓ Consistent output structure (headings, code blocks, bullets)")
        print("✓ Structured section extraction (Quick Plan, Next Action, etc.)")
        print("✓ Optional CopilotKit enhancements (complexity graphs, suggestions)")
        print("✓ Graceful degradation when CopilotKit unavailable")
        print("✓ Custom formatting options")
        print("✓ Code block truncation for long code")
        print("✓ DRY reusable logic throughout")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())