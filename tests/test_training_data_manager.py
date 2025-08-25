"""
Tests for the TrainingDataManager system.

This module tests all aspects of training data management including dataset
curation, editing, upload, validation, format conversion, version control,
and automated quality assessment.
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

from ai_karen_engine.core.response.training_data_manager import (
    TrainingDataManager,
    DataFormat,
    DataQuality,
    ValidationSeverity,
    DatasetVersion,
    ValidationIssue,
    ValidationReport,
    DatasetMetadata,
    QualityMetrics
)
from ai_karen_engine.core.response.autonomous_learner import (
    TrainingExample,
    LearningDataType
)


class TestTrainingDataManager:
    """Test suite for TrainingDataManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create TrainingDataManager instance for testing."""
        return TrainingDataManager(data_dir=temp_dir)
    
    @pytest.fixture
    def sample_examples(self):
        """Create sample training examples for testing."""
        return [
            TrainingExample(
                text="How do I optimize this code?",
                expected_intent="optimize_code",
                expected_sentiment="neutral",
                expected_entities=[("code", "TECH", 21, 25)],
                confidence=0.9,
                source=LearningDataType.CONVERSATION
            ),
            TrainingExample(
                text="I'm frustrated with this bug",
                expected_intent="debug_error",
                expected_sentiment="frustrated",
                expected_entities=[("bug", "ISSUE", 23, 26)],
                confidence=0.8,
                source=LearningDataType.USER_FEEDBACK
            ),
            TrainingExample(
                text="Can you help me write documentation?",
                expected_intent="write_docs",
                expected_sentiment="positive",
                expected_entities=[("documentation", "TASK", 22, 35)],
                confidence=0.95,
                source=LearningDataType.CONVERSATION
            )
        ]
    
    def test_create_dataset(self, manager):
        """Test dataset creation."""
        dataset_id = manager.create_dataset(
            name="Test Dataset",
            description="A test dataset for unit testing",
            created_by="test_user",
            format=DataFormat.JSON,
            tags=["test", "unit_test"]
        )
        
        assert dataset_id is not None
        assert len(dataset_id) == 36  # UUID length
        
        # Check metadata was created
        metadata = manager._load_dataset_metadata(dataset_id)
        assert metadata is not None
        assert metadata.name == "Test Dataset"
        assert metadata.description == "A test dataset for unit testing"
        assert metadata.created_by == "test_user"
        assert metadata.format == DataFormat.JSON
        assert metadata.tags == ["test", "unit_test"]
        assert metadata.size == 0
        assert metadata.quality_score == 0.0
    
    def test_upload_dataset(self, manager, sample_examples):
        """Test dataset upload functionality."""
        # Create dataset
        dataset_id = manager.create_dataset(
            name="Upload Test",
            description="Test upload functionality",
            created_by="test_user"
        )
        
        # Upload examples
        version_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON,
            version_description="Initial test upload"
        )
        
        assert version_id is not None
        
        # Verify data was uploaded
        retrieved_examples = manager.get_dataset(dataset_id)
        assert len(retrieved_examples) == len(sample_examples)
        
        # Check metadata was updated
        metadata = manager._load_dataset_metadata(dataset_id)
        assert metadata.size == len(sample_examples)
        assert metadata.quality_score > 0
    
    def test_get_dataset(self, manager, sample_examples):
        """Test dataset retrieval."""
        # Create and upload dataset
        dataset_id = manager.create_dataset(
            name="Retrieval Test",
            description="Test retrieval functionality",
            created_by="test_user"
        )
        
        version_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON
        )
        
        # Test retrieval
        retrieved_examples = manager.get_dataset(dataset_id)
        assert len(retrieved_examples) == len(sample_examples)
        
        # Verify content
        for original, retrieved in zip(sample_examples, retrieved_examples):
            assert retrieved.text == original.text
            assert retrieved.expected_intent == original.expected_intent
            assert retrieved.expected_sentiment == original.expected_sentiment
            assert retrieved.confidence == original.confidence
    
    def test_validate_dataset(self, manager, sample_examples):
        """Test dataset validation functionality."""
        # Test with valid examples
        report = manager.validate_dataset(sample_examples)
        
        assert report.total_examples == len(sample_examples)
        assert report.valid_examples == len(sample_examples)
        assert report.invalid_examples == 0
        assert report.quality_score > 0.5
        assert len(report.issues) == 0  # Should be no issues with good examples
        
        # Test with invalid examples
        invalid_examples = [
            TrainingExample(
                text="",  # Empty text
                expected_intent="",  # Empty intent
                expected_sentiment="positive",
                confidence=1.5  # Invalid confidence
            ),
            TrainingExample(
                text="Very short",
                expected_intent="test",
                expected_sentiment="",  # Empty sentiment
                confidence=-0.1  # Invalid confidence
            )
        ]
        
        report = manager.validate_dataset(invalid_examples)
        assert report.total_examples == len(invalid_examples)
        assert report.invalid_examples > 0
        assert len(report.issues) > 0
        
        # Check for specific validation issues
        error_issues = [issue for issue in report.issues if issue.severity == ValidationSeverity.ERROR]
        assert len(error_issues) > 0
    
    def test_format_conversion(self, manager, sample_examples):
        """Test format conversion functionality."""
        # Test JSON conversion
        json_data = manager.convert_format(sample_examples, DataFormat.JSON)
        assert isinstance(json_data, list)
        assert len(json_data) == len(sample_examples)
        assert all('text' in item for item in json_data)
        
        # Test JSONL conversion
        jsonl_data = manager.convert_format(sample_examples, DataFormat.JSONL)
        assert isinstance(jsonl_data, str)
        lines = jsonl_data.strip().split('\n')
        assert len(lines) == len(sample_examples)
        
        # Test CSV conversion
        csv_data = manager.convert_format(sample_examples, DataFormat.CSV)
        assert isinstance(csv_data, str)
        assert 'text,expected_intent' in csv_data
        
        # Test spaCy conversion
        spacy_data = manager.convert_format(sample_examples, DataFormat.SPACY)
        assert isinstance(spacy_data, list)
        assert len(spacy_data) == len(sample_examples)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in spacy_data)
        
        # Test HuggingFace conversion
        hf_data = manager.convert_format(sample_examples, DataFormat.HUGGINGFACE)
        assert isinstance(hf_data, dict)
        assert 'text' in hf_data
        assert 'intent' in hf_data
        assert 'sentiment' in hf_data
        assert len(hf_data['text']) == len(sample_examples)
    
    def test_quality_assessment(self, manager, sample_examples):
        """Test quality assessment functionality."""
        metrics = manager.assess_quality(sample_examples)
        
        assert isinstance(metrics, QualityMetrics)
        assert 0 <= metrics.completeness <= 1
        assert 0 <= metrics.consistency <= 1
        assert 0 <= metrics.accuracy <= 1
        assert 0 <= metrics.diversity <= 1
        assert 0 <= metrics.balance <= 1
        assert 0 <= metrics.complexity <= 1
        assert 0 <= metrics.overall_score <= 1
        
        # Test with high-quality examples
        assert metrics.completeness > 0.8  # Should be high for complete examples
        assert metrics.overall_score > 0.5  # Should be decent for good examples
    
    def test_data_enhancement(self, manager, sample_examples):
        """Test data enhancement functionality."""
        # Add some problematic examples
        problematic_examples = sample_examples + [
            TrainingExample(
                text="  Extra   whitespace   everywhere  ",
                expected_intent="test",
                expected_sentiment="neutral",
                confidence=1.5  # Invalid confidence
            ),
            TrainingExample(
                text="How do I optimize this code?",  # Duplicate
                expected_intent="optimize_code",
                expected_sentiment="neutral",
                confidence=0.9
            )
        ]
        
        enhanced = manager.enhance_dataset(problematic_examples)
        
        # Should have fewer examples due to duplicate removal
        assert len(enhanced) < len(problematic_examples)
        
        # Check that text was cleaned
        for example in enhanced:
            if example.text:
                assert not example.text.startswith(' ')
                assert not example.text.endswith(' ')
                assert '   ' not in example.text  # No excessive whitespace
            
            # Check confidence was fixed
            assert 0 <= example.confidence <= 1
    
    def test_version_control(self, manager, sample_examples):
        """Test version control functionality."""
        # Create dataset and initial version
        dataset_id = manager.create_dataset(
            name="Version Test",
            description="Test version control",
            created_by="test_user"
        )
        
        version1_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON,
            version_description="Initial version"
        )
        
        # Create second version with modifications
        modified_examples = sample_examples + [
            TrainingExample(
                text="New example for version 2",
                expected_intent="general_assist",
                expected_sentiment="neutral",
                confidence=0.8
            )
        ]
        
        version2_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in modified_examples],
            format=DataFormat.JSON,
            version_description="Added new example"
        )
        
        # Test version listing
        versions = manager.list_versions(dataset_id)
        assert len(versions) == 2
        assert version2_id in [v.version_id for v in versions]
        assert version1_id in [v.version_id for v in versions]
        
        # Test retrieving specific versions
        v1_examples = manager.get_dataset(dataset_id, version1_id)
        v2_examples = manager.get_dataset(dataset_id, version2_id)
        
        assert len(v1_examples) == len(sample_examples)
        assert len(v2_examples) == len(modified_examples)
        
        # Test creating version from existing
        version3_id = manager.create_version_from_existing(
            dataset_id=dataset_id,
            source_version=version1_id,
            description="Copy of version 1",
            modifications={'confidence_adjustment': 0.1}
        )
        
        v3_examples = manager.get_dataset(dataset_id, version3_id)
        assert len(v3_examples) == len(sample_examples)
        
        # Check confidence was adjusted
        for original, modified in zip(sample_examples, v3_examples):
            expected_confidence = min(1.0, original.confidence + 0.1)
            assert abs(modified.confidence - expected_confidence) < 0.001
    
    def test_export_import(self, manager, sample_examples):
        """Test export and import functionality."""
        # Create and populate dataset
        dataset_id = manager.create_dataset(
            name="Export Test",
            description="Test export functionality",
            created_by="test_user"
        )
        
        manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON
        )
        
        # Test export
        exported_data = manager.export_dataset(
            dataset_id=dataset_id,
            format=DataFormat.JSON,
            include_metadata=True
        )
        
        assert isinstance(exported_data, bytes)
        
        # Parse exported data
        exported_json = json.loads(exported_data.decode('utf-8'))
        assert 'examples' in exported_json
        assert 'metadata' in exported_json
        assert len(exported_json['examples']) == len(sample_examples)
        
        # Test import
        imported_dataset_id = manager.import_dataset(
            data=exported_data,
            format=DataFormat.JSON,
            dataset_name="Imported Dataset",
            created_by="test_user",
            description="Imported from export test"
        )
        
        # Verify imported data
        imported_examples = manager.get_dataset(imported_dataset_id)
        assert len(imported_examples) == len(sample_examples)
        
        # Check content matches
        for original, imported in zip(sample_examples, imported_examples):
            assert imported.text == original.text
            assert imported.expected_intent == original.expected_intent
            assert imported.expected_sentiment == original.expected_sentiment
    
    def test_validation_issues(self, manager):
        """Test specific validation issue detection."""
        # Create examples with various issues
        problematic_examples = [
            TrainingExample(
                text="",  # Empty text - ERROR
                expected_intent="test",
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="Hi",  # Very short text - WARNING
                expected_intent="greet",
                expected_sentiment="positive"
            ),
            TrainingExample(
                text="A" * 15000,  # Very long text - WARNING
                expected_intent="long_text",
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="Normal text",
                expected_intent="",  # Empty intent - ERROR
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="Another normal text",
                expected_intent="test",
                expected_sentiment="",  # Empty sentiment - ERROR
            ),
            TrainingExample(
                text="Text with entities",
                expected_intent="entity_test",
                expected_sentiment="neutral",
                expected_entities=[("invalid", "LABEL", -1, 100)],  # Invalid entity span - ERROR
                confidence=2.0  # Invalid confidence - WARNING
            )
        ]
        
        report = manager.validate_dataset(problematic_examples)
        
        # Should have multiple issues
        assert len(report.issues) > 0
        
        # Check for specific issue types
        error_issues = [issue for issue in report.issues if issue.severity == ValidationSeverity.ERROR]
        warning_issues = [issue for issue in report.issues if issue.severity == ValidationSeverity.WARNING]
        
        assert len(error_issues) >= 4  # Empty text, intent, sentiment, invalid entity
        assert len(warning_issues) >= 3  # Short text, long text, invalid confidence
        
        # Check that recommendations were generated
        assert len(report.recommendations) > 0
    
    def test_statistical_analysis(self, manager, sample_examples):
        """Test statistical analysis of datasets."""
        # Create dataset with known distribution
        balanced_examples = []
        intents = ["intent1", "intent2", "intent3"]
        sentiments = ["positive", "negative", "neutral"]
        
        for intent in intents:
            for sentiment in sentiments:
                for i in range(5):  # 5 examples per combination
                    balanced_examples.append(TrainingExample(
                        text=f"Example text for {intent} and {sentiment} {i}",
                        expected_intent=intent,
                        expected_sentiment=sentiment,
                        confidence=0.8 + i * 0.05
                    ))
        
        report = manager.validate_dataset(balanced_examples)
        stats = report.statistics
        
        # Check intent distribution
        assert 'intent_distribution' in stats
        intent_dist = stats['intent_distribution']
        assert len(intent_dist) == 3
        assert all(count == 15 for count in intent_dist.values())  # 15 examples per intent
        
        # Check sentiment distribution
        assert 'sentiment_distribution' in stats
        sentiment_dist = stats['sentiment_distribution']
        assert len(sentiment_dist) == 3
        assert all(count == 15 for count in sentiment_dist.values())  # 15 examples per sentiment
        
        # Check text length statistics
        assert 'text_length_stats' in stats
        length_stats = stats['text_length_stats']
        assert length_stats['mean'] > 0
        assert length_stats['min'] > 0
        assert length_stats['max'] > length_stats['min']
    
    def test_quality_metrics_edge_cases(self, manager):
        """Test quality metrics with edge cases."""
        # Test with empty dataset
        empty_metrics = manager.assess_quality([])
        assert empty_metrics.overall_score == 0
        assert empty_metrics.completeness == 0
        
        # Test with single example
        single_example = [TrainingExample(
            text="Single example",
            expected_intent="test",
            expected_sentiment="neutral"
        )]
        
        single_metrics = manager.assess_quality(single_example)
        assert single_metrics.completeness == 1.0  # Complete example
        assert single_metrics.overall_score > 0
        
        # Test with highly imbalanced dataset
        imbalanced_examples = []
        # 90 examples of one intent
        for i in range(90):
            imbalanced_examples.append(TrainingExample(
                text=f"Common intent example {i}",
                expected_intent="common",
                expected_sentiment="neutral"
            ))
        
        # 10 examples of another intent
        for i in range(10):
            imbalanced_examples.append(TrainingExample(
                text=f"Rare intent example {i}",
                expected_intent="rare",
                expected_sentiment="neutral"
            ))
        
        imbalanced_metrics = manager.assess_quality(imbalanced_examples)
        # Balance score should be lower due to imbalance
        assert imbalanced_metrics.balance < 0.8
    
    def test_data_cleaning(self, manager):
        """Test data cleaning functionality."""
        dirty_text = "  \t  Extra   whitespace\n\n  and   newlines  \t  "
        clean_text = manager._clean_text(dirty_text)
        
        assert clean_text == "Extra whitespace and newlines"
        assert not clean_text.startswith(' ')
        assert not clean_text.endswith(' ')
        assert '  ' not in clean_text  # No double spaces
        
        # Test with None/empty
        assert manager._clean_text(None) is None
        assert manager._clean_text("") == ""
        assert manager._clean_text("   ") == ""
    
    def test_duplicate_removal(self, manager, sample_examples):
        """Test duplicate removal functionality."""
        # Create dataset with duplicates
        examples_with_dupes = sample_examples + [
            TrainingExample(
                text="How do I optimize this code?",  # Exact duplicate
                expected_intent="optimize_code",
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="HOW DO I OPTIMIZE THIS CODE?",  # Case variation
                expected_intent="optimize_code",
                expected_sentiment="neutral"
            )
        ]
        
        unique_examples = manager._remove_duplicates(examples_with_dupes)
        
        # Should have fewer examples
        assert len(unique_examples) < len(examples_with_dupes)
        
        # Should keep original examples
        assert len(unique_examples) >= len(sample_examples)
    
    def test_class_balancing(self, manager):
        """Test class balancing functionality."""
        # Create imbalanced dataset
        imbalanced_examples = []
        
        # 20 examples of intent1
        for i in range(20):
            imbalanced_examples.append(TrainingExample(
                text=f"Intent1 example {i}",
                expected_intent="intent1",
                expected_sentiment="neutral"
            ))
        
        # 5 examples of intent2
        for i in range(5):
            imbalanced_examples.append(TrainingExample(
                text=f"Intent2 example {i}",
                expected_intent="intent2",
                expected_sentiment="neutral"
            ))
        
        # 10 examples of intent3
        for i in range(10):
            imbalanced_examples.append(TrainingExample(
                text=f"Intent3 example {i}",
                expected_intent="intent3",
                expected_sentiment="neutral"
            ))
        
        balanced_examples = manager._balance_classes(imbalanced_examples)
        
        # Count examples per intent
        intent_counts = {}
        for example in balanced_examples:
            intent_counts[example.expected_intent] = intent_counts.get(example.expected_intent, 0) + 1
        
        # Should be more balanced (target is median = 10)
        assert intent_counts["intent1"] <= 10  # Should be reduced
        assert intent_counts["intent2"] == 5   # Should stay the same (below target)
        assert intent_counts["intent3"] == 10  # Should stay the same (at target)
    
    def test_error_handling(self, manager):
        """Test error handling in various scenarios."""
        # Test with non-existent dataset
        with pytest.raises(ValueError):
            manager.get_dataset("non-existent-id")
        
        # Test upload to non-existent dataset
        with pytest.raises(ValueError):
            manager.upload_dataset(
                dataset_id="non-existent-id",
                data=[],
                format=DataFormat.JSON
            )
        
        # Test invalid format conversion
        with pytest.raises(ValueError):
            manager.convert_format([], DataFormat.CUSTOM)
        
        # Test invalid import data
        with pytest.raises(Exception):
            manager.import_dataset(
                data=b"invalid json data",
                format=DataFormat.JSON,
                dataset_name="Test",
                created_by="test"
            )
    
    def test_checksum_calculation(self, manager, temp_dir):
        """Test checksum calculation for version integrity."""
        # Create a test file
        test_file = Path(temp_dir) / "test.json"
        test_data = {"test": "data"}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Calculate checksum
        checksum1 = manager._calculate_checksum(test_file)
        assert checksum1 is not None
        assert len(checksum1) == 64  # SHA-256 hex length
        
        # Same file should produce same checksum
        checksum2 = manager._calculate_checksum(test_file)
        assert checksum1 == checksum2
        
        # Modified file should produce different checksum
        with open(test_file, 'w') as f:
            json.dump({"test": "modified"}, f)
        
        checksum3 = manager._calculate_checksum(test_file)
        assert checksum1 != checksum3
    
    def test_provenance_tracking(self, manager, sample_examples):
        """Test provenance tracking for datasets."""
        # Create dataset
        dataset_id = manager.create_dataset(
            name="Provenance Test",
            description="Test provenance tracking",
            created_by="test_user"
        )
        
        # Check initial provenance
        metadata = manager._load_dataset_metadata(dataset_id)
        assert 'provenance' in metadata.to_dict()
        assert 'created_via' in metadata.provenance
        assert 'timestamp' in metadata.provenance
        
        # Upload data and check version provenance
        version_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON,
            version_description="Test upload"
        )
        
        versions = manager.list_versions(dataset_id)
        version = next(v for v in versions if v.version_id == version_id)
        
        assert version.created_at is not None
        assert version.description == "Test upload"
        assert version.checksum is not None
    
    def test_concurrent_operations(self, manager, sample_examples):
        """Test concurrent operations on the training data manager."""
        # Create dataset
        dataset_id = manager.create_dataset(
            name="Concurrent Test",
            description="Test concurrent operations",
            created_by="test_user"
        )
        
        # Run sequential uploads (simulating concurrent behavior)
        results = []
        for i in range(3):
            data = [manager._example_to_dict(ex) for ex in sample_examples[i:i+1]]
            result = manager.upload_dataset(
                dataset_id=dataset_id,
                data=data,
                format=DataFormat.JSON,
                version_description=f"Sequential upload {i}"
            )
            results.append(result)
        
        # All uploads should succeed
        assert len(results) == 3
        assert all(result is not None for result in results)
        
        # Check versions were created
        versions = manager.list_versions(dataset_id)
        assert len(versions) >= 3


if __name__ == "__main__":
    pytest.main([__file__])