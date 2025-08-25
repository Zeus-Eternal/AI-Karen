"""
Demo script for the Flexible Model Training Interface.

This script demonstrates the key features of the training interface including:
- Model compatibility checking
- Training environment setup
- Basic and advanced training modes
- Hardware constraint validation
- Training job management
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.response.training_interface import (
    FlexibleTrainingInterface,
    HardwareConstraints,
    BasicTrainingConfig,
    AdvancedTrainingConfig,
    TrainingType,
    TrainingMode
)
from ai_karen_engine.services.enhanced_huggingface_service import EnhancedHuggingFaceService, TrainableModel
from ai_karen_engine.core.response.training_data_manager import TrainingDataManager
from ai_karen_engine.services.system_model_manager import SystemModelManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockEnhancedHuggingFaceService:
    """Mock enhanced HuggingFace service for demo purposes."""
    
    async def get_model_info(self, model_id: str):
        """Mock getting model information."""
        # Return different models based on ID for demo
        if "gpt2" in model_id.lower():
            return TrainableModel(
                id=model_id,
                name="GPT-2 Small",
                family="gpt",
                parameters="124M",
                tags=["text-generation", "transformers"],
                downloads=50000,
                likes=1000,
                supports_fine_tuning=True,
                supports_lora=True,
                supports_full_training=True,
                training_frameworks=["transformers", "peft"],
                training_complexity="easy"
            )
        elif "bert" in model_id.lower():
            return TrainableModel(
                id=model_id,
                name="BERT Base",
                family="bert",
                parameters="110M",
                tags=["fill-mask", "transformers"],
                downloads=100000,
                likes=2000,
                supports_fine_tuning=True,
                supports_lora=True,
                supports_full_training=True,
                training_frameworks=["transformers"],
                training_complexity="easy"
            )
        elif "llama" in model_id.lower():
            return TrainableModel(
                id=model_id,
                name="LLaMA 7B",
                family="llama",
                parameters="7B",
                tags=["text-generation", "transformers"],
                downloads=25000,
                likes=5000,
                supports_fine_tuning=True,
                supports_lora=True,
                supports_full_training=False,  # Too large for full training
                training_frameworks=["transformers", "peft"],
                training_complexity="medium"
            )
        else:
            return None
    
    async def search_models(self, query: str, filters: dict = None):
        """Mock searching for models."""
        # Return some sample trainable models
        models = [
            await self.get_model_info("gpt2"),
            await self.get_model_info("bert-base-uncased"),
            await self.get_model_info("meta-llama/Llama-2-7b-hf")
        ]
        return [model for model in models if model is not None]


class MockTrainingDataManager:
    """Mock training data manager for demo purposes."""
    
    def get_dataset(self, dataset_id: str):
        """Mock getting dataset."""
        return f"Mock dataset: {dataset_id}"


class MockSystemModelManager:
    """Mock system model manager for demo purposes."""
    
    def get_model_info(self, model_id: str):
        """Mock getting system model info."""
        return f"Mock system model: {model_id}"


async def demo_hardware_detection():
    """Demonstrate hardware constraint detection."""
    print("\n" + "="*60)
    print("HARDWARE CONSTRAINT DETECTION")
    print("="*60)
    
    constraints = HardwareConstraints.detect_current()
    
    print(f"Available System Memory: {constraints.available_memory_gb:.1f} GB")
    print(f"Available GPU Memory: {constraints.available_gpu_memory_gb:.1f} GB")
    print(f"GPU Count: {constraints.gpu_count}")
    print(f"CPU Cores: {constraints.cpu_cores}")
    print(f"Supports Mixed Precision: {constraints.supports_mixed_precision}")
    print(f"Supports Gradient Checkpointing: {constraints.supports_gradient_checkpointing}")
    print(f"Recommended Precision: {constraints.recommended_precision}")
    
    return constraints


async def demo_model_compatibility(training_interface: FlexibleTrainingInterface):
    """Demonstrate model compatibility checking."""
    print("\n" + "="*60)
    print("MODEL COMPATIBILITY CHECKING")
    print("="*60)
    
    test_models = [
        ("gpt2", TrainingType.FINE_TUNING),
        ("bert-base-uncased", TrainingType.LORA_ADAPTATION),
        ("meta-llama/Llama-2-7b-hf", TrainingType.FULL_TRAINING),
        ("nonexistent/model", TrainingType.FINE_TUNING)
    ]
    
    for model_id, training_type in test_models:
        print(f"\nChecking compatibility: {model_id} for {training_type.value}")
        print("-" * 50)
        
        try:
            compatibility = await training_interface.check_model_compatibility(
                model_id, training_type
            )
            
            print(f"Compatible: {compatibility.is_compatible}")
            print(f"Supports Fine-tuning: {compatibility.supports_fine_tuning}")
            print(f"Supports LoRA: {compatibility.supports_lora}")
            print(f"Supports Full Training: {compatibility.supports_full_training}")
            print(f"Required Memory: {compatibility.required_memory_gb:.1f} GB")
            print(f"Required GPU Memory: {compatibility.required_gpu_memory_gb:.1f} GB")
            print(f"Recommended Batch Size: {compatibility.recommended_batch_size}")
            print(f"Training Frameworks: {', '.join(compatibility.training_frameworks)}")
            print(f"Estimated Training Time: {compatibility.estimated_training_time}")
            
            if compatibility.compatibility_issues:
                print(f"Issues: {', '.join(compatibility.compatibility_issues)}")
            
            if compatibility.recommendations:
                print("Recommendations:")
                for rec in compatibility.recommendations:
                    print(f"  - {rec}")
                    
        except Exception as e:
            print(f"Error: {e}")


async def demo_training_environment(training_interface: FlexibleTrainingInterface):
    """Demonstrate training environment setup."""
    print("\n" + "="*60)
    print("TRAINING ENVIRONMENT SETUP")
    print("="*60)
    
    try:
        environment = await training_interface.setup_training_environment(
            "gpt2",
            TrainingType.FINE_TUNING,
            TrainingMode.BASIC
        )
        
        print(f"Model ID: {environment.model_id}")
        print(f"Training Type: {environment.training_type.value}")
        print(f"Training Mode: {environment.training_mode.value}")
        print(f"Output Directory: {environment.output_dir}")
        print(f"Temp Directory: {environment.temp_dir}")
        print(f"Logs Directory: {environment.logs_dir}")
        print(f"Environment Ready: {environment.environment_ready}")
        
        if environment.setup_errors:
            print("Setup Errors:")
            for error in environment.setup_errors:
                print(f"  - {error}")
        
        print(f"Hardware - Memory: {environment.hardware_constraints.available_memory_gb:.1f} GB")
        print(f"Hardware - GPU Memory: {environment.hardware_constraints.available_gpu_memory_gb:.1f} GB")
        
    except Exception as e:
        print(f"Error setting up environment: {e}")


async def demo_basic_training(training_interface: FlexibleTrainingInterface):
    """Demonstrate basic training job creation and management."""
    print("\n" + "="*60)
    print("BASIC TRAINING JOB MANAGEMENT")
    print("="*60)
    
    try:
        # Create basic training configuration
        config = BasicTrainingConfig(
            model_id="gpt2",
            dataset_id="demo_dataset",
            training_type=TrainingType.FINE_TUNING,
            num_epochs=3,
            learning_rate=2e-5,
            batch_size=8,
            max_length=512,
            use_mixed_precision=True,
            gradient_checkpointing=True
        )
        
        print("Creating basic training job...")
        print(f"Model: {config.model_id}")
        print(f"Dataset: {config.dataset_id}")
        print(f"Training Type: {config.training_type.value}")
        print(f"Epochs: {config.num_epochs}")
        print(f"Learning Rate: {config.learning_rate}")
        print(f"Batch Size: {config.batch_size}")
        
        # Create training job
        job = await training_interface.create_basic_training_job(config)
        
        print(f"\nTraining job created successfully!")
        print(f"Job ID: {job.job_id}")
        print(f"Status: {job.status.value}")
        print(f"Created: {job.created_at}")
        print(f"Total Epochs: {job.total_epochs}")
        print(f"Output Directory: {job.output_dir}")
        
        # Start the training job
        print(f"\nStarting training job {job.job_id}...")
        success = await training_interface.start_training_job(job.job_id)
        
        if success:
            print("Training job started successfully!")
            
            # Check job status
            updated_job = training_interface.get_training_job(job.job_id)
            print(f"Updated Status: {updated_job.status.value}")
            
            # Wait a bit and check progress
            await asyncio.sleep(2)
            updated_job = training_interface.get_training_job(job.job_id)
            print(f"Progress: {updated_job.progress:.1%}")
            print(f"Current Epoch: {updated_job.current_epoch}/{updated_job.total_epochs}")
            
            if updated_job.logs:
                print("Recent Logs:")
                for log in updated_job.logs[-3:]:  # Show last 3 logs
                    print(f"  {log}")
        else:
            print("Failed to start training job")
            
        return job.job_id
        
    except Exception as e:
        print(f"Error in basic training demo: {e}")
        return None


async def demo_advanced_training(training_interface: FlexibleTrainingInterface):
    """Demonstrate advanced training job creation."""
    print("\n" + "="*60)
    print("ADVANCED TRAINING JOB MANAGEMENT")
    print("="*60)
    
    try:
        # Create advanced training configuration
        config = AdvancedTrainingConfig(
            model_id="bert-base-uncased",
            dataset_id="advanced_dataset",
            training_type=TrainingType.LORA_ADAPTATION,
            learning_rate=1e-4,
            weight_decay=0.01,
            num_epochs=5,
            per_device_train_batch_size=16,
            gradient_accumulation_steps=2,
            max_length=256,
            fp16=True,
            gradient_checkpointing=True,
            lora_r=32,
            lora_alpha=64,
            lora_dropout=0.1,
            lora_target_modules=["query", "value", "key"],
            logging_steps=50,
            save_steps=1000,
            eval_steps=500
        )
        
        print("Creating advanced training job...")
        print(f"Model: {config.model_id}")
        print(f"Training Type: {config.training_type.value}")
        print(f"Learning Rate: {config.learning_rate}")
        print(f"Weight Decay: {config.weight_decay}")
        print(f"Batch Size: {config.per_device_train_batch_size}")
        print(f"Gradient Accumulation: {config.gradient_accumulation_steps}")
        print(f"Mixed Precision: FP16={config.fp16}, BF16={config.bf16}")
        print(f"LoRA Config: r={config.lora_r}, alpha={config.lora_alpha}, dropout={config.lora_dropout}")
        print(f"LoRA Targets: {', '.join(config.lora_target_modules)}")
        
        # Create training job
        job = await training_interface.create_advanced_training_job(config)
        
        print(f"\nAdvanced training job created successfully!")
        print(f"Job ID: {job.job_id}")
        print(f"Status: {job.status.value}")
        print(f"Training Mode: {job.training_mode.value}")
        
        return job.job_id
        
    except Exception as e:
        print(f"Error in advanced training demo: {e}")
        return None


async def demo_job_management(training_interface: FlexibleTrainingInterface, job_ids: list):
    """Demonstrate training job management operations."""
    print("\n" + "="*60)
    print("TRAINING JOB MANAGEMENT")
    print("="*60)
    
    # List all jobs
    jobs = training_interface.list_training_jobs()
    print(f"Total active jobs: {len(jobs)}")
    
    for job in jobs:
        print(f"\nJob {job.job_id}:")
        print(f"  Model: {job.model_id}")
        print(f"  Type: {job.training_type.value}")
        print(f"  Mode: {job.training_mode.value}")
        print(f"  Status: {job.status.value}")
        print(f"  Progress: {job.progress:.1%}")
        print(f"  Created: {job.created_at}")
        
        if job.error_message:
            print(f"  Error: {job.error_message}")
    
    # Demonstrate job cancellation
    if job_ids:
        job_id = job_ids[0]
        print(f"\nCancelling job {job_id}...")
        
        success = await training_interface.cancel_training_job(job_id)
        if success:
            print("Job cancelled successfully!")
            
            # Check updated status
            updated_job = training_interface.get_training_job(job_id)
            print(f"Updated Status: {updated_job.status.value}")
        else:
            print("Failed to cancel job")


async def demo_trainable_models(training_interface: FlexibleTrainingInterface):
    """Demonstrate getting trainable models."""
    print("\n" + "="*60)
    print("TRAINABLE MODELS DISCOVERY")
    print("="*60)
    
    try:
        models = await training_interface.get_trainable_models()
        
        print(f"Found {len(models)} trainable models:")
        
        for model in models:
            print(f"\nModel: {model.id}")
            print(f"  Name: {model.name}")
            print(f"  Family: {model.family}")
            print(f"  Parameters: {model.parameters}")
            print(f"  Fine-tuning: {getattr(model, 'supports_fine_tuning', False)}")
            print(f"  LoRA: {getattr(model, 'supports_lora', False)}")
            print(f"  Full Training: {getattr(model, 'supports_full_training', False)}")
            print(f"  Complexity: {getattr(model, 'training_complexity', 'unknown')}")
            print(f"  Frameworks: {', '.join(getattr(model, 'training_frameworks', []))}")
            print(f"  Downloads: {model.downloads:,}")
            print(f"  Likes: {model.likes:,}")
            
    except Exception as e:
        print(f"Error getting trainable models: {e}")


async def main():
    """Run the complete training interface demo."""
    print("="*60)
    print("FLEXIBLE MODEL TRAINING INTERFACE DEMO")
    print("="*60)
    
    # Initialize mock services
    enhanced_hf_service = MockEnhancedHuggingFaceService()
    training_data_manager = MockTrainingDataManager()
    system_model_manager = MockSystemModelManager()
    
    # Create training interface
    training_interface = FlexibleTrainingInterface(
        enhanced_hf_service=enhanced_hf_service,
        training_data_manager=training_data_manager,
        system_model_manager=system_model_manager,
        base_dir="./demo_training_environments"
    )
    
    try:
        # Run all demos
        hardware_constraints = await demo_hardware_detection()
        await demo_model_compatibility(training_interface)
        await demo_training_environment(training_interface)
        
        # Create training jobs
        job_ids = []
        
        basic_job_id = await demo_basic_training(training_interface)
        if basic_job_id:
            job_ids.append(basic_job_id)
        
        advanced_job_id = await demo_advanced_training(training_interface)
        if advanced_job_id:
            job_ids.append(advanced_job_id)
        
        # Demonstrate job management
        if job_ids:
            await demo_job_management(training_interface, job_ids)
        
        # Demonstrate model discovery
        await demo_trainable_models(training_interface)
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Hardware constraint detection")
        print("✓ Model compatibility checking")
        print("✓ Training environment setup")
        print("✓ Basic training job creation")
        print("✓ Advanced training job creation")
        print("✓ Training job management")
        print("✓ Trainable model discovery")
        print("\nThe training interface provides a comprehensive solution for:")
        print("- Model compatibility validation")
        print("- Hardware constraint checking")
        print("- Environment setup and management")
        print("- Multiple training modes (basic/advanced)")
        print("- Support for different training types (fine-tuning, LoRA, full training)")
        print("- Real-time job monitoring and management")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())