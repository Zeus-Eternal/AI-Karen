#!/usr/bin/env python3
"""
Demo script to test the extension CLI tools.
"""

import tempfile
import shutil
from pathlib import Path
from .main import main


def demo_create_extension():
    """Demo creating an extension."""
    print("🚀 Extension CLI Demo")
    print("=" * 50)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Working in: {temp_path}")
        
        # Test create command
        print("\n1. Creating a basic extension...")
        result = main([
            "create", 
            "demo-extension",
            "--template", "basic",
            "--output-dir", str(temp_path),
            "--author", "Demo Author",
            "--description", "A demo extension for testing"
        ])
        
        if result == 0:
            print("✅ Extension created successfully!")
            
            extension_path = temp_path / "demo-extension"
            
            # List created files
            print(f"\n📁 Created files in {extension_path}:")
            for file_path in sorted(extension_path.rglob("*")):
                if file_path.is_file():
                    relative_path = file_path.relative_to(extension_path)
                    print(f"   {relative_path}")
            
            # Test validate command
            print("\n2. Validating the extension...")
            result = main([
                "validate",
                str(extension_path)
            ])
            
            if result == 0:
                print("✅ Extension validation passed!")
            else:
                print("❌ Extension validation failed!")
            
            # Test package command (dry run)
            print("\n3. Testing package command...")
            result = main([
                "package",
                str(extension_path),
                "--metadata-only"
            ])
            
            if result == 0:
                print("✅ Package metadata generated!")
            else:
                print("❌ Package command failed!")
        
        else:
            print("❌ Extension creation failed!")
    
    print("\n🎉 Demo completed!")


def demo_templates():
    """Demo different templates."""
    print("\n📋 Available Templates:")
    print("=" * 30)
    
    from .commands.create import CreateCommand
    
    for template, description in CreateCommand.TEMPLATES.items():
        print(f"  {template:15} - {description}")
    
    print("\nTo create with different templates:")
    print("  kari-ext create my-api --template api-only")
    print("  kari-ext create my-ui --template ui-only")
    print("  kari-ext create my-tasks --template background-task")
    print("  kari-ext create my-full --template full")


if __name__ == "__main__":
    demo_create_extension()
    demo_templates()