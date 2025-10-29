"""
Unit tests for Model Validation System

Tests the comprehensive model validation system to ensure it correctly
validates model compatibility, dependencies, and performance characteristics.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.ai_karen_engine.services.model_validation_system import (
    ModelValidationSystem, ValidationLevel, ValidationResult, ValidationIssue,
    ValidationReport
)
from src.ai_karen_engine.services.model_discovery_engine import (
    ModelInfo, ModelType, ModalityType, ModelCategory, ModelSpecialization,
    ModelStatus, Modality, ResourceRequirements, ModelMetadata
)


class TestModelValidationSystem:
    """Test suite for ModelValidationSystem."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "validation_cache"
    
    @pytest.fixture
    def validation_system(self, temp_cache_dir):
        """Create a ModelValidationSystem instance for testing."""
        return ModelValidationSystem(cache_dir=str(temp_cache_dir))
    
    @pytest.fixture
    def sample_model_info(self):
        """Create a sample ModelInfo for testing."""
        return ModelInfo(
            id="test-model",
            name="test_model",
            display_name="Test Model",
            type=ModelType.LLAMA_CPP,
            path="/fake/path/test_model.gguf",
            size=1024 * 1024 * 1024,  # 1GB
            modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True,
                    formats=["text"]
                )
            ],
            capabilities=["text-generation", "local-inference"],
            requirements=ResourceRequirements(
                min_ram_gb=2.0,
                recommended_ram_gb=4.0,
                cpu_cores=2,
                gpu_required=False,
                disk_space_gb=1.0,
                supported_platforms=["linux", "windows", "macos"]
            ),
            status=ModelStatus.AVAILABLE,
            metadata=ModelMetadata(
                name="test_model",
                display_name="Test Model",
                description="A test model for validation",
                version="1.0",
                author="Test Author",
                license="MIT",
                context_length=2048,
                parameter_count=1100000000,  # 1.1B
                quantization="Q4_K_M",
                architecture="llama"
            ),
            category=ModelCategory.LANGUAGE,
            specialization=[ModelSpecialization.CHAT],
            tags=["test", "small", "quantized"],
            last_updated=0.0
        )
    
    def test_system_info_collection(self, validation_system):
        """Test that system information is collected correctly."""
        system_info = validation_system.system_info
        
        assert "platform" in system_info
        assert "architecture" in system_info
        assert "python_version" in system_info
        assert "cpu_count" in system_info
        assert "memory_gb" in system_info
        assert "disk_free_gb" in system_info
        assert "gpu_available" in system_info
        
        assert isinstance(system_info["cpu_count"], int)
        assert isinstance(system_info["memory_gb"], float)
        assert isinstance(system_info["disk_free_gb"], float)
        assert isinstance(system_info["gpu_available"], dict)
    
    @pytest.mark.asyncio
    async def test_basic_validation_file_exists(self, validation_system):
        """Test basic validation when file exists."""
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            # Write GGUF magic number
            temp_file.write(b'GGUF')
            temp_file.write(b'\x00' * 1000)
            temp_file.flush()
            
            model_info = ModelInfo(
                id="test", name="test", display_name="Test", type=ModelType.LLAMA_CPP,
                path=temp_file.name, size=1004, modalities=[], capabilities=[],
                requirements=ResourceRequirements(1.0, 2.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.GENERAL],
                tags=[], last_updated=0.0
            )
            
            try:
                issues = await validation_system._validate_basic(model_info)
                
                # Should have no critical errors for valid file
                error_issues = [i for i in issues if i.severity == "error"]
                assert len(error_issues) == 0
                
            finally:
                os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_basic_validation_file_missing(self, validation_system, sample_model_info):
        """Test basic validation when file is missing."""
        # Use non-existent path
        sample_model_info.path = "/nonexistent/path/model.gguf"
        
        issues = await validation_system._validate_basic(sample_model_info)
        
        # Should have error for missing file
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) > 0
        assert any("does not exist" in issue.message for issue in error_issues)
    
    @pytest.mark.asyncio
    async def test_basic_validation_empty_file(self, validation_system):
        """Test basic validation with empty file."""
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            # Create empty file
            temp_file.flush()
            
            model_info = ModelInfo(
                id="test", name="test", display_name="Test", type=ModelType.LLAMA_CPP,
                path=temp_file.name, size=0, modalities=[], capabilities=[],
                requirements=ResourceRequirements(1.0, 2.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.GENERAL],
                tags=[], last_updated=0.0
            )
            
            try:
                issues = await validation_system._validate_basic(model_info)
                
                # Should have error for empty file
                error_issues = [i for i in issues if i.severity == "error"]
                assert len(error_issues) > 0
                assert any("empty" in issue.message.lower() for issue in error_issues)
                
            finally:
                os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_basic_validation_gguf_format(self, validation_system):
        """Test GGUF format validation."""
        # Test valid GGUF file
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            temp_file.write(b'GGUF')  # Correct magic number
            temp_file.write(b'\x00' * 1000)
            temp_file.flush()
            
            model_info = ModelInfo(
                id="test", name="test", display_name="Test", type=ModelType.LLAMA_CPP,
                path=temp_file.name, size=1004, modalities=[], capabilities=[],
                requirements=ResourceRequirements(1.0, 2.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.GENERAL],
                tags=[], last_updated=0.0
            )
            
            try:
                issues = await validation_system._validate_basic_llama_cpp(Path(temp_file.name))
                
                # Should have no format errors
                format_errors = [i for i in issues if i.severity == "error" and i.category == "format"]
                assert len(format_errors) == 0
                
            finally:
                os.unlink(temp_file.name)
        
        # Test invalid GGUF file
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            temp_file.write(b'FAKE')  # Wrong magic number
            temp_file.write(b'\x00' * 1000)
            temp_file.flush()
            
            try:
                issues = await validation_system._validate_basic_llama_cpp(Path(temp_file.name))
                
                # Should have format error
                format_errors = [i for i in issues if i.severity == "error" and i.category == "format"]
                assert len(format_errors) > 0
                assert any("magic number" in issue.message.lower() for issue in format_errors)
                
            finally:
                os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_basic_validation_transformers_directory(self, validation_system):
        """Test transformers directory validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "test_model"
            model_dir.mkdir()
            
            # Create config.json
            config_data = {"model_type": "gpt2", "n_positions": 1024}
            with open(model_dir / "config.json", 'w') as f:
                json.dump(config_data, f)
            
            # Create model file
            with open(model_dir / "pytorch_model.bin", 'wb') as f:
                f.write(b'\x00' * 1000)
            
            issues = await validation_system._validate_basic_transformers(model_dir)
            
            # Should have no critical errors
            error_issues = [i for i in issues if i.severity == "error"]
            assert len(error_issues) == 0
        
        # Test missing config.json
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir) / "test_model"
            model_dir.mkdir()
            
            issues = await validation_system._validate_basic_transformers(model_dir)
            
            # Should have error for missing config
            error_issues = [i for i in issues if i.severity == "error"]
            assert len(error_issues) > 0
            assert any("config.json" in issue.message for issue in error_issues)
    
    @pytest.mark.asyncio
    async def test_resource_validation_sufficient_resources(self, validation_system, sample_model_info):
        """Test resource validation when system has sufficient resources."""
        # Mock system info with sufficient resources
        validation_system.system_info = {
            "memory_gb": 16.0,  # More than required 4GB
            "cpu_count": 8,     # More than required 2
            "disk_free_gb": 100.0,  # More than required 1GB
            "gpu_available": {"available": False, "devices": []}
        }
        
        issues = await validation_system._validate_resources(sample_model_info)
        
        # Should have no resource errors
        resource_errors = [i for i in issues if i.severity == "error" and i.category == "performance"]
        assert len(resource_errors) == 0
    
    @pytest.mark.asyncio
    async def test_resource_validation_insufficient_ram(self, validation_system, sample_model_info):
        """Test resource validation when system has insufficient RAM."""
        # Mock system info with insufficient RAM
        validation_system.system_info = {
            "memory_gb": 1.0,   # Less than required 2GB
            "cpu_count": 8,
            "disk_free_gb": 100.0,
            "gpu_available": {"available": False, "devices": []}
        }
        
        issues = await validation_system._validate_resources(sample_model_info)
        
        # Should have RAM error
        ram_errors = [i for i in issues if i.severity == "error" and "RAM" in i.message]
        assert len(ram_errors) > 0
    
    @pytest.mark.asyncio
    async def test_resource_validation_gpu_required_but_missing(self, validation_system, sample_model_info):
        """Test resource validation when GPU is required but not available."""
        # Set model to require GPU
        sample_model_info.requirements.gpu_required = True
        
        # Mock system info without GPU
        validation_system.system_info = {
            "memory_gb": 16.0,
            "cpu_count": 8,
            "disk_free_gb": 100.0,
            "gpu_available": {"available": False, "devices": []}
        }
        
        issues = await validation_system._validate_resources(sample_model_info)
        
        # Should have GPU error
        gpu_errors = [i for i in issues if i.severity == "error" and "GPU" in i.message]
        assert len(gpu_errors) > 0
    
    @pytest.mark.asyncio
    async def test_compatibility_validation_supported_platform(self, validation_system, sample_model_info):
        """Test compatibility validation on supported platform."""
        # Mock system info
        validation_system.system_info = {
            "platform": "Linux",
            "architecture": "x86_64",
            "python_version": "3.9.0"
        }
        
        issues, compat_info = await validation_system._validate_compatibility(sample_model_info)
        
        # Should have no compatibility errors
        compat_errors = [i for i in issues if i.severity == "error" and i.category == "compatibility"]
        assert len(compat_errors) == 0
        assert compat_info["platform_supported"] is True
    
    @pytest.mark.asyncio
    async def test_compatibility_validation_unsupported_platform(self, validation_system, sample_model_info):
        """Test compatibility validation on unsupported platform."""
        # Set model to only support Windows
        sample_model_info.requirements.supported_platforms = ["windows"]
        
        # Mock Linux system
        validation_system.system_info = {
            "platform": "Linux",
            "architecture": "x86_64",
            "python_version": "3.9.0"
        }
        
        issues, compat_info = await validation_system._validate_compatibility(sample_model_info)
        
        # Should have platform warning
        platform_warnings = [i for i in issues if i.severity == "warning" and "Platform" in i.message]
        assert len(platform_warnings) > 0
        assert compat_info["platform_supported"] is False
    
    @pytest.mark.asyncio
    async def test_full_validation_valid_model(self, validation_system):
        """Test full validation of a valid model."""
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            # Create valid GGUF file
            temp_file.write(b'GGUF')
            temp_file.write(b'\x00' * 1000)
            temp_file.flush()
            
            model_info = ModelInfo(
                id="test-valid", name="test_valid", display_name="Test Valid",
                type=ModelType.LLAMA_CPP, path=temp_file.name, size=1004,
                modalities=[], capabilities=[],
                requirements=ResourceRequirements(
                    min_ram_gb=0.5,  # Very low requirements
                    recommended_ram_gb=1.0,
                    cpu_cores=1,
                    gpu_required=False,
                    disk_space_gb=0.001,
                    supported_platforms=["linux", "windows", "macos"]
                ),
                status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE,
                specialization=[ModelSpecialization.GENERAL],
                tags=[], last_updated=0.0
            )
            
            try:
                report = await validation_system.validate_model(
                    model_info, ValidationLevel.STANDARD
                )
                
                assert report.model_id == "test-valid"
                assert report.validation_level == ValidationLevel.STANDARD
                assert report.overall_result in [ValidationResult.VALID, ValidationResult.WARNING]
                assert report.validation_time > 0
                
                # Check that report is cached
                cached_report = validation_system.get_validation_report("test-valid")
                assert cached_report is not None
                assert cached_report.model_id == "test-valid"
                
            finally:
                os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_full_validation_invalid_model(self, validation_system, sample_model_info):
        """Test full validation of an invalid model."""
        # Use non-existent path
        sample_model_info.path = "/nonexistent/model.gguf"
        
        report = await validation_system.validate_model(
            sample_model_info, ValidationLevel.BASIC
        )
        
        assert report.model_id == "test-model"
        assert report.overall_result == ValidationResult.INVALID
        assert report.status == ModelStatus.ERROR
        assert len(report.issues) > 0
        
        # Should have at least one error
        error_issues = [i for i in report.issues if i.severity == "error"]
        assert len(error_issues) > 0
    
    @pytest.mark.asyncio
    async def test_validation_caching(self, validation_system):
        """Test that validation results are properly cached."""
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as temp_file:
            temp_file.write(b'GGUF')
            temp_file.write(b'\x00' * 1000)
            temp_file.flush()
            
            model_info = ModelInfo(
                id="test-cache", name="test_cache", display_name="Test Cache",
                type=ModelType.LLAMA_CPP, path=temp_file.name, size=1004,
                modalities=[], capabilities=[],
                requirements=ResourceRequirements(0.5, 1.0),
                status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE,
                specialization=[ModelSpecialization.GENERAL],
                tags=[], last_updated=0.0
            )
            
            try:
                # First validation
                report1 = await validation_system.validate_model(model_info, ValidationLevel.BASIC)
                
                # Second validation (should use cache)
                report2 = await validation_system.validate_model(model_info, ValidationLevel.BASIC)
                
                # Should be the same report (from cache)
                assert report1.timestamp == report2.timestamp
                assert report1.validation_time == report2.validation_time
                
                # Force refresh should create new report
                report3 = await validation_system.validate_model(
                    model_info, ValidationLevel.BASIC, force_refresh=True
                )
                
                assert report3.timestamp > report1.timestamp
                
            finally:
                os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_validate_multiple_models(self, validation_system):
        """Test validating multiple models concurrently."""
        models = []
        temp_files = []
        
        try:
            # Create multiple test models
            for i in range(3):
                temp_file = tempfile.NamedTemporaryFile(suffix=".gguf", delete=False)
                temp_file.write(b'GGUF')
                temp_file.write(b'\x00' * 1000)
                temp_file.flush()
                temp_files.append(temp_file.name)
                
                model_info = ModelInfo(
                    id=f"test-multi-{i}", name=f"test_multi_{i}", 
                    display_name=f"Test Multi {i}",
                    type=ModelType.LLAMA_CPP, path=temp_file.name, size=1004,
                    modalities=[], capabilities=[],
                    requirements=ResourceRequirements(0.5, 1.0),
                    status=ModelStatus.AVAILABLE,
                    metadata=ModelMetadata(f"test{i}", f"Test {i}", "", "1.0", "test", "MIT", 1024),
                    category=ModelCategory.LANGUAGE,
                    specialization=[ModelSpecialization.GENERAL],
                    tags=[], last_updated=0.0
                )
                models.append(model_info)
            
            # Validate all models
            reports = await validation_system.validate_multiple_models(
                models, ValidationLevel.BASIC, max_concurrent=2
            )
            
            assert len(reports) == 3
            
            for i, report in enumerate(reports):
                assert report.model_id == f"test-multi-{i}"
                assert report.validation_level == ValidationLevel.BASIC
                
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except FileNotFoundError:
                    pass
    
    def test_validation_statistics(self, validation_system):
        """Test validation statistics generation."""
        # Add some test validation reports
        reports = [
            ValidationReport(
                model_id="test1", model_path="/test1", validation_level=ValidationLevel.BASIC,
                overall_result=ValidationResult.VALID, status=ModelStatus.AVAILABLE,
                issues=[], validation_time=1.0, timestamp=0.0
            ),
            ValidationReport(
                model_id="test2", model_path="/test2", validation_level=ValidationLevel.STANDARD,
                overall_result=ValidationResult.INVALID, status=ModelStatus.ERROR,
                issues=[
                    ValidationIssue("error", "format", "Test error"),
                    ValidationIssue("warning", "performance", "Test warning")
                ],
                validation_time=2.0, timestamp=0.0
            )
        ]
        
        with validation_system._lock:
            for report in reports:
                validation_system.validation_cache[report.model_id] = report
        
        stats = validation_system.get_validation_statistics()
        
        assert stats["total_validations"] == 2
        assert stats["results"]["valid"] == 1
        assert stats["results"]["invalid"] == 1
        assert stats["statuses"]["available"] == 1
        assert stats["statuses"]["error"] == 1
        assert stats["issue_severities"]["error"] == 1
        assert stats["issue_severities"]["warning"] == 1
        assert stats["issue_categories"]["format"] == 1
        assert stats["issue_categories"]["performance"] == 1
        assert stats["average_validation_time"] == 1.5
    
    def test_cache_persistence(self, validation_system, temp_cache_dir):
        """Test that validation cache persists between instances."""
        # Create a validation report
        report = ValidationReport(
            model_id="test_persist", model_path="/test", validation_level=ValidationLevel.BASIC,
            overall_result=ValidationResult.VALID, status=ModelStatus.AVAILABLE,
            issues=[], validation_time=1.0, timestamp=0.0
        )
        
        # Add to cache and save
        with validation_system._lock:
            validation_system.validation_cache["test_persist"] = report
            validation_system._save_validation_cache()
        
        # Create new instance and check if report is loaded
        new_system = ModelValidationSystem(cache_dir=str(temp_cache_dir))
        
        assert "test_persist" in new_system.validation_cache
        cached_report = new_system.validation_cache["test_persist"]
        assert cached_report.model_id == "test_persist"
        assert cached_report.overall_result == ValidationResult.VALID


@pytest.mark.integration
class TestModelValidationIntegration:
    """Integration tests for model validation with real dependencies."""
    
    @pytest.mark.asyncio
    async def test_dependency_checking_real_environment(self):
        """Test dependency checking in real environment."""
        validation_system = ModelValidationSystem()
        
        try:
            # Test llama-cpp dependencies
            llama_issues = await validation_system._check_llama_cpp_dependencies()
            print(f"Llama-cpp dependency issues: {len(llama_issues)}")
            
            # Test transformers dependencies
            transformers_issues = await validation_system._check_transformers_dependencies()
            print(f"Transformers dependency issues: {len(transformers_issues)}")
            
            # Test diffusion dependencies
            diffusion_issues = await validation_system._check_diffusion_dependencies()
            print(f"Diffusion dependency issues: {len(diffusion_issues)}")
            
            # Results depend on what's installed in the environment
            assert isinstance(llama_issues, list)
            assert isinstance(transformers_issues, list)
            assert isinstance(diffusion_issues, list)
            
        finally:
            validation_system.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])