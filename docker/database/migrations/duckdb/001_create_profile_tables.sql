-- DuckDB Profile Tables Creation
-- This migration creates the core profile-related tables for AI Karen

-- Create profiles table with enhanced structure
CREATE TABLE IF NOT EXISTS profiles (
    user_id VARCHAR PRIMARY KEY,
    profile_json VARCHAR NOT NULL,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Create profile history table for tracking changes
CREATE TABLE IF NOT EXISTS profile_history (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    timestamp DOUBLE NOT NULL,
    field VARCHAR NOT NULL,
    old VARCHAR,
    new VARCHAR,
    change_type VARCHAR DEFAULT 'update', -- 'create', 'update', 'delete'
    metadata VARCHAR -- JSON string for additional context
);

-- Create indexes for profiles table
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_last_update ON profiles(last_update);
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_profiles_version ON profiles(version);

-- Create indexes for profile_history table
CREATE INDEX IF NOT EXISTS idx_profile_history_user_id ON profile_history(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_history_timestamp ON profile_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_profile_history_field ON profile_history(field);
CREATE INDEX IF NOT EXISTS idx_profile_history_change_type ON profile_history(change_type);