# Training Data Manager

The Training Data Manager is a comprehensive system for managing training datasets used by the Response Core orchestrator. It provides capabilities for dataset curation, editing, upload, validation, format conversion, version control, and automated quality assessment and enhancement.

## Overview

The Training Data Manager addresses the critical need for high-quality, well-managed training data in machine learning systems. It provides:

- **Dataset Management**: Create, organize, and manage multiple training datasets
- **Data Validation**: Comprehensive validation with detailed error reporting and suggestions
- **Format Conversion**: Support for multiple data formats (JSON, CSV, JSONL, spaCy, HuggingFace, Pickle)
- **Version Control**: Full versioning with provenance tracking and rollback capabilities
- **Quality Assessment**: Automated quality metrics and enhancement suggestions
- **Data Enhancement**: Automated cleaning, deduplication, and class balancing
- **Import/Export**: Flexible data exchange with external systems

## Key Features

### 1. Dataset Creation and Management

```python
from ai_karen_engine.core.response.training_data_manager import TrainingDataManager

manager = TrainingDataManager(data_dir="data/training")

# Create a new dataset
dataset_id = manager.create_dataset(
    name="Intent Classification Dataset",
    description="Training data for intent classification",
    created_by="data_scientist",
    format=DataFormat.JSON,
    tags=["intent", "classification", "production"]
)
```

### 2. Data Upload and Validation

```python
# Upload training examples
version_id = manager.upload_dataset(
    dataset_id=dataset_id,
    data=training_examples,
    format=DataFormat.JSON,
    version_description="Initial training data",
    created_by="trainer_user_id"
)

# Validate dataset quality
examples = manager.get_dataset(dataset_id)
validation_report = manager.validate_dataset(examples)

print(f"Quality Score: {validation_report.quality_score}")
print(f"Issues Found: {len(validation_report.issues)}")
```

### 3. Format Conversion

```python
# Convert to different formats
examples = manager.get_dataset(dataset_id)

# Convert to spaCy format for training
spacy_data = manager.convert_format(examples, DataFormat.SPACY)

# Convert to HuggingFace format
hf_data = manager.convert_format(examples, DataFormat.HUGGINGFACE)

# Convert to CSV for analysis
csv_data = manager.convert_format(examples, DataFormat.CSV)
```

### 4. Quality Assessment and Enhancement

```python
# Assess data quality
quality_metrics = manager.assess_quality(examples)
print(f"Overall Quality: {quality_metrics.overall_score:.2f}")
print(f"Completeness: {quality_metrics.completeness:.2f}")
print(f"Balance: {quality_metrics.balance:.2f}")

# Enhance dataset automatically
enhanced_examples = manager.enhance_dataset(examples)
print(f"Enhanced from {len(examples)} to {len(enhanced_examples)} examples")
```

### 5. Version Control

```python
# List all versions
versions = manager.list_versions(dataset_id)
for version in versions:
    print(f"Version {version.version_number}: {version.description}")

# Create new version with modifications
new_version_id = manager.create_version_from_existing(
    dataset_id=dataset_id,
    source_version=latest_version_id,
    description="Confidence score adjustments",
    modifications={'confidence_adjustment': 0.1},
    created_by="trainer_user_id"
)
```

### 6. Export and Import

```python
# Export dataset
exported_data = manager.export_dataset(
    dataset_id=dataset_id,
    format=DataFormat.JSON,
    include_metadata=True
)

# Import dataset
new_dataset_id = manager.import_dataset(
    data=exported_data,
    format=DataFormat.JSON,
    dataset_name="Imported Dataset",
    created_by="importer"
)
```

## Data Models

### TrainingExample

The core data structure representing a single training example:

```python
@dataclass
class TrainingExample:
    text: str                                    # Input text
    expected_intent: str                         # Expected intent classification
    expected_sentiment: str                      # Expected sentiment classification
    expected_entities: List[Tuple[str, str, int, int]]  # Entity annotations
    expected_persona: Optional[str] = None       # Expected persona selection
    confidence: float = 1.0                      # Confidence score (0-1)
    source: LearningDataType = LearningDataType.CONVERSATION
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### ValidationReport

Comprehensive validation results:

```python
@dataclass
class ValidationReport:
    dataset_id: str
    validation_id: str
    timestamp: datetime
    total_examples: int
    valid_examples: int
    invalid_examples: int
    quality_score: float
    issues: List[ValidationIssue]
    statistics: Dict[str, Any]
    recommendations: List[str]
```

### QualityMetrics

Quality assessment metrics:

```python
@dataclass
class QualityMetrics:
    completeness: float    # Percentage of complete examples
    consistency: float     # Consistency of labels/annotations
    accuracy: float        # Estimated accuracy of labels
    diversity: float       # Diversity of examples
    balance: float         # Class balance
    complexity: float      # Linguistic complexity
    overall_score: float   # Overall quality score
```

## Validation System

The validation system performs comprehensive checks on training data:

### Validation Levels

1. **ERROR**: Critical issues that prevent training
   - Empty or missing text
   - Missing required labels
   - Invalid entity spans
   - Malformed data structures

2. **WARNING**: Issues that may affect quality
   - Very short or long text
   - Confidence scores out of range
   - Potential duplicates
   - Class imbalances

3. **INFO**: Informational notices
   - Data statistics
   - Recommendations for improvement

### Validation Checks

- **Required Fields**: Ensures all mandatory fields are present
- **Data Types**: Validates correct data types for all fields
- **Value Ranges**: Checks confidence scores, entity spans, etc.
- **Content Quality**: Analyzes text length, complexity, clarity
- **Consistency**: Checks for consistent labeling of similar examples
- **Balance**: Assesses class distribution and balance

## Quality Assessment

The quality assessment system evaluates datasets across multiple dimensions:

### Quality Dimensions

1. **Completeness**: Percentage of examples with all required fields
2. **Consistency**: Consistency of labels for similar texts
3. **Accuracy**: Estimated accuracy based on confidence scores
4. **Diversity**: Lexical and semantic diversity of examples
5. **Balance**: Distribution balance across classes
6. **Complexity**: Linguistic complexity and sophistication

### Quality Scoring

- Each dimension is scored from 0.0 to 1.0
- Overall score is a weighted combination of all dimensions
- Scores above 0.8 are considered excellent
- Scores below 0.4 indicate significant quality issues

## Data Enhancement

The enhancement system automatically improves data quality:

### Enhancement Operations

1. **Text Cleaning**: Remove excessive whitespace, normalize formatting
2. **Duplicate Removal**: Identify and remove duplicate examples
3. **Confidence Correction**: Fix invalid confidence scores
4. **Class Balancing**: Balance class distributions through sampling
5. **Metadata Enrichment**: Add enhancement metadata and timestamps

### Enhancement Pipeline

```python
def enhance_dataset(examples: List[TrainingExample]) -> List[TrainingExample]:
    # 1. Clean individual examples
    enhanced = [self._enhance_example(ex) for ex in examples]
    
    # 2. Remove duplicates
    enhanced = self._remove_duplicates(enhanced)
    
    # 3. Balance classes
    enhanced = self._balance_classes(enhanced)
    
    return enhanced
```

## Format Support

### Supported Formats

1. **JSON**: Standard JSON format with full metadata
2. **JSONL**: JSON Lines format for streaming processing
3. **CSV**: Comma-separated values for spreadsheet compatibility
4. **spaCy**: Native spaCy training format
5. **HuggingFace**: HuggingFace datasets format
6. **Pickle**: Python pickle format for object serialization

### Format Conversion

The system provides seamless conversion between formats:

```python
# Convert examples to any supported format
converted_data = manager.convert_format(examples, target_format)

# Format-specific optimizations
if target_format == DataFormat.SPACY:
    # Optimized for spaCy training pipeline
    return [(text, annotations) for text, annotations in spacy_data]
elif target_format == DataFormat.HUGGINGFACE:
    # Optimized for HuggingFace datasets
    return {
        'text': [ex.text for ex in examples],
        'labels': [ex.expected_intent for ex in examples]
    }
```

## Version Control

### Versioning Strategy

- **Semantic Versioning**: Major.Minor format (e.g., 1.0, 1.1, 2.0)
- **Immutable Versions**: Once created, versions cannot be modified
- **Provenance Tracking**: Full history of changes and modifications
- **Checksum Verification**: Data integrity verification

### Version Operations

```python
# Create version from existing
new_version = manager.create_version_from_existing(
    dataset_id=dataset_id,
    source_version="1.0",
    description="Applied confidence adjustments",
    modifications={
        'confidence_adjustment': 0.1,
        'intent_mapping': {'old_intent': 'new_intent'}
    },
    created_by="trainer_user_id"
)

# List all versions with metadata
versions = manager.list_versions(dataset_id)
for version in versions:
    print(f"{version.version_number}: {version.size} examples, "
          f"quality {version.quality_score:.2f}")
```

## API Integration

The Training Data Manager is exposed through REST API endpoints:

### Key Endpoints

- `POST /api/training-data/datasets` - Create dataset
- `GET /api/training-data/datasets` - List datasets
- `POST /api/training-data/datasets/{id}/upload` - Upload data
- `GET /api/training-data/datasets/{id}/data` - Get dataset data
- `POST /api/training-data/datasets/{id}/validate` - Validate dataset
- `POST /api/training-data/datasets/{id}/enhance` - Enhance dataset
- `GET /api/training-data/datasets/{id}/export` - Export dataset
- `POST /api/training-data/datasets/import` - Import dataset

### Authentication and Authorization

All API endpoints require appropriate permissions:

- `training_data:read` - Read access to datasets
- `training_data:write` - Create and modify datasets
- `training_data:delete` - Delete datasets

## Performance Considerations

### Scalability

- **Streaming Processing**: Large datasets processed in chunks
- **Lazy Loading**: Data loaded on-demand to minimize memory usage
- **Caching**: Frequently accessed data cached for performance
- **Parallel Processing**: CPU-intensive operations parallelized

### Storage Optimization

- **Compression**: Large datasets compressed for storage efficiency
- **Deduplication**: Duplicate data identified and stored once
- **Incremental Updates**: Only changes stored for new versions
- **Cleanup**: Automatic cleanup of temporary files and old versions

## Error Handling

### Error Categories

1. **Validation Errors**: Data quality and format issues
2. **Storage Errors**: File system and database issues
3. **Format Errors**: Conversion and parsing issues
4. **Version Errors**: Version control and consistency issues

### Error Recovery

- **Graceful Degradation**: System continues operating with reduced functionality
- **Automatic Retry**: Transient errors automatically retried
- **Rollback Support**: Failed operations can be rolled back
- **Detailed Logging**: Comprehensive error logging for debugging

## Best Practices

### Data Quality

1. **Validate Early**: Validate data as soon as it's uploaded
2. **Monitor Quality**: Continuously monitor quality metrics
3. **Regular Enhancement**: Periodically enhance datasets
4. **Version Control**: Use versions for all significant changes

### Performance

1. **Batch Operations**: Process data in batches for efficiency
2. **Index Frequently**: Index commonly queried fields
3. **Cache Results**: Cache validation and quality assessment results
4. **Monitor Resources**: Monitor memory and disk usage

### Security

1. **Access Control**: Implement proper access controls
2. **Data Privacy**: Ensure sensitive data is properly protected
3. **Audit Logging**: Log all data access and modifications
4. **Backup Strategy**: Implement comprehensive backup strategy

## Integration with Response Core

The Training Data Manager integrates seamlessly with the Response Core orchestrator:

### Autonomous Learning Integration

```python
# Collect training data from conversations
conversation_data = autonomous_learner.collect_interaction_data(conversation)

# Upload to training dataset
manager.upload_dataset(
    dataset_id=learning_dataset_id,
    data=[conversation_data],
    format=DataFormat.JSON,
    version_description="Autonomous learning data",
    created_by=conversation_data.get("user_id", "autonomous_agent")
)

# Enhance and validate
enhanced_data = manager.enhance_dataset(examples)
validation_report = manager.validate_dataset(enhanced_data)

# Use for model training if quality is sufficient
if validation_report.quality_score > 0.8:
    spacy_data = manager.convert_format(enhanced_data, DataFormat.SPACY)
    # Train model with spacy_data
```

### Model Training Pipeline

```python
# Get training data in appropriate format
training_data = manager.get_dataset(dataset_id, version="latest")
spacy_format = manager.convert_format(training_data, DataFormat.SPACY)

# Train spaCy model
nlp = spacy.blank("en")
nlp.add_pipe("textcat")
nlp.update(spacy_format)

# Validate trained model
validation_data = manager.get_dataset(validation_dataset_id)
accuracy = evaluate_model(nlp, validation_data)

# Store model version if performance is good
if accuracy > threshold:
    save_model_version(nlp, dataset_version=version_id)
```

## Monitoring and Observability

### Metrics

The system exposes comprehensive metrics for monitoring:

```python
# Dataset metrics
dataset_count = Counter("training_datasets_total")
dataset_size = Histogram("training_dataset_size", ["dataset_id"])
quality_score = Histogram("training_dataset_quality", ["dataset_id"])

# Operation metrics
validation_time = Histogram("validation_duration_seconds")
enhancement_time = Histogram("enhancement_duration_seconds")
conversion_time = Histogram("format_conversion_duration_seconds")

# Error metrics
validation_errors = Counter("validation_errors_total", ["error_type"])
enhancement_failures = Counter("enhancement_failures_total")
```

### Health Checks

```python
@router.get("/health")
async def health_check():
    manager = get_training_manager()
    
    # Check directory accessibility
    directories_ok = all([
        manager.data_dir.exists(),
        manager.datasets_dir.exists(),
        manager.versions_dir.exists(),
        manager.metadata_dir.exists()
    ])
    
    return {
        "status": "healthy" if directories_ok else "degraded",
        "directories_ok": directories_ok,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Future Enhancements

### Planned Features

1. **Advanced Analytics**: Statistical analysis and visualization
2. **Data Lineage**: Complete data lineage tracking
3. **Automated Labeling**: AI-assisted data labeling
4. **Collaborative Editing**: Multi-user collaborative dataset editing
5. **Integration APIs**: Enhanced integration with external tools
6. **Performance Optimization**: Advanced caching and indexing
7. **Data Governance**: Comprehensive data governance features

### Extensibility

The system is designed for extensibility:

- **Plugin Architecture**: Support for custom validation rules
- **Custom Formats**: Easy addition of new data formats
- **Enhancement Plugins**: Custom data enhancement algorithms
- **Quality Metrics**: Custom quality assessment metrics

## Conclusion

The Training Data Manager provides a comprehensive solution for managing training data in machine learning systems. It combines robust data management capabilities with advanced quality assessment and enhancement features, making it an essential component of the Response Core orchestrator's autonomous learning system.

The system's focus on data quality, version control, and automated enhancement ensures that training data remains high-quality and well-managed throughout the machine learning lifecycle, supporting the development of more accurate and reliable AI models.