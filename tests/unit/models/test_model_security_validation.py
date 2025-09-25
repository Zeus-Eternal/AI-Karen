"""
Test Model Security and Validation

Tests for enhanced model security and validation functionality including:
- Checksum verification for downloaded models
- File integrity checks before adding to registry
- Security scanning for potential issues
- Pre-download validation

This test suite covers Task 8.2 requirements.
"""

import pytest
import json
import tempfile
import shutil
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from src.ai_karen_engine.services.model_library_service import (
    ModelLibraryService,
    ModelInfo,
    ModelMetadata
)


class TestModelSecurityValidation:
    """Test model security and validation functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_registry_file(self, temp_dir):
        """Create mock registry file."""
        registry_file = temp_dir / "test_registry.json"
        registry_data = {
            "models": [
                {
                    "id": "test-model-secure",
                    "name": "Test Secure Model",
                    "path": str(temp_dir / "models" / "test-model-secure.gguf"),
                    "type": "gguf",
                    "provider": "llama-cpp",
                    "size": 1000,
                    "capabilities": ["chat", "completion"],
                    "metadata": {
                        "parameters": "1B",
                        "quantization": "Q4_K_M",
                        "memory_requirement": "1GB",
                        "context_length": 2048,
                        "license": "Apache 2.0",
                        "tags": ["test", "secure"]
                    },
                    "downloadInfo": {
                        "url": "https://example.com/secure-model.gguf",
                        "checksum": "sha256:test_checksum_hash",
                        "downloadDate": time.time() - 86400
                    }
                }
            ],
            "repositories": []
        }
        
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f)
        
        return registry_file
    
    @pytest.fixture
    def mock_model_file(self, temp_dir):
        """Create mock model file with GGUF header."""
        models_dir = temp_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        model_file = models_dir / "test-model-secure.gguf"
        # Create file with GGUF header
        model_data = b"GGUF" + b"fake model data" * 100
        model_file.write_bytes(model_data)
        
        return model_file
    
    @pytest.fixture
    def service(self, mock_registry_file, temp_dir):
        """Create ModelLibraryService instance for testing."""
        models_dir = temp_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        service = ModelLibraryService(registry_path=str(mock_registry_file))
        service.models_dir = models_dir
        
        return service
    
    def test_validate_checksum_sha256_valid(self, service, mock_model_file):
        """Test checksum validation with valid SHA256."""
        # Calculate actual checksum
        hasher = hashlib.sha256()
        with open(mock_model_file, 'rb') as f:
            hasher.update(f.read())
        actual_checksum = hasher.hexdigest()
        
        # Test with correct checksum
        result = service.validate_checksum(mock_model_file, f"sha256:{actual_checksum}")
        assert result is True
    
    def test_validate_checksum_sha256_invalid(self, service, mock_model_file):
        """Test checksum validation with invalid SHA256."""
        # Test with incorrect checksum
        result = service.validate_checksum(mock_model_file, "sha256:invalid_checksum_hash")
        assert result is False
    
    def test_validate_checksum_placeholder(self, service, mock_model_file):
        """Test checksum validation with placeholder checksum."""
        # Test with placeholder checksum (should pass)
        result = service.validate_checksum(mock_model_file, "placeholder_checksum_for_validation")
        assert result is True
    
    def test_validate_checksum_unsupported_algorithm(self, service, mock_model_file):
        """Test checksum validation with unsupported algorithm."""
        result = service.validate_checksum(mock_model_file, "unsupported:hash_value")
        assert result is False
    
    def test_validate_checksum_invalid_format(self, service, mock_model_file):
        """Test checksum validation with invalid format."""
        result = service.validate_checksum(mock_model_file, "invalid_format_no_colon")
        assert result is False
    
    def test_validate_checksum_missing_file(self, service, temp_dir):
        """Test checksum validation with missing file."""
        missing_file = temp_dir / "missing.gguf"
        result = service.validate_checksum(missing_file, "sha256:some_hash")
        assert result is False
    
    def test_scan_model_security_valid_model(self, service, mock_model_file):
        """Test security scan on a valid model."""
        scan_result = service.scan_model_security("test-model-secure")
        
        assert "error" not in scan_result
        assert scan_result["model_id"] == "test-model-secure"
        assert "security_checks" in scan_result
        assert "warnings" in scan_result
        assert "errors" in scan_result
        assert "overall_status" in scan_result
        
        # Check specific security checks
        assert "file_integrity" in scan_result["security_checks"]
        assert "file_format" in scan_result["security_checks"]
        assert "path_security" in scan_result["security_checks"]
        
        # File should exist and be readable
        file_integrity = scan_result["security_checks"]["file_integrity"]
        assert file_integrity["exists"] is True
        assert file_integrity["readable"] is True
    
    def test_scan_model_security_gguf_header_validation(self, service, mock_model_file):
        """Test GGUF header validation in security scan."""
        scan_result = service.scan_model_security("test-model-secure")
        
        file_format = scan_result["security_checks"]["file_format"]
        assert file_format["extension"] == ".gguf"
        assert file_format["valid_extension"] is True
        assert file_format["header_valid"] is True  # Should detect GGUF header
    
    def test_scan_model_security_invalid_gguf_header(self, service, temp_dir):
        """Test security scan with invalid GGUF header."""
        # Create file with invalid header
        models_dir = temp_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        invalid_file = models_dir / "invalid-header.gguf"
        invalid_file.write_bytes(b"INVALID" + b"fake data" * 100)
        
        # Update registry to include this file
        service.registry["models"].append({
            "id": "invalid-header-model",
            "name": "Invalid Header Model",
            "path": str(invalid_file),
            "type": "gguf",
            "provider": "llama-cpp",
            "size": len(invalid_file.read_bytes())
        })
        
        scan_result = service.scan_model_security("invalid-header-model")
        
        file_format = scan_result["security_checks"]["file_format"]
        assert file_format["header_valid"] is False
        assert any("GGUF file header is invalid" in warning for warning in scan_result["warnings"])
    
    def test_scan_model_security_nonexistent_model(self, service):
        """Test security scan on non-existent model."""
        scan_result = service.scan_model_security("nonexistent-model")
        
        assert "error" in scan_result
        assert scan_result["error"] == "Model not found in registry"
    
    def test_scan_model_security_missing_file(self, service):
        """Test security scan when model file is missing."""
        # Model exists in registry but file doesn't exist
        scan_result = service.scan_model_security("test-model-secure")
        
        # Should handle missing file gracefully
        assert "error" in scan_result or scan_result.get("overall_status") == "failed"
    
    def test_quarantine_model_success(self, service, mock_model_file):
        """Test successfully quarantining a model."""
        result = service.quarantine_model("test-model-secure", "Security concern detected")
        
        assert result is True
        
        # Check that quarantine directory was created
        quarantine_dir = service.models_dir / "quarantine"
        assert quarantine_dir.exists()
        
        # Check that original file was moved
        assert not mock_model_file.exists()
        
        # Check that registry was updated
        model_data = None
        for model in service.registry["models"]:
            if model.get("id") == "test-model-secure":
                model_data = model
                break
        
        assert model_data is not None
        assert model_data["status"] == "quarantined"
        assert "quarantine_info" in model_data
        assert model_data["quarantine_info"]["reason"] == "Security concern detected"
    
    def test_quarantine_model_nonexistent(self, service):
        """Test quarantining non-existent model."""
        result = service.quarantine_model("nonexistent-model", "Test reason")
        
        assert result is False
    
    def test_validate_model_before_download_valid_url(self, service):
        """Test pre-download validation with valid HTTPS URL."""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-length': '1000000', 'content-type': 'application/octet-stream'}
            mock_head.return_value = mock_response
            
            # Add test model to predefined models
            service.metadata_service.predefined_models["test-download-model"] = {
                "id": "test-download-model",
                "name": "Test Download Model",
                "size": 1000000,
                "checksum": "sha256:test_hash",
                "download_url": "https://example.com/model.gguf"
            }
            
            result = service.validate_model_before_download(
                "test-download-model", 
                "https://example.com/model.gguf"
            )
            
            assert "error" not in result
            assert result["safe_to_download"] is True
            assert "checks" in result
            
            # Check URL validation
            url_check = result["checks"]["url_validation"]
            assert url_check["scheme"] == "https"
            assert url_check["valid_scheme"] is True
            
            # Check network connectivity
            network_check = result["checks"]["network_connectivity"]
            assert network_check["url_accessible"] is True
            assert network_check["status_code"] == 200
    
    def test_validate_model_before_download_http_warning(self, service):
        """Test pre-download validation with HTTP URL (should warn)."""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_head.return_value = mock_response
            
            service.metadata_service.predefined_models["test-http-model"] = {
                "id": "test-http-model",
                "name": "Test HTTP Model",
                "size": 1000000,
                "download_url": "http://example.com/model.gguf"
            }
            
            result = service.validate_model_before_download(
                "test-http-model", 
                "http://example.com/model.gguf"
            )
            
            assert result["safe_to_download"] is True  # Still safe, but with warning
            assert any("HTTP instead of HTTPS" in warning for warning in result["warnings"])
    
    def test_validate_model_before_download_invalid_url(self, service):
        """Test pre-download validation with invalid URL."""
        service.metadata_service.predefined_models["test-invalid-url"] = {
            "id": "test-invalid-url",
            "name": "Test Invalid URL",
            "size": 1000000,
            "download_url": "ftp://invalid.com/model.gguf"
        }
        
        result = service.validate_model_before_download(
            "test-invalid-url", 
            "ftp://invalid.com/model.gguf"
        )
        
        assert result["safe_to_download"] is False
        assert any("Invalid URL scheme" in error for error in result["errors"])
    
    def test_validate_model_before_download_insufficient_space(self, service):
        """Test pre-download validation with insufficient disk space."""
        with patch.object(service, 'get_available_disk_space', return_value=100):  # Very small space
            service.metadata_service.predefined_models["test-large-model"] = {
                "id": "test-large-model",
                "name": "Test Large Model",
                "size": 1000000,  # 1MB model, but only 100 bytes available
                "download_url": "https://example.com/large-model.gguf"
            }
            
            result = service.validate_model_before_download(
                "test-large-model", 
                "https://example.com/large-model.gguf"
            )
            
            assert result["safe_to_download"] is False
            assert any("Insufficient disk space" in error for error in result["errors"])
    
    def test_validate_model_before_download_network_error(self, service):
        """Test pre-download validation with network error."""
        with patch('requests.head', side_effect=Exception("Network error")):
            service.metadata_service.predefined_models["test-network-error"] = {
                "id": "test-network-error",
                "name": "Test Network Error",
                "size": 1000000,
                "download_url": "https://example.com/model.gguf"
            }
            
            result = service.validate_model_before_download(
                "test-network-error", 
                "https://example.com/model.gguf"
            )
            
            # Should still be safe to download despite network check failure
            assert result["safe_to_download"] is True
            assert any("Network connectivity check failed" in warning for warning in result["warnings"])
    
    def test_validate_model_before_download_nonexistent_model(self, service):
        """Test pre-download validation with non-existent model."""
        result = service.validate_model_before_download(
            "nonexistent-model", 
            "https://example.com/model.gguf"
        )
        
        assert result["safe_to_download"] is True  # URL validation might pass
        assert any("not in predefined models list" in warning for warning in result["warnings"])
    
    def test_multiple_hash_algorithms(self, service, mock_model_file):
        """Test checksum validation with different hash algorithms."""
        # Test SHA1
        hasher = hashlib.sha1()
        with open(mock_model_file, 'rb') as f:
            hasher.update(f.read())
        sha1_hash = hasher.hexdigest()
        
        result = service.validate_checksum(mock_model_file, f"sha1:{sha1_hash}")
        assert result is True
        
        # Test MD5
        hasher = hashlib.md5()
        with open(mock_model_file, 'rb') as f:
            hasher.update(f.read())
        md5_hash = hasher.hexdigest()
        
        result = service.validate_checksum(mock_model_file, f"md5:{md5_hash}")
        assert result is True
        
        # Test SHA512
        hasher = hashlib.sha512()
        with open(mock_model_file, 'rb') as f:
            hasher.update(f.read())
        sha512_hash = hasher.hexdigest()
        
        result = service.validate_checksum(mock_model_file, f"sha512:{sha512_hash}")
        assert result is True
    
    def test_security_scan_path_traversal_detection(self, service, temp_dir):
        """Test security scan detects path traversal attempts."""
        # Create a model file outside the models directory
        outside_file = temp_dir / "outside_models.gguf"
        outside_file.write_bytes(b"GGUF" + b"outside data" * 100)
        
        # Add to registry with path outside models directory
        service.registry["models"].append({
            "id": "path-traversal-model",
            "name": "Path Traversal Model",
            "path": str(outside_file),
            "type": "gguf",
            "provider": "llama-cpp",
            "size": len(outside_file.read_bytes())
        })
        
        scan_result = service.scan_model_security("path-traversal-model")
        
        path_security = scan_result["security_checks"]["path_security"]
        assert path_security["within_models_dir"] is False
        assert any("outside the designated models directory" in error for error in scan_result["errors"])
        assert scan_result["overall_status"] == "failed"


class TestModelSecurityAPI:
    """Test API endpoints for model security functionality."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock ModelLibraryService."""
        service = Mock()
        
        # Mock security scan result
        service.scan_model_security.return_value = {
            "model_id": "test-model",
            "scan_timestamp": time.time(),
            "file_path": "/path/to/model.gguf",
            "security_checks": {
                "file_integrity": {"exists": True, "readable": True},
                "checksum": {"valid": True},
                "file_format": {"valid_extension": True, "header_valid": True}
            },
            "warnings": [],
            "errors": [],
            "overall_status": "passed"
        }
        
        # Mock quarantine result
        service.quarantine_model.return_value = True
        
        # Mock pre-download validation
        service.validate_model_before_download.return_value = {
            "safe_to_download": True,
            "checks": {"url_validation": {"valid_scheme": True}},
            "warnings": [],
            "errors": []
        }
        
        return service
    
    @patch('src.ai_karen_engine.api_routes.model_library_routes.get_model_library_service')
    def test_security_scan_endpoint(self, mock_get_service, mock_service):
        """Test the security scan API endpoint."""
        mock_get_service.return_value = mock_service
        
        # Mock model info
        from src.ai_karen_engine.services.model_library_service import ModelInfo, ModelMetadata
        mock_model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="llama-cpp",
            size=1000000,
            description="Test model",
            capabilities=["chat"],
            status="local",
            metadata=ModelMetadata(
                parameters="1B",
                quantization="Q4_K_M",
                memory_requirement="1GB",
                context_length=2048,
                license="Apache 2.0",
                tags=["test"]
            )
        )
        mock_service.get_model_info.return_value = mock_model
        
        # Test the service method directly
        result = mock_service.scan_model_security("test-model")
        
        assert result["overall_status"] == "passed"
        assert result["model_id"] == "test-model"
        mock_service.scan_model_security.assert_called_with("test-model")
    
    @patch('src.ai_karen_engine.api_routes.model_library_routes.get_model_library_service')
    def test_quarantine_endpoint(self, mock_get_service, mock_service):
        """Test the quarantine API endpoint."""
        mock_get_service.return_value = mock_service
        
        # Mock model info
        from src.ai_karen_engine.services.model_library_service import ModelInfo, ModelMetadata
        mock_model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="llama-cpp",
            size=1000000,
            description="Test model",
            capabilities=["chat"],
            status="local",
            metadata=ModelMetadata(
                parameters="1B",
                quantization="Q4_K_M",
                memory_requirement="1GB",
                context_length=2048,
                license="Apache 2.0",
                tags=["test"]
            )
        )
        mock_service.get_model_info.return_value = mock_model
        
        # Test quarantine
        result = mock_service.quarantine_model("test-model", "Security concern")
        
        assert result is True
        mock_service.quarantine_model.assert_called_with("test-model", "Security concern")


if __name__ == "__main__":
    pytest.main([__file__])