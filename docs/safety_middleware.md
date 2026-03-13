# Safety Middleware for CoPilot Architecture

## Overview

The Safety Middleware is a critical component of the CoPilot Architecture that provides comprehensive safety checks for all requests and responses. It includes content safety validation, authorization checks, and integration with existing safety systems.

## Components

### 1. SafetyMiddleware

The main middleware class that integrates with FastAPI applications to provide safety checks for all HTTP requests and responses.

**Key Features:**
- Content safety validation
- Authorization checks
- Behavior monitoring
- Compliance checking
- Error handling for safety operations
- Configurable safety levels

**Usage:**
```python
from fastapi import FastAPI
from ai_karen_engine.middleware.safety_middleware import SafetyMiddleware, SafetyMiddlewareConfig

app = FastAPI()

# Create safety configuration
config = SafetyMiddlewareConfig(
    mode=SafetyMiddlewareMode.ENFORCE,
    enabled=True,
    log_safety_events=True
)

# Add safety middleware
app.add_middleware(SafetyMiddleware, config=config)
```

### 2. SafetyMiddlewareConfig

Configuration class for the Safety Middleware that allows customization of safety checks and behavior.

**Key Configuration Options:**
- `mode`: Safety middleware mode (disabled, monitor, enforce, strict)
- `enabled`: Whether the middleware is enabled
- `log_safety_events`: Whether to log safety events
- `content_safety`: Configuration for content safety checks
- `authorization`: Configuration for authorization checks
- `behavior_monitoring`: Configuration for behavior monitoring
- `compliance`: Configuration for compliance checking

**Usage:**
```python
from ai_karen_engine.middleware.safety_config import SafetyMiddlewareConfig, SafetyMiddlewareMode

config = SafetyMiddlewareConfig(
    mode=SafetyMiddlewareMode.ENFORCE,
    enabled=True,
    log_safety_events=True,
    content_safety=ContentSafetyConfig(
        enabled=True,
        sensitivity_level=SafetyLevel.MEDIUM,
        check_input=True,
        check_output=True
    ),
    authorization=AuthorizationConfig(
        enabled=True,
        strict_mode=False,
        default_role="user"
    )
)
```

### 3. ContentSafetyChecker

Component that checks content for safety violations, including malicious content, harmful language, and other safety concerns.

**Key Features:**
- Keyword-based filtering
- Pattern matching
- ML-based content analysis
- Adaptive learning
- Content sanitization

**Usage:**
```python
from ai_karen_engine.middleware.content_safety_checker import ContentSafetyChecker

checker = ContentSafetyChecker()

# Check content safety
result = await checker.check_content_safety("This is a safe message")
if result.is_safe:
    # Content is safe
    pass
else:
    # Content is unsafe
    print(f"Violations: {result.violations}")

# Sanitize content
sanitized = await checker.sanitize_content("This has bad words")
print(f"Sanitized: {sanitized}")

# Analyze content
analysis = await checker.analyze_content("This is a message for analysis")
print(f"Safety score: {analysis['safety_score']}")
print(f"Risk level: {analysis['risk_level']}")
```

### 4. AuthorizationChecker

Component that handles authorization checks for requests, ensuring users have the necessary permissions to access resources.

**Key Features:**
- Role-based access control
- Resource-based authorization
- Permission validation
- User permission management

**Usage:**
```python
from ai_karen_engine.middleware.authorization_checker import AuthorizationChecker

checker = AuthorizationChecker()

# Check authorization
result = await checker.check_authorization("user_id", "/api/resource", "read")
if result.is_authorized:
    # User is authorized
    pass
else:
    # User is not authorized
    print(f"Reason: {result.denied_reason}")

# Check specific permission
permission_result = await checker.check_permission("user_id", "read:content")
if permission_result.has_permission:
    # User has permission
    pass

# Get user permissions
permissions = await checker.get_user_permissions("user_id")
print(f"User permissions: {permissions}")
```

### 5. SafetyErrorHandler

Component that handles errors that occur during safety checks, providing appropriate responses and error recovery.

**Key Features:**
- Error classification
- Error handling strategies
- Error tracking and statistics
- Custom error handlers
- Alerting for critical errors

**Usage:**
```python
from ai_karen_engine.middleware.safety_error_handler import SafetyErrorHandler

handler = SafetyErrorHandler()

# Handle an error
try:
    # Code that might raise an error
    pass
except Exception as e:
    response = await handler.handle_error(e)
    if response:
        return response

# Get error statistics
stats = handler.get_error_statistics()
print(f"Total errors: {stats['total_errors']}")
print(f"Top error types: {stats['top_error_types']}")

# Clear error history
handler.clear_error_history()
```

## Configuration

### Environment Variables

The Safety Middleware can be configured using environment variables:

- `SAFETY_MIDDLEWARE_MODE`: Safety middleware mode (disabled, monitor, enforce, strict)
- `SAFETY_MIDDLEWARE_ENABLED`: Whether the middleware is enabled (true/false)
- `SAFETY_MIDDLEWARE_LOG_EVENTS`: Whether to log safety events (true/false)
- `SAFETY_MIDDLEWARE_DEBUG`: Whether to enable debug mode (true/false)
- `SAFETY_CONTENT_ENABLED`: Whether content safety checks are enabled (true/false)
- `SAFETY_CONTENT_SENSITIVITY`: Content safety sensitivity level (low, medium, high)
- `SAFETY_AUTH_ENABLED`: Whether authorization checks are enabled (true/false)
- `SAFETY_AUTH_STRICT`: Whether authorization is in strict mode (true/false)
- `SAFETY_BEHAVIOR_ENABLED`: Whether behavior monitoring is enabled (true/false)
- `SAFETY_COMPLIANCE_ENABLED`: Whether compliance checking is enabled (true/false)

### Configuration File

The Safety Middleware can also be configured using a JSON file:

```json
{
  "mode": "enforce",
  "enabled": true,
  "log_safety_events": true,
  "debug_mode": false,
  "content_safety": {
    "enabled": true,
    "sensitivity_level": "medium",
    "check_input": true,
    "check_output": true,
    "max_content_length": 1000000,
    "blocked_keywords": ["malicious", "harmful", "dangerous", "illegal"],
    "allowed_content_types": ["text/plain", "application/json"],
    "ml_filtering_enabled": true,
    "adaptive_learning_enabled": true
  },
  "authorization": {
    "enabled": true,
    "strict_mode": false,
    "default_role": "user",
    "admin_roles": ["admin", "administrator"],
    "protected_paths": {
      "admin": ["/admin/", "/api/admin/"],
      "user": ["/api/user/", "/api/profile/"],
      "guest": []
    },
    "public_paths": [
      "/health", "/metrics", "/docs", "/openapi.json", "/redoc",
      "/api/auth/login", "/api/auth/health", "/api/auth/status"
    ],
    "session_timeout": 3600,
    "token_refresh_enabled": true
  },
  "behavior_monitoring": {
    "enabled": true,
    "track_requests": true,
    "track_responses": true,
    "track_errors": true,
    "anomaly_detection": true,
    "baseline_learning": true,
    "risk_assessment": true,
    "max_events_per_session": 1000,
    "event_retention_days": 30,
    "alert_thresholds": {
      "error_rate": 0.1,
      "request_rate": 100,
      "response_time": 5.0
    }
  },
  "compliance": {
    "enabled": true,
    "standards": ["SOC2", "GDPR", "HIPAA", "ISO27001"],
    "audit_logging": true,
    "data_retention_days": 365,
    "report_generation_interval": 86400,
    "auto_escalation": true,
    "violation_threshold": 3,
    "escalation_contacts": ["security_team", "compliance_officer"]
  }
}
```

## Safety Events

The Safety Middleware logs safety events that can be retrieved for monitoring and analysis:

```python
from ai_karen_engine.middleware.safety_middleware import SafetyMiddleware

# Get safety middleware instance
middleware = app.middleware_stack[0]  # Assuming SafetyMiddleware is the first middleware

# Get all safety events
events = middleware.get_safety_events()

# Get events with filtering
events = middleware.get_safety_events(
    limit=100,
    event_type="content_safety_check",
    severity=SafetyLevel.HIGH,
    user_id="user_id"
)

# Clear safety events
middleware.clear_safety_events()
```

## Error Handling

The Safety ErrorHandler provides comprehensive error handling for safety operations:

```python
from ai_karen_engine.middleware.safety_error_handler import SafetyErrorHandler, ErrorHandlingStrategy, ErrorAction

handler = SafetyErrorHandler()

# Add custom error handling strategy
strategy = ErrorHandlingStrategy(
    error_category=ErrorCategory.CONTENT_SAFETY,
    error_type="custom_error",
    action=ErrorAction.BLOCK,
    should_log=True,
    should_alert=True,
    fallback_response={
        "error": "Custom error",
        "message": "A custom error occurred",
        "category": "content_safety"
    }
)
handler.add_strategy(strategy)

# Register custom error handler
async def custom_handler(error, strategy, request):
    # Custom error handling logic
    return JSONResponse(
        status_code=400,
        content={"error": "Custom error response"}
    )

handler.register_error_handler("custom_error", custom_handler)
```

## Testing

The Safety Middleware includes comprehensive tests that can be run using pytest:

```bash
# Run all safety middleware tests
pytest tests/test_safety_middleware.py

# Run specific test class
pytest tests/test_safety_middleware.py::TestSafetyMiddleware

# Run specific test method
pytest tests/test_safety_middleware.py::TestSafetyMiddleware::test_safety_middleware_initialization
```

## Best Practices

1. **Configure appropriate safety levels**: Set the safety level based on your application's requirements. Higher safety levels provide more protection but may impact performance.

2. **Monitor safety events**: Regularly review safety events to identify potential issues and adjust configuration as needed.

3. **Customize for your application**: Customize the Safety Middleware configuration to match your application's specific requirements and use cases.

4. **Test thoroughly**: Test the Safety Middleware with various scenarios to ensure it works as expected in your application.

5. **Keep up to date**: Regularly update the Safety Middleware to benefit from the latest security improvements and bug fixes.

## Troubleshooting

### Common Issues

1. **Middleware not working**: Ensure the middleware is properly added to the FastAPI application and that the configuration is correct.

2. **All requests being blocked**: Check the safety level configuration and ensure it's not set too high for your use case.

3. **Performance issues**: Consider disabling certain safety checks or reducing the safety level if performance is a concern.

4. **False positives**: Customize the content safety configuration to reduce false positives for your specific use case.

### Debug Mode

Enable debug mode to get more detailed logging:

```python
config = SafetyMiddlewareConfig(
    debug_mode=True
)
```

Or using environment variables:

```bash
export SAFETY_MIDDLEWARE_DEBUG=true
```

## Conclusion

The Safety Middleware is a powerful component that provides comprehensive safety checks for the CoPilot Architecture. By properly configuring and using the Safety Middleware, you can ensure that your application is secure and compliant with relevant standards and regulations.