# Basic Training Mode

The Basic Training Mode provides a simplified training interface with preset configurations, automatic parameter selection, user-friendly progress monitoring, and comprehensive system reset capabilities. This module implements requirement 16 from the Response Core orchestrator specification.

## Overview

Basic Training Mode is designed to make model training accessible to users without deep technical expertise while maintaining enterprise-grade functionality. It provides:

- **Preset Configurations**: Pre-defined training configurations optimized for different use cases
- **Automatic Parameter Selection**: Hardware-aware parameter optimization
- **User-Friendly Monitoring**: Plain-language progress updates and recommendations
- **System Reset Capabilities**: Comprehensive backup and restore functionality

## Key Components

### BasicTrainingPresets

Provides pre-defined training configurations for common use cases:

- **Quick Test**: Fast training for experimentation (15-30 minutes)
- **Chat Fine-tuning**: Optimized for conversational AI (2-6 hours)
- **Code Assistant**: Specialized for code generation (3-8 hours)
- **Domain Expert**: Deep specialization training (8-24 hours)

Each preset includes:
- Training type (LoRA, fine-tuning, etc.)
- Optimized hyperparameters
- Hardware requirements
- Estimated training time
- Recommended use cases

### ProgressMonitor

Provides user-friendly progress monitoring with:

- **Real-time Updates**: Progress percentage, time estimates, loss metrics
- **Plain Language Status**: Non-technical status messages
- **Intelligent Warnings**: Automatic detection of training issues
- **Helpful Recommendations**: Suggestions for optimization

### SystemResetManager

Comprehensive backup and restore functionality:

- **Configuration Backups**: Complete system state snapshots
- **Selective Restore**: Restore specific components
- **Factory Reset**: Return to default settings with data preservation options
- **Backup Management**: List, delete, and manage backup versions

## Usage Examples

### Basic Training Workflow

```python
from ai_karen_engine.core.response.basic_training_mode import BasicTrainingMode

# Initialize basic training mode
basic_training = BasicTrainingMode(
    training_interface,
    training_data_manager,
    system_model_manager,
    enhanced_hf_service
)

# Get recommended presets for current hardware
presets = await basic_training.get_recommended_presets()

# Start training with automatic configuration
job = await basic_training.start_basic_training(
    model_id="microsoft/DialoGPT-medium",
    dataset_id="my_chat_dataset",
    preset_name="chat_fine_tune"
)

# Monitor progress
progress = basic_training.get_training_progress(job.job_id)
print(f"Status: {progress.status}")
print(f"Progress: {progress.progress_percentage:.1f}%")
print(f"Estimated remaining: {progress.estimated_remaining}")

# Get results when complete
result = basic_training.get_training_result(job.job_id)
print(f"Performance: {result.performance_summary}")
```

### System Backup and Reset

```python
# Create system backup
backup = basic_training.create_system_backup("Pre-training backup")

# List available backups
backups = basic_training.list_system_backups()

# Restore from backup
success = basic_training.restore_system_backup(backup.backup_id)

# Factory reset with user data preservation
success = basic_training.reset_to_factory_defaults(preserve_user_data=True)
```

### Training Presets

```python
# Get preset for specific model
preset = await basic_training.get_preset_for_model("microsoft/CodeBERT-base")

# Get all recommended presets
presets = await basic_training.get_recommended_presets()

# Access preset details
for preset in presets:
    print(f"{preset.name}: {preset.description}")
    print(f"Difficulty: {preset.difficulty}")
    print(f"Estimated time: {preset.estimated_time}")
    print(f"Memory required: {preset.memory_requirements_gb}GB")
```

## API Endpoints

The basic training mode is exposed through REST API endpoints:

### Training Operations
- `GET /api/basic-training/presets` - Get recommended presets
- `GET /api/basic-training/presets/{model_id}` - Get preset for model
- `POST /api/basic-training/start` - Start basic training
- `GET /api/basic-training/progress/{job_id}` - Get training progress
- `GET /api/basic-training/result/{job_id}` - Get training results
- `POST /api/basic-training/cancel/{job_id}` - Cancel training

### System Management
- `POST /api/basic-training/backup` - Create system backup
- `GET /api/basic-training/backups` - List all backups
- `POST /api/basic-training/restore` - Restore from backup
- `DELETE /api/basic-training/backup/{backup_id}` - Delete backup
- `POST /api/basic-training/reset` - Factory reset

### Status and Health
- `GET /api/basic-training/status` - Get system status

## Training Presets Details

### Quick Test
- **Purpose**: Fast experimentation and testing
- **Training Type**: LoRA Adaptation
- **Duration**: 15-30 minutes
- **Memory**: 2GB
- **Configuration**: 1 epoch, LR=3e-4, batch_size=4
- **Best for**: Learning, testing, quick experiments

### Chat Fine-tuning
- **Purpose**: Conversational AI optimization
- **Training Type**: Fine-tuning
- **Duration**: 2-6 hours
- **Memory**: 6GB
- **Configuration**: 3 epochs, LR=2e-5, batch_size=8
- **Best for**: Chat applications, customer support

### Code Assistant
- **Purpose**: Code generation and assistance
- **Training Type**: LoRA Adaptation
- **Duration**: 3-8 hours
- **Memory**: 8GB
- **Configuration**: 5 epochs, LR=1e-4, batch_size=4, max_length=1024
- **Best for**: Programming assistance, technical documentation

### Domain Expert
- **Purpose**: Deep domain specialization
- **Training Type**: Fine-tuning
- **Duration**: 8-24 hours
- **Memory**: 12GB
- **Configuration**: 10 epochs, LR=1e-5, batch_size=16
- **Best for**: Professional applications, specialized knowledge

## Hardware Optimization

The system automatically adjusts configurations based on available hardware:

### GPU Memory Optimization
- **24GB+**: Full preset configurations
- **16GB**: Reduced batch sizes, optimized sequences
- **8GB**: Small batch sizes, gradient checkpointing
- **4GB**: Minimal configurations, CPU fallback

### CPU-Only Training
- **Batch Size**: Limited to 1-2
- **Precision**: FP32 only
- **Memory**: Uses system RAM efficiently
- **Recommendations**: Suggests GPU acceleration when beneficial

### Mixed Precision Support
- **Automatic Detection**: Checks hardware capabilities
- **Fallback**: Graceful degradation to FP32
- **Memory Savings**: Up to 50% reduction in memory usage

## Progress Monitoring Features

### Real-Time Metrics
- **Progress Percentage**: Based on steps or epochs
- **Time Estimates**: Elapsed and remaining time
- **Loss Tracking**: Current and best loss values
- **Resource Usage**: Memory and GPU utilization

### User-Friendly Status
- **Plain Language**: Non-technical status messages
- **Stage Descriptions**: Clear explanation of current activity
- **Completion Estimates**: Realistic time predictions

### Intelligent Warnings
- **Stalled Training**: Detects lack of progress
- **Memory Issues**: High memory usage alerts
- **Loss Problems**: Identifies convergence issues
- **Performance Degradation**: Suggests optimizations

### Helpful Recommendations
- **Parameter Adjustments**: Learning rate, batch size suggestions
- **Hardware Optimization**: Memory and compute recommendations
- **Training Strategy**: Alternative approaches when needed

## System Reset Capabilities

### Backup Types
- **Configuration Backup**: Model settings, training parameters
- **Full System Backup**: Complete system state
- **Selective Backup**: Specific components only

### Restore Options
- **Complete Restore**: Full system state restoration
- **Selective Restore**: Specific components only
- **Merge Restore**: Combine with current settings

### Factory Reset
- **Default Settings**: Return to original configuration
- **User Data Preservation**: Optional data retention
- **Backup Creation**: Automatic pre-reset backup

## Error Handling and Recovery

### Training Failures
- **Automatic Recovery**: Retry with adjusted parameters
- **Fallback Configurations**: Simpler settings on failure
- **User Guidance**: Clear error messages and suggestions

### System Issues
- **Graceful Degradation**: Continue with reduced functionality
- **Backup Restoration**: Automatic rollback on critical failures
- **Health Monitoring**: Continuous system status checks

### User Support
- **Plain Language Errors**: Non-technical error descriptions
- **Recovery Suggestions**: Step-by-step resolution guidance
- **Support Information**: Contact details and resources

## Integration Points

### Training Interface
- Uses `FlexibleTrainingInterface` for actual training operations
- Provides simplified wrapper with preset configurations
- Maintains compatibility with advanced training features

### System Model Manager
- Integrates with model configuration management
- Supports model-specific optimizations
- Provides hardware compatibility checking

### Enhanced HuggingFace Service
- Uses model discovery and compatibility features
- Supports automatic model selection and optimization
- Provides training framework integration

### Training Data Manager
- Integrates with data management capabilities
- Supports dataset validation and preprocessing
- Provides data quality assessment

## Security and Privacy

### Data Protection
- **Local Processing**: All training data remains local
- **Encrypted Backups**: Secure backup storage
- **Access Controls**: Role-based permissions

### System Security
- **Backup Integrity**: Checksum validation
- **Secure Restore**: Verification before restoration
- **Audit Logging**: Complete operation tracking

### Privacy Preservation
- **No External Calls**: Fully local operation
- **Data Anonymization**: Optional sensitive data handling
- **User Consent**: Explicit permission for data operations

## Performance Considerations

### Memory Management
- **Efficient Allocation**: Optimized memory usage patterns
- **Garbage Collection**: Automatic cleanup of temporary data
- **Memory Monitoring**: Real-time usage tracking

### Compute Optimization
- **Hardware Detection**: Automatic capability assessment
- **Resource Allocation**: Optimal CPU/GPU utilization
- **Batch Processing**: Efficient data processing patterns

### Storage Efficiency
- **Compressed Backups**: Space-efficient storage
- **Incremental Backups**: Only store changes
- **Cleanup Automation**: Automatic old backup removal

## Testing and Validation

### Unit Tests
- **Component Testing**: Individual module validation
- **Mock Integration**: Isolated functionality testing
- **Error Scenarios**: Failure condition handling

### Integration Tests
- **End-to-End Workflows**: Complete training cycles
- **API Testing**: REST endpoint validation
- **Performance Testing**: Load and stress testing

### User Acceptance Testing
- **Usability Testing**: User experience validation
- **Documentation Testing**: Guide accuracy verification
- **Accessibility Testing**: Interface accessibility compliance

## Future Enhancements

### Planned Features
- **Advanced Presets**: More specialized configurations
- **Custom Preset Creation**: User-defined presets
- **Training Analytics**: Detailed performance analysis
- **Collaborative Training**: Multi-user training coordination

### Integration Improvements
- **Cloud Acceleration**: Optional cloud training support
- **Distributed Training**: Multi-GPU and multi-node support
- **Model Marketplace**: Integration with model sharing platforms

### User Experience
- **Visual Progress**: Graphical training visualization
- **Mobile Interface**: Mobile-friendly monitoring
- **Voice Notifications**: Audio progress updates
- **Smart Recommendations**: AI-powered optimization suggestions

## Troubleshooting

### Common Issues

#### Training Won't Start
- Check model compatibility
- Verify dataset availability
- Ensure sufficient hardware resources
- Review preset requirements

#### Slow Training Progress
- Reduce batch size
- Enable gradient checkpointing
- Check memory usage
- Consider simpler preset

#### High Memory Usage
- Enable mixed precision
- Reduce sequence length
- Use gradient checkpointing
- Switch to CPU training

#### Training Fails
- Check error messages
- Review hardware requirements
- Try simpler configuration
- Restore from backup if needed

### Support Resources
- **Documentation**: Comprehensive guides and examples
- **Demo Scripts**: Working example implementations
- **Test Suite**: Validation and debugging tools
- **Community Support**: User forums and discussions

This Basic Training Mode implementation provides a complete solution for simplified model training while maintaining enterprise-grade capabilities and user-friendly interfaces.