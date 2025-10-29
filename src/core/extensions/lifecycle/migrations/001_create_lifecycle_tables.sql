-- Extension Lifecycle Management Tables

-- Extension health monitoring
CREATE TABLE IF NOT EXISTS extension_health (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_check TIMESTAMP NOT NULL,
    cpu_usage FLOAT DEFAULT 0,
    memory_usage FLOAT DEFAULT 0,
    disk_usage FLOAT DEFAULT 0,
    error_rate FLOAT DEFAULT 0,
    response_time FLOAT DEFAULT 0,
    uptime FLOAT DEFAULT 0,
    restart_count INTEGER DEFAULT 0,
    last_error TEXT,
    health_score FLOAT DEFAULT 0,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(extension_name)
);

-- Extension backups
CREATE TABLE IF NOT EXISTS extension_backups (
    id SERIAL PRIMARY KEY,
    backup_id VARCHAR(255) UNIQUE NOT NULL,
    extension_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    size_bytes BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    checksum VARCHAR(255) NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    description TEXT,
    tenant_id VARCHAR(255),
    created_by VARCHAR(255)
);

-- Extension migrations
CREATE TABLE IF NOT EXISTS extension_migrations (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(255) UNIQUE NOT NULL,
    extension_name VARCHAR(255) NOT NULL,
    from_version VARCHAR(50) NOT NULL,
    to_version VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    migration_steps JSONB DEFAULT '[]',
    rollback_plan JSONB DEFAULT '[]',
    error_message TEXT,
    backup_id VARCHAR(255),
    tenant_id VARCHAR(255),
    initiated_by VARCHAR(255)
);

-- Extension snapshots
CREATE TABLE IF NOT EXISTS extension_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(255) UNIQUE NOT NULL,
    extension_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    state JSONB DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    data_checksum VARCHAR(255) NOT NULL,
    is_restorable BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(255)
);

-- Lifecycle events
CREATE TABLE IF NOT EXISTS extension_lifecycle_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    extension_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    details JSONB DEFAULT '{}',
    user_id VARCHAR(255),
    tenant_id VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Recovery actions
CREATE TABLE IF NOT EXISTS extension_recovery_actions (
    id SERIAL PRIMARY KEY,
    action_id VARCHAR(255) UNIQUE NOT NULL,
    extension_name VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    trigger_condition VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    max_attempts INTEGER DEFAULT 3,
    cooldown_seconds INTEGER DEFAULT 300,
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    tenant_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Health check configurations
CREATE TABLE IF NOT EXISTS extension_health_configs (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    check_interval_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,
    failure_threshold INTEGER DEFAULT 3,
    success_threshold INTEGER DEFAULT 1,
    enabled_checks JSONB DEFAULT '[]',
    thresholds JSONB DEFAULT '{}',
    custom_checks JSONB DEFAULT '[]',
    tenant_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(extension_name, tenant_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_extension_health_name ON extension_health(extension_name);
CREATE INDEX IF NOT EXISTS idx_extension_health_status ON extension_health(status);
CREATE INDEX IF NOT EXISTS idx_extension_health_last_check ON extension_health(last_check);

CREATE INDEX IF NOT EXISTS idx_extension_backups_name ON extension_backups(extension_name);
CREATE INDEX IF NOT EXISTS idx_extension_backups_created ON extension_backups(created_at);
CREATE INDEX IF NOT EXISTS idx_extension_backups_type ON extension_backups(backup_type);

CREATE INDEX IF NOT EXISTS idx_extension_migrations_name ON extension_migrations(extension_name);
CREATE INDEX IF NOT EXISTS idx_extension_migrations_status ON extension_migrations(status);
CREATE INDEX IF NOT EXISTS idx_extension_migrations_started ON extension_migrations(started_at);

CREATE INDEX IF NOT EXISTS idx_extension_snapshots_name ON extension_snapshots(extension_name);
CREATE INDEX IF NOT EXISTS idx_extension_snapshots_created ON extension_snapshots(created_at);

CREATE INDEX IF NOT EXISTS idx_lifecycle_events_name ON extension_lifecycle_events(extension_name);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_type ON extension_lifecycle_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_timestamp ON extension_lifecycle_events(timestamp);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_name ON extension_recovery_actions(extension_name);
CREATE INDEX IF NOT EXISTS idx_recovery_actions_enabled ON extension_recovery_actions(is_enabled);

CREATE INDEX IF NOT EXISTS idx_health_configs_name ON extension_health_configs(extension_name);