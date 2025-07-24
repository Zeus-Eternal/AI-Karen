-- Migration: Create conversations table
-- Date: 2025-07-24
-- Creates tenant-specific conversations table

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255),
    messages JSONB DEFAULT '[]',
    conversation_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    session_id VARCHAR(255),
    ui_context JSONB DEFAULT '{}',
    ai_insights JSONB DEFAULT '{}',
    user_settings JSONB DEFAULT '{}',
    summary TEXT,
    tags TEXT[] DEFAULT '{}',
    last_ai_response_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_active ON conversations(is_active);
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_tags ON conversations USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_conversation_user_session ON conversations(user_id, session_id);
