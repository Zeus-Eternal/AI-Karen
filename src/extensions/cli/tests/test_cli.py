"""
Tests for CLI functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from ..main import main
from ..commands.create import CreateCommand
from ..commands.validate import ValidateCommand


class TestCLI:
    """Test CLI main functionality."""
    
    def test_main_no_args(self):
        """Test main with no arguments shows help."""
        result = main([])
        assert result == 1
    
    def test_main_invalid_command(self):
        """Test main with invalid command."""
        result = main(["invalid-command"])
        assert result == 1


class TestCreateCommand:
    """Test create command."""
    
    def test_create_basic_extension(self):
        """Test creating a basic extension."""
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
            
            # Execute create command
            result = CreateCommand.execute(args)
            
            # Check result
            assert result == 0
            
            # Check files were created
            extension_dir = temp_path / extension_name
            assert extension_dir.exists()
            assert (extension_dir / "extension.json").exists()
            assert (extension_dir / "__init__.py").exists()
            assert (extension_dir / "api").exists()
            assert (extension_dir / "ui").exists()
            assert (extension_dir / "tests").exists()
    
    def test_create_invalid_name(self):
        """Test creating extension with invalid name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            args = MagicMock()
            args.name = "Invalid_Name"  # Invalid characters
            args.template = "basic"
            args.output_dir = temp_path
            args.author = "Test Author"
            args.description = "Test extension"
            args.force = False
            
            result = CreateCommand.execute(args)
            assert result == 1


class TestValidateCommand:
    """Test validate command."""
    
    def test_validate_nonexistent_path(self):
        """Test validating non-existent path."""
        args = MagicMock()
        args.path = Path("/nonexistent/path")
        args.strict = False
        args.fix = False
        args.output_format = "text"
        
        result = ValidateCommand.execute(args)
        assert result == 1
    
    def test_validate_valid_extension(self):
        """Test validating a valid extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a basic extension structure
            manifest = {
                "name": "test-extension",
                "version": "1.0.0",
                "display_name": "Test Extension",
                "description": "A test extension",
                "author": "Test Author",
                "api_version": "1.0",
                "capabilities": {
                    "provides_ui": True,
                    "provides_api": True,
                    "provides_background_tasks": False,
                    "provides_webhooks": False
                },
                "permissions": {
                    "data_access": [],
                    "plugin_access": [],
                    "system_access": [],
                    "network_access": []
                },
                "resources": {
                    "max_memory_mb": 64,
                    "max_cpu_percent": 5,
                    "max_disk_mb": 128
                }
            }
            
            # Write manifest
            with open(temp_path / "extension.json", "w") as f:
                json.dump(manifest, f)
            
            # Write basic __init__.py
            with open(temp_path / "__init__.py", "w") as f:
                f.write("# Test extension")
            
            args = MagicMock()
            args.path = temp_path
            args.strict = False
            args.fix = False
            args.output_format = "text"
            
            result = ValidateCommand.execute(args)
            assert result == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_is_valid_extension_name(self):
        """Test extension name validation."""
        from ..commands.create import CreateCommand
        
        assert CreateCommand._is_valid_extension_name("valid-name")
        assert CreateCommand._is_valid_extension_name("valid123")
        assert CreateCommand._is_valid_extension_name("123valid")
        
        assert not CreateCommand._is_valid_extension_name("Invalid_Name")
        assert not CreateCommand._is_valid_extension_name("Invalid Name")
        assert not CreateCommand._is_valid_extension_name("Invalid.Name")
        assert not CreateCommand._is_valid_extension_name("")
    
    def test_generate_manifest(self):
        """Test manifest generation."""
        manifest = CreateCommand._generate_manifest(
            "test-extension", 
            "basic", 
            "Test Author", 
            "Test description"
        )
        
        assert manifest["name"] == "test-extension"
        assert manifest["author"] == "Test Author"
        assert manifest["description"] == "Test description"
        assert manifest["capabilities"]["provides_ui"] is True
        assert manifest["capabilities"]["provides_api"] is True