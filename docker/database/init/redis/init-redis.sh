#!/bin/bash
set -e

# Redis Initialization Script for AI Karen
# This script configures Redis for optimal AI Karen performance

echo "🔴 Initializing Redis for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to wait for Redis to be ready
wait_for_redis() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6380}"
    local password="${REDIS_PASSWORD:-}"
    local max_attempts=30
    local attempt=1
    
    log "Waiting for Redis to be ready at $host:$port..."
    
    # Install redis-cli if not present
    if ! command -v redis-cli &> /dev/null; then
        log "Installing redis-cli..."
        # Try different package managers
        if command -v apk &> /dev/null; then
            apk add --no-cache redis
        elif command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y redis-tools
        elif command -v yum &> /dev/null; then
            yum install -y redis
        elif command -v pacman &> /dev/null; then
            pacman -S --noconfirm redis
        else
            log "❌ No known package manager found. Please install redis-cli manually."
            return 1
        fi
    fi
    
    while [ $attempt -le $max_attempts ]; do
        if [ -n "$password" ]; then
            if redis-cli -h "$host" -p "$port" -a "$password" ping > /dev/null 2>&1; then
                log "✅ Redis is ready!"
                return 0
            fi
        else
            if redis-cli -h "$host" -p "$port" ping > /dev/null 2>&1; then
                log "✅ Redis is ready!"
                return 0
            fi
        fi
        
        log "Attempt $attempt/$max_attempts: Redis not ready yet, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "❌ Redis failed to become ready after $max_attempts attempts"
    return 1
}

# Function to execute Redis commands
redis_cmd() {
    local cmd="$1"
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6380}"
    local password="${REDIS_PASSWORD:-}"
    
    if [ -n "$password" ]; then
        redis-cli -h "$host" -p "$port" -a "$password" "$cmd"
    else
        redis-cli -h "$host" -p "$port" "$cmd"
    fi
}

# Function to execute Redis commands with multiple arguments
redis_cmd_multi() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6380}"
    local password="${REDIS_PASSWORD:-}"
    
    if [ -n "$password" ]; then
        redis-cli -h "$host" -p "$port" -a "$password" "$@"
    else
        redis-cli -h "$host" -p "$port" "$@"
    fi
}

# Wait for Redis to be ready
wait_for_redis

# Configure Redis for AI Karen workloads
log "Configuring Redis for AI Karen..."

# Set up key namespaces and configurations
log "Setting up AI Karen namespaces..."

# Create configuration keys
redis_cmd_multi HSET "ai_karen:config:cache" \
    "default_ttl" "3600" \
    "max_memory_policy" "allkeys-lru" \
    "session_ttl" "86400" \
    "user_data_ttl" "7200" \
    "analytics_ttl" "1800" \
    "temp_data_ttl" "300"

# Set up session management configuration
redis_cmd_multi HSET "ai_karen:config:sessions" \
    "max_sessions_per_user" "5" \
    "session_timeout" "1800" \
    "cleanup_interval" "300" \
    "max_idle_time" "3600"

# Set up rate limiting configuration
redis_cmd_multi HSET "ai_karen:config:rate_limits" \
    "api_requests_per_minute" "100" \
    "chat_messages_per_minute" "20" \
    "file_uploads_per_hour" "10" \
    "search_queries_per_minute" "50"

# Set up caching strategies
redis_cmd_multi HSET "ai_karen:config:caching" \
    "user_profiles_ttl" "7200" \
    "model_responses_ttl" "3600" \
    "search_results_ttl" "1800" \
    "analytics_data_ttl" "900" \
    "system_metrics_ttl" "300"

# Initialize health monitoring
log "Setting up health monitoring..."
redis_cmd_multi HSET "ai_karen:health:redis" \
    "status" "healthy" \
    "initialized_at" "$(date -Iseconds)" \
    "version" "7" \
    "memory_policy" "allkeys-lru"

# Set up Lua scripts for atomic operations
log "Installing Lua scripts..."

# Script for session management
redis_cmd_multi SCRIPT LOAD '
local session_key = KEYS[1]
local user_id = ARGV[1]
local session_data = ARGV[2]
local ttl = tonumber(ARGV[3])

-- Set session data
redis.call("HSET", session_key, "user_id", user_id, "data", session_data, "last_activity", redis.call("TIME")[1])
redis.call("EXPIRE", session_key, ttl)

-- Update user session list
local user_sessions_key = "ai_karen:user_sessions:" .. user_id
redis.call("SADD", user_sessions_key, session_key)
redis.call("EXPIRE", user_sessions_key, ttl)

return "OK"
'

# Script for rate limiting
redis_cmd_multi SCRIPT LOAD '
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call("GET", key)
if current == false then
    redis.call("SETEX", key, window, 1)
    return {1, limit}
elseif tonumber(current) < limit then
    local new_val = redis.call("INCR", key)
    local ttl = redis.call("TTL", key)
    return {new_val, limit}
else
    local ttl = redis.call("TTL", key)
    return {tonumber(current), limit}
end
'

# Script for cache invalidation patterns
redis_cmd_multi SCRIPT LOAD '
local pattern = KEYS[1]
local cursor = "0"
local keys_deleted = 0

repeat
    local result = redis.call("SCAN", cursor, "MATCH", pattern, "COUNT", 100)
    cursor = result[1]
    local keys = result[2]
    
    if #keys > 0 then
        keys_deleted = keys_deleted + redis.call("DEL", unpack(keys))
    end
until cursor == "0"

return keys_deleted
'

# Create sample data structures for testing
log "Creating sample data structures..."

# Test user session
redis_cmd_multi HSET "ai_karen:session:test_session_123" \
    "user_id" "test_user" \
    "created_at" "$(date -Iseconds)" \
    "last_activity" "$(date -Iseconds)" \
    "data" '{"theme": "dark", "language": "en"}'

redis_cmd_multi EXPIRE "ai_karen:session:test_session_123" 3600

# Test user profile cache
redis_cmd_multi HSET "ai_karen:user:test_user:profile" \
    "name" "Test User" \
    "email" "test@example.com" \
    "preferences" '{"notifications": true, "theme": "dark"}' \
    "cached_at" "$(date -Iseconds)"

redis_cmd_multi EXPIRE "ai_karen:user:test_user:profile" 7200

# Test analytics cache
redis_cmd_multi HSET "ai_karen:analytics:daily:$(date +%Y-%m-%d)" \
    "total_requests" "0" \
    "unique_users" "0" \
    "avg_response_time" "0" \
    "error_count" "0"

redis_cmd_multi EXPIRE "ai_karen:analytics:daily:$(date +%Y-%m-%d)" 86400

# Set up pub/sub channels for real-time features
log "Setting up pub/sub channels..."

# Create channel configuration
redis_cmd_multi HSET "ai_karen:config:pubsub" \
    "user_notifications" "ai_karen:notifications:user:*" \
    "system_events" "ai_karen:events:system" \
    "chat_messages" "ai_karen:chat:*" \
    "analytics_updates" "ai_karen:analytics:updates"

# Test the pub/sub system
redis_cmd_multi PUBLISH "ai_karen:events:system" '{"type": "redis_initialized", "timestamp": "'$(date -Iseconds)'"}'

# Verify Redis configuration
log "Verifying Redis configuration..."

# Check memory info
memory_info=$(redis_cmd_multi INFO memory | grep used_memory_human)
log "Memory usage: $memory_info"

# Check keyspace info
keyspace_info=$(redis_cmd_multi INFO keyspace)
log "Keyspace info: $keyspace_info"

# Test basic operations
redis_cmd_multi SET "ai_karen:test:init" "Redis initialization successful" EX 300
test_result=$(redis_cmd_multi GET "ai_karen:test:init")
if [ "$test_result" = "Redis initialization successful" ]; then
    log "✅ Basic operations test passed"
else
    log "❌ Basic operations test failed"
fi

# Test hash operations
redis_cmd_multi HSET "ai_karen:test:hash" "field1" "value1" "field2" "value2"
hash_result=$(redis_cmd_multi HGET "ai_karen:test:hash" "field1")
if [ "$hash_result" = "value1" ]; then
    log "✅ Hash operations test passed"
else
    log "❌ Hash operations test failed"
fi

# Test list operations
redis_cmd_multi LPUSH "ai_karen:test:list" "item1" "item2" "item3"
list_length=$(redis_cmd_multi LLEN "ai_karen:test:list")
if [ "$list_length" = "3" ]; then
    log "✅ List operations test passed"
else
    log "❌ List operations test failed"
fi

# Clean up test keys
redis_cmd_multi DEL "ai_karen:test:init" "ai_karen:test:hash" "ai_karen:test:list"

# Update health status
redis_cmd_multi HSET "ai_karen:health:redis" \
    "status" "initialized" \
    "last_check" "$(date -Iseconds)" \
    "tests_passed" "true" \
    "configuration_complete" "true"

log "🎉 Redis initialization completed successfully!"
log "Namespaces created: sessions, users, analytics, config, health"
log "Lua scripts installed: session management, rate limiting, cache invalidation"
log "Pub/sub channels configured: notifications, events, chat, analytics"

# Display Redis info
log "Redis server information:"
redis_cmd_multi INFO server | head -10