-- Context management schema

CREATE TABLE IF NOT EXISTS context_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  org_id TEXT,
  session_id TEXT,
  conversation_id UUID,
  title TEXT NOT NULL DEFAULT '',
  content TEXT NOT NULL DEFAULT '',
  context_type TEXT NOT NULL DEFAULT 'custom',
  access_level TEXT NOT NULL DEFAULT 'private',
  status TEXT NOT NULL DEFAULT 'active',
  summary TEXT,
  keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
  entities JSONB NOT NULL DEFAULT '[]'::jsonb,
  relevance_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  importance_score DOUBLE PRECISION NOT NULL DEFAULT 5.0,
  access_count INTEGER NOT NULL DEFAULT 0,
  last_accessed TIMESTAMP,
  version INTEGER NOT NULL DEFAULT 1,
  parent_context_id UUID,
  child_context_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  expires_at TIMESTAMP,
  file_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  CONSTRAINT fk_context_entries_parent
    FOREIGN KEY (parent_context_id) REFERENCES context_entries(id) ON DELETE SET NULL,
  CONSTRAINT chk_context_type CHECK (
    context_type IN (
      'conversation', 'document', 'code', 'image', 'audio', 'video',
      'web_page', 'note', 'task', 'memory', 'custom'
    )
  ),
  CONSTRAINT chk_context_access_level CHECK (
    access_level IN ('private', 'shared', 'team', 'organization', 'public')
  ),
  CONSTRAINT chk_context_status CHECK (
    status IN ('active', 'archived', 'deleted', 'processing', 'error')
  )
);

CREATE INDEX IF NOT EXISTS idx_context_entries_user_status
  ON context_entries(user_id, status);
CREATE INDEX IF NOT EXISTS idx_context_entries_org_status
  ON context_entries(org_id, status);
CREATE INDEX IF NOT EXISTS idx_context_entries_type
  ON context_entries(context_type);
CREATE INDEX IF NOT EXISTS idx_context_entries_access_level
  ON context_entries(access_level);
CREATE INDEX IF NOT EXISTS idx_context_entries_session
  ON context_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_context_entries_conversation
  ON context_entries(conversation_id);
CREATE INDEX IF NOT EXISTS idx_context_entries_updated_at
  ON context_entries(updated_at DESC);

CREATE TABLE IF NOT EXISTS context_versions (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  content TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  created_by TEXT NOT NULL,
  change_summary TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT uq_context_version_number UNIQUE (context_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_context_versions_context
  ON context_versions(context_id, version_number DESC);

CREATE TABLE IF NOT EXISTS context_shares (
  share_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
  shared_by TEXT NOT NULL,
  shared_with TEXT,
  access_level TEXT NOT NULL DEFAULT 'shared',
  permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  last_accessed TIMESTAMP,
  access_count INTEGER NOT NULL DEFAULT 0,
  expires_at TIMESTAMP,
  CONSTRAINT chk_context_share_access_level CHECK (
    access_level IN ('private', 'shared', 'team', 'organization', 'public')
  )
);

CREATE INDEX IF NOT EXISTS idx_context_shares_context
  ON context_shares(context_id);
CREATE INDEX IF NOT EXISTS idx_context_shares_shared_with
  ON context_shares(shared_with);

CREATE TABLE IF NOT EXISTS context_files (
  file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL DEFAULT 0,
  storage_path TEXT NOT NULL,
  checksum TEXT NOT NULL,
  extracted_text TEXT,
  extracted_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  processed_at TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'processing',
  error_message TEXT,
  CONSTRAINT chk_context_file_status CHECK (
    status IN ('active', 'archived', 'deleted', 'processing', 'error')
  )
);

CREATE INDEX IF NOT EXISTS idx_context_files_context
  ON context_files(context_id);
CREATE INDEX IF NOT EXISTS idx_context_files_checksum
  ON context_files(checksum);
CREATE INDEX IF NOT EXISTS idx_context_files_status
  ON context_files(status);

CREATE TABLE IF NOT EXISTS context_access_log (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  action TEXT NOT NULL,
  access_level TEXT NOT NULL,
  ip_address INET,
  user_agent TEXT,
  success BOOLEAN NOT NULL DEFAULT TRUE,
  error_message TEXT,
  processing_time_ms INTEGER,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT chk_context_access_action CHECK (
    action IN ('read', 'write', 'share', 'delete', 'search')
  ),
  CONSTRAINT chk_context_access_level CHECK (
    access_level IN ('private', 'shared', 'team', 'organization', 'public')
  )
);

CREATE INDEX IF NOT EXISTS idx_context_access_log_context
  ON context_access_log(context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_user
  ON context_access_log(user_id, created_at DESC);
