#!/usr/bin/env python3
"""
Integration test for news response formatter.

This script tests the news formatter integration with the response formatting system.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from integration import get_response_formatting_integration
from base import ContentType


async def test_news_formatting():
    """Test news response formatting integration."""
    print("Testing News Response Formatter Integration")
    print("=" * 50)
    
    # Get integration instance
    integration = get_response_formatting_integration()
    
    # Test news content
    test_cases = [
        {
            "query": "What's the latest news about technology?",
            "response": """
            Breaking News: Major AI Breakthrough Announced
            
            Source: Reuters
            Author: Sarah Johnson
            Published: March 15, 2024
            Category: Technology
            
            In a groundbreaking announcement today, researchers at TechCorp unveiled 
            their latest artificial intelligence system that promises to revolutionize 
            how we interact with technology. The new AI system, developed over three 
            years, incorporates advanced machine learning algorithms and natural 
            language processing capabilities.
            
            According to company officials, the system can process natural language 
            with unprecedented accuracy. "This represents a major leap forward in AI 
            capabilities," said CEO Jane Doe during the press conference held at the 
            company's headquarters.
            
            The announcement has already sparked significant interest from investors 
            and competitors alike, with TechCorp's stock price rising 15% in 
            after-hours trading.
            
            Tags: AI, technology, innovation, machine learning
            """
        },
        {
            "query": "Tell me about recent political developments",
            "response": """
            Political Update: New Policy Announced
            
            Source: Associated Press
            Published: Today
            
            Government officials announced a new policy initiative aimed at 
            addressing climate change concerns. The policy, which will take 
            effect next month, includes several key provisions for renewable 
            energy development.
            
            According to sources close to the administration, the policy has 
            been in development for several months and represents a significant 
            shift in environmental strategy.
            """
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Query: {test_case['query']}")
        print("-" * 30)
        
        try:
            # Format the response
            result = await integration.format_response(
                user_query=test_case['query'],
                response_content=test_case['response'],
                theme_context={'current_theme': 'light'}
            )
            
            print(f"Content Type: {result.content_type.value}")
            print(f"Formatter Used: {result.metadata.get('formatter', 'unknown')}")
            print(f"Has Images: {result.has_images}")
            print(f"Has Interactive Elements: {result.has_interactive_elements}")
            print(f"CSS Classes: {', '.join(result.css_classes)}")
            
            # Check if it's news content
            if result.content_type == ContentType.NEWS:
                print("✅ Successfully detected and formatted as news")
                
                # Check for key news elements
                news_elements = [
                    "news-article",
                    "news-headline", 
                    "news-source",
                    "credibility-indicator"
                ]
                
                found_elements = []
                for element in news_elements:
                    if element in result.content:
                        found_elements.append(element)
                
                print(f"News Elements Found: {', '.join(found_elements)}")
                
                # Check metadata
                metadata = result.metadata
                if 'headline' in metadata:
                    print(f"Extracted Headline: {metadata['headline']}")
                if 'source' in metadata:
                    print(f"Extracted Source: {metadata['source']}")
                if 'credibility_score' in metadata:
                    print(f"Credibility Score: {metadata['credibility_score']}")
                
            else:
                print(f"⚠️  Detected as {result.content_type.value} instead of news")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test content detection separately
    print(f"\n{'='*50}")
    print("Testing Content Detection")
    print("=" * 50)
    
    detection_test = """
    Breaking: Scientists Discover New Species
    
    Source: Nature Journal
    Published: Yesterday
    
    Marine biologists have discovered a new species of deep-sea fish 
    in the Pacific Ocean. The discovery was announced in the latest 
    issue of Nature journal.
    """
    
    try:
        detection_result = await integration.detect_content_type(
            "What's new in science?", 
            detection_test
        )
        
        print(f"Detected Type: {detection_result.content_type.value}")
        print(f"Confidence: {detection_result.confidence:.2f}")
        print(f"Reasoning: {detection_result.reasoning}")
        print(f"Keywords: {', '.join(detection_result.keywords[:5])}")
        
        if detection_result.content_type == ContentType.NEWS:
            print("✅ Content detection working correctly")
        else:
            print("⚠️  Content detection may need tuning")
            
    except Exception as e:
        print(f"❌ Detection Error: {e}")
    
    # Show integration metrics
    print(f"\n{'='*50}")
    print("Integration Metrics")
    print("=" * 50)
    
    metrics = integration.get_integration_metrics()
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Successful Formats: {metrics['successful_formats']}")
    print(f"Failed Formats: {metrics['failed_formats']}")
    print(f"Fallback Uses: {metrics['fallback_uses']}")
    
    if metrics['content_type_detections']:
        print("Content Type Detections:")
        for content_type, count in metrics['content_type_detections'].items():
            print(f"  {content_type}: {count}")
    
    print(f"\nAvailable Formatters: {len(metrics['registry_stats']['formatter_names'])}")
    print(f"Formatter Names: {', '.join(metrics['registry_stats']['formatter_names'])}")


if __name__ == "__main__":
    asyncio.run(test_news_formatting())