"""
Tests for the Flexible Model Training Interface.

This module tests model compatibility checking, training environment setup,
basic and advanced training modes, and hardware constraint validation.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_karen_engine.core.response.training_interface import (
    FlexibleTrainingInterface,
    ModelCompatibilityChecker,
    TrainingEnvironmentManager,
    TrainingParameterValidator,
    HardwareConstraints,
    ModelCompatibility,
    TrainingEnvironment,
    BasicTrainingConfig,
    AdvancedTrainingConfig,
    TrainingJob,
    TrainingMode,
    TrainingType,
    TrainingStatus
)
from ai_karen_engine.services.enhanced_huggingface_service import TrainableModel


class TestHardwareConstraints:
    """Test hardware constraints detection and validation."""
    
    def test_hardware_constraints_creation(self):
        """Test creating hardware constraints."""
        constraints = HardwareConstraints(
            available_memory_gb=16.0,
            available_gpu_memory_gb=8.0,
            gpu_count=1,
            cpu_cores=8,
            supports_mixed_precision=True
        )
        
        assert constraints.available_memory_gb == 16.0
        assert constraints.available_gpu_memory_gb == 8.0
        assert constraints.gpu_count == 1
        assert constraints.cpu_cores == 8
        assert constraints.supports_mixed_precision is True
        assert constraints.recommended_precision == "fp16"
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    @patch('torch.cuda.is_available')
    def test_detect_current_hardware(self, mock_cuda_available, mock_cpu_count, mock_virtual_memory):
        """Test detecting current hardware constraints."""
        # Mock system information
        mock_memory = Mock()
        mock_memory.available = 16 * 1024**3  # 16GB
        mock_virtual_memory.return_value = mock_memory
        
        mock_cpu_count.return_value = 8
        mock_cuda_available.return_value = False
        
        constraints = HardwareConstraints.detect_current()
        
        assert constraints.available_memory_gb == 16.0
        assert constraints.gpu_count == 0
        assert constraints.cpu_cores == 8
        assert constraints.supports_mixed_precision is False


class TestModelCompatibilityChecker:
    """Test model compatibility checking functionality."""
    
    @pytest.fixture
    def mock_enhanced_hf_service(self):
        """Mock enhanced HuggingFace service."""
        service = Mock()
        return service
    
    @pytest.fixture
    def compatibility_checker(self, mock_enhanced_hf_service):
        """Create compatibility checker with mocked service."""
        return ModelCompatibilityChecker(mock_enhanced_hf_service)
    
    @pytest.fixture
    def sample_trainable_model(self):
        """Create sample trainable model."""
        return TrainableModel(
            id="microsoft/DialoGPT-medium",
            name="DialoGPT Medium",
            family="gpt",
            parameters="345M",
            tags=["conversational", "transformers"],
            downloads=1000,
            likes=50,
            supports_fine_tuning=True,
            supports_lora=True,
            supports_full_training=False,
            training_frameworks=["transformers", "peft"]
        )
    
    @pytest.fixture
    def sample_hardware_constraints(self):
        """Create sample hardware constraints."""
        return HardwareConstraints(
            available_memory_gb=16.0,
            available_gpu_memory_gb=8.0,
            gpu_count=1,
            cpu_cores=8,
            supports_mixed_precision=True
        )
    
    @pytest.mark.asyncio
    async def test_check_compatibility_success(
        self, 
        compatibility_checker, 
        mock_enhanced_hf_service,
        sample_trainable_model,
        sample_hardware_constraints
    ):
        """Test successful compatibility check."""
        # Mock service response
        mock_enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_trainable_model)
        
        compatibility = await compatibility_checker.check_compatibility(
            "microsoft/DialoGPT-medium",
            TrainingType.FINE_TUNING,
            sample_hardware_constraints
        )
        
        assert compatibility.model_id == "microsoft/DialoGPT-medium"
        assert compatibility.is_compatible is True
        assert compatibility.supports_fine_tuning is True
        assert compatibility.required_memory_gb > 0
        assert compatibility.recommended_batch_size > 0
        assert len(compatibility.training_frameworks) > 0
    
    @pytest.mark.asyncio
    async def test_check_compatibility_model_not_found(
        self, 
        compatibility_checker, 
        mock_enhanced_hf_service,
        sample_hardware_constraints
    ):
        """Test compatibility check when model is not found."""
        # Mock service response
        mock_enhanced_hf_service.get_model_info = AsyncMock(return_value=None)
        
        compatibility = await compatibility_checker.check_compatibility(
            "nonexistent/model",
            TrainingType.FINE_TUNING,
            sample_hardware_constraints
        )
        
        assert compatibility.model_id == "nonexistent/model"
        assert compatibility.is_compatible is False
        assert "Model not found" in compatibility.compatibility_issues[0]
    
    @pytest.mark.asyncio
    async def test_check_compatibility_insufficient_memory(
        self, 
        compatibility_checker, 
        mock_enhanced_hf_service,
        sample_trainable_model
    ):
        """Test compatibility check with insufficient memory."""
        # Mock service response
        mock_enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_trainable_model)
        
        # Create constraints with very low memory
        low_memory_constraints = HardwareConstraints(
            available_memory_gb=1.0,
            available_gpu_memory_gb=1.0,
            gpu_count=1,
            cpu_cores=2
        )
        
        compatibility = await compatibility_checker.check_compatibility(
            "microsoft/DialoGPT-medium",
            TrainingType.FINE_TUNING,
            low_memory_constraints
        )
        
        assert compatibility.is_compatible is False
        assert any("Insufficient" in issue for issue in compatibility.compatibility_issues)
    
    def test_extract_parameter_count(self, compatibility_checker):
        """Test parameter count extraction."""
        assert compatibility_checker._extract_parameter_count("7B") == 7.0
        assert compatibility_checker._extract_parameter_count("1.3B") == 1.3
        assert compatibility_checker._extract_parameter_count("345M") == 0.345
        assert compatibility_checker._extract_parameter_count("invalid") is None


class TestTrainingEnvironmentManager:
    """Test training environment management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def environment_manager(self, temp_dir):
        """Create environment manager with temporary directory."""
        return TrainingEnvironmentManager(temp_dir)
    
    @pytest.mark.asyncio
    async def test_setup_environment(self, environment_manager):
        """Test setting up training environment."""
        environment = await environment_manager.setup_environment(
            "microsoft/DialoGPT-medium",
            TrainingType.FINE_TUNING,
            TrainingMode.BASIC
        )
        
        assert environment.model_id == "microsoft/DialoGPT-medium"
        assert environment.training_type == TrainingType.FINE_TUNING
        assert environment.training_mode == TrainingMode.BASIC
        assert environment.output_dir.exists()
        assert environment.temp_dir.exists()
        assert environment.logs_dir.exists()
        assert isinstance(environment.hardware_constraints, HardwareConstraints)
    
    def test_cleanup_environment(self, environment_manager, temp_dir):
        """Test cleaning up training environment."""
        # Create a mock environment
        env_dir = Path(temp_dir) / "test_env"
        env_dir.mkdir()
        temp_subdir = env_dir / "temp"
        temp_subdir.mkdir()
        
        environment = TrainingEnvironment(
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode=TrainingMode.BASIC,
            output_dir=env_dir / "output",
            temp_dir=temp_subdir,
            model_cache_dir=env_dir / "models",
            data_dir=env_dir / "data",
            checkpoint_dir=env_dir / "checkpoints",
            logs_dir=env_dir / "logs",
            hardware_constraints=HardwareConstraints.detect_current()
        )
        
        # Cleanup should remove temp directory
        environment_manager.cleanup_environment(environment)
        assert not temp_subdir.exists()


class TestTrainingParameterValidator:
    """Test training parameter validation."""
    
    @pytest.fixture
    def validator(self):
        """Create parameter validator."""
        return TrainingParameterValidator()
    
    @pytest.fixture
    def sample_compatibility(self):
        """Create sample compatibility result."""
        return ModelCompatibility(
            model_id="test/model",
            is_compatible=True,
            supports_fine_tuning=True,
            required_memory_gb=4.0,
            required_gpu_memory_gb=2.0,
            recommended_batch_size=8
        )
    
    @pytest.fixture
    def sample_hardware(self):
        """Create sample hardware constraints."""
        return HardwareConstraints(
            available_memory_gb=16.0,
            available_gpu_memory_gb=8.0,
            gpu_count=1,
            cpu_cores=8
        )
    
    def test_validate_basic_config_success(self, validator, sample_compatibility, sample_hardware):
        """Test successful basic configuration validation."""
        config = BasicTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.FINE_TUNING,
            num_epochs=3,
            learning_rate=2e-5,
            batch_size=8
        )
        
        is_valid, issues = validator.validate_basic_config(
            config, sample_compatibility, sample_hardware
        )
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_basic_config_high_batch_size(self, validator, sample_compatibility, sample_hardware):
        """Test validation with high batch size."""
        config = BasicTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.FINE_TUNING,
            batch_size=32  # Much higher than recommended
        )
        
        is_valid, issues = validator.validate_basic_config(
            config, sample_compatibility, sample_hardware
        )
        
        assert is_valid is False
        assert any("Batch size" in issue for issue in issues)
    
    def test_validate_advanced_config_success(self, validator, sample_compatibility, sample_hardware):
        """Test successful advanced configuration validation."""
        config = AdvancedTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.LORA_ADAPTATION,
            learning_rate=2e-5,
            per_device_train_batch_size=8,
            lora_r=16,
            lora_alpha=32
        )
        
        is_valid, issues = validator.validate_advanced_config(
            config, sample_compatibility, sample_hardware
        )
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_advanced_config_invalid_lora(self, validator, sample_compatibility, sample_hardware):
        """Test validation with invalid LoRA parameters."""
        config = AdvancedTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.LORA_ADAPTATION,
            lora_r=16,
            lora_alpha=8  # Should be >= lora_r
        )
        
        is_valid, issues = validator.validate_advanced_config(
            config, sample_compatibility, sample_hardware
        )
        
        assert is_valid is False
        assert any("LoRA alpha" in issue for issue in issues)


class TestFlexibleTrainingInterface:
    """Test the main flexible training interface."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        enhanced_hf_service = Mock()
        training_data_manager = Mock()
        system_model_manager = Mock()
        
        return enhanced_hf_service, training_data_manager, system_model_manager
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def training_interface(self, mock_services, temp_dir):
        """Create training interface with mocked services."""
        enhanced_hf_service, training_data_manager, system_model_manager = mock_services
        
        return FlexibleTrainingInterface(
            enhanced_hf_service=enhanced_hf_service,
            training_data_manager=training_data_manager,
            system_model_manager=system_model_manager,
            base_dir=temp_dir
        )
    
    @pytest.mark.asyncio
    async def test_check_model_compatibility(self, training_interface, mock_services):
        """Test model compatibility checking through interface."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock model info
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            family="gpt",
            parameters="1B",
            supports_fine_tuning=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        compatibility = await training_interface.check_model_compatibility(
            "test/model", TrainingType.FINE_TUNING
        )
        
        assert compatibility.model_id == "test/model"
        assert compatibility.is_compatible is True
    
    @pytest.mark.asyncio
    async def test_setup_training_environment(self, training_interface):
        """Test training environment setup through interface."""
        environment = await training_interface.setup_training_environment(
            "test/model",
            TrainingType.FINE_TUNING,
            TrainingMode.BASIC
        )
        
        assert environment.model_id == "test/model"
        assert environment.training_type == TrainingType.FINE_TUNING
        assert environment.training_mode == TrainingMode.BASIC
    
    @pytest.mark.asyncio
    async def test_create_basic_training_job(self, training_interface, mock_services):
        """Test creating basic training job."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock compatible model
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            family="gpt",
            parameters="1B",
            supports_fine_tuning=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        config = BasicTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.FINE_TUNING,
            batch_size=1  # Use small batch size for testing
        )
        
        # Mock the compatibility check to return success
        with patch.object(training_interface, 'check_model_compatibility') as mock_check:
            mock_check.return_value = ModelCompatibility(
                model_id="test/model",
                is_compatible=True,
                supports_fine_tuning=True,
                required_memory_gb=4.0,
                required_gpu_memory_gb=2.0,
                recommended_batch_size=16
            )
            
            job = await training_interface.create_basic_training_job(config)
            
            assert job.model_id == "test/model"
            assert job.training_type == TrainingType.FINE_TUNING
            assert job.training_mode == TrainingMode.BASIC
            assert job.status == TrainingStatus.PENDING
            assert job.job_id in training_interface.active_jobs
    
    @pytest.mark.asyncio
    async def test_create_advanced_training_job(self, training_interface, mock_services):
        """Test creating advanced training job."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock compatible model
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            family="gpt",
            parameters="1B",
            supports_lora=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        config = AdvancedTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.LORA_ADAPTATION,
            per_device_train_batch_size=1  # Use small batch size for testing
        )
        
        # Mock the compatibility check to return success
        with patch.object(training_interface, 'check_model_compatibility') as mock_check:
            mock_check.return_value = ModelCompatibility(
                model_id="test/model",
                is_compatible=True,
                supports_lora=True,
                required_memory_gb=4.0,
                required_gpu_memory_gb=2.0,
                recommended_batch_size=16
            )
            
            job = await training_interface.create_advanced_training_job(config)
            
            assert job.model_id == "test/model"
            assert job.training_type == TrainingType.LORA_ADAPTATION
            assert job.training_mode == TrainingMode.ADVANCED
            assert job.status == TrainingStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_start_training_job(self, training_interface, mock_services):
        """Test starting a training job."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock compatible model
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            supports_fine_tuning=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        # Create job first with small batch size
        config = BasicTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.FINE_TUNING,
            batch_size=1  # Use small batch size for testing
        )
        
        # Mock the compatibility check to return success
        with patch.object(training_interface, 'check_model_compatibility') as mock_check:
            mock_check.return_value = ModelCompatibility(
                model_id="test/model",
                is_compatible=True,
                supports_fine_tuning=True,
                required_memory_gb=4.0,
                required_gpu_memory_gb=2.0,
                recommended_batch_size=16
            )
            
            job = await training_interface.create_basic_training_job(config)
            
            # Start the job
            success = await training_interface.start_training_job(job.job_id)
            assert success is True
            
            # Check job status changed
            updated_job = training_interface.get_training_job(job.job_id)
            assert updated_job.status in [TrainingStatus.PREPARING, TrainingStatus.TRAINING]
    
    @pytest.mark.asyncio
    async def test_cancel_training_job(self, training_interface, mock_services):
        """Test cancelling a training job."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock compatible model
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            supports_fine_tuning=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        # Create and start job with small batch size
        config = BasicTrainingConfig(
            model_id="test/model",
            dataset_id="test_dataset",
            training_type=TrainingType.FINE_TUNING,
            batch_size=1  # Use small batch size for testing
        )
        
        # Mock the compatibility check to return success
        with patch.object(training_interface, 'check_model_compatibility') as mock_check:
            mock_check.return_value = ModelCompatibility(
                model_id="test/model",
                is_compatible=True,
                supports_fine_tuning=True,
                required_memory_gb=4.0,
                required_gpu_memory_gb=2.0,
                recommended_batch_size=16
            )
            
            job = await training_interface.create_basic_training_job(config)
            await training_interface.start_training_job(job.job_id)
            
            # Cancel the job
            success = await training_interface.cancel_training_job(job.job_id)
            assert success is True
            
            # Check job status
            updated_job = training_interface.get_training_job(job.job_id)
            assert updated_job.status == TrainingStatus.CANCELLED
    
    def test_get_training_job(self, training_interface):
        """Test getting training job by ID."""
        # Create a mock job
        job = TrainingJob(
            job_id="test_job",
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode=TrainingMode.BASIC,
            status=TrainingStatus.PENDING,
            created_at=datetime.utcnow(),
            total_epochs=3
        )
        training_interface.active_jobs["test_job"] = job
        
        retrieved_job = training_interface.get_training_job("test_job")
        assert retrieved_job is not None
        assert retrieved_job.job_id == "test_job"
        
        # Test non-existent job
        non_existent = training_interface.get_training_job("non_existent")
        assert non_existent is None
    
    def test_list_training_jobs(self, training_interface):
        """Test listing all training jobs."""
        # Create mock jobs
        job1 = TrainingJob(
            job_id="job1",
            model_id="test/model1",
            training_type=TrainingType.FINE_TUNING,
            training_mode=TrainingMode.BASIC,
            status=TrainingStatus.PENDING,
            created_at=datetime.utcnow(),
            total_epochs=3
        )
        job2 = TrainingJob(
            job_id="job2",
            model_id="test/model2",
            training_type=TrainingType.LORA_ADAPTATION,
            training_mode=TrainingMode.ADVANCED,
            status=TrainingStatus.TRAINING,
            created_at=datetime.utcnow(),
            total_epochs=5
        )
        
        training_interface.active_jobs["job1"] = job1
        training_interface.active_jobs["job2"] = job2
        
        jobs = training_interface.list_training_jobs()
        assert len(jobs) == 2
        assert any(job.job_id == "job1" for job in jobs)
        assert any(job.job_id == "job2" for job in jobs)
    
    def test_get_hardware_constraints(self, training_interface):
        """Test getting hardware constraints."""
        constraints = training_interface.get_hardware_constraints()
        assert isinstance(constraints, HardwareConstraints)
        assert constraints.available_memory_gb > 0
        assert constraints.cpu_cores > 0
    
    @pytest.mark.asyncio
    async def test_get_trainable_models(self, training_interface, mock_services):
        """Test getting trainable models."""
        enhanced_hf_service, _, _ = mock_services
        
        # Mock trainable models
        sample_models = [
            TrainableModel(
                id="model1",
                name="Model 1",
                supports_fine_tuning=True
            ),
            TrainableModel(
                id="model2",
                name="Model 2",
                supports_fine_tuning=True,  # Make sure both have fine_tuning support
                supports_lora=True
            )
        ]
        enhanced_hf_service.search_models = AsyncMock(return_value=sample_models)
        
        models = await training_interface.get_trainable_models()
        assert len(models) == 2
        assert all(hasattr(model, 'supports_fine_tuning') for model in models)


# Integration Tests

class TestTrainingInterfaceIntegration:
    """Integration tests for the training interface."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_training_workflow(self, temp_dir):
        """Test complete training workflow from compatibility check to job completion."""
        # This would be a more comprehensive integration test
        # that tests the entire workflow with real or more realistic mocks
        
        # Mock services
        enhanced_hf_service = Mock()
        training_data_manager = Mock()
        system_model_manager = Mock()
        
        # Create interface
        interface = FlexibleTrainingInterface(
            enhanced_hf_service=enhanced_hf_service,
            training_data_manager=training_data_manager,
            system_model_manager=system_model_manager,
            base_dir=temp_dir
        )
        
        # Mock compatible model
        sample_model = TrainableModel(
            id="test/model",
            name="Test Model",
            family="gpt",
            parameters="1B",
            supports_fine_tuning=True
        )
        enhanced_hf_service.get_model_info = AsyncMock(return_value=sample_model)
        
        # Mock the compatibility check to return success
        with patch.object(interface, 'check_model_compatibility') as mock_check:
            mock_check.return_value = ModelCompatibility(
                model_id="test/model",
                is_compatible=True,
                supports_fine_tuning=True,
                required_memory_gb=4.0,
                required_gpu_memory_gb=2.0,
                recommended_batch_size=16
            )
            
            # 1. Check compatibility
            compatibility = await interface.check_model_compatibility(
                "test/model", TrainingType.FINE_TUNING
            )
            assert compatibility.is_compatible is True
            
            # 2. Create training job with small batch size
            config = BasicTrainingConfig(
                model_id="test/model",
                dataset_id="test_dataset",
                training_type=TrainingType.FINE_TUNING,
                num_epochs=1,  # Short for testing
                batch_size=1   # Small batch size for testing
            )
            job = await interface.create_basic_training_job(config)
        assert job.status == TrainingStatus.PENDING
        
        # 3. Start training
        success = await interface.start_training_job(job.job_id)
        assert success is True
        
        # 4. Wait a bit for training to progress (in real test, would mock this)
        await asyncio.sleep(0.1)
        
        # 5. Check job status
        updated_job = interface.get_training_job(job.job_id)
        assert updated_job.status in [
            TrainingStatus.PREPARING, 
            TrainingStatus.TRAINING, 
            TrainingStatus.COMPLETED
        ]


if __name__ == "__main__":
    pytest.main([__file__])