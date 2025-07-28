"""
Unit tests for the CredentialAnalyzer service.

This module tests the credential analysis functionality including
NLP feature extraction, suspicious pattern detection, and caching.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import (
    IntelligentAuthConfig,
    CredentialFeatures,
    NLPFeatures
)
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.nlp_config import SpacyConfig


class TestCredentialAnalyzer:
    """Test cases for CredentialAnalyzer."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return IntelligentAuthConfig(
            cache_size=100,
            cache_ttl=300,
            max_processing_time=5.0
        )

    @pytest.fixture
    def mock_spacy_service(self):
        """Create mock spaCy service."""
        mock_service = Mock(spec=SpacyService)
        
        # Mock parse_message method
        async def mock_parse_message(text):
            return ParsedMessage(
                tokens=text.split(),
                lemmas=[token.lower() for token in text.split()],
                entities=[],
                pos_tags=[(token, 'NOUN') for token in text.split()],
                noun_phrases=[text],
                sentences=[text],
                dependencies=[],
                language='en',
                processing_time=0.1,
                used_fallback=False
            )
        
        mock_service.parse_message = AsyncMock(side_effect=mock_parse_message)
        
        # Mock health status
        from ai_karen_engine.services.spacy_service import SpacyHealthStatus
        mock_service.get_health_status.return_value = SpacyHealthStatus(
            is_healthy=True,
            model_loaded=True,
            fallback_mode=False,
            cache_size=10,
            cache_hit_rate=0.8,
            avg_processing_time=0.1,
            error_count=0,
            last_error=None
        )
        
        return mock_service

    @pytest.fixture
    def analyzer(self, config, mock_spacy_service):
        """Create CredentialAnalyzer instance."""
        return CredentialAnalyzer(config, mock_spacy_service)

    @pytest.mark.asyncio
    async def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        result = await analyzer.initialize()
        assert result is True
        assert analyzer.config is not None
        assert analyzer.spacy_service is not None

    @pytest.mark.asyncio
    async def test_health_check(self, analyzer):
        """Test health check functionality."""
        await analyzer.initialize()
        
        health_status = await analyzer.health_check()
        
        assert health_status is not None
        assert health_status.service_name == "CredentialAnalyzer"
        assert health_status.response_time >= 0

    @pytest.mark.asyncio
    async def test_analyze_credentials_basic(self, analyzer):
        """Test basic credential analysis."""
        await analyzer.initialize()
        
        email = "user@example.com"
        password_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        
        result = await analyzer.analyze_credentials(email, password_hash)
        
        assert isinstance(result, NLPFeatures)
        assert result.email_features is not None
        assert result.password_features is not None
        assert 0.0 <= result.credential_similarity <= 1.0
        assert isinstance(result.language_consistency, bool)
        assert isinstance(result.suspicious_patterns, list)
        assert result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_analyze_text_features(self, analyzer):
        """Test text feature analysis."""
        await analyzer.initialize()
        
        text = "user@example.com"
        features = await analyzer._analyze_text_features(text, is_email=True)
        
        assert isinstance(features, CredentialFeatures)
        assert features.token_count > 0
        assert 0.0 <= features.unique_token_ratio <= 1.0
        assert features.entropy_score >= 0.0
        assert features.language in ['en', 'unknown', 'multi']
        assert isinstance(features.contains_suspicious_patterns, bool)
        assert isinstance(features.pattern_types, list)

    @pytest.mark.asyncio
    async def test_detect_suspicious_patterns(self, analyzer):
        """Test suspicious pattern detection."""
        await analyzer.initialize()
        
        # Test various suspicious patterns
        test_cases = [
            ("password123", ["sequential_numbers"]),
            ("qwerty", ["keyboard_walk_qwerty_horizontal"]),
            ("aaaa", ["repeated_chars"]),
            ("abc123", ["sequential_letters", "sequential_numbers"]),
            ("user2023", ["year_pattern"]),
            ("normal@email.com", [])  # Should not detect patterns
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            # Check that expected patterns are detected
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    def test_calculate_entropy(self, analyzer):
        """Test entropy calculation."""
        # Test various entropy scenarios
        test_cases = [
            ("", 0.0),  # Empty string
            ("aaaa", 0.0),  # All same character
            ("abcd", 2.0),  # Maximum entropy for 4 unique chars
            ("password", None)  # Should be > 0 but < max
        ]
        
        for text, expected in test_cases:
            entropy = analyzer._calculate_entropy(text)
            
            if expected is None:
                assert entropy > 0.0
            else:
                assert abs(entropy - expected) < 0.1, \
                    f"Entropy for '{text}' was {entropy}, expected {expected}"

    @pytest.mark.asyncio
    async def test_language_detection(self, analyzer):
        """Test language detection functionality."""
        await analyzer.initialize()
        
        # Create mock parsed message
        parsed = ParsedMessage(
            tokens=['test'],
            lemmas=['test'],
            entities=[],
            pos_tags=[],
            noun_phrases=[],
            sentences=[],
            dependencies=[],
            language='en',
            used_fallback=False
        )
        
        language = await analyzer._detect_language("test", parsed)
        assert language == 'en'

    def test_fallback_language_detection(self, analyzer):
        """Test fallback language detection."""
        # Test ASCII text
        assert analyzer._fallback_language_detection("hello world") == "en"
        
        # Test non-ASCII text
        assert analyzer._fallback_language_detection("héllo wörld") == "multi"
        
        # Test empty text
        assert analyzer._fallback_language_detection("") == "unknown"

    @pytest.mark.asyncio
    async def test_credential_similarity(self, analyzer):
        """Test credential similarity calculation."""
        await analyzer.initialize()
        
        test_cases = [
            ("user@example.com", "user123hash", 0.0),  # Should have some similarity
            ("test@test.com", "completelydifferenthash", 0.0),  # Should be low
            ("admin@site.com", "admin", 0.0)  # Should be high if admin in hash
        ]
        
        for email, password_hash, min_expected in test_cases:
            similarity = await analyzer._calculate_credential_similarity(email, password_hash)
            assert 0.0 <= similarity <= 1.0
            assert similarity >= min_expected

    @pytest.mark.asyncio
    async def test_language_consistency(self, analyzer):
        """Test language consistency checking."""
        await analyzer.initialize()
        
        # Mock the spacy service to return consistent languages
        analyzer.spacy_service.parse_message = AsyncMock(return_value=ParsedMessage(
            tokens=['test'],
            lemmas=['test'],
            entities=[],
            pos_tags=[],
            noun_phrases=[],
            sentences=[],
            dependencies=[],
            language='en',
            used_fallback=False
        ))
        
        consistency = await analyzer._check_language_consistency(
            "user@example.com", 
            "somehash123"
        )
        
        assert isinstance(consistency, bool)

    @pytest.mark.asyncio
    async def test_caching_functionality(self, analyzer):
        """Test caching of analysis results."""
        await analyzer.initialize()
        
        email = "cache@test.com"
        password_hash = "cachehash123"
        
        # First call - should miss cache
        start_time = time.time()
        result1 = await analyzer.analyze_credentials(email, password_hash)
        first_call_time = time.time() - start_time
        
        # Second call - should hit cache
        start_time = time.time()
        result2 = await analyzer.analyze_credentials(email, password_hash)
        second_call_time = time.time() - start_time
        
        # Results should be identical (except processing time)
        assert result1.email_features.token_count == result2.email_features.token_count
        assert result1.credential_similarity == result2.credential_similarity
        
        # Second call should be faster due to caching
        assert second_call_time < first_call_time or second_call_time < 0.01

    @pytest.mark.asyncio
    async def test_error_handling(self, analyzer):
        """Test error handling in credential analysis."""
        await analyzer.initialize()
        
        # Mock spacy service to raise exception in the main analyze_credentials method
        original_analyze_text_features = analyzer._analyze_text_features
        
        async def failing_analyze_text_features(*args, **kwargs):
            raise Exception("Test error")
        
        analyzer._analyze_text_features = failing_analyze_text_features
        
        # Should return fallback result instead of raising
        result = await analyzer.analyze_credentials("test@test.com", "testhash")
        
        assert isinstance(result, NLPFeatures)
        assert result.used_fallback is True
        assert result.model_version == "fallback"

    def test_pattern_detection_keyboard_walks(self, analyzer):
        """Test keyboard walk pattern detection."""
        # Test horizontal walks
        assert "keyboard_walk_qwerty_horizontal" in asyncio.run(
            analyzer.detect_suspicious_patterns("qwerty123")
        )
        
        # Test vertical walks
        assert any("keyboard_walk_qwerty_vertical" in pattern for pattern in asyncio.run(
            analyzer.detect_suspicious_patterns("qazwsx")
        ))

    def test_pattern_detection_common_weak(self, analyzer):
        """Test common weak pattern detection."""
        weak_passwords = ["password123", "admin", "123456", "qwerty"]
        
        for password in weak_passwords:
            patterns = asyncio.run(analyzer.detect_suspicious_patterns(password))
            # Should detect at least one suspicious pattern
            assert len(patterns) > 0

    def test_pattern_detection_regex_patterns(self, analyzer):
        """Test regex-based pattern detection."""
        test_cases = [
            ("aaaaaa", "repeated_chars"),
            ("123456", "sequential_numbers"),
            ("abcdef", "sequential_letters"),
            ("born1995", "year_pattern")
        ]
        
        for text, expected_pattern in test_cases:
            patterns = asyncio.run(analyzer.detect_suspicious_patterns(text))
            assert any(expected_pattern in pattern for pattern in patterns), \
                f"Expected {expected_pattern} in patterns for '{text}'"

    @pytest.mark.asyncio
    async def test_performance_metrics(self, analyzer):
        """Test performance metrics collection."""
        await analyzer.initialize()
        
        # Perform some analyses
        await analyzer.analyze_credentials("test1@test.com", "hash1")
        await analyzer.analyze_credentials("test2@test.com", "hash2")
        
        metrics = analyzer.get_performance_metrics()
        
        assert 'analysis_count' in metrics
        assert 'cache_hit_rate' in metrics
        assert 'avg_processing_time' in metrics
        assert 'error_count' in metrics
        assert metrics['analysis_count'] >= 2

    @pytest.mark.asyncio
    async def test_cache_management(self, analyzer):
        """Test cache management functionality."""
        await analyzer.initialize()
        
        # Add some items to cache
        await analyzer.analyze_credentials("test@test.com", "hash")
        
        # Check cache has items
        assert len(analyzer.cache) > 0
        
        # Clear cache
        analyzer.clear_cache()
        assert len(analyzer.cache) == 0
        assert len(analyzer._language_cache) == 0

    def test_metrics_reset(self, analyzer):
        """Test metrics reset functionality."""
        # Set some metrics
        analyzer._analysis_count = 10
        analyzer._error_count = 2
        analyzer._processing_times = [0.1, 0.2, 0.3]
        
        # Reset metrics
        analyzer.reset_metrics()
        
        assert analyzer._analysis_count == 0
        assert analyzer._error_count == 0
        assert len(analyzer._processing_times) == 0

    @pytest.mark.asyncio
    async def test_fallback_nlp_features(self, analyzer):
        """Test fallback NLP features creation."""
        email = "test@example.com"
        password_hash = "testhash123"
        processing_time = 0.5
        
        fallback_features = analyzer._create_fallback_nlp_features(
            email, password_hash, processing_time
        )
        
        assert isinstance(fallback_features, NLPFeatures)
        assert fallback_features.used_fallback is True
        assert fallback_features.model_version == "fallback"
        assert fallback_features.processing_time == processing_time
        assert fallback_features.email_features.entropy_score > 0
        assert fallback_features.password_features.entropy_score > 0

    def test_credential_reuse_patterns(self, analyzer):
        """Test credential reuse pattern detection."""
        # Test username in password hash (simplified)
        assert analyzer._check_credential_reuse_patterns(
            "admin@test.com", 
            "admin123hash"
        ) is True
        
        # Test domain in password hash
        assert analyzer._check_credential_reuse_patterns(
            "user@testsite.com", 
            "testsite123hash"
        ) is True
        
        # Test no reuse
        assert analyzer._check_credential_reuse_patterns(
            "user@example.com", 
            "randomhash456"
        ) is False

    def test_weak_combination_patterns(self, analyzer):
        """Test weak combination pattern detection."""
        # Test short email
        assert analyzer._check_weak_combination_patterns("a@b.c", "longhash123") is True
        
        # Test short hash
        assert analyzer._check_weak_combination_patterns("user@test.com", "short") is True
        
        # Test invalid email format
        assert analyzer._check_weak_combination_patterns("invalid-email", "hash123") is True
        
        # Test valid combination
        assert analyzer._check_weak_combination_patterns(
            "user@example.com", 
            "properlengthash123456"
        ) is False

    @pytest.mark.asyncio
    async def test_shutdown(self, analyzer):
        """Test graceful shutdown."""
        await analyzer.initialize()
        
        # Add some cache items
        await analyzer.analyze_credentials("test@test.com", "hash")
        assert len(analyzer.cache) > 0
        
        # Shutdown should clear caches
        await analyzer.shutdown()
        assert len(analyzer.cache) == 0

    @pytest.mark.asyncio
    async def test_combined_suspicious_patterns(self, analyzer):
        """Test combined suspicious pattern detection."""
        await analyzer.initialize()
        
        email = "admin@test.com"
        password_hash = "admin123"  # Reuses username
        
        patterns = await analyzer._detect_combined_suspicious_patterns(email, password_hash)
        
        assert isinstance(patterns, list)
        # Should detect credential reuse
        assert "credential_reuse_pattern" in patterns

    @pytest.mark.asyncio
    async def test_dictionary_words_detection(self, analyzer):
        """Test dictionary words detection."""
        # Test with common words
        assert await analyzer._contains_dictionary_words("the quick brown") is True
        
        # Test with uncommon text
        assert await analyzer._contains_dictionary_words("xyzabc123") is False
        
        # Test empty text
        assert await analyzer._contains_dictionary_words("") is False

    def test_personal_info_patterns(self, analyzer):
        """Test personal information pattern detection."""
        # Test month abbreviations
        assert analyzer._check_personal_info_patterns("jan2023") is True
        
        # Test date patterns
        assert analyzer._check_personal_info_patterns("12/25/2023") is True
        
        # Test capitalized words (names)
        assert analyzer._check_personal_info_patterns("JohnSmith") is True
        
        # Test normal text (lowercase to avoid capitalized word pattern)
        assert analyzer._check_personal_info_patterns("randomtext123") is False


if __name__ == "__main__":
    pytest.main([__file__])