-- Migration: Create plugin_executions table
-- Date: 2025-07-24
-- Stores plugin execution records per tenant

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS plugin_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    execution_data JSONB DEFAULT '{}',
    result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plugin_user ON plugin_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_plugin_name ON plugin_executions(plugin_name);
CREATE INDEX IF NOT EXISTS idx_plugin_status ON plugin_executions(status);
CREATE INDEX IF NOT EXISTS idx_plugin_created ON plugin_executions(created_at);
