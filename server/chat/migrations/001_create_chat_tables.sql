-- Migration: Create production chat system tables
-- Date: 2025-12-22
-- Creates tables for the new production chat system

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Chat Conversations Table
CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider_id VARCHAR(50),
    model_used VARCHAR(100),
    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    is_archived BOOLEAN DEFAULT FALSE
);

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider_id VARCHAR(50),
    model_used VARCHAR(100),
    token_count INTEGER,
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    parent_message_id UUID REFERENCES chat_messages(id),
    is_streaming BOOLEAN DEFAULT FALSE,
    streaming_completed_at TIMESTAMP WITH TIME ZONE
);

-- Provider Configurations Table
CREATE TABLE IF NOT EXISTS chat_provider_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    provider_id VARCHAR(50) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Sessions Table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Message Attachments Table
CREATE TABLE IF NOT EXISTS message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id_updated_at ON chat_conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id_created_at ON chat_messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role_created_at ON chat_messages(role, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_provider_configurations_user_active ON chat_provider_configurations(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_token ON chat_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_activity ON chat_sessions(user_id, last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_attachments_message_id ON message_attachments(message_id);

-- Full-text Search Indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_content_fts ON chat_messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_chat_conversations_title_fts ON chat_conversations USING gin(to_tsvector('english', title));

-- Add comments for documentation
COMMENT ON TABLE chat_conversations IS 'Production chat system conversations with multi-LLM support';
COMMENT ON TABLE chat_messages IS 'Individual messages within chat conversations with streaming support';
COMMENT ON TABLE chat_provider_configurations IS 'User-specific LLM provider configurations';
COMMENT ON TABLE chat_sessions IS 'Active chat session tracking for real-time features';
COMMENT ON TABLE message_attachments IS 'File attachments for chat messages';

-- Add column comments
COMMENT ON COLUMN chat_conversations.metadata IS 'Conversation-level metadata and settings';
COMMENT ON COLUMN chat_messages.metadata IS 'Message-level metadata including token usage and performance metrics';
COMMENT ON COLUMN chat_messages.is_streaming IS 'Indicates if message was streamed';
COMMENT ON COLUMN chat_messages.streaming_completed_at IS 'Timestamp when streaming completed';
COMMENT ON COLUMN chat_provider_configurations.config IS 'Encrypted provider-specific configuration';
COMMENT ON COLUMN chat_sessions.metadata IS 'Session-level metadata and UI state';
COMMENT ON COLUMN message_attachments.metadata IS 'File metadata and processing status';