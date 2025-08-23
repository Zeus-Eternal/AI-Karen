#!/usr/bin/env python3
"""
Demonstration of the Intelligent Error Response Service

This script shows how the error response service analyzes different types of errors
and provides intelligent, actionable responses to users.
"""

import sys
import os

# Add the src directory to the path so we can import the services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    format_error_for_user,
    format_error_for_api
)
from ai_karen_engine.services.provider_health_monitor import (
    get_health_monitor,
    record_provider_failure,
    record_provider_success
)


def print_separator(title: str):
    """Print a section separator"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demonstrate_error_classification():
    """Demonstrate error classification capabilities"""
    print_separator("ERROR CLASSIFICATION DEMONSTRATION")
    
    service = ErrorResponseService()
    
    # Test cases with different error types
    test_cases = [
        {
            "name": "OpenAI API Key Missing",
            "error_message": "OPENAI_API_KEY not set in environment",
            "provider_name": "OpenAI"
        },
        {
            "name": "Session Expired",
            "error_message": "Token has expired",
            "status_code": 401
        },
        {
            "name": "Rate Limit Exceeded",
            "error_message": "Rate limit exceeded for requests",
            "status_code": 429,
            "provider_name": "OpenAI"
        },
        {
            "name": "Database Connection Failed",
            "error_message": "Database connection failed: Connection refused"
        },
        {
            "name": "Missing Database Table",
            "error_message": 'relation "users" does not exist'
        },
        {
            "name": "Provider Unavailable",
            "error_message": "Service unavailable: 503 error",
            "status_code": 503,
            "provider_name": "Anthropic"
        },
        {
            "name": "Network Timeout",
            "error_message": "Request timeout after 30 seconds",
            "status_code": 504
        },
        {
            "name": "Validation Error",
            "error_message": "Validation failed: required field missing",
            "status_code": 400
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        response = service.analyze_error(
            error_message=test_case["error_message"],
            error_type=test_case.get("error_type"),
            status_code=test_case.get("status_code"),
            provider_name=test_case.get("provider_name")
        )
        
        print(f"Category: {response.category.value}")
        print(f"Severity: {response.severity.value}")
        print(f"Title: {response.title}")
        print(f"Summary: {response.summary}")
        print("Next Steps:")
        for step in response.next_steps:
            print(f"  • {step}")
        
        if response.contact_admin:
            print("⚠️  Contact admin required")
        
        if response.retry_after:
            print(f"⏱️  Retry after: {response.retry_after} seconds")


def demonstrate_provider_health_integration():
    """Demonstrate provider health integration"""
    print_separator("PROVIDER HEALTH INTEGRATION DEMONSTRATION")
    
    service = ErrorResponseService()
    health_monitor = get_health_monitor()
    
    # Clear any existing health data
    health_monitor.clear_cache()
    
    print("1. Setting up provider health states...")
    
    # Set up different provider health states
    record_provider_success("OpenAI", response_time=0.5)
    
    # Make Anthropic degraded (multiple failures)
    for _ in range(3):
        record_provider_failure("Anthropic", "Rate limit exceeded")
    
    # Make Google unhealthy (many failures)
    for _ in range(6):
        record_provider_failure("Google", "Service unavailable")
    
    print("   ✓ OpenAI: Healthy")
    print("   ⚠️ Anthropic: Degraded (3 failures)")
    print("   ❌ Google: Unhealthy (6 failures)")
    
    print("\n2. Analyzing errors with provider context...")
    
    # Test error with healthy provider
    print("\n--- Error with Healthy Provider (OpenAI) ---")
    response = service.analyze_error(
        error_message="OPENAI_API_KEY missing",
        provider_name="OpenAI"
    )
    
    print(f"Title: {response.title}")
    print(f"Provider Status: {response.provider_health['status']}")
    print(f"Success Rate: {response.provider_health['success_rate']:.1%}")
    
    # Test error with degraded provider
    print("\n--- Error with Degraded Provider (Anthropic) ---")
    response = service.analyze_error(
        error_message="Rate limit exceeded",
        provider_name="Anthropic"
    )
    
    print(f"Title: {response.title}")
    print(f"Provider Status: {response.provider_health['status']}")
    print(f"Success Rate: {response.provider_health['success_rate']:.1%}")
    print("Next Steps:")
    for step in response.next_steps:
        print(f"  • {step}")
    
    # Test error with unhealthy provider
    print("\n--- Error with Unhealthy Provider (Google) ---")
    response = service.analyze_error(
        error_message="Service unavailable",
        provider_name="Google"
    )
    
    print(f"Title: {response.title}")
    print(f"Provider Status: {response.provider_health['status']}")
    print(f"Success Rate: {response.provider_health['success_rate']:.1%}")
    print("Next Steps:")
    for step in response.next_steps:
        print(f"  • {step}")


def demonstrate_response_formatting():
    """Demonstrate response formatting for different consumers"""
    print_separator("RESPONSE FORMATTING DEMONSTRATION")
    
    service = ErrorResponseService()
    
    # Analyze an error
    response = service.analyze_error(
        error_message="OPENAI_API_KEY not found in environment",
        provider_name="OpenAI"
    )
    
    print("1. Raw Response Object:")
    print(f"   Title: {response.title}")
    print(f"   Category: {response.category.value}")
    print(f"   Severity: {response.severity.value}")
    
    print("\n2. Formatted for User (Frontend):")
    user_format = format_error_for_user(response)
    print(f"   Title: {user_format['title']}")
    print(f"   Message: {user_format['message']}")
    print(f"   Severity: {user_format['severity']}")
    print("   Next Steps:")
    for step in user_format['next_steps']:
        print(f"     • {step}")
    
    print("\n3. Formatted for API (Backend):")
    api_format = format_error_for_api(response)
    print(f"   Error: {api_format['error']}")
    print(f"   Category: {api_format['category']}")
    print(f"   Technical Details: {api_format.get('technical_details', 'None')}")


def demonstrate_custom_rules():
    """Demonstrate adding custom classification rules"""
    print_separator("CUSTOM CLASSIFICATION RULES DEMONSTRATION")
    
    from ai_karen_engine.services.error_response_service import (
        ErrorClassificationRule,
        ErrorCategory,
        ErrorSeverity
    )
    
    service = ErrorResponseService()
    
    print("1. Adding custom rule for Docker errors...")
    
    # Add a custom rule for Docker errors
    docker_rule = ErrorClassificationRule(
        name="docker_not_running",
        patterns=[r"docker.*not.*running", r"cannot.*connect.*docker", r"docker.*daemon.*not.*running"],
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.HIGH,
        title_template="Docker Not Running",
        summary_template="Docker daemon is not running or not accessible.",
        next_steps=[
            "Start Docker Desktop or Docker daemon",
            "Check if Docker is installed correctly",
            "Verify Docker permissions for your user"
        ],
        help_url="https://docs.docker.com/get-started/"
    )
    
    service.add_classification_rule(docker_rule)
    
    print("   ✓ Custom Docker rule added")
    
    print("\n2. Testing custom rule...")
    
    response = service.analyze_error(
        error_message="Cannot connect to Docker daemon. Is docker running?"
    )
    
    print(f"   Title: {response.title}")
    print(f"   Category: {response.category.value}")
    print(f"   Summary: {response.summary}")
    print("   Next Steps:")
    for step in response.next_steps:
        print(f"     • {step}")
    print(f"   Help URL: {response.help_url}")


def main():
    """Run all demonstrations"""
    print("🤖 Intelligent Error Response Service Demo")
    print("This demo shows how the service analyzes errors and provides actionable guidance.")
    
    try:
        demonstrate_error_classification()
        demonstrate_provider_health_integration()
        demonstrate_response_formatting()
        demonstrate_custom_rules()
        
        print_separator("DEMO COMPLETE")
        print("✅ All demonstrations completed successfully!")
        print("\nThe Error Response Service provides:")
        print("  • Intelligent error classification")
        print("  • Provider health integration")
        print("  • Actionable user guidance")
        print("  • Flexible response formatting")
        print("  • Extensible rule system")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())