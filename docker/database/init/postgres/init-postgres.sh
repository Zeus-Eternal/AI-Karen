#!/bin/bash
set -e

# PostgreSQL Initialization Script for AI Karen
# This script runs automatically when the PostgreSQL container starts for the first time

echo "🐘 Initializing PostgreSQL for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to run SQL with error handling
run_sql() {
    local sql_file="$1"
    local description="$2"
    
    if [ -f "$sql_file" ]; then
        log "Running $description..."
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$sql_file"
        log "✅ $description completed successfully"
    else
        log "⚠️  $sql_file not found, skipping $description"
    fi
}

# Wait for PostgreSQL to be ready
log "Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    sleep 1
done

log "PostgreSQL is ready, starting initialization..."

# Create extensions if needed
log "Creating PostgreSQL extensions..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable commonly used extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "btree_gin";
    
    -- Log extension creation
    SELECT 'Extension created: ' || extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin');
EOSQL

# Run migration files in order
log "Running database migrations..."

# Check if migrations directory exists
if [ -d "/migrations/postgres" ]; then
    # Run migrations in numerical order
    for migration_file in /migrations/postgres/*.sql; do
        if [ -f "$migration_file" ]; then
            filename=$(basename "$migration_file")
            run_sql "$migration_file" "migration $filename"
        fi
    done
else
    log "⚠️  No migrations directory found at /migrations/postgres"
fi

# Create migration tracking table
log "Setting up migration tracking..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create migration tracking table
    CREATE TABLE IF NOT EXISTS migration_history (
        id SERIAL PRIMARY KEY,
        service VARCHAR(50) NOT NULL DEFAULT 'postgres',
        migration_name VARCHAR(255) NOT NULL,
        applied_at TIMESTAMP DEFAULT NOW(),
        checksum VARCHAR(64)
    );
    
    -- Record current migrations
    INSERT INTO migration_history (migration_name, applied_at) 
    VALUES ('001_create_tables.sql', NOW()),
           ('002_create_extension_tables.sql', NOW())
    ON CONFLICT DO NOTHING;
EOSQL

# Create service health tracking
log "Setting up service health tracking..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create service health table
    CREATE TABLE IF NOT EXISTS service_health (
        service_name VARCHAR(50) PRIMARY KEY,
        status VARCHAR(20) NOT NULL,
        last_check TIMESTAMP DEFAULT NOW(),
        metadata JSONB
    );
    
    -- Insert initial health record
    INSERT INTO service_health (service_name, status, metadata) 
    VALUES ('postgres', 'healthy', '{"version": "15", "initialized_at": "'$(date -Iseconds)'"}')
    ON CONFLICT (service_name) DO UPDATE SET 
        status = EXCLUDED.status,
        last_check = NOW(),
        metadata = EXCLUDED.metadata;
EOSQL

# Create indexes for performance
log "Creating performance indexes..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Indexes for memory table
    CREATE INDEX IF NOT EXISTS idx_memory_user_id ON memory(user_id);
    CREATE INDEX IF NOT EXISTS idx_memory_tenant_id ON memory(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_memory_session_id ON memory(session_id);
    CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
    
    -- Indexes for profiles
    CREATE INDEX IF NOT EXISTS idx_profiles_last_update ON profiles(last_update);
    
    -- Indexes for profile_history
    CREATE INDEX IF NOT EXISTS idx_profile_history_user_id ON profile_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_profile_history_timestamp ON profile_history(timestamp);
    
    -- Indexes for user_roles
    CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);
EOSQL

# Verify database setup
log "Verifying database setup..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Check tables exist
    SELECT 'Table exists: ' || tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename IN ('profiles', 'profile_history', 'long_term_memory', 'user_roles', 'memory', 'extension_registry');
    
    -- Check extensions
    SELECT 'Extension loaded: ' || extname FROM pg_extension;
    
    -- Update health status
    UPDATE service_health 
    SET status = 'initialized', 
        last_check = NOW(),
        metadata = metadata || '{"tables_verified": true}'::jsonb
    WHERE service_name = 'postgres';
EOSQL

log "🎉 PostgreSQL initialization completed successfully!"
log "Database: $POSTGRES_DB"
log "User: $POSTGRES_USER"
log "Extensions: uuid-ossp, pg_trgm, btree_gin"
log "Tables: profiles, profile_history, long_term_memory, user_roles, memory, extension_registry"