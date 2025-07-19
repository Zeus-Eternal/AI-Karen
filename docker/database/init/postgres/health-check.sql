-- PostgreSQL Health Check Queries
-- This file contains SQL queries to verify PostgreSQL health and functionality

-- Basic connectivity test
SELECT 'PostgreSQL connection successful' as status, now() as timestamp;

-- Check database size and statistics
SELECT 
    pg_database.datname as database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) as size,
    (SELECT count(*) FROM pg_stat_activity WHERE datname = pg_database.datname) as active_connections
FROM pg_database 
WHERE datname = current_database();

-- Check table existence and row counts
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check extension status
SELECT 
    extname as extension_name,
    extversion as version,
    'installed' as status
FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin');

-- Check recent activity
SELECT 
    'memory' as table_name,
    count(*) as total_rows,
    count(*) FILTER (WHERE timestamp > extract(epoch from now() - interval '1 hour')) as recent_rows
FROM memory
UNION ALL
SELECT 
    'profiles' as table_name,
    count(*) as total_rows,
    count(*) FILTER (WHERE last_update > now() - interval '1 hour') as recent_rows
FROM profiles;

-- Update health status
UPDATE service_health 
SET 
    status = 'healthy',
    last_check = NOW(),
    metadata = jsonb_build_object(
        'last_health_check', now(),
        'database_size', (SELECT pg_size_pretty(pg_database_size(current_database()))),
        'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database())
    )
WHERE service_name = 'postgres';

-- Return final health status
SELECT 
    service_name,
    status,
    last_check,
    metadata
FROM service_health 
WHERE service_name = 'postgres';