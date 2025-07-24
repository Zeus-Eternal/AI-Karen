-- Create memory_entries table for tenant data
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY,
    vector_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    query TEXT,
    result JSONB,
    embedding_id VARCHAR(255),
    memory_metadata JSONB DEFAULT '{}',
    ttl TIMESTAMP,
    timestamp BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Base indexes
CREATE INDEX idx_memory_vector ON memory_entries(vector_id);
CREATE INDEX idx_memory_user ON memory_entries(user_id);
CREATE INDEX idx_memory_session ON memory_entries(session_id);
CREATE INDEX idx_memory_created ON memory_entries(created_at);
CREATE INDEX idx_memory_ttl ON memory_entries(ttl);
