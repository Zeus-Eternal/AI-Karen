-- Case Memory Learning System Migration
-- Creates table for storing case memory metadata and payloads

CREATE TABLE IF NOT EXISTS case_memory_cases (
  case_id    TEXT PRIMARY KEY,
  tenant_id  TEXT NOT NULL,
  user_id    TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  reward     DOUBLE PRECISION NOT NULL,
  tags       TEXT[] NOT NULL,
  payload    JSONB NOT NULL
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_cm_tenant_created ON case_memory_cases(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cm_tenant_reward ON case_memory_cases(tenant_id, reward DESC);
CREATE INDEX IF NOT EXISTS idx_cm_tags ON case_memory_cases USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_cm_payload ON case_memory_cases USING GIN(payload);

-- Add comments for documentation
COMMENT ON TABLE case_memory_cases IS 'Case memory storage for learning from past agent executions';
COMMENT ON COLUMN case_memory_cases.case_id IS 'Unique identifier for the case';
COMMENT ON COLUMN case_memory_cases.tenant_id IS 'Tenant isolation identifier';
COMMENT ON COLUMN case_memory_cases.user_id IS 'User who initiated the original task';
COMMENT ON COLUMN case_memory_cases.created_at IS 'Timestamp when case was created';
COMMENT ON COLUMN case_memory_cases.reward IS 'Reward score (0.0 to 1.0) for case quality';
COMMENT ON COLUMN case_memory_cases.tags IS 'Tags for categorizing and filtering cases';
COMMENT ON COLUMN case_memory_cases.payload IS 'Full case data including steps, embeddings, and metadata';
