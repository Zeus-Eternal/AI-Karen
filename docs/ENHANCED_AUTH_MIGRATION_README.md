# Enhanced Authentication and Validation System Migration

This document describes the migration to the enhanced authentication and validation system, including new features, database schema changes, and deployment instructions.

## Overview

The enhanced authentication system provides:

- **Username-based login**: Users can log in with either email or username
- **Advanced form validation**: Configurable validation rules with detailed error messages
- **Enhanced security logging**: Comprehensive audit trail with security event tracking
- **Rate limiting**: Configurable rate limiting to prevent brute force attacks
- **Password policies**: Enforced password strength requirements with history tracking
- **Improved monitoring**: Enhanced statistics and monitoring views

## Migration Details

### Database Schema Changes

The migration `022_enhanced_auth_validation_system.sql` adds:

#### New Tables

1. **`auth_validation_rules`** - Configurable form validation rules
2. **`auth_security_events`** - Enhanced security event logging
3. **`auth_rate_limits`** - Rate limiting tracking
4. **`auth_password_policies`** - Password policy configuration
5. **`auth_password_history`** - Password history tracking

#### Enhanced Tables

- **`auth_users`** - Added `username`, `password_strength_score`, `password_last_changed`, etc.
- **`auth_sessions`** - Added validation tracking and login method fields

#### New Functions

- `validate_password_strength()` - Server-side password validation
- `check_rate_limit()` - Rate limiting checks
- `record_rate_limit_attempt()` - Rate limit tracking
- `log_security_event()` - Security event logging

#### New Views

- `auth_statistics_enhanced` - Comprehensive authentication metrics
- `recent_security_events` - Recent security events with user context

## Deployment Instructions

### 1. Apply the Migration

```bash
# Option 1: Use the migration script
python scripts/apply_enhanced_auth_migration.py

# Option 2: Apply manually with psql
psql -d ai_karen -f data/migrations/postgres/022_enhanced_auth_validation_system.sql
```

### 2. Update Schema Validator

The schema validator has been updated to expect the new migration version:
- `EXPECTED_MIGRATION_VERSION = "022_enhanced_auth_validation_system.sql"`

### 3. Test the Migration

```bash
# Run the validation test suite
python scripts/test_enhanced_validation.py
```

### 4. Restart Services

Restart your application services to pick up the new schema and features.

## New Features

### Username-Based Login

Users can now log in with either email or username:

```python
# Login with email
validate_login_form({
    "email": "user@example.com",
    "password": "password123"
})

# Login with username
validate_login_form({
    "username": "myusername",
    "password": "password123"
})
```

### Enhanced Form Validation

The new validation system provides detailed error messages:

```python
from src.ai_karen_engine.guardrails.validator import validate_registration_form, ValidationError

try:
    validate_registration_form({
        "username": "newuser",
        "email": "user@example.com",
        "password": "StrongPass123!",
        "confirm_password": "StrongPass123!"
    })
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Password Strength Validation

```python
from src.ai_karen_engine.guardrails.validator import validate_password_strength, get_password_strength_score

# Get detailed password strength analysis
checks = validate_password_strength("MyPassword123!")
score = get_password_strength_score("MyPassword123!")

print(f"Password strength: {score}/100")
print(f"Checks passed: {checks}")
```

### Security Event Logging

All authentication events are now logged with enhanced details:

```sql
-- View recent security events
SELECT * FROM recent_security_events 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Rate Limiting

Built-in rate limiting prevents brute force attacks:

```sql
-- Check rate limit status
SELECT * FROM check_rate_limit('192.168.1.100', 'ip', 10, 15);

-- Record an attempt
SELECT record_rate_limit_attempt('192.168.1.100', 'ip', 10, 15);
```

### Enhanced Monitoring

New monitoring views provide comprehensive metrics:

```sql
-- Get enhanced authentication statistics
SELECT * FROM auth_statistics_enhanced;

-- View password strength distribution
SELECT 
    CASE 
        WHEN password_strength_score >= 80 THEN 'Strong'
        WHEN password_strength_score >= 60 THEN 'Medium'
        ELSE 'Weak'
    END as strength_category,
    COUNT(*) as user_count
FROM auth_users 
WHERE password_strength_score > 0
GROUP BY strength_category;
```

## Configuration

### Password Policies

Password policies can be configured per tenant:

```sql
-- Update default password policy
UPDATE auth_password_policies 
SET min_length = 10,
    require_special_chars = true,
    prevent_common_passwords = true
WHERE policy_name = 'default_policy';
```

### Validation Rules

Form validation rules are configurable:

```sql
-- Update login password requirements
UPDATE auth_validation_rules 
SET validation_config = jsonb_set(
    validation_config, 
    '{min_length}', 
    '10'
) 
WHERE rule_name = 'login_password';
```

## API Changes

### Authentication Service

The `AuthService` now supports:

- Username-based authentication
- Enhanced password validation
- Detailed error messages
- Security event logging

### Validation Functions

New validation functions in `guardrails/validator.py`:

- `validate_login_form()` - Enhanced login validation
- `validate_registration_form()` - Registration with strength checks
- `validate_password_strength()` - Detailed password analysis
- `get_password_strength_score()` - Numeric strength score

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Authentication Success Rate**
   ```sql
   SELECT 
       COUNT(CASE WHEN success THEN 1 END) * 100.0 / COUNT(*) as success_rate
   FROM auth_security_events 
   WHERE event_type LIKE '%LOGIN%' 
     AND timestamp > NOW() - INTERVAL '24 hours';
   ```

2. **Password Strength Distribution**
   ```sql
   SELECT * FROM auth_statistics_enhanced;
   ```

3. **Rate Limiting Activity**
   ```sql
   SELECT COUNT(*) as blocked_attempts
   FROM auth_rate_limits 
   WHERE is_blocked = true 
     AND blocked_until > NOW();
   ```

### Maintenance Tasks

1. **Clean up expired tokens and sessions**
   ```sql
   SELECT cleanup_expired_auth_sessions();
   SELECT cleanup_expired_auth_tokens();
   ```

2. **Monitor security events**
   ```sql
   SELECT * FROM recent_security_events 
   WHERE severity IN ('high', 'critical')
   ORDER BY timestamp DESC;
   ```

3. **Review password policies**
   ```sql
   SELECT policy_name, min_length, require_uppercase, require_special_chars
   FROM auth_password_policies 
   WHERE is_active = true;
   ```

## Troubleshooting

### Common Issues

1. **Migration fails with permission errors**
   - Ensure the database user has CREATE, ALTER, and INSERT permissions
   - Check that the `karen_user` exists and has proper grants

2. **Validation errors after migration**
   - Run the test suite: `python scripts/test_enhanced_validation.py`
   - Check that validation rules are properly loaded

3. **Authentication service fails to start**
   - Verify the schema version matches: `EXPECTED_MIGRATION_VERSION`
   - Check database connectivity and permissions

### Rollback Procedure

If you need to rollback the migration:

1. **Backup current data**
   ```bash
   pg_dump ai_karen > backup_before_rollback.sql
   ```

2. **Drop new tables** (if needed)
   ```sql
   DROP TABLE IF EXISTS auth_validation_rules CASCADE;
   DROP TABLE IF EXISTS auth_security_events CASCADE;
   DROP TABLE IF EXISTS auth_rate_limits CASCADE;
   DROP TABLE IF EXISTS auth_password_policies CASCADE;
   DROP TABLE IF EXISTS auth_password_history CASCADE;
   ```

3. **Update schema validator**
   ```python
   EXPECTED_MIGRATION_VERSION = "021_admin_system_rollback.sql"
   ```

## Support

For issues or questions about the enhanced authentication system:

1. Check the test suite output for specific error details
2. Review the database logs for migration errors
3. Verify all environment variables are properly set
4. Ensure all dependencies are installed and up to date

## Next Steps

After successful migration:

1. **Update frontend applications** to use the new validation features
2. **Configure password policies** according to your security requirements
3. **Set up monitoring** for the new security metrics
4. **Train users** on the new username login capability
5. **Review and adjust** rate limiting settings based on usage patterns