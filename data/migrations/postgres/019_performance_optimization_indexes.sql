-- Performance Optimization Migration
-- This migration adds additional indexes and optimizations for the admin management system
-- to improve query performance for role-based queries, audit logs, and bulk operations

-- Enable additional extensions for performance
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Additional indexes for auth_users table for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_role_active ON auth_users(role, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_email_lower ON auth_users(LOWER(email));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_full_name_gin ON auth_users USING gin(to_tsvector('english', COALESCE(full_name, '')));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_last_login ON auth_users(last_login_at DESC NULLS LAST) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_created_at_role ON auth_users(created_at DESC, role) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_tenant_role ON auth_users(tenant_id, role) WHERE is_active = true;

-- Composite indexes for common admin queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_search_composite ON auth_users(
  is_active, role, created_at DESC
) WHERE is_active = true;

-- Partial indexes for specific role queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_admins_only ON auth_users(created_at DESC) 
WHERE role IN ('admin', 'super_admin') AND is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_regular_users ON auth_users(created_at DESC) 
WHERE role = 'user' AND is_active = true;

-- Enhanced audit_logs indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action, timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_resource_composite ON audit_logs(resource_type, resource_id, timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp_action ON audit_logs(timestamp DESC, action);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_ip_timestamp ON audit_logs(ip_address, timestamp DESC) WHERE ip_address IS NOT NULL;

-- GIN index for audit log details JSONB column for fast searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_details_gin ON audit_logs USING gin(details);

-- Partial indexes for recent audit logs (most commonly queried)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_recent ON audit_logs(timestamp DESC, user_id) 
WHERE timestamp >= NOW() - INTERVAL '30 days';

-- System config indexes for caching optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_config_category_key ON system_config(category, key);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_config_updated_at ON system_config(updated_at DESC);

-- Role permissions indexes for permission checking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_role_permissions_composite ON role_permissions(role, permission_id);

-- Create materialized view for user statistics (for dashboard performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS user_statistics AS
SELECT 
  COUNT(*) as total_users,
  COUNT(*) FILTER (WHERE is_active = true) as active_users,
  COUNT(*) FILTER (WHERE role = 'admin') as admin_users,
  COUNT(*) FILTER (WHERE role = 'super_admin') as super_admin_users,
  COUNT(*) FILTER (WHERE is_verified = true) as verified_users,
  COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '24 hours') as daily_active_users,
  COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '7 days') as weekly_active_users,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_users_30d,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_users_7d,
  MAX(last_login_at) as last_user_login,
  MIN(created_at) as first_user_created
FROM auth_users;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_statistics_unique ON user_statistics((1));

-- Create materialized view for audit log statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS audit_statistics AS
SELECT 
  COUNT(*) as total_logs,
  COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '24 hours') as logs_24h,
  COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') as logs_7d,
  COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '30 days') as logs_30d,
  COUNT(DISTINCT user_id) as unique_users,
  COUNT(DISTINCT action) as unique_actions,
  COUNT(DISTINCT resource_type) as unique_resource_types,
  MAX(timestamp) as last_log_time
FROM audit_logs;

-- Create unique index on audit statistics materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_statistics_unique ON audit_statistics((1));

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_admin_statistics()
RETURNS void AS $
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
  REFRESH MATERIALIZED VIEW CONCURRENTLY audit_statistics;
END;
$ LANGUAGE plpgsql;

-- Create function for efficient bulk user operations
CREATE OR REPLACE FUNCTION bulk_update_users(
  p_user_ids UUID[],
  p_updates JSONB,
  p_updated_by UUID
) RETURNS TABLE(updated_count INTEGER) AS $
DECLARE
  update_query TEXT;
  set_clauses TEXT[] := ARRAY[]::TEXT[];
  audit_details JSONB := '{}';
BEGIN
  -- Build dynamic update query based on provided updates
  IF p_updates ? 'is_active' THEN
    set_clauses := array_append(set_clauses, 'is_active = ' || (p_updates->>'is_active')::boolean);
    audit_details := audit_details || jsonb_build_object('is_active', p_updates->>'is_active');
  END IF;
  
  IF p_updates ? 'role' THEN
    set_clauses := array_append(set_clauses, 'role = ' || quote_literal(p_updates->>'role'));
    audit_details := audit_details || jsonb_build_object('role', p_updates->>'role');
  END IF;
  
  IF p_updates ? 'is_verified' THEN
    set_clauses := array_append(set_clauses, 'is_verified = ' || (p_updates->>'is_verified')::boolean);
    audit_details := audit_details || jsonb_build_object('is_verified', p_updates->>'is_verified');
  END IF;
  
  -- Always update the updated_at timestamp
  set_clauses := array_append(set_clauses, 'updated_at = NOW()');
  
  IF array_length(set_clauses, 1) > 1 THEN -- More than just updated_at
    -- Build and execute update query
    update_query := 'UPDATE auth_users SET ' || array_to_string(set_clauses, ', ') || 
                   ' WHERE user_id = ANY($1) AND is_active = true';
    
    EXECUTE update_query USING p_user_ids;
    
    -- Log the bulk operation
    INSERT INTO audit_logs (user_id, action, resource_type, details, timestamp)
    VALUES (
      p_updated_by,
      'user.bulk_update',
      'user',
      audit_details || jsonb_build_object('user_ids', p_user_ids, 'count', array_length(p_user_ids, 1)),
      NOW()
    );
    
    RETURN QUERY SELECT array_length(p_user_ids, 1);
  ELSE
    RETURN QUERY SELECT 0;
  END IF;
END;
$ LANGUAGE plpgsql;

-- Create function for efficient user search with full-text search
CREATE OR REPLACE FUNCTION search_users(
  p_search_term TEXT DEFAULT NULL,
  p_role TEXT DEFAULT NULL,
  p_is_active BOOLEAN DEFAULT NULL,
  p_is_verified BOOLEAN DEFAULT NULL,
  p_limit INTEGER DEFAULT 20,
  p_offset INTEGER DEFAULT 0,
  p_sort_by TEXT DEFAULT 'created_at',
  p_sort_order TEXT DEFAULT 'desc'
) RETURNS TABLE(
  user_id UUID,
  email TEXT,
  full_name TEXT,
  role TEXT,
  is_active BOOLEAN,
  is_verified BOOLEAN,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE,
  last_login_at TIMESTAMP WITH TIME ZONE,
  total_count BIGINT
) AS $
DECLARE
  where_conditions TEXT[] := ARRAY[]::TEXT[];
  order_clause TEXT;
  query_text TEXT;
BEGIN
  -- Build WHERE conditions
  IF p_search_term IS NOT NULL AND p_search_term != '' THEN
    where_conditions := array_append(where_conditions, 
      '(email ILIKE ' || quote_literal('%' || p_search_term || '%') || 
      ' OR full_name ILIKE ' || quote_literal('%' || p_search_term || '%') || 
      ' OR to_tsvector(''english'', COALESCE(full_name, '''')) @@ plainto_tsquery(''english'', ' || quote_literal(p_search_term) || '))');
  END IF;
  
  IF p_role IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'role = ' || quote_literal(p_role));
  END IF;
  
  IF p_is_active IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'is_active = ' || p_is_active);
  END IF;
  
  IF p_is_verified IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'is_verified = ' || p_is_verified);
  END IF;
  
  -- Build ORDER BY clause
  order_clause := 'ORDER BY ' || p_sort_by || ' ' || UPPER(p_sort_order);
  
  -- Build complete query
  query_text := 'SELECT 
    u.user_id,
    u.email,
    u.full_name,
    u.role,
    u.is_active,
    u.is_verified,
    u.created_at,
    u.updated_at,
    u.last_login_at,
    COUNT(*) OVER() as total_count
  FROM auth_users u';
  
  IF array_length(where_conditions, 1) > 0 THEN
    query_text := query_text || ' WHERE ' || array_to_string(where_conditions, ' AND ');
  END IF;
  
  query_text := query_text || ' ' || order_clause || ' LIMIT ' || p_limit || ' OFFSET ' || p_offset;
  
  RETURN QUERY EXECUTE query_text;
END;
$ LANGUAGE plpgsql;

-- Create function for efficient audit log queries with date partitioning support
CREATE OR REPLACE FUNCTION get_audit_logs_optimized(
  p_user_id UUID DEFAULT NULL,
  p_action TEXT DEFAULT NULL,
  p_resource_type TEXT DEFAULT NULL,
  p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
) RETURNS TABLE(
  id UUID,
  user_id UUID,
  action TEXT,
  resource_type TEXT,
  resource_id TEXT,
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  timestamp TIMESTAMP WITH TIME ZONE,
  user_email TEXT,
  user_full_name TEXT,
  total_count BIGINT
) AS $
DECLARE
  where_conditions TEXT[] := ARRAY[]::TEXT[];
  query_text TEXT;
BEGIN
  -- Build WHERE conditions
  IF p_user_id IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'al.user_id = ' || quote_literal(p_user_id));
  END IF;
  
  IF p_action IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'al.action = ' || quote_literal(p_action));
  END IF;
  
  IF p_resource_type IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'al.resource_type = ' || quote_literal(p_resource_type));
  END IF;
  
  IF p_start_date IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'al.timestamp >= ' || quote_literal(p_start_date));
  END IF;
  
  IF p_end_date IS NOT NULL THEN
    where_conditions := array_append(where_conditions, 'al.timestamp <= ' || quote_literal(p_end_date));
  END IF;
  
  -- Build complete query
  query_text := 'SELECT 
    al.id,
    al.user_id,
    al.action,
    al.resource_type,
    al.resource_id,
    al.details,
    al.ip_address,
    al.user_agent,
    al.timestamp,
    u.email as user_email,
    u.full_name as user_full_name,
    COUNT(*) OVER() as total_count
  FROM audit_logs al
  LEFT JOIN auth_users u ON al.user_id = u.user_id';
  
  IF array_length(where_conditions, 1) > 0 THEN
    query_text := query_text || ' WHERE ' || array_to_string(where_conditions, ' AND ');
  END IF;
  
  query_text := query_text || ' ORDER BY al.timestamp DESC LIMIT ' || p_limit || ' OFFSET ' || p_offset;
  
  RETURN QUERY EXECUTE query_text;
END;
$ LANGUAGE plpgsql;

-- Create indexes for password hashes table if it exists
DO $
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_password_hashes') THEN
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_password_hashes_user_id ON auth_password_hashes(user_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_password_hashes_created_at ON auth_password_hashes(created_at DESC);
  END IF;
END $;

-- Create indexes for sessions table if it exists
DO $
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_sessions') THEN
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(user_id, expires_at) WHERE expires_at > NOW();
  END IF;
END $;

-- Create function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_admin_query_performance()
RETURNS TABLE(
  query TEXT,
  calls BIGINT,
  total_time DOUBLE PRECISION,
  mean_time DOUBLE PRECISION,
  rows BIGINT
) AS $
BEGIN
  RETURN QUERY
  SELECT 
    pss.query,
    pss.calls,
    pss.total_time,
    pss.mean_time,
    pss.rows
  FROM pg_stat_statements pss
  WHERE pss.query ILIKE '%auth_users%' 
     OR pss.query ILIKE '%audit_logs%'
     OR pss.query ILIKE '%system_config%'
  ORDER BY pss.total_time DESC
  LIMIT 20;
END;
$ LANGUAGE plpgsql;

-- Create function to get table statistics
CREATE OR REPLACE FUNCTION get_admin_table_stats()
RETURNS TABLE(
  table_name TEXT,
  row_count BIGINT,
  table_size TEXT,
  index_size TEXT,
  total_size TEXT
) AS $
BEGIN
  RETURN QUERY
  SELECT 
    t.table_name::TEXT,
    t.n_tup_ins - t.n_tup_del as row_count,
    pg_size_pretty(pg_total_relation_size(c.oid) - pg_indexes_size(c.oid)) as table_size,
    pg_size_pretty(pg_indexes_size(c.oid)) as index_size,
    pg_size_pretty(pg_total_relation_size(c.oid)) as total_size
  FROM pg_stat_user_tables t
  JOIN pg_class c ON c.relname = t.relname
  WHERE t.relname IN ('auth_users', 'audit_logs', 'system_config', 'permissions', 'role_permissions')
  ORDER BY pg_total_relation_size(c.oid) DESC;
END;
$ LANGUAGE plpgsql;

-- Schedule automatic statistics refresh (requires pg_cron extension)
-- This is optional and only works if pg_cron is installed
DO $
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    -- Refresh statistics every hour
    PERFORM cron.schedule('refresh-admin-stats', '0 * * * *', 'SELECT refresh_admin_statistics();');
    
    -- Analyze tables every 6 hours for better query planning
    PERFORM cron.schedule('analyze-admin-tables', '0 */6 * * *', 
      'ANALYZE auth_users; ANALYZE audit_logs; ANALYZE system_config;');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    -- Ignore errors if pg_cron is not available
    NULL;
END $;

-- Verify the performance optimization migration
DO $
DECLARE
  index_count INTEGER;
  materialized_view_count INTEGER;
  function_count INTEGER;
BEGIN
  -- Count new indexes
  SELECT COUNT(*) INTO index_count
  FROM pg_indexes 
  WHERE indexname LIKE 'idx_auth_users_%' 
     OR indexname LIKE 'idx_audit_logs_%'
     OR indexname LIKE 'idx_system_config_%';
  
  -- Count materialized views
  SELECT COUNT(*) INTO materialized_view_count
  FROM pg_matviews 
  WHERE matviewname IN ('user_statistics', 'audit_statistics');
  
  -- Count new functions
  SELECT COUNT(*) INTO function_count
  FROM pg_proc p
  JOIN pg_namespace n ON p.pronamespace = n.oid
  WHERE n.nspname = 'public' 
    AND p.proname IN ('refresh_admin_statistics', 'bulk_update_users', 'search_users', 'get_audit_logs_optimized');
  
  RAISE NOTICE 'Performance optimization verification:';
  RAISE NOTICE 'New indexes created: %', index_count;
  RAISE NOTICE 'Materialized views created: %', materialized_view_count;
  RAISE NOTICE 'Performance functions created: %', function_count;
  
  IF index_count >= 10 AND materialized_view_count = 2 AND function_count = 4 THEN
    RAISE NOTICE 'SUCCESS: Performance optimization migration completed successfully!';
  ELSE
    RAISE NOTICE 'WARNING: Performance optimization migration may not have completed successfully!';
  END IF;
END $;

COMMIT;