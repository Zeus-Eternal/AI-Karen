-- Create messages and message_tools tables (if they don't exist)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_metadata JSONB DEFAULT '{}'::jsonb,
    function_call JSONB,
    function_response JSONB,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_convo_time ON messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS message_tools (
    id BIGSERIAL PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    arguments JSONB,
    result JSONB,
    latency_ms INT,
    status TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_message_tools_message ON message_tools(message_id);

-- Get the view definition before dropping it
CREATE OR REPLACE TEMPORARY VIEW temp_active_conversations_def AS 
SELECT view_definition 
FROM information_schema.views 
WHERE table_name = 'active_conversations';

-- Drop the dependent view
DROP VIEW IF EXISTS active_conversations CASCADE;

-- Backfill existing conversation messages into messages table
INSERT INTO messages (id, conversation_id, role, content, message_metadata, function_call, function_response, created_at)
SELECT
    (msg->>'id')::uuid,
    c.id,
    msg->>'role',
    msg->>'content',
    COALESCE(msg->'metadata', '{}'::jsonb),
    msg->'function_call',
    msg->'function_response',
    (msg->>'timestamp')::timestamp
FROM conversations c
CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.messages::jsonb, '[]'::jsonb)) AS msg;

-- Remove old messages column
ALTER TABLE conversations DROP COLUMN IF EXISTS messages;

-- Recreate the active_conversations view without the messages column
CREATE OR REPLACE VIEW active_conversations AS
SELECT 
    c.id,
    c.user_id,
    c.title,
    '{}'::jsonb as messages, -- Empty JSONB instead of the messages column
    c.conversation_metadata,
    c.is_active,
    c.created_at,
    c.updated_at,
    c.session_id,
    c.ui_context,
    c.ai_insights,
    c.user_settings,
    c.summary,
    c.tags,
    c.last_ai_response_id,
    c.status,
    c.priority,
    c.context_memories,
    c.proactive_suggestions,
    c.message_count,
    c.last_message_at,
    c.total_tokens_used,
    c.average_response_time_ms,
    u.email as user_email,
    t.name as tenant_name
FROM conversations c
LEFT JOIN users u ON c.user_id = u.id
LEFT JOIN tenants t ON u.tenant_id = t.id
WHERE c.is_active = true;