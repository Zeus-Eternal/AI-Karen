-- 023_context_management_tables.sql
-- Context Management Database Schema for CoPilot System
-- Creates tables for context entries, files, sharing, versioning, and access control

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Create context_entries table (main context storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    org_id VARCHAR(255),
    session_id VARCHAR(255),
    conversation_id UUID,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    context_type VARCHAR(50) NOT NULL DEFAULT 'custom' CHECK (
        context_type IN (
            'conversation', 'document', 'code', 'image', 'audio', 'video',
            'web_page', 'note', 'task', 'memory', 'custom'
        )
    ),
    access_level VARCHAR(20) NOT NULL DEFAULT 'private' CHECK (
        access_level IN ('private', 'shared', 'team', 'organization', 'public')
    ),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'archived', 'deleted', 'processing', 'error')
    ),
    
    -- Content analysis fields
    embedding_id VARCHAR(255), -- Reference to vector store
    summary TEXT,
    keywords JSONB DEFAULT '[]',
    entities JSONB DEFAULT '[]',
    
    -- Relevance and scoring
    relevance_score REAL DEFAULT 0.0 CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    importance_score REAL DEFAULT 5.0 CHECK (importance_score >= 1.0 AND importance_score <= 10.0),
    access_count INTEGER DEFAULT 0 CHECK (access_count >= 0),
    last_accessed TIMESTAMPTZ,
    
    -- Versioning and relationships
    version INTEGER DEFAULT 1 CHECK (version >= 1),
    parent_context_id UUID REFERENCES context_entries(id) ON DELETE SET NULL,
    child_context_ids JSONB DEFAULT '[]',
    
    -- Metadata and timestamps
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,
    
    -- File associations
    file_ids JSONB DEFAULT '[]'
);

-- ============================================================================
-- 2. Create context_files table (file upload storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (
        file_type IN (
            'pdf', 'docx', 'txt', 'md', 'json', 'csv', 'xml', 'html',
            'py', 'js', 'ts', 'java', 'cpp',
            'png', 'jpg', 'jpeg', 'gif', 'svg',
            'mp3', 'wav', 'mp4', 'avi', 'mov',
            'zip', 'tar', 'gz'
        )
    ),
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    storage_path VARCHAR(1000) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    
    -- Processing fields
    extracted_text TEXT,
    extracted_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (
        status IN ('active', 'archived', 'deleted', 'processing', 'error')
    ),
    error_message TEXT
);

-- ============================================================================
-- 3. Create context_shares table (sharing configuration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_shares (
    share_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
    shared_by VARCHAR(255) NOT NULL,
    shared_with VARCHAR(255), -- NULL means public/team/org
    access_level VARCHAR(20) NOT NULL DEFAULT 'shared' CHECK (
        access_level IN ('private', 'shared', 'team', 'organization', 'public')
    ),
    permissions JSONB DEFAULT '[]', -- read, write, share, delete
    created_at TIMESTAMPTZ DEFAULT now(),
    last_accessed TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0 CHECK (access_count >= 0),
    expires_at TIMESTAMPTZ
);

-- ============================================================================
-- 4. Create context_versions table (version history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    content TEXT NOT NULL,
    title VARCHAR(500) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    change_summary TEXT,
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now(),
    
    -- Unique constraint to prevent duplicate versions
    UNIQUE(context_id, version_number)
);

-- ============================================================================
-- 5. Create context_access_log table (audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_access_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID NOT NULL REFERENCES context_entries(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (
        action IN ('read', 'write', 'share', 'delete', 'search')
    ),
    access_level VARCHAR(20) NOT NULL CHECK (
        access_level IN ('private', 'shared', 'team', 'organization', 'public')
    ),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- 6. Create indexes for performance and querying
-- ============================================================================

-- Context entries indexes
CREATE INDEX IF NOT EXISTS idx_context_entries_user ON context_entries(user_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_org ON context_entries(org_id) WHERE org_id IS NOT NULL AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_session ON context_entries(session_id, created_at DESC) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_entries_conversation ON context_entries(conversation_id, created_at DESC) WHERE conversation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_entries_type ON context_entries(context_type, created_at DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_access ON context_entries(access_level, created_at DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_status ON context_entries(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_entries_importance ON context_entries(importance_score DESC, created_at DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_accessed ON context_entries(last_accessed DESC, access_count DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_expires ON context_entries(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_entries_tags ON context_entries USING GIN(tags) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_metadata ON context_entries USING GIN(metadata) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_context_entries_embedding ON context_entries(embedding_id) WHERE embedding_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_entries_parent ON context_entries(parent_context_id) WHERE parent_context_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_entries_created ON context_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_entries_updated ON context_entries(updated_at DESC);

-- Context files indexes
CREATE INDEX IF NOT EXISTS idx_context_files_context ON context_files(context_id);
CREATE INDEX IF NOT EXISTS idx_context_files_type ON context_files(file_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_files_status ON context_files(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_files_checksum ON context_files(checksum);
CREATE INDEX IF NOT EXISTS idx_context_files_size ON context_files(size_bytes DESC);
CREATE INDEX IF NOT EXISTS idx_context_files_created ON context_files(created_at DESC);

-- Context shares indexes
CREATE INDEX IF NOT EXISTS idx_context_shares_context ON context_shares(context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_shares_by ON context_shares(shared_by, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_shares_with ON context_shares(shared_with, created_at DESC) WHERE shared_with IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_shares_access ON context_shares(access_level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_shares_expires ON context_shares(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_context_shares_active ON context_shares(created_at DESC) WHERE expires_at IS NULL OR expires_at > now();

-- Context versions indexes
CREATE INDEX IF NOT EXISTS idx_context_versions_context ON context_versions(context_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_context_versions_created ON context_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_versions_by ON context_versions(created_by, created_at DESC);

-- Context access log indexes
CREATE INDEX IF NOT EXISTS idx_context_access_log_context ON context_access_log(context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_user ON context_access_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_action ON context_access_log(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_access ON context_access_log(access_level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_success ON context_access_log(success, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_access_log_created ON context_access_log(created_at DESC);

-- ============================================================================
-- 7. Create helper functions for context operations
-- ============================================================================

-- Function to calculate context relevance score
CREATE OR REPLACE FUNCTION calculate_context_relevance(
    context_id UUID,
    query_text TEXT DEFAULT NULL,
    user_id TEXT DEFAULT NULL,
    current_timestamp TIMESTAMPTZ DEFAULT now()
) RETURNS REAL AS $$
DECLARE
    relevance_score REAL := 0.0;
    recency_score REAL := 0.0;
    importance_score REAL := 0.0;
    usage_score REAL := 0.0;
    age_days REAL;
    context_record RECORD;
BEGIN
    -- Get context record
    SELECT * INTO context_record 
    FROM context_entries 
    WHERE id = context_id AND status = 'active';
    
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;
    
    -- Calculate recency score (exponential decay)
    age_days := EXTRACT(EPOCH FROM (current_timestamp - context_record.created_at)) / 86400.0;
    recency_score := EXP(-age_days / 30.0); -- 30-day half-life
    
    -- Normalize importance score (1-10 to 0-1)
    importance_score := (context_record.importance_score - 1.0) / 9.0;
    
    -- Normalize usage score (logarithmic)
    usage_score := CASE 
        WHEN context_record.access_count = 0 THEN 0.0
        ELSE LOG(context_record.access_count + 1) / LOG(100)
    END;
    
    -- Combine scores (weighted average)
    relevance_score := (
        recency_score * 0.4 +
        importance_score * 0.3 +
        usage_score * 0.2 +
        0.1 -- Base score
    );
    
    -- Apply text matching bonus if query provided
    IF query_text IS NOT NULL THEN
        IF LOWER(query_text) LIKE '%' || LOWER(context_record.title) || '%' THEN
            relevance_score := relevance_score * 1.2;
        END IF;
        
        IF LOWER(query_text) LIKE '%' || LOWER(context_record.content) || '%' THEN
            relevance_score := relevance_score * 1.1;
        END IF;
    END IF;
    
    RETURN LEAST(1.0, GREATEST(0.0, relevance_score));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update context access tracking
CREATE OR REPLACE FUNCTION update_context_access(
    context_id UUID,
    access_user_id TEXT DEFAULT NULL,
    access_action TEXT DEFAULT 'read',
    access_ip_address INET DEFAULT NULL,
    access_user_agent TEXT DEFAULT NULL,
    processing_time_ms INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Update access count and last accessed
    UPDATE context_entries 
    SET 
        access_count = COALESCE(access_count, 0) + 1,
        last_accessed = NOW(),
        updated_at = NOW()
    WHERE id = context_id;
    
    -- Insert access log entry
    INSERT INTO context_access_log (
        context_id,
        user_id,
        action,
        ip_address,
        user_agent,
        processing_time_ms
    ) VALUES (
        context_id,
        COALESCE(access_user_id, (SELECT user_id FROM context_entries WHERE id = context_id)),
        access_action,
        access_ip_address,
        access_user_agent,
        processing_time_ms
    );
END;
$$ LANGUAGE plpgsql;

-- Function to create context version
CREATE OR REPLACE FUNCTION create_context_version(
    p_context_id UUID,
    p_content TEXT,
    p_title TEXT,
    p_created_by TEXT,
    p_change_summary TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}',
    p_tags JSONB DEFAULT '[]'
) RETURNS UUID AS $$
DECLARE
    new_version_id UUID;
    next_version_number INTEGER;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version_number), 0) + 1 
    INTO next_version_number
    FROM context_versions 
    WHERE context_id = p_context_id;
    
    -- Insert new version
    INSERT INTO context_versions (
        context_id,
        version_number,
        content,
        title,
        created_by,
        change_summary,
        metadata,
        tags
    ) VALUES (
        p_context_id,
        next_version_number,
        p_content,
        p_title,
        p_created_by,
        p_change_summary,
        p_metadata,
        p_tags
    ) RETURNING version_id INTO new_version_id;
    
    -- Update context entry version
    UPDATE context_entries 
    SET 
        version = next_version_number,
        updated_at = NOW()
    WHERE id = p_context_id;
    
    RETURN new_version_id;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired contexts
CREATE OR REPLACE FUNCTION cleanup_expired_contexts() RETURNS INTEGER AS $$
DECLARE
    cleanup_count INTEGER := 0;
BEGIN
    -- Archive expired contexts
    UPDATE context_entries 
    SET status = 'archived', updated_at = NOW()
    WHERE status = 'active' 
      AND expires_at IS NOT NULL 
      AND expires_at < NOW();
    
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    
    -- Delete expired shares
    DELETE FROM context_shares 
    WHERE expires_at IS NOT NULL 
      AND expires_at < NOW();
    
    RETURN cleanup_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. Create triggers for automatic maintenance
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_context_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to context_entries table
CREATE TRIGGER update_context_entries_updated_at 
    BEFORE UPDATE ON context_entries
    FOR EACH ROW EXECUTE FUNCTION update_context_updated_at();

-- Apply trigger to context_files table
CREATE TRIGGER update_context_files_updated_at 
    BEFORE UPDATE ON context_files
    FOR EACH ROW EXECUTE FUNCTION update_context_updated_at();

-- ============================================================================
-- 9. Create views for common queries
-- ============================================================================

-- View for active contexts with relevance scores
CREATE OR REPLACE VIEW active_contexts_with_relevance AS
SELECT 
    ce.*,
    calculate_context_relevance(ce.id) as calculated_relevance_score
FROM context_entries ce
WHERE ce.status = 'active'
  AND (ce.expires_at IS NULL OR ce.expires_at > NOW());

-- View for context files with processing status
CREATE OR REPLACE VIEW context_files_with_status AS
SELECT 
    cf.*,
    CASE 
        WHEN cf.status = 'active' THEN 'Ready'
        WHEN cf.status = 'processing' THEN 'Processing'
        WHEN cf.status = 'error' THEN 'Error'
        WHEN cf.status = 'archived' THEN 'Archived'
        WHEN cf.status = 'deleted' THEN 'Deleted'
    END as status_description,
    CASE 
        WHEN cf.processed_at IS NOT NULL THEN EXTRACT(EPOCH FROM (cf.processed_at - cf.created_at))
        ELSE NULL
    END as processing_duration_seconds
FROM context_files cf;

-- View for context sharing analytics
CREATE OR REPLACE VIEW context_sharing_analytics AS
SELECT 
    cs.context_id,
    ce.title,
    ce.user_id as owner_id,
    COUNT(*) as total_shares,
    COUNT(DISTINCT cs.shared_with) as unique_recipients,
    SUM(cs.access_count) as total_accesses,
    MAX(cs.last_accessed) as last_accessed,
    AVG(cs.access_count) as avg_accesses_per_share
FROM context_shares cs
JOIN context_entries ce ON cs.context_id = ce.id
WHERE (cs.expires_at IS NULL OR cs.expires_at > NOW())
GROUP BY cs.context_id, ce.title, ce.user_id;

-- View for context access analytics
CREATE OR REPLACE VIEW context_access_analytics AS
SELECT 
    ce.user_id,
    ce.context_type,
    DATE_TRUNC('day', cal.created_at) as access_date,
    COUNT(*) as total_accesses,
    COUNT(DISTINCT cal.context_id) as unique_contexts_accessed,
    AVG(cal.processing_time_ms) as avg_processing_time_ms,
    COUNT(*) FILTER (WHERE cal.success = false) as failed_accesses,
    COUNT(*) FILTER (WHERE cal.action = 'search') as searches,
    COUNT(*) FILTER (WHERE cal.action = 'read') as reads,
    COUNT(*) FILTER (WHERE cal.action = 'write') as writes
FROM context_access_log cal
JOIN context_entries ce ON cal.context_id = ce.id
GROUP BY ce.user_id, ce.context_type, DATE_TRUNC('day', cal.created_at);

-- ============================================================================
-- 10. Add comments for documentation
-- ============================================================================

COMMENT ON TABLE context_entries IS 'Main context storage table with full metadata, versioning, and access control';
COMMENT ON TABLE context_files IS 'File upload storage with processing status and extracted content';
COMMENT ON TABLE context_shares IS 'Context sharing configuration with permissions and expiration';
COMMENT ON TABLE context_versions IS 'Version history for context entries with change tracking';
COMMENT ON TABLE context_access_log IS 'Comprehensive audit log for all context access operations';

COMMENT ON COLUMN context_entries.id IS 'Unique identifier for context entry';
COMMENT ON COLUMN context_entries.user_id IS 'User who owns the context';
COMMENT ON COLUMN context_entries.org_id IS 'Organization for multi-tenant isolation';
COMMENT ON COLUMN context_entries.session_id IS 'Session identifier for conversation tracking';
COMMENT ON COLUMN context_entries.conversation_id IS 'Conversation identifier for grouping';
COMMENT ON COLUMN context_entries.title IS 'Human-readable title for the context';
COMMENT ON COLUMN context_entries.content IS 'Main content/text of the context';
COMMENT ON COLUMN context_entries.context_type IS 'Type of context (conversation, document, code, etc.)';
COMMENT ON COLUMN context_entries.access_level IS 'Access permissions (private, shared, team, organization, public)';
COMMENT ON COLUMN context_entries.status IS 'Current status of the context';
COMMENT ON COLUMN context_entries.embedding_id IS 'Reference to vector embedding for semantic search';
COMMENT ON COLUMN context_entries.summary IS 'AI-generated or user-provided summary';
COMMENT ON COLUMN context_entries.keywords IS 'Extracted keywords for search and categorization';
COMMENT ON COLUMN context_entries.entities IS 'Named entities (people, places, organizations)';
COMMENT ON COLUMN context_entries.relevance_score IS 'Calculated relevance for search ranking';
COMMENT ON COLUMN context_entries.importance_score IS 'User-assigned importance (1-10 scale)';
COMMENT ON COLUMN context_entries.access_count IS 'Number of times context has been accessed';
COMMENT ON COLUMN context_entries.last_accessed IS 'Timestamp of last access';
COMMENT ON COLUMN context_entries.version IS 'Current version number';
COMMENT ON COLUMN context_entries.parent_context_id IS 'Parent context for versioning';
COMMENT ON COLUMN context_entries.child_context_ids IS 'List of child context versions';
COMMENT ON COLUMN context_entries.metadata IS 'Additional metadata in JSON format';
COMMENT ON COLUMN context_entries.tags IS 'User-defined tags for categorization';
COMMENT ON COLUMN context_entries.created_at IS 'Timestamp when context was created';
COMMENT ON COLUMN context_entries.updated_at IS 'Timestamp when context was last updated';
COMMENT ON COLUMN context_entries.expires_at IS 'Timestamp when context expires (optional)';
COMMENT ON COLUMN context_entries.file_ids IS 'List of associated file IDs';

COMMENT ON FUNCTION calculate_context_relevance IS 'Calculates relevance score for context based on recency, importance, and usage';
COMMENT ON FUNCTION update_context_access IS 'Updates access tracking and creates audit log entry';
COMMENT ON FUNCTION create_context_version IS 'Creates new version entry for context with change tracking';
COMMENT ON FUNCTION cleanup_expired_contexts IS 'Archives expired contexts and cleans up expired shares';

-- ============================================================================
-- 11. Create migration completion marker
-- ============================================================================

-- Insert migration record
INSERT INTO migration_history (service, migration_name, checksum, status)
VALUES (
    'postgres',
    '023_context_management_tables.sql',
    encode(digest('023_context_management_tables.sql', 'sha256'), 'hex'),
    'applied'
) ON CONFLICT (service, migration_name) DO UPDATE 
SET applied_at = NOW(), checksum = EXCLUDED.checksum, status = 'applied';

COMMIT;