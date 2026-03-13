-- Add security fields to chat models
-- This migration adds security tracking, audit logging, and enhanced access control

-- Add security fields to conversations
ALTER TABLE chat_conversations 
ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN security_level VARCHAR(20) DEFAULT 'medium',
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN created_by_ip VARCHAR(45),
ADD COLUMN last_modified_by VARCHAR(255);

-- Add indexes for conversation security
CREATE INDEX idx_chat_conversations_security_level ON chat_conversations(security_level);
CREATE INDEX idx_chat_conversations_last_accessed ON chat_conversations(last_accessed_at DESC);
CREATE INDEX idx_chat_conversations_created_by_ip ON chat_conversations(created_by_ip);

-- Add security fields to messages
ALTER TABLE chat_messages 
ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN is_sanitized BOOLEAN DEFAULT FALSE,
ADD COLUMN threat_level VARCHAR(20) DEFAULT 'low',
ADD COLUMN content_hash VARCHAR(64),
ADD COLUMN moderation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN moderation_flags JSONB DEFAULT '{}',
ADD COLUMN created_by_ip VARCHAR(45),
ADD COLUMN user_agent VARCHAR(500);

-- Add indexes for message security
CREATE INDEX idx_chat_messages_threat_level ON chat_messages(threat_level);
CREATE INDEX idx_chat_messages_moderation_status ON chat_messages(moderation_status);
CREATE INDEX idx_chat_messages_content_hash ON chat_messages(content_hash);
CREATE INDEX idx_chat_messages_created_by_ip ON chat_messages(created_by_ip);

-- Add security fields to provider configurations
ALTER TABLE chat_provider_configurations 
ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN security_level VARCHAR(20) DEFAULT 'medium',
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN created_by_ip VARCHAR(45),
ADD COLUMN last_modified_by VARCHAR(255),
ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN approval_notes TEXT;

-- Add indexes for provider configuration security
CREATE INDEX idx_chat_provider_configurations_security_level ON chat_provider_configurations(security_level);
CREATE INDEX idx_chat_provider_configurations_approval_status ON chat_provider_configurations(approval_status);
CREATE INDEX idx_chat_provider_configurations_last_accessed ON chat_provider_configurations(last_accessed_at DESC);

-- Add security fields to sessions
ALTER TABLE chat_sessions 
ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN security_level VARCHAR(20) DEFAULT 'medium',
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN created_by_ip VARCHAR(45),
ADD COLUMN user_agent VARCHAR(500),
ADD COLUMN session_fingerprint VARCHAR(64),
ADD COLUMN is_suspicious BOOLEAN DEFAULT FALSE,
ADD COLUMN threat_score INTEGER DEFAULT 0,
ADD COLUMN termination_reason VARCHAR(100);

-- Add indexes for session security
CREATE INDEX idx_chat_sessions_security_level ON chat_sessions(security_level);
CREATE INDEX idx_chat_sessions_is_suspicious ON chat_sessions(is_suspicious);
CREATE INDEX idx_chat_sessions_fingerprint ON chat_sessions(session_fingerprint);
CREATE INDEX idx_chat_sessions_threat_score ON chat_sessions(threat_score DESC);
CREATE INDEX idx_chat_sessions_last_accessed ON chat_sessions(last_accessed_at DESC);

-- Add security fields to attachments
ALTER TABLE message_attachments 
ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE,
ADD COLUMN is_scanned BOOLEAN DEFAULT FALSE,
ADD COLUMN scan_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN scan_result JSONB DEFAULT '{}',
ADD COLUMN content_hash VARCHAR(64),
ADD COLUMN quarantine_reason VARCHAR(255),
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN uploaded_by_ip VARCHAR(45);

-- Add indexes for attachment security
CREATE INDEX idx_message_attachments_scan_status ON message_attachments(scan_status);
CREATE INDEX idx_message_attachments_is_encrypted ON message_attachments(is_encrypted);
CREATE INDEX idx_message_attachments_content_hash ON message_attachments(content_hash);
CREATE INDEX idx_message_attachments_last_accessed ON message_attachments(last_accessed_at DESC);

-- Create security audit table
CREATE TABLE chat_security_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES auth_users(user_id),
    conversation_id UUID REFERENCES chat_conversations(id),
    message_id UUID REFERENCES chat_messages(id),
    session_id UUID REFERENCES chat_sessions(id),
    provider_id VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    threat_level VARCHAR(20) NOT NULL,
    details JSONB DEFAULT '{}',
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit table
CREATE INDEX idx_chat_security_audit_event_timestamp ON chat_security_audit(event_timestamp DESC);
CREATE INDEX idx_chat_security_audit_event_type ON chat_security_audit(event_type);
CREATE INDEX idx_chat_security_audit_user_id ON chat_security_audit(user_id);
CREATE INDEX idx_chat_security_audit_threat_level ON chat_security_audit(threat_level);
CREATE INDEX idx_chat_security_audit_resolved ON chat_security_audit(resolved);

-- Create security metrics table
CREATE TABLE chat_security_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES auth_users(user_id),
    provider_id VARCHAR(50),
    value NUMERIC NOT NULL,
    unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for metrics table
CREATE INDEX idx_chat_security_metrics_metric_timestamp ON chat_security_metrics(metric_timestamp DESC);
CREATE INDEX idx_chat_security_metrics_metric_type ON chat_security_metrics(metric_type);
CREATE INDEX idx_chat_security_metrics_user_id ON chat_security_metrics(user_id);

-- Create security alerts table
CREATE TABLE chat_security_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES auth_users(user_id),
    conversation_id UUID REFERENCES chat_conversations(id),
    session_id UUID REFERENCES chat_sessions(id),
    provider_id VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for alerts table
CREATE INDEX idx_chat_security_alerts_alert_timestamp ON chat_security_alerts(alert_timestamp DESC);
CREATE INDEX idx_chat_security_alerts_alert_type ON chat_security_alerts(alert_type);
CREATE INDEX idx_chat_security_alerts_severity ON chat_security_alerts(severity);
CREATE INDEX idx_chat_security_alerts_status ON chat_security_alerts(status);
CREATE INDEX idx_chat_security_alerts_resolved ON chat_security_alerts(resolved);

-- Add comments to document the security enhancements
COMMENT ON TABLE chat_conversations IS 'Enhanced with security tracking fields';
COMMENT ON TABLE chat_messages IS 'Enhanced with content validation and moderation fields';
COMMENT ON TABLE chat_provider_configurations IS 'Enhanced with security and approval tracking';
COMMENT ON TABLE chat_sessions IS 'Enhanced with security monitoring and threat detection';
COMMENT ON TABLE message_attachments IS 'Enhanced with security scanning and quarantine support';
COMMENT ON TABLE chat_security_audit IS 'Security event audit log for chat system';
COMMENT ON TABLE chat_security_metrics IS 'Security metrics collection for chat system';
COMMENT ON TABLE chat_security_alerts IS 'Security alerts for chat system';