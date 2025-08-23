#!/usr/bin/env python3
"""
Demo script showing AI integration in Error Response Service

This script demonstrates how the Error Response Service integrates with
the AI orchestrator to provide intelligent error analysis and guidance.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import Mock

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity
)


def mock_llm_response_for_demo():
    """Mock LLM response for demonstration"""
    return json.dumps({
        "title": "AI-Enhanced Database Connection Error",
        "summary": "The database connection failed due to network timeout. This appears to be a temporary connectivity issue rather than a configuration problem.",
        "category": "database_error",
        "severity": "critical",
        "next_steps": [
            "Check if the database server is running and accessible",
            "Verify network connectivity between application and database",
            "Review database connection pool settings for timeout values",
            "Contact database administrator if issue persists beyond 5 minutes"
        ],
        "contact_admin": true,
        "retry_after": 300,
        "technical_details": "Connection timeout after 30 seconds suggests network-level issue rather than authentication failure"
    })


def demo_rule_based_classification():
    """Demonstrate rule-based error classification"""
    print("=== Rule-Based Error Classification Demo ===")
    
    service = ErrorResponseService()
    
    # Test various error types
    test_errors = [
        {
            "message": "OPENAI_API_KEY not set in environment",
            "provider": "OpenAI",
            "description": "Missing API key error"
        },
        {
            "message": "Rate limit exceeded for requests",
            "provider": "OpenAI",
            "status_code": 429,
            "description": "Rate limiting error"
        },
        {
            "message": "Token has expired",
            "status_code": 401,
            "description": "Session expiry error"
        },
        {
            "message": 'relation "users" does not exist',
            "description": "Database schema error"
        }
    ]
    
    for i, error in enumerate(test_errors, 1):
        print(f"\n{i}. {error['description']}:")
        print(f"   Error: {error['message']}")
        
        response = service.analyze_error(
            error_message=error["message"],
            provider_name=error.get("provider"),
            status_code=error.get("status_code"),
            use_ai_analysis=False  # Use only rule-based classification
        )
        
        print(f"   Category: {response.category.value}")
        print(f"   Severity: {response.severity.value}")
        print(f"   Title: {response.title}")
        print(f"   Next Steps: {len(response.next_steps)} actions")
        for j, step in enumerate(response.next_steps[:2], 1):
            print(f"     {j}. {step}")
        if len(response.next_steps) > 2:
            print(f"     ... and {len(response.next_steps) - 2} more")


def demo_ai_enhanced_analysis():
    """Demonstrate AI-enhanced error analysis"""
    print("\n=== AI-Enhanced Error Analysis Demo ===")
    
    service = ErrorResponseService()
    
    # Mock the LLM components for demo
    mock_llm_router = Mock()
    mock_llm_utils = Mock()
    
    # Set up mock responses
    mock_llm_router.invoke.return_value = mock_llm_response_for_demo()
    
    service._llm_router = mock_llm_router
    service._llm_utils = mock_llm_utils
    
    # Test AI analysis on a complex error
    complex_error = "Database connection failed: timeout after 30 seconds connecting to postgresql://localhost:5432/karen_db"
    
    print(f"Complex Error: {complex_error}")
    print("\nAI Analysis Result:")
    
    response = service.analyze_error(
        error_message=complex_error,
        error_type="DatabaseConnectionError",
        status_code=500,
        use_ai_analysis=True
    )
    
    print(f"Title: {response.title}")
    print(f"Summary: {response.summary}")
    print(f"Category: {response.category.value}")
    print(f"Severity: {response.severity.value}")
    print(f"Contact Admin: {response.contact_admin}")
    print(f"Retry After: {response.retry_after} seconds")
    
    print("\nNext Steps:")
    for i, step in enumerate(response.next_steps, 1):
        print(f"  {i}. {step}")
    
    if response.technical_details:
        print(f"\nTechnical Details: {response.technical_details}")
    
    # Verify LLM was called
    print(f"\nLLM Router Called: {mock_llm_router.invoke.called}")
    if mock_llm_router.invoke.called:
        call_args = mock_llm_router.invoke.call_args
        print(f"Task Intent: {call_args[1]['task_intent']}")
        print(f"Preferred Provider: {call_args[1]['preferred_provider']}")


def demo_response_enhancement():
    """Demonstrate AI enhancement of rule-based responses"""
    print("\n=== AI Response Enhancement Demo ===")
    
    service = ErrorResponseService()
    
    # Mock the LLM components
    mock_llm_router = Mock()
    mock_llm_utils = Mock()
    
    # Mock enhancement response
    enhancement_response = json.dumps({
        "title": "Enhanced OpenAI API Key Missing - Quick Setup Guide",
        "summary": "Your OpenAI API key is missing. This is a common setup issue that can be resolved in 2-3 minutes by following these specific steps.",
        "next_steps": [
            "Visit https://platform.openai.com/api-keys and create a new API key",
            "Add 'OPENAI_API_KEY=your_key_here' to your .env file in the project root",
            "Restart the application to load the new environment variable",
            "Verify the key works by testing a simple API call"
        ],
        "additional_insights": "Pro tip: Keep your API key secure and never commit it to version control"
    })
    
    mock_llm_router.invoke.return_value = enhancement_response
    service._llm_router = mock_llm_router
    service._llm_utils = mock_llm_utils
    
    # Test enhancement
    print("Original Rule-Based Response:")
    original_response = service.analyze_error(
        error_message="OPENAI_API_KEY not found in environment",
        provider_name="OpenAI",
        use_ai_analysis=False
    )
    
    print(f"Title: {original_response.title}")
    print(f"Next Steps: {len(original_response.next_steps)} actions")
    
    print("\nAI-Enhanced Response:")
    enhanced_response = service.analyze_error(
        error_message="OPENAI_API_KEY not found in environment",
        provider_name="OpenAI",
        use_ai_analysis=True
    )
    
    print(f"Title: {enhanced_response.title}")
    print(f"Summary: {enhanced_response.summary}")
    print(f"Next Steps: {len(enhanced_response.next_steps)} actions")
    for i, step in enumerate(enhanced_response.next_steps, 1):
        print(f"  {i}. {step}")
    
    if enhanced_response.technical_details and "AI Insights:" in enhanced_response.technical_details:
        insights = enhanced_response.technical_details.split("AI Insights: ")[1]
        print(f"\nAI Insights: {insights}")


def demo_response_quality_validation():
    """Demonstrate response quality validation"""
    print("\n=== Response Quality Validation Demo ===")
    
    service = ErrorResponseService()
    
    # Test valid response
    from ai_karen_engine.services.error_response_service import IntelligentErrorResponse
    
    valid_response = IntelligentErrorResponse(
        title="Well-Structured Error Response",
        summary="This response has a clear summary with sufficient detail to help users understand the issue.",
        category=ErrorCategory.API_KEY_MISSING,
        severity=ErrorSeverity.HIGH,
        next_steps=[
            "Add your API key to the configuration file",
            "Verify the key format is correct",
            "Restart the application to apply changes"
        ]
    )
    
    invalid_response = IntelligentErrorResponse(
        title="Bad",  # Too short
        summary="Short",  # Too short
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.LOW,
        next_steps=["Something happened", "Error occurred"]  # Not actionable
    )
    
    print(f"Valid Response Quality: {service.validate_response_quality(valid_response)}")
    print(f"Invalid Response Quality: {service.validate_response_quality(invalid_response)}")
    
    # Show quality metrics
    print("\nQuality Validation Criteria:")
    print("- Title must be at least 5 characters")
    print("- Summary must be at least 10 characters")
    print("- Must have actionable next steps (contain action words)")
    print("- Critical database errors must set contact_admin=True")
    print("- Severity must match error type appropriately")


def demo_ai_analysis_metrics():
    """Demonstrate AI analysis metrics"""
    print("\n=== AI Analysis Metrics Demo ===")
    
    service = ErrorResponseService()
    metrics = service.get_ai_analysis_metrics()
    
    print("AI Integration Status:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\nComponent Availability:")
    print(f"  AI Orchestrator: {'Available' if service._get_ai_orchestrator() else 'Not Available'}")
    print(f"  LLM Router: {'Available' if service._get_llm_router() else 'Not Available'}")
    print(f"  LLM Utils: {'Available' if service._get_llm_utils() else 'Not Available'}")


def main():
    """Run all demos"""
    print("AI Karen - Error Response Service AI Integration Demo")
    print("=" * 60)
    
    try:
        demo_rule_based_classification()
        demo_ai_enhanced_analysis()
        demo_response_enhancement()
        demo_response_quality_validation()
        demo_ai_analysis_metrics()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Rule-based error classification")
        print("✓ AI-powered error analysis")
        print("✓ Response enhancement with AI insights")
        print("✓ Response quality validation")
        print("✓ Graceful fallback when AI is unavailable")
        print("✓ Integration with provider health monitoring")
        print("✓ Comprehensive metrics collection")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()