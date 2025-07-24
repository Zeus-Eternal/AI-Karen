-- Migration: Create memory_entries table
-- Date: 2025-07-24
-- Creates table used for storing memory metadata per tenant

CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vector_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    query TEXT,
    result JSONB,
    embedding_id VARCHAR(255),
    memory_metadata JSONB DEFAULT '{}',
    ttl TIMESTAMP,
    timestamp INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    ui_source VARCHAR(50),
    conversation_id UUID,
    memory_type VARCHAR(50) DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    importance_score INTEGER DEFAULT 5 CHECK (importance_score >= 1 AND importance_score <= 10),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    ai_generated BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_memory_vector ON memory_entries(vector_id);
CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_ttl ON memory_entries(ttl);
CREATE INDEX IF NOT EXISTS idx_memory_ui_source ON memory_entries(ui_source);
CREATE INDEX IF NOT EXISTS idx_memory_conversation ON memory_entries(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_entries USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance_score);
CREATE INDEX IF NOT EXISTS idx_memory_user_conversation ON memory_entries(user_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_entries(user_id, memory_type);
