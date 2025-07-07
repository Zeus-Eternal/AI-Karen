-- Initial tables for Kari AI Postgres backend

CREATE TABLE IF NOT EXISTS profiles (
    user_id VARCHAR PRIMARY KEY,
    profile_json TEXT,
    last_update TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profile_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR,
    timestamp DOUBLE PRECISION,
    field VARCHAR,
    old TEXT,
    new TEXT
);

CREATE TABLE IF NOT EXISTS long_term_memory (
    user_id VARCHAR,
    memory_json TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id VARCHAR,
    role VARCHAR
);

CREATE TABLE IF NOT EXISTS memory (
    user_id VARCHAR,
    query VARCHAR,
    result TEXT,
    timestamp BIGINT
);

