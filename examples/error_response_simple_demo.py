#!/usr/bin/env python3
"""
Simple demonstration of the Intelligent Error Response Service

This script shows the core functionality without complex dependencies.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


class ErrorCategory(str, Enum):
    """Categories for error classification"""
    AUTHENTICATION = "authentication"
    API_KEY_MISSING = "api_key_missing"
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMIT = "rate_limit"
    PROVIDER_DOWN = "provider_down"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorResponse:
    """Simple error response"""
    title: str
    summary: str
    category: ErrorCategory
    severity: ErrorSeverity
    next_steps: List[str]
    contact_admin: bool = False
    retry_after: Optional[int] = None


class SimpleErrorClassifier:
    """Simplified error classifier for demonstration"""
    
    def __init__(self):
        self.rules = [
            {
                "name": "openai_api_key_missing",
                "pattern": r"openai.*api.*key.*not.*found|OPENAI_API_KEY.*not.*set",
                "category": ErrorCategory.API_KEY_MISSING,
                "severity": ErrorSeverity.HIGH,
                "title": "OpenAI API Key Missing",
                "summary": "The OpenAI API key is not configured in your environment.",
                "next_steps": [
                    "Add OPENAI_API_KEY to your .env file",
                    "Get your API key from https://platform.openai.com/api-keys",
                    "Restart the application after adding the key"
                ]
            },
            {
                "name": "session_expired",
                "pattern": r"token.*expired|session.*expired",
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "title": "Session Expired",
                "summary": "Your session has expired and you need to log in again.",
                "next_steps": [
                    "Click the login button to sign in again",
                    "Your work will be saved automatically"
                ]
            },
            {
                "name": "rate_limit_exceeded",
                "pattern": r"rate.*limit.*exceeded|too.*many.*requests",
                "category": ErrorCategory.RATE_LIMIT,
                "severity": ErrorSeverity.MEDIUM,
                "title": "Rate Limit Exceeded",
                "summary": "You've exceeded the rate limit for the service.",
                "next_steps": [
                    "Wait a few minutes before trying again",
                    "Consider upgrading your plan for higher limits",
                    "Try using a different provider if available"
                ],
                "retry_after": 300
            },
            {
                "name": "database_connection_error",
                "pattern": r"database.*connection.*failed|could.*not.*connect.*database",
                "category": ErrorCategory.DATABASE_ERROR,
                "severity": ErrorSeverity.CRITICAL,
                "title": "Database Connection Failed",
                "summary": "Unable to connect to the database.",
                "next_steps": [
                    "Contact admin immediately",
                    "Check if database service is running"
                ],
                "contact_admin": True
            },
            {
                "name": "provider_unavailable",
                "pattern": r"service.*unavailable|provider.*unavailable|503.*service.*unavailable",
                "category": ErrorCategory.PROVIDER_DOWN,
                "severity": ErrorSeverity.HIGH,
                "title": "Service Temporarily Unavailable",
                "summary": "The service is currently unavailable.",
                "next_steps": [
                    "Try again in a few minutes",
                    "Check service status page for updates",
                    "Use an alternative provider if configured"
                ],
                "retry_after": 180
            }
        ]
    
    def classify_error(self, error_message: str) -> ErrorResponse:
        """Classify an error message and return appropriate response"""
        for rule in self.rules:
            if re.search(rule["pattern"], error_message, re.IGNORECASE):
                return ErrorResponse(
                    title=rule["title"],
                    summary=rule["summary"],
                    category=rule["category"],
                    severity=rule["severity"],
                    next_steps=rule["next_steps"],
                    contact_admin=rule.get("contact_admin", False),
                    retry_after=rule.get("retry_after")
                )
        
        # Fallback for unclassified errors
        return ErrorResponse(
            title="Unexpected Error",
            summary="An unexpected error occurred while processing your request.",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            next_steps=[
                "Try refreshing the page",
                "Check your internet connection",
                "Contact admin if the problem persists"
            ],
            contact_admin=True
        )


def print_separator(title: str):
    """Print a section separator"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demonstrate_error_classification():
    """Demonstrate error classification"""
    print_separator("INTELLIGENT ERROR RESPONSE DEMO")
    
    classifier = SimpleErrorClassifier()
    
    test_cases = [
        "OPENAI_API_KEY not set in environment",
        "Token has expired, please log in again",
        "Rate limit exceeded for requests",
        "Database connection failed: Connection refused",
        "Service unavailable: 503 error",
        "Some completely unknown error occurred"
    ]
    
    for i, error_message in enumerate(test_cases, 1):
        print(f"\n{i}. Error: {error_message}")
        print("-" * 50)
        
        response = classifier.classify_error(error_message)
        
        print(f"📋 Category: {response.category.value}")
        print(f"⚠️  Severity: {response.severity.value}")
        print(f"📝 Title: {response.title}")
        print(f"💬 Summary: {response.summary}")
        print("🔧 Next Steps:")
        for step in response.next_steps:
            print(f"   • {step}")
        
        if response.contact_admin:
            print("👨‍💼 Contact admin required: Yes")
        
        if response.retry_after:
            print(f"⏱️  Retry after: {response.retry_after} seconds")


def demonstrate_response_formatting():
    """Demonstrate different response formats"""
    print_separator("RESPONSE FORMATTING EXAMPLES")
    
    classifier = SimpleErrorClassifier()
    response = classifier.classify_error("OPENAI_API_KEY not found in environment")
    
    print("1. User-Friendly Format (Frontend):")
    print(f"   🚨 {response.title}")
    print(f"   {response.summary}")
    print("   What to do next:")
    for i, step in enumerate(response.next_steps, 1):
        print(f"   {i}. {step}")
    
    print("\n2. API Format (Backend):")
    api_response = {
        "error": response.title,
        "message": response.summary,
        "category": response.category.value,
        "severity": response.severity.value,
        "next_steps": response.next_steps,
        "contact_admin": response.contact_admin,
        "retry_after": response.retry_after,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for key, value in api_response.items():
        if value is not None:
            print(f"   {key}: {value}")


def demonstrate_benefits():
    """Show the benefits of intelligent error responses"""
    print_separator("BENEFITS OF INTELLIGENT ERROR RESPONSES")
    
    print("🎯 BEFORE (Generic Error):")
    print("   Error: Something went wrong")
    print("   Message: An error occurred")
    print("   Action: Contact support")
    
    print("\n✨ AFTER (Intelligent Response):")
    classifier = SimpleErrorClassifier()
    response = classifier.classify_error("OPENAI_API_KEY not set")
    
    print(f"   Error: {response.title}")
    print(f"   Message: {response.summary}")
    print("   Actions:")
    for step in response.next_steps:
        print(f"     • {step}")
    
    print("\n📈 Key Improvements:")
    print("   ✅ Specific problem identification")
    print("   ✅ Clear, actionable next steps")
    print("   ✅ Reduced support tickets")
    print("   ✅ Better user experience")
    print("   ✅ Faster problem resolution")


def main():
    """Run the demonstration"""
    print("🤖 Intelligent Error Response Service")
    print("Transforming cryptic errors into actionable guidance")
    
    try:
        demonstrate_error_classification()
        demonstrate_response_formatting()
        demonstrate_benefits()
        
        print_separator("DEMO COMPLETE")
        print("✅ Demo completed successfully!")
        print("\n🚀 Ready to implement in your application!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())