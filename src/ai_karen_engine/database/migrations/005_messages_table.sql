-- Create messages and message_tools tables
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
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

-- Backfill existing conversation messages into messages table
INSERT INTO messages (id, conversation_id, role, content, metadata, function_call, function_response, created_at)
SELECT
    (msg->>'id')::uuid,
    c.id,
    msg->>'role',
    msg->>'content',
    COALESCE(msg->'metadata', '{}'),
    msg->'function_call',
    msg->'function_response',
    (msg->>'timestamp')::timestamp
FROM conversations c
CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.messages::jsonb, '[]'::jsonb)) AS msg;

-- Remove old messages column
ALTER TABLE conversations DROP COLUMN IF EXISTS messages;
