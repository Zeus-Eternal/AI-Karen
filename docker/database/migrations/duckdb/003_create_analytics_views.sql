-- DuckDB Analytics Views and Functions
-- This migration creates views and helper functions for analytics and reporting

-- Create view for recent profile activity
CREATE OR REPLACE VIEW recent_profile_activity AS
SELECT 
    ph.user_id,
    p.profile_json,
    ph.field,
    ph.old,
    ph.new,
    ph.timestamp,
    datetime(ph.timestamp, 'unixepoch') as timestamp_readable,
    ph.change_type,
    ph.metadata,
    p.last_update,
    p.version
FROM profile_history ph
LEFT JOIN profiles p ON ph.user_id = p.user_id
WHERE ph.timestamp > (strftime('%s', 'now') - 86400) -- Last 24 hours
ORDER BY ph.timestamp DESC;

-- Create view for user activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    ph.user_id,
    COUNT(*) as total_changes,
    COUNT(DISTINCT ph.field) as fields_modified,
    MIN(ph.timestamp) as first_activity,
    MAX(ph.timestamp) as last_activity,
    datetime(MIN(ph.timestamp), 'unixepoch') as first_activity_readable,
    datetime(MAX(ph.timestamp), 'unixepoch') as last_activity_readable,
    COUNT(DISTINCT DATE(datetime(ph.timestamp, 'unixepoch'))) as active_days,
    p.created_at as profile_created,
    p.version as profile_version
FROM profile_history ph
LEFT JOIN profiles p ON ph.user_id = p.user_id
GROUP BY ph.user_id, p.created_at, p.version
ORDER BY last_activity DESC;

-- Create view for memory analytics
CREATE OR REPLACE VIEW memory_analytics AS
SELECT 
    user_id,
    memory_type,
    COUNT(*) as memory_count,
    AVG(importance_score) as avg_importance,
    MIN(created_at) as oldest_memory,
    MAX(created_at) as newest_memory,
    COUNT(*) FILTER (WHERE expires_at IS NULL) as permanent_memories,
    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at > CURRENT_TIMESTAMP) as active_temporary_memories,
    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP) as expired_memories
FROM long_term_memory
GROUP BY user_id, memory_type
ORDER BY user_id, memory_type;

-- Create view for role analytics
CREATE OR REPLACE VIEW role_analytics AS
SELECT 
    role,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE is_active = true) as active_users,
    COUNT(*) FILTER (WHERE expires_at IS NULL) as permanent_assignments,
    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at > CURRENT_TIMESTAMP) as temporary_active,
    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP) as expired_assignments,
    MIN(granted_at) as first_granted,
    MAX(granted_at) as last_granted
FROM user_roles
GROUP BY role
ORDER BY total_users DESC;

-- Create view for session analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    user_id,
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE is_active = true) as active_sessions,
    MIN(created_at) as first_session,
    MAX(last_activity) as last_activity,
    AVG(strftime('%s', last_activity) - strftime('%s', created_at)) as avg_session_duration_seconds,
    COUNT(DISTINCT DATE(created_at)) as active_days
FROM user_sessions
GROUP BY user_id
ORDER BY last_activity DESC;

-- Create view for system health overview
CREATE OR REPLACE VIEW system_health_overview AS
SELECT 
    'profiles' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(last_update) as newest_record
FROM profiles
UNION ALL
SELECT 
    'profile_history' as table_name,
    COUNT(*) as record_count,
    datetime(MIN(timestamp), 'unixepoch') as oldest_record,
    datetime(MAX(timestamp), 'unixepoch') as newest_record
FROM profile_history
UNION ALL
SELECT 
    'long_term_memory' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(updated_at) as newest_record
FROM long_term_memory
UNION ALL
SELECT 
    'user_roles' as table_name,
    COUNT(*) as record_count,
    MIN(granted_at) as oldest_record,
    MAX(granted_at) as newest_record
FROM user_roles
UNION ALL
SELECT 
    'user_sessions' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(last_activity) as newest_record
FROM user_sessions;