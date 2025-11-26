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

# Initialize DuckDB database
log "Initializing DuckDB database at: $DUCKDB_PATH"

# Create a simple initialization script
cat > /tmp/duckdb_init.py << 'EOF'
import sqlite3
import os
import json
import sys
from datetime import datetime

# Connect to the DuckDB database (which uses SQLite syntax for basic operations)
db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create profiles table
cursor.execute('''
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    profile_json TEXT,
    last_update TIMESTAMP
)
''')

# Create profile history table
cursor.execute('''
CREATE TABLE IF NOT EXISTS profile_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    timestamp REAL,
    field TEXT,
    old TEXT,
    new TEXT
)
''')

# Create long term memory table
cursor.execute('''
CREATE TABLE IF NOT EXISTS long_term_memory (
    user_id TEXT,
    memory_json TEXT
)
''')

# Create user roles table
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT,
    role TEXT
)
''')

# Create service health tracking table
cursor.execute('''
CREATE TABLE IF NOT EXISTS service_health (
    service_name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON as string
)
''')

# Create migration tracking table
cursor.execute('''
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY,
    service TEXT NOT NULL DEFAULT 'duckdb',
    migration_name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT
)
''')

# Insert initial migration records
cursor.execute("INSERT OR IGNORE INTO migration_history (migration_name, applied_at) VALUES ('001_create_profile_tables.sql', CURRENT_TIMESTAMP)")
cursor.execute("INSERT OR IGNORE INTO migration_history (migration_name, applied_at) VALUES ('002_create_history_tables.sql', CURRENT_TIMESTAMP)")
cursor.execute("INSERT OR IGNORE INTO migration_history (migration_name, applied_at) VALUES ('003_create_indexes.sql', CURRENT_TIMESTAMP)")

# Insert initial health record
metadata = json.dumps({
    "version": "latest",
    "initialized_at": datetime.now().isoformat(),
    "database_path": db_path
})
cursor.execute("INSERT OR REPLACE INTO service_health (service_name, status, metadata) VALUES (?, ?, ?)", 
               ('duckdb', 'healthy', metadata))

# Create indexes for better performance
cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_last_update ON profiles(last_update)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_history_user_id ON profile_history(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_history_timestamp ON profile_history(timestamp)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role)')

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print(f"DuckDB database initialized at {db_path}")
EOF

# Run the Python script
python3 /tmp/duckdb_init.py "$DUCKDB_PATH"

# Clean up
rm -f /tmp/duckdb_init.py

# Verify the database file was created
if [ ! -f "$DUCKDB_PATH" ]; then
    log "ERROR" "Failed to create DuckDB database file at $DUCKDB_PATH"
    exit 1
fi

log "DuckDB database file created successfully"

# Create a simple backup
if [ -f "$DUCKDB_PATH" ]; then
    log "Creating initial backup..."
    BACKUP_FILE="$BACKUP_DIR/initial_backup_$(date +%Y%m%d_%H%M%S).db"
    cp "$DUCKDB_PATH" "$BACKUP_FILE"
    log "Initial backup created: $BACKUP_FILE"
else
    log "Database file not found, skipping backup creation"
fi

# Set proper permissions
chmod 644 "$DUCKDB_PATH"
chmod -R 755 "$DUCKDB_DIR"
chmod -R 755 "$BACKUP_DIR"

log "🎉 DuckDB initialization completed successfully!"
log "Database file: $DUCKDB_PATH"
log "Backup directory: $BACKUP_DIR"
log "Tables created: profiles, profile_history, long_term_memory, user_roles"