#!/bin/bash
set -e

# DuckDB Initialization Script for AI Karen
# This script sets up DuckDB database files and schemas

echo "🦆 Initializing DuckDB for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Set DuckDB path
PROJECT_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DUCKDB_PATH="${DUCKDB_PATH:-$PROJECT_ROOT/data/duckdb/kari_duckdb.db}"
DUCKDB_DIR=$(dirname "$DUCKDB_PATH")

# Create DuckDB directory if it doesn't exist
log "Creating DuckDB directory: $DUCKDB_DIR"
mkdir -p "$DUCKDB_DIR"

# Create backup directory
BACKUP_DIR="${DUCKDB_BACKUP_PATH:-$PROJECT_ROOT/data/duckdb/backups}"
log "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Initialize DuckDB database using Docker
log "Initializing DuckDB database at: $DUCKDB_PATH"

# First, create an empty database file using Docker
log "Creating empty DuckDB database file..."
# Create the database file inside the container first
docker run --rm -v "$PROJECT_ROOT":/project -w /project alpine:latest sh -c "mkdir -p /project/data/duckdb"
# Create the database file in a temporary location inside the container
docker run --rm -v "$PROJECT_ROOT":/project -w /project duckdb/duckdb:latest duckdb /tmp/kari_duckdb.db "CREATE TABLE temp_table (id INTEGER); DROP TABLE temp_table;"
# Copy the database file from the container to the host
docker run --rm -v "$PROJECT_ROOT":/project -w /project alpine:latest sh -c "cp /tmp/kari_duckdb.db /project/data/duckdb/kari_duckdb.db"

# Check if the database file was created
if [ ! -f "$DUCKDB_PATH" ]; then
    log "ERROR" "Failed to create DuckDB database file at $DUCKDB_PATH"
    exit 1
fi

log "DuckDB database file created successfully"

# Create database file and initial schema using Docker
# Create a temporary SQL file
cat > /tmp/duckdb_init.sql << 'EOF'
-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
    user_id VARCHAR PRIMARY KEY,
    profile_json VARCHAR,
    last_update TIMESTAMP
);

-- Create profile history table
CREATE TABLE IF NOT EXISTS profile_history (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR,
    timestamp DOUBLE,
    field VARCHAR,
    old VARCHAR,
    new VARCHAR
);

-- Create long term memory table
CREATE TABLE IF NOT EXISTS long_term_memory (
    user_id VARCHAR,
    memory_json VARCHAR
);

-- Create user roles table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id VARCHAR,
    role VARCHAR
);

-- Create service health tracking table
CREATE TABLE IF NOT EXISTS service_health (
    service_name VARCHAR PRIMARY KEY,
    status VARCHAR NOT NULL,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata VARCHAR -- JSON as string since DuckDB has limited JSON support
);

-- Create migration tracking table
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY,
    service VARCHAR(50) NOT NULL DEFAULT 'duckdb',
    migration_name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);

-- Insert initial migration records
INSERT OR IGNORE INTO migration_history (migration_name, applied_at) VALUES
    ('001_create_profile_tables.sql', CURRENT_TIMESTAMP),
    ('002_create_history_tables.sql', CURRENT_TIMESTAMP),
    ('003_create_indexes.sql', CURRENT_TIMESTAMP);

-- Insert initial health record
INSERT OR REPLACE INTO service_health (service_name, status, metadata) VALUES
    ('duckdb', 'healthy', '{"version": "latest", "initialized_at": "' || CURRENT_TIMESTAMP || '", "database_path": "' || '$DUCKDB_PATH' || '"}');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_last_update ON profiles(last_update);
CREATE INDEX IF NOT EXISTS idx_profile_history_user_id ON profile_history(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_history_timestamp ON profile_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);

-- Create views for common queries
CREATE OR REPLACE VIEW recent_profile_changes AS
SELECT
    user_id,
    field,
    old,
    new,
    timestamp,
    datetime(timestamp, 'unixepoch') as timestamp_readable
FROM profile_history
WHERE timestamp > (strftime('%s', 'now') - 86400) -- Last 24 hours
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    user_id,
    COUNT(*) as total_changes,
    MAX(timestamp) as last_activity,
    datetime(MAX(timestamp), 'unixepoch') as last_activity_readable,
    COUNT(DISTINCT field) as fields_modified
FROM profile_history
GROUP BY user_id
ORDER BY last_activity DESC;
EOF

# Run the SQL file using Docker
log "Running SQL initialization script..."
docker run --rm -v "$PROJECT_ROOT":/project -v /tmp:/tmp -w /project duckdb/duckdb:latest duckdb "$DUCKDB_PATH" < /tmp/duckdb_init.sql

# Clean up the temporary file
rm -f /tmp/duckdb_init.sql

# Verify the database file still exists after initialization
if [ ! -f "$DUCKDB_PATH" ]; then
    log "ERROR" "DuckDB database file disappeared after initialization"
    exit 1
fi

log "DuckDB database initialization completed"

# Create a simple backup (only if database file exists)
if [ -f "$DUCKDB_PATH" ]; then
    log "Creating initial backup..."
    BACKUP_FILE="$BACKUP_DIR/initial_backup_$(date +%Y%m%d_%H%M%S).db"
    cp "$DUCKDB_PATH" "$BACKUP_FILE"
    log "Initial backup created: $BACKUP_FILE"
else
    log "Database file not found, skipping backup creation"
fi

# Verify database integrity
log "Verifying database integrity..."

# Create a temporary SQL file for verification
cat > /tmp/duckdb_verify.sql << 'EOF'
-- Check table counts
SELECT 'profiles' as table_name, COUNT(*) as row_count FROM profiles
UNION ALL
SELECT 'profile_history' as table_name, COUNT(*) as row_count FROM profile_history
UNION ALL
SELECT 'long_term_memory' as table_name, COUNT(*) as row_count FROM long_term_memory
UNION ALL
SELECT 'user_roles' as table_name, COUNT(*) as row_count FROM user_roles;

-- Check service health
SELECT * FROM service_health WHERE service_name = 'duckdb';

-- Update health status
UPDATE service_health 
SET 
    status = 'initialized',
    last_check = CURRENT_TIMESTAMP,
    metadata = '{"tables_verified": true, "backup_created": true, "database_size": "initialized"}'
WHERE service_name = 'duckdb';
EOF

# Run the verification SQL file using Docker
docker run --rm -v "$PROJECT_ROOT":/project -v /tmp:/tmp -w /project duckdb/duckdb:latest duckdb "$DUCKDB_PATH" < /tmp/duckdb_verify.sql

# Clean up the temporary file
rm -f /tmp/duckdb_verify.sql

# Set proper permissions (only if database file exists)
if [ -f "$DUCKDB_PATH" ]; then
    chmod 644 "$DUCKDB_PATH"
fi
chmod -R 755 "$DUCKDB_DIR"
chmod -R 755 "$BACKUP_DIR"

log "🎉 DuckDB initialization completed successfully!"
log "Database file: $DUCKDB_PATH"
log "Backup directory: $BACKUP_DIR"
log "Tables created: profiles, profile_history, long_term_memory, user_roles"
log "Views created: recent_profile_changes, user_activity_summary"

# Display database info (only if database file exists)
if [ -f "$DUCKDB_PATH" ]; then
    log "Database information:"
    docker run --rm -v "$PROJECT_ROOT":/project -w /project duckdb/duckdb:latest duckdb "$DUCKDB_PATH" -c ".tables"
else
    log "Database file not found, skipping database information display"
fi