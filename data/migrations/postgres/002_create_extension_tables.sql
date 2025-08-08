-- Extension system database schema
-- This migration creates tables for the extension registry and related data

-- Extension registry table
CREATE TABLE IF NOT EXISTS extension_registry (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'inactive',
    installed_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    tenant_id VARCHAR(255), -- NULL for global extensions
    installed_by VARCHAR(255),

    CONSTRAINT extension_status_check CHECK (status IN ('inactive', 'loading', 'active', 'error', 'unloading'))
);

-- Extension permissions table
CREATE TABLE IF NOT EXISTS extension_permissions (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    permission VARCHAR(255) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by VARCHAR(255),

    FOREIGN KEY (extension_name) REFERENCES extension_registry(name) ON DELETE CASCADE,
    UNIQUE(extension_name, tenant_id, user_id, permission)
);

-- Extension configuration table
CREATE TABLE IF NOT EXISTS extension_config (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),

    FOREIGN KEY (extension_name) REFERENCES extension_registry(name) ON DELETE CASCADE,
    UNIQUE(extension_name, tenant_id, config_key)
);

-- Extension metrics table
CREATE TABLE IF NOT EXISTS extension_metrics (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (extension_name) REFERENCES extension_registry(name) ON DELETE CASCADE
);

-- Extension audit log table
CREATE TABLE IF NOT EXISTS extension_audit_log (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (extension_name) REFERENCES extension_registry(name) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_extension_registry_status ON extension_registry(status);
CREATE INDEX IF NOT EXISTS idx_extension_registry_tenant ON extension_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_extension_permissions_tenant_user ON extension_permissions(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_extension_config_tenant ON extension_config(tenant_id);
CREATE INDEX IF NOT EXISTS idx_extension_metrics_name_timestamp ON extension_metrics(extension_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_extension_audit_timestamp ON extension_audit_log(timestamp);

-- Update trigger for extension_registry
CREATE OR REPLACE FUNCTION update_extension_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER extension_registry_update_timestamp
    BEFORE UPDATE ON extension_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_extension_registry_timestamp();

-- Update trigger for extension_config
CREATE OR REPLACE FUNCTION update_extension_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER extension_config_update_timestamp
    BEFORE UPDATE ON extension_config
    FOR EACH ROW
    EXECUTE FUNCTION update_extension_config_timestamp();

-- Marketplace extension metadata
CREATE TABLE IF NOT EXISTS marketplace_extensions (
    extension_id TEXT PRIMARY KEY,
    latest_version TEXT,
    title TEXT,
    author TEXT,
    summary TEXT,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Installed extension records
CREATE TABLE IF NOT EXISTS installed_extensions (
    id SERIAL PRIMARY KEY,
    extension_id TEXT REFERENCES marketplace_extensions(extension_id) ON DELETE SET NULL,
    version TEXT,
    installed_by TEXT REFERENCES auth_users(user_id) ON DELETE SET NULL,
    installed_at TIMESTAMP DEFAULT NOW(),
    source TEXT,
    directory TEXT
);
