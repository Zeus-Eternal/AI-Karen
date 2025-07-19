#!/bin/bash
set -e

# Environment Configuration Script for AI Karen Database
# This script helps set up environment-specific configurations

echo "🔧 AI Karen Database Environment Configuration"
echo "=============================================="

# Function to log with timestamp and color
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")
            echo -e "\033[0;32m[$timestamp] INFO: $message\033[0m"
            ;;
        "WARN")
            echo -e "\033[0;33m[$timestamp] WARN: $message\033[0m"
            ;;
        "ERROR")
            echo -e "\033[0;31m[$timestamp] ERROR: $message\033[0m"
            ;;
        "SUCCESS")
            echo -e "\033[0;36m[$timestamp] SUCCESS: $message\033[0m"
            ;;
        *)
            echo "[$timestamp] $message"
            ;;
    esac
}

# Function to generate secure password
generate_password() {
    local length="${1:-16}"
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-${length}
}

# Function to validate environment
validate_environment() {
    local env="$1"
    
    case "$env" in
        "development"|"dev")
            echo "development"
            ;;
        "production"|"prod")
            echo "production"
            ;;
        "testing"|"test")
            echo "testing"
            ;;
        *)
            log "ERROR" "Invalid environment: $env"
            log "INFO" "Valid environments: development, production, testing"
            exit 1
            ;;
    esac
}

# Function to setup development environment
setup_development() {
    log "INFO" "Setting up development environment..."
    
    # Copy development template
    cp .env.development .env
    
    # Generate development passwords (less secure for convenience)
    local postgres_pass="dev_postgres_$(date +%s)"
    local redis_pass="dev_redis_$(date +%s)"
    local elastic_pass="dev_elastic_$(date +%s)"
    
    # Update passwords in .env file
    sed -i "s/dev_password_123_change_me/$postgres_pass/g" .env
    sed -i "s/dev_redis_123_change_me/$redis_pass/g" .env
    sed -i "s/dev_elastic_123_change_me/$elastic_pass/g" .env
    
    log "SUCCESS" "Development environment configured"
    log "INFO" "PostgreSQL password: $postgres_pass"
    log "INFO" "Redis password: $redis_pass"
    log "INFO" "Elasticsearch password: $elastic_pass"
    
    # Create development-specific directories
    mkdir -p data/dev/{postgres,elasticsearch,milvus,redis,duckdb}
    
    log "INFO" "Development data directories created"
}

# Function to setup production environment
setup_production() {
    log "INFO" "Setting up production environment..."
    
    # Copy production template
    cp .env.production .env
    
    # Generate secure passwords
    local postgres_pass=$(generate_password 24)
    local redis_pass=$(generate_password 24)
    local elastic_pass=$(generate_password 24)
    local milvus_pass=$(generate_password 24)
    local minio_access=$(generate_password 16)
    local minio_secret=$(generate_password 32)
    
    # Update passwords in .env file
    sed -i "s/CHANGE_ME_SECURE_POSTGRES_PASSWORD/$postgres_pass/g" .env
    sed -i "s/CHANGE_ME_SECURE_REDIS_PASSWORD/$redis_pass/g" .env
    sed -i "s/CHANGE_ME_SECURE_ELASTICSEARCH_PASSWORD/$elastic_pass/g" .env
    sed -i "s/CHANGE_ME_SECURE_MILVUS_PASSWORD/$milvus_pass/g" .env
    sed -i "s/CHANGE_ME_MINIO_ACCESS_KEY/$minio_access/g" .env
    sed -i "s/CHANGE_ME_SECURE_MINIO_SECRET_KEY/$minio_secret/g" .env
    
    # Create secure password file
    cat > .env.passwords << EOF
# AI Karen Database Passwords - KEEP SECURE!
# Generated: $(date)

POSTGRES_PASSWORD=$postgres_pass
REDIS_PASSWORD=$redis_pass
ELASTICSEARCH_PASSWORD=$elastic_pass
MILVUS_PASSWORD=$milvus_pass
MINIO_ACCESS_KEY=$minio_access
MINIO_SECRET_KEY=$minio_secret
EOF
    
    chmod 600 .env.passwords
    
    log "SUCCESS" "Production environment configured"
    log "WARN" "Passwords saved to .env.passwords - KEEP THIS FILE SECURE!"
    
    # Create production data directories
    local data_path="${DATA_PATH:-/opt/ai-karen/data}"
    log "INFO" "Creating production data directories at: $data_path"
    
    sudo mkdir -p "$data_path"/{postgres,elasticsearch,milvus,redis,duckdb,etcd,minio}
    sudo chown -R $(whoami):$(whoami) "$data_path"
    
    # Create backup directories
    mkdir -p backups/{postgres,elasticsearch,milvus,redis,duckdb}
    
    log "INFO" "Production directories created"
}

# Function to setup testing environment
setup_testing() {
    log "INFO" "Setting up testing environment..."
    
    # Use development template as base for testing
    cp .env.development .env
    
    # Modify for testing
    sed -i 's/ai_karen_dev/ai_karen_test/g' .env
    sed -i 's/karen_dev/karen_test/g' .env
    sed -i 's/POSTGRES_PORT=5432/POSTGRES_PORT=5433/g' .env
    sed -i 's/ELASTICSEARCH_PORT=9200/ELASTICSEARCH_PORT=9201/g' .env
    sed -i 's/REDIS_PORT=6379/REDIS_PORT=6380/g' .env
    sed -i 's/MILVUS_PORT=19530/MILVUS_PORT=19531/g' .env
    
    # Disable persistence for testing
    sed -i 's/POSTGRES_PERSISTENCE=true/POSTGRES_PERSISTENCE=false/g' .env
    sed -i 's/ELASTICSEARCH_PERSISTENCE=true/ELASTICSEARCH_PERSISTENCE=false/g' .env
    sed -i 's/REDIS_PERSISTENCE=true/REDIS_PERSISTENCE=false/g' .env
    
    log "SUCCESS" "Testing environment configured"
    log "INFO" "Testing uses different ports to avoid conflicts"
}

# Function to validate configuration
validate_configuration() {
    log "INFO" "Validating configuration..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log "ERROR" ".env file not found"
        return 1
    fi
    
    # Check for placeholder passwords
    local placeholders=$(grep -E "CHANGE_ME|change_me|123_change_me" .env | wc -l)
    if [ "$placeholders" -gt 0 ]; then
        log "WARN" "Found $placeholders placeholder passwords that should be changed"
        grep -E "CHANGE_ME|change_me|123_change_me" .env
    fi
    
    # Check required variables
    local required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "ENVIRONMENT")
    local missing_vars=0
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env; then
            log "ERROR" "Missing required variable: $var"
            missing_vars=$((missing_vars + 1))
        fi
    done
    
    if [ $missing_vars -eq 0 ]; then
        log "SUCCESS" "Configuration validation passed"
    else
        log "ERROR" "Configuration validation failed: $missing_vars missing variables"
        return 1
    fi
}

# Function to show current configuration
show_configuration() {
    log "INFO" "Current configuration:"
    echo ""
    
    if [ -f ".env" ]; then
        echo "Environment file: .env"
        echo "Environment: $(grep "^ENVIRONMENT=" .env | cut -d'=' -f2)"
        echo "PostgreSQL DB: $(grep "^POSTGRES_DB=" .env | cut -d'=' -f2)"
        echo "PostgreSQL User: $(grep "^POSTGRES_USER=" .env | cut -d'=' -f2)"
        echo "Data Path: $(grep "^DATA_PATH=" .env | cut -d'=' -f2 || echo "default")"
        echo ""
        
        # Show service status
        echo "Enabled Services:"
        grep "^ENABLE_" .env | while read line; do
            echo "  $line"
        done
    else
        echo "No .env file found"
    fi
}

# Function to switch environment
switch_environment() {
    local target_env="$1"
    
    if [ -f ".env" ]; then
        log "WARN" "Backing up current .env to .env.backup"
        cp .env .env.backup
    fi
    
    case "$target_env" in
        "development")
            setup_development
            ;;
        "production")
            setup_production
            ;;
        "testing")
            setup_testing
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "AI Karen Database Environment Configuration"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup <env>        Set up environment (development, production, testing)"
    echo "  switch <env>       Switch to different environment"
    echo "  validate           Validate current configuration"
    echo "  show               Show current configuration"
    echo "  generate-password  Generate secure password"
    echo "  help               Show this help message"
    echo ""
    echo "Environments:"
    echo "  development        Development environment with debugging enabled"
    echo "  production         Production environment with security and performance"
    echo "  testing            Testing environment with isolated ports"
    echo ""
    echo "Examples:"
    echo "  $0 setup development"
    echo "  $0 switch production"
    echo "  $0 validate"
    echo "  $0 show"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "setup")
            local env=$(validate_environment "${2:-}")
            if [ $? -eq 0 ]; then
                case "$env" in
                    "development") setup_development ;;
                    "production") setup_production ;;
                    "testing") setup_testing ;;
                esac
                validate_configuration
            fi
            ;;
        "switch")
            local env=$(validate_environment "${2:-}")
            if [ $? -eq 0 ]; then
                switch_environment "$env"
                validate_configuration
            fi
            ;;
        "validate")
            validate_configuration
            ;;
        "show")
            show_configuration
            ;;
        "generate-password")
            local length="${2:-16}"
            echo "Generated password: $(generate_password $length)"
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Change to script directory
cd "$(dirname "$0")/.."

# Run main function with all arguments
main "$@"