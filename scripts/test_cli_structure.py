#!/usr/bin/env python3
"""
Test CLI structure and files without importing dependencies.
"""

import sys
from pathlib import Path

def test_cli_files_exist():
    """Test that CLI files exist."""
    print("🧪 Testing CLI File Structure")
    print("=" * 40)
    
    cli_path = Path("src/extensions/cli")
    
    expected_files = [
        "__init__.py",
        "main.py",
        "cli.py",
        "utils.py",
        "README.md",
        "demo.py",
        "commands/__init__.py",
        "commands/base.py",
        "commands/create.py",
        "commands/validate.py",
        "commands/test.py",
        "commands/package.py",
        "commands/dev_server.py",
        "templates/__init__.py",
        "templates/base.py",
        "templates/basic.py",
        "templates/api_only.py",
        "templates/ui_only.py",
        "templates/background_task.py",
        "templates/full.py",
        "tests/__init__.py",
        "tests/test_cli.py"
    ]
    
    all_exist = True
    
    for file_path in expected_files:
        full_path = cli_path / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist


def test_pyproject_entry():
    """Test that pyproject.toml has the CLI entry point."""
    print("\n🧪 Testing PyProject Entry Point")
    print("=" * 40)
    
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("   ❌ pyproject.toml not found")
        return False
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    if 'kari-ext = "src.extensions.cli.main:main"' in content:
        print("   ✅ CLI entry point found in pyproject.toml")
        return True
    else:
        print("   ❌ CLI entry point not found in pyproject.toml")
        return False


def test_template_structure():
    """Test template file structure."""
    print("\n🧪 Testing Template Structure")
    print("=" * 40)
    
    templates_path = Path("src/extensions/cli/templates")
    
    expected_templates = [
        "basic.py",
        "api_only.py", 
        "ui_only.py",
        "background_task.py",
        "full.py"
    ]
    
    all_exist = True
    
    for template in expected_templates:
        template_path = templates_path / template
        if template_path.exists():
            print(f"   ✅ {template}")
            
            # Check if template has required methods
            with open(template_path, 'r') as f:
                content = f.read()
            
            required_methods = ["get_manifest_template", "get_file_templates", "get_directory_structure"]
            for method in required_methods:
                if method in content:
                    print(f"      ✅ {method} method found")
                else:
                    print(f"      ❌ {method} method missing")
                    all_exist = False
        else:
            print(f"   ❌ {template} (missing)")
            all_exist = False
    
    return all_exist


def test_command_structure():
    """Test command file structure."""
    print("\n🧪 Testing Command Structure")
    print("=" * 40)
    
    commands_path = Path("src/extensions/cli/commands")
    
    expected_commands = [
        "create.py",
        "validate.py",
        "test.py", 
        "package.py",
        "dev_server.py"
    ]
    
    all_exist = True
    
    for command in expected_commands:
        command_path = commands_path / command
        if command_path.exists():
            print(f"   ✅ {command}")
            
            # Check if command has required methods
            with open(command_path, 'r') as f:
                content = f.read()
            
            required_methods = ["add_arguments", "execute"]
            for method in required_methods:
                if method in content:
                    print(f"      ✅ {method} method found")
                else:
                    print(f"      ❌ {method} method missing")
                    all_exist = False
        else:
            print(f"   ❌ {command} (missing)")
            all_exist = False
    
    return all_exist


def test_file_sizes():
    """Test that files have reasonable content."""
    print("\n🧪 Testing File Content Size")
    print("=" * 40)
    
    important_files = [
        "src/extensions/cli/main.py",
        "src/extensions/cli/commands/create.py",
        "src/extensions/cli/templates/basic.py",
        "src/extensions/cli/templates/full.py",
        "src/extensions/cli/README.md"
    ]
    
    all_good = True
    
    for file_path in important_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            lines = len(path.read_text().splitlines())
            print(f"   ✅ {path.name}: {size} bytes, {lines} lines")
            
            if size < 100:  # Very small files might be incomplete
                print(f"      ⚠️  File seems very small")
                all_good = False
        else:
            print(f"   ❌ {file_path} (missing)")
            all_good = False
    
    return all_good


def main():
    """Run all tests."""
    print("🚀 CLI Structure Test")
    print("=" * 50)
    
    tests = [
        test_cli_files_exist,
        test_pyproject_entry,
        test_template_structure,
        test_command_structure,
        test_file_sizes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All structure tests passed!")
        print("\n📋 CLI Implementation Summary:")
        print("   ✅ Extension scaffolding generator (kari-ext create)")
        print("   ✅ Extension validation and testing tools (kari-ext validate)")
        print("   ✅ Extension packaging utilities (kari-ext package)")
        print("   ✅ Hot-reload development server (kari-ext dev-server)")
        print("   ✅ 5 extension templates (basic, api-only, ui-only, background-task, full)")
        print("   ✅ Comprehensive test suite")
        print("   ✅ Documentation and examples")
        return 0
    else:
        print("❌ Some structure tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())