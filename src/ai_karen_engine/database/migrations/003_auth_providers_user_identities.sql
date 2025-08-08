-- Migration: ensure auth_providers and user_identities tables exist with metadata
-- Adds tables for external authentication providers and user identities

CREATE TABLE IF NOT EXISTS auth_providers (
    provider_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    type TEXT NOT NULL,
    config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_identities (
    identity_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL REFERENCES auth_providers(provider_id),
    provider_user TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (provider_id, provider_user)
);

CREATE INDEX IF NOT EXISTS idx_user_identity_user ON user_identities(user_id);
