#!/usr/bin/env python3
"""
Simple test runner for response formatting system.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def run_basic_tests():
    """Run basic functionality tests."""
    print("🧪 Testing Response Formatting System")
    print("=" * 50)
    
    try:
        # Test imports
        print("Testing imports...")
        from base import (
            ResponseFormatter, FormattedResponse, ResponseContext, 
            ContentType, DefaultResponseFormatter, FormattingError
        )
        from registry import ResponseFormatterRegistry, get_formatter_registry
        from content_detector import ContentTypeDetector, ContentDetectionResult
        from integration import ResponseFormattingIntegration
        print("✅ All imports successful")
        
        # Test basic functionality
        print("\nTesting basic functionality...")
        
        # Test DefaultResponseFormatter
        formatter = DefaultResponseFormatter()
        context = ResponseContext(
            user_query="test query",
            response_content="test response",
            user_preferences={},
            theme_context={},
            session_data={}
        )
        
        assert formatter.can_format("Valid content", context) == True
        assert formatter.can_format("", context) == False
        
        result = formatter.format_response("Test content", context)
        assert isinstance(result, FormattedResponse)
        assert result.content_type == ContentType.DEFAULT
        assert "Test content" in result.content
        print("✅ DefaultResponseFormatter working")
        
        # Test Registry
        registry = ResponseFormatterRegistry()
        assert len(registry._formatters) == 1  # Default formatter
        
        class TestFormatter(ResponseFormatter):
            def can_format(self, content, context):
                return True
            def format_response(self, content, context):
                return FormattedResponse(
                    content=content, content_type=ContentType.DEFAULT,
                    theme_requirements=[], metadata={}, css_classes=[]
                )
            def get_theme_requirements(self):
                return []
        
        test_formatter = TestFormatter("test", "1.0.0")
        registry.register_formatter(test_formatter)
        assert len(registry._formatters) == 2
        print("✅ Registry working")
        
        # Test ContentTypeDetector
        detector = ContentTypeDetector()
        supported_types = detector.get_supported_content_types()
        assert ContentType.MOVIE in supported_types
        assert ContentType.RECIPE in supported_types
        print("✅ ContentTypeDetector working")
        
        # Test Integration
        integration = ResponseFormattingIntegration()
        formatters = integration.get_available_formatters()
        assert len(formatters) >= 1
        print("✅ Integration working")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)