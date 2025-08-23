#!/usr/bin/env python3
"""
Simple demo script showing AI integration in Error Response Service

This script demonstrates the AI integration features without requiring
full system initialization.
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import Mock
from datetime import datetime

# Import only the specific classes we need
from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    IntelligentErrorResponse
)


def create_mock_service():
    """Create a service with mocked AI components"""
    service = ErrorResponseService()
    
    # Mock the AI components
    mock_llm_router = Mock()
    mock_llm_utils = Mock()
    
    service._llm_router = mock_llm_router
    service._llm_utils = mock_llm_utils
    
    return service, mock_llm_router, mock_llm_utils


def demo_ai_error_analysis():
    """Demonstrate AI-powered error analysis"""
    print("=== AI-Powered Error Analysis Demo ===")
    
    service, mock_llm_router, mock_llm_utils = create_mock_service()
    
    # Mock AI response for a complex error
    ai_response = json.dumps({
        "title": "Multi-Service Authentication Failure",
        "summary": "Authentication failed due to a cascade of service dependencies. The OAuth provider is healthy, but the token validation service is experiencing intermittent issues.",
        "category": "authentication",
        "severity": "high",
        "next_steps": [
            "Check the token validation service status dashboard",
            "Verify OAuth provider configuration is correct",
            "Try logging in again in 2-3 minutes",
            "Contact admin if authentication continues to fail after 5 minutes"
        ],
        "contact_admin": false,
        "retry_after": 120,
        "technical_details": "OAuth token received successfully but validation service returned 503 intermittently"
    })
    
    mock_llm_router.invoke.return_value = ai_response
    
    # Test with a complex error that would be hard to classify with rules
    complex_error = "Authentication chain failure: OAuth token validation failed with service unavailable (503) - intermittent failures detected"
    
    print(f"Complex Error: {complex_error}")
    print("\nAI Analysis:")
    
    context = ErrorContext(
        error_message=complex_error,
        error_type="AuthenticationChainError",
        status_code=503
    )
    
    response = service._generate_ai_error_response(context)
    
    if response:
        print(f"✓ Title: {response.title}")
        print(f"✓ Category: {response.category.value}")
        print(f"✓ Severity: {response.severity.value}")
        print(f"✓ Summary: {response.summary}")
        print(f"✓ Retry After: {response.retry_after} seconds")
        
        print("\nNext Steps:")
        for i, step in enumerate(response.next_steps, 1):
            print(f"  {i}. {step}")
        
        print(f"\nTechnical Details: {response.technical_details}")
        
        # Verify AI was called correctly
        print(f"\n✓ LLM Router called: {mock_llm_router.invoke.called}")
        if mock_llm_router.invoke.called:
            call_args = mock_llm_router.invoke.call_args
            print(f"✓ Task intent: {call_args[1]['task_intent']}")
            print(f"✓ Provider: {call_args[1]['preferred_provider']}")
    else:
        print("✗ AI analysis failed")


def demo_response_enhancement():
    """Demonstrate AI enhancement of rule-based responses"""
    print("\n=== AI Response Enhancement Demo ===")
    
    service, mock_llm_router, mock_llm_utils = create_mock_service()
    
    # Create a base rule-based response
    base_response = IntelligentErrorResponse(
        title="Rate Limit Exceeded",
        summary="You've exceeded the rate limit for OpenAI.",
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM,
        next_steps=[
            "Wait a few minutes before trying again",
            "Consider upgrading your OpenAI plan"
        ]
    )
    
    # Mock AI enhancement
    enhancement_response = json.dumps({
        "title": "OpenAI Rate Limit - Upgrade Recommended",
        "summary": "You've hit OpenAI's rate limit. Based on your usage pattern, upgrading to a higher tier would prevent future interruptions and provide 5x higher limits.",
        "next_steps": [
            "Wait 5 minutes for the rate limit to reset automatically",
            "Upgrade to OpenAI Pro for 5x higher limits and priority access",
            "Consider using Anthropic Claude as a backup provider",
            "Implement request queuing to smooth out traffic spikes"
        ],
        "additional_insights": "Your current usage suggests you need at least Tier 2 limits to avoid future interruptions"
    })
    
    mock_llm_router.invoke.return_value = enhancement_response
    
    print("Original Rule-Based Response:")
    print(f"  Title: {base_response.title}")
    print(f"  Next Steps: {len(base_response.next_steps)} actions")
    
    # Test enhancement
    context = ErrorContext(
        error_message="Rate limit exceeded",
        provider_name="OpenAI"
    )
    
    enhanced_response = service._enhance_response_with_ai(base_response, context)
    
    if enhanced_response:
        print("\nAI-Enhanced Response:")
        print(f"✓ Enhanced Title: {enhanced_response.title}")
        print(f"✓ Enhanced Summary: {enhanced_response.summary}")
        print(f"✓ Enhanced Steps: {len(enhanced_response.next_steps)} actions")
        
        print("\nEnhanced Next Steps:")
        for i, step in enumerate(enhanced_response.next_steps, 1):
            print(f"  {i}. {step}")
        
        if enhanced_response.technical_details and "AI Insights:" in enhanced_response.technical_details:
            insights = enhanced_response.technical_details.split("AI Insights: ")[1]
            print(f"\n✓ AI Insights: {insights}")
    else:
        print("✗ AI enhancement failed")


def demo_prompt_generation():
    """Demonstrate AI prompt generation"""
    print("\n=== AI Prompt Generation Demo ===")
    
    service, _, _ = create_mock_service()
    
    # Create error context
    context = ErrorContext(
        error_message="Database connection timeout after 30 seconds",
        error_type="ConnectionTimeoutError",
        status_code=500,
        provider_name="PostgreSQL",
        additional_data={"connection_pool": "exhausted", "retry_count": 3}
    )
    
    # Build analysis context
    analysis_context = {
        "provider_health": {
            "name": "PostgreSQL",
            "status": "degraded",
            "success_rate": 75.0,
            "response_time": 8000,
            "error_message": "High connection latency detected"
        },
        "alternative_providers": ["MySQL", "SQLite"],
        "connection_pool": "exhausted",
        "retry_count": 3
    }
    
    # Generate prompt
    prompt = service._build_error_analysis_prompt(context, analysis_context)
    
    print("Generated AI Analysis Prompt:")
    print("-" * 50)
    print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
    print("-" * 50)
    
    print("\n✓ Prompt includes:")
    print("  - Error message and context")
    print("  - Provider health information")
    print("  - Alternative providers")
    print("  - JSON response format specification")
    print("  - Actionable guidance requirements")


def demo_response_validation():
    """Demonstrate response quality validation"""
    print("\n=== Response Quality Validation Demo ===")
    
    service, _, _ = create_mock_service()
    
    # Test valid response
    valid_response = IntelligentErrorResponse(
        title="Well-Structured Database Error",
        summary="The database connection failed due to network timeout. This appears to be a temporary connectivity issue that should resolve within a few minutes.",
        category=ErrorCategory.DATABASE_ERROR,
        severity=ErrorSeverity.CRITICAL,
        next_steps=[
            "Check if the database server is running",
            "Verify network connectivity to the database",
            "Review connection pool settings",
            "Contact database administrator if issue persists"
        ],
        contact_admin=True
    )
    
    # Test invalid response
    invalid_response = IntelligentErrorResponse(
        title="Bad",  # Too short
        summary="Error",  # Too short
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.LOW,
        next_steps=["Something went wrong", "Try again"]  # Not actionable
    )
    
    print(f"Valid Response Quality: {'✓ PASS' if service.validate_response_quality(valid_response) else '✗ FAIL'}")
    print(f"Invalid Response Quality: {'✓ PASS' if service.validate_response_quality(invalid_response) else '✗ FAIL'}")
    
    print("\nQuality Validation Criteria:")
    print("  ✓ Title must be at least 5 characters")
    print("  ✓ Summary must be at least 10 characters")
    print("  ✓ Must have actionable next steps")
    print("  ✓ Critical database errors must set contact_admin=True")
    print("  ✓ Severity must match error type")


def demo_json_parsing():
    """Demonstrate AI response JSON parsing"""
    print("\n=== AI Response JSON Parsing Demo ===")
    
    service, _, _ = create_mock_service()
    
    # Test parsing response with code blocks
    ai_response_with_blocks = """```json
{
    "title": "Parsed from Code Blocks",
    "summary": "This response was wrapped in markdown code blocks",
    "category": "system_error",
    "severity": "medium",
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}
```"""
    
    context = ErrorContext(error_message="Test error")
    
    parsed_response = service._parse_ai_error_response(ai_response_with_blocks, context)
    
    if parsed_response:
        print("✓ Successfully parsed response with code blocks")
        print(f"  Title: {parsed_response.title}")
        print(f"  Category: {parsed_response.category.value}")
        print(f"  Steps: {len(parsed_response.next_steps)}")
    else:
        print("✗ Failed to parse response")
    
    # Test parsing invalid JSON
    invalid_json = "This is not valid JSON at all"
    parsed_invalid = service._parse_ai_error_response(invalid_json, context)
    
    print(f"Invalid JSON handling: {'✓ Gracefully handled' if parsed_invalid is None else '✗ Should return None'}")


def main():
    """Run all demos"""
    print("AI Karen - Error Response Service AI Integration Demo")
    print("=" * 60)
    
    try:
        demo_ai_error_analysis()
        demo_response_enhancement()
        demo_prompt_generation()
        demo_response_validation()
        demo_json_parsing()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("\nKey AI Integration Features:")
        print("✓ AI-powered error analysis for complex/unclassified errors")
        print("✓ AI enhancement of rule-based responses")
        print("✓ Intelligent prompt generation with context")
        print("✓ Response quality validation")
        print("✓ Robust JSON parsing with error handling")
        print("✓ Graceful fallback when AI components fail")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()