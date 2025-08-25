# Autonomous Learning Engine

The spaCy-based autonomous learning engine enables Karen AI to continuously improve its understanding and responses based on user interactions and curated data. This system integrates seamlessly with the existing spaCy analyzer and memory infrastructure to provide incremental learning capabilities.

## Overview

The autonomous learning engine implements a complete learning pipeline that:

1. **Collects conversation metadata** from user interactions
2. **Curates high-quality training data** from memory storage
3. **Performs incremental training** on spaCy models
4. **Validates model improvements** against test data
5. **Deploys or rolls back** based on validation results
6. **Tracks learning metrics** and history

## Key Components

### AutonomousLearner

The main orchestrator class that coordinates the entire learning pipeline:

```python
from ai_karen_engine.core.response.autonomous_learner import create_autonomous_learner

# Create autonomous learner
learner = create_autonomous_learner(
    spacy_analyzer=spacy_analyzer,
    memory_service=memory_service,
    model_backup_dir=Path("./model_backups")
)

# Collect conversation metadata
metadata = await learner.collect_conversation_metadata(
    tenant_id="tenant_123",
    user_text="How do I optimize this Python code?",
    assistant_response="Here are some optimization techniques...",
    user_id="user_123",
    user_feedback={"satisfaction_score": 0.9, "response_quality": 0.8}
)

# Trigger learning cycle
result = await learner.trigger_learning_cycle("tenant_123")
```

### ConversationMetadataCollector

Collects and curates conversation metadata for training:

- Analyzes user input for intent, sentiment, and entities
- Extracts linguistic features and context information
- Applies quality filters to ensure high-quality training data
- Stores metadata in the memory system for future use

### IncrementalTrainingPipeline

Manages incremental training of spaCy models:

- Creates training examples from conversation metadata
- Backs up current models before training
- Performs incremental updates using spaCy's training API
- Supports rollback to previous model versions

### ModelValidator

Validates trained models against test data:

- Tests intent detection accuracy
- Validates sentiment analysis performance
- Checks entity extraction quality
- Provides detailed error analysis and metrics

## Features

### Conversation Metadata Collection

The system automatically collects rich metadata from every conversation:

```python
@dataclass
class ConversationMetadata:
    conversation_id: str
    user_id: str
    intent_detected: str
    sentiment_detected: str
    persona_selected: str
    user_satisfaction: Optional[float]
    response_quality: Optional[float]
    entities_extracted: List[Tuple[str, str]]
    linguistic_features: Dict[str, Any]
    feedback_provided: bool
    correction_needed: bool
```

### Quality-Based Data Curation

Training data is automatically curated based on quality metrics:

- User satisfaction scores
- Response quality ratings
- Feedback availability
- Correction requirements
- Confidence thresholds

### Incremental Learning

The system supports incremental learning to avoid catastrophic forgetting:

- Preserves existing model knowledge
- Adds new patterns from user interactions
- Maintains performance on previous tasks
- Efficient training with small data batches

### Model Validation and Rollback

Comprehensive validation ensures model quality:

```python
@dataclass
class ValidationResult:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    intent_accuracy: float
    sentiment_accuracy: float
    entity_accuracy: float
    passed_threshold: bool
```

Automatic rollback if validation fails:
- Restores previous model version
- Maintains system stability
- Logs rollback reasons
- Preserves training history

### Learning Metrics and History

Track learning progress over time:

```python
metrics = await learner.get_learning_metrics()
# Returns:
# - Total learning cycles
# - Successful vs failed cycles
# - Model improvements count
# - Average training time
# - Recent cycle history
```

## Integration with Existing Systems

### spaCy Analyzer Integration

The autonomous learner integrates seamlessly with the existing spaCy analyzer:

```python
# Uses existing analyzer for intent detection
intent = await spacy_analyzer._detect_intent_async(user_text)

# Leverages existing sentiment analysis
sentiment = await spacy_analyzer._sentiment_async(user_text)

# Utilizes existing entity extraction
entities = await spacy_analyzer._entities_async(user_text)
```

### Memory System Integration

Stores and retrieves training data through the memory system:

```python
# Store conversation metadata
await memory_service.store_web_ui_memory(
    tenant_id=tenant_id,
    content=content,
    memory_type=MemoryType.INSIGHT,
    tags=["autonomous_learning", "conversation_metadata"],
    ai_generated=True,
    metadata=metadata.to_dict()
)

# Query for training data
memories = await memory_service.query_memories(tenant_id, query)
```

### Chat Orchestrator Integration

Works with the existing chat orchestrator to collect real-time data:

- Intercepts conversation flows
- Extracts metadata without disrupting responses
- Provides feedback mechanisms for users
- Maintains conversation context

## Configuration

### Learning Configuration

```python
learning_config = {
    "min_data_threshold": 50,      # Minimum conversations before training
    "quality_threshold": 0.7,      # Minimum quality score for training data
    "validation_threshold": 0.85,  # Minimum validation score for deployment
    "max_training_examples": 1000, # Maximum examples per training cycle
    "backup_retention_days": 30    # How long to keep model backups
}
```

### Training Configuration

```python
training_config = {
    "n_iter": 10,           # Number of training iterations
    "batch_size": 32,       # Training batch size
    "dropout": 0.2,         # Dropout rate for regularization
    "learn_rate": 0.001,    # Learning rate
    "validation_split": 0.2 # Fraction of data for validation
}
```

### Validation Thresholds

```python
validation_thresholds = {
    "accuracy": 0.85,        # Overall accuracy threshold
    "intent_accuracy": 0.80, # Intent detection accuracy
    "sentiment_accuracy": 0.75, # Sentiment analysis accuracy
    "entity_accuracy": 0.70  # Entity extraction accuracy
}
```

## Usage Examples

### Basic Usage

```python
# Initialize components
spacy_analyzer = create_spacy_analyzer()
memory_service = WebUIMemoryService(base_memory_manager)
learner = create_autonomous_learner(spacy_analyzer, memory_service)

# Collect conversation data
for conversation in conversations:
    await learner.collect_conversation_metadata(
        tenant_id="tenant_123",
        user_text=conversation["user_text"],
        assistant_response=conversation["assistant_response"],
        user_id=conversation["user_id"],
        user_feedback=conversation.get("feedback")
    )

# Trigger learning when enough data is available
result = await learner.trigger_learning_cycle("tenant_123")

if result.model_improved:
    print("Model successfully improved!")
else:
    print(f"Learning cycle failed: {result.error_message}")
```

### Advanced Usage with Custom Configuration

```python
# Create learner with custom configuration
learner = AutonomousLearner(
    spacy_analyzer=spacy_analyzer,
    memory_service=memory_service,
    model_backup_dir=Path("./custom_backups")
)

# Override learning configuration
learner.learning_config.update({
    "min_data_threshold": 100,
    "quality_threshold": 0.8,
    "validation_threshold": 0.9
})

# Force training even with insufficient data
result = await learner.trigger_learning_cycle(
    tenant_id="tenant_123",
    force_training=True
)

# Get detailed metrics
metrics = await learner.get_learning_metrics()
print(f"Total cycles: {metrics['total_cycles']}")
print(f"Success rate: {metrics['successful_cycles'] / metrics['total_cycles']:.2%}")
```

### Scheduled Learning

```python
import asyncio
from datetime import datetime, timedelta

async def scheduled_learning():
    """Run learning cycles on a schedule."""
    while True:
        try:
            # Trigger learning cycle
            result = await learner.trigger_learning_cycle("tenant_123")
            
            if result.model_improved:
                logger.info(f"Model improved: {result.cycle_id}")
            else:
                logger.info(f"No improvement: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Scheduled learning failed: {e}")
        
        # Wait 24 hours before next cycle
        await asyncio.sleep(24 * 60 * 60)

# Start scheduled learning
asyncio.create_task(scheduled_learning())
```

## Error Handling and Recovery

### Graceful Degradation

The system handles failures gracefully:

- **Training failures**: Preserve existing model, log errors
- **Validation failures**: Automatic rollback to previous version
- **Data corruption**: Skip corrupted examples, continue training
- **Memory issues**: Reduce batch size, retry with smaller batches

### Error Recovery

```python
try:
    result = await learner.trigger_learning_cycle("tenant_123")
except Exception as e:
    logger.error(f"Learning cycle failed: {e}")
    
    # Check if rollback is needed
    if hasattr(e, 'backup_path'):
        success = await learner.training_pipeline.rollback_model(e.backup_path)
        if success:
            logger.info("Successfully rolled back to previous model")
```

### Monitoring and Alerts

```python
# Monitor learning metrics
metrics = await learner.get_learning_metrics()

# Alert on high failure rate
failure_rate = metrics['failed_cycles'] / metrics['total_cycles']
if failure_rate > 0.3:  # More than 30% failures
    send_alert(f"High learning failure rate: {failure_rate:.2%}")

# Alert on model degradation
if metrics['last_cycle']['status'] == 'rolled_back':
    send_alert("Model rollback occurred - investigate data quality")
```

## Performance Considerations

### Memory Usage

- Training examples are processed in batches to manage memory
- Model backups are compressed and rotated automatically
- Cache is cleared after training to free memory

### Training Time

- Incremental training is faster than full retraining
- Batch size can be adjusted based on available resources
- Training can be interrupted and resumed

### Storage Requirements

- Model backups require disk space (typically 100-500MB per backup)
- Training data is stored in the memory system
- Logs and metrics are rotated automatically

## Security and Privacy

### Data Privacy

- All training happens locally using the existing spaCy infrastructure
- No external API calls required for core functionality
- User data remains within the system boundaries

### Access Control

- Learning operations require appropriate permissions
- Model backups are stored securely
- Training data access is logged and audited

### Data Sanitization

- Personal information is filtered from training examples
- Sensitive data is excluded from model updates
- User consent is respected for data usage

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_autonomous_learner.py -v
```

Run the demo to see all features:

```bash
python examples/autonomous_learner_demo.py
```

## Requirements Satisfied

This implementation satisfies all requirements from the specification:

- **12.1**: ✅ spaCy works with LLM orchestrator for enhanced reasoning
- **12.2**: ✅ Automatic fallback to spaCy when larger models fail
- **12.3**: ✅ Integration with existing chat orchestrator and memory processor
- **12.4**: ✅ Automatic collection and curation of conversation metadata
- **12.5**: ✅ Autonomous incremental training sessions with prompt-first methodology
- **12.6**: ✅ Model validation and rollback capabilities
- **12.7**: ✅ Fallback to degraded mode if spaCy fails

The autonomous learning engine provides a robust, scalable solution for continuous improvement of Karen AI's understanding and response capabilities while maintaining full integration with the existing infrastructure.