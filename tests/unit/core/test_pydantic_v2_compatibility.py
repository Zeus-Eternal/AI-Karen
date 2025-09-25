"""
Unit tests for Pydantic V2 compatibility

This module tests that all Pydantic models in the system are compatible
with Pydantic V2 patterns and do not use deprecated V1 patterns.
"""

import pytest
from pathlib import Path
from typing import Dict, List

from src.ai_karen_engine.utils.pydantic_validator import PydanticV1Validator
from src.ai_karen_engine.utils.pydantic_migration_fixed import PydanticMigrationUtility


class TestPydanticV2Compatibility:
    """Test suite for Pydantic V2 compatibility"""
    
    def test_no_deprecated_config_class_patterns(self):
        """Test that no files use deprecated Config class patterns"""
        validator = PydanticV1Validator()
        result = validator.validate_directory("src", recursive=True)
        
        # Filter out false positives (files that use json_schema_extra correctly)
        actual_errors = []
        for file_result in result.get('files', []):
            violations = file_result.get('violations', [])
            for violation in violations:
                # Skip violations that are actually correct V2 patterns
                if 'json_schema_extra' in violation.get('line_content', ''):
                    continue
                if violation['severity'] == 'error':
                    actual_errors.append(violation)
        
        assert len(actual_errors) == 0, f"Found deprecated Pydantic V1 patterns: {actual_errors}"
    
    def test_error_response_routes_models(self):
        """Test that error response route models use correct V2 patterns"""
        from src.ai_karen_engine.api_routes.error_response_routes import (
            ErrorAnalysisRequest,
            ErrorAnalysisResponse
        )
        
        # Test that models can be instantiated
        request = ErrorAnalysisRequest(error_message="test error")
        assert request.error_message == "test error"
        assert request.use_ai_analysis is True  # default value
        
        # Test that model_config is used instead of Config class
        assert hasattr(ErrorAnalysisRequest, 'model_config')
        assert hasattr(ErrorAnalysisResponse, 'model_config')
        
        # Test that json_schema_extra is accessible
        request_config = ErrorAnalysisRequest.model_config
        response_config = ErrorAnalysisResponse.model_config
        
        assert 'json_schema_extra' in request_config
        assert 'json_schema_extra' in response_config
        
        # Test that examples are properly defined
        request_example = request_config['json_schema_extra']['example']
        response_example = response_config['json_schema_extra']['example']
        
        assert 'error_message' in request_example
        assert 'title' in response_example
    
    def test_unified_schemas_models(self):
        """Test that unified schema models use correct V2 patterns"""
        from src.ai_karen_engine.api_routes.unified_schemas import (
            ErrorResponse,
            SuccessResponse
        )
        
        # Test that models can be instantiated
        from datetime import datetime
        
        error_response = ErrorResponse(
            error="validation_error",
            message="Test error",
            correlation_id="test-123",
            timestamp=datetime.now(),
            path="/test",
            status_code=400
        )
        
        success_response = SuccessResponse(
            correlation_id="test-123",
            timestamp=datetime.now()
        )
        
        # Test that model_config is used
        assert hasattr(ErrorResponse, 'model_config')
        assert hasattr(SuccessResponse, 'model_config')
        
        # Test that json_encoders work correctly
        error_dict = error_response.model_dump()
        success_dict = success_response.model_dump()
        
        assert isinstance(error_dict['timestamp'], str)  # Should be ISO format
        assert isinstance(success_dict['timestamp'], str)  # Should be ISO format
    
    def test_pydantic_migration_utility(self):
        """Test the Pydantic migration utility"""
        utility = PydanticMigrationUtility("src")
        
        # Test scanning functionality
        issues = utility.scan_for_deprecated_patterns()
        
        # Should be able to generate a report
        report = utility.generate_report()
        assert isinstance(report, str)
        assert len(report) > 0
        
        # Test that files are processed
        assert len(utility.files_processed) > 0
    
    def test_pydantic_validator(self):
        """Test the Pydantic validator"""
        validator = PydanticV1Validator()
        
        # Test validating a specific file that should be compliant
        result = validator.validate_file("src/ai_karen_engine/api_routes/error_response_routes.py")
        
        assert 'file' in result
        assert 'violations' in result
        
        # Test directory validation
        dir_result = validator.validate_directory("src", recursive=True)
        
        assert 'directory' in dir_result
        assert 'files_checked' in dir_result
        assert dir_result['files_checked'] > 0
    
    def test_configdict_imports(self):
        """Test that ConfigDict is properly imported where needed"""
        import ast
        import importlib.util
        
        # Check a few key files that should have ConfigDict imports
        key_files = [
            "src/ai_karen_engine/api_routes/error_response_routes.py",
            "src/ai_karen_engine/api_routes/unified_schemas.py",
        ]
        
        for file_path in key_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Parse the AST to check imports
                tree = ast.parse(content)
                
                has_pydantic_import = False
                has_configdict_import = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module == 'pydantic':
                        has_pydantic_import = True
                        for alias in node.names:
                            if alias.name == 'ConfigDict':
                                has_configdict_import = True
                
                # If file imports from pydantic and uses model_config, it should import ConfigDict
                if has_pydantic_import and 'model_config' in content:
                    assert has_configdict_import, f"File {file_path} uses model_config but doesn't import ConfigDict"
    
    def test_no_deprecated_field_patterns(self):
        """Test that no Field definitions use deprecated patterns"""
        import re
        
        # Check for deprecated 'env' parameter in Field definitions
        src_dir = Path("src")
        deprecated_field_patterns = []
        
        for py_file in src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for Field(...env=...) patterns
                env_pattern = r'Field\([^)]*\benv\s*='
                matches = re.finditer(env_pattern, content)
                
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    deprecated_field_patterns.append({
                        'file': str(py_file),
                        'line': line_number,
                        'pattern': match.group(0)
                    })
                    
            except Exception as e:
                # Skip files that can't be read
                continue
        
        assert len(deprecated_field_patterns) == 0, f"Found deprecated Field env patterns: {deprecated_field_patterns}"
    
    def test_model_serialization(self):
        """Test that models serialize correctly with V2 patterns"""
        from src.ai_karen_engine.api_routes.error_response_routes import ErrorAnalysisRequest
        
        # Create a model instance
        request = ErrorAnalysisRequest(
            error_message="Test error message",
            error_type="TestError",
            status_code=500,
            use_ai_analysis=False
        )
        
        # Test serialization methods
        dict_data = request.model_dump()
        json_data = request.model_dump_json()
        
        assert isinstance(dict_data, dict)
        assert isinstance(json_data, str)
        
        assert dict_data['error_message'] == "Test error message"
        assert dict_data['error_type'] == "TestError"
        assert dict_data['status_code'] == 500
        assert dict_data['use_ai_analysis'] is False
        
        # Test that JSON schema generation works
        schema = request.model_json_schema()
        assert isinstance(schema, dict)
        assert 'properties' in schema
        assert 'example' in schema  # Should include the json_schema_extra example
    
    def test_validation_errors(self):
        """Test that validation errors work correctly with V2 patterns"""
        from src.ai_karen_engine.api_routes.error_response_routes import ErrorAnalysisRequest
        from pydantic import ValidationError
        
        # Test that validation errors are raised for invalid data
        with pytest.raises(ValidationError):
            ErrorAnalysisRequest()  # Missing required error_message
        
        with pytest.raises(ValidationError):
            ErrorAnalysisRequest(error_message="")  # Empty error_message should fail
        
        # Test that valid data passes validation
        valid_request = ErrorAnalysisRequest(error_message="Valid error message")
        assert valid_request.error_message == "Valid error message"


class TestPydanticV2MigrationUtility:
    """Test the migration utility functionality"""
    
    def test_migration_utility_initialization(self):
        """Test that migration utility initializes correctly"""
        utility = PydanticMigrationUtility("src")
        
        assert utility.root_path == Path("src")
        assert len(utility.issues_found) == 0
        assert len(utility.files_processed) == 0
    
    def test_pydantic_import_detection(self):
        """Test detection of Pydantic imports"""
        utility = PydanticMigrationUtility("src")
        
        # Test positive cases
        assert utility._contains_pydantic_imports("from pydantic import BaseModel")
        assert utility._contains_pydantic_imports("import pydantic")
        assert utility._contains_pydantic_imports("from pydantic.fields import Field")
        assert utility._contains_pydantic_imports("class MyModel(BaseModel):")
        
        # Test negative cases
        assert not utility._contains_pydantic_imports("import json")
        assert not utility._contains_pydantic_imports("from typing import Dict")
        assert not utility._contains_pydantic_imports("# This is a comment about pydantic")


if __name__ == '__main__':
    pytest.main([__file__])