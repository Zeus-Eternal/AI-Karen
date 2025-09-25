"""
Tests for Basic Training Mode functionality.

This module tests the simplified training interface, automatic parameter selection,
user-friendly progress monitoring, and system reset capabilities.
"""

import asyncio
import json
import pytest
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_karen_engine.core.response.basic_training_mode import (
    BasicTrainingMode, BasicTrainingPresets, ProgressMonitor, SystemResetManager,
    BasicTrainingPreset, TrainingProgress, TrainingResult, SystemBackup,
    BasicTrainingDifficulty
)
from ai_karen_engine.core.response.training_interface import (
    FlexibleTrainingInterface, TrainingJob, TrainingStatus, TrainingType, HardwareConstraints
)
from ai_karen_engine.core.response.training_data_manager import TrainingDataManager
from ai_karen_engine.services.enhanced_huggingface_service import EnhancedHuggingFaceService
from ai_karen_engine.services.system_model_manager import SystemModelManager


class TestBasicTrainingPresets:
    """Test basic training presets functionality."""
    
    def test_get_preset(self):
        """Test getting a preset by name."""
        preset = BasicTrainingPresets.get_preset("quick_test")
        assert preset is not None
        assert preset.name == "Quick Test"
        assert preset.difficulty == BasicTrainingDifficulty.BEGINNER
        assert preset.training_type == TrainingType.LORA_ADAPTATION
        
        # Test non-existent preset
        assert BasicTrainingPresets.get_preset("non_existent") is None
    
    def test_get_recommended_presets(self):
        """Test getting recommended presets for hardware."""
        # Mock hardware with high memory
        hardware = HardwareConstraints(
            available_memory_gb=32.0,
            available_gpu_memory_gb=24.0,
            gpu_count=1,
            cpu_cores=8,
            supports_mixed_precision=True
        )
        
        presets = BasicTrainingPresets.get_recommended_presets(hardware)
        assert len(presets) > 0
        assert all(preset.memory_requirements_gb <= hardware.available_gpu_memory_gb for preset in presets)
        
        # Mock hardware with low memory
        hardware_low = HardwareConstraints(
            available_memory_gb=8.0,
            available_gpu_memory_gb=4.0,
            gpu_count=1,
            cpu_cores=4,
            supports_mixed_precision=False
        )
        
        presets_low = BasicTrainingPresets.get_recommended_presets(hardware_low)
        assert len(presets_low) <= len(presets)
        assert all(preset.memory_requirements_gb <= hardware_low.available_gpu_memory_gb for preset in presets_low)
    
    def test_get_preset_for_model(self):
        """Test getting preset for specific model."""
        # Hardware with sufficient memory for all presets
        hardware_high = HardwareConstraints(
            available_memory_gb=32.0,
            available_gpu_memory_gb=24.0,
            gpu_count=1,
            cpu_cores=8,
            supports_mixed_precision=True
        )
        
        # Test code model
        preset = BasicTrainingPresets.get_preset_for_model("microsoft/CodeBERT-base", hardware_high)
        assert preset is not None
        assert preset.name == "Code Assistant"
        
        # Test chat model
        preset = BasicTrainingPresets.get_preset_for_model("microsoft/DialoGPT-medium", hardware_high)
        assert preset is not None
        assert preset.name == "Chat Fine-tuning"
        
        # Test large model
        preset = BasicTrainingPresets.get_preset_for_model("meta-llama/Llama-2-7b-hf", hardware_high)
        assert preset is not None
        assert preset.name == "Domain Expert"
        
        # Test generic model
        preset = BasicTrainingPresets.get_preset_for_model("bert-base-uncased", hardware_high)
        assert preset is not None
        assert preset.name == "Quick Test"
        
        # Test with limited hardware - should fallback to Quick Test for memory-intensive presets
        hardware_low = HardwareConstraints(
            available_memory_gb=8.0,
            available_gpu_memory_gb=4.0,
            gpu_count=1,
            cpu_cores=4,
            supports_mixed_precision=False
        )
        
        preset = BasicTrainingPresets.get_preset_for_model("meta-llama/Llama-2-7b-hf", hardware_low)
        assert preset is not None
        assert preset.name == "Quick Test"  # Falls back due to memory constraints


class TestProgressMonitor:
    """Test progress monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = ProgressMonitor()
        self.job_id = str(uuid.uuid4())
        
        # Create mock training job
        self.job = TrainingJob(
            job_id=self.job_id,
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.TRAINING,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            total_epochs=3,
            total_steps=1000,
            current_epoch=1,
            current_step=500,
            loss=0.5,
            learning_rate=2e-5,
            metrics={"best_loss": 0.3, "memory_usage_gb": 4.2}
        )
    
    def test_start_monitoring(self):
        """Test starting progress monitoring."""
        self.monitor.start_monitoring(self.job_id)
        assert self.job_id in self.monitor.start_times
        assert isinstance(self.monitor.start_times[self.job_id], datetime)
    
    def test_get_progress(self):
        """Test getting training progress."""
        self.monitor.start_monitoring(self.job_id)
        progress = self.monitor.get_progress(self.job)
        
        assert progress.job_id == self.job_id
        assert progress.model_name == "model"
        assert progress.status == "Training in progress"
        assert progress.progress_percentage == 50.0  # 500/1000 steps
        assert progress.current_step == 500
        assert progress.total_steps == 1000
        assert progress.current_epoch == 1
        assert progress.total_epochs == 3
        assert progress.current_loss == 0.5
        assert progress.best_loss == 0.3
        assert progress.learning_rate == 2e-5
        assert progress.memory_usage_gb == 4.2
        assert "Training epoch 2 of 3" in progress.status_message
    
    def test_format_duration(self):
        """Test duration formatting."""
        # Test seconds
        duration = timedelta(seconds=45)
        formatted = self.monitor._format_duration(duration)
        assert formatted == "45s"
        
        # Test minutes
        duration = timedelta(minutes=5, seconds=30)
        formatted = self.monitor._format_duration(duration)
        assert formatted == "5m 30s"
        
        # Test hours
        duration = timedelta(hours=2, minutes=15)
        formatted = self.monitor._format_duration(duration)
        assert formatted == "2h 15m"
    
    def test_friendly_status(self):
        """Test friendly status conversion."""
        assert self.monitor._friendly_status(TrainingStatus.PENDING) == "Getting ready..."
        assert self.monitor._friendly_status(TrainingStatus.TRAINING) == "Training in progress"
        assert self.monitor._friendly_status(TrainingStatus.COMPLETED) == "Training completed!"
        assert self.monitor._friendly_status(TrainingStatus.FAILED) == "Training encountered an issue"
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Test with increasing loss
        self.job.loss = 0.8  # Higher than best loss
        recommendations = self.monitor._generate_recommendations(
            self.job, 50.0, timedelta(minutes=30)
        )
        assert any("reducing learning rate" in rec for rec in recommendations)
        
        # Test with slow progress
        recommendations = self.monitor._generate_recommendations(
            self.job, 5.0, timedelta(hours=2)
        )
        assert any("slower than expected" in rec for rec in recommendations)
    
    def test_check_warnings(self):
        """Test warning generation."""
        # Test stalled training
        warnings = self.monitor._check_warnings(
            self.job, 0.5, timedelta(minutes=35)
        )
        assert any("stalled" in warning for warning in warnings)
        
        # Test high loss
        self.job.loss = 15.0
        warnings = self.monitor._check_warnings(
            self.job, 50.0, timedelta(minutes=10)
        )
        assert any("very high" in warning for warning in warnings)


class TestSystemResetManager:
    """Test system reset and backup functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.reset_manager = SystemResetManager(backup_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_backup(self):
        """Test creating system backup."""
        backup = self.reset_manager.create_backup("Test backup")
        
        assert backup.backup_id is not None
        assert backup.description == "Test backup"
        assert backup.created_at is not None
        assert backup.size_mb >= 0
        
        # Check backup directory exists
        backup_path = Path(backup.backup_path)
        assert backup_path.exists()
        assert (backup_path / "backup_metadata.json").exists()
    
    def test_get_backup(self):
        """Test getting backup by ID."""
        # Create backup
        backup = self.reset_manager.create_backup("Test backup")
        
        # Retrieve backup
        retrieved = self.reset_manager.get_backup(backup.backup_id)
        assert retrieved is not None
        assert retrieved.backup_id == backup.backup_id
        assert retrieved.description == backup.description
        
        # Test non-existent backup
        assert self.reset_manager.get_backup("non-existent") is None
    
    def test_list_backups(self):
        """Test listing all backups."""
        # Create multiple backups
        backup1 = self.reset_manager.create_backup("Backup 1")
        backup2 = self.reset_manager.create_backup("Backup 2")
        
        backups = self.reset_manager.list_backups()
        assert len(backups) == 2
        
        backup_ids = [b.backup_id for b in backups]
        assert backup1.backup_id in backup_ids
        assert backup2.backup_id in backup_ids
    
    def test_delete_backup(self):
        """Test deleting backup."""
        # Create backup
        backup = self.reset_manager.create_backup("Test backup")
        
        # Delete backup
        success = self.reset_manager.delete_backup(backup.backup_id)
        assert success
        
        # Verify deletion
        assert self.reset_manager.get_backup(backup.backup_id) is None
        assert not Path(backup.backup_path).exists()
    
    def test_restore_backup(self):
        """Test restoring from backup."""
        # Create backup
        backup = self.reset_manager.create_backup("Test backup")
        
        # Restore backup (should not fail even with empty backup)
        success = self.reset_manager.restore_backup(backup.backup_id)
        assert success
        
        # Test non-existent backup
        success = self.reset_manager.restore_backup("non-existent")
        assert not success
    
    def test_reset_to_factory_defaults(self):
        """Test factory reset."""
        # Should create backup and reset
        success = self.reset_manager.reset_to_factory_defaults(preserve_user_data=True)
        assert success
        
        # Should have created a backup
        backups = self.reset_manager.list_backups()
        assert len(backups) > 0
        assert any("Pre-factory-reset" in b.description for b in backups)


class TestBasicTrainingMode:
    """Test main BasicTrainingMode functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.training_interface = Mock(spec=FlexibleTrainingInterface)
        self.training_data_manager = Mock(spec=TrainingDataManager)
        self.system_model_manager = Mock(spec=SystemModelManager)
        self.enhanced_hf_service = Mock(spec=EnhancedHuggingFaceService)
        
        # Create BasicTrainingMode instance
        self.basic_training = BasicTrainingMode(
            self.training_interface,
            self.training_data_manager,
            self.system_model_manager,
            self.enhanced_hf_service
        )
        
        # Mock active jobs
        self.training_interface.active_jobs = {}
    
    @pytest.mark.asyncio
    async def test_get_recommended_presets(self):
        """Test getting recommended presets."""
        with patch('ai_karen_engine.core.response.training_interface.HardwareConstraints.detect_current') as mock_hardware:
            mock_hardware.return_value = HardwareConstraints(
                available_memory_gb=16.0,
                available_gpu_memory_gb=8.0,
                gpu_count=1,
                cpu_cores=8,
                supports_mixed_precision=True
            )
            
            presets = await self.basic_training.get_recommended_presets()
            assert len(presets) > 0
            assert all(isinstance(preset, BasicTrainingPreset) for preset in presets)
    
    @pytest.mark.asyncio
    async def test_get_preset_for_model(self):
        """Test getting preset for specific model."""
        with patch('ai_karen_engine.core.response.training_interface.HardwareConstraints.detect_current') as mock_hardware:
            mock_hardware.return_value = HardwareConstraints(
                available_memory_gb=16.0,
                available_gpu_memory_gb=8.0,
                gpu_count=1,
                cpu_cores=8,
                supports_mixed_precision=True
            )
            
            preset = await self.basic_training.get_preset_for_model("microsoft/DialoGPT-medium")
            assert preset is not None
            assert isinstance(preset, BasicTrainingPreset)
    
    @pytest.mark.asyncio
    async def test_start_basic_training(self):
        """Test starting basic training."""
        # Mock compatibility check
        from ai_karen_engine.core.response.training_interface import ModelCompatibility
        mock_compatibility = ModelCompatibility(
            model_id="test/model",
            is_compatible=True,
            supports_fine_tuning=True,
            recommended_batch_size=8
        )
        self.training_interface.check_model_compatibility = AsyncMock(return_value=mock_compatibility)
        
        # Mock training job creation
        mock_job = TrainingJob(
            job_id=str(uuid.uuid4()),
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self.training_interface.create_basic_training_job = AsyncMock(return_value=mock_job)
        
        with patch('ai_karen_engine.core.response.training_interface.HardwareConstraints.detect_current') as mock_hardware:
            mock_hardware.return_value = HardwareConstraints(
                available_memory_gb=16.0,
                available_gpu_memory_gb=8.0,
                gpu_count=1,
                cpu_cores=8,
                supports_mixed_precision=True
            )
            
            job = await self.basic_training.start_basic_training(
                model_id="test/model",
                dataset_id="test/dataset",
                preset_name="quick_test"
            )
            
            assert job.job_id == mock_job.job_id
            assert job.model_id == "test/model"
            assert self.training_interface.check_model_compatibility.called
            assert self.training_interface.create_basic_training_job.called
    
    @pytest.mark.asyncio
    async def test_start_basic_training_incompatible_model(self):
        """Test starting training with incompatible model."""
        # Mock incompatible model
        from ai_karen_engine.core.response.training_interface import ModelCompatibility
        mock_compatibility = ModelCompatibility(
            model_id="test/model",
            is_compatible=False,
            compatibility_issues=["Model not supported"]
        )
        self.training_interface.check_model_compatibility = AsyncMock(return_value=mock_compatibility)
        
        with patch('ai_karen_engine.core.response.training_interface.HardwareConstraints.detect_current') as mock_hardware:
            mock_hardware.return_value = HardwareConstraints(
                available_memory_gb=16.0,
                available_gpu_memory_gb=8.0,
                gpu_count=1,
                cpu_cores=8,
                supports_mixed_precision=True
            )
            
            with pytest.raises(ValueError, match="Model not compatible"):
                await self.basic_training.start_basic_training(
                    model_id="test/model",
                    dataset_id="test/dataset",
                    preset_name="quick_test"
                )
    
    def test_get_training_progress(self):
        """Test getting training progress."""
        job_id = str(uuid.uuid4())
        mock_job = TrainingJob(
            job_id=job_id,
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.TRAINING,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            total_epochs=3,
            total_steps=1000,
            current_epoch=1,
            current_step=500,
            loss=0.5
        )
        
        self.training_interface.active_jobs[job_id] = mock_job
        
        progress = self.basic_training.get_training_progress(job_id)
        assert progress is not None
        assert progress.job_id == job_id
        assert progress.model_name == "model"
        assert progress.progress_percentage == 50.0
        
        # Test non-existent job
        assert self.basic_training.get_training_progress("non-existent") is None
    
    def test_get_training_result(self):
        """Test getting training result."""
        job_id = str(uuid.uuid4())
        mock_job = TrainingJob(
            job_id=job_id,
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() + timedelta(hours=2),
            loss=0.3,
            metrics={"initial_loss": 0.8},
            model_path="/path/to/model"
        )
        
        self.training_interface.active_jobs[job_id] = mock_job
        
        result = self.basic_training.get_training_result(job_id)
        assert result is not None
        assert result.job_id == job_id
        assert result.model_name == "model"
        assert result.success is True
        assert result.final_loss == 0.3
        assert result.improvement_percentage is not None
        assert result.improvement_percentage > 0  # Loss improved from 0.8 to 0.3
        assert result.model_path == "/path/to/model"
        
        # Test incomplete job
        mock_job.status = TrainingStatus.TRAINING
        assert self.basic_training.get_training_result(job_id) is None
    
    def test_cancel_training(self):
        """Test cancelling training."""
        job_id = str(uuid.uuid4())
        mock_job = TrainingJob(
            job_id=job_id,
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.TRAINING,
            created_at=datetime.utcnow()
        )
        
        self.training_interface.active_jobs[job_id] = mock_job
        
        success = self.basic_training.cancel_training(job_id)
        assert success
        assert mock_job.status == TrainingStatus.CANCELLED
        
        # Test non-existent job
        assert not self.basic_training.cancel_training("non-existent")
    
    def test_system_backup_operations(self):
        """Test system backup operations."""
        # Test create backup
        backup = self.basic_training.create_system_backup("Test backup")
        assert backup is not None
        assert backup.description == "Test backup"
        
        # Test list backups
        backups = self.basic_training.list_system_backups()
        assert len(backups) > 0
        assert backup.backup_id in [b.backup_id for b in backups]
        
        # Test restore backup
        success = self.basic_training.restore_system_backup(backup.backup_id)
        assert success
        
        # Test delete backup
        success = self.basic_training.delete_system_backup(backup.backup_id)
        assert success
    
    def test_reset_to_factory_defaults(self):
        """Test factory reset."""
        success = self.basic_training.reset_to_factory_defaults(preserve_user_data=True)
        assert success
        
        success = self.basic_training.reset_to_factory_defaults(preserve_user_data=False)
        assert success
    
    def test_adjust_config_for_hardware(self):
        """Test configuration adjustment for hardware."""
        preset = BasicTrainingPresets.get_preset("chat_fine_tune")
        
        # Test high-end hardware
        hardware = HardwareConstraints(
            available_memory_gb=32.0,
            available_gpu_memory_gb=24.0,
            gpu_count=1,
            cpu_cores=16,
            supports_mixed_precision=True
        )
        
        from ai_karen_engine.core.response.training_interface import ModelCompatibility
        compatibility = ModelCompatibility(
            model_id="test/model",
            is_compatible=True,
            recommended_batch_size=16
        )
        
        config = self.basic_training._adjust_config_for_hardware(preset, hardware, compatibility)
        assert config["use_mixed_precision"] is True
        assert config["batch_size"] <= 16
        
        # Test low-end hardware
        hardware_low = HardwareConstraints(
            available_memory_gb=8.0,
            available_gpu_memory_gb=4.0,
            gpu_count=1,
            cpu_cores=4,
            supports_mixed_precision=False
        )
        
        config_low = self.basic_training._adjust_config_for_hardware(preset, hardware_low, compatibility)
        assert config_low["use_mixed_precision"] is False
        assert config_low["batch_size"] <= 4
        assert config_low["max_length"] <= 256
        
        # Test CPU-only hardware
        hardware_cpu = HardwareConstraints(
            available_memory_gb=16.0,
            available_gpu_memory_gb=0.0,
            gpu_count=0,
            cpu_cores=8,
            supports_mixed_precision=False
        )
        
        config_cpu = self.basic_training._adjust_config_for_hardware(preset, hardware_cpu, compatibility)
        assert config_cpu["batch_size"] <= 2
    
    def test_generate_performance_summary(self):
        """Test performance summary generation."""
        mock_job = TrainingJob(
            job_id=str(uuid.uuid4()),
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        # Test excellent improvement
        summary = self.basic_training._generate_performance_summary(mock_job, 25.0)
        assert "Excellent results" in summary
        assert "25.0%" in summary
        
        # Test good improvement
        summary = self.basic_training._generate_performance_summary(mock_job, 15.0)
        assert "Good results" in summary
        
        # Test moderate improvement
        summary = self.basic_training._generate_performance_summary(mock_job, 7.0)
        assert "Moderate improvement" in summary
        
        # Test small improvement
        summary = self.basic_training._generate_performance_summary(mock_job, 2.0)
        assert "Small improvement" in summary
        
        # Test no improvement
        summary = self.basic_training._generate_performance_summary(mock_job, -1.0)
        assert "did not improve" in summary
        
        # Test no improvement data
        summary = self.basic_training._generate_performance_summary(mock_job, None)
        assert "Performance evaluation requires" in summary
    
    def test_generate_result_recommendations(self):
        """Test result recommendation generation."""
        mock_job = TrainingJob(
            job_id=str(uuid.uuid4()),
            model_id="test/model",
            training_type=TrainingType.FINE_TUNING,
            training_mode="basic",
            status=TrainingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            loss=0.5
        )
        
        # Test poor improvement
        recommendations = self.basic_training._generate_result_recommendations(mock_job, 2.0)
        assert any("more epochs" in rec for rec in recommendations)
        assert any("more diverse" in rec for rec in recommendations)
        
        # Test excellent improvement
        recommendations = self.basic_training._generate_result_recommendations(mock_job, 35.0)
        assert any("Excellent results" in rec for rec in recommendations)
        
        # Test high loss
        mock_job.loss = 2.0
        recommendations = self.basic_training._generate_result_recommendations(mock_job, 10.0)
        assert any("Loss is still high" in rec for rec in recommendations)
    
    def test_generate_next_steps(self):
        """Test next steps generation."""
        mock_job = TrainingJob(
            job_id=str(uuid.uuid4()),
            model_id="test/model",
            training_type=TrainingType.LORA_ADAPTATION,
            training_mode="basic",
            status=TrainingStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        next_steps = self.basic_training._generate_next_steps(mock_job)
        assert len(next_steps) > 0
        assert any("Test the trained model" in step for step in next_steps)
        assert any("Evaluate performance" in step for step in next_steps)
        assert any("backup" in step for step in next_steps)
        assert any("full fine-tuning" in step for step in next_steps)  # LoRA specific


if __name__ == "__main__":
    pytest.main([__file__])