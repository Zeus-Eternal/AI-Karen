"""
Training Data Management System for the Response Core orchestrator.

This module implements comprehensive training data management capabilities including
dataset curation, editing, upload, validation, format conversion, version control,
and automated quality assessment and enhancement.
"""

import asyncio
import hashlib
import json
import logging
import shutil
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Iterator
import csv
import pickle
import tempfile
import zipfile
from collections import defaultdict

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from ai_karen_engine.core.response.autonomous_learner import (
    TrainingExample, LearningDataType, ConversationMetadata
)

logger = logging.getLogger(__name__)


class DataFormat(str, Enum):
    """Supported data formats for training data."""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"
    PICKLE = "pickle"
    HUGGINGFACE = "huggingface"
    SPACY = "spacy"
    CUSTOM = "custom"


class DataQuality(str, Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DatasetVersion:
    """Version information for training datasets."""
    version_id: str
    dataset_id: str
    version_number: str
    created_at: datetime
    created_by: str
    description: str
    parent_version: Optional[str] = None
    size: int = 0
    quality_score: float = 0.0
    validation_passed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class ValidationIssue:
    """Represents a validation issue found in training data."""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    example_id: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)


@dataclass
class ValidationReport:
    """Comprehensive validation report for training data."""
    dataset_id: str
    validation_id: str
    timestamp: datetime
    total_examples: int
    valid_examples: int
    invalid_examples: int
    quality_score: float
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['issues'] = [issue.to_dict() for issue in self.issues]
        return data


@dataclass
class DatasetMetadata:
    """Metadata for training datasets."""
    dataset_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    format: DataFormat
    size: int
    quality_score: float
    tags: List[str] = field(default_factory=list)
    source: str = "manual"
    provenance: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class QualityMetrics:
    """Quality assessment metrics for training data."""
    completeness: float  # Percentage of complete examples
    consistency: float   # Consistency of labels/annotations
    accuracy: float      # Estimated accuracy of labels
    diversity: float     # Diversity of examples
    balance: float       # Class balance
    complexity: float    # Linguistic complexity
    overall_score: float # Overall quality score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)


class TrainingDataManager:
    """
    Comprehensive training data management system.
    
    Provides capabilities for dataset curation, editing, upload, validation,
    format conversion, version control, and automated quality assessment.
    """
    
    def __init__(self, data_dir: str = "data/training"):
        """Initialize the training data manager.
        
        Args:
            data_dir: Directory to store training data and metadata
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.datasets_dir = self.data_dir / "datasets"
        self.versions_dir = self.data_dir / "versions"
        self.metadata_dir = self.data_dir / "metadata"
        self.temp_dir = self.data_dir / "temp"
        
        for dir_path in [self.datasets_dir, self.versions_dir, self.metadata_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    # Dataset Management Methods
    
    def create_dataset(
        self, 
        name: str, 
        description: str, 
        created_by: str,
        format: DataFormat = DataFormat.JSON,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a new training dataset.
        
        Args:
            name: Dataset name
            description: Dataset description
            created_by: Creator identifier
            format: Data format
            tags: Optional tags for categorization
            
        Returns:
            Dataset ID
        """
        dataset_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            format=format,
            size=0,
            quality_score=0.0,
            tags=tags or [],
            provenance={"created_via": "api", "timestamp": now.isoformat()}
        )
        
        # Save metadata
        metadata_path = self.metadata_dir / f"{dataset_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Create dataset directory
        dataset_dir = self.datasets_dir / dataset_id
        dataset_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Created dataset {dataset_id}: {name}")
        return dataset_id
    
    def upload_dataset(
        self,
        dataset_id: str,
        data: Union[List[Dict[str, Any]], str, bytes],
        format: DataFormat,
        version_description: str = "Initial upload",
        created_by: Optional[str] = None
    ) -> str:
        """Upload training data to a dataset.
        
        Args:
            dataset_id: Target dataset ID
            data: Training data (list of examples, file path, or raw bytes)
            format: Data format
            version_description: Description of this version
            created_by: Identifier for the actor creating this version
            
        Returns:
            Version ID
        """
        # Load dataset metadata
        metadata = self._load_dataset_metadata(dataset_id)
        if not metadata:
            raise ValueError(f"Dataset {dataset_id} not found")

        # Resolve creator for the new version
        creator_id = created_by or metadata.created_by or "system"

        # Process and validate data
        examples = self._process_upload_data(data, format)
        validation_report = self.validate_dataset(examples)

        # Create new version
        version_id = self._create_version(
            dataset_id,
            examples,
            version_description,
            validation_report,
            created_by=creator_id
        )
        
        # Update dataset metadata
        metadata.size = len(examples)
        metadata.quality_score = validation_report.quality_score
        metadata.updated_at = datetime.utcnow()
        
        self._save_dataset_metadata(metadata)
        
        self.logger.info(f"Uploaded {len(examples)} examples to dataset {dataset_id}, version {version_id}")
        return version_id
    
    def get_dataset(self, dataset_id: str, version: Optional[str] = None) -> List[TrainingExample]:
        """Retrieve training data from a dataset.
        
        Args:
            dataset_id: Dataset ID
            version: Specific version (latest if None)
            
        Returns:
            List of training examples
        """
        if version is None:
            version = self._get_latest_version(dataset_id)
        
        version_path = self.versions_dir / dataset_id / f"{version}.json"
        if not version_path.exists():
            raise ValueError(f"Version {version} not found for dataset {dataset_id}")
        
        with open(version_path, 'r') as f:
            data = json.load(f)
        
        examples = []
        for item in data['examples']:
            example = TrainingExample(
                text=item['text'],
                expected_intent=item['expected_intent'],
                expected_sentiment=item['expected_sentiment'],
                expected_entities=item.get('expected_entities', []),
                expected_persona=item.get('expected_persona'),
                confidence=item.get('confidence', 1.0),
                source=LearningDataType(item.get('source', 'manual')),
                metadata=item.get('metadata', {}),
                created_at=datetime.fromisoformat(item['created_at'])
            )
            examples.append(example)
        
        return examples
    
    # Data Validation Methods
    
    def validate_dataset(self, examples: List[TrainingExample]) -> ValidationReport:
        """Perform comprehensive validation of training data.
        
        Args:
            examples: List of training examples to validate
            
        Returns:
            Validation report with issues and recommendations
        """
        validation_id = str(uuid.uuid4())
        issues = []
        statistics = {}
        
        # Basic validation
        valid_count = 0
        for i, example in enumerate(examples):
            example_issues = self._validate_example(example, i)
            issues.extend(example_issues)
            if not any(issue.severity == ValidationSeverity.ERROR for issue in example_issues):
                valid_count += 1
        
        # Statistical analysis
        statistics = self._compute_dataset_statistics(examples)
        
        # Quality assessment
        quality_score = self._assess_quality(examples, issues, statistics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, statistics)
        
        report = ValidationReport(
            dataset_id="temp",
            validation_id=validation_id,
            timestamp=datetime.utcnow(),
            total_examples=len(examples),
            valid_examples=valid_count,
            invalid_examples=len(examples) - valid_count,
            quality_score=quality_score,
            issues=issues,
            statistics=statistics,
            recommendations=recommendations
        )
        
        return report
    
    def _validate_example(self, example: TrainingExample, index: int) -> List[ValidationIssue]:
        """Validate a single training example.
        
        Args:
            example: Training example to validate
            index: Example index for error reporting
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Required field validation
        if not example.text or not example.text.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Empty or missing text",
                field="text",
                example_id=str(index),
                suggestion="Provide non-empty text content"
            ))
        
        if not example.expected_intent:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Missing expected intent",
                field="expected_intent",
                example_id=str(index),
                suggestion="Specify the expected intent classification"
            ))
        
        if not example.expected_sentiment:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Missing expected sentiment",
                field="expected_sentiment",
                example_id=str(index),
                suggestion="Specify the expected sentiment classification"
            ))
        
        # Content quality validation
        if example.text and len(example.text.strip()) < 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Text is very short",
                field="text",
                example_id=str(index),
                suggestion="Consider providing more context in the text"
            ))
        
        if example.text and len(example.text) > 10000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Text is very long",
                field="text",
                example_id=str(index),
                suggestion="Consider splitting long text into smaller examples"
            ))
        
        # Entity validation
        if example.expected_entities:
            text_len = len(example.text) if example.text else 0
            for entity in example.expected_entities:
                if len(entity) >= 4:  # (text, label, start, end)
                    start, end = entity[2], entity[3]
                    if start < 0 or end > text_len or start >= end:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Invalid entity span: {start}-{end}",
                            field="expected_entities",
                            example_id=str(index),
                            suggestion="Ensure entity spans are within text bounds"
                        ))
        
        # Confidence validation
        if example.confidence < 0 or example.confidence > 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Confidence out of range: {example.confidence}",
                field="confidence",
                example_id=str(index),
                suggestion="Confidence should be between 0 and 1",
                auto_fixable=True
            ))
        
        return issues
    
    # Format Conversion Methods
    
    def convert_format(
        self, 
        examples: List[TrainingExample], 
        target_format: DataFormat
    ) -> Union[str, bytes, List[Dict[str, Any]]]:
        """Convert training data to different formats.
        
        Args:
            examples: Training examples to convert
            target_format: Target format
            
        Returns:
            Converted data in the specified format
        """
        if target_format == DataFormat.JSON:
            return [self._example_to_dict(ex) for ex in examples]
        
        elif target_format == DataFormat.JSONL:
            lines = []
            for example in examples:
                lines.append(json.dumps(self._example_to_dict(example)))
            return '\n'.join(lines)
        
        elif target_format == DataFormat.CSV:
            data = []
            for example in examples:
                row = {
                    'text': example.text,
                    'expected_intent': example.expected_intent,
                    'expected_sentiment': example.expected_sentiment,
                    'expected_persona': example.expected_persona or '',
                    'confidence': example.confidence,
                    'source': example.source.value,
                    'created_at': example.created_at.isoformat()
                }
                # Flatten entities
                if example.expected_entities:
                    entities_str = json.dumps(example.expected_entities)
                    row['expected_entities'] = entities_str
                else:
                    row['expected_entities'] = ''
                
                data.append(row)
            
            # Convert to CSV string
            import io
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            return output.getvalue()
        
        elif target_format == DataFormat.SPACY:
            spacy_data = []
            for example in examples:
                spacy_example = example.to_spacy_format()
                spacy_data.append(spacy_example)
            return spacy_data
        
        elif target_format == DataFormat.HUGGINGFACE:
            hf_data = {
                'text': [ex.text for ex in examples],
                'intent': [ex.expected_intent for ex in examples],
                'sentiment': [ex.expected_sentiment for ex in examples]
            }
            return hf_data
        
        elif target_format == DataFormat.PICKLE:
            return pickle.dumps(examples)
        
        else:
            raise ValueError(f"Unsupported format: {target_format}")
    
    # Quality Assessment Methods
    
    def assess_quality(self, examples: List[TrainingExample]) -> QualityMetrics:
        """Assess the quality of training data.
        
        Args:
            examples: Training examples to assess
            
        Returns:
            Quality metrics
        """
        if not examples:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0)
        
        # Completeness: percentage of examples with all required fields
        complete_count = 0
        for example in examples:
            if (example.text and example.text.strip() and 
                example.expected_intent and example.expected_sentiment):
                complete_count += 1
        completeness = complete_count / len(examples)
        
        # Consistency: consistency of labels for similar texts
        consistency = self._assess_consistency(examples)
        
        # Accuracy: estimated accuracy based on confidence scores
        confidences = [ex.confidence for ex in examples if ex.confidence is not None]
        accuracy = np.mean(confidences) if confidences else 0.0
        
        # Diversity: lexical diversity of the dataset
        diversity = self._assess_diversity(examples)
        
        # Balance: class balance across intents and sentiments
        balance = self._assess_balance(examples)
        
        # Complexity: linguistic complexity
        complexity = self._assess_complexity(examples)
        
        # Overall score: weighted combination
        overall_score = (
            completeness * 0.25 +
            consistency * 0.20 +
            accuracy * 0.20 +
            diversity * 0.15 +
            balance * 0.10 +
            complexity * 0.10
        )
        
        return QualityMetrics(
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            diversity=diversity,
            balance=balance,
            complexity=complexity,
            overall_score=overall_score
        )
    
    # Data Enhancement Methods
    
    def enhance_dataset(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Automatically enhance training data quality.
        
        Args:
            examples: Training examples to enhance
            
        Returns:
            Enhanced training examples
        """
        enhanced = []
        
        for example in examples:
            enhanced_example = self._enhance_example(example)
            enhanced.append(enhanced_example)
        
        # Remove duplicates
        enhanced = self._remove_duplicates(enhanced)
        
        # Balance classes if needed
        enhanced = self._balance_classes(enhanced)
        
        return enhanced
    
    def _enhance_example(self, example: TrainingExample) -> TrainingExample:
        """Enhance a single training example.
        
        Args:
            example: Training example to enhance
            
        Returns:
            Enhanced training example
        """
        # Create a copy to avoid modifying the original
        enhanced = TrainingExample(
            text=example.text,
            expected_intent=example.expected_intent,
            expected_sentiment=example.expected_sentiment,
            expected_entities=example.expected_entities.copy(),
            expected_persona=example.expected_persona,
            confidence=example.confidence,
            source=example.source,
            metadata=example.metadata.copy(),
            created_at=example.created_at
        )
        
        # Clean and normalize text
        if enhanced.text:
            enhanced.text = self._clean_text(enhanced.text)
        
        # Fix confidence values
        if enhanced.confidence < 0:
            enhanced.confidence = 0.0
        elif enhanced.confidence > 1:
            enhanced.confidence = 1.0
        
        # Add metadata if missing
        if 'enhanced' not in enhanced.metadata:
            enhanced.metadata['enhanced'] = True
            enhanced.metadata['enhancement_timestamp'] = datetime.utcnow().isoformat()
        
        return enhanced
    
    # Version Control Methods
    
    def list_versions(self, dataset_id: str) -> List[DatasetVersion]:
        """List all versions of a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            List of dataset versions
        """
        versions_path = self.versions_dir / dataset_id
        if not versions_path.exists():
            return []
        
        versions = []
        for version_file in versions_path.glob("*.json"):
            if version_file.name.startswith("version_"):
                continue  # Skip version metadata files
            
            version_id = version_file.stem
            version_metadata_path = versions_path / f"version_{version_id}.json"
            
            if version_metadata_path.exists():
                with open(version_metadata_path, 'r') as f:
                    version_data = json.load(f)
                
                version = DatasetVersion(
                    version_id=version_data['version_id'],
                    dataset_id=version_data['dataset_id'],
                    version_number=version_data['version_number'],
                    created_at=datetime.fromisoformat(version_data['created_at']),
                    created_by=version_data['created_by'],
                    description=version_data['description'],
                    parent_version=version_data.get('parent_version'),
                    size=version_data.get('size', 0),
                    quality_score=version_data.get('quality_score', 0.0),
                    validation_passed=version_data.get('validation_passed', False),
                    metadata=version_data.get('metadata', {}),
                    file_path=str(version_file),
                    checksum=version_data.get('checksum')
                )
                versions.append(version)
        
        # Sort by creation time
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions
    
    def create_version_from_existing(
        self,
        dataset_id: str,
        source_version: str,
        description: str,
        modifications: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Create a new version based on an existing version.
        
        Args:
            dataset_id: Dataset ID
            source_version: Source version ID
            description: Description of the new version
            modifications: Optional modifications to apply
            created_by: Identifier for the actor creating this version
            
        Returns:
            New version ID
        """
        # Load source data
        examples = self.get_dataset(dataset_id, source_version)
        
        # Apply modifications if provided
        if modifications:
            examples = self._apply_modifications(examples, modifications)
        
        # Validate modified data
        validation_report = self.validate_dataset(examples)
        
        # Create new version
        # Determine creator
        if created_by is None:
            metadata = self._load_dataset_metadata(dataset_id)
            created_by = metadata.created_by if metadata else "system"

        version_id = self._create_version(
            dataset_id,
            examples,
            description,
            validation_report,
            parent_version=source_version,
            created_by=created_by
        )
        
        return version_id
    
    # Export/Import Methods
    
    def export_dataset(
        self, 
        dataset_id: str, 
        format: DataFormat,
        version: Optional[str] = None,
        include_metadata: bool = True
    ) -> bytes:
        """Export dataset in specified format.
        
        Args:
            dataset_id: Dataset ID
            format: Export format
            version: Specific version (latest if None)
            include_metadata: Whether to include metadata
            
        Returns:
            Exported data as bytes
        """
        examples = self.get_dataset(dataset_id, version)
        converted_data = self.convert_format(examples, format)
        
        if format == DataFormat.JSON:
            export_data = {
                'examples': converted_data,
                'metadata': self._load_dataset_metadata(dataset_id).to_dict() if include_metadata else {}
            }
            return json.dumps(export_data, indent=2).encode('utf-8')
        
        elif isinstance(converted_data, str):
            return converted_data.encode('utf-8')
        
        elif isinstance(converted_data, bytes):
            return converted_data
        
        else:
            return json.dumps(converted_data).encode('utf-8')
    
    def import_dataset(
        self, 
        data: bytes, 
        format: DataFormat,
        dataset_name: str,
        created_by: str,
        description: str = "Imported dataset"
    ) -> str:
        """Import dataset from external data.
        
        Args:
            data: Raw data bytes
            format: Data format
            dataset_name: Name for the new dataset
            created_by: Creator identifier
            description: Dataset description
            
        Returns:
            New dataset ID
        """
        # Parse data based on format
        examples = self._parse_import_data(data, format)
        
        # Create new dataset
        dataset_id = self.create_dataset(
            name=dataset_name,
            description=description,
            created_by=created_by,
            format=format
        )
        
        # Upload data
        self.upload_dataset(
            dataset_id=dataset_id,
            data=examples,
            format=DataFormat.JSON,  # Internal format
            version_description="Initial import",
            created_by=created_by
        )
        
        return dataset_id
    
    # Helper Methods
    
    def _load_dataset_metadata(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Load dataset metadata from file."""
        metadata_path = self.metadata_dir / f"{dataset_id}.json"
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        return DatasetMetadata(
            dataset_id=data['dataset_id'],
            name=data['name'],
            description=data['description'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            created_by=data['created_by'],
            format=DataFormat(data['format']),
            size=data['size'],
            quality_score=data['quality_score'],
            tags=data.get('tags', []),
            source=data.get('source', 'manual'),
            provenance=data.get('provenance', {}),
            schema_version=data.get('schema_version', '1.0')
        )
    
    def _save_dataset_metadata(self, metadata: DatasetMetadata) -> None:
        """Save dataset metadata to file."""
        metadata_path = self.metadata_dir / f"{metadata.dataset_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _process_upload_data(
        self, 
        data: Union[List[Dict[str, Any]], str, bytes],
        format: DataFormat
    ) -> List[TrainingExample]:
        """Process uploaded data into TrainingExample objects."""
        if isinstance(data, list):
            # Check if it's already TrainingExample objects or dictionaries
            if data and isinstance(data[0], TrainingExample):
                return data
            else:
                # Convert dictionaries to TrainingExample objects
                return [self._dict_to_example(item) for item in data]
        
        elif isinstance(data, (str, bytes)):
            # Parse based on format
            return self._parse_import_data(data, format)
        
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    def _parse_import_data(self, data: Union[str, bytes], format: DataFormat) -> List[TrainingExample]:
        """Parse imported data based on format."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        examples = []
        
        if format == DataFormat.JSON:
            parsed = json.loads(data)
            if isinstance(parsed, dict) and 'examples' in parsed:
                parsed = parsed['examples']
            
            for item in parsed:
                examples.append(self._dict_to_example(item))
        
        elif format == DataFormat.JSONL:
            for line in data.strip().split('\n'):
                if line.strip():
                    item = json.loads(line)
                    examples.append(self._dict_to_example(item))
        
        elif format == DataFormat.CSV:
            import io
            reader = csv.DictReader(io.StringIO(data))
            for row in reader:
                examples.append(self._dict_to_example(row))
        
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        return examples
    
    def _dict_to_example(self, data: Union[Dict[str, Any], TrainingExample]) -> TrainingExample:
        """Convert dictionary to TrainingExample."""
        # If it's already a TrainingExample, return as-is
        if isinstance(data, TrainingExample):
            return data
        
        entities = data.get('expected_entities', [])
        if isinstance(entities, str):
            try:
                entities = json.loads(entities)
            except:
                entities = []
        
        return TrainingExample(
            text=data.get('text', ''),
            expected_intent=data.get('expected_intent', ''),
            expected_sentiment=data.get('expected_sentiment', ''),
            expected_entities=entities,
            expected_persona=data.get('expected_persona'),
            confidence=float(data.get('confidence', 1.0)),
            source=LearningDataType(data.get('source', 'manual')),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.utcnow()
        )
    
    def _example_to_dict(self, example: TrainingExample) -> Dict[str, Any]:
        """Convert TrainingExample to dictionary."""
        return {
            'text': example.text,
            'expected_intent': example.expected_intent,
            'expected_sentiment': example.expected_sentiment,
            'expected_entities': example.expected_entities,
            'expected_persona': example.expected_persona,
            'confidence': example.confidence,
            'source': example.source.value,
            'metadata': example.metadata,
            'created_at': example.created_at.isoformat()
        }
    
    def _create_version(
        self,
        dataset_id: str,
        examples: List[TrainingExample],
        description: str,
        validation_report: ValidationReport,
        parent_version: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Create a new dataset version."""
        version_id = str(uuid.uuid4())
        version_number = self._get_next_version_number(dataset_id)
        
        # Create version directory
        version_dir = self.versions_dir / dataset_id
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Save examples data
        examples_data = {
            'examples': [self._example_to_dict(ex) for ex in examples],
            'validation_report': validation_report.to_dict()
        }
        
        examples_path = version_dir / f"{version_id}.json"
        with open(examples_path, 'w') as f:
            json.dump(examples_data, f, indent=2)
        
        # Calculate checksum
        checksum = self._calculate_checksum(examples_path)
        
        # Create version metadata
        if created_by is None:
            metadata = self._load_dataset_metadata(dataset_id)
            created_by = metadata.created_by if metadata else "system"

        version_metadata = DatasetVersion(
            version_id=version_id,
            dataset_id=dataset_id,
            version_number=version_number,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=description,
            parent_version=parent_version,
            size=len(examples),
            quality_score=validation_report.quality_score,
            validation_passed=validation_report.invalid_examples == 0,
            file_path=str(examples_path),
            checksum=checksum
        )
        
        # Save version metadata
        version_metadata_path = version_dir / f"version_{version_id}.json"
        with open(version_metadata_path, 'w') as f:
            json.dump(version_metadata.to_dict(), f, indent=2)
        
        return version_id
    
    def _get_latest_version(self, dataset_id: str) -> Optional[str]:
        """Get the latest version ID for a dataset."""
        versions = self.list_versions(dataset_id)
        return versions[0].version_id if versions else None
    
    def _get_next_version_number(self, dataset_id: str) -> str:
        """Get the next version number for a dataset."""
        versions = self.list_versions(dataset_id)
        if not versions:
            return "1.0"
        
        # Parse version numbers and increment
        version_numbers = []
        for version in versions:
            try:
                parts = version.version_number.split('.')
                major, minor = int(parts[0]), int(parts[1])
                version_numbers.append((major, minor))
            except:
                continue
        
        if version_numbers:
            max_major, max_minor = max(version_numbers)
            return f"{max_major}.{max_minor + 1}"
        else:
            return "1.0"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _compute_dataset_statistics(self, examples: List[TrainingExample]) -> Dict[str, Any]:
        """Compute statistical information about the dataset."""
        if not examples:
            return {}
        
        # Intent distribution
        intent_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        text_lengths = []
        confidence_scores = []
        
        for example in examples:
            if example.expected_intent:
                intent_counts[example.expected_intent] += 1
            if example.expected_sentiment:
                sentiment_counts[example.expected_sentiment] += 1
            if example.source:
                source_counts[example.source.value] += 1
            if example.text:
                text_lengths.append(len(example.text))
            if example.confidence is not None:
                confidence_scores.append(example.confidence)
        
        statistics = {
            'total_examples': len(examples),
            'intent_distribution': dict(intent_counts),
            'sentiment_distribution': dict(sentiment_counts),
            'source_distribution': dict(source_counts),
            'text_length_stats': {
                'mean': np.mean(text_lengths) if text_lengths else 0,
                'median': np.median(text_lengths) if text_lengths else 0,
                'min': min(text_lengths) if text_lengths else 0,
                'max': max(text_lengths) if text_lengths else 0,
                'std': np.std(text_lengths) if text_lengths else 0
            },
            'confidence_stats': {
                'mean': np.mean(confidence_scores) if confidence_scores else 0,
                'median': np.median(confidence_scores) if confidence_scores else 0,
                'min': min(confidence_scores) if confidence_scores else 0,
                'max': max(confidence_scores) if confidence_scores else 0,
                'std': np.std(confidence_scores) if confidence_scores else 0
            }
        }
        
        return statistics
    
    def _assess_quality(
        self, 
        examples: List[TrainingExample], 
        issues: List[ValidationIssue],
        statistics: Dict[str, Any]
    ) -> float:
        """Assess overall quality score for the dataset."""
        if not examples:
            return 0.0
        
        # Base score from validation issues
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        
        # Penalty for errors and warnings
        error_penalty = (error_count / len(examples)) * 0.5
        warning_penalty = (warning_count / len(examples)) * 0.2
        
        base_score = max(0, 1.0 - error_penalty - warning_penalty)
        
        # Bonus for good statistics
        intent_diversity = len(statistics.get('intent_distribution', {}))
        sentiment_diversity = len(statistics.get('sentiment_distribution', {}))
        
        diversity_bonus = min(0.1, (intent_diversity + sentiment_diversity) / 20)
        
        # Confidence bonus
        confidence_stats = statistics.get('confidence_stats', {})
        avg_confidence = confidence_stats.get('mean', 0)
        confidence_bonus = avg_confidence * 0.1
        
        final_score = min(1.0, base_score + diversity_bonus + confidence_bonus)
        return final_score
    
    def _generate_recommendations(
        self, 
        issues: List[ValidationIssue],
        statistics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        # Error-based recommendations
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        if error_count > 0:
            recommendations.append(f"Fix {error_count} validation errors before training")
        
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        if warning_count > 0:
            recommendations.append(f"Consider addressing {warning_count} warnings to improve quality")
        
        # Distribution-based recommendations
        intent_dist = statistics.get('intent_distribution', {})
        if len(intent_dist) < 3:
            recommendations.append("Add more diverse intent examples for better classification")
        
        # Check for class imbalance
        if intent_dist:
            max_count = max(intent_dist.values())
            min_count = min(intent_dist.values())
            if max_count > min_count * 5:
                recommendations.append("Consider balancing intent classes - some are underrepresented")
        
        # Text length recommendations
        text_stats = statistics.get('text_length_stats', {})
        avg_length = text_stats.get('mean', 0)
        if avg_length < 20:
            recommendations.append("Consider adding more detailed examples - average text length is very short")
        elif avg_length > 1000:
            recommendations.append("Consider splitting very long examples into smaller, focused examples")
        
        # Confidence recommendations
        confidence_stats = statistics.get('confidence_stats', {})
        avg_confidence = confidence_stats.get('mean', 0)
        if avg_confidence < 0.7:
            recommendations.append("Review examples with low confidence scores and improve labeling quality")
        
        return recommendations
    
    def _assess_consistency(self, examples: List[TrainingExample]) -> float:
        """Assess consistency of labels for similar texts."""
        # Simple consistency check based on text similarity and label agreement
        # This is a simplified implementation - could be enhanced with more sophisticated similarity measures
        
        if len(examples) < 2:
            return 1.0
        
        consistent_pairs = 0
        total_pairs = 0
        
        # Sample pairs to avoid O(n²) complexity for large datasets
        sample_size = min(100, len(examples))
        sampled_examples = examples[:sample_size]
        
        for i, ex1 in enumerate(sampled_examples):
            for j, ex2 in enumerate(sampled_examples[i+1:], i+1):
                if self._texts_similar(ex1.text, ex2.text):
                    total_pairs += 1
                    if (ex1.expected_intent == ex2.expected_intent and 
                        ex1.expected_sentiment == ex2.expected_sentiment):
                        consistent_pairs += 1
        
        return consistent_pairs / total_pairs if total_pairs > 0 else 1.0
    
    def _texts_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar (simple implementation)."""
        if not text1 or not text2:
            return False
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _assess_diversity(self, examples: List[TrainingExample]) -> float:
        """Assess lexical diversity of the dataset."""
        if not examples:
            return 0.0
        
        all_words = []
        for example in examples:
            if example.text:
                words = example.text.lower().split()
                all_words.extend(words)
        
        if not all_words:
            return 0.0
        
        unique_words = len(set(all_words))
        total_words = len(all_words)
        
        # Type-token ratio as a measure of diversity
        diversity = unique_words / total_words
        return min(1.0, diversity * 2)  # Scale to make it more meaningful
    
    def _assess_balance(self, examples: List[TrainingExample]) -> float:
        """Assess class balance across intents and sentiments."""
        if not examples:
            return 0.0
        
        # Intent balance
        intent_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)
        
        for example in examples:
            if example.expected_intent:
                intent_counts[example.expected_intent] += 1
            if example.expected_sentiment:
                sentiment_counts[example.expected_sentiment] += 1
        
        # Calculate balance scores
        intent_balance = self._calculate_balance_score(list(intent_counts.values()))
        sentiment_balance = self._calculate_balance_score(list(sentiment_counts.values()))
        
        return (intent_balance + sentiment_balance) / 2
    
    def _calculate_balance_score(self, counts: List[int]) -> float:
        """Calculate balance score for a list of class counts."""
        if not counts or len(counts) < 2:
            return 1.0
        
        total = sum(counts)
        if total == 0:
            return 0.0
        
        # Calculate entropy-based balance score
        proportions = [count / total for count in counts]
        entropy = -sum(p * np.log2(p) for p in proportions if p > 0)
        max_entropy = np.log2(len(counts))
        
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _assess_complexity(self, examples: List[TrainingExample]) -> float:
        """Assess linguistic complexity of the dataset."""
        if not examples:
            return 0.0
        
        complexities = []
        
        for example in examples:
            if example.text:
                # Simple complexity measures
                words = example.text.split()
                sentences = example.text.split('.')
                
                avg_word_length = np.mean([len(word) for word in words]) if words else 0
                avg_sentence_length = np.mean([len(sent.split()) for sent in sentences if sent.strip()]) if sentences else 0
                
                # Normalize complexity score
                complexity = (avg_word_length / 10 + avg_sentence_length / 20) / 2
                complexities.append(min(1.0, complexity))
        
        return np.mean(complexities) if complexities else 0.0
    
    def _remove_duplicates(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Remove duplicate examples from the dataset."""
        seen_texts = set()
        unique_examples = []
        
        for example in examples:
            text_key = example.text.strip().lower() if example.text else ""
            if text_key and text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_examples.append(example)
        
        return unique_examples
    
    def _balance_classes(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Balance classes in the dataset through sampling."""
        # Group by intent
        intent_groups = defaultdict(list)
        for example in examples:
            intent_groups[example.expected_intent].append(example)
        
        if len(intent_groups) < 2:
            return examples
        
        # Find target size (median of group sizes)
        group_sizes = [len(group) for group in intent_groups.values()]
        target_size = int(np.median(group_sizes))
        
        balanced_examples = []
        for intent, group in intent_groups.items():
            if len(group) <= target_size:
                # Keep all examples
                balanced_examples.extend(group)
            else:
                # Sample down to target size
                sampled = np.random.choice(group, target_size, replace=False)
                balanced_examples.extend(sampled)
        
        return balanced_examples
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return text
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text
    
    def _apply_modifications(
        self, 
        examples: List[TrainingExample], 
        modifications: Dict[str, Any]
    ) -> List[TrainingExample]:
        """Apply modifications to a list of examples."""
        modified_examples = []
        
        for example in examples:
            modified_example = TrainingExample(
                text=example.text,
                expected_intent=example.expected_intent,
                expected_sentiment=example.expected_sentiment,
                expected_entities=example.expected_entities.copy(),
                expected_persona=example.expected_persona,
                confidence=example.confidence,
                source=example.source,
                metadata=example.metadata.copy(),
                created_at=example.created_at
            )
            
            # Apply modifications
            if 'intent_mapping' in modifications:
                intent_mapping = modifications['intent_mapping']
                if modified_example.expected_intent in intent_mapping:
                    modified_example.expected_intent = intent_mapping[modified_example.expected_intent]
            
            if 'sentiment_mapping' in modifications:
                sentiment_mapping = modifications['sentiment_mapping']
                if modified_example.expected_sentiment in sentiment_mapping:
                    modified_example.expected_sentiment = sentiment_mapping[modified_example.expected_sentiment]
            
            if 'confidence_adjustment' in modifications:
                adjustment = modifications['confidence_adjustment']
                modified_example.confidence = max(0, min(1, modified_example.confidence + adjustment))
            
            modified_examples.append(modified_example)
        
        return modified_examples