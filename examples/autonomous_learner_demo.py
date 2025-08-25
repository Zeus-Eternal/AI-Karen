"""
Demo script for the spaCy-based autonomous learning engine.

This script demonstrates how to use the AutonomousLearner to:
1. Collect conversation metadata
2. Curate training data
3. Perform incremental training
4. Validate model improvements
5. Monitor learning metrics
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock imports for demo (in real usage, these would be actual imports)
try:
    from ai_karen_engine.core.response.autonomous_learner import (
        AutonomousLearner,
        ConversationMetadata,
        create_autonomous_learner
    )
    from ai_karen_engine.core.response.analyzer import SpacyAnalyzer, create_spacy_analyzer
    from ai_karen_engine.services.spacy_service import SpacyService
    from ai_karen_engine.services.memory_service import WebUIMemoryService
    IMPORTS_AVAILABLE = True
except ImportError:
    logger.warning("Required modules not available, running in demo mode")
    IMPORTS_AVAILABLE = False


class MockSpacyService:
    """Mock SpacyService for demo purposes."""
    
    def __init__(self):
        self.nlp = MockNLP()
        self.config = MockConfig()
    
    def clear_cache(self):
        logger.info("SpaCy cache cleared")
    
    async def parse_message(self, text: str):
        """Mock parse message."""
        from dataclasses import dataclass
        from typing import List, Tuple, Dict, Any
        
        @dataclass
        class MockParsedMessage:
            tokens: List[str]
            lemmas: List[str]
            entities: List[Tuple[str, str]]
            pos_tags: List[Tuple[str, str]]
            noun_phrases: List[str]
            sentences: List[str]
            dependencies: List[Dict[str, Any]]
            language: str = "en"
            processing_time: float = 0.1
            used_fallback: bool = False
        
        return MockParsedMessage(
            tokens=text.split(),
            lemmas=[token.lower() for token in text.split()],
            entities=[("Python", "LANGUAGE"), ("API", "PRODUCT")],
            pos_tags=[(token, "NOUN") for token in text.split()],
            noun_phrases=["Python API"],
            sentences=[text],
            dependencies=[]
        )


class MockNLP:
    """Mock spaCy NLP model."""
    
    def update(self, texts, annotations, losses=None, drop=0.0):
        """Mock model update."""
        if losses is not None:
            losses.update({"ner": 0.1, "textcat": 0.05})
    
    def to_disk(self, path):
        """Mock save to disk."""
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Mock model saved to {path}")


class MockConfig:
    """Mock spaCy config."""
    
    def __init__(self):
        self.model_name = "en_core_web_sm"


class MockSpacyAnalyzer:
    """Mock SpacyAnalyzer for demo purposes."""
    
    def __init__(self):
        self.spacy_service = MockSpacyService()
    
    async def _detect_intent_async(self, text: str) -> str:
        """Mock intent detection."""
        text_lower = text.lower()
        if "optimize" in text_lower or "performance" in text_lower:
            return "optimize_code"
        elif "error" in text_lower or "bug" in text_lower:
            return "debug_error"
        elif "how" in text_lower or "what" in text_lower:
            return "technical_question"
        else:
            return "general_assist"
    
    async def _sentiment_async(self, text: str) -> str:
        """Mock sentiment analysis."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["frustrated", "annoying", "terrible"]):
            return "frustrated"
        elif any(word in text_lower for word in ["excited", "awesome", "great"]):
            return "excited"
        else:
            return "neutral"
    
    async def _entities_async(self, text: str) -> Dict[str, Any]:
        """Mock entity extraction."""
        entities = []
        if "python" in text.lower():
            entities.append({"text": "Python", "label": "LANGUAGE"})
        if "api" in text.lower():
            entities.append({"text": "API", "label": "PRODUCT"})
        
        return {
            "entities": entities,
            "metadata": {
                "token_count": len(text.split()),
                "original_text": text
            }
        }
    
    def select_persona(self, intent: str, sentiment: str) -> str:
        """Mock persona selection."""
        if intent == "optimize_code":
            return "technical-expert"
        elif intent == "debug_error" and sentiment == "frustrated":
            return "support-assistant"
        elif intent == "technical_question":
            return "technical-expert"
        else:
            return "support-assistant"


class MockMemoryService:
    """Mock WebUIMemoryService for demo purposes."""
    
    def __init__(self):
        self.stored_memories = []
    
    async def store_web_ui_memory(self, **kwargs) -> str:
        """Mock memory storage."""
        memory_id = str(uuid.uuid4())
        self.stored_memories.append({
            "id": memory_id,
            **kwargs
        })
        logger.info(f"Stored memory: {memory_id}")
        return memory_id
    
    async def query_memories(self, tenant_id, query):
        """Mock memory query."""
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class MockMemory:
            id: str
            metadata: Dict[str, Any]
        
        # Return mock memories with conversation metadata
        mock_memories = []
        for i in range(5):  # Return 5 mock memories
            mock_memories.append(MockMemory(
                id=f"memory_{i}",
                metadata={
                    "conversation_id": f"conv_{i}",
                    "user_id": "user_123",
                    "session_id": "session_123",
                    "timestamp": datetime.utcnow().isoformat(),
                    "intent_detected": "technical_question",
                    "sentiment_detected": "neutral",
                    "persona_selected": "technical-expert",
                    "user_satisfaction": 0.8,
                    "response_quality": 0.9,
                    "entities_extracted": [["Python", "LANGUAGE"]],
                    "linguistic_features": {"token_count": 5, "original_text": f"Sample question {i}"},
                    "context_used": [],
                    "feedback_provided": True,
                    "correction_needed": False
                }
            ))
        
        return mock_memories


async def demo_conversation_metadata_collection():
    """Demo conversation metadata collection."""
    logger.info("=== Demo: Conversation Metadata Collection ===")
    
    # Create mock services
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    # Create autonomous learner
    learner = AutonomousLearner(
        spacy_analyzer=spacy_analyzer,
        memory_service=memory_service,
        spacy_service=spacy_analyzer.spacy_service
    )
    
    tenant_id = "demo_tenant"
    
    # Simulate conversation interactions
    conversations = [
        {
            "user_text": "How do I optimize this Python code for better performance?",
            "assistant_response": "Here are several optimization techniques you can use...",
            "user_feedback": {"satisfaction_score": 0.9, "response_quality": 0.8}
        },
        {
            "user_text": "I'm getting a frustrating error in my API call",
            "assistant_response": "Let me help you debug this error step by step...",
            "user_feedback": {"satisfaction_score": 0.7, "response_quality": 0.8}
        },
        {
            "user_text": "What's the best way to handle database connections?",
            "assistant_response": "For database connections, I recommend using connection pooling...",
            "user_feedback": {"satisfaction_score": 0.8, "response_quality": 0.9}
        }
    ]
    
    collected_metadata = []
    
    for i, conv in enumerate(conversations):
        logger.info(f"Processing conversation {i+1}: {conv['user_text'][:50]}...")
        
        metadata = await learner.collect_conversation_metadata(
            tenant_id=tenant_id,
            user_text=conv["user_text"],
            assistant_response=conv["assistant_response"],
            user_id="demo_user",
            session_id="demo_session",
            conversation_id=f"conv_{i}",
            user_feedback=conv["user_feedback"]
        )
        
        collected_metadata.append(metadata)
        
        logger.info(f"  Intent: {metadata.intent_detected}")
        logger.info(f"  Sentiment: {metadata.sentiment_detected}")
        logger.info(f"  Persona: {metadata.persona_selected}")
        logger.info(f"  Satisfaction: {metadata.user_satisfaction}")
        logger.info(f"  Entities: {metadata.entities_extracted}")
    
    logger.info(f"Collected {len(collected_metadata)} conversation metadata entries")
    return collected_metadata


async def demo_training_data_curation():
    """Demo training data curation."""
    logger.info("\n=== Demo: Training Data Curation ===")
    
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    learner = AutonomousLearner(
        spacy_analyzer=spacy_analyzer,
        memory_service=memory_service,
        spacy_service=spacy_analyzer.spacy_service
    )
    
    tenant_id = "demo_tenant"
    
    # Curate training data from memory
    curated_metadata = await learner.metadata_collector.curate_training_data(
        tenant_id=tenant_id,
        min_confidence=0.7,
        max_examples=100
    )
    
    logger.info(f"Curated {len(curated_metadata)} high-quality metadata entries")
    
    for i, metadata in enumerate(curated_metadata[:3]):  # Show first 3
        logger.info(f"  Entry {i+1}:")
        logger.info(f"    Intent: {metadata.intent_detected}")
        logger.info(f"    Sentiment: {metadata.sentiment_detected}")
        logger.info(f"    Satisfaction: {metadata.user_satisfaction}")
        logger.info(f"    Feedback provided: {metadata.feedback_provided}")
    
    return curated_metadata


async def demo_incremental_training():
    """Demo incremental training pipeline."""
    logger.info("\n=== Demo: Incremental Training ===")
    
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    # Create temporary directory for model backups
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        learner = AutonomousLearner(
            spacy_analyzer=spacy_analyzer,
            memory_service=memory_service,
            spacy_service=spacy_analyzer.spacy_service,
            model_backup_dir=Path(tmp_dir)
        )
        
        # Create sample conversation metadata
        sample_metadata = [
            ConversationMetadata(
                conversation_id=f"conv_{i}",
                user_id="demo_user",
                session_id="demo_session",
                timestamp=datetime.utcnow(),
                intent_detected="technical_question",
                sentiment_detected="neutral",
                persona_selected="technical-expert",
                user_satisfaction=0.8,
                response_quality=0.9,
                entities_extracted=[("Python", "LANGUAGE")],
                linguistic_features={"token_count": 5, "original_text": f"Sample question {i}"},
                feedback_provided=True,
                correction_needed=False
            )
            for i in range(10)
        ]
        
        # Create training examples
        training_examples = await learner.training_pipeline.create_training_examples(sample_metadata)
        logger.info(f"Created {len(training_examples)} training examples")
        
        # Backup current model
        backup_path = await learner.training_pipeline.backup_current_model()
        logger.info(f"Model backed up to: {backup_path}")
        
        # Perform incremental training
        success, result = await learner.training_pipeline.train_incremental(training_examples)
        
        if success:
            logger.info("Training completed successfully!")
            logger.info(f"  Training examples: {result['training_examples']}")
            logger.info(f"  Iterations: {result['iterations']}")
            logger.info(f"  Final losses: {result['losses'].get('iter_9', {})}")
        else:
            logger.error(f"Training failed: {result.get('error')}")
        
        return success, result


async def demo_model_validation():
    """Demo model validation."""
    logger.info("\n=== Demo: Model Validation ===")
    
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    learner = AutonomousLearner(
        spacy_analyzer=spacy_analyzer,
        memory_service=memory_service,
        spacy_service=spacy_analyzer.spacy_service
    )
    
    # Create validation examples
    from ai_karen_engine.core.response.autonomous_learner import TrainingExample, LearningDataType
    
    validation_examples = [
        TrainingExample(
            text="How do I optimize this Python code?",
            expected_intent="optimize_code",
            expected_sentiment="neutral",
            expected_entities=[("Python", "LANGUAGE", 20, 26)],
            confidence=0.9,
            source=LearningDataType.CONVERSATION
        ),
        TrainingExample(
            text="I'm frustrated with this bug",
            expected_intent="debug_error",
            expected_sentiment="frustrated",
            expected_entities=[("bug", "PROBLEM", 24, 27)],
            confidence=0.8,
            source=LearningDataType.USER_FEEDBACK
        ),
        TrainingExample(
            text="What's the best API design pattern?",
            expected_intent="technical_question",
            expected_sentiment="neutral",
            expected_entities=[("API", "PRODUCT", 16, 19)],
            confidence=0.9,
            source=LearningDataType.CONVERSATION
        )
    ]
    
    # Validate model
    validation_result = await learner.validator.validate_model(validation_examples)
    
    logger.info("Validation Results:")
    logger.info(f"  Overall accuracy: {validation_result.accuracy:.3f}")
    logger.info(f"  Intent accuracy: {validation_result.intent_accuracy:.3f}")
    logger.info(f"  Sentiment accuracy: {validation_result.sentiment_accuracy:.3f}")
    logger.info(f"  Entity accuracy: {validation_result.entity_accuracy:.3f}")
    logger.info(f"  F1 score: {validation_result.f1_score:.3f}")
    logger.info(f"  Passed threshold: {validation_result.passed_threshold}")
    logger.info(f"  Validation examples: {validation_result.validation_examples}")
    
    if validation_result.errors:
        logger.info(f"  Errors found: {len(validation_result.errors)}")
        for i, error in enumerate(validation_result.errors[:2]):  # Show first 2 errors
            logger.info(f"    Error {i+1}: {error}")
    
    return validation_result


async def demo_complete_learning_cycle():
    """Demo complete autonomous learning cycle."""
    logger.info("\n=== Demo: Complete Learning Cycle ===")
    
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    # Create temporary directory for model backups
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        learner = AutonomousLearner(
            spacy_analyzer=spacy_analyzer,
            memory_service=memory_service,
            spacy_service=spacy_analyzer.spacy_service,
            model_backup_dir=Path(tmp_dir)
        )
        
        # Override learning config for demo
        learner.learning_config["min_data_threshold"] = 3  # Lower threshold for demo
        
        tenant_id = "demo_tenant"
        
        # Trigger learning cycle
        logger.info("Triggering autonomous learning cycle...")
        result = await learner.trigger_learning_cycle(tenant_id, force_training=True)
        
        logger.info("Learning Cycle Results:")
        logger.info(f"  Cycle ID: {result.cycle_id}")
        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Data collected: {result.data_collected}")
        logger.info(f"  Examples created: {result.examples_created}")
        logger.info(f"  Training time: {result.training_time:.2f}s" if result.training_time else "  Training time: N/A")
        logger.info(f"  Model improved: {result.model_improved}")
        logger.info(f"  Rollback performed: {result.rollback_performed}")
        
        if result.validation_result:
            logger.info(f"  Validation accuracy: {result.validation_result.accuracy:.3f}")
            logger.info(f"  Validation passed: {result.validation_result.passed_threshold}")
        
        if result.error_message:
            logger.info(f"  Error: {result.error_message}")
        
        return result


async def demo_learning_metrics():
    """Demo learning metrics and history."""
    logger.info("\n=== Demo: Learning Metrics ===")
    
    spacy_analyzer = MockSpacyAnalyzer()
    memory_service = MockMemoryService()
    
    learner = AutonomousLearner(
        spacy_analyzer=spacy_analyzer,
        memory_service=memory_service,
        spacy_service=spacy_analyzer.spacy_service
    )
    
    # Add some mock learning history
    from ai_karen_engine.core.response.autonomous_learner import LearningCycleResult, TrainingStatus
    
    mock_results = [
        LearningCycleResult(
            cycle_id="cycle_1",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=TrainingStatus.COMPLETED,
            data_collected=100,
            examples_created=80,
            training_time=45.5,
            model_improved=True
        ),
        LearningCycleResult(
            cycle_id="cycle_2",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=TrainingStatus.ROLLED_BACK,
            data_collected=75,
            examples_created=60,
            training_time=38.2,
            model_improved=False,
            rollback_performed=True
        ),
        LearningCycleResult(
            cycle_id="cycle_3",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=TrainingStatus.COMPLETED,
            data_collected=120,
            examples_created=95,
            training_time=52.1,
            model_improved=True
        )
    ]
    
    learner.learning_history = mock_results
    
    # Get learning metrics
    metrics = await learner.get_learning_metrics()
    
    logger.info("Learning Metrics:")
    logger.info(f"  Total cycles: {metrics['total_cycles']}")
    logger.info(f"  Successful cycles: {metrics['successful_cycles']}")
    logger.info(f"  Failed cycles: {metrics['failed_cycles']}")
    logger.info(f"  Model improvements: {metrics['model_improvements']}")
    logger.info(f"  Average training time: {metrics['average_training_time']:.1f}s")
    
    if metrics['last_cycle']:
        last_cycle = metrics['last_cycle']
        logger.info(f"  Last cycle: {last_cycle['cycle_id']} ({last_cycle['status']})")
    
    logger.info("Recent cycles:")
    for cycle in metrics['recent_cycles']:
        logger.info(f"    {cycle['cycle_id']}: {cycle['status']} "
                   f"(improved: {cycle['model_improved']})")
    
    return metrics


async def main():
    """Run all demos."""
    logger.info("Starting Autonomous Learning Engine Demo")
    logger.info("=" * 50)
    
    try:
        # Run all demo functions
        await demo_conversation_metadata_collection()
        await demo_training_data_curation()
        await demo_incremental_training()
        await demo_model_validation()
        await demo_complete_learning_cycle()
        await demo_learning_metrics()
        
        logger.info("\n" + "=" * 50)
        logger.info("Demo completed successfully!")
        logger.info("\nKey Features Demonstrated:")
        logger.info("✓ Conversation metadata collection and curation")
        logger.info("✓ Training data creation from user interactions")
        logger.info("✓ Incremental spaCy model training")
        logger.info("✓ Model validation and quality assessment")
        logger.info("✓ Complete autonomous learning cycles")
        logger.info("✓ Learning metrics and history tracking")
        logger.info("✓ Model backup and rollback capabilities")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())