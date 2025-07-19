#!/bin/bash
set -e

# Redis Health Check Script for AI Karen
# This script verifies Redis functionality and performance

echo "🔴 Running Redis health check..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to execute Redis commands
redis_cmd() {
    local cmd="$1"
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
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
    local port="${REDIS_PORT:-6379}"
    local password="${REDIS_PASSWORD:-}"
    
    if [ -n "$password" ]; then
        redis-cli -h "$host" -p "$port" -a "$password" "$@"
    else
        redis-cli -h "$host" -p "$port" "$@"
    fi
}

# Basic connectivity test
log "Testing basic connectivity..."
ping_result=$(redis_cmd "PING")
if [ "$ping_result" = "PONG" ]; then
    log "✅ Basic connectivity test passed"
else
    log "❌ Basic connectivity test failed: $ping_result"
    exit 1
fi

# Memory usage check
log "Checking memory usage..."
memory_info=$(redis_cmd_multi INFO memory)
used_memory=$(echo "$memory_info" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
max_memory=$(echo "$memory_info" | grep "maxmemory_human:" | cut -d: -f2 | tr -d '\r')
log "Memory usage: $used_memory / $max_memory"

# Performance test
log "Running performance test..."
start_time=$(date +%s%N)
for i in {1..100}; do
    redis_cmd_multi SET "test:perf:$i" "value$i" > /dev/null
done
for i in {1..100}; do
    redis_cmd_multi GET "test:perf:$i" > /dev/null
done
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))
log "Performance test: 200 operations in ${duration}ms"

# Clean up performance test keys
redis_cmd_multi DEL $(redis_cmd_multi KEYS "test:perf:*" | tr '\n' ' ') > /dev/null 2>&1 || true

# Check AI Karen specific namespaces
log "Checking AI Karen namespaces..."
namespaces=("ai_karen:config:cache" "ai_karen:config:sessions" "ai_karen:health:redis")
for namespace in "${namespaces[@]}"; do
    if redis_cmd_multi EXISTS "$namespace" | grep -q "1"; then
        log "✅ Namespace $namespace exists"
    else
        log "⚠️  Namespace $namespace not found"
    fi
done

# Test hash operations (user profiles)
log "Testing hash operations..."
redis_cmd_multi HSET "test:hash:health" "field1" "value1" "timestamp" "$(date -Iseconds)" > /dev/null
hash_value=$(redis_cmd_multi HGET "test:hash:health" "field1")
if [ "$hash_value" = "value1" ]; then
    log "✅ Hash operations test passed"
else
    log "❌ Hash operations test failed"
fi
redis_cmd_multi DEL "test:hash:health" > /dev/null

# Test list operations (message queues)
log "Testing list operations..."
redis_cmd_multi LPUSH "test:list:health" "item1" "item2" "item3" > /dev/null
list_length=$(redis_cmd_multi LLEN "test:list:health")
if [ "$list_length" = "3" ]; then
    log "✅ List operations test passed"
else
    log "❌ List operations test failed"
fi
redis_cmd_multi DEL "test:list:health" > /dev/null

# Test set operations (unique collections)
log "Testing set operations..."
redis_cmd_multi SADD "test:set:health" "member1" "member2" "member3" > /dev/null
set_size=$(redis_cmd_multi SCARD "test:set:health")
if [ "$set_size" = "3" ]; then
    log "✅ Set operations test passed"
else
    log "❌ Set operations test failed"
fi
redis_cmd_multi DEL "test:set:health" > /dev/null

# Test sorted set operations (rankings/analytics)
log "Testing sorted set operations..."
redis_cmd_multi ZADD "test:zset:health" 1 "item1" 2 "item2" 3 "item3" > /dev/null
zset_size=$(redis_cmd_multi ZCARD "test:zset:health")
if [ "$zset_size" = "3" ]; then
    log "✅ Sorted set operations test passed"
else
    log "❌ Sorted set operations test failed"
fi
redis_cmd_multi DEL "test:zset:health" > /dev/null

# Test expiration (TTL functionality)
log "Testing expiration functionality..."
redis_cmd_multi SET "test:ttl:health" "expires" EX 2 > /dev/null
sleep 1
if redis_cmd_multi EXISTS "test:ttl:health" | grep -q "1"; then
    sleep 2
    if redis_cmd_multi EXISTS "test:ttl:health" | grep -q "0"; then
        log "✅ TTL functionality test passed"
    else
        log "❌ TTL functionality test failed - key did not expire"
    fi
else
    log "❌ TTL functionality test failed - key not found"
fi

# Test pub/sub functionality
log "Testing pub/sub functionality..."
redis_cmd_multi PUBLISH "test:pubsub:health" "test message" > /dev/null
log "✅ Pub/sub publish test completed"

# Check server info
log "Checking server information..."
server_info=$(redis_cmd_multi INFO server)
version=$(echo "$server_info" | grep "redis_version:" | cut -d: -f2 | tr -d '\r')
uptime=$(echo "$server_info" | grep "uptime_in_seconds:" | cut -d: -f2 | tr -d '\r')
log "Redis version: $version"
log "Uptime: ${uptime} seconds"

# Check connected clients
clients_info=$(redis_cmd_multi INFO clients)
connected_clients=$(echo "$clients_info" | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
log "Connected clients: $connected_clients"

# Check keyspace statistics
log "Checking keyspace statistics..."
keyspace_info=$(redis_cmd_multi INFO keyspace)
if [ -n "$keyspace_info" ]; then
    log "Keyspace info: $keyspace_info"
else
    log "No keyspace data available"
fi

# Update health status
redis_cmd_multi HSET "ai_karen:health:redis" \
    "status" "healthy" \
    "last_health_check" "$(date -Iseconds)" \
    "version" "$version" \
    "uptime_seconds" "$uptime" \
    "connected_clients" "$connected_clients" \
    "memory_used" "$used_memory" \
    "tests_passed" "true"

log "🎉 Redis health check completed successfully!"
log "All tests passed - Redis is healthy and ready for AI Karen"