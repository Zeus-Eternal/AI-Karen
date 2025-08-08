-- Migration: add 2FA and provider metadata columns
-- Ensures auth_users has two-factor and login tracking fields
-- Adds metadata column to auth_providers

ALTER TABLE auth_users
    ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS two_factor_secret TEXT,
    ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

ALTER TABLE auth_providers
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
