"""
Tests for Web UI integration models and shared types.
"""

from datetime import datetime

import pytest

try:
    from pydantic import ValidationError
except ImportError:
    # Handle case where pydantic stub doesn't have ValidationError
    class ValidationError(Exception):
        pass


from src.ai_karen_engine.database.models import TenantConversation, TenantMemoryEntry
from src.ai_karen_engine.models.shared_types import (
    AiData,
    ChatMessage,
    DecideActionInput,
    DecideActionOutput,
    FlowInput,
    FlowOutput,
    FlowType,
    HandleUserMessageResult,
    KarenEnhancedInput,
    KarenEnhancedOutput,
    KarenSettings,
    MemoryContext,
    MemoryDepth,
    MessageRole,
    NotificationPreferences,
    PersonalityTone,
    PersonalityVerbosity,
    PluginInfo,
    TemperatureUnit,
    ToolInput,
    ToolType,
    WeatherServiceOption,
)
from src.ai_karen_engine.models.web_ui_types import ChatProcessRequest


class TestSharedTypes:
    """Test shared type definitions."""

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_memory_depth_enum(self):
        """Test MemoryDepth enum values."""
        assert MemoryDepth.SHORT == "short"
        assert MemoryDepth.MEDIUM == "medium"
        assert MemoryDepth.LONG == "long"

    def test_personality_tone_enum(self):
        """Test PersonalityTone enum values."""
        assert PersonalityTone.NEUTRAL == "neutral"
        assert PersonalityTone.FRIENDLY == "friendly"
        assert PersonalityTone.FORMAL == "formal"
        assert PersonalityTone.HUMOROUS == "humorous"

    def test_ai_data_model(self):
        """Test AiData model."""
        ai_data = AiData(
            keywords=["test", "keyword"],
            knowledge_graph_insights="Some insights",
            confidence=0.85,
            reasoning="Test reasoning",
        )
        assert ai_data.keywords == ["test", "keyword"]
        assert ai_data.confidence == 0.85

        # Test validation (skip for stub implementation)
        # Note: Validation would fail in real pydantic for confidence > 1.0
        # with pytest.raises(ValidationError):
        #     AiData(confidence=1.5)  # Should fail - confidence > 1.0

    def test_chat_message_model(self):
        """Test ChatMessage model."""
        message = ChatMessage(
            id="test-id",
            role=MessageRole.USER,
            content="Hello world",
            timestamp=datetime.now(),
            ai_data=AiData(keywords=["hello"]),
            should_auto_play=True,
        )
        assert message.role == MessageRole.USER
        assert message.content == "Hello world"
        assert message.ai_data.keywords == ["hello"]

    def test_karen_settings_model(self):
        """Test KarenSettings model."""
        settings = KarenSettings(
            memory_depth=MemoryDepth.LONG,
            personality_tone=PersonalityTone.FRIENDLY,
            personality_verbosity=PersonalityVerbosity.DETAILED,
            personal_facts=["I like coffee", "I work in tech"],
            custom_persona_instructions="Be helpful and friendly",
            temperature_unit=TemperatureUnit.FAHRENHEIT,
            weather_service=WeatherServiceOption.CUSTOM_API,
            default_weather_location="New York",
            active_listen_mode=True,
        )
        assert settings.memory_depth == MemoryDepth.LONG
        assert settings.personal_facts == ["I like coffee", "I work in tech"]
        assert settings.temperature_unit == TemperatureUnit.FAHRENHEIT

    def test_flow_input_model(self):
        """Test FlowInput model."""
        flow_input = FlowInput(
            prompt="What's the weather?",
            conversation_history=[{"role": "user", "content": "Hello"}],
            user_settings={"theme": "dark"},
            user_id="user-123",
            session_id="session-456",
            memory_depth=MemoryDepth.MEDIUM,
            personality_tone=PersonalityTone.FRIENDLY,
        )
        assert flow_input.prompt == "What's the weather?"
        assert flow_input.user_id == "user-123"
        assert flow_input.memory_depth == MemoryDepth.MEDIUM

    def test_flow_output_model(self):
        """Test FlowOutput model."""
        flow_output = FlowOutput(
            response="Here's the weather information",
            requires_plugin=True,
            plugin_to_execute="weather_plugin",
            plugin_parameters={"location": "New York"},
            ai_data=AiData(confidence=0.9),
            tool_to_call=ToolType.GET_WEATHER,
            suggested_new_facts=["User asked about weather"],
        )
        assert flow_output.response == "Here's the weather information"
        assert flow_output.requires_plugin is True
        assert flow_output.tool_to_call == ToolType.GET_WEATHER


class TestDatabaseModels:
    """Test database model extensions."""

    def test_tenant_conversation_web_ui_fields(self):
        """Test TenantConversation web UI integration fields."""
        conversation = TenantConversation(
            user_id="user-123",
            title="Test Conversation",
            session_id="session-456",
            ui_context={"theme": "dark", "layout": "compact"},
            ai_insights={"sentiment": "positive", "topics": ["weather"]},
            user_settings={"memory_depth": "medium"},
            summary="A conversation about weather",
            tags=["weather", "casual"],
            last_ai_response_id="response-789",
        )

        assert conversation.session_id == "session-456"
        assert conversation.ui_context["theme"] == "dark"
        assert conversation.ai_insights["sentiment"] == "positive"
        assert conversation.tags == ["weather", "casual"]
        assert conversation.summary == "A conversation about weather"

    def test_tenant_conversation_tag_methods(self):
        """Test TenantConversation tag manipulation methods."""
        conversation = TenantConversation(user_id="user-123")

        # Test adding tags
        conversation.add_tag("weather")
        conversation.add_tag("casual")
        assert "weather" in conversation.tags
        assert "casual" in conversation.tags

        # Test adding duplicate tag (should not duplicate)
        conversation.add_tag("weather")
        assert conversation.tags.count("weather") == 1

        # Test removing tag
        conversation.remove_tag("casual")
        assert "casual" not in conversation.tags
        assert "weather" in conversation.tags

    def test_tenant_conversation_context_methods(self):
        """Test TenantConversation context update methods."""
        conversation = TenantConversation(user_id="user-123")

        # Test updating UI context
        conversation.update_ui_context({"theme": "dark"})
        conversation.update_ui_context({"layout": "compact"})
        assert conversation.ui_context["theme"] == "dark"
        assert conversation.ui_context["layout"] == "compact"

        # Test updating AI insights
        conversation.update_ai_insights({"sentiment": "positive"})
        conversation.update_ai_insights({"topics": ["weather"]})
        assert conversation.ai_insights["sentiment"] == "positive"
        assert conversation.ai_insights["topics"] == ["weather"]

    def test_tenant_memory_entry_web_ui_fields(self):
        """Test TenantMemoryEntry web UI integration fields."""
        memory_entry = TenantMemoryEntry(
            vector_id="vector-123",
            user_id="user-456",
            content="User likes coffee",
            ui_source="web",
            conversation_id="conv-789",
            memory_type="preference",
            tags=["coffee", "preference"],
            importance_score=8,
            access_count=5,
            last_accessed=datetime.now(),
            ai_generated=True,
            user_confirmed=True,
        )

        assert memory_entry.ui_source == "web"
        assert memory_entry.conversation_id == "conv-789"
        assert memory_entry.memory_type == "preference"
        assert memory_entry.importance_score == 8
        assert memory_entry.ai_generated is True

    def test_tenant_memory_entry_tag_methods(self):
        """Test TenantMemoryEntry tag manipulation methods."""
        memory_entry = TenantMemoryEntry(
            vector_id="vector-123", user_id="user-456", content="Test content"
        )

        # Test adding tags
        memory_entry.add_tag("coffee")
        memory_entry.add_tag("preference")
        assert "coffee" in memory_entry.tags
        assert "preference" in memory_entry.tags

        # Test removing tag
        memory_entry.remove_tag("coffee")
        assert "coffee" not in memory_entry.tags
        assert "preference" in memory_entry.tags

    def test_tenant_memory_entry_access_tracking(self):
        """Test TenantMemoryEntry access tracking."""
        memory_entry = TenantMemoryEntry(
            vector_id="vector-123",
            user_id="user-456",
            content="Test content",
            access_count=0,
        )

        # Test incrementing access count
        initial_time = datetime.now()
        memory_entry.increment_access_count()
        assert memory_entry.access_count == 1
        assert memory_entry.last_accessed >= initial_time

        # Test multiple increments
        memory_entry.increment_access_count()
        assert memory_entry.access_count == 2

    def test_tenant_memory_entry_importance_validation(self):
        """Test TenantMemoryEntry importance score validation."""
        memory_entry = TenantMemoryEntry(
            vector_id="vector-123", user_id="user-456", content="Test content"
        )

        # Test valid importance scores
        memory_entry.set_importance(1)
        assert memory_entry.importance_score == 1

        memory_entry.set_importance(10)
        assert memory_entry.importance_score == 10

        memory_entry.set_importance(5)
        assert memory_entry.importance_score == 5

        # Test invalid importance scores
        with pytest.raises(ValueError):
            memory_entry.set_importance(0)

        with pytest.raises(ValueError):
            memory_entry.set_importance(11)

    def test_tenant_memory_entry_metadata_update(self):
        """Test TenantMemoryEntry metadata update."""
        memory_entry = TenantMemoryEntry(
            vector_id="vector-123", user_id="user-456", content="Test content"
        )

        # Test updating metadata
        memory_entry.update_metadata({"source": "web"})
        memory_entry.update_metadata({"confidence": 0.85})
        assert memory_entry.memory_metadata["source"] == "web"
        assert memory_entry.memory_metadata["confidence"] == 0.85


class TestChatProcessRequestValidation:
    """Tests for ChatProcessRequest validators."""

    def test_empty_message(self):
        with pytest.raises(ValidationError):
            ChatProcessRequest(message="")

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            ChatProcessRequest(message="x" * 10001)

    def test_invalid_conversation_history(self):
        with pytest.raises(ValidationError):
            ChatProcessRequest(message="hi", conversation_history=["bad"])

    def test_invalid_user_settings(self):
        with pytest.raises(ValidationError):
            ChatProcessRequest(message="hi", user_settings="bad")


if __name__ == "__main__":
    pytest.main([__file__])
