-- AI Karen Complete Database Schema
-- Multi-tenant PostgreSQL schema for AI Karen platform
-- Generated: 2025-08-03

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS plugin_executions CASCADE;
DROP TABLE IF EXISTS memory_entries CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS email_verification_tokens CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- Create tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'basic',
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tenants
CREATE INDEX idx_tenant_slug ON tenants(slug);
CREATE INDEX idx_tenant_active ON tenants(is_active);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    roles TEXT[] DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users
CREATE INDEX idx_user_tenant ON users(tenant_id);
CREATE INDEX idx_user_email ON users(email);
CREATE UNIQUE INDEX idx_user_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_user_active ON users(is_active);

-- Create user_sessions table for authentication
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for user_sessions
CREATE INDEX idx_session_user ON user_sessions(user_id);
CREATE INDEX idx_session_token ON user_sessions(session_token);
CREATE INDEX idx_session_expires ON user_sessions(expires_at);
CREATE INDEX idx_session_active ON user_sessions(is_active);

-- Create password_reset_tokens table
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    used_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for password_reset_tokens
CREATE INDEX idx_reset_token_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_token ON password_reset_tokens(token);
CREATE INDEX idx_reset_expires ON password_reset_tokens(expires_at);

-- Create email_verification_tokens table
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for email_verification_tokens
CREATE INDEX idx_verify_token_user ON email_verification_tokens(user_id);
CREATE INDEX idx_verify_token ON email_verification_tokens(token);
CREATE INDEX idx_verify_expires ON email_verification_tokens(expires_at);

-- Create conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255),
    messages JSONB DEFAULT '[]',
    conversation_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Web UI integration fields
    session_id VARCHAR(255),
    ui_context JSONB DEFAULT '{}',
    ai_insights JSONB DEFAULT '{}',
    user_settings JSONB DEFAULT '{}',
    summary TEXT,
    tags TEXT[] DEFAULT '{}',
    last_ai_response_id VARCHAR(255),

    -- Conversation management fields
    status VARCHAR(50) DEFAULT 'active',
    priority VARCHAR(50) DEFAULT 'normal',
    context_memories JSONB DEFAULT '[]',
    proactive_suggestions TEXT[] DEFAULT '{}',

    -- Performance and analytics fields
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITHOUT TIME ZONE,
    total_tokens_used INTEGER DEFAULT 0,
    average_response_time_ms INTEGER DEFAULT 0
);

-- Create indexes for conversations
CREATE INDEX idx_conversation_user ON conversations(user_id);
CREATE INDEX idx_conversation_created ON conversations(created_at);
CREATE INDEX idx_conversation_active ON conversations(is_active);
CREATE INDEX idx_conversation_session ON conversations(session_id);
CREATE INDEX idx_conversation_tags ON conversations USING GIN(tags);
CREATE INDEX idx_conversation_user_session ON conversations(user_id, session_id);
CREATE INDEX idx_conversation_status ON conversations(status);
CREATE INDEX idx_conversation_priority ON conversations(priority);
CREATE INDEX idx_conversation_last_message ON conversations(last_message_at);

-- Create memory_entries table
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vector_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    query TEXT,
    result JSONB,
    embedding_id VARCHAR(255),
    memory_metadata JSONB DEFAULT '{}',
    ttl TIMESTAMP WITHOUT TIME ZONE,
    timestamp INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Web UI integration fields
    ui_source VARCHAR(50),
    conversation_id UUID,
    memory_type VARCHAR(50) DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    importance_score INTEGER DEFAULT 5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITHOUT TIME ZONE,
    ai_generated BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT TRUE,

    -- Memory classification fields
    category VARCHAR(100),
    subcategory VARCHAR(100),
    confidence_score FLOAT DEFAULT 0.0,
    source_type VARCHAR(50) DEFAULT 'user_input',

    -- Memory relationships
    parent_memory_id UUID,
    related_memory_ids UUID[] DEFAULT '{}',

    -- Performance fields
    retrieval_count INTEGER DEFAULT 0,
    last_retrieved TIMESTAMP WITHOUT TIME ZONE,
    effectiveness_score FLOAT DEFAULT 0.0
);

-- Create indexes for memory_entries
CREATE INDEX idx_memory_vector ON memory_entries(vector_id);
CREATE INDEX idx_memory_user ON memory_entries(user_id);
CREATE INDEX idx_memory_session ON memory_entries(session_id);
CREATE INDEX idx_memory_created ON memory_entries(created_at);
CREATE INDEX idx_memory_ttl ON memory_entries(ttl);
CREATE INDEX idx_memory_ui_source ON memory_entries(ui_source);
CREATE INDEX idx_memory_conversation ON memory_entries(conversation_id);
CREATE INDEX idx_memory_type ON memory_entries(memory_type);
CREATE INDEX idx_memory_tags ON memory_entries USING GIN(tags);
CREATE INDEX idx_memory_importance ON memory_entries(importance_score);
CREATE INDEX idx_memory_user_conversation ON memory_entries(user_id, conversation_id);
CREATE INDEX idx_memory_user_type ON memory_entries(user_id, memory_type);
CREATE INDEX idx_memory_category ON memory_entries(category);
CREATE INDEX idx_memory_access_count ON memory_entries(access_count);
CREATE INDEX idx_memory_effectiveness ON memory_entries(effectiveness_score);

-- Create plugin_executions table
CREATE TABLE plugin_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    plugin_version VARCHAR(50),
    execution_data JSONB DEFAULT '{}',
    result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,

    -- Plugin execution context
    conversation_id UUID,
    session_id VARCHAR(255),
    trigger_type VARCHAR(50) DEFAULT 'manual',

    -- Resource usage tracking
    memory_usage_mb INTEGER,
    cpu_usage_percent FLOAT,
    network_requests INTEGER DEFAULT 0,

    -- Plugin metadata
    plugin_metadata JSONB DEFAULT '{}',
    execution_context JSONB DEFAULT '{}',

    -- Retry and failure handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    failure_reason TEXT,

    -- Performance metrics
    queue_time_ms INTEGER,
    processing_time_ms INTEGER,
    total_time_ms INTEGER
);

-- Create indexes for plugin_executions
CREATE INDEX idx_plugin_user ON plugin_executions(user_id);
CREATE INDEX idx_plugin_name ON plugin_executions(plugin_name);
CREATE INDEX idx_plugin_status ON plugin_executions(status);
CREATE INDEX idx_plugin_created ON plugin_executions(created_at);
CREATE INDEX idx_plugin_conversation ON plugin_executions(conversation_id);
CREATE INDEX idx_plugin_session ON plugin_executions(session_id);
CREATE INDEX idx_plugin_trigger ON plugin_executions(trigger_type);
CREATE INDEX idx_plugin_execution_time ON plugin_executions(execution_time_ms);
CREATE INDEX idx_plugin_user_name ON plugin_executions(user_id, plugin_name);

-- Create hooks table
CREATE TABLE hooks (
    hook_id TEXT PRIMARY KEY,
    hook_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_name TEXT,
    priority INT DEFAULT 50,
    enabled BOOLEAN DEFAULT TRUE,
    conditions JSONB,
    registered_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create hook_exec_stats table
CREATE TABLE hook_exec_stats (
    id BIGSERIAL PRIMARY KEY,
    hook_type TEXT,
    source_name TEXT,
    executions BIGINT DEFAULT 0,
    successes BIGINT DEFAULT 0,
    errors BIGINT DEFAULT 0,
    timeouts BIGINT DEFAULT 0,
    avg_duration_ms INT DEFAULT 0,
    window_start TIMESTAMP WITHOUT TIME ZONE,
    window_end TIMESTAMP WITHOUT TIME ZONE
);

-- Create indexes for hook_exec_stats
CREATE INDEX idx_hook_exec_stats_type_window ON hook_exec_stats(hook_type, window_start);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    correlation_id VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Audit context
    session_id VARCHAR(255),
    tenant_id UUID,

    -- Request/Response tracking
    request_method VARCHAR(10),
    request_path TEXT,
    response_status INTEGER,
    response_time_ms INTEGER,

    -- Security context
    authentication_method VARCHAR(50),
    authorization_level VARCHAR(50),
    risk_score INTEGER DEFAULT 0,

    -- Compliance fields
    data_classification VARCHAR(50),
    retention_period_days INTEGER DEFAULT 2555, -- 7 years default

    -- Geolocation
    country_code VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100)
);

-- Create indexes for audit_logs
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
CREATE INDEX idx_audit_correlation ON audit_logs(correlation_id);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_session ON audit_logs(session_id);
CREATE INDEX idx_audit_ip ON audit_logs(ip_address);
CREATE INDEX idx_audit_risk ON audit_logs(risk_score);

-- Create additional tables for advanced features

-- Chat memories table (for conversation context)
CREATE TABLE chat_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    importance_score INTEGER DEFAULT 5,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE,

    -- Memory relationships
    parent_id UUID,
    thread_id UUID,

    -- AI processing
    embedding_vector FLOAT[],
    similarity_threshold FLOAT DEFAULT 0.7,

    -- Usage tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITHOUT TIME ZONE
);

-- Create indexes for chat_memories
CREATE INDEX idx_chat_memory_conversation ON chat_memories(conversation_id);
CREATE INDEX idx_chat_memory_user ON chat_memories(user_id);
CREATE INDEX idx_chat_memory_type ON chat_memories(memory_type);
CREATE INDEX idx_chat_memory_importance ON chat_memories(importance_score);
CREATE INDEX idx_chat_memory_created ON chat_memories(created_at);
CREATE INDEX idx_chat_memory_expires ON chat_memories(expires_at);

-- AI model registry table
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- llm, embedding, classification, etc.
    configuration JSONB DEFAULT '{}',
    capabilities TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Performance metrics
    average_response_time_ms INTEGER,
    success_rate FLOAT DEFAULT 1.0,
    cost_per_token FLOAT DEFAULT 0.0,

    -- Model metadata
    context_window INTEGER,
    max_tokens INTEGER,
    supports_streaming BOOLEAN DEFAULT FALSE,
    supports_functions BOOLEAN DEFAULT FALSE
);

-- Create indexes for ai_models
CREATE INDEX idx_ai_model_name ON ai_models(name);
CREATE INDEX idx_ai_model_provider ON ai_models(provider);
CREATE INDEX idx_ai_model_type ON ai_models(model_type);
CREATE INDEX idx_ai_model_active ON ai_models(is_active);
CREATE UNIQUE INDEX idx_ai_model_name_version ON ai_models(name, version);

-- System configuration table
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(100),
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID
);

-- Create indexes for system_config
CREATE INDEX idx_config_key ON system_config(key);
CREATE INDEX idx_config_category ON system_config(category);
CREATE INDEX idx_config_sensitive ON system_config(is_sensitive);

-- Analytics and metrics table
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    user_id UUID,
    session_id VARCHAR(255),
    conversation_id UUID,
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Event context
    ui_source VARCHAR(50),
    user_agent TEXT,
    ip_address INET,

    -- Performance data
    response_time_ms INTEGER,
    tokens_used INTEGER,
    cost_cents INTEGER,

    -- A/B testing
    experiment_id VARCHAR(255),
    variant VARCHAR(100),

    -- Geolocation
    country_code VARCHAR(2),
    timezone VARCHAR(50)
);

-- Create indexes for analytics_events
CREATE INDEX idx_analytics_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_user ON analytics_events(user_id);
CREATE INDEX idx_analytics_session ON analytics_events(session_id);
CREATE INDEX idx_analytics_conversation ON analytics_events(conversation_id);
CREATE INDEX idx_analytics_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_ui_source ON analytics_events(ui_source);
CREATE INDEX idx_analytics_experiment ON analytics_events(experiment_id);

-- Feature flags table
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INTEGER DEFAULT 0,
    target_users UUID[] DEFAULT '{}',
    target_tenants UUID[] DEFAULT '{}',
    conditions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    -- Feature flag metadata
    environment VARCHAR(50) DEFAULT 'production',
    category VARCHAR(100),
    priority INTEGER DEFAULT 0
);

-- Create indexes for feature_flags
CREATE INDEX idx_feature_flag_name ON feature_flags(name);
CREATE INDEX idx_feature_flag_enabled ON feature_flags(is_enabled);
CREATE INDEX idx_feature_flag_environment ON feature_flags(environment);
CREATE INDEX idx_feature_flag_category ON feature_flags(category);

-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE,

    -- Notification delivery
    delivery_method VARCHAR(50) DEFAULT 'in_app',
    delivery_status VARCHAR(50) DEFAULT 'pending',
    delivered_at TIMESTAMP WITHOUT TIME ZONE,

    -- Notification context
    source_type VARCHAR(100),
    source_id VARCHAR(255),
    priority INTEGER DEFAULT 0,

    -- Actions
    action_url TEXT,
    action_label VARCHAR(100)
);

-- Create indexes for notifications
CREATE INDEX idx_notification_user ON notifications(user_id);
CREATE INDEX idx_notification_type ON notifications(type);
CREATE INDEX idx_notification_read ON notifications(is_read);
CREATE INDEX idx_notification_created ON notifications(created_at);
CREATE INDEX idx_notification_expires ON notifications(expires_at);
CREATE INDEX idx_notification_priority ON notifications(priority);

-- Insert default tenant and anonymous user
INSERT INTO tenants (id, name, slug, subscription_tier, settings, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default Tenant',
    'default',
    'enterprise',
    '{"features": ["all"], "limits": {"conversations": -1, "memory_entries": -1}}',
    TRUE
) ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, tenant_id, email, roles, preferences, is_active, is_verified)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'anonymous@ai-karen.local',
    ARRAY['user'],
    '{"ui_theme": "auto", "language": "en", "timezone": "UTC"}',
    TRUE,
    TRUE
) ON CONFLICT (id) DO NOTHING;

-- Insert default AI models
INSERT INTO ai_models (name, version, provider, model_type, configuration, capabilities, is_active) VALUES
('gpt-4', '2024-04-09', 'openai', 'llm', '{"temperature": 0.7, "max_tokens": 4096}', ARRAY['chat', 'completion', 'functions'], TRUE),
('gpt-3.5-turbo', '2024-01-25', 'openai', 'llm', '{"temperature": 0.7, "max_tokens": 4096}', ARRAY['chat', 'completion', 'functions'], TRUE),
('text-embedding-ada-002', '2', 'openai', 'embedding', '{"dimensions": 1536}', ARRAY['embedding'], TRUE),
('llama3.2:1b', '1b', 'ollama', 'llm', '{"temperature": 0.7, "context_window": 8192}', ARRAY['chat', 'completion'], TRUE),
('distilbert-base-uncased', 'base', 'huggingface', 'classification', '{}', ARRAY['classification', 'sentiment'], TRUE)
ON CONFLICT (name, version) DO NOTHING;

-- Insert default system configuration
INSERT INTO system_config (key, value, description, category) VALUES
('app.name', '"AI Karen"', 'Application name', 'general'),
('app.version', '"1.0.0"', 'Application version', 'general'),
('features.web_ui_enabled', 'true', 'Enable web UI interface', 'features'),
('features.memory_enabled', 'true', 'Enable memory system', 'features'),
('features.plugins_enabled', 'true', 'Enable plugin system', 'features'),
('limits.max_conversation_length', '1000', 'Maximum messages per conversation', 'limits'),
('limits.max_memory_entries_per_user', '10000', 'Maximum memory entries per user', 'limits'),
('ai.default_model', '"gpt-3.5-turbo"', 'Default AI model for conversations', 'ai'),
('ai.embedding_model', '"text-embedding-ada-002"', 'Default embedding model', 'ai'),
('security.session_timeout_minutes', '60', 'Session timeout in minutes', 'security'),
('security.max_login_attempts', '5', 'Maximum login attempts before lockout', 'security')
ON CONFLICT (key) DO NOTHING;

-- Insert default feature flags
INSERT INTO feature_flags (name, description, is_enabled, environment, category) VALUES
('web_ui_v2', 'Enable new web UI interface', TRUE, 'production', 'ui'),
('advanced_memory', 'Enable advanced memory features', TRUE, 'production', 'memory'),
('plugin_marketplace', 'Enable plugin marketplace', FALSE, 'production', 'plugins'),
('ai_insights', 'Enable AI-generated insights', TRUE, 'production', 'ai'),
('conversation_analytics', 'Enable conversation analytics', TRUE, 'production', 'analytics')
ON CONFLICT (name) DO NOTHING;

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_memory_entries_updated_at BEFORE UPDATE ON memory_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_models_updated_at BEFORE UPDATE ON ai_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_flags_updated_at BEFORE UPDATE ON feature_flags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- Active conversations view
CREATE VIEW active_conversations AS
SELECT
    c.*,
    u.email as user_email,
    t.name as tenant_name
FROM conversations c
JOIN users u ON c.user_id = u.id
JOIN tenants t ON u.tenant_id = t.id
WHERE c.is_active = TRUE;

-- User statistics view
CREATE VIEW user_statistics AS
SELECT
    u.id,
    u.email,
    u.tenant_id,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT m.id) as memory_count,
    COUNT(DISTINCT p.id) as plugin_execution_count,
    MAX(c.updated_at) as last_conversation_at,
    MAX(m.created_at) as last_memory_at
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN memory_entries m ON u.id = m.user_id
LEFT JOIN plugin_executions p ON u.id = p.user_id
GROUP BY u.id, u.email, u.tenant_id;

-- Memory usage by type view
CREATE VIEW memory_usage_by_type AS
SELECT
    memory_type,
    COUNT(*) as entry_count,
    AVG(importance_score) as avg_importance,
    AVG(access_count) as avg_access_count,
    MAX(created_at) as latest_entry
FROM memory_entries
GROUP BY memory_type;

-- Plugin performance view
CREATE VIEW plugin_performance AS
SELECT
    plugin_name,
    COUNT(*) as execution_count,
    AVG(execution_time_ms) as avg_execution_time,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as success_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failure_count,
    (COUNT(CASE WHEN status = 'completed' THEN 1 END)::FLOAT / COUNT(*)::FLOAT * 100) as success_rate
FROM plugin_executions
GROUP BY plugin_name;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_karen_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_karen_app;

-- Create indexes for performance optimization on large datasets
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memory_entries_user_created ON memory_entries(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_desc ON audit_logs(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_timestamp_desc ON analytics_events(timestamp DESC);

-- Add comments for documentation
COMMENT ON TABLE tenants IS 'Multi-tenant isolation and configuration';
COMMENT ON TABLE users IS 'User accounts with tenant association';
COMMENT ON TABLE conversations IS 'AI conversations with full context and metadata';
COMMENT ON TABLE memory_entries IS 'Long-term memory storage with vector embeddings';
COMMENT ON TABLE plugin_executions IS 'Plugin execution tracking and results';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for compliance';
COMMENT ON TABLE analytics_events IS 'User behavior and system performance analytics';
COMMENT ON TABLE ai_models IS 'AI model registry and configuration';
COMMENT ON TABLE system_config IS 'System-wide configuration parameters';
COMMENT ON TABLE feature_flags IS 'Feature flag management for gradual rollouts';
COMMENT ON TABLE notifications IS 'User notification system';

-- Schema version tracking
CREATE TABLE schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
('1.0.0', 'Initial AI Karen database schema with multi-tenant support');

-- Final message
SELECT 'AI Karen database schema created successfully!' as status;
