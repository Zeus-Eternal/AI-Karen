#!/bin/bash

# Authentication System Deployment Script
# Usage: ./deploy.sh [environment] [command]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"
CONFIG_FILE="$SCRIPT_DIR/deployment_config.json"

# Default values
ENVIRONMENT="${1:-production}"
COMMAND="${2:-deploy}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check required Python packages
    $PYTHON_CMD -c "import asyncio, asyncpg, aiofiles, aiohttp" 2>/dev/null || {
        log_error "Required Python packages not installed. Run: pip install asyncpg aiofiles aiohttp"
        exit 1
    }
    
    # Check configuration file
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_warning "Configuration file not found: $CONFIG_FILE"
        log_info "Using default configuration"
    fi
    
    log_success "Prerequisites check passed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p "$SCRIPT_DIR/../config"
    mkdir -p "$SCRIPT_DIR/deployment_logs"
    mkdir -p "$SCRIPT_DIR/config_backups"
    
    log_success "Directories created"
}

# Run deployment
run_deployment() {
    log_info "Starting authentication system deployment for environment: $ENVIRONMENT"
    
    cd "$SCRIPT_DIR"
    
    case $COMMAND in
        "deploy")
            log_info "Running full deployment..."
            $PYTHON_CMD deploy_auth_system.py deploy --environment "$ENVIRONMENT" --config "$CONFIG_FILE"
            ;;
        "status")
            log_info "Checking deployment status..."
            $PYTHON_CMD deploy_auth_system.py status --config "$CONFIG_FILE"
            ;;
        "migrate")
            log_info "Running database migrations..."
            $PYTHON_CMD migration_runner.py migrate --config "$CONFIG_FILE"
            ;;
        "rollback")
            if [[ -z "$3" ]]; then
                log_error "Backup ID required for rollback. Usage: ./deploy.sh $ENVIRONMENT rollback <backup_id>"
                exit 1
            fi
            log_info "Rolling back to backup: $3"
            $PYTHON_CMD deploy_auth_system.py rollback --backup-id "$3" --config "$CONFIG_FILE"
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Show usage information
show_usage() {
    echo "Usage: $0 [environment] [command] [options]"
    echo ""
    echo "Environments:"
    echo "  development  - Development environment"
    echo "  staging      - Staging environment"
    echo "  production   - Production environment (default)"
    echo ""
    echo "Commands:"
    echo "  deploy       - Full system deployment (default)"
    echo "  status       - Check deployment status"
    echo "  migrate      - Run database migrations only"
    echo "  rollback     - Rollback to previous backup"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Deploy to production"
    echo "  $0 staging deploy                     # Deploy to staging"
    echo "  $0 production status                  # Check production status"
    echo "  $0 production rollback backup_123     # Rollback production"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Add any cleanup tasks here
}

# Signal handlers
trap cleanup EXIT
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Main execution
main() {
    log_info "Authentication System Deployment Tool"
    log_info "Environment: $ENVIRONMENT"
    log_info "Command: $COMMAND"
    echo ""
    
    check_prerequisites
    setup_directories
    run_deployment
    
    log_success "Deployment completed successfully!"
}

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"