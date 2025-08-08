-- Migration: Create audit_log table
-- Date: 2025-07-24
-- Stores audit logging information per tenant

CREATE TABLE IF NOT EXISTS audit_log (
    event_id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT,
    user_id TEXT,
    actor_type TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
