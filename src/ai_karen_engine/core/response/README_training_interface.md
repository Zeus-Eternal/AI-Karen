# Flexible Model Training Interface

The Flexible Model Training Interface provides comprehensive model training capabilities for the Response Core orchestrator, including model compatibility checking, training environment setup, and support for different training modes with hardware constraint validation.

## Overview

This interface implements the requirements for task 11 of the Response Core Orchestrator specification:
- Model compatibility checking and training environment setup
- Basic and advanced training modes with different complexity levels
- Support for fine-tuning, continued pre-training, and task-specific adaptation
- Training parameter validation and hardware constraint checking

## Key Features

### 🔍 Model Compatibility Checking
- Automatic detection of training capabilities (fine-tuning, LoRA, full training)
- Hardware requirement estimation and validation
- Framework compatibility assessment
- Training time estimation

### 🏗️ Training Environment Management
- Automated environment setup with proper directory structure
- Hardware constraint detection and validation
- Environment cleanup and resource management
- Disk space and permission validation

### 🎯 Multiple Training Modes
- **Basic Mode**: Preset configurations for easy training
- **Advanced Mode**: Full control over training parameters
- **Expert Mode**: Custom training logic and mathematical parameters

### 🚀 Training Types Support
- **Fine-tuning**: Adapt pre-trained models to specific tasks
- **LoRA Adaptation**: Parameter-efficient fine-tuning
- **Continued Pre-training**: Continue training on domain-specific data
- **Task-specific Adaptation**: Specialized training for specific use cases
- **Full Training**: Complete model training from scratch

### 💻 Hardware Optimization
- Automatic hardware detection (CPU, GPU, memory)
- Mixed precision training support
- Gradient checkpointing for memory efficiency
- Multi-GPU training recommendations
- Batch size optimization based on available resources

## Architecture

```
FlexibleTrainingInterface
├── ModelCompatibilityChecker
│   ├── Hardware requirement estimation
│   ├── Framework compatibility checking
│   └── Training capability detection
├── TrainingEnvironmentManager
│   ├── Directory structure setup
│   ├── Environment validation
│   └── Resource cleanup
├── TrainingParameterValidator
│   ├── Basic configuration validation
│   ├── Advanced parameter checking
│   └── Hardware constraint validation
└── Training Job Management
    ├── Job creation and tracking
    ├── Progress monitoring
    └── Status management
```

## Usage Examples

### Basic Training Job

```python
from ai_karen_engine.core.response.training_interface import (
    FlexibleTrainingInterface,
    BasicTrainingConfig,
    TrainingType
)

# Initialize interface
training_interface = FlexibleTrainingInterface(
    enhanced_hf_service=enhanced_hf_service,
    training_data_manager=training_data_manager,
    system_model_manager=system_model_manager
)

# Check model compatibility
compatibility = await training_interface.check_model_compatibility(
    "microsoft/DialoGPT-medium",
    TrainingType.FINE_TUNING
)

if compatibility.is_compatible:
    # Create basic training configuration
    config = BasicTrainingConfig(
        model_id="microsoft/DialoGPT-medium",
        dataset_id="conversation_dataset",
        training_type=TrainingType.FINE_TUNING,
        num_epochs=3,
        learning_rate=2e-5,
        batch_size=8
    )
    
    # Create and start training job
    job = await training_interface.create_basic_training_job(config)
    await training_interface.start_training_job(job.job_id)
    
    # Monitor progress
    updated_job = training_interface.get_training_job(job.job_id)
    print(f"Progress: {updated_job.progress:.1%}")
```

### Advanced Training Job

```python
from ai_karen_engine.core.response.training_interface import (
    AdvancedTrainingConfig,
    TrainingType
)

# Create advanced configuration with full control
config = AdvancedTrainingConfig(
    model_id="microsoft/DialoGPT-medium",
    dataset_id="conversation_dataset",
    training_type=TrainingType.LORA_ADAPTATION,
    
    # Learning parameters
    learning_rate=1e-4,
    weight_decay=0.01,
    adam_beta1=0.9,
    adam_beta2=0.999,
    
    # Training schedule
    num_epochs=5,
    warmup_steps=100,
    lr_scheduler_type="cosine",
    
    # Batch settings
    per_device_train_batch_size=16,
    gradient_accumulation_steps=2,
    
    # Optimization
    fp16=True,
    gradient_checkpointing=True,
    
    # LoRA settings
    lora_r=32,
    lora_alpha=64,
    lora_dropout=0.1,
    lora_target_modules=["q_proj", "v_proj", "k_proj"]
)

job = await training_interface.create_advanced_training_job(config)
```

### Hardware Constraint Detection

```python
from ai_karen_engine.core.response.training_interface import HardwareConstraints

# Detect current hardware
constraints = HardwareConstraints.detect_current()

print(f"Available Memory: {constraints.available_memory_gb:.1f} GB")
print(f"GPU Memory: {constraints.available_gpu_memory_gb:.1f} GB")
print(f"GPU Count: {constraints.gpu_count}")
print(f"Mixed Precision Support: {constraints.supports_mixed_precision}")
print(f"Recommended Precision: {constraints.recommended_precision}")
```

## API Endpoints

The training interface provides REST API endpoints for web integration:

### Model Compatibility
- `POST /api/training/compatibility/check` - Check model compatibility
- `GET /api/training/models/trainable` - Get trainable models list

### Training Jobs
- `POST /api/training/jobs/basic` - Create basic training job
- `POST /api/training/jobs/advanced` - Create advanced training job
- `POST /api/training/jobs/{job_id}/start` - Start training job
- `POST /api/training/jobs/{job_id}/cancel` - Cancel training job
- `GET /api/training/jobs/{job_id}` - Get job details
- `GET /api/training/jobs` - List all jobs

### Hardware Information
- `GET /api/training/hardware` - Get hardware constraints

## Configuration Options

### Basic Training Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | str | - | HuggingFace model identifier |
| `dataset_id` | str | - | Training dataset identifier |
| `training_type` | TrainingType | - | Type of training operation |
| `num_epochs` | int | 3 | Number of training epochs |
| `learning_rate` | float | 2e-5 | Learning rate |
| `batch_size` | int | 8 | Training batch size |
| `max_length` | int | 512 | Maximum sequence length |
| `use_mixed_precision` | bool | True | Enable mixed precision |
| `gradient_checkpointing` | bool | True | Enable gradient checkpointing |

### Advanced Training Configuration

Includes all basic parameters plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `weight_decay` | float | 0.01 | Weight decay for regularization |
| `adam_beta1` | float | 0.9 | Adam optimizer beta1 |
| `adam_beta2` | float | 0.999 | Adam optimizer beta2 |
| `lr_scheduler_type` | str | "linear" | Learning rate scheduler |
| `gradient_accumulation_steps` | int | 1 | Gradient accumulation steps |
| `fp16` | bool | False | Use FP16 precision |
| `bf16` | bool | False | Use BF16 precision |
| `lora_r` | int | 16 | LoRA rank |
| `lora_alpha` | int | 32 | LoRA alpha parameter |
| `lora_dropout` | float | 0.1 | LoRA dropout rate |

## Hardware Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 10 GB free space
- **Python**: 3.8+

### Recommended for GPU Training
- **GPU**: NVIDIA GPU with 8+ GB VRAM
- **RAM**: 16+ GB
- **Storage**: 50+ GB SSD
- **CUDA**: 11.0+

### Supported Training Types by Hardware

| Training Type | CPU Only | Single GPU | Multi-GPU |
|---------------|----------|------------|-----------|
| Fine-tuning (small models) | ✅ | ✅ | ✅ |
| LoRA Adaptation | ✅ | ✅ | ✅ |
| Fine-tuning (large models) | ⚠️ | ✅ | ✅ |
| Full Training | ❌ | ⚠️ | ✅ |

## Error Handling

The interface provides comprehensive error handling:

### Compatibility Issues
- Model not found or inaccessible
- Insufficient hardware resources
- Unsupported training type
- Framework compatibility problems

### Environment Issues
- Insufficient disk space
- Permission problems
- Missing dependencies
- CUDA availability problems

### Training Issues
- Invalid parameters
- Data loading failures
- Out of memory errors
- Training convergence problems

## Integration with Existing Systems

### Enhanced HuggingFace Service
- Model discovery and metadata
- Automatic compatibility detection
- Download progress tracking

### Training Data Manager
- Dataset management and validation
- Format conversion and preprocessing
- Version control and provenance

### System Model Manager
- Local model management
- Configuration and optimization
- Performance monitoring

## Performance Considerations

### Memory Optimization
- Gradient checkpointing for large models
- Mixed precision training (FP16/BF16)
- Dynamic batch size adjustment
- Model sharding for multi-GPU setups

### Training Speed
- Optimized data loading with multiple workers
- Efficient gradient accumulation
- Learning rate scheduling
- Early stopping and validation

### Resource Management
- Automatic cleanup of temporary files
- Model checkpoint management
- Memory monitoring and alerts
- Disk space management

## Security and Privacy

### Local-First Training
- All training happens locally by default
- No data sent to external services
- Model weights stored locally
- Complete control over training process

### Access Control
- RBAC integration for admin features
- Audit logging for training operations
- Secure model storage and versioning
- Training data access controls

## Monitoring and Observability

### Training Metrics
- Loss curves and validation metrics
- Learning rate schedules
- Gradient norms and statistics
- Memory usage tracking

### Job Monitoring
- Real-time progress updates
- Status tracking and alerts
- Error reporting and diagnostics
- Performance benchmarking

### System Metrics
- Hardware utilization
- Resource consumption
- Training throughput
- Model performance metrics

## Future Enhancements

### Planned Features
- Distributed training across multiple nodes
- Automatic hyperparameter optimization
- Model compression and quantization
- Advanced training strategies (curriculum learning, etc.)

### Integration Roadmap
- Integration with MLflow for experiment tracking
- Support for custom training frameworks
- Advanced model evaluation and testing
- Production deployment automation

## Troubleshooting

### Common Issues

**Out of Memory Errors**
- Reduce batch size
- Enable gradient checkpointing
- Use mixed precision training
- Consider LoRA instead of full fine-tuning

**Slow Training**
- Increase batch size if memory allows
- Use multiple data loading workers
- Enable mixed precision
- Consider multi-GPU training

**Model Compatibility Issues**
- Check model architecture support
- Verify framework compatibility
- Update transformers library
- Check model licensing restrictions

**Environment Setup Failures**
- Verify disk space availability
- Check directory permissions
- Install missing dependencies
- Validate CUDA installation

For more detailed troubleshooting, check the logs in the training job's logs directory.

## Contributing

When contributing to the training interface:

1. Follow the existing code patterns and architecture
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Consider backward compatibility
5. Test with different hardware configurations

## License

This training interface is part of the AI Karen Engine and follows the same licensing terms.