#!/usr/bin/env python3
"""
Basic Training Mode Demo

This script demonstrates the simplified training interface with preset configurations,
automatic parameter selection, user-friendly progress monitoring, and comprehensive
system reset capabilities.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.response.basic_training_mode import (
    BasicTrainingMode, BasicTrainingPresets, ProgressMonitor, SystemResetManager,
    BasicTrainingDifficulty
)
from ai_karen_engine.core.response.training_interface import (
    FlexibleTrainingInterface, TrainingType, TrainingStatus, HardwareConstraints
)
from ai_karen_engine.core.response.training_data_manager import TrainingDataManager
from ai_karen_engine.services.enhanced_huggingface_service import EnhancedHuggingFaceService
from ai_karen_engine.services.system_model_manager import SystemModelManager


class MockTrainingInterface:
    """Mock training interface for demo purposes."""
    
    def __init__(self):
        self.active_jobs = {}
        self.job_counter = 0
    
    async def check_model_compatibility(self, model_id, training_type):
        """Mock compatibility check."""
        from ai_karen_engine.core.response.training_interface import ModelCompatibility
        
        return ModelCompatibility(
            model_id=model_id,
            is_compatible=True,
            supports_fine_tuning=True,
            supports_lora=True,
            recommended_batch_size=8,
            required_memory_gb=4.0,
            required_gpu_memory_gb=6.0,
            training_frameworks=["transformers", "peft"],
            estimated_training_time="2-4 hours"
        )
    
    async def create_basic_training_job(self, config):
        """Mock training job creation."""
        from ai_karen_engine.core.response.training_interface import TrainingJob
        import uuid
        
        job_id = str(uuid.uuid4())
        job = TrainingJob(
            job_id=job_id,
            model_id=config.model_id,
            training_type=config.training_type,
            training_mode="basic",
            status=TrainingStatus.PENDING,
            created_at=datetime.utcnow(),
            total_epochs=config.num_epochs,
            total_steps=1000,  # Mock value
            output_dir=f"./training_output/{job_id}"
        )
        
        self.active_jobs[job_id] = job
        return job
    
    def simulate_training_progress(self, job_id):
        """Simulate training progress for demo."""
        if job_id not in self.active_jobs:
            return
        
        job = self.active_jobs[job_id]
        
        # Simulate training stages
        if job.status == TrainingStatus.PENDING:
            job.status = TrainingStatus.VALIDATING
            logger.info(f"Job {job_id}: Validating configuration...")
        
        elif job.status == TrainingStatus.VALIDATING:
            job.status = TrainingStatus.PREPARING
            logger.info(f"Job {job_id}: Preparing training environment...")
        
        elif job.status == TrainingStatus.PREPARING:
            job.status = TrainingStatus.TRAINING
            job.started_at = datetime.utcnow()
            job.current_step = 0
            job.current_epoch = 0
            job.loss = 2.5  # Initial loss
            job.learning_rate = 2e-5
            job.metrics = {"initial_loss": 2.5, "memory_usage_gb": 4.2}
            logger.info(f"Job {job_id}: Training started!")
        
        elif job.status == TrainingStatus.TRAINING:
            # Simulate training progress
            job.current_step = min(job.current_step + 50, job.total_steps)
            job.current_epoch = job.current_step // (job.total_steps // job.total_epochs)
            
            # Simulate decreasing loss
            progress_ratio = job.current_step / job.total_steps
            job.loss = 2.5 * (1 - progress_ratio * 0.7)  # Loss decreases by 70%
            
            # Update best loss
            if "best_loss" not in job.metrics or job.loss < job.metrics["best_loss"]:
                job.metrics["best_loss"] = job.loss
            
            # Simulate memory usage fluctuation
            job.metrics["memory_usage_gb"] = 4.2 + (progress_ratio * 0.5)
            job.metrics["gpu_utilization"] = 85 + (progress_ratio * 10)
            
            if job.current_step >= job.total_steps:
                job.status = TrainingStatus.EVALUATING
                logger.info(f"Job {job_id}: Evaluating results...")
        
        elif job.status == TrainingStatus.EVALUATING:
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.model_path = f"./models/{job_id}/final_model"
            logger.info(f"Job {job_id}: Training completed!")


async def demo_training_presets():
    """Demonstrate training presets functionality."""
    print("\n" + "="*60)
    print("BASIC TRAINING MODE DEMO - TRAINING PRESETS")
    print("="*60)
    
    # Get hardware constraints
    hardware = HardwareConstraints.detect_current()
    print(f"\nDetected Hardware:")
    print(f"  Memory: {hardware.available_memory_gb:.1f}GB")
    print(f"  GPU Memory: {hardware.available_gpu_memory_gb:.1f}GB")
    print(f"  GPU Count: {hardware.gpu_count}")
    print(f"  CPU Cores: {hardware.cpu_cores}")
    print(f"  Mixed Precision: {hardware.supports_mixed_precision}")
    
    # Get recommended presets
    print(f"\nRecommended Training Presets:")
    presets = BasicTrainingPresets.get_recommended_presets(hardware)
    
    for i, preset in enumerate(presets, 1):
        print(f"\n{i}. {preset.name} ({preset.difficulty.value})")
        print(f"   Description: {preset.description}")
        print(f"   Training Type: {preset.training_type.value}")
        print(f"   Estimated Time: {preset.estimated_time}")
        print(f"   Memory Required: {preset.memory_requirements_gb}GB")
        print(f"   Configuration: {preset.num_epochs} epochs, LR={preset.learning_rate}")
        print(f"   Recommended for: {', '.join(preset.recommended_for[:3])}")
    
    # Test model-specific presets
    print(f"\nModel-Specific Preset Recommendations:")
    test_models = [
        "microsoft/DialoGPT-medium",
        "microsoft/CodeBERT-base", 
        "meta-llama/Llama-2-7b-hf",
        "bert-base-uncased"
    ]
    
    for model in test_models:
        preset = BasicTrainingPresets.get_preset_for_model(model, hardware)
        if preset:
            print(f"  {model} -> {preset.name}")


async def demo_basic_training():
    """Demonstrate basic training functionality."""
    print("\n" + "="*60)
    print("BASIC TRAINING MODE DEMO - TRAINING WORKFLOW")
    print("="*60)
    
    # Create mock dependencies
    training_interface = MockTrainingInterface()
    training_data_manager = TrainingDataManager()
    system_model_manager = SystemModelManager()
    enhanced_hf_service = EnhancedHuggingFaceService()
    
    # Create BasicTrainingMode instance
    basic_training = BasicTrainingMode(
        training_interface,
        training_data_manager,
        system_model_manager,
        enhanced_hf_service
    )
    
    # Override the training interface with our mock
    basic_training.training_interface = training_interface
    
    print("\n1. Starting Basic Training Job...")
    
    # Start training with a preset
    try:
        job = await basic_training.start_basic_training(
            model_id="microsoft/DialoGPT-medium",
            dataset_id="conversational_dataset",
            preset_name="chat_fine_tune",
            custom_description="Training a conversational AI model"
        )
        
        print(f"   ✓ Training job started: {job.job_id}")
        print(f"   ✓ Model: {job.model_id}")
        print(f"   ✓ Training Type: {job.training_type.value}")
        print(f"   ✓ Status: {job.status.value}")
        
    except Exception as e:
        print(f"   ✗ Failed to start training: {e}")
        return
    
    print("\n2. Monitoring Training Progress...")
    
    # Simulate training progress
    for step in range(10):
        # Simulate progress
        training_interface.simulate_training_progress(job.job_id)
        
        # Get progress
        progress = basic_training.get_training_progress(job.job_id)
        if progress:
            print(f"\n   Step {step + 1}:")
            print(f"   Status: {progress.status}")
            print(f"   Progress: {progress.progress_percentage:.1f}%")
            print(f"   Epoch: {progress.current_epoch + 1}/{progress.total_epochs}")
            print(f"   Step: {progress.current_step}/{progress.total_steps}")
            print(f"   Elapsed: {progress.elapsed_time}")
            print(f"   Estimated Remaining: {progress.estimated_remaining}")
            
            if progress.current_loss:
                print(f"   Current Loss: {progress.current_loss:.4f}")
            if progress.best_loss:
                print(f"   Best Loss: {progress.best_loss:.4f}")
            
            if progress.warnings:
                print(f"   ⚠️  Warnings: {', '.join(progress.warnings)}")
            if progress.recommendations:
                print(f"   💡 Recommendations: {', '.join(progress.recommendations[:2])}")
            
            # Check if completed
            if progress.status == "Training completed!":
                break
        
        # Wait before next update
        await asyncio.sleep(1)
    
    print("\n3. Getting Training Results...")
    
    # Get final results
    result = basic_training.get_training_result(job.job_id)
    if result:
        print(f"\n   Training Results for {result.model_name}:")
        print(f"   ✓ Success: {result.success}")
        print(f"   ✓ Training Time: {result.training_time}")
        
        if result.final_loss:
            print(f"   ✓ Final Loss: {result.final_loss:.4f}")
        if result.improvement_percentage:
            print(f"   ✓ Improvement: {result.improvement_percentage:.1f}%")
        if result.model_path:
            print(f"   ✓ Model Path: {result.model_path}")
        
        print(f"\n   Performance Summary:")
        print(f"   {result.performance_summary}")
        
        if result.recommendations:
            print(f"\n   Recommendations:")
            for rec in result.recommendations:
                print(f"   • {rec}")
        
        if result.next_steps:
            print(f"\n   Next Steps:")
            for step in result.next_steps:
                print(f"   • {step}")


async def demo_progress_monitoring():
    """Demonstrate progress monitoring features."""
    print("\n" + "="*60)
    print("BASIC TRAINING MODE DEMO - PROGRESS MONITORING")
    print("="*60)
    
    # Create progress monitor
    monitor = ProgressMonitor()
    
    # Create mock training job
    from ai_karen_engine.core.response.training_interface import TrainingJob
    import uuid
    
    job_id = str(uuid.uuid4())
    job = TrainingJob(
        job_id=job_id,
        model_id="microsoft/DialoGPT-medium",
        training_type=TrainingType.FINE_TUNING,
        training_mode="basic",
        status=TrainingStatus.TRAINING,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        total_epochs=3,
        total_steps=1000,
        current_epoch=1,
        current_step=350,
        loss=1.2,
        learning_rate=2e-5,
        metrics={
            "best_loss": 0.8,
            "initial_loss": 2.5,
            "memory_usage_gb": 5.2,
            "gpu_utilization": 87
        }
    )
    
    print("\n1. Progress Monitoring Features:")
    
    # Start monitoring
    monitor.start_monitoring(job_id)
    
    # Get progress
    progress = monitor.get_progress(job)
    
    print(f"\n   Job Information:")
    print(f"   • Job ID: {progress.job_id}")
    print(f"   • Model: {progress.model_name}")
    print(f"   • Status: {progress.status}")
    print(f"   • Status Message: {progress.status_message}")
    
    print(f"\n   Progress Metrics:")
    print(f"   • Overall Progress: {progress.progress_percentage:.1f}%")
    print(f"   • Current Epoch: {progress.current_epoch + 1}/{progress.total_epochs}")
    print(f"   • Current Step: {progress.current_step}/{progress.total_steps}")
    print(f"   • Elapsed Time: {progress.elapsed_time}")
    print(f"   • Estimated Remaining: {progress.estimated_remaining}")
    
    print(f"\n   Training Metrics:")
    print(f"   • Current Loss: {progress.current_loss:.4f}")
    print(f"   • Best Loss: {progress.best_loss:.4f}")
    print(f"   • Learning Rate: {progress.learning_rate:.2e}")
    print(f"   • Memory Usage: {progress.memory_usage_gb:.1f}GB")
    print(f"   • GPU Utilization: {progress.gpu_utilization:.0f}%")
    
    if progress.warnings:
        print(f"\n   ⚠️  Warnings:")
        for warning in progress.warnings:
            print(f"   • {warning}")
    
    if progress.recommendations:
        print(f"\n   💡 Recommendations:")
        for rec in progress.recommendations:
            print(f"   • {rec}")
    
    print("\n2. Duration Formatting Examples:")
    from datetime import timedelta
    
    durations = [
        timedelta(seconds=45),
        timedelta(minutes=5, seconds=30),
        timedelta(hours=2, minutes=15),
        timedelta(hours=1, minutes=0, seconds=0)
    ]
    
    for duration in durations:
        formatted = monitor._format_duration(duration)
        print(f"   • {duration} -> {formatted}")


async def demo_system_reset():
    """Demonstrate system reset and backup functionality."""
    print("\n" + "="*60)
    print("BASIC TRAINING MODE DEMO - SYSTEM RESET & BACKUP")
    print("="*60)
    
    # Create temporary directory for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create system reset manager
        reset_manager = SystemResetManager(backup_dir=temp_dir)
        
        print("\n1. Creating System Backups...")
        
        # Create multiple backups
        backup1 = reset_manager.create_backup("Initial configuration backup")
        print(f"   ✓ Created backup: {backup1.backup_id}")
        print(f"     Description: {backup1.description}")
        print(f"     Size: {backup1.size_mb:.2f}MB")
        print(f"     Created: {backup1.created_at}")
        
        await asyncio.sleep(1)  # Ensure different timestamps
        
        backup2 = reset_manager.create_backup("Pre-training backup")
        print(f"   ✓ Created backup: {backup2.backup_id}")
        print(f"     Description: {backup2.description}")
        print(f"     Size: {backup2.size_mb:.2f}MB")
        
        print("\n2. Listing Available Backups...")
        
        backups = reset_manager.list_backups()
        print(f"   Found {len(backups)} backups:")
        
        for i, backup in enumerate(backups, 1):
            print(f"   {i}. {backup.backup_id[:8]}... - {backup.description}")
            print(f"      Created: {backup.created_at}")
            print(f"      Size: {backup.size_mb:.2f}MB")
        
        print("\n3. Backup Operations...")
        
        # Test getting specific backup
        retrieved = reset_manager.get_backup(backup1.backup_id)
        if retrieved:
            print(f"   ✓ Retrieved backup: {retrieved.description}")
        
        # Test restore backup
        success = reset_manager.restore_backup(backup1.backup_id)
        if success:
            print(f"   ✓ Restored backup: {backup1.backup_id[:8]}...")
        
        print("\n4. Factory Reset Simulation...")
        
        # Test factory reset (this will create a pre-reset backup)
        success = reset_manager.reset_to_factory_defaults(preserve_user_data=True)
        if success:
            print(f"   ✓ System reset to factory defaults (user data preserved)")
            
            # Check if pre-reset backup was created
            updated_backups = reset_manager.list_backups()
            pre_reset_backup = next(
                (b for b in updated_backups if "Pre-factory-reset" in b.description), 
                None
            )
            if pre_reset_backup:
                print(f"   ✓ Pre-reset backup created: {pre_reset_backup.backup_id[:8]}...")
        
        print("\n5. Cleanup Operations...")
        
        # Delete a backup
        success = reset_manager.delete_backup(backup2.backup_id)
        if success:
            print(f"   ✓ Deleted backup: {backup2.backup_id[:8]}...")
        
        # List remaining backups
        final_backups = reset_manager.list_backups()
        print(f"   Remaining backups: {len(final_backups)}")
        
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def demo_integration():
    """Demonstrate full integration of basic training mode."""
    print("\n" + "="*60)
    print("BASIC TRAINING MODE DEMO - FULL INTEGRATION")
    print("="*60)
    
    # Create mock dependencies
    training_interface = MockTrainingInterface()
    training_data_manager = TrainingDataManager()
    system_model_manager = SystemModelManager()
    enhanced_hf_service = EnhancedHuggingFaceService()
    
    # Create BasicTrainingMode instance
    basic_training = BasicTrainingMode(
        training_interface,
        training_data_manager,
        system_model_manager,
        enhanced_hf_service
    )
    
    # Override with mock
    basic_training.training_interface = training_interface
    
    print("\n1. System Status Check...")
    
    # Get recommended presets
    presets = await basic_training.get_recommended_presets()
    print(f"   ✓ Available presets: {len(presets)}")
    
    # Get model-specific preset
    preset = await basic_training.get_preset_for_model("microsoft/DialoGPT-medium")
    if preset:
        print(f"   ✓ Recommended preset for DialoGPT: {preset.name}")
    
    print("\n2. System Backup Before Training...")
    
    # Create backup before training
    backup = basic_training.create_system_backup("Pre-training system state")
    print(f"   ✓ Backup created: {backup.backup_id[:8]}...")
    
    print("\n3. Multiple Training Jobs...")
    
    # Start multiple training jobs
    models = [
        ("microsoft/DialoGPT-medium", "chat_dataset", "chat_fine_tune"),
        ("microsoft/CodeBERT-base", "code_dataset", "code_assistant")
    ]
    
    jobs = []
    for model_id, dataset_id, preset_name in models:
        try:
            job = await basic_training.start_basic_training(
                model_id=model_id,
                dataset_id=dataset_id,
                preset_name=preset_name
            )
            jobs.append(job)
            print(f"   ✓ Started training: {model_id} -> {job.job_id[:8]}...")
        except Exception as e:
            print(f"   ✗ Failed to start training for {model_id}: {e}")
    
    print("\n4. Monitoring Multiple Jobs...")
    
    # Monitor all jobs
    for _ in range(5):
        print(f"\n   Progress Update:")
        
        for job in jobs:
            # Simulate progress
            training_interface.simulate_training_progress(job.job_id)
            
            # Get progress
            progress = basic_training.get_training_progress(job.job_id)
            if progress:
                print(f"   • {progress.model_name}: {progress.status} ({progress.progress_percentage:.0f}%)")
        
        await asyncio.sleep(1)
    
    print("\n5. System Management...")
    
    # List all backups
    backups = basic_training.list_system_backups()
    print(f"   ✓ Total system backups: {len(backups)}")
    
    # Cancel one job (if still running)
    if jobs:
        job_to_cancel = jobs[0]
        if basic_training.get_training_progress(job_to_cancel.job_id):
            success = basic_training.cancel_training(job_to_cancel.job_id)
            if success:
                print(f"   ✓ Cancelled training job: {job_to_cancel.job_id[:8]}...")
    
    print("\n6. Final Results...")
    
    # Get results for completed jobs
    for job in jobs:
        result = basic_training.get_training_result(job.job_id)
        if result:
            print(f"   ✓ {result.model_name}: {result.performance_summary[:50]}...")


async def main():
    """Run all demos."""
    print("BASIC TRAINING MODE COMPREHENSIVE DEMO")
    print("=" * 80)
    print("This demo showcases the simplified training interface with preset")
    print("configurations, automatic parameter selection, user-friendly progress")
    print("monitoring, and comprehensive system reset capabilities.")
    print("=" * 80)
    
    try:
        # Run all demo sections
        await demo_training_presets()
        await demo_basic_training()
        await demo_progress_monitoring()
        await demo_system_reset()
        await demo_integration()
        
        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✓ Training presets with automatic hardware optimization")
        print("✓ Simplified training workflow with guided configuration")
        print("✓ Real-time progress monitoring with user-friendly metrics")
        print("✓ Plain-language performance summaries and recommendations")
        print("✓ Comprehensive system backup and restore capabilities")
        print("✓ Factory reset with user data preservation options")
        print("✓ Multi-job training management and monitoring")
        print("\nThe Basic Training Mode provides an intuitive interface for")
        print("users to train models without technical complexity while")
        print("maintaining full system control and recovery options.")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())