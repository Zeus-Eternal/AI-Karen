-- Create usage_counters and rate_limits tables

CREATE TABLE IF NOT EXISTS usage_counters (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT,
    user_id TEXT,
    metric TEXT NOT NULL,
    value BIGINT NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_counter_metric_window ON usage_counters(metric, window_start);

CREATE TABLE IF NOT EXISTS rate_limits (
    key TEXT PRIMARY KEY,
    limit_name TEXT,
    window_sec INT,
    max_count INT,
    current_count INT,
    window_reset TIMESTAMP
);
