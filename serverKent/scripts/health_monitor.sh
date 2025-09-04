#!/bin/bash
echo "[DEPRECATED] Use scripts/llamacpp_service.sh or scripts/llamacpp_launcher.py instead." >&2
exit 1
# Health monitoring and automated recovery script for codeKent LLM providers
# Monitors all providers and performs automated recovery actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_INTERVAL=30
LOG_FILE="$HOME/.kiro/logs/health_monitor.log"
PID_FILE="$HOME/.kiro/health_monitor.pid"
MAX_RETRIES=3
RETRY_DELAY=10

# Provider endpoints
declare -A PROVIDERS=(
    ["cpp-llama"]="http://127.0.0.1:8080/health"
    ["lm-studio"]="http://127.0.0.1:1234/v1/models"
    ["openai"]="https://api.openai.com/v1/models"
    ["claude"]="https://api.anthropic.com/v1/messages"
    ["gemini"]="https://generativelanguage.googleapis.com/v1/models"
    ["groq"]="https://api.groq.com/openai/v1/models"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup logging
setup_logging() {
    local log_dir=$(dirname "$LOG_FILE")
    mkdir -p "$log_dir"
    
    # Rotate log if it's too large (>10MB)
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        print_status "Log file rotated"
    fi
}

# Function to check provider health
check_provider_health() {
    local provider="$1"
    local endpoint="$2"
    local timeout=10
    
    # Use curl if available, otherwise wget
    if command_exists curl; then
        if curl -f -s --max-time "$timeout" "$endpoint" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    elif command_exists wget; then
        if wget -q -T "$timeout" -O /dev/null "$endpoint" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        print_error "Neither curl nor wget is available for health checks"
        return 1
    fi
}

# Function to restart local provider
restart_provider() {
    local provider="$1"
    
    case "$provider" in
        "cpp-llama")
            restart_cpp_llama
            ;;
        "lm-studio")
            print_warning "LM Studio requires manual restart"
            ;;
        *)
            print_warning "Cannot restart cloud provider: $provider"
            ;;
    esac
}

# Function to restart cpp-llama server
restart_cpp_llama() {
    print_status "Attempting to restart cpp-llama server..."
    
    # Check if startup script exists
    local startup_script="$HOME/.kiro/cpp-llama/start_server.sh"
    if [[ -f "$startup_script" ]]; then
        # Kill existing server process
        pkill -f "cpp-llama.*server" || true
        sleep 5
        
        # Start new server in background
        nohup "$startup_script" >/dev/null 2>&1 &
        
        # Wait a bit for server to start
        sleep 10
        
        # Check if it's running
        if check_provider_health "cpp-llama" "${PROVIDERS[cpp-llama]}"; then
            print_success "cpp-llama server restarted successfully"
            return 0
        else
            print_error "Failed to restart cpp-llama server"
            return 1
        fi
    else
        print_error "cpp-llama startup script not found: $startup_script"
        return 1
    fi
}

# Function to send notification
send_notification() {
    local message="$1"
    local level="$2"  # info, warning, error
    
    # Log the notification
    case "$level" in
        "error")
            print_error "$message"
            ;;
        "warning")
            print_warning "$message"
            ;;
        *)
            print_status "$message"
            ;;
    esac
    
    # Send desktop notification if available
    if command_exists notify-send; then
        notify-send "codeKent Health Monitor" "$message" -u "$level" 2>/dev/null || true
    fi
    
    # Send to system log
    if command_exists logger; then
        logger -t "codekent-health" "$message"
    fi
}

# Function to perform health check on all providers
perform_health_checks() {
    local failed_providers=()
    local recovered_providers=()
    
    for provider in "${!PROVIDERS[@]}"; do
        local endpoint="${PROVIDERS[$provider]}"
        
        if check_provider_health "$provider" "$endpoint"; then
            # Check if this provider was previously failed
            if [[ -f "/tmp/codekent_${provider}_failed" ]]; then
                rm "/tmp/codekent_${provider}_failed"
                recovered_providers+=("$provider")
                send_notification "Provider $provider has recovered" "info"
            fi
        else
            # Provider is down
            failed_providers+=("$provider")
            
            # Check if this is a new failure
            if [[ ! -f "/tmp/codekent_${provider}_failed" ]]; then
                touch "/tmp/codekent_${provider}_failed"
                send_notification "Provider $provider is down" "error"
                
                # Attempt recovery for local providers
                if [[ "$provider" == "cpp-llama" ]] || [[ "$provider" == "lm-studio" ]]; then
                    print_status "Attempting to recover $provider..."
                    restart_provider "$provider"
                fi
            fi
        fi
    done
    
    # Summary
    if [[ ${#failed_providers[@]} -eq 0 ]]; then
        print_success "All providers are healthy"
    else
        print_warning "Failed providers: ${failed_providers[*]}"
    fi
    
    if [[ ${#recovered_providers[@]} -gt 0 ]]; then
        print_success "Recovered providers: ${recovered_providers[*]}"
    fi
}

# Function to generate health report
generate_health_report() {
    local report_file="$HOME/.kiro/health_report.json"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    print_status "Generating health report..."
    
    # Start JSON report
    cat > "$report_file" << EOF
{
  "timestamp": "$timestamp",
  "providers": {
EOF
    
    local first=true
    for provider in "${!PROVIDERS[@]}"; do
        local endpoint="${PROVIDERS[$provider]}"
        local status="healthy"
        local response_time=0
        
        # Measure response time
        local start_time=$(date +%s%N)
        if ! check_provider_health "$provider" "$endpoint"; then
            status="unhealthy"
        fi
        local end_time=$(date +%s%N)
        response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
        
        # Add comma if not first entry
        if [[ "$first" == "false" ]]; then
            echo "," >> "$report_file"
        fi
        first=false
        
        # Add provider entry
        cat >> "$report_file" << EOF
    "$provider": {
      "status": "$status",
      "endpoint": "$endpoint",
      "response_time_ms": $response_time
    }
EOF
    done
    
    # Close JSON
    cat >> "$report_file" << EOF
  }
}
EOF
    
    print_success "Health report generated: $report_file"
}

# Function to start monitoring daemon
start_daemon() {
    # Check if already running
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        print_error "Health monitor is already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi
    
    print_status "Starting health monitor daemon..."
    
    # Save PID
    echo $$ > "$PID_FILE"
    
    # Setup signal handlers
    trap 'cleanup_daemon' EXIT INT TERM
    
    print_success "Health monitor started (PID: $$)"
    send_notification "codeKent health monitor started" "info"
    
    # Main monitoring loop
    while true; do
        perform_health_checks
        
        # Generate report every 10 cycles (5 minutes with 30s interval)
        if (( $(date +%s) % 300 < HEALTH_CHECK_INTERVAL )); then
            generate_health_report
        fi
        
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# Function to stop monitoring daemon
stop_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping health monitor daemon (PID: $pid)..."
            kill "$pid"
            rm -f "$PID_FILE"
            print_success "Health monitor stopped"
        else
            print_warning "Health monitor is not running"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "Health monitor PID file not found"
    fi
}

# Function to cleanup daemon
cleanup_daemon() {
    print_status "Cleaning up health monitor daemon..."
    rm -f "$PID_FILE"
    send_notification "codeKent health monitor stopped" "info"
}

# Function to show daemon status
show_status() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        local pid=$(cat "$PID_FILE")
        print_success "Health monitor is running (PID: $pid)"
        
        # Show recent log entries
        if [[ -f "$LOG_FILE" ]]; then
            print_status "Recent log entries:"
            tail -10 "$LOG_FILE"
        fi
    else
        print_warning "Health monitor is not running"
        if [[ -f "$PID_FILE" ]]; then
            rm -f "$PID_FILE"
        fi
    fi
}

# Function to run single health check
run_single_check() {
    print_status "Running single health check..."
    perform_health_checks
    generate_health_report
}

# Function to print usage
print_usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start     Start health monitoring daemon"
    echo "  stop      Stop health monitoring daemon"
    echo "  status    Show daemon status"
    echo "  check     Run single health check"
    echo "  report    Generate health report"
    echo ""
    echo "Configuration:"
    echo "  Health check interval: ${HEALTH_CHECK_INTERVAL}s"
    echo "  Log file: $LOG_FILE"
    echo "  PID file: $PID_FILE"
}

# Main execution
main() {
    local command="$1"
    
    # Setup logging
    setup_logging
    
    case "$command" in
        "start")
            start_daemon
            ;;
        "stop")
            stop_daemon
            ;;
        "status")
            show_status
            ;;
        "check")
            run_single_check
            ;;
        "report")
            generate_health_report
            ;;
        "help"|"--help"|"-h"|"")
            print_usage
            ;;
        *)
            print_error "Unknown command: $command"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
