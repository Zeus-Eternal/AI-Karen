#!/usr/bin/env python3
"""
Simple integration test for movie formatter.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from integration import get_response_formatting_integration


async def test_movie_formatting():
    """Test movie formatting integration."""
    print("🎬 Testing Movie Formatter Integration")
    print("=" * 50)
    
    integration = get_response_formatting_integration()
    
    # Test movie content
    movie_query = "Tell me about the movie Inception"
    movie_response = """
    Movie: Inception (2010)
    Directed by Christopher Nolan
    Starring Leonardo DiCaprio, Marion Cotillard, Tom Hardy
    Genre: Sci-Fi, Thriller, Action
    IMDB Rating: 8.8/10
    Runtime: 148 minutes
    Plot: A thief who steals corporate secrets through dream-sharing technology 
    is given the inverse task of planting an idea into the mind of a C.E.O.
    """
    
    try:
        # Test content detection
        detection_result = await integration.detect_content_type(movie_query, movie_response)
        print(f"Detection Result: {detection_result.content_type.value}")
        print(f"Detection Confidence: {detection_result.confidence:.2f}")
        print(f"Detection Reasoning: {detection_result.reasoning}")
        
        result = await integration.format_response(
            user_query=movie_query,
            response_content=movie_response,
            theme_context={'current_theme': 'light'}
        )
        
        print("✅ Movie formatting successful!")
        print(f"Content Type: {result.content_type.value}")
        print(f"Formatter Used: {result.metadata.get('formatter', 'unknown')}")
        print(f"Movie Title: {result.metadata.get('movie_title', 'unknown')}")
        print(f"Has Images: {result.has_images}")
        print(f"CSS Classes: {', '.join(result.css_classes)}")
        print(f"Theme Requirements: {', '.join(result.theme_requirements)}")
        
        # Verify content contains expected elements
        assert "movie-card" in result.content
        assert "Inception" in result.content
        assert "Christopher Nolan" in result.content
        assert "Leonardo DiCaprio" in result.content
        assert "8.8" in result.content
        assert "style>" in result.content  # CSS included
        
        print("✅ All assertions passed!")
        
    except Exception as e:
        print(f"❌ Movie formatting failed: {e}")
        return False
    
    # Test non-movie content (should use default formatter)
    non_movie_query = "How do I cook pasta?"
    non_movie_response = "To cook pasta, boil water, add salt, then add pasta and cook for 8-10 minutes."
    
    try:
        result = await integration.format_response(
            user_query=non_movie_query,
            response_content=non_movie_response,
            theme_context={'current_theme': 'light'}
        )
        
        print("✅ Non-movie content handled correctly!")
        print(f"Content Type: {result.content_type.value}")
        print(f"Formatter Used: {result.metadata.get('formatter', 'unknown')}")
        
        # Should use default formatter
        assert result.content_type.value == "default"
        assert result.metadata.get('formatter') == 'default'
        
        print("✅ Default formatter used correctly!")
        
    except Exception as e:
        print(f"❌ Non-movie content handling failed: {e}")
        return False
    
    # Test metrics
    metrics = integration.get_integration_metrics()
    print(f"\n📊 Integration Metrics:")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Successful Formats: {metrics['successful_formats']}")
    print(f"Failed Formats: {metrics['failed_formats']}")
    print(f"Content Type Detections: {metrics['content_type_detections']}")
    
    return True


async def main():
    """Main test function."""
    success = await test_movie_formatting()
    
    if success:
        print("\n🎉 All movie formatter integration tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)