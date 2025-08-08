-- Migration: create tables for LLM provider configurations and request metrics
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    encrypted_config BYTEA NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    provider_name VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    tenant_id VARCHAR(255),
    user_id VARCHAR(255),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost NUMERIC(10,4),
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_requests_provider_time ON llm_requests(provider_name, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_requests_tenant_time ON llm_requests(tenant_id, created_at);
