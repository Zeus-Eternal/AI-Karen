# Security Enhancements and Monitoring (Task 13)

## Overview

This document describes the implementation of enhanced security features for the authentication system, including rate limiting with exponential backoff, suspicious activity detection, security alerts, and CSRF protection.

## Features Implemented

### 1. Enhanced Rate Limiting with Exponential Backoff

**Location**: `src/ai_karen_engine/auth/security_monitor.py`

#### Key Features:
- **Exponential Backoff**: Failed attempts result in progressively longer lockout periods
- **Per-IP and Per-User Limiting**: Separate limits for IP addresses and user accounts
- **Configurable Thresholds**: Customizable attempt limits and backoff multipliers
- **Automatic Reset**: Successful authentication resets backoff levels

#### Configuration:
```python
# Default settings (configurable)
base_window_seconds = 60        # Base rate limiting window
max_attempts_per_window = 5     # Max attempts per window
backoff_multiplier = 2.0        # Exponential backoff multiplier
max_backoff_hours = 24          # Maximum lockout duration
```

#### Usage Example:
```python
rate_limiter = ExponentialBackoffRateLimiter(config)

# Check if request is allowed
await rate_limiter.check_rate_limit(ip_address, email, "login")

# Record attempt result
await rate_limiter.record_attempt(ip_address, email, success=False)
```

### 2. Suspicious Activity Detection

**Location**: `src/ai_karen_engine/auth/security_monitor.py`

#### Anomaly Types Detected:
- **Rapid Failed Attempts**: Multiple failed logins in short time
- **Multiple IPs**: Same user from many different IP addresses
- **Unusual Location**: Login from unexpected geographic location
- **Unusual Time**: Login at atypical hours for the user
- **Brute Force Pattern**: High failure rate across multiple accounts
- **Account Enumeration**: Many "user not found" errors from same IP

#### Risk Scoring:
- Each anomaly contributes to an overall risk score (0.0 to 1.0)
- Confidence level indicates detection certainty
- Multiple anomalies compound the risk score

#### Usage Example:
```python
detector = SuspiciousActivityDetector(config)

result = await detector.analyze_attempt(
    ip_address="192.168.1.1",
    user_agent="Browser/1.0",
    email="user@example.com",
    success=False,
    failure_reason="invalid_credentials",
    geolocation={"country": "US", "city": "New York"}
)

if result.is_suspicious:
    print(f"Risk Score: {result.risk_score}")
    print(f"Anomalies: {result.anomaly_types}")
```

### 3. Security Alert System

**Location**: `src/ai_karen_engine/auth/security_monitor.py`

#### Alert Types:
- **Excessive Failed Attempts**: Too many failed logins from IP/user
- **Authentication Anomaly**: Suspicious patterns detected
- **Custom Alerts**: Extensible alert system for new threat types

#### Threat Levels:
- **LOW**: Minor security events
- **MEDIUM**: Moderate security concerns
- **HIGH**: Serious security threats
- **CRITICAL**: Immediate security risks

#### Alert Management:
```python
alert_manager = SecurityAlertManager(config)

# Create alert for failed attempts
alert = await alert_manager.create_failed_attempt_alert(
    ip_address="192.168.1.1",
    email="user@example.com",
    attempt_count=25,
    time_window="1 hour"
)

# Get recent alerts
recent_alerts = alert_manager.get_recent_alerts(hours=24)

# Get alert statistics
stats = alert_manager.get_alert_stats()
```

### 4. CSRF Protection

**Location**: `src/ai_karen_engine/auth/csrf_protection.py`

#### Protection Method:
- **Double-Submit Cookie Pattern**: Token in both cookie and header
- **HMAC Validation**: Cryptographically secure token validation
- **Time-Based Expiry**: Tokens expire after configurable period
- **User Binding**: Optional binding of tokens to specific users

#### Protected Operations:
- User registration
- User login
- Password changes
- Account settings updates
- Any state-changing authentication operation

#### Usage Example:
```python
csrf_middleware = CSRFProtectionMiddleware(config)

# Generate CSRF token
token = csrf_middleware.generate_csrf_response(
    response, user_id="user123", secure=True
)

# Validate CSRF protection
await csrf_middleware.validate_csrf_protection(request, user_id="user123")
```

### 5. Enhanced Security Monitoring

**Location**: `src/ai_karen_engine/auth/security_monitor.py`

#### Main Security Monitor:
The `EnhancedSecurityMonitor` class orchestrates all security components:

```python
security_monitor = EnhancedSecurityMonitor(config)

# Pre-authentication security check
await security_monitor.check_authentication_security(
    ip_address="192.168.1.1",
    user_agent="Browser/1.0",
    email="user@example.com",
    endpoint="login"
)

# Post-authentication result recording
await security_monitor.record_authentication_result(
    ip_address="192.168.1.1",
    user_agent="Browser/1.0",
    success=False,
    email="user@example.com",
    failure_reason="invalid_credentials"
)

# Get security statistics
stats = security_monitor.get_security_stats()
```

## Integration with Authentication Routes

### Updated Endpoints

All authentication endpoints in `src/ai_karen_engine/api_routes/auth_session_routes.py` have been enhanced with:

1. **Pre-request Security Checks**: Rate limiting and anomaly detection
2. **CSRF Protection**: For state-changing operations
3. **Post-request Monitoring**: Result recording and alert generation

### New Endpoints

#### CSRF Token Endpoint
```
GET /api/auth/csrf-token
```
Returns CSRF token for authenticated users.

#### Security Statistics Endpoint
```
GET /api/auth/security-stats
```
Returns security statistics (admin only).

### Enhanced Health Check
The `/api/auth/health` endpoint now includes security monitoring status.

## Configuration

### Environment Variables

Security features can be configured through the auth config:

```python
class SecurityConfig:
    enable_rate_limiting: bool = True
    enable_anomaly_detection: bool = True
    enable_security_alerts: bool = True
    enable_csrf_protection: bool = True
    
    # Rate limiting settings
    rate_limit_max_requests: int = 5
    rate_limit_window_minutes: int = 1
    max_failed_attempts: int = 10
    lockout_duration_minutes: int = 15
    
    # CSRF settings
    csrf_token_lifetime_minutes: int = 60
```

### Feature Toggles

Each security feature can be individually enabled/disabled:

```python
# Disable specific features if needed
config.security.enable_rate_limiting = False
config.security.enable_anomaly_detection = False
config.security.enable_security_alerts = False
config.security.enable_csrf_protection = False
```

## Security Considerations

### Rate Limiting
- Uses in-memory storage by default (can be extended to Redis)
- Separate limits for different endpoints
- Exponential backoff prevents sustained attacks
- Successful authentication resets penalties

### Anomaly Detection
- Machine learning-like pattern recognition
- Builds user behavior profiles over time
- Geographic and temporal analysis
- Low false positive rate through confidence scoring

### CSRF Protection
- Cryptographically secure tokens using HMAC-SHA256
- HttpOnly cookies prevent XSS access
- SameSite=Strict prevents CSRF attacks
- Time-based expiry limits token lifetime

### Alert System
- Structured logging for security events
- Configurable alert handlers for notifications
- Rate limiting prevents alert spam
- Historical data for trend analysis

## Monitoring and Observability

### Metrics Collected
- Authentication success/failure rates
- Rate limiting violations
- Anomaly detection triggers
- Alert generation frequency
- Security event patterns

### Log Entries
All security events are logged with structured data:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "rate_limit_exceeded",
  "ip_address": "192.168.1.1",
  "user_email": "user@example.com",
  "backoff_level": 2,
  "retry_after": 240
}
```

### Dashboard Integration
Security statistics are available through the `/api/auth/security-stats` endpoint for dashboard integration.

## Testing

### Test Coverage

Comprehensive tests are provided in:
- `tests/test_security_enhancements.py`: Full integration tests
- `tests/test_rate_limiting_anomaly_detection.py`: Focused component tests
- `tests/test_security_components_simple.py`: Lightweight unit tests

### Test Scenarios
- Rate limiting with exponential backoff
- Anomaly detection for various attack patterns
- CSRF token generation and validation
- Security alert creation and management
- Integration between components

### Running Tests
```bash
# Run all security tests
python -m pytest tests/test_security_enhancements.py -v

# Run focused tests
python -m pytest tests/test_rate_limiting_anomaly_detection.py -v

# Run simple component tests
python tests/test_security_components_simple.py
```

## Performance Considerations

### Memory Usage
- In-memory storage for rate limiting and anomaly detection
- Automatic cleanup of expired entries
- Configurable history retention limits
- Optional Redis backend for distributed deployments

### CPU Impact
- Efficient algorithms for pattern detection
- Lazy evaluation of anomaly detection
- Minimal overhead for normal requests
- Asynchronous processing where possible

### Scalability
- Stateless design allows horizontal scaling
- Optional external storage backends
- Configurable thresholds for different load levels
- Graceful degradation under high load

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**: Advanced anomaly detection using ML models
2. **Geolocation Services**: Enhanced location-based security
3. **Device Fingerprinting**: Browser and device identification
4. **Behavioral Biometrics**: Typing patterns and mouse movements
5. **Threat Intelligence**: Integration with external threat feeds

### Extension Points
- Custom anomaly detectors
- Additional alert handlers
- External storage backends
- Custom rate limiting strategies
- Integration with SIEM systems

## Troubleshooting

### Common Issues

#### High False Positive Rate
- Adjust anomaly detection thresholds
- Increase confidence requirements
- Review user behavior patterns

#### Rate Limiting Too Aggressive
- Increase attempt limits
- Reduce backoff multiplier
- Adjust window sizes

#### CSRF Token Issues
- Check token expiry settings
- Verify cookie security flags
- Ensure proper header inclusion

### Debug Information
Enable debug logging to see detailed security event information:

```python
import logging
logging.getLogger('ai_karen_engine.auth.security_monitor').setLevel(logging.DEBUG)
```

## Compliance and Standards

### Security Standards
- OWASP Top 10 protection
- NIST Cybersecurity Framework alignment
- Industry best practices for authentication security

### Privacy Considerations
- Minimal data collection for security purposes
- Configurable data retention periods
- User privacy protection in logging

### Audit Trail
- Complete audit trail of security events
- Tamper-evident logging
- Compliance reporting capabilities

## Conclusion

The enhanced security monitoring system provides comprehensive protection against common authentication attacks while maintaining usability and performance. The modular design allows for easy customization and extension based on specific security requirements.

For questions or issues, please refer to the test files for usage examples or contact the development team.