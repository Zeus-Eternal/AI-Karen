#!/bin/bash
set -e

# Bootstrap Data Loader for AI Karen
# This script loads initial data into all database systems

echo "📊 Loading AI Karen bootstrap data..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to load classifier seed data
load_classifier_data() {
    log "Loading classifier seed data..."
    
    # Load into PostgreSQL
    if command -v psql > /dev/null 2>&1; then
        log "Loading classifier data into PostgreSQL..."
        
        cat > /tmp/classifier_bootstrap.sql << 'EOF'
-- Create classifier training data table
CREATE TABLE IF NOT EXISTS classifier_training_data (
    id SERIAL PRIMARY KEY,
    text VARCHAR NOT NULL,
    intent VARCHAR NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    language VARCHAR DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_classifier_intent ON classifier_training_data(intent);
CREATE INDEX IF NOT EXISTS idx_classifier_language ON classifier_training_data(language);
CREATE INDEX IF NOT EXISTS idx_classifier_created_at ON classifier_training_data(created_at);

-- Insert classifier seed data
INSERT INTO classifier_training_data (text, intent, confidence) VALUES
('hello', 'greet', 1.0),
('hi', 'greet', 1.0),
('hey there', 'greet', 0.9),
('good morning', 'greet', 1.0),
('good afternoon', 'greet', 1.0),
('good evening', 'greet', 1.0),
('goodbye', 'farewell', 1.0),
('bye', 'farewell', 1.0),
('see you later', 'farewell', 0.9),
('farewell', 'farewell', 0.8),
('thanks', 'thanks', 1.0),
('thank you', 'thanks', 1.0),
('much appreciated', 'thanks', 0.9),
('thanks a lot', 'thanks', 0.9),
('what time is it', 'time_query', 1.0),
('tell me the time', 'time_query', 1.0),
('current time please', 'time_query', 0.9),
('what is the time', 'time_query', 1.0),
('open the door', 'open_door', 1.0),
('close the door', 'close_door', 1.0),
('play some music', 'play_music', 1.0),
('stop the music', 'stop_music', 1.0),
('weather today', 'weather_query', 1.0),
('what is the forecast', 'weather_query', 0.9),
('turn on the lights', 'lights_on', 1.0),
('turn off the lights', 'lights_off', 1.0),
('increase volume', 'volume_up', 1.0),
('decrease volume', 'volume_down', 1.0),
('who are you', 'identity_query', 1.0),
('what can you do', 'capabilities_query', 1.0),
('help me', 'help_request', 1.0),
('I need help', 'help_request', 1.0),
('how are you', 'status_query', 1.0),
('what is your status', 'status_query', 0.9)
ON CONFLICT DO NOTHING;

-- Create intent statistics view
CREATE OR REPLACE VIEW classifier_intent_stats AS
SELECT 
    intent,
    COUNT(*) as sample_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence
FROM classifier_training_data 
GROUP BY intent
ORDER BY sample_count DESC;
EOF
        
        if psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /tmp/classifier_bootstrap.sql; then
            log "✅ Classifier data loaded into PostgreSQL"
        else
            log "❌ Failed to load classifier data into PostgreSQL"
        fi
        
        rm -f /tmp/classifier_bootstrap.sql
    fi
    
    # Load into Elasticsearch
    if command -v curl > /dev/null 2>&1; then
        log "Loading classifier data into Elasticsearch..."
        
        # Create classifier index
        curl -s -X PUT "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_classifier" \
            -H "Content-Type: application/json" \
            -d '{
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "intent_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "text": {
                            "type": "text",
                            "analyzer": "intent_analyzer"
                        },
                        "intent": {
                            "type": "keyword"
                        },
                        "confidence": {
                            "type": "float"
                        },
                        "language": {
                            "type": "keyword"
                        },
                        "created_at": {
                            "type": "date"
                        }
                    }
                }
            }' > /dev/null
        
        # Bulk load classifier data
        cat > /tmp/classifier_bulk.json << EOF
{"index":{}}
{"text":"hello","intent":"greet","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"hi","intent":"greet","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"hey there","intent":"greet","confidence":0.9,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"goodbye","intent":"farewell","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"bye","intent":"farewell","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"thanks","intent":"thanks","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"thank you","intent":"thanks","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"what time is it","intent":"time_query","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"weather today","intent":"weather_query","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
{"index":{}}
{"text":"who are you","intent":"identity_query","confidence":1.0,"language":"en","created_at":"$(date -Iseconds)"}
EOF
        
        curl -s -X POST "http://${ELASTICSEARCH_HOST:-localhost}:${ELASTICSEARCH_PORT:-9200}/ai_karen_classifier/_bulk" \
            -H "Content-Type: application/json" \
            --data-binary @/tmp/classifier_bulk.json > /dev/null
        
        rm -f /tmp/classifier_bulk.json
        log "✅ Classifier data loaded into Elasticsearch"
    fi
}

# Function to load system configuration data
load_system_config() {
    log "Loading system configuration data..."
    
    # Load into PostgreSQL
    if command -v psql > /dev/null 2>&1; then
        log "Loading system config into PostgreSQL..."
        
        cat > /tmp/system_config.sql << 'EOF'
-- Create system configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description, is_public) VALUES
('ai_karen.version', '"1.0.0"', 'AI Karen system version', true),
('ai_karen.environment', '"development"', 'Current environment', false),
('ai_karen.features.chat', 'true', 'Enable chat functionality', true),
('ai_karen.features.memory', 'true', 'Enable memory functionality', true),
('ai_karen.features.analytics', 'true', 'Enable analytics functionality', true),
('ai_karen.features.plugins', 'true', 'Enable plugin system', true),
('ai_karen.limits.max_sessions_per_user', '5', 'Maximum concurrent sessions per user', false),
('ai_karen.limits.max_message_length', '4096', 'Maximum message length in characters', true),
('ai_karen.limits.rate_limit_per_minute', '60', 'API rate limit per minute', false),
('ai_karen.ui.default_theme', '"light"', 'Default UI theme', true),
('ai_karen.ui.available_themes', '["light", "dark", "enterprise"]', 'Available UI themes', true),
('ai_karen.llm.default_provider', '"llamacpp"', 'Default LLM provider', false),
('ai_karen.llm.default_model', '"llama3.2:latest"', 'Default LLM model', false),
('ai_karen.memory.retention_days', '30', 'Memory retention period in days', false),
('ai_karen.analytics.retention_days', '90', 'Analytics data retention in days', false)
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    updated_at = NOW();

-- Create configuration view for public settings
CREATE OR REPLACE VIEW public_config AS
SELECT config_key, config_value, description
FROM system_config 
WHERE is_public = true;
EOF
        
        if psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /tmp/system_config.sql; then
            log "✅ System config loaded into PostgreSQL"
        else
            log "❌ Failed to load system config into PostgreSQL"
        fi
        
        rm -f /tmp/system_config.sql
    fi
    
    # Load into Redis
    if command -v redis-cli > /dev/null 2>&1; then
        log "Loading system config into Redis..."
        
        redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} \
            HSET "ai_karen:config:system" \
            "version" "1.0.0" \
            "environment" "development" \
            "initialized_at" "$(date -Iseconds)" \
            "features_enabled" "chat,memory,analytics,plugins" \
            "default_theme" "light" \
            "default_llm_provider" "llamacpp" \
            "default_llm_model" "llama3.2:latest" > /dev/null
        
        redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} \
            EXPIRE "ai_karen:config:system" 86400 > /dev/null
        
        log "✅ System config loaded into Redis"
    fi
}

# Function to load sample user data
load_sample_users() {
    log "Loading sample user data..."
    
    # Load into DuckDB
    if [ -f "${DUCKDB_PATH}" ]; then
        log "Loading sample users into DuckDB..."
        
        cat > /tmp/sample_users.sql << 'EOF'
-- Insert sample users
INSERT OR IGNORE INTO profiles (user_id, profile_json, last_update) VALUES
('admin', '{"name": "Administrator", "email": "admin@ai-karen.local", "role": "admin", "theme": "dark", "created_at": "' || strftime('%Y-%m-%dT%H:%M:%SZ', 'now') || '"}', CURRENT_TIMESTAMP),
('demo_user', '{"name": "Demo User", "email": "demo@ai-karen.local", "role": "user", "theme": "light", "created_at": "' || strftime('%Y-%m-%dT%H:%M:%SZ', 'now') || '"}', CURRENT_TIMESTAMP),
('developer', '{"name": "Developer", "email": "dev@ai-karen.local", "role": "developer", "theme": "dark", "created_at": "' || strftime('%Y-%m-%dT%H:%M:%SZ', 'now') || '"}', CURRENT_TIMESTAMP);

-- Insert sample user roles
INSERT OR IGNORE INTO user_roles (user_id, role) VALUES
('admin', 'admin'),
('admin', 'user'),
('demo_user', 'user'),
('developer', 'developer'),
('developer', 'user');

-- Insert sample profile history
INSERT OR IGNORE INTO profile_history (user_id, timestamp, field, old, new) VALUES
('admin', strftime('%s', 'now'), 'created', 'null', '{"initial_setup": true}'),
('demo_user', strftime('%s', 'now'), 'created', 'null', '{"initial_setup": true}'),
('developer', strftime('%s', 'now'), 'created', 'null', '{"initial_setup": true}');
EOF
        
        if duckdb "${DUCKDB_PATH}" < /tmp/sample_users.sql; then
            log "✅ Sample users loaded into DuckDB"
        else
            log "❌ Failed to load sample users into DuckDB"
        fi
        
        rm -f /tmp/sample_users.sql
    fi
}

# Function to create health check data
create_health_data() {
    log "Creating health check data..."
    
    # PostgreSQL health data
    if command -v psql > /dev/null 2>&1; then
        psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
            INSERT INTO service_health (service_name, status, metadata) VALUES
            ('bootstrap_loader', 'completed', '{\"bootstrap_data_loaded\": true, \"timestamp\": \"$(date -Iseconds)\"}')
            ON CONFLICT (service_name) DO UPDATE SET
                status = EXCLUDED.status,
                last_check = NOW(),
                metadata = EXCLUDED.metadata;
        " > /dev/null
    fi
    
    # Redis health data
    if command -v redis-cli > /dev/null 2>&1; then
        redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} \
            HSET "ai_karen:health:bootstrap" \
            "status" "completed" \
            "timestamp" "$(date -Iseconds)" \
            "data_loaded" "classifier,config,users" > /dev/null
    fi
    
    log "✅ Health check data created"
}

# Main bootstrap loading function
main() {
    log "Starting bootstrap data loading..."
    
    # Install required tools if not present
    if ! command -v curl > /dev/null 2>&1; then
        apk add --no-cache curl
    fi
    
    if ! command -v duckdb > /dev/null 2>&1; then
        apk add --no-cache wget
        wget -O /tmp/duckdb.zip https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64.zip
        unzip -o /tmp/duckdb.zip -d /usr/local/bin/
        chmod +x /usr/local/bin/duckdb
        rm -f /tmp/duckdb.zip
    fi
    
    # Load all bootstrap data
    load_classifier_data
    load_system_config
    load_sample_users
    create_health_data
    
    # Create completion marker
    mkdir -p /tmp/ai_karen_init
    echo "$(date -Iseconds)" > /tmp/ai_karen_init/bootstrap_complete
    
    log "🎉 Bootstrap data loading completed successfully!"
    log "Data loaded:"
    log "  - Classifier training data (intents and examples)"
    log "  - System configuration (features, limits, defaults)"
    log "  - Sample users (admin, demo_user, developer)"
    log "  - Health check data"
}

# Run main function
main "$@"