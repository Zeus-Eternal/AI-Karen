-- 016_unified_memory_schema.sql
-- Unified Memory Database Schema for Phase 4.1 Production Polish
-- Creates consolidated memory tables with tenant isolation and audit trails

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Create unified memories table (consolidates all memory storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    org_id VARCHAR(255),
    text TEXT NOT NULL,
    embedding_id VARCHAR(255), -- Reference to vector store
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    decay_tier VARCHAR(20) DEFAULT 'short' CHECK (decay_tier IN ('short', 'medium', 'long', 'pinned')),
    tags JSONB DEFAULT '[]',
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- Computed from decay policy
    deleted_at TIMESTAMPTZ, -- Soft deletion
    version INTEGER DEFAULT 1,
    
    -- Additional fields for backward compatibility and enhanced functionality
    session_id VARCHAR(255),
    conversation_id UUID,
    ui_source VARCHAR(50) DEFAULT 'api' CHECK (ui_source IN ('web', 'streamlit', 'desktop', 'api', 'ag_ui', 'copilot')),
    memory_type VARCHAR(50) DEFAULT 'general' CHECK (memory_type IN ('general', 'fact', 'preference', 'context', 'conversation', 'insight', 'episodic', 'semantic', 'procedural')),
    ai_generated BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT TRUE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    
    -- NeuroVault compatibility fields
    neuro_type VARCHAR(20) DEFAULT 'episodic' CHECK (neuro_type IN ('episodic', 'semantic', 'procedural', 'general', 'fact', 'preference', 'context', 'conversation', 'insight')),
    decay_lambda REAL DEFAULT 0.1 CHECK (decay_lambda >= 0.0 AND decay_lambda <= 1.0),
    reflection_count INTEGER DEFAULT 0 CHECK (reflection_count >= 0),
    source_memories JSONB DEFAULT '[]',
    derived_memories JSONB DEFAULT '[]',
    importance_decay REAL DEFAULT 1.0 CHECK (importance_decay >= 0.0 AND importance_decay <= 1.0),
    last_reflection TIMESTAMPTZ
);

-- ============================================================================
-- 2. Create memory access audit log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    org_id VARCHAR(255),
    access_type VARCHAR(20) NOT NULL CHECK (access_type IN ('read', 'write', 'update', 'delete', 'search')),
    correlation_id VARCHAR(255),
    accessed_at TIMESTAMPTZ DEFAULT now(),
    ip_address INET,
    user_agent TEXT,
    request_path VARCHAR(255),
    response_status INTEGER,
    query_text TEXT, -- For search operations
    results_count INTEGER, -- For search operations
    processing_time_ms INTEGER,
    meta JSONB DEFAULT '{}'
);

-- ============================================================================
-- 3. Create memory relationships table (for NeuroVault compatibility)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    derived_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('reflection', 'consolidation', 'pattern', 'decay_promotion', 'semantic_link')),
    confidence_score REAL DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Prevent self-referential relationships
    CONSTRAINT chk_no_self_reference CHECK (source_memory_id != derived_memory_id),
    
    -- Unique constraint to prevent duplicate relationships
    UNIQUE(source_memory_id, derived_memory_id, relationship_type)
);

-- ============================================================================
-- 4. Create indexes for performance and tenant isolation
-- ============================================================================

-- Primary tenant isolation indexes
CREATE INDEX IF NOT EXISTS idx_memories_tenant ON memories(user_id, org_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_org ON memories(org_id) WHERE org_id IS NOT NULL AND deleted_at IS NULL;

-- Temporal and lifecycle indexes
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at DESC) WHERE updated_at IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at) WHERE expires_at IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_deleted ON memories(deleted_at) WHERE deleted_at IS NOT NULL;

-- Decay and importance indexes
CREATE INDEX IF NOT EXISTS idx_memories_decay_tier ON memories(decay_tier, expires_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_importance_decay ON memories(importance_decay DESC, last_accessed DESC) WHERE deleted_at IS NULL;

-- Content and metadata indexes
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_meta ON memories USING GIN(meta) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories(embedding_id) WHERE embedding_id IS NOT NULL AND deleted_at IS NULL;

-- Session and conversation indexes
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id, created_at DESC) WHERE session_id IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_conversation ON memories(conversation_id, created_at DESC) WHERE conversation_id IS NOT NULL AND deleted_at IS NULL;

-- UI source and memory type indexes
CREATE INDEX IF NOT EXISTS idx_memories_ui_source ON memories(ui_source, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories(memory_type, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_neuro_type ON memories(neuro_type, created_at DESC) WHERE deleted_at IS NULL;

-- Access tracking indexes
CREATE INDEX IF NOT EXISTS idx_memories_access_count ON memories(access_count DESC, last_accessed DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON memories(last_accessed DESC) WHERE last_accessed IS NOT NULL AND deleted_at IS NULL;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_memories_tenant_type ON memories(user_id, org_id, memory_type, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_tenant_importance ON memories(user_id, org_id, importance DESC, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_memories_decay_cleanup ON memories(decay_tier, importance_decay, last_accessed) WHERE importance_decay < 0.1 AND deleted_at IS NULL;

-- Memory access log indexes
CREATE INDEX IF NOT EXISTS idx_memory_access_log_memory ON memory_access_log(memory_id, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_user ON memory_access_log(user_id, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_org ON memory_access_log(org_id, accessed_at DESC) WHERE org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_access_log_correlation ON memory_access_log(correlation_id) WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_access_log_type ON memory_access_log(access_type, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_access_log_accessed ON memory_access_log(accessed_at DESC);

-- Memory relationships indexes
CREATE INDEX IF NOT EXISTS idx_memory_relationships_source ON memory_relationships(source_memory_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_derived ON memory_relationships(derived_memory_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_type ON memory_relationships(relationship_type, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_created ON memory_relationships(created_at DESC);

-- ============================================================================
-- 5. Create helper functions for memory operations
-- ============================================================================

-- Function to calculate decay score based on memory type and age
CREATE OR REPLACE FUNCTION calculate_decay_score(
    memory_created_at TIMESTAMPTZ,
    memory_neuro_type VARCHAR DEFAULT 'episodic',
    memory_importance_score INTEGER DEFAULT 5,
    memory_access_count INTEGER DEFAULT 0
) RETURNS REAL AS $$
DECLARE
    base_lambda REAL;
    age_days REAL;
    access_boost REAL;
    importance_boost REAL;
    decay_score REAL;
BEGIN
    -- Set base decay lambda based on memory type
    CASE memory_neuro_type
        WHEN 'episodic' THEN base_lambda := 0.12;
        WHEN 'semantic' THEN base_lambda := 0.04;
        WHEN 'procedural' THEN base_lambda := 0.02;
        ELSE base_lambda := 0.08; -- Default for other types
    END CASE;
    
    -- Calculate age in days
    age_days := EXTRACT(EPOCH FROM (NOW() - memory_created_at)) / 86400.0;
    
    -- Calculate access boost (more accessed memories decay slower)
    access_boost := LEAST(memory_access_count * 0.01, 0.5);
    
    -- Calculate importance boost (more important memories decay slower)
    importance_boost := (memory_importance_score - 5) * 0.02;
    
    -- Calculate final decay score using exponential decay
    decay_score := EXP(-(base_lambda - access_boost - importance_boost) * age_days);
    
    -- Ensure score is between 0 and 1
    RETURN GREATEST(0.0, LEAST(1.0, decay_score));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update memory access tracking
CREATE OR REPLACE FUNCTION update_memory_access(
    memory_id UUID,
    access_user_id VARCHAR DEFAULT NULL,
    access_org_id VARCHAR DEFAULT NULL,
    access_type VARCHAR DEFAULT 'read',
    correlation_id VARCHAR DEFAULT NULL,
    ip_address INET DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    request_path VARCHAR DEFAULT NULL,
    response_status INTEGER DEFAULT 200,
    query_text TEXT DEFAULT NULL,
    results_count INTEGER DEFAULT NULL,
    processing_time_ms INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Update memory access tracking
    UPDATE memories 
    SET 
        access_count = COALESCE(access_count, 0) + 1,
        last_accessed = NOW(),
        updated_at = NOW()
    WHERE id = memory_id;
    
    -- Insert audit log entry
    INSERT INTO memory_access_log (
        memory_id,
        user_id,
        org_id,
        access_type,
        correlation_id,
        ip_address,
        user_agent,
        request_path,
        response_status,
        query_text,
        results_count,
        processing_time_ms
    ) VALUES (
        memory_id,
        COALESCE(access_user_id, (SELECT user_id FROM memories WHERE id = memory_id)),
        COALESCE(access_org_id, (SELECT org_id FROM memories WHERE id = memory_id)),
        access_type,
        correlation_id,
        ip_address,
        user_agent,
        request_path,
        response_status,
        query_text,
        results_count,
        processing_time_ms
    );
END;
$$ LANGUAGE plpgsql;

-- Function to create memory relationship
CREATE OR REPLACE FUNCTION create_memory_relationship(
    source_id UUID,
    derived_id UUID,
    rel_type VARCHAR,
    confidence REAL DEFAULT 1.0,
    rel_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    relationship_id UUID;
BEGIN
    -- Insert relationship record
    INSERT INTO memory_relationships (
        source_memory_id,
        derived_memory_id,
        relationship_type,
        confidence_score,
        metadata
    ) VALUES (
        source_id,
        derived_id,
        rel_type,
        confidence,
        rel_metadata
    ) RETURNING id INTO relationship_id;
    
    -- Update source and derived memory arrays
    UPDATE memories 
    SET 
        derived_memories = COALESCE(derived_memories, '[]'::jsonb) || jsonb_build_array(derived_id::text),
        updated_at = NOW()
    WHERE id = source_id;
    
    UPDATE memories 
    SET 
        source_memories = COALESCE(source_memories, '[]'::jsonb) || jsonb_build_array(source_id::text),
        updated_at = NOW()
    WHERE id = derived_id;
    
    RETURN relationship_id;
END;
$$ LANGUAGE plpgsql;

-- Function to soft delete memory with audit trail
CREATE OR REPLACE FUNCTION soft_delete_memory(
    memory_id UUID,
    delete_user_id VARCHAR,
    delete_org_id VARCHAR DEFAULT NULL,
    correlation_id VARCHAR DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    memory_exists BOOLEAN;
BEGIN
    -- Check if memory exists and is not already deleted
    SELECT EXISTS(
        SELECT 1 FROM memories 
        WHERE id = memory_id AND deleted_at IS NULL
    ) INTO memory_exists;
    
    IF NOT memory_exists THEN
        RETURN FALSE;
    END IF;
    
    -- Soft delete the memory
    UPDATE memories 
    SET 
        deleted_at = NOW(),
        updated_at = NOW()
    WHERE id = memory_id;
    
    -- Log the deletion
    PERFORM update_memory_access(
        memory_id,
        delete_user_id,
        delete_org_id,
        'delete',
        correlation_id
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate expires_at based on decay tier
CREATE OR REPLACE FUNCTION calculate_expires_at(
    decay_tier VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
) RETURNS TIMESTAMPTZ AS $$
BEGIN
    CASE decay_tier
        WHEN 'short' THEN RETURN created_at + INTERVAL '7 days';
        WHEN 'medium' THEN RETURN created_at + INTERVAL '30 days';
        WHEN 'long' THEN RETURN created_at + INTERVAL '180 days';
        WHEN 'pinned' THEN RETURN NULL; -- Never expires
        ELSE RETURN created_at + INTERVAL '7 days'; -- Default to short
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 6. Create triggers for automatic maintenance
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to memories table
CREATE TRIGGER update_memories_updated_at 
    BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to memory_relationships table
CREATE TRIGGER update_memory_relationships_updated_at 
    BEFORE UPDATE ON memory_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger function to automatically set expires_at and decay_lambda
CREATE OR REPLACE FUNCTION set_memory_defaults()
RETURNS TRIGGER AS $$
BEGIN
    -- Set expires_at if not explicitly provided
    IF NEW.expires_at IS NULL AND NEW.decay_tier != 'pinned' THEN
        NEW.expires_at := calculate_expires_at(NEW.decay_tier, NEW.created_at);
    END IF;
    
    -- Set default decay lambda if not explicitly provided
    IF NEW.decay_lambda IS NULL OR NEW.decay_lambda = 0.1 THEN
        CASE NEW.neuro_type
            WHEN 'episodic' THEN NEW.decay_lambda := 0.12;
            WHEN 'semantic' THEN NEW.decay_lambda := 0.04;
            WHEN 'procedural' THEN NEW.decay_lambda := 0.02;
            ELSE NEW.decay_lambda := 0.08;
        END CASE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to memories table
CREATE TRIGGER set_memory_defaults_trigger 
    BEFORE INSERT OR UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION set_memory_defaults();

-- ============================================================================
-- 7. Create views for common queries
-- ============================================================================

-- View for active memories with decay scores
CREATE OR REPLACE VIEW active_memories_with_decay AS
SELECT 
    m.*,
    calculate_decay_score(m.created_at, m.neuro_type, m.importance, m.access_count) as current_decay_score,
    CASE 
        WHEN calculate_decay_score(m.created_at, m.neuro_type, m.importance, m.access_count) < 0.1 THEN true
        ELSE false
    END as should_cleanup
FROM memories m
WHERE m.deleted_at IS NULL 
  AND (m.expires_at IS NULL OR m.expires_at > NOW())
  AND m.importance_decay > 0.05;

-- View for memory relationships with details
CREATE OR REPLACE VIEW memory_relationship_details AS
SELECT 
    mr.*,
    sm.text as source_content,
    sm.neuro_type as source_type,
    sm.importance as source_importance,
    dm.text as derived_content,
    dm.neuro_type as derived_type,
    dm.importance as derived_importance,
    sm.created_at as source_created_at,
    dm.created_at as derived_created_at
FROM memory_relationships mr
JOIN memories sm ON mr.source_memory_id = sm.id AND sm.deleted_at IS NULL
JOIN memories dm ON mr.derived_memory_id = dm.id AND dm.deleted_at IS NULL;

-- View for memory analytics by tenant
CREATE OR REPLACE VIEW memory_analytics_by_tenant AS
SELECT 
    user_id,
    org_id,
    neuro_type,
    memory_type,
    ui_source,
    COUNT(*) as total_count,
    AVG(importance) as avg_importance,
    AVG(access_count) as avg_access_count,
    AVG(calculate_decay_score(created_at, neuro_type, importance, access_count)) as avg_decay_score,
    COUNT(*) FILTER (WHERE ai_generated = true) as ai_generated_count,
    COUNT(*) FILTER (WHERE user_confirmed = true) as user_confirmed_count,
    COUNT(*) FILTER (WHERE decay_tier = 'pinned') as pinned_count,
    MAX(created_at) as latest_created,
    MIN(created_at) as earliest_created,
    SUM(access_count) as total_accesses
FROM memories
WHERE deleted_at IS NULL
GROUP BY user_id, org_id, neuro_type, memory_type, ui_source;

-- View for audit trail summary
CREATE OR REPLACE VIEW memory_audit_summary AS
SELECT 
    mal.user_id,
    mal.org_id,
    mal.access_type,
    DATE_TRUNC('day', mal.accessed_at) as access_date,
    COUNT(*) as access_count,
    COUNT(DISTINCT mal.memory_id) as unique_memories_accessed,
    AVG(mal.processing_time_ms) as avg_processing_time_ms,
    COUNT(*) FILTER (WHERE mal.response_status >= 400) as error_count
FROM memory_access_log mal
GROUP BY mal.user_id, mal.org_id, mal.access_type, DATE_TRUNC('day', mal.accessed_at);

-- ============================================================================
-- 8. Add comments for documentation
-- ============================================================================

COMMENT ON TABLE memories IS 'Unified memory storage table consolidating all memory types with tenant isolation and audit trails';
COMMENT ON TABLE memory_access_log IS 'Comprehensive audit log for all memory access operations with correlation tracking';
COMMENT ON TABLE memory_relationships IS 'Tracks relationships between memories for NeuroVault reflection and consolidation processes';

COMMENT ON COLUMN memories.user_id IS 'User identifier for tenant isolation';
COMMENT ON COLUMN memories.org_id IS 'Organization identifier for multi-tenant isolation';
COMMENT ON COLUMN memories.text IS 'The actual memory content text';
COMMENT ON COLUMN memories.embedding_id IS 'Reference to vector store embedding';
COMMENT ON COLUMN memories.importance IS 'User/AI assigned importance score (1-10)';
COMMENT ON COLUMN memories.decay_tier IS 'Memory decay tier: short (7d), medium (30d), long (180d), pinned (never)';
COMMENT ON COLUMN memories.tags IS 'JSON array of tags for organization and filtering';
COMMENT ON COLUMN memories.meta IS 'JSON object for additional metadata';
COMMENT ON COLUMN memories.expires_at IS 'Computed expiration timestamp based on decay policy';
COMMENT ON COLUMN memories.deleted_at IS 'Soft deletion timestamp for audit trails';
COMMENT ON COLUMN memories.version IS 'Version number for optimistic locking';

COMMENT ON FUNCTION calculate_decay_score IS 'Calculates current decay score for a memory based on type, age, importance, and access patterns';
COMMENT ON FUNCTION update_memory_access IS 'Updates access count and creates audit log entry for memory access';
COMMENT ON FUNCTION create_memory_relationship IS 'Creates a relationship between two memories and updates their relationship arrays';
COMMENT ON FUNCTION soft_delete_memory IS 'Soft deletes a memory with proper audit trail logging';
COMMENT ON FUNCTION calculate_expires_at IS 'Calculates expiration timestamp based on decay tier';

-- ============================================================================
-- 9. Create migration completion marker
-- ============================================================================

-- Insert migration record
INSERT INTO migration_history (service, migration_name, checksum, status)
VALUES (
    'postgres',
    '016_unified_memory_schema.sql',
    encode(digest('016_unified_memory_schema.sql', 'sha256'), 'hex'),
    'applied'
) ON CONFLICT (service, migration_name) DO UPDATE 
SET applied_at = NOW(), checksum = EXCLUDED.checksum, status = 'applied';

COMMIT;