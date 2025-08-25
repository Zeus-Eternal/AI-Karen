"""
Demo script for the TrainingDataManager system.

This script demonstrates the comprehensive training data management capabilities
including dataset creation, upload, validation, format conversion, version control,
and quality assessment.
"""

import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from ai_karen_engine.core.response.training_data_manager import (
    TrainingDataManager,
    DataFormat,
    ValidationSeverity
)
from ai_karen_engine.core.response.autonomous_learner import (
    TrainingExample,
    LearningDataType
)


def create_sample_data():
    """Create sample training data for demonstration."""
    return [
        TrainingExample(
            text="How can I optimize this Python code for better performance?",
            expected_intent="optimize_code",
            expected_sentiment="neutral",
            expected_entities=[("Python", "LANGUAGE", 25, 31), ("code", "TECH", 32, 36)],
            expected_persona="ruthless_optimizer",
            confidence=0.95,
            source=LearningDataType.CONVERSATION,
            metadata={"complexity": "medium", "domain": "programming"}
        ),
        TrainingExample(
            text="I'm really frustrated with this bug that keeps appearing",
            expected_intent="debug_error",
            expected_sentiment="frustrated",
            expected_entities=[("bug", "ISSUE", 35, 38)],
            expected_persona="calm_fixit",
            confidence=0.9,
            source=LearningDataType.USER_FEEDBACK,
            metadata={"urgency": "high", "emotion": "frustrated"}
        ),
        TrainingExample(
            text="Can you help me write comprehensive documentation for my API?",
            expected_intent="write_docs",
            expected_sentiment="positive",
            expected_entities=[("documentation", "TASK", 32, 45), ("API", "TECH", 56, 59)],
            expected_persona="technical_writer",
            confidence=0.88,
            source=LearningDataType.CONVERSATION,
            metadata={"task_type": "documentation", "scope": "comprehensive"}
        ),
        TrainingExample(
            text="What's the best way to implement authentication in a web app?",
            expected_intent="implement_feature",
            expected_sentiment="curious",
            expected_entities=[("authentication", "FEATURE", 32, 46), ("web app", "PLATFORM", 52, 59)],
            expected_persona="security_expert",
            confidence=0.92,
            source=LearningDataType.CONVERSATION,
            metadata={"category": "security", "platform": "web"}
        ),
        TrainingExample(
            text="This error message doesn't make any sense to me",
            expected_intent="explain_error",
            expected_sentiment="confused",
            expected_entities=[("error message", "ISSUE", 5, 18)],
            expected_persona="patient_teacher",
            confidence=0.85,
            source=LearningDataType.USER_FEEDBACK,
            metadata={"clarity": "low", "help_needed": "explanation"}
        )
    ]


def demonstrate_basic_operations():
    """Demonstrate basic dataset operations."""
    print("=== Basic Dataset Operations ===")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Initialize manager
        manager = TrainingDataManager(data_dir=temp_dir)
        
        # Create dataset
        print("\n1. Creating dataset...")
        dataset_id = manager.create_dataset(
            name="Demo Dataset",
            description="Demonstration dataset for training data management",
            created_by="demo_user",
            format=DataFormat.JSON,
            tags=["demo", "training", "examples"]
        )
        print(f"Created dataset: {dataset_id}")
        
        # Create sample data
        sample_examples = create_sample_data()
        
        # Upload data
        print("\n2. Uploading training data...")
        version_id = manager.upload_dataset(
            dataset_id=dataset_id,
            data=[manager._example_to_dict(ex) for ex in sample_examples],
            format=DataFormat.JSON,
            version_description="Initial demo data upload"
        )
        print(f"Uploaded data, created version: {version_id}")
        
        # Retrieve data
        print("\n3. Retrieving dataset...")
        retrieved_examples = manager.get_dataset(dataset_id)
        print(f"Retrieved {len(retrieved_examples)} examples")
        
        # Display first example
        if retrieved_examples:
            first_example = retrieved_examples[0]
            print(f"First example:")
            print(f"  Text: {first_example.text}")
            print(f"  Intent: {first_example.expected_intent}")
            print(f"  Sentiment: {first_example.expected_sentiment}")
            print(f"  Confidence: {first_example.confidence}")
        
        return manager, dataset_id, sample_examples
        
    except Exception as e:
        print(f"Error in basic operations: {e}")
        shutil.rmtree(temp_dir)
        raise


def demonstrate_validation():
    """Demonstrate dataset validation capabilities."""
    print("\n=== Dataset Validation ===")
    
    manager, dataset_id, sample_examples = demonstrate_basic_operations()
    
    try:
        # Validate good data
        print("\n1. Validating good data...")
        validation_report = manager.validate_dataset(sample_examples)
        
        print(f"Validation Results:")
        print(f"  Total examples: {validation_report.total_examples}")
        print(f"  Valid examples: {validation_report.valid_examples}")
        print(f"  Invalid examples: {validation_report.invalid_examples}")
        print(f"  Quality score: {validation_report.quality_score:.2f}")
        print(f"  Issues found: {len(validation_report.issues)}")
        
        if validation_report.recommendations:
            print(f"  Recommendations:")
            for rec in validation_report.recommendations:
                print(f"    - {rec}")
        
        # Create problematic data for validation demo
        print("\n2. Validating problematic data...")
        problematic_examples = [
            TrainingExample(
                text="",  # Empty text
                expected_intent="test",
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="Hi",  # Very short
                expected_intent="greet",
                expected_sentiment="positive"
            ),
            TrainingExample(
                text="Normal text",
                expected_intent="",  # Empty intent
                expected_sentiment="neutral"
            ),
            TrainingExample(
                text="Another example",
                expected_intent="test",
                expected_sentiment="",  # Empty sentiment
                confidence=1.5  # Invalid confidence
            )
        ]
        
        problematic_report = manager.validate_dataset(problematic_examples)
        
        print(f"Problematic Data Results:")
        print(f"  Total examples: {problematic_report.total_examples}")
        print(f"  Valid examples: {problematic_report.valid_examples}")
        print(f"  Invalid examples: {problematic_report.invalid_examples}")
        print(f"  Quality score: {problematic_report.quality_score:.2f}")
        print(f"  Issues found: {len(problematic_report.issues)}")
        
        # Show specific issues
        if problematic_report.issues:
            print(f"  Specific Issues:")
            for issue in problematic_report.issues[:5]:  # Show first 5 issues
                print(f"    - {issue.severity.value.upper()}: {issue.message}")
                if issue.suggestion:
                    print(f"      Suggestion: {issue.suggestion}")
        
        return manager, dataset_id
        
    except Exception as e:
        print(f"Error in validation demo: {e}")
        raise


def demonstrate_format_conversion():
    """Demonstrate format conversion capabilities."""
    print("\n=== Format Conversion ===")
    
    manager, dataset_id = demonstrate_validation()
    
    try:
        # Get sample data
        examples = manager.get_dataset(dataset_id)
        
        # Convert to different formats
        formats_to_test = [
            DataFormat.JSON,
            DataFormat.JSONL,
            DataFormat.CSV,
            DataFormat.SPACY,
            DataFormat.HUGGINGFACE
        ]
        
        for format_type in formats_to_test:
            print(f"\n1. Converting to {format_type.value}...")
            converted_data = manager.convert_format(examples, format_type)
            
            if format_type == DataFormat.JSON:
                print(f"  JSON format: {len(converted_data)} items")
                if converted_data:
                    print(f"  Sample keys: {list(converted_data[0].keys())}")
            
            elif format_type == DataFormat.JSONL:
                lines = converted_data.strip().split('\n')
                print(f"  JSONL format: {len(lines)} lines")
                if lines:
                    sample_line = json.loads(lines[0])
                    print(f"  Sample keys: {list(sample_line.keys())}")
            
            elif format_type == DataFormat.CSV:
                lines = converted_data.strip().split('\n')
                print(f"  CSV format: {len(lines)} lines (including header)")
                if lines:
                    header = lines[0]
                    print(f"  Header: {header}")
            
            elif format_type == DataFormat.SPACY:
                print(f"  spaCy format: {len(converted_data)} training examples")
                if converted_data:
                    text, annotations = converted_data[0]
                    print(f"  Sample text: {text[:50]}...")
                    print(f"  Sample annotations: {list(annotations.keys())}")
            
            elif format_type == DataFormat.HUGGINGFACE:
                print(f"  HuggingFace format: {list(converted_data.keys())}")
                for key, values in converted_data.items():
                    print(f"    {key}: {len(values)} items")
        
        return manager, dataset_id
        
    except Exception as e:
        print(f"Error in format conversion demo: {e}")
        raise


def demonstrate_quality_assessment():
    """Demonstrate quality assessment capabilities."""
    print("\n=== Quality Assessment ===")
    
    manager, dataset_id = demonstrate_format_conversion()
    
    try:
        # Get examples
        examples = manager.get_dataset(dataset_id)
        
        # Assess quality
        print("\n1. Assessing data quality...")
        quality_metrics = manager.assess_quality(examples)
        
        print(f"Quality Metrics:")
        print(f"  Completeness: {quality_metrics.completeness:.2f}")
        print(f"  Consistency: {quality_metrics.consistency:.2f}")
        print(f"  Accuracy: {quality_metrics.accuracy:.2f}")
        print(f"  Diversity: {quality_metrics.diversity:.2f}")
        print(f"  Balance: {quality_metrics.balance:.2f}")
        print(f"  Complexity: {quality_metrics.complexity:.2f}")
        print(f"  Overall Score: {quality_metrics.overall_score:.2f}")
        
        # Create imbalanced dataset for comparison
        print("\n2. Comparing with imbalanced data...")
        imbalanced_examples = []
        
        # 80% optimize_code, 20% other intents
        for i in range(8):
            imbalanced_examples.append(TrainingExample(
                text=f"How to optimize code example {i}",
                expected_intent="optimize_code",
                expected_sentiment="neutral"
            ))
        
        for i in range(2):
            imbalanced_examples.append(TrainingExample(
                text=f"Debug error example {i}",
                expected_intent="debug_error",
                expected_sentiment="frustrated"
            ))
        
        imbalanced_metrics = manager.assess_quality(imbalanced_examples)
        
        print(f"Imbalanced Data Quality:")
        print(f"  Balance: {imbalanced_metrics.balance:.2f} (vs {quality_metrics.balance:.2f})")
        print(f"  Overall Score: {imbalanced_metrics.overall_score:.2f} (vs {quality_metrics.overall_score:.2f})")
        
        return manager, dataset_id
        
    except Exception as e:
        print(f"Error in quality assessment demo: {e}")
        raise


def demonstrate_version_control():
    """Demonstrate version control capabilities."""
    print("\n=== Version Control ===")
    
    manager, dataset_id = demonstrate_quality_assessment()
    
    try:
        # List current versions
        print("\n1. Listing current versions...")
        versions = manager.list_versions(dataset_id)
        print(f"Current versions: {len(versions)}")
        
        for version in versions:
            print(f"  Version {version.version_number} ({version.version_id[:8]}...)")
            print(f"    Created: {version.created_at}")
            print(f"    Description: {version.description}")
            print(f"    Size: {version.size} examples")
            print(f"    Quality: {version.quality_score:.2f}")
        
        # Create a new version with modifications
        print("\n2. Creating modified version...")
        if versions:
            latest_version = versions[0]
            
            # Create new version with confidence adjustment
            new_version_id = manager.create_version_from_existing(
                dataset_id=dataset_id,
                source_version=latest_version.version_id,
                description="Adjusted confidence scores",
                modifications={'confidence_adjustment': 0.05}
            )
            
            print(f"Created new version: {new_version_id}")
            
            # Compare versions
            original_examples = manager.get_dataset(dataset_id, latest_version.version_id)
            modified_examples = manager.get_dataset(dataset_id, new_version_id)
            
            print(f"Version comparison:")
            print(f"  Original version: {len(original_examples)} examples")
            print(f"  Modified version: {len(modified_examples)} examples")
            
            if original_examples and modified_examples:
                orig_conf = original_examples[0].confidence
                mod_conf = modified_examples[0].confidence
                print(f"  Sample confidence change: {orig_conf:.2f} -> {mod_conf:.2f}")
        
        # List versions again
        print("\n3. Updated version list...")
        updated_versions = manager.list_versions(dataset_id)
        print(f"Total versions now: {len(updated_versions)}")
        
        return manager, dataset_id
        
    except Exception as e:
        print(f"Error in version control demo: {e}")
        raise


def demonstrate_enhancement():
    """Demonstrate data enhancement capabilities."""
    print("\n=== Data Enhancement ===")
    
    manager, dataset_id = demonstrate_version_control()
    
    try:
        # Create data that needs enhancement
        print("\n1. Creating data that needs enhancement...")
        messy_examples = [
            TrainingExample(
                text="  How   to   optimize   code?  ",  # Extra whitespace
                expected_intent="optimize_code",
                expected_sentiment="neutral",
                confidence=1.2  # Invalid confidence
            ),
            TrainingExample(
                text="Debug this error please",
                expected_intent="debug_error",
                expected_sentiment="frustrated",
                confidence=0.8
            ),
            TrainingExample(
                text="  How   to   optimize   code?  ",  # Duplicate
                expected_intent="optimize_code",
                expected_sentiment="neutral",
                confidence=0.9
            ),
            TrainingExample(
                text="Write documentation",
                expected_intent="write_docs",
                expected_sentiment="neutral",
                confidence=-0.1  # Invalid confidence
            )
        ]
        
        print(f"Original messy data: {len(messy_examples)} examples")
        
        # Show issues
        for i, ex in enumerate(messy_examples):
            print(f"  Example {i+1}:")
            print(f"    Text: '{ex.text}'")
            print(f"    Confidence: {ex.confidence}")
        
        # Enhance the data
        print("\n2. Enhancing data...")
        enhanced_examples = manager.enhance_dataset(messy_examples)
        
        print(f"Enhanced data: {len(enhanced_examples)} examples")
        
        # Show improvements
        for i, ex in enumerate(enhanced_examples):
            print(f"  Enhanced example {i+1}:")
            print(f"    Text: '{ex.text}'")
            print(f"    Confidence: {ex.confidence}")
        
        # Compare quality
        original_quality = manager.assess_quality(messy_examples)
        enhanced_quality = manager.assess_quality(enhanced_examples)
        
        print(f"\n3. Quality comparison:")
        print(f"  Original overall score: {original_quality.overall_score:.2f}")
        print(f"  Enhanced overall score: {enhanced_quality.overall_score:.2f}")
        print(f"  Improvement: {enhanced_quality.overall_score - original_quality.overall_score:.2f}")
        
        return manager, dataset_id
        
    except Exception as e:
        print(f"Error in enhancement demo: {e}")
        raise


def demonstrate_export_import():
    """Demonstrate export and import capabilities."""
    print("\n=== Export and Import ===")
    
    manager, dataset_id = demonstrate_enhancement()
    
    try:
        # Export dataset
        print("\n1. Exporting dataset...")
        exported_data = manager.export_dataset(
            dataset_id=dataset_id,
            format=DataFormat.JSON,
            include_metadata=True
        )
        
        print(f"Exported data size: {len(exported_data)} bytes")
        
        # Parse exported data to show structure
        exported_json = json.loads(exported_data.decode('utf-8'))
        print(f"Export structure:")
        print(f"  Examples: {len(exported_json.get('examples', []))}")
        print(f"  Metadata included: {'metadata' in exported_json}")
        
        if 'metadata' in exported_json:
            metadata = exported_json['metadata']
            print(f"  Dataset name: {metadata.get('name')}")
            print(f"  Created by: {metadata.get('created_by')}")
        
        # Import as new dataset
        print("\n2. Importing as new dataset...")
        imported_dataset_id = manager.import_dataset(
            data=exported_data,
            format=DataFormat.JSON,
            dataset_name="Imported Demo Dataset",
            created_by="demo_importer",
            description="Dataset imported from export demo"
        )
        
        print(f"Imported dataset ID: {imported_dataset_id}")
        
        # Verify imported data
        imported_examples = manager.get_dataset(imported_dataset_id)
        original_examples = manager.get_dataset(dataset_id)
        
        print(f"Verification:")
        print(f"  Original examples: {len(original_examples)}")
        print(f"  Imported examples: {len(imported_examples)}")
        
        # Compare first example
        if original_examples and imported_examples:
            orig = original_examples[0]
            imported = imported_examples[0]
            
            print(f"  Sample comparison:")
            print(f"    Original text: {orig.text}")
            print(f"    Imported text: {imported.text}")
            print(f"    Match: {orig.text == imported.text}")
        
        return manager, dataset_id, imported_dataset_id
        
    except Exception as e:
        print(f"Error in export/import demo: {e}")
        raise


def demonstrate_statistics():
    """Demonstrate statistical analysis capabilities."""
    print("\n=== Statistical Analysis ===")
    
    manager, original_dataset_id, imported_dataset_id = demonstrate_export_import()
    
    try:
        # Get examples for analysis
        examples = manager.get_dataset(original_dataset_id)
        
        # Generate validation report with statistics
        print("\n1. Generating comprehensive statistics...")
        validation_report = manager.validate_dataset(examples)
        stats = validation_report.statistics
        
        print(f"Dataset Statistics:")
        print(f"  Total examples: {stats.get('total_examples', 0)}")
        
        # Intent distribution
        intent_dist = stats.get('intent_distribution', {})
        print(f"  Intent distribution:")
        for intent, count in intent_dist.items():
            percentage = (count / stats.get('total_examples', 1)) * 100
            print(f"    {intent}: {count} ({percentage:.1f}%)")
        
        # Sentiment distribution
        sentiment_dist = stats.get('sentiment_distribution', {})
        print(f"  Sentiment distribution:")
        for sentiment, count in sentiment_dist.items():
            percentage = (count / stats.get('total_examples', 1)) * 100
            print(f"    {sentiment}: {count} ({percentage:.1f}%)")
        
        # Text length statistics
        length_stats = stats.get('text_length_stats', {})
        if length_stats:
            print(f"  Text length statistics:")
            print(f"    Mean: {length_stats.get('mean', 0):.1f} characters")
            print(f"    Median: {length_stats.get('median', 0):.1f} characters")
            print(f"    Min: {length_stats.get('min', 0)} characters")
            print(f"    Max: {length_stats.get('max', 0)} characters")
            print(f"    Std Dev: {length_stats.get('std', 0):.1f} characters")
        
        # Confidence statistics
        conf_stats = stats.get('confidence_stats', {})
        if conf_stats:
            print(f"  Confidence statistics:")
            print(f"    Mean: {conf_stats.get('mean', 0):.2f}")
            print(f"    Median: {conf_stats.get('median', 0):.2f}")
            print(f"    Min: {conf_stats.get('min', 0):.2f}")
            print(f"    Max: {conf_stats.get('max', 0):.2f}")
            print(f"    Std Dev: {conf_stats.get('std', 0):.2f}")
        
        # Source distribution
        source_dist = stats.get('source_distribution', {})
        if source_dist:
            print(f"  Source distribution:")
            for source, count in source_dist.items():
                percentage = (count / stats.get('total_examples', 1)) * 100
                print(f"    {source}: {count} ({percentage:.1f}%)")
        
        print(f"\n2. Quality assessment summary:")
        quality_metrics = manager.assess_quality(examples)
        print(f"  Overall quality score: {quality_metrics.overall_score:.2f}/1.0")
        
        quality_breakdown = [
            ("Completeness", quality_metrics.completeness),
            ("Consistency", quality_metrics.consistency),
            ("Accuracy", quality_metrics.accuracy),
            ("Diversity", quality_metrics.diversity),
            ("Balance", quality_metrics.balance),
            ("Complexity", quality_metrics.complexity)
        ]
        
        for metric_name, score in quality_breakdown:
            status = "Excellent" if score > 0.8 else "Good" if score > 0.6 else "Fair" if score > 0.4 else "Poor"
            print(f"    {metric_name}: {score:.2f} ({status})")
        
    except Exception as e:
        print(f"Error in statistics demo: {e}")
        raise
    
    finally:
        # Cleanup
        print(f"\n=== Cleanup ===")
        try:
            temp_dir = manager.data_dir
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Run the complete training data manager demonstration."""
    print("Training Data Manager Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_statistics()
        print(f"\n=== Demo Complete ===")
        print("All training data management features demonstrated successfully!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()