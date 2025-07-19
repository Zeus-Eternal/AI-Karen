-- Enhanced memory table structure for better performance and functionality
-- This migration enhances the existing memory table with additional fields and constraints

-- Add missing columns to memory table if they don't exist
DO $$ 
BEGIN
    -- Add vector_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='memory' AND column_name='vector_id') THEN
        ALTER TABLE memory ADD COLUMN vector_id BIGINT;
    END IF;
    
    -- Add tenant_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='memory' AND column_name='tenant_id') THEN
        ALTER TABLE memory ADD COLUMN tenant_id VARCHAR;
    END IF;
    
    -- Add session_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='memory' AND column_name='session_id') THEN
        ALTER TABLE memory ADD COLUMN session_id VARCHAR;
    END IF;
END $$;

-- Create unique constraint on vector_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'memory_vector_id_unique') THEN
        ALTER TABLE memory ADD CONSTRAINT memory_vector_id_unique UNIQUE (vector_id);
    END IF;
END $$;

-- Create additional indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_memory_vector_id ON memory(vector_id);
CREATE INDEX IF NOT EXISTS idx_memory_user_tenant ON memory(user_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_memory_session_timestamp ON memory(session_id, timestamp);

-- Create a view for recent memory entries
CREATE OR REPLACE VIEW recent_memory AS
SELECT 
    vector_id,
    tenant_id,
    user_id,
    session_id,
    query,
    result,
    timestamp,
    to_timestamp(timestamp) as timestamp_readable
FROM memory 
WHERE timestamp > extract(epoch from now() - interval '7 days')
ORDER BY timestamp DESC;

-- Create a function to clean old memory entries
CREATE OR REPLACE FUNCTION cleanup_old_memory(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_timestamp BIGINT;
BEGIN
    -- Calculate cutoff timestamp
    cutoff_timestamp := extract(epoch from now() - (days_to_keep || ' days')::interval);
    
    -- Delete old entries
    DELETE FROM memory WHERE timestamp < cutoff_timestamp;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    INSERT INTO service_health (service_name, status, metadata) 
    VALUES ('postgres_cleanup', 'completed', 
            jsonb_build_object('deleted_entries', deleted_count, 'cutoff_days', days_to_keep, 'cleanup_time', now()))
    ON CONFLICT (service_name) DO UPDATE SET 
        status = EXCLUDED.status,
        last_check = NOW(),
        metadata = EXCLUDED.metadata;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;