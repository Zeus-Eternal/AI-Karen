"""
Tests for the spaCy-based autonomous learning engine.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from ai_karen_engine.core.response.autonomous_learner import (
    AutonomousLearner,
    ConversationMetadata,
    ConversationMetadataCollector,
    IncrementalTrainingPipeline,
    ModelValidator,
    TrainingExample,
    ValidationResult,
    LearningCycleResult,
    LearningDataType,
    TrainingStatus,
    create_autonomous_learner
)
from ai_karen_engine.core.response.analyzer import SpacyAnalyzer
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.memory_service import WebUIMemoryService, MemoryType, UISource


@pytest.fixture
def mock_spacy_service():
    """Mock SpacyService for testing."""
    service = MagicMock(spec=SpacyService)
    service.nlp = MagicMock()
    service.config = MagicMock()
    service.config.model_name = "en_core_web_sm"
    service.clear_cache = MagicMock()
    
    # Mock parse_message
    async def mock_parse_message(text):
        return ParsedMessage(
            tokens=text.split(),
            lemmas=[token.lower() for token in text.split()],
            entities=[("Python", "LANGUAGE"), ("API", "PRODUCT")],
            pos_tags=[(token, "NOUN") for token in text.split()],
            noun_phrases=["Python API"],
            sentences=[text],
            dependencies=[],
            language="en",
            processing_time=0.1,
            used_fallback=False
        )
    
    service.parse_message = mock_parse_message
    service.extract_entities = AsyncMock(return_value=[("Python", "LANGUAGE")])
    service.get_linguistic_features = AsyncMock(return_value={"token_count": 5})
    
    return service


@pytest.fixture
def mock_spacy_analyzer(mock_spacy_service):
    """Mock SpacyAnalyzer for testing."""
    analyzer = MagicMock(spec=SpacyAnalyzer)
    analyzer.spacy_service = mock_spacy_service
    
    # Mock async methods
    analyzer._detect_intent_async = AsyncMock(return_value="technical_question")
    analyzer._sentiment_async = AsyncMock(return_value="neutral")
    analyzer._entities_async = AsyncMock(return_value={
        "entities": [{"text": "Python", "label": "LANGUAGE"}],
        "metadata": {"token_count": 5, "original_text": "How do I use Python API?"}
    })
    analyzer.select_persona = MagicMock(return_value="technical-expert")
    
    return analyzer


@pytest.fixture
def mock_memory_service():
    """Mock WebUIMemoryService for testing."""
    service = MagicMock(spec=WebUIMemoryService)
    service.store_web_ui_memory = AsyncMock(return_value="memory_123")
    
    # Mock memory entries
    mock_memory = MagicMock()
    mock_memory.id = "memory_123"
    mock_memory.metadata = {
        "conversation_id": "conv_123",
        "user_id": "user_123",
        "session_id": "session_123",
        "timestamp": datetime.utcnow().isoformat(),
        "intent_detected": "technical_question",
        "sentiment_detected": "neutral",
        "persona_selected": "technical-expert",
        "user_satisfaction": 0.8,
        "response_quality": 0.9,
        "entities_extracted": [["Python", "LANGUAGE"]],
        "linguistic_features": {"token_count": 5, "original_text": "How do I use Python API?"},
        "context_used": [],
        "feedback_provided": True,
        "correction_needed": False
    }
    
    service.query_memories = AsyncMock(return_value=[mock_memory])
    
    return service


@pytest.fixture
def conversation_metadata():
    """Sample conversation metadata for testing."""
    return ConversationMetadata(
        conversation_id="conv_123",
        user_id="user_123",
        session_id="session_123",
        timestamp=datetime.utcnow(),
        intent_detected="technical_question",
        sentiment_detected="neutral",
        persona_selected="technical-expert",
        user_satisfaction=0.8,
        response_quality=0.9,
        entities_extracted=[("Python", "LANGUAGE"), ("API", "PRODUCT")],
        linguistic_features={"token_count": 5, "original_text": "How do I use Python API?"},
        context_used=["previous_context"],
        feedback_provided=True,
        correction_needed=False
    )


@pytest.fixture
def training_examples():
    """Sample training examples for testing."""
    return [
        TrainingExample(
            text="How do I use Python API?",
            expected_intent="technical_question",
            expected_sentiment="neutral",
            expected_entities=[("Python", "LANGUAGE", 14, 20), ("API", "PRODUCT", 21, 24)],
            expected_persona="technical-expert",
            confidence=0.9,
            source=LearningDataType.CONVERSATION
        ),
        TrainingExample(
            text="I'm frustrated with this bug",
            expected_intent="debug_error",
            expected_sentiment="frustrated",
            expected_entities=[("bug", "PROBLEM", 24, 27)],
            expected_persona="support-assistant",
            confidence=0.8,
            source=LearningDataType.USER_FEEDBACK
        )
    ]


class TestConversationMetadata:
    """Test ConversationMetadata class."""
    
    def test_to_dict(self, conversation_metadata):
        """Test conversion to dictionary."""
        result = conversation_metadata.to_dict()
        
        assert result["conversation_id"] == "conv_123"
        assert result["user_id"] == "user_123"
        assert result["intent_detected"] == "technical_question"
        assert result["sentiment_detected"] == "neutral"
        assert result["persona_selected"] == "technical-expert"
        assert result["user_satisfaction"] == 0.8
        assert result["response_quality"] == 0.9
        assert result["entities_extracted"] == [("Python", "LANGUAGE"), ("API", "PRODUCT")]
        assert result["feedback_provided"] is True
        assert result["correction_needed"] is False


class TestTrainingExample:
    """Test TrainingExample class."""
    
    def test_to_spacy_format(self, training_examples):
        """Test conversion to spaCy training format."""
        example = training_examples[0]
        text, annotations = example.to_spacy_format()
        
        assert text == "How do I use Python API?"
        assert "entities" in annotations
        assert "cats" in annotations
        
        # Check entities format
        entities = annotations["entities"]
        assert (14, 20, "LANGUAGE") in entities
        assert (21, 24, "PRODUCT") in entities
        
        # Check categories format
        cats = annotations["cats"]
        assert cats["INTENT_TECHNICAL_QUESTION"] == 1.0
        assert cats["SENTIMENT_NEUTRAL"] == 1.0


class TestConversationMetadataCollector:
    """Test ConversationMetadataCollector class."""
    
    @pytest.fixture
    def collector(self, mock_memory_service, mock_spacy_analyzer):
        """Create collector instance for testing."""
        return ConversationMetadataCollector(mock_memory_service, mock_spacy_analyzer)
    
    @pytest.mark.asyncio
    async def test_collect_from_conversation(self, collector):
        """Test collecting metadata from conversation."""
        tenant_id = "tenant_123"
        user_text = "How do I use Python API?"
        assistant_response = "Here's how to use the Python API..."
        user_id = "user_123"
        session_id = "session_123"
        conversation_id = "conv_123"
        user_feedback = {
            "satisfaction_score": 0.8,
            "response_quality": 0.9,
            "needs_correction": False
        }
        
        metadata = await collector.collect_from_conversation(
            tenant_id=tenant_id,
            user_text=user_text,
            assistant_response=assistant_response,
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            user_feedback=user_feedback
        )
        
        assert metadata.conversation_id == conversation_id
        assert metadata.user_id == user_id
        assert metadata.session_id == session_id
        assert metadata.intent_detected == "technical_question"
        assert metadata.sentiment_detected == "neutral"
        assert metadata.persona_selected == "technical-expert"
        assert metadata.user_satisfaction == 0.8
        assert metadata.response_quality == 0.9
        assert metadata.feedback_provided is True
        assert metadata.correction_needed is False
        
        # Verify memory storage was called
        collector.memory_service.store_web_ui_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_curate_training_data(self, collector):
        """Test curating training data from memory."""
        tenant_id = "tenant_123"
        
        curated_data = await collector.curate_training_data(
            tenant_id=tenant_id,
            min_confidence=0.7,
            max_examples=100
        )
        
        assert len(curated_data) == 1
        metadata = curated_data[0]
        assert metadata.conversation_id == "conv_123"
        assert metadata.intent_detected == "technical_question"
        assert metadata.sentiment_detected == "neutral"
        
        # Verify memory query was called
        collector.memory_service.query_memories.assert_called_once()
    
    def test_passes_quality_filters(self, collector, conversation_metadata):
        """Test quality filtering logic."""
        # Should pass with good metadata
        assert collector._passes_quality_filters(conversation_metadata, 0.7) is True
        
        # Should fail if correction needed
        conversation_metadata.correction_needed = True
        assert collector._passes_quality_filters(conversation_metadata, 0.7) is False
        
        # Should fail if satisfaction too low
        conversation_metadata.correction_needed = False
        conversation_metadata.user_satisfaction = 0.5
        assert collector._passes_quality_filters(conversation_metadata, 0.7) is False


class TestIncrementalTrainingPipeline:
    """Test IncrementalTrainingPipeline class."""
    
    @pytest.fixture
    def pipeline(self, mock_spacy_service, tmp_path):
        """Create pipeline instance for testing."""
        return IncrementalTrainingPipeline(mock_spacy_service, tmp_path)
    
    @pytest.mark.asyncio
    async def test_create_training_examples(self, pipeline, conversation_metadata):
        """Test creating training examples from metadata."""
        metadata_list = [conversation_metadata]
        
        examples = await pipeline.create_training_examples(metadata_list)
        
        assert len(examples) == 1
        example = examples[0]
        assert example.text == "How do I use Python API?"
        assert example.expected_intent == "technical_question"
        assert example.expected_sentiment == "neutral"
        assert example.confidence == 0.8
        assert example.source == LearningDataType.CONVERSATION
    
    @pytest.mark.asyncio
    async def test_backup_current_model(self, pipeline, tmp_path):
        """Test model backup functionality."""
        # Mock model to_disk method
        pipeline.spacy_service.nlp.to_disk = MagicMock()
        
        backup_path = await pipeline.backup_current_model()
        
        assert backup_path is not None
        assert Path(backup_path).exists()
        assert Path(backup_path, "backup_metadata.json").exists()
        
        # Verify model was saved
        pipeline.spacy_service.nlp.to_disk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_train_incremental(self, pipeline, training_examples):
        """Test incremental training."""
        # Mock model update method
        pipeline.spacy_service.nlp.update = MagicMock()
        
        success, result = await pipeline.train_incremental(training_examples)
        
        assert success is True
        assert "training_examples" in result
        assert "iterations" in result
        assert "losses" in result
        assert result["training_examples"] == len(training_examples)
    
    @pytest.mark.asyncio
    async def test_rollback_model(self, pipeline, tmp_path):
        """Test model rollback functionality."""
        # Create a mock backup directory
        backup_dir = tmp_path / "test_backup"
        backup_dir.mkdir()
        
        # Mock spacy.load
        with patch("spacy.load") as mock_load:
            mock_nlp = MagicMock()
            mock_load.return_value = mock_nlp
            
            success = await pipeline.rollback_model(str(backup_dir))
            
            assert success is True
            assert pipeline.spacy_service.nlp == mock_nlp
            pipeline.spacy_service.clear_cache.assert_called_once()


class TestModelValidator:
    """Test ModelValidator class."""
    
    @pytest.fixture
    def validator(self, mock_spacy_analyzer):
        """Create validator instance for testing."""
        return ModelValidator(mock_spacy_analyzer)
    
    @pytest.mark.asyncio
    async def test_validate_model(self, validator, training_examples):
        """Test model validation."""
        result = await validator.validate_model(training_examples)
        
        assert isinstance(result, ValidationResult)
        assert result.validation_examples == len(training_examples)
        assert 0 <= result.accuracy <= 1
        assert 0 <= result.intent_accuracy <= 1
        assert 0 <= result.sentiment_accuracy <= 1
        assert 0 <= result.entity_accuracy <= 1
        assert isinstance(result.passed_threshold, bool)
    
    @pytest.mark.asyncio
    async def test_validate_model_with_errors(self, validator, training_examples):
        """Test model validation with detailed errors."""
        # Make analyzer return wrong predictions
        validator.spacy_analyzer._detect_intent_async.return_value = "wrong_intent"
        
        result = await validator.validate_model(training_examples, detailed_errors=True)
        
        assert result.accuracy < 1.0  # Should have errors
        assert len(result.errors) > 0
        assert result.passed_threshold is False


class TestAutonomousLearner:
    """Test AutonomousLearner main class."""
    
    @pytest.fixture
    def learner(self, mock_spacy_analyzer, mock_memory_service, mock_spacy_service, tmp_path):
        """Create learner instance for testing."""
        return AutonomousLearner(
            spacy_analyzer=mock_spacy_analyzer,
            memory_service=mock_memory_service,
            spacy_service=mock_spacy_service,
            model_backup_dir=tmp_path
        )
    
    @pytest.mark.asyncio
    async def test_collect_conversation_metadata(self, learner):
        """Test conversation metadata collection."""
        tenant_id = "tenant_123"
        user_text = "How do I use Python API?"
        assistant_response = "Here's how..."
        user_id = "user_123"
        
        metadata = await learner.collect_conversation_metadata(
            tenant_id=tenant_id,
            user_text=user_text,
            assistant_response=assistant_response,
            user_id=user_id
        )
        
        assert metadata.user_id == user_id
        assert metadata.intent_detected == "technical_question"
        assert metadata.sentiment_detected == "neutral"
        assert metadata.persona_selected == "technical-expert"
    
    @pytest.mark.asyncio
    async def test_trigger_learning_cycle_insufficient_data(self, learner):
        """Test learning cycle with insufficient data."""
        tenant_id = "tenant_123"
        
        # Mock empty curated data
        learner.metadata_collector.curate_training_data = AsyncMock(return_value=[])
        
        result = await learner.trigger_learning_cycle(tenant_id)
        
        assert result.status == TrainingStatus.COMPLETED
        assert result.data_collected == 0
        assert "insufficient data" in result.error_message.lower()
        assert result.model_improved is False
    
    @pytest.mark.asyncio
    async def test_trigger_learning_cycle_success(self, learner, conversation_metadata):
        """Test successful learning cycle."""
        tenant_id = "tenant_123"
        
        # Mock sufficient data
        learner.metadata_collector.curate_training_data = AsyncMock(
            return_value=[conversation_metadata] * 60  # Above threshold
        )
        
        # Mock successful training
        learner.training_pipeline.train_incremental = AsyncMock(
            return_value=(True, {"training_examples": 60, "backup_path": "/tmp/backup"})
        )
        
        # Mock successful validation
        validation_result = ValidationResult(
            accuracy=0.9,
            precision=0.9,
            recall=0.9,
            f1_score=0.9,
            intent_accuracy=0.9,
            sentiment_accuracy=0.9,
            entity_accuracy=0.9,
            validation_examples=12,
            passed_threshold=True
        )
        learner.validator.validate_model = AsyncMock(return_value=validation_result)
        
        result = await learner.trigger_learning_cycle(tenant_id)
        
        assert result.status == TrainingStatus.COMPLETED
        assert result.model_improved is True
        assert result.data_collected == 60
        assert result.validation_result is not None
        assert result.validation_result.passed_threshold is True
    
    @pytest.mark.asyncio
    async def test_trigger_learning_cycle_rollback(self, learner, conversation_metadata):
        """Test learning cycle with rollback due to poor validation."""
        tenant_id = "tenant_123"
        
        # Mock sufficient data
        learner.metadata_collector.curate_training_data = AsyncMock(
            return_value=[conversation_metadata] * 60
        )
        
        # Mock successful training
        learner.training_pipeline.train_incremental = AsyncMock(
            return_value=(True, {"training_examples": 60, "backup_path": "/tmp/backup"})
        )
        
        # Mock failed validation
        validation_result = ValidationResult(
            accuracy=0.5,  # Below threshold
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            intent_accuracy=0.5,
            sentiment_accuracy=0.5,
            entity_accuracy=0.5,
            validation_examples=12,
            passed_threshold=False
        )
        learner.validator.validate_model = AsyncMock(return_value=validation_result)
        
        # Mock successful rollback
        learner.training_pipeline.rollback_model = AsyncMock(return_value=True)
        
        result = await learner.trigger_learning_cycle(tenant_id)
        
        assert result.status == TrainingStatus.ROLLED_BACK
        assert result.model_improved is False
        assert result.rollback_performed is True
        assert "validation failed" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_get_learning_metrics_empty(self, learner):
        """Test getting metrics with no learning history."""
        metrics = await learner.get_learning_metrics()
        
        assert metrics["total_cycles"] == 0
        assert metrics["successful_cycles"] == 0
        assert metrics["failed_cycles"] == 0
        assert metrics["average_training_time"] == 0
        assert metrics["last_cycle"] is None
        assert metrics["model_improvements"] == 0
    
    @pytest.mark.asyncio
    async def test_get_learning_metrics_with_history(self, learner):
        """Test getting metrics with learning history."""
        # Add some mock history
        successful_result = LearningCycleResult(
            cycle_id="cycle_1",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=TrainingStatus.COMPLETED,
            data_collected=100,
            examples_created=80,
            training_time=30.0,
            model_improved=True
        )
        
        failed_result = LearningCycleResult(
            cycle_id="cycle_2",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=TrainingStatus.FAILED,
            data_collected=50,
            examples_created=0,
            error_message="Training failed"
        )
        
        learner.learning_history = [successful_result, failed_result]
        
        metrics = await learner.get_learning_metrics()
        
        assert metrics["total_cycles"] == 2
        assert metrics["successful_cycles"] == 1
        assert metrics["failed_cycles"] == 1
        assert metrics["average_training_time"] == 30.0
        assert metrics["model_improvements"] == 1
        assert metrics["last_cycle"]["cycle_id"] == "cycle_2"


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_autonomous_learner(self, mock_spacy_analyzer, mock_memory_service, tmp_path):
        """Test factory function creates proper instance."""
        learner = create_autonomous_learner(
            spacy_analyzer=mock_spacy_analyzer,
            memory_service=mock_memory_service,
            model_backup_dir=tmp_path
        )
        
        assert isinstance(learner, AutonomousLearner)
        assert learner.spacy_analyzer == mock_spacy_analyzer
        assert learner.memory_service == mock_memory_service
        assert learner.training_pipeline.model_backup_dir == tmp_path


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_learning_workflow(self, mock_spacy_analyzer, mock_memory_service, mock_spacy_service, tmp_path):
        """Test complete end-to-end learning workflow."""
        learner = AutonomousLearner(
            spacy_analyzer=mock_spacy_analyzer,
            memory_service=mock_memory_service,
            spacy_service=mock_spacy_service,
            model_backup_dir=tmp_path
        )
        
        tenant_id = "tenant_123"
        
        # Step 1: Collect conversation metadata
        metadata = await learner.collect_conversation_metadata(
            tenant_id=tenant_id,
            user_text="How do I optimize this Python code?",
            assistant_response="Here are some optimization techniques...",
            user_id="user_123",
            user_feedback={"satisfaction_score": 0.9, "response_quality": 0.8}
        )
        
        assert metadata is not None
        assert metadata.intent_detected == "technical_question"
        
        # Step 2: Mock sufficient training data for learning cycle
        conversation_metadata = ConversationMetadata(
            conversation_id="conv_123",
            user_id="user_123",
            session_id="session_123",
            timestamp=datetime.utcnow(),
            intent_detected="optimize_code",
            sentiment_detected="neutral",
            persona_selected="technical-expert",
            user_satisfaction=0.9,
            response_quality=0.8,
            entities_extracted=[("Python", "LANGUAGE")],
            linguistic_features={"token_count": 6, "original_text": "How do I optimize this Python code?"},
            feedback_provided=True,
            correction_needed=False
        )
        
        learner.metadata_collector.curate_training_data = AsyncMock(
            return_value=[conversation_metadata] * 60  # Above threshold
        )
        
        # Mock successful training and validation
        learner.training_pipeline.train_incremental = AsyncMock(
            return_value=(True, {"training_examples": 60, "backup_path": str(tmp_path / "backup")})
        )
        
        validation_result = ValidationResult(
            accuracy=0.9,
            precision=0.9,
            recall=0.9,
            f1_score=0.9,
            intent_accuracy=0.9,
            sentiment_accuracy=0.9,
            entity_accuracy=0.9,
            validation_examples=12,
            passed_threshold=True
        )
        learner.validator.validate_model = AsyncMock(return_value=validation_result)
        
        # Step 3: Trigger learning cycle
        result = await learner.trigger_learning_cycle(tenant_id)
        
        assert result.status == TrainingStatus.COMPLETED
        assert result.model_improved is True
        
        # Step 4: Check learning metrics
        metrics = await learner.get_learning_metrics()
        
        assert metrics["total_cycles"] == 1
        assert metrics["successful_cycles"] == 1
        assert metrics["model_improvements"] == 1


if __name__ == "__main__":
    pytest.main([__file__])