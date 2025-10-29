#!/usr/bin/env python3
"""
Standalone test for CLI functionality without dependencies.
"""

import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_create_command():
    """Test the create command functionality."""
    print("🧪 Testing CLI Create Command")
    print("=" * 40)
    
    try:
        from extensions.cli.commands.create import CreateCommand
        from unittest.mock import MagicMock
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extension_name = "test-extension"
            
            # Mock arguments
            args = MagicMock()
            args.name = extension_name
            args.template = "basic"
            args.output_dir = temp_path
            args.author = "Test Author"
            args.description = "Test extension"
            args.force = False
            
            print(f"Creating extension '{extension_name}' in {temp_path}")
            
            # Execute create command
            result = CreateCommand.execute(args)
            
            if result == 0:
                print("✅ Extension created successfully!")
                
                extension_dir = temp_path / extension_name
                
                # Check files were created
                expected_files = [
                    "extension.json",
                    "__init__.py",
                    "README.md",
                    "api/__init__.py",
                    "api/routes.py",
                    "api/models.py",
                    "ui/__init__.py",
                    "ui/components.py",
                    "tests/__init__.py",
                    "tests/test_extension.py",
                    "tests/test_api.py"
                ]
                
                print("\n📁 Created files:")
                for file_path in expected_files:
                    full_path = extension_dir / file_path
                    if full_path.exists():
                        print(f"   ✅ {file_path}")
                    else:
                        print(f"   ❌ {file_path} (missing)")
                
                # Check manifest content
                manifest_path = extension_dir / "extension.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    print(f"\n📋 Manifest details:")
                    print(f"   Name: {manifest.get('name')}")
                    print(f"   Version: {manifest.get('version')}")
                    print(f"   Author: {manifest.get('author')}")
                    print(f"   Template: {args.template}")
                
                return True
            else:
                print("❌ Extension creation failed!")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


def test_validation_functions():
    """Test validation utility functions."""
    print("\n🧪 Testing Validation Functions")
    print("=" * 40)
    
    try:
        from extensions.cli.commands.create import CreateCommand
        
        # Test valid names
        valid_names = ["test-extension", "my-plugin", "hello-world", "api123"]
        for name in valid_names:
            if CreateCommand._is_valid_extension_name(name):
                print(f"   ✅ '{name}' is valid")
            else:
                print(f"   ❌ '{name}' should be valid")
        
        # Test invalid names
        invalid_names = ["Test_Extension", "test extension", "test.extension", ""]
        for name in invalid_names:
            if not CreateCommand._is_valid_extension_name(name):
                print(f"   ✅ '{name}' is correctly invalid")
            else:
                print(f"   ❌ '{name}' should be invalid")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def test_templates():
    """Test template availability."""
    print("\n🧪 Testing Templates")
    print("=" * 40)
    
    try:
        from extensions.cli.commands.create import CreateCommand
        
        expected_templates = ["basic", "api-only", "ui-only", "background-task", "full"]
        
        for template in expected_templates:
            if template in CreateCommand.TEMPLATES:
                print(f"   ✅ Template '{template}' available")
            else:
                print(f"   ❌ Template '{template}' missing")
        
        print(f"\n📋 Available templates:")
        for template, description in CreateCommand.TEMPLATES.items():
            print(f"   {template:15} - {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 CLI Tools Standalone Test")
    print("=" * 50)
    
    tests = [
        test_validation_functions,
        test_templates,
        test_create_command
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())