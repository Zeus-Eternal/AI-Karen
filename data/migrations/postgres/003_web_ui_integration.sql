-- Migration: Add Web UI integration fields to existing tables
-- Date: 2025-01-19
-- Description: Extends TenantConversation and TenantMemoryEntry models with web UI specific fields

-- Add new fields to conversations table
ALTER TABLE conversations 
ADD COLUMN session_id VARCHAR(255),
ADD COLUMN ui_context JSONB DEFAULT '{}',
ADD COLUMN ai_insights JSONB DEFAULT '{}',
ADD COLUMN user_settings JSONB DEFAULT '{}',
ADD COLUMN summary TEXT,
ADD COLUMN tags TEXT[] DEFAULT '{}',
ADD COLUMN last_ai_response_id VARCHAR(255);

-- Add indexes for conversations table new fields
CREATE INDEX idx_conversation_session ON conversations(session_id);
CREATE INDEX idx_conversation_tags ON conversations USING GIN(tags);
CREATE INDEX idx_conversation_user_session ON conversations(user_id, session_id);

-- Add new fields to memory_entries table
ALTER TABLE memory_entries
ADD COLUMN ui_source VARCHAR(50),
ADD COLUMN conversation_id UUID,
ADD COLUMN memory_type VARCHAR(50) DEFAULT 'general',
ADD COLUMN tags TEXT[] DEFAULT '{}',
ADD COLUMN importance_score INTEGER DEFAULT 5,
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN last_accessed TIMESTAMP,
ADD COLUMN ai_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN user_confirmed BOOLEAN DEFAULT TRUE;

-- Add indexes for memory_entries table new fields
CREATE INDEX idx_memory_ui_source ON memory_entries(ui_source);
CREATE INDEX idx_memory_conversation ON memory_entries(conversation_id);
CREATE INDEX idx_memory_type ON memory_entries(memory_type);
CREATE INDEX idx_memory_tags ON memory_entries USING GIN(tags);
CREATE INDEX idx_memory_importance ON memory_entries(importance_score);
CREATE INDEX idx_memory_user_conversation ON memory_entries(user_id, conversation_id);
CREATE INDEX idx_memory_user_type ON memory_entries(user_id, memory_type);

-- Add constraints for importance_score (1-10 range)
ALTER TABLE memory_entries 
ADD CONSTRAINT chk_importance_score CHECK (importance_score >= 1 AND importance_score <= 10);

-- Add comments for documentation
COMMENT ON COLUMN conversations.session_id IS 'Session tracking for web UI';
COMMENT ON COLUMN conversations.ui_context IS 'Web UI specific context data';
COMMENT ON COLUMN conversations.ai_insights IS 'AI-generated insights and metadata';
COMMENT ON COLUMN conversations.user_settings IS 'User settings snapshot for this conversation';
COMMENT ON COLUMN conversations.summary IS 'Conversation summary';
COMMENT ON COLUMN conversations.tags IS 'Conversation tags for organization';
COMMENT ON COLUMN conversations.last_ai_response_id IS 'Track last AI response for continuity';

COMMENT ON COLUMN memory_entries.ui_source IS 'Source UI (web, desktop)';
COMMENT ON COLUMN memory_entries.conversation_id IS 'Link to conversation';
COMMENT ON COLUMN memory_entries.memory_type IS 'Type of memory (fact, preference, context)';
COMMENT ON COLUMN memory_entries.tags IS 'Memory tags for categorization';
COMMENT ON COLUMN memory_entries.importance_score IS 'Importance score (1-10)';
COMMENT ON COLUMN memory_entries.access_count IS 'How many times this memory was accessed';
COMMENT ON COLUMN memory_entries.last_accessed IS 'When this memory was last accessed';
COMMENT ON COLUMN memory_entries.ai_generated IS 'Whether this memory was AI-generated';
COMMENT ON COLUMN memory_entries.user_confirmed IS 'Whether user confirmed this memory';