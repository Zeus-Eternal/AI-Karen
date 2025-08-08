-- RBAC and API key tables with constraints

-- Create roles table if it does not exist
CREATE TABLE IF NOT EXISTS roles (
  role_id     TEXT PRIMARY KEY,
  tenant_id   TEXT,
  name        TEXT NOT NULL,
  description TEXT,
  created_at  TIMESTAMP DEFAULT now(),
  UNIQUE (tenant_id, name)
);

-- Create role_permissions table if it does not exist
CREATE TABLE IF NOT EXISTS role_permissions (
  role_id    TEXT REFERENCES roles(role_id) ON DELETE CASCADE,
  permission TEXT NOT NULL,
  scope      TEXT,
  PRIMARY KEY (role_id, permission, scope)
);

-- Create api_keys table if it does not exist
CREATE TABLE IF NOT EXISTS api_keys (
  key_id       TEXT PRIMARY KEY,
  tenant_id    TEXT,
  user_id      TEXT REFERENCES auth_users(user_id) ON DELETE SET NULL,
  hashed_key   TEXT NOT NULL,
  name         TEXT,
  scopes       JSONB NOT NULL,
  last_used_at TIMESTAMP,
  created_at   TIMESTAMP DEFAULT now(),
  expires_at   TIMESTAMP,
  UNIQUE (hashed_key)
);

-- Ensure role names are unique per tenant
ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_tenant_name ON roles(tenant_id, name);

-- Ensure hashed API keys are unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_hashed_key ON api_keys(hashed_key);
