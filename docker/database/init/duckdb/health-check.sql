-- DuckDB Health Check Queries
-- This file contains SQL queries to verify DuckDB health and functionality

-- Basic connectivity and version check
SELECT 'DuckDB connection successful' as status, CURRENT_TIMESTAMP as timestamp;

-- Check database file size and basic stats
SELECT 
    'duckdb' as database_type,
    COUNT(*) as total_tables
FROM information_schema.tables 
WHERE table_schema = 'main';

-- Check table existence and row counts
SELECT 
    table_name,
    'exists' as status
FROM information_schema.tables 
WHERE table_schema = 'main' 
AND table_name IN ('profiles', 'profile_history', 'long_term_memory', 'user_roles', 'user_sessions')
ORDER BY table_name;

-- Check recent activity across all tables
SELECT 
    'profiles' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE last_update > CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_rows
FROM profiles
UNION ALL
SELECT 
    'profile_history' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE datetime(timestamp, 'unixepoch') > CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_rows
FROM profile_history
UNION ALL
SELECT 
    'long_term_memory' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_rows
FROM long_term_memory
UNION ALL
SELECT 
    'user_roles' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE granted_at > CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_rows
FROM user_roles
UNION ALL
SELECT 
    'user_sessions' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE last_activity > CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_rows
FROM user_sessions;

-- Check view availability
SELECT 
    table_name as view_name,
    'available' as status
FROM information_schema.tables 
WHERE table_schema = 'main' 
AND table_type = 'VIEW'
ORDER BY table_name;

-- Update health status
UPDATE service_health 
SET 
    status = 'healthy',
    last_check = CURRENT_TIMESTAMP,
    metadata = '{"last_health_check": "' || CURRENT_TIMESTAMP || '", "tables_verified": true}'
WHERE service_name = 'duckdb';

-- Return final health status
SELECT 
    service_name,
    status,
    last_check,
    metadata
FROM service_health 
WHERE service_name = 'duckdb';