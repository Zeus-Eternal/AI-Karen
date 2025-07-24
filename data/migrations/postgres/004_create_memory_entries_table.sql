-- 001_create_memory_entries.sql
-- Date: 2025-07-24
-- Creates table used for storing memory metadata per tenant

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vector_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    query TEXT,
    result JSONB,                                            -- ← store your AI result here
    embedding_id VARCHAR(255),
    memory_metadata JSONB DEFAULT '{}'::JSONB,
    ttl TIMESTAMP,
    timestamp INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    ui_source VARCHAR(50),
    conversation_id UUID,
    memory_type VARCHAR(50) DEFAULT 'general',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    importance_score INTEGER DEFAULT 5 
        CHECK (importance_score >= 1 AND importance_score <= 10),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITHOUT TIME ZONE,
    ai_generated BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_vector     ON memory_entries(vector_id);
CREATE INDEX        IF NOT EXISTS idx_memory_user       ON memory_entries(user_id);
CREATE INDEX        IF NOT EXISTS idx_memory_session    ON memory_entries(session_id);
CREATE INDEX        IF NOT EXISTS idx_memory_created    ON memory_entries(created_at);
CREATE INDEX        IF NOT EXISTS idx_memory_ttl        ON memory_entries(ttl);
CREATE INDEX        IF NOT EXISTS idx_memory_ui_source  ON memory_entries(ui_source);
CREATE INDEX        IF NOT EXISTS idx_memory_conversation ON memory_entries(conversation_id);
CREATE INDEX        IF NOT EXISTS idx_memory_type       ON memory_entries(memory_type);
CREATE INDEX        IF NOT EXISTS idx_memory_tags       ON memory_entries USING GIN (tags);
CREATE INDEX        IF NOT EXISTS idx_memory_importance ON memory_entries(importance_score);
CREATE INDEX        IF NOT EXISTS idx_memory_user_conv  ON memory_entries(user_id, conversation_id);
CREATE INDEX        IF NOT EXISTS idx_memory_user_type  ON memory_entries(user_id, memory_type);
