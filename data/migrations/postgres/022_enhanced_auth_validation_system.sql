-- Enhanced Authentication and Validation System Migration
-- This migration updates the authentication schema to support the new enhanced
-- authentication service with improved validation, security features, and form validation

BEGIN;

-- ============================================================================
-- Update auth_users table to match AuthService requirements
-- ============================================================================

-- Add username column for flexible login (email or username)
ALTER TABLE auth_users 
ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE;

-- Create index for username lookups
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username) WHERE username IS NOT NULL;

-- Update existing users to have usernames based on email
UPDATE auth_users 
SET username = split_part(email, '@', 1) 
WHERE username IS NULL;

-- ============================================================================
-- Create auth_validation_rules table for form validation
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_validation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL, -- 'login', 'registration', 'password_reset'
    field_name VARCHAR(50) NOT NULL,
    validation_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default validation rules for login form
INSERT INTO auth_validation_rules (rule_name, rule_type, field_name, validation_config) VALUES
('login_username', 'login', 'username', '{
    "regex": "^[a-zA-Z0-9._-]{3,50}$",
    "required": false,
    "min_length": 3,
    "max_length": 50,
    "description": "Username can contain letters, numbers, dots, underscores, and hyphens"
}'),
('login_email', 'login', 'email', '{
    "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
    "required": false,
    "max_length": 254,
    "description": "Valid email address format"
}'),
('login_password', 'login', 'password', '{
    "regex": "^.{8,128}$",
    "required": true,
    "min_length": 8,
    "max_length": 128,
    "description": "Password must be at least 8 characters"
}'),
('login_remember_me', 'login', 'remember_me', '{
    "enum": [true, false, "true", "false", "1", "0"],
    "required": false,
    "description": "Remember me option"
}'),
('login_two_factor_code', 'login', 'two_factor_code', '{
    "regex": "^\\d{6}$",
    "required": false,
    "description": "6-digit two-factor authentication code"
}');

-- Insert default validation rules for registration form
INSERT INTO auth_validation_rules (rule_name, rule_type, field_name, validation_config) VALUES
('registration_username', 'registration', 'username', '{
    "regex": "^[a-zA-Z0-9._-]{3,50}$",
    "required": true,
    "min_length": 3,
    "max_length": 50,
    "description": "Username can contain letters, numbers, dots, underscores, and hyphens"
}'),
('registration_email', 'registration', 'email', '{
    "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
    "required": true,
    "max_length": 254,
    "description": "Valid email address format"
}'),
('registration_password', 'registration', 'password', '{
    "regex": "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,128}$",
    "required": true,
    "min_length": 8,
    "max_length": 128,
    "description": "Password must contain uppercase, lowercase, digit, and special character"
}'),
('registration_confirm_password', 'registration', 'confirm_password', '{
    "required": true,
    "match_field": "password",
    "description": "Must match password field"
}');

-- Create indexes for validation rules
CREATE INDEX IF NOT EXISTS idx_auth_validation_rules_type ON auth_validation_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_auth_validation_rules_active ON auth_validation_rules(is_active) WHERE is_active = true;

-- ============================================================================
-- Create auth_security_events table for enhanced security logging
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info', -- 'low', 'medium', 'high', 'critical'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- User context
    user_id UUID REFERENCES auth_users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    username VARCHAR(50),
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    session_token VARCHAR(255),
    
    -- Event details
    success BOOLEAN NOT NULL,
    error_message TEXT,
    validation_errors JSONB,
    security_flags JSONB DEFAULT '[]'::jsonb,
    risk_score FLOAT DEFAULT 0.0,
    blocked_by_security BOOLEAN DEFAULT false,
    
    -- Performance metrics
    processing_time_ms FLOAT DEFAULT 0.0,
    
    -- Additional context
    details JSONB DEFAULT '{}'::jsonb,
    tenant_id UUID,
    service_version VARCHAR(100) DEFAULT 'enhanced-auth-v1.0'
);

-- Create indexes for security events
CREATE INDEX IF NOT EXISTS idx_auth_security_events_type ON auth_security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_security_events_timestamp ON auth_security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_auth_security_events_user ON auth_security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_security_events_severity ON auth_security_events(severity);
CREATE INDEX IF NOT EXISTS idx_auth_security_events_ip ON auth_security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_auth_security_events_success ON auth_security_events(success);

-- ============================================================================
-- Create auth_rate_limits table for rate limiting tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL, -- IP address or email
    identifier_type VARCHAR(20) NOT NULL, -- 'ip', 'email', 'user'
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_duration_minutes INTEGER NOT NULL DEFAULT 15,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 10,
    is_blocked BOOLEAN DEFAULT false,
    blocked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for rate limits
CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_identifier ON auth_rate_limits(identifier, identifier_type);
CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_window ON auth_rate_limits(window_start, window_duration_minutes);
CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_blocked ON auth_rate_limits(is_blocked, blocked_until);

-- ============================================================================
-- Create auth_password_policies table for configurable password policies
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_password_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    tenant_id UUID,
    
    -- Password requirements
    min_length INTEGER DEFAULT 8,
    max_length INTEGER DEFAULT 128,
    require_uppercase BOOLEAN DEFAULT true,
    require_lowercase BOOLEAN DEFAULT true,
    require_digits BOOLEAN DEFAULT true,
    require_special_chars BOOLEAN DEFAULT true,
    special_chars VARCHAR(50) DEFAULT '@$!%*?&',
    
    -- Security settings
    prevent_common_passwords BOOLEAN DEFAULT true,
    prevent_username_in_password BOOLEAN DEFAULT true,
    password_history_count INTEGER DEFAULT 5,
    max_age_days INTEGER DEFAULT 90,
    
    -- Policy metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default password policy
INSERT INTO auth_password_policies (
    policy_name, 
    tenant_id,
    min_length,
    max_length,
    require_uppercase,
    require_lowercase,
    require_digits,
    require_special_chars,
    special_chars,
    prevent_common_passwords,
    prevent_username_in_password,
    password_history_count,
    max_age_days,
    is_active
) VALUES (
    'default_policy',
    'default'::uuid,
    8,
    128,
    true,
    true,
    true,
    true,
    '@$!%*?&',
    true,
    true,
    5,
    90,
    true
) ON CONFLICT (policy_name) DO NOTHING;

-- ============================================================================
-- Create auth_password_history table for password history tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_password_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for password history
CREATE INDEX IF NOT EXISTS idx_auth_password_history_user ON auth_password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_password_history_created ON auth_password_history(created_at);

-- ============================================================================
-- Update existing tables with new columns for enhanced features
-- ============================================================================

-- Add validation tracking to auth_users
ALTER TABLE auth_users 
ADD COLUMN IF NOT EXISTS password_strength_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS password_last_changed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS account_locked_reason VARCHAR(255),
ADD COLUMN IF NOT EXISTS login_attempts_window_start TIMESTAMP WITH TIME ZONE;

-- Add enhanced session tracking to auth_sessions
ALTER TABLE auth_sessions
ADD COLUMN IF NOT EXISTS validation_passed BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS validation_errors JSONB,
ADD COLUMN IF NOT EXISTS login_method VARCHAR(50) DEFAULT 'password'; -- 'password', '2fa', 'oauth', etc.

-- ============================================================================
-- Create enhanced functions for validation and security
-- ============================================================================

-- Function to validate password strength
CREATE OR REPLACE FUNCTION validate_password_strength(
    password_text TEXT,
    username_text TEXT DEFAULT NULL,
    policy_name_param VARCHAR DEFAULT 'default_policy'
)
RETURNS TABLE(
    is_valid BOOLEAN,
    score INTEGER,
    issues TEXT[]
) AS $
DECLARE
    policy_record auth_password_policies%ROWTYPE;
    issues_array TEXT[] := '{}';
    strength_score INTEGER := 0;
    is_password_valid BOOLEAN := true;
BEGIN
    -- Get password policy
    SELECT * INTO policy_record 
    FROM auth_password_policies 
    WHERE policy_name = policy_name_param AND is_active = true;
    
    IF NOT FOUND THEN
        -- Use default policy if specified policy not found
        SELECT * INTO policy_record 
        FROM auth_password_policies 
        WHERE policy_name = 'default_policy' AND is_active = true;
    END IF;
    
    -- Check minimum length
    IF LENGTH(password_text) < policy_record.min_length THEN
        issues_array := array_append(issues_array, 'Password must be at least ' || policy_record.min_length || ' characters long');
        is_password_valid := false;
    ELSE
        strength_score := strength_score + 16;
    END IF;
    
    -- Check maximum length
    IF LENGTH(password_text) > policy_record.max_length THEN
        issues_array := array_append(issues_array, 'Password must be no more than ' || policy_record.max_length || ' characters long');
        is_password_valid := false;
    END IF;
    
    -- Check uppercase requirement
    IF policy_record.require_uppercase AND password_text !~ '[A-Z]' THEN
        issues_array := array_append(issues_array, 'Password must contain at least one uppercase letter');
        is_password_valid := false;
    ELSIF password_text ~ '[A-Z]' THEN
        strength_score := strength_score + 16;
    END IF;
    
    -- Check lowercase requirement
    IF policy_record.require_lowercase AND password_text !~ '[a-z]' THEN
        issues_array := array_append(issues_array, 'Password must contain at least one lowercase letter');
        is_password_valid := false;
    ELSIF password_text ~ '[a-z]' THEN
        strength_score := strength_score + 16;
    END IF;
    
    -- Check digits requirement
    IF policy_record.require_digits AND password_text !~ '[0-9]' THEN
        issues_array := array_append(issues_array, 'Password must contain at least one number');
        is_password_valid := false;
    ELSIF password_text ~ '[0-9]' THEN
        strength_score := strength_score + 16;
    END IF;
    
    -- Check special characters requirement
    IF policy_record.require_special_chars AND password_text !~ ('[' || policy_record.special_chars || ']') THEN
        issues_array := array_append(issues_array, 'Password must contain at least one special character (' || policy_record.special_chars || ')');
        is_password_valid := false;
    ELSIF password_text ~ ('[' || policy_record.special_chars || ']') THEN
        strength_score := strength_score + 16;
    END IF;
    
    -- Check common passwords
    IF policy_record.prevent_common_passwords THEN
        IF LOWER(password_text) ~ '^(password|123456|qwerty|admin|letmein|welcome|monkey|dragon)' THEN
            issues_array := array_append(issues_array, 'Password is too common or weak');
            is_password_valid := false;
        ELSE
            strength_score := strength_score + 4;
        END IF;
    END IF;
    
    -- Check username in password
    IF policy_record.prevent_username_in_password AND username_text IS NOT NULL THEN
        IF LOWER(password_text) LIKE '%' || LOWER(username_text) || '%' THEN
            issues_array := array_append(issues_array, 'Password cannot contain username');
            is_password_valid := false;
        ELSE
            strength_score := strength_score + 4;
        END IF;
    END IF;
    
    -- Bonus points for length
    IF LENGTH(password_text) >= 12 THEN
        strength_score := strength_score + 4;
    END IF;
    IF LENGTH(password_text) >= 16 THEN
        strength_score := strength_score + 4;
    END IF;
    
    -- Cap score at 100
    strength_score := LEAST(strength_score, 100);
    
    RETURN QUERY SELECT is_password_valid, strength_score, issues_array;
END;
$ LANGUAGE plpgsql;

-- Function to check rate limiting
CREATE OR REPLACE FUNCTION check_rate_limit(
    identifier_param VARCHAR,
    identifier_type_param VARCHAR,
    max_attempts_param INTEGER DEFAULT 10,
    window_minutes_param INTEGER DEFAULT 15
)
RETURNS TABLE(
    is_allowed BOOLEAN,
    attempts_remaining INTEGER,
    reset_time TIMESTAMP WITH TIME ZONE
) AS $
DECLARE
    current_window_start TIMESTAMP WITH TIME ZONE;
    current_attempts INTEGER := 0;
    rate_limit_record auth_rate_limits%ROWTYPE;
BEGIN
    -- Calculate current window start
    current_window_start := DATE_TRUNC('minute', NOW()) - 
                           INTERVAL '1 minute' * (EXTRACT(MINUTE FROM NOW())::INTEGER % window_minutes_param);
    
    -- Get or create rate limit record
    SELECT * INTO rate_limit_record
    FROM auth_rate_limits
    WHERE identifier = identifier_param 
      AND identifier_type = identifier_type_param
      AND window_start = current_window_start;
    
    IF FOUND THEN
        current_attempts := rate_limit_record.attempt_count;
    ELSE
        -- Clean up old rate limit records for this identifier
        DELETE FROM auth_rate_limits
        WHERE identifier = identifier_param 
          AND identifier_type = identifier_type_param
          AND window_start < current_window_start - INTERVAL '1 hour';
        
        current_attempts := 0;
    END IF;
    
    -- Check if blocked
    IF current_attempts >= max_attempts_param THEN
        RETURN QUERY SELECT 
            false,
            0,
            current_window_start + INTERVAL '1 minute' * window_minutes_param;
    ELSE
        RETURN QUERY SELECT 
            true,
            max_attempts_param - current_attempts,
            current_window_start + INTERVAL '1 minute' * window_minutes_param;
    END IF;
END;
$ LANGUAGE plpgsql;

-- Function to record rate limit attempt
CREATE OR REPLACE FUNCTION record_rate_limit_attempt(
    identifier_param VARCHAR,
    identifier_type_param VARCHAR,
    max_attempts_param INTEGER DEFAULT 10,
    window_minutes_param INTEGER DEFAULT 15
)
RETURNS BOOLEAN AS $
DECLARE
    current_window_start TIMESTAMP WITH TIME ZONE;
    current_attempts INTEGER := 0;
BEGIN
    -- Calculate current window start
    current_window_start := DATE_TRUNC('minute', NOW()) - 
                           INTERVAL '1 minute' * (EXTRACT(MINUTE FROM NOW())::INTEGER % window_minutes_param);
    
    -- Insert or update rate limit record
    INSERT INTO auth_rate_limits (
        identifier,
        identifier_type,
        window_start,
        window_duration_minutes,
        attempt_count,
        max_attempts,
        is_blocked,
        blocked_until
    ) VALUES (
        identifier_param,
        identifier_type_param,
        current_window_start,
        window_minutes_param,
        1,
        max_attempts_param,
        false,
        NULL
    )
    ON CONFLICT (identifier, identifier_type, window_start) 
    DO UPDATE SET
        attempt_count = auth_rate_limits.attempt_count + 1,
        is_blocked = (auth_rate_limits.attempt_count + 1) >= max_attempts_param,
        blocked_until = CASE 
            WHEN (auth_rate_limits.attempt_count + 1) >= max_attempts_param 
            THEN current_window_start + INTERVAL '1 minute' * window_minutes_param
            ELSE NULL
        END,
        updated_at = NOW();
    
    -- Return whether the attempt was allowed
    SELECT attempt_count INTO current_attempts
    FROM auth_rate_limits
    WHERE identifier = identifier_param 
      AND identifier_type = identifier_type_param
      AND window_start = current_window_start;
    
    RETURN current_attempts <= max_attempts_param;
END;
$ LANGUAGE plpgsql;

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    event_type_param VARCHAR,
    severity_param VARCHAR DEFAULT 'info',
    user_id_param UUID DEFAULT NULL,
    email_param VARCHAR DEFAULT NULL,
    username_param VARCHAR DEFAULT NULL,
    ip_address_param INET DEFAULT NULL,
    user_agent_param TEXT DEFAULT NULL,
    success_param BOOLEAN DEFAULT true,
    error_message_param TEXT DEFAULT NULL,
    validation_errors_param JSONB DEFAULT NULL,
    details_param JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO auth_security_events (
        event_type,
        severity,
        user_id,
        email,
        username,
        ip_address,
        user_agent,
        success,
        error_message,
        validation_errors,
        details
    ) VALUES (
        event_type_param,
        severity_param,
        user_id_param,
        email_param,
        username_param,
        ip_address_param,
        user_agent_param,
        success_param,
        error_message_param,
        validation_errors_param,
        details_param
    ) RETURNING id INTO event_id;
    
    RETURN event_id;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- Create enhanced views for monitoring
-- ============================================================================

-- View for authentication statistics with validation metrics
CREATE OR REPLACE VIEW auth_statistics_enhanced AS
SELECT 
    (SELECT COUNT(*) FROM auth_users) as total_users,
    (SELECT COUNT(*) FROM auth_users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM auth_users WHERE is_verified = true) as verified_users,
    (SELECT COUNT(*) FROM auth_users WHERE username IS NOT NULL) as users_with_username,
    (SELECT COUNT(*) FROM auth_sessions WHERE is_active = true AND expires_at > NOW()) as active_sessions,
    (SELECT COUNT(*) FROM auth_users WHERE two_factor_enabled = true) as users_with_2fa,
    (SELECT COUNT(*) FROM auth_users WHERE locked_until > NOW()) as locked_users,
    (SELECT COUNT(*) FROM auth_security_events WHERE timestamp > NOW() - INTERVAL '1 hour' AND event_type = 'LOGIN_FAILED') as failed_logins_last_hour,
    (SELECT COUNT(*) FROM auth_security_events WHERE timestamp > NOW() - INTERVAL '1 hour' AND event_type = 'LOGIN_SUCCESS') as successful_logins_last_hour,
    (SELECT COUNT(*) FROM auth_security_events WHERE timestamp > NOW() - INTERVAL '1 hour' AND severity IN ('high', 'critical')) as security_alerts_last_hour,
    (SELECT AVG(password_strength_score) FROM auth_users WHERE password_strength_score > 0) as avg_password_strength,
    (SELECT COUNT(*) FROM auth_rate_limits WHERE is_blocked = true AND blocked_until > NOW()) as currently_rate_limited;

-- View for recent security events with user context
CREATE OR REPLACE VIEW recent_security_events AS
SELECT 
    e.id,
    e.event_type,
    e.severity,
    e.timestamp,
    e.user_id,
    e.email,
    e.username,
    u.full_name,
    e.ip_address,
    e.success,
    e.error_message,
    e.validation_errors,
    e.security_flags,
    e.risk_score,
    e.blocked_by_security,
    e.processing_time_ms,
    e.details
FROM auth_security_events e
LEFT JOIN auth_users u ON e.user_id = u.id
WHERE e.timestamp > NOW() - INTERVAL '24 hours'
ORDER BY e.timestamp DESC;

-- ============================================================================
-- Update triggers for enhanced functionality
-- ============================================================================

-- Trigger to update password strength score when password changes
CREATE OR REPLACE FUNCTION update_password_strength_trigger()
RETURNS TRIGGER AS $
BEGIN
    -- This would typically be called from application code after password validation
    -- For now, we'll set a default score
    IF NEW.password_hash != OLD.password_hash THEN
        NEW.password_strength_score := 75; -- Default score, should be calculated by app
        NEW.password_last_changed := NOW();
        
        -- Store password in history
        INSERT INTO auth_password_history (user_id, password_hash)
        VALUES (NEW.id, NEW.password_hash);
        
        -- Clean up old password history (keep only last N passwords)
        DELETE FROM auth_password_history
        WHERE user_id = NEW.id
          AND id NOT IN (
              SELECT id FROM auth_password_history
              WHERE user_id = NEW.id
              ORDER BY created_at DESC
              LIMIT 5
          );
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply password strength trigger
DROP TRIGGER IF EXISTS update_password_strength_trigger ON auth_users;
CREATE TRIGGER update_password_strength_trigger
    BEFORE UPDATE ON auth_users
    FOR EACH ROW
    EXECUTE FUNCTION update_password_strength_trigger();

-- ============================================================================
-- Grant permissions for enhanced tables and functions
-- ============================================================================

DO $
BEGIN
    -- Grant table permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_validation_rules TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_security_events TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_rate_limits TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_password_policies TO karen_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON auth_password_history TO karen_user;
    
    -- Grant view permissions
    GRANT SELECT ON auth_statistics_enhanced TO karen_user;
    GRANT SELECT ON recent_security_events TO karen_user;
    
    -- Grant function execution permissions
    GRANT EXECUTE ON FUNCTION validate_password_strength(TEXT, TEXT, VARCHAR) TO karen_user;
    GRANT EXECUTE ON FUNCTION check_rate_limit(VARCHAR, VARCHAR, INTEGER, INTEGER) TO karen_user;
    GRANT EXECUTE ON FUNCTION record_rate_limit_attempt(VARCHAR, VARCHAR, INTEGER, INTEGER) TO karen_user;
    GRANT EXECUTE ON FUNCTION log_security_event(VARCHAR, VARCHAR, UUID, VARCHAR, VARCHAR, INET, TEXT, BOOLEAN, TEXT, JSONB, JSONB) TO karen_user;
    
    RAISE NOTICE 'Enhanced authentication permissions granted to karen_user';
EXCEPTION
    WHEN undefined_object THEN
        RAISE NOTICE 'User karen_user does not exist, skipping permission grants';
END $;

-- ============================================================================
-- Data migration for existing users
-- ============================================================================

-- Update existing users with usernames if they don't have them
UPDATE auth_users 
SET username = split_part(email, '@', 1) 
WHERE username IS NULL;

-- Set default password strength scores for existing users
UPDATE auth_users 
SET password_strength_score = 50,
    password_last_changed = COALESCE(updated_at, created_at)
WHERE password_strength_score = 0;

-- ============================================================================
-- Verification and status report
-- ============================================================================

-- Display new table creation status
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE tablename IN (
    'auth_validation_rules',
    'auth_security_events', 
    'auth_rate_limits',
    'auth_password_policies',
    'auth_password_history'
)
ORDER BY tablename;

-- Display enhanced authentication statistics
SELECT * FROM auth_statistics_enhanced;

-- Display validation rules
SELECT rule_name, rule_type, field_name, validation_config 
FROM auth_validation_rules 
WHERE is_active = true
ORDER BY rule_type, field_name;

-- Final status message
DO $
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Enhanced Authentication and Validation System Migration Complete';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'New features enabled:';
    RAISE NOTICE '- Username-based login (email or username)';
    RAISE NOTICE '- Configurable form validation rules';
    RAISE NOTICE '- Enhanced security event logging';
    RAISE NOTICE '- Rate limiting with configurable windows';
    RAISE NOTICE '- Password policy enforcement';
    RAISE NOTICE '- Password history tracking';
    RAISE NOTICE '- Password strength validation';
    RAISE NOTICE '- Enhanced monitoring views';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Database schema updated for AuthService compatibility';
    RAISE NOTICE 'All existing users have been migrated with usernames';
    RAISE NOTICE '=================================================================';
END $;

COMMIT;