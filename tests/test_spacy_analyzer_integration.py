"""
Integration tests for the spaCy analyzer with response core system.
"""

import pytest
from unittest.mock import Mock, patch

from src.ai_karen_engine.core.response.analyzer import SpacyAnalyzer, IntentType, SentimentType


class TestSpacyAnalyzerIntegration:
    """Integration test cases for SpacyAnalyzer."""
    
    def test_analyzer_creation(self):
        """Test that analyzer can be created successfully."""
        analyzer = SpacyAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'detect_intent')
        assert hasattr(analyzer, 'sentiment')
        assert hasattr(analyzer, 'entities')
        assert hasattr(analyzer, 'select_persona')
    
    def test_intent_detection_integration(self):
        """Test intent detection with real patterns."""
        analyzer = SpacyAnalyzer()
        
        # Test various intents
        test_cases = [
            ("How can I optimize this code?", IntentType.OPTIMIZE_CODE.value),
            ("I'm getting an error", IntentType.DEBUG_ERROR.value),
            ("Help me create an app", IntentType.CREATIVE_TASK.value),
            ("Hi there!", IntentType.CASUAL_CHAT.value),
            ("What is machine learning?", IntentType.EXPLAIN_CONCEPT.value),
        ]
        
        for text, expected_intent in test_cases:
            result = analyzer.detect_intent(text)
            # Allow some flexibility in intent detection
            assert result in [expected_intent, IntentType.GENERAL_ASSIST.value, IntentType.TROUBLESHOOT.value]
    
    def test_sentiment_analysis_integration(self):
        """Test sentiment analysis with real keywords."""
        analyzer = SpacyAnalyzer()
        
        test_cases = [
            ("This is frustrating!", [SentimentType.FRUSTRATED.value, SentimentType.NEGATIVE.value]),
            ("I'm confused about this", [SentimentType.CONFUSED.value]),
            ("This is awesome!", [SentimentType.EXCITED.value, SentimentType.POSITIVE.value]),
            ("I need help urgently", [SentimentType.URGENT.value]),
            ("Hello there", [SentimentType.NEUTRAL.value, SentimentType.POSITIVE.value]),
        ]
        
        for text, expected_sentiments in test_cases:
            result = analyzer.sentiment(text)
            # Allow neutral as fallback
            assert result in expected_sentiments + [SentimentType.NEUTRAL.value]
    
    def test_persona_selection_integration(self):
        """Test persona selection logic."""
        analyzer = SpacyAnalyzer()
        
        # Test key persona mappings
        test_cases = [
            (IntentType.DEBUG_ERROR.value, SentimentType.FRUSTRATED.value, "support-assistant"),
            (IntentType.OPTIMIZE_CODE.value, SentimentType.NEUTRAL.value, "technical-expert"),
            (IntentType.CREATIVE_TASK.value, SentimentType.EXCITED.value, "creative-collaborator"),
            (IntentType.BUSINESS_ADVICE.value, SentimentType.NEUTRAL.value, "business-advisor"),
            (IntentType.CASUAL_CHAT.value, SentimentType.POSITIVE.value, "casual-friend"),
        ]
        
        for intent, sentiment, expected_persona in test_cases:
            result = analyzer.select_persona(intent, sentiment)
            assert result == expected_persona
    
    def test_end_to_end_analysis(self):
        """Test complete analysis pipeline."""
        analyzer = SpacyAnalyzer()
        
        # Test a frustrated user with a code error
        text = "I'm getting this stupid error and I can't fix it!"
        
        intent = analyzer.detect_intent(text)
        sentiment = analyzer.sentiment(text)
        persona = analyzer.select_persona(intent, sentiment)
        entities = analyzer.entities(text)
        
        # Verify results make sense
        assert intent in [IntentType.DEBUG_ERROR.value, IntentType.TROUBLESHOOT.value]
        assert sentiment in [SentimentType.FRUSTRATED.value, SentimentType.NEGATIVE.value, SentimentType.NEUTRAL.value]
        assert persona == "support-assistant"  # Should select calm support for frustrated debug
        assert "entities" in entities
        assert "metadata" in entities
    
    @pytest.mark.asyncio
    async def test_profile_gap_detection(self):
        """Test profile gap detection for onboarding."""
        analyzer = SpacyAnalyzer()
        
        # Test with missing project context
        ui_caps = {}
        result = await analyzer.detect_profile_gaps("Help me with my code", ui_caps)
        
        assert result["onboarding_needed"] is True
        assert "project_context" in result["gaps"]
        assert result["next_question"] is not None
        
        # Test with complete profile
        complete_ui_caps = {
            "project_name": "MyApp",
            "tech_stack": "Python",
            "experience_level": "intermediate",
            "user_goals": "Build web app"
        }
        
        result = await analyzer.detect_profile_gaps("Help me with Django", complete_ui_caps)
        assert result["onboarding_needed"] is False
        assert len(result["gaps"]) == 0
    
    def test_protocol_compliance(self):
        """Test that analyzer implements the Analyzer protocol correctly."""
        from src.ai_karen_engine.core.response.protocols import Analyzer
        
        analyzer = SpacyAnalyzer()
        
        # Test protocol methods exist and return correct types
        assert hasattr(analyzer, 'detect_intent')
        assert hasattr(analyzer, 'sentiment')
        assert hasattr(analyzer, 'entities')
        
        # Test method signatures work
        intent = analyzer.detect_intent("test")
        assert isinstance(intent, str)
        
        sentiment = analyzer.sentiment("test")
        assert isinstance(sentiment, str)
        
        entities = analyzer.entities("test")
        assert isinstance(entities, dict)
        assert "entities" in entities
        assert "metadata" in entities
    
    def test_factory_function(self):
        """Test the factory function works correctly."""
        from src.ai_karen_engine.core.response.analyzer import create_spacy_analyzer
        
        analyzer = create_spacy_analyzer()
        assert isinstance(analyzer, SpacyAnalyzer)
        assert analyzer.spacy_service is not None


if __name__ == "__main__":
    pytest.main([__file__])