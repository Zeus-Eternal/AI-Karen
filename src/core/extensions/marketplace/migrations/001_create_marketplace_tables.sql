-- Extension Marketplace Database Schema Migration
-- Version: 001
-- Description: Create initial marketplace tables

-- Extension listings table
CREATE TABLE IF NOT EXISTS extension_listings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Marketplace metadata
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    price VARCHAR(50) DEFAULT 'free' NOT NULL,
    license VARCHAR(100) NOT NULL,
    support_url VARCHAR(500),
    documentation_url VARCHAR(500),
    repository_url VARCHAR(500),
    
    -- Statistics
    download_count INTEGER DEFAULT 0,
    rating_average FLOAT DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    -- Indexes
    CONSTRAINT extension_listings_name_check CHECK (name ~ '^[a-z0-9_-]+$'),
    CONSTRAINT extension_listings_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'deprecated', 'suspended')),
    CONSTRAINT extension_listings_rating_check CHECK (rating_average >= 0.0 AND rating_average <= 5.0)
);

-- Create indexes for extension listings
CREATE INDEX IF NOT EXISTS idx_extension_listings_name ON extension_listings(name);
CREATE INDEX IF NOT EXISTS idx_extension_listings_category ON extension_listings(category);
CREATE INDEX IF NOT EXISTS idx_extension_listings_status ON extension_listings(status);
CREATE INDEX IF NOT EXISTS idx_extension_listings_tags ON extension_listings USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_extension_listings_download_count ON extension_listings(download_count DESC);
CREATE INDEX IF NOT EXISTS idx_extension_listings_rating ON extension_listings(rating_average DESC);
CREATE INDEX IF NOT EXISTS idx_extension_listings_published ON extension_listings(published_at DESC);

-- Extension versions table
CREATE TABLE IF NOT EXISTS extension_versions (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES extension_listings(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    
    -- Version metadata
    changelog TEXT,
    is_stable BOOLEAN DEFAULT TRUE,
    min_kari_version VARCHAR(50),
    max_kari_version VARCHAR(50),
    
    -- Package information
    package_url VARCHAR(500),
    package_size INTEGER,
    package_hash VARCHAR(128),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    -- Constraints
    UNIQUE(listing_id, version),
    CONSTRAINT extension_versions_version_check CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$')
);

-- Create indexes for extension versions
CREATE INDEX IF NOT EXISTS idx_extension_versions_listing ON extension_versions(listing_id);
CREATE INDEX IF NOT EXISTS idx_extension_versions_version ON extension_versions(listing_id, version);
CREATE INDEX IF NOT EXISTS idx_extension_versions_stable ON extension_versions(listing_id, is_stable, created_at DESC);

-- Extension dependencies table
CREATE TABLE IF NOT EXISTS extension_dependencies (
    id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL REFERENCES extension_versions(id) ON DELETE CASCADE,
    
    -- Dependency details
    dependency_type VARCHAR(50) NOT NULL,
    dependency_name VARCHAR(255) NOT NULL,
    version_constraint VARCHAR(100),
    is_optional BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT extension_dependencies_type_check CHECK (dependency_type IN ('extension', 'plugin', 'system_service'))
);

-- Create indexes for extension dependencies
CREATE INDEX IF NOT EXISTS idx_extension_dependencies_version ON extension_dependencies(version_id);
CREATE INDEX IF NOT EXISTS idx_extension_dependencies_name ON extension_dependencies(dependency_name);

-- Extension installations table
CREATE TABLE IF NOT EXISTS extension_installations (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES extension_listings(id) ON DELETE CASCADE,
    version_id INTEGER NOT NULL REFERENCES extension_versions(id) ON DELETE CASCADE,
    
    -- Installation context
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    
    -- Installation status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    
    -- Configuration
    config JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    installed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(listing_id, tenant_id),
    CONSTRAINT extension_installations_status_check CHECK (status IN ('pending', 'installing', 'installed', 'failed', 'updating', 'uninstalling'))
);

-- Create indexes for extension installations
CREATE INDEX IF NOT EXISTS idx_extension_installations_tenant ON extension_installations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_extension_installations_user ON extension_installations(user_id);
CREATE INDEX IF NOT EXISTS idx_extension_installations_status ON extension_installations(status);
CREATE INDEX IF NOT EXISTS idx_extension_installations_listing_tenant ON extension_installations(listing_id, tenant_id);

-- Extension reviews table
CREATE TABLE IF NOT EXISTS extension_reviews (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES extension_listings(id) ON DELETE CASCADE,
    
    -- Review details
    user_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL,
    title VARCHAR(255),
    comment TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(listing_id, user_id),
    CONSTRAINT extension_reviews_rating_check CHECK (rating >= 1 AND rating <= 5)
);

-- Create indexes for extension reviews
CREATE INDEX IF NOT EXISTS idx_extension_reviews_listing ON extension_reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_extension_reviews_user ON extension_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_extension_reviews_rating ON extension_reviews(rating);

-- Create trigger to update extension listing statistics when reviews change
CREATE OR REPLACE FUNCTION update_extension_rating_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE extension_listings 
    SET 
        rating_average = (
            SELECT COALESCE(AVG(rating::float), 0.0) 
            FROM extension_reviews 
            WHERE listing_id = COALESCE(NEW.listing_id, OLD.listing_id)
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM extension_reviews 
            WHERE listing_id = COALESCE(NEW.listing_id, OLD.listing_id)
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.listing_id, OLD.listing_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for rating statistics
DROP TRIGGER IF EXISTS trigger_update_rating_stats_insert ON extension_reviews;
CREATE TRIGGER trigger_update_rating_stats_insert
    AFTER INSERT ON extension_reviews
    FOR EACH ROW EXECUTE FUNCTION update_extension_rating_stats();

DROP TRIGGER IF EXISTS trigger_update_rating_stats_update ON extension_reviews;
CREATE TRIGGER trigger_update_rating_stats_update
    AFTER UPDATE ON extension_reviews
    FOR EACH ROW EXECUTE FUNCTION update_extension_rating_stats();

DROP TRIGGER IF EXISTS trigger_update_rating_stats_delete ON extension_reviews;
CREATE TRIGGER trigger_update_rating_stats_delete
    AFTER DELETE ON extension_reviews
    FOR EACH ROW EXECUTE FUNCTION update_extension_rating_stats();

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers to relevant tables
DROP TRIGGER IF EXISTS trigger_extension_listings_updated_at ON extension_listings;
CREATE TRIGGER trigger_extension_listings_updated_at
    BEFORE UPDATE ON extension_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_extension_installations_updated_at ON extension_installations;
CREATE TRIGGER trigger_extension_installations_updated_at
    BEFORE UPDATE ON extension_installations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_extension_reviews_updated_at ON extension_reviews;
CREATE TRIGGER trigger_extension_reviews_updated_at
    BEFORE UPDATE ON extension_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO extension_listings (
    name, display_name, description, author, category, tags, status, license, published_at
) VALUES 
(
    'advanced-analytics',
    'Advanced Analytics Dashboard',
    'Comprehensive analytics and reporting extension with interactive charts and real-time data visualization.',
    'Analytics Corp',
    'analytics',
    '["dashboard", "reporting", "charts", "visualization"]'::jsonb,
    'approved',
    'MIT',
    NOW()
),
(
    'workflow-automation',
    'Workflow Automation Engine',
    'AI-powered workflow automation that understands natural language instructions and orchestrates plugins automatically.',
    'Automation Inc',
    'automation',
    '["workflow", "automation", "ai", "orchestration"]'::jsonb,
    'approved',
    'Apache-2.0',
    NOW()
),
(
    'crm-integration',
    'CRM Integration Suite',
    'Connect your Kari AI platform with popular CRM systems like Salesforce, HubSpot, and Pipedrive.',
    'Integration Solutions',
    'crm',
    '["crm", "integration", "salesforce", "hubspot"]'::jsonb,
    'approved',
    'Commercial',
    NOW()
)
ON CONFLICT (name) DO NOTHING;

-- Insert sample versions
INSERT INTO extension_versions (
    listing_id, version, manifest, changelog, is_stable, package_url
) 
SELECT 
    el.id,
    '1.0.0',
    '{"name": "' || el.name || '", "version": "1.0.0", "api_version": "1.0"}'::jsonb,
    'Initial release with core functionality',
    true,
    'https://marketplace.kari.ai/packages/' || el.name || '/1.0.0.tar.gz'
FROM extension_listings el
WHERE NOT EXISTS (
    SELECT 1 FROM extension_versions ev 
    WHERE ev.listing_id = el.id AND ev.version = '1.0.0'
);

COMMIT;