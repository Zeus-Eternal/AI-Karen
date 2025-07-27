-- 008_create_web_ui_memory_entries_table.sql

-- 1️⃣ enable UUID support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2️⃣ create memory_entries table for the Web-UI
CREATE TABLE IF NOT EXISTS memory_entries (
  id            UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     TEXT                NOT NULL,
  content       TEXT                NOT NULL,
  user_id       UUID                NULL,
  ui_source     TEXT                NOT NULL,
  session_id    TEXT                NULL,
  memory_type   TEXT                NOT NULL,
  tags          JSONB               NOT NULL DEFAULT '[]',
  metadata      JSONB               NOT NULL DEFAULT '{}' ,
  ai_generated  BOOLEAN             NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

-- 3️⃣ add helpful indexes
CREATE INDEX IF NOT EXISTS memory_entries_tenant_idx ON memory_entries(tenant_id);
CREATE INDEX IF NOT EXISTS memory_entries_user_idx   ON memory_entries(user_id);
