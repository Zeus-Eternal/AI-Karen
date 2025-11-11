-- 015_neuro_vault_schema_extensions.sql
-- NeuroVault Memory System Database Schema Extensions
-- Extends existing memory_items table with tri-partite memory capabilities

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Extend existing memory_items table with NeuroVault-specific columns
-- ============================================================================

-- Add NeuroVault columns to existing memory_items table
ALTER TABLE memory_items 
ADD COLUMN IF NOT EXISTS neuro_type VARCHAR(20) DEFAULT 'episodic',
ADD COLUMN IF NOT EXISTS decay_lambda REAL DEFAULT 0.1,
ADD COLUMN IF NOT EXISTS reflection_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS source_memories JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS derived_memories JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS importance_decay REAL DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS last_reflection TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS importance_score INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS user_id UUID,
ADD COLUMN IF NOT EXISTS tenant_id UUID,
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS memory_type VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS ui_source VARCHAR(50) DEFAULT 'api',
ADD COLUMN IF NOT EXISTS conversation_id UUID,
ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS user_confirmed BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb;

-- ============================================================================
-- 2. Create memory relationships table for tracking derivations
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL,
    derived_memory_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'reflection', 'consolidation', 'pattern', 'decay_promotion'
    confidence_score REAL DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_source_memory FOREIGN KEY (source_memory_id) REFERENCES memory_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_derived_memory FOREIGN KEY (derived_memory_id) REFERENCES memory_items(id) ON DELETE CASCADE,
    
    -- Ensure valid relationship types
    CONSTRAINT chk_relationship_type CHECK (relationship_type IN ('reflection', 'consolidation', 'pattern', 'decay_promotion', 'semantic_link')),
    
    -- Ensure confidence score is valid
    CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Prevent self-referential relationships
    CONSTRAINT chk_no_self_reference CHECK (source_memory_id != derived_memory_id)
);

-- ============================================================================
-- 3. Create indexes for efficient querying by memory type and decay
-- ============================================================================

-- Indexes for NeuroVault-specific queries on memory_items
CREATE INDEX IF NOT EXISTS idx_memory_items_neuro_type ON memory_items(neuro_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_decay ON memory_items(decay_lambda, last_accessed) WHERE last_accessed IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_reflection ON memory_items(last_reflection) WHERE last_reflection IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_importance ON memory_items(importance_score DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_access_count ON memory_items(access_count DESC, last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_tenant_user ON memory_items(tenant_id, user_id) WHERE tenant_id IS NOT NULL AND user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_conversation ON memory_items(conversation_id, created_at DESC) WHERE conversation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_session ON memory_items(session_id, created_at DESC) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_memory_type ON memory_items(memory_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_ui_source ON memory_items(ui_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_ai_generated ON memory_items(ai_generated, user_confirmed);
CREATE INDEX IF NOT EXISTS idx_memory_items_tags ON memory_items USING gin(tags) WHERE tags IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_memory_items_neuro_importance ON memory_items(neuro_type, importance_score DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_items_tenant_neuro ON memory_items(tenant_id, neuro_type, created_at DESC) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_user_neuro ON memory_items(user_id, neuro_type, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_items_decay_cleanup ON memory_items(neuro_type, importance_decay, last_accessed) WHERE importance_decay < 0.1;

-- Indexes for memory_relationships table
CREATE INDEX IF NOT EXISTS idx_memory_relationships_source ON memory_relationships(source_memory_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_derived ON memory_relationships(derived_memory_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_type ON memory_relationships(relationship_type, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_created ON memory_relationships(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_relationships_confidence ON memory_relationships(confidence_score DESC, created_at DESC);

-- Unique constraint to prevent duplicate relationships
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_relationships_unique 
ON memory_relationships(source_memory_id, derived_memory_id, relationship_type);

-- ============================================================================
-- 4. Add constraints and validation
-- ============================================================================

-- Add constraints to memory_items for NeuroVault fields
ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_neuro_type 
CHECK (neuro_type IN ('episodic', 'semantic', 'procedural', 'general', 'fact', 'preference', 'context', 'conversation', 'insight'));

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_decay_lambda 
CHECK (decay_lambda >= 0.0 AND decay_lambda <= 1.0);

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_importance_decay 
CHECK (importance_decay >= 0.0 AND importance_decay <= 1.0);

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_reflection_count 
CHECK (reflection_count >= 0);

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_importance_score 
CHECK (importance_score >= 1 AND importance_score <= 10);

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_access_count 
CHECK (access_count >= 0);

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_memory_type 
CHECK (memory_type IN ('general', 'fact', 'preference', 'context', 'conversation', 'insight', 'episodic', 'semantic', 'procedural'));

ALTER TABLE memory_items 
ADD CONSTRAINT IF NOT EXISTS chk_ui_source 
CHECK (ui_source IN ('web', 'desktop', 'api', 'ag_ui'));

-- ============================================================================
-- 5. Create helper functions for NeuroVault operations
-- ============================================================================

-- Function to calculate decay score based on memory type and age
CREATE OR REPLACE FUNCTION calculate_decay_score(
    memory_created_at TIMESTAMPTZ,
    memory_neuro_type VARCHAR,
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
CREATE OR REPLACE FUNCTION update_memory_access(memory_id UUID) RETURNS VOID AS $$
BEGIN
    UPDATE memory_items 
    SET 
        access_count = COALESCE(access_count, 0) + 1,
        last_accessed = NOW()
    WHERE id = memory_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create memory relationship
CREATE OR REPLACE FUNCTION create_memory_relationship(
    source_id UUID,
    derived_id UUID,
    rel_type VARCHAR,
    confidence REAL DEFAULT 1.0,
    rel_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    relationship_id UUID;
BEGIN
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
    UPDATE memory_items 
    SET derived_memories = COALESCE(derived_memories, '[]'::jsonb) || jsonb_build_array(derived_id::text)
    WHERE id = source_id;
    
    UPDATE memory_items 
    SET source_memories = COALESCE(source_memories, '[]'::jsonb) || jsonb_build_array(source_id::text)
    WHERE id = derived_id;
    
    RETURN relationship_id;
END;
$$ LANGUAGE plpgsql;

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

-- Apply trigger to memory_relationships table
CREATE TRIGGER update_memory_relationships_updated_at 
    BEFORE UPDATE ON memory_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger function to automatically set decay lambda based on neuro_type
CREATE OR REPLACE FUNCTION set_default_decay_lambda()
RETURNS TRIGGER AS $$
BEGIN
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

-- Apply trigger to memory_items table
CREATE TRIGGER set_memory_decay_lambda 
    BEFORE INSERT OR UPDATE ON memory_items
    FOR EACH ROW EXECUTE FUNCTION set_default_decay_lambda();

-- ============================================================================
-- 7. Create views for common NeuroVault queries
-- ============================================================================

-- View for active memories with decay scores
CREATE OR REPLACE VIEW active_memories_with_decay AS
SELECT 
    m.*,
    calculate_decay_score(m.created_at, m.neuro_type, m.importance_score, m.access_count) as current_decay_score,
    CASE 
        WHEN calculate_decay_score(m.created_at, m.neuro_type, m.importance_score, m.access_count) < 0.1 THEN true
        ELSE false
    END as should_cleanup
FROM memory_items m
WHERE m.importance_decay > 0.05; -- Only show memories that haven't decayed too much

-- View for memory relationships with details
CREATE OR REPLACE VIEW memory_relationship_details AS
SELECT 
    mr.*,
    sm.content as source_content,
    sm.neuro_type as source_type,
    dm.content as derived_content,
    dm.neuro_type as derived_type,
    sm.created_at as source_created_at,
    dm.created_at as derived_created_at
FROM memory_relationships mr
JOIN memory_items sm ON mr.source_memory_id = sm.id
JOIN memory_items dm ON mr.derived_memory_id = dm.id;

-- View for memory analytics
CREATE OR REPLACE VIEW memory_analytics AS
SELECT 
    neuro_type,
    COUNT(*) as total_count,
    AVG(importance_score) as avg_importance,
    AVG(access_count) as avg_access_count,
    AVG(calculate_decay_score(created_at, neuro_type, importance_score, access_count)) as avg_decay_score,
    COUNT(*) FILTER (WHERE ai_generated = true) as ai_generated_count,
    COUNT(*) FILTER (WHERE user_confirmed = true) as user_confirmed_count,
    MAX(created_at) as latest_created,
    MIN(created_at) as earliest_created
FROM memory_items
GROUP BY neuro_type;

-- ============================================================================
-- 8. Grant permissions (adjust as needed for your setup)
-- ============================================================================

-- Note: Uncomment and adjust these grants based on your application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_items TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_relationships TO your_app_user;
-- GRANT SELECT ON active_memories_with_decay TO your_app_user;
-- GRANT SELECT ON memory_relationship_details TO your_app_user;
-- GRANT SELECT ON memory_analytics TO your_app_user;
-- GRANT EXECUTE ON FUNCTION calculate_decay_score TO your_app_user;
-- GRANT EXECUTE ON FUNCTION update_memory_access TO your_app_user;
-- GRANT EXECUTE ON FUNCTION create_memory_relationship TO your_app_user;

-- ============================================================================
-- 9. Add comments for documentation
-- ============================================================================

COMMENT ON TABLE memory_relationships IS 'Tracks relationships between memories for NeuroVault reflection and consolidation processes';
COMMENT ON COLUMN memory_items.neuro_type IS 'Tri-partite memory type: episodic, semantic, or procedural';
COMMENT ON COLUMN memory_items.decay_lambda IS 'Decay rate parameter for this memory type';
COMMENT ON COLUMN memory_items.reflection_count IS 'Number of times this memory has been processed by reflection engine';
COMMENT ON COLUMN memory_items.source_memories IS 'JSON array of memory IDs that contributed to creating this memory';
COMMENT ON COLUMN memory_items.derived_memories IS 'JSON array of memory IDs that were derived from this memory';
COMMENT ON COLUMN memory_items.importance_decay IS 'Current importance after applying decay (0.0 to 1.0)';
COMMENT ON COLUMN memory_items.last_reflection IS 'Timestamp of last reflection processing';
COMMENT ON FUNCTION calculate_decay_score IS 'Calculates current decay score for a memory based on type, age, importance, and access patterns';
COMMENT ON FUNCTION update_memory_access IS 'Updates access count and last accessed timestamp for a memory';
COMMENT ON FUNCTION create_memory_relationship IS 'Creates a relationship between two memories and updates their relationship arrays';

COMMIT;