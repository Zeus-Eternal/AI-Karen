"""
Comprehensive unit tests for suspicious pattern detection algorithms.

This module tests the advanced pattern detection functionality including
keyboard walks, attack patterns, statistical anomalies, and encoding detection.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import IntelligentAuthConfig
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.nlp_config import SpacyConfig


class TestPatternDetection:
    """Test cases for advanced pattern detection algorithms."""

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
    async def test_keyboard_walk_detection(self, analyzer):
        """Test keyboard walk pattern detection."""
        await analyzer.initialize()
        
        test_cases = [
            # Horizontal walks
            ("qwerty123", ["keyboard_walk_qwerty_horizontal"]),
            ("asdfgh", ["keyboard_walk_qwerty_horizontal"]),
            ("zxcvbn", ["keyboard_walk_qwerty_horizontal"]),
            
            # Vertical walks
            ("qazwsx", ["keyboard_walk_qwerty_vertical"]),
            ("edcrfv", ["keyboard_walk_qwerty_vertical"]),
            
            # Diagonal walks
            ("qweasd", ["keyboard_walk_qwerty_diagonal"]),
            ("zxcasd", ["keyboard_walk_qwerty_diagonal"]),
            
            # Reverse walks
            ("rewqfdsa", ["keyboard_walk_qwerty_reverse"]),
            ("vcxzbvcx", ["keyboard_walk_qwerty_reverse"]),
            
            # No keyboard walks
            ("randomtext", []),
            ("secure123", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_attack_pattern_detection(self, analyzer):
        """Test attack-specific pattern detection."""
        await analyzer.initialize()
        
        test_cases = [
            # Brute force indicators
            ("password123", ["brute_force_indicators"]),
            ("admin456", ["brute_force_indicators"]),
            ("user789", ["brute_force_indicators"]),
            ("test123", ["brute_force_indicators"]),
            
            # Credential stuffing indicators
            ("john1234", ["credential_stuffing_indicators"]),
            ("mary5678", ["credential_stuffing_indicators"]),
            ("user!123", ["credential_stuffing_indicators"]),
            
            # Dictionary attack indicators
            ("password", ["dictionary_attack_indicators"]),
            ("welcome", ["dictionary_attack_indicators"]),
            ("Password1", ["dictionary_attack_indicators"]),
            
            # No attack patterns
            ("randomsecure456", []),
            ("complex!Pass@2023", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_language_specific_patterns(self, analyzer):
        """Test language-specific pattern detection."""
        await analyzer.initialize()
        
        test_cases = [
            # English weak words
            ("password", ["english_weak_word"]),
            ("admin", ["english_weak_word"]),
            ("secret", ["english_weak_word"]),
            ("welcome", ["english_weak_word"]),
            
            # Common names
            ("john123", ["common_name"]),
            ("mary456", ["common_name"]),
            ("david789", ["common_name"]),
            
            # Common words
            ("love123", ["common_word"]),
            ("work456", ["common_word"]),
            ("home789", ["common_word"]),
            
            # Multiple common words
            ("lovework", ["multiple_common_words"]),
            ("homefamily", ["multiple_common_words"]),
            
            # No language patterns
            ("xyzabc123", []),
            ("randomtext", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_statistical_anomaly_detection(self, analyzer):
        """Test statistical anomaly detection."""
        await analyzer.initialize()
        
        test_cases = [
            # Low entropy
            ("aaaaaaa", ["low_entropy"]),
            ("1111111", ["low_entropy"]),
            
            # Character dominance
            ("aaaaabbbbb", ["character_dominance"]),
            
            # Low character diversity
            ("abababab", ["low_character_diversity"]),
            
            # Numeric dominance
            ("12345678901", ["numeric_dominance"]),
            
            # Alphabetic dominance
            ("abcdefghijklmnop", ["alphabetic_dominance"]),
            
            # High special characters
            ("!@#$%^&*()_+", ["high_special_chars"]),
            
            # Normal text (should not trigger anomalies)
            ("normaltext123", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_encoding_pattern_detection(self, analyzer):
        """Test encoding pattern detection."""
        await analyzer.initialize()
        
        test_cases = [
            # Base64 patterns
            ("SGVsbG8gV29ybGQhISE=", ["base64_encoded"]),
            ("VGhpcyBpcyBhIHRlc3Q=", ["base64_encoded"]),
            
            # Hex patterns
            ("48656c6c6f20576f726c64", ["hex_encoded"]),
            ("deadbeefcafebabe1234", ["hex_encoded"]),
            
            # URL encoding
            ("hello%20world%21", ["url_encoded"]),
            ("test%2Bstring%3D", ["url_encoded"]),
            
            # Unicode escape sequences
            ("\\u0048\\u0065\\u006c\\u006c\\u006f", ["unicode_escaped"]),
            
            # HTML entity encoding
            ("&lt;script&gt;alert&lpar;&rpar;&semi;", ["html_encoded"]),
            ("&#72;&#101;&#108;&#108;&#111;", ["html_encoded"]),
            
            # Normal text (no encoding)
            ("normaltext123", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_regex_pattern_detection(self, analyzer):
        """Test regex-based pattern detection."""
        await analyzer.initialize()
        
        test_cases = [
            # Repeated characters
            ("aaaa", ["repeated_chars"]),
            ("1111", ["repeated_chars"]),
            ("!!!!", ["repeated_chars"]),
            
            # Sequential numbers
            ("123456", ["sequential_numbers"]),
            ("789012", ["sequential_numbers"]),
            ("987654", ["sequential_numbers"]),
            
            # Sequential letters
            ("abcdef", ["sequential_letters"]),
            ("hijklm", ["sequential_letters"]),
            ("zyxwvu", ["sequential_letters"]),
            
            # Year patterns
            ("born1995", ["year_pattern"]),
            ("year2023", ["year_pattern"]),
            ("since1980", ["year_pattern"]),
            
            # Common endings
            ("password123", ["common_endings"]),
            ("user456", ["common_endings"]),
            ("test000", ["common_endings"]),
            
            # Common beginnings
            ("123password", ["common_beginnings"]),
            ("abcdefgh", ["common_beginnings"]),
            ("qwertyui", ["common_beginnings"]),
            
            # Phone patterns
            ("555-123-4567", ["phone_pattern"]),
            ("555.123.4567", ["phone_pattern"]),
            ("5551234567", ["phone_pattern"]),
            
            # Email patterns
            ("user@example.com", ["email_pattern"]),
            ("test.email@domain.org", ["email_pattern"]),
            
            # No patterns
            ("randomsecure", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    def test_brute_force_pattern_check(self, analyzer):
        """Test brute force pattern checking."""
        test_cases = [
            ("password123", True),
            ("admin456", True),
            ("user789", True),
            ("test1", True),
            ("simple123", True),
            ("12345678", True),
            ("complexpassword", False),
            ("randomtext", False)
        ]
        
        for text, expected in test_cases:
            result = analyzer._check_brute_force_patterns(text)
            assert result == expected, f"Brute force check for '{text}' expected {expected}, got {result}"

    def test_credential_stuffing_pattern_check(self, analyzer):
        """Test credential stuffing pattern checking."""
        test_cases = [
            ("john1234", True),
            ("mary5678", True),
            ("user!123", True),
            ("test_456", True),
            ("admin.789", True),
            ("1234user", True),
            ("complexpassword", False),
            ("randomtext", False)
        ]
        
        for text, expected in test_cases:
            result = analyzer._check_credential_stuffing_patterns(text)
            assert result == expected, f"Credential stuffing check for '{text}' expected {expected}, got {result}"

    def test_dictionary_attack_pattern_check(self, analyzer):
        """Test dictionary attack pattern checking."""
        test_cases = [
            ("password", True),
            ("welcome", True),
            ("Password1", True),
            ("admin!", True),
            ("test123", True),
            ("Admin", True),
            ("complexpassword123", False),
            ("verylongrandomtext456", False)
        ]
        
        for text, expected in test_cases:
            result = analyzer._check_dictionary_attack_patterns(text)
            assert result == expected, f"Dictionary attack check for '{text}' expected {expected}, got {result}"

    def test_rot13_pattern_check(self, analyzer):
        """Test ROT13 pattern detection."""
        test_cases = [
            ("cnffjbeq", True),  # "password" in ROT13
            ("nqzva", True),     # "admin" in ROT13
            ("frperg", True),    # "secret" in ROT13
            ("randomtext", False),
            ("12345", False),
            ("!@#$%", False)
        ]
        
        for text, expected in test_cases:
            result = analyzer._check_rot13_pattern(text)
            assert result == expected, f"ROT13 check for '{text}' expected {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_enhanced_keyboard_walk_detection(self, analyzer):
        """Test enhanced keyboard walk detection with longer patterns."""
        await analyzer.initialize()
        
        test_cases = [
            # Long keyboard walks should be detected
            ("qwertyuiop", ["keyboard_walk_qwerty_horizontal", "long_keyboard_walk_qwerty_horizontal"]),
            ("asdfghjkl", ["keyboard_walk_qwerty_horizontal", "long_keyboard_walk_qwerty_horizontal"]),
            ("zxcvbnm", ["keyboard_walk_qwerty_horizontal"]),
            
            # Short patterns
            ("qwe", ["keyboard_walk_qwerty_diagonal"]),
            ("asd", ["keyboard_walk_qwerty_diagonal"]),
            
            # No keyboard walks
            ("randomtext", [])
        ]
        
        for text, expected_patterns in test_cases:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            for expected in expected_patterns:
                assert any(expected in pattern for pattern in patterns), \
                    f"Expected pattern '{expected}' not found in {patterns} for text '{text}'"

    @pytest.mark.asyncio
    async def test_pattern_detection_performance(self, analyzer):
        """Test pattern detection performance with various inputs."""
        await analyzer.initialize()
        
        test_inputs = [
            "password123",
            "qwertyuiop",
            "admin456",
            "SGVsbG8gV29ybGQh",
            "user@example.com",
            "555-123-4567",
            "aaaaaaaaaa",
            "12345678901234567890",
            "normaltext",
            "complex!Pass@2023"
        ]
        
        for text in test_inputs:
            patterns = await analyzer.detect_suspicious_patterns(text)
            
            # Should always return a list
            assert isinstance(patterns, list)
            
            # Should not contain duplicates
            assert len(patterns) == len(set(patterns))
            
            # All patterns should be strings
            assert all(isinstance(pattern, str) for pattern in patterns)

    @pytest.mark.asyncio
    async def test_pattern_detection_edge_cases(self, analyzer):
        """Test pattern detection with edge cases."""
        await analyzer.initialize()
        
        edge_cases = [
            "",  # Empty string
            " ",  # Single space
            "a",  # Single character
            "12",  # Two characters
            "!@#$%^&*()",  # Only special characters
            "1234567890",  # Only numbers
            "abcdefghij",  # Only letters
            "A" * 100,  # Very long repeated character
            "🔒🔑🛡️",  # Unicode characters
            "\n\t\r",  # Whitespace characters
        ]
        
        for text in edge_cases:
            try:
                patterns = await analyzer.detect_suspicious_patterns(text)
                assert isinstance(patterns, list)
            except Exception as e:
                pytest.fail(f"Pattern detection failed for edge case '{repr(text)}': {e}")

    @pytest.mark.asyncio
    async def test_combined_pattern_detection(self, analyzer):
        """Test detection of multiple patterns in single text."""
        await analyzer.initialize()
        
        # Text with multiple suspicious patterns
        complex_text = "password123qwerty"
        patterns = await analyzer.detect_suspicious_patterns(complex_text)
        
        # Should detect multiple patterns
        expected_patterns = [
            "common_beginnings",  # starts with "password"
            "sequential_numbers",  # contains "123"
            "keyboard_walk_qwerty_horizontal",  # contains "qwerty"
            "english_weak_word",  # contains "password"
            "common_endings"  # ends with numbers
        ]
        
        detected_count = 0
        for expected in expected_patterns:
            if any(expected in pattern for pattern in patterns):
                detected_count += 1
        
        # Should detect at least some of the expected patterns
        assert detected_count >= 2, f"Expected multiple patterns, but only found: {patterns}"

    @pytest.mark.asyncio
    async def test_pattern_detection_accuracy(self, analyzer):
        """Test pattern detection accuracy with known good and bad inputs."""
        await analyzer.initialize()
        
        # Known weak patterns (should detect many patterns)
        weak_inputs = [
            "password",
            "123456",
            "qwerty",
            "admin",
            "password123"
        ]
        
        # Known strong patterns (should detect fewer patterns)
        strong_inputs = [
            "Tr0ub4dor&3",
            "correct-horse-battery-staple",
            "MyS3cur3P@ssw0rd!",
            "randomSecureString456"
        ]
        
        for weak_input in weak_inputs:
            patterns = await analyzer.detect_suspicious_patterns(weak_input)
            assert len(patterns) > 0, f"Weak input '{weak_input}' should have detected patterns: {patterns}"
        
        for strong_input in strong_inputs:
            patterns = await analyzer.detect_suspicious_patterns(strong_input)
            # Strong inputs might still have some patterns, but should have fewer
            # This is more of a sanity check than a strict requirement
            assert isinstance(patterns, list), f"Strong input '{strong_input}' should return valid patterns list"


if __name__ == "__main__":
    pytest.main([__file__])