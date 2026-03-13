-- Create rate limiting table for chat API
-- This table tracks API requests per user for rate limiting

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(255) DEFAULT '/api/ai/chat'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_time ON rate_limits(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rate_limits_created_at ON rate_limits(created_at);

-- Clean up old entries (older than 1 hour)
DELETE FROM rate_limits WHERE created_at < NOW() - INTERVAL '1 hour';

-- Add comments
COMMENT ON TABLE rate_limits IS 'Rate limiting table for chat API requests';
COMMENT ON COLUMN rate_limits.user_id IS 'User identifier for rate limiting';
COMMENT ON COLUMN rate_limits.created_at IS 'Timestamp of the request';
COMMENT ON COLUMN rate_limits.ip_address IS 'IP address of the requester';
COMMENT ON COLUMN rate_limits.user_agent IS 'User agent string of the requester';
COMMENT ON COLUMN rate_limits.endpoint IS 'API endpoint that was called';