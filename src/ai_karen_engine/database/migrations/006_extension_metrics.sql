-- Extension and hook monitoring tables

CREATE TABLE IF NOT EXISTS extensions (
  name         TEXT PRIMARY KEY,
  version      TEXT NOT NULL,
  category     TEXT,
  capabilities JSONB,
  directory    TEXT,
  status       TEXT NOT NULL,
  error_msg    TEXT,
  loaded_at    TIMESTAMP,
  updated_at   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS extension_usage (
  id              BIGSERIAL PRIMARY KEY,
  name            TEXT REFERENCES extensions(name) ON DELETE CASCADE,
  memory_mb       NUMERIC(10,2),
  cpu_percent     NUMERIC(5,2),
  disk_mb         NUMERIC(12,2),
  network_sent    BIGINT,
  network_recv    BIGINT,
  uptime_seconds  BIGINT,
  sampled_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ext_usage_name_time ON extension_usage(name, sampled_at DESC);

CREATE TABLE IF NOT EXISTS hooks (
  hook_id      TEXT PRIMARY KEY,
  hook_type    TEXT NOT NULL,
  source_type  TEXT NOT NULL,
  source_name  TEXT,
  priority     INT DEFAULT 50,
  enabled      BOOLEAN DEFAULT TRUE,
  conditions   JSONB,
  registered_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_hooks_type ON hooks(hook_type);
CREATE INDEX IF NOT EXISTS idx_hooks_enabled ON hooks(enabled);

CREATE TABLE IF NOT EXISTS hook_exec_stats (
  id           BIGSERIAL PRIMARY KEY,
  hook_type    TEXT,
  source_name  TEXT,
  executions   BIGINT DEFAULT 0,
  successes    BIGINT DEFAULT 0,
  errors       BIGINT DEFAULT 0,
  timeouts     BIGINT DEFAULT 0,
  avg_duration_ms INT DEFAULT 0,
  window_start TIMESTAMP,
  window_end   TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hook_exec_stats_type_window ON hook_exec_stats(hook_type, window_start);
