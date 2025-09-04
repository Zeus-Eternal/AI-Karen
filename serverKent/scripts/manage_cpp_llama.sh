#!/bin/bash
# Comprehensive management script for cpp-llama server
# Provides start, stop, restart, status, and maintenance operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.kiro/cpp-llama"
SERVER_PORT=8080
PID_FILE="$INSTALL_DIR/server.pid"
LOG_FILE="$INSTALL_DIR/server.log"
CONFIG_FILE="$HOME/.kiro/cpp_llama.env"

# New backend bridge (optional)
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CPP_LLAMA_BACKEND="${CPP_LLAMA_BACKEND:-auto}"   # manager|bare|legacy|auto
CPP_LLAMA_MODEL_PATH="${CPP_LLAMA_MODEL_PATH:-}"   # optional explicit model file/dir
CPP_LLAMA_MODEL_DIRS="${CPP_LLAMA_MODEL_DIRS:-}"   # optional colon-separated dirs

# Function to print colored output
print_header() {
    echo -e "${PURPLE}[cpp-llama]${NC} $1"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_action() {
    echo -e "${CYAN}[ACTION]${NC} $1"
}

# Function to load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
        print_status "Loaded configuration from $CONFIG_FILE"
    fi
    
    # Override with environment variables if set
    SERVER_PORT=${CPP_LLAMA_PORT:-$SERVER_PORT}
    INSTALL_DIR=${CPP_LLAMA_INSTALL_DIR:-$INSTALL_DIR}
    
    # Update derived paths
    PID_FILE="$INSTALL_DIR/server.pid"
    LOG_FILE="$INSTALL_DIR/server.log"
}

# Function to check if server is running
is_server_running() {
    local port=${1:-$SERVER_PORT}
    
    if command -v curl >/dev/null 2>&1; then
        curl -s --max-time 2 "http://127.0.0.1:$port/health" >/dev/null 2>&1
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O /dev/null -T 2 "http://127.0.0.1:$port/health" >/dev/null 2>&1
    else
        # Fallback: check if port is in use
        if command -v lsof >/dev/null 2>&1; then
            lsof -i ":$port" >/dev/null 2>&1
        elif command -v netstat >/dev/null 2>&1; then
            netstat -ln | grep ":$port " >/dev/null 2>&1
        else
            return 1
        fi
    fi
}

# Function to get server PID
get_server_pid() {
    local pids=()
    
    # Check PID file
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            pids+=("$pid")
        fi
    fi
    
    # Find by process name
    if command -v pgrep >/dev/null 2>&1; then
        local found_pids=$(pgrep -f "server.*--port.*$SERVER_PORT" 2>/dev/null || true)
        if [[ -n "$found_pids" ]]; then
            pids+=($found_pids)
        fi
    fi
    
    # Remove duplicates
    printf '%s\n' "${pids[@]}" | sort -u
}

# Function to start server
start_server() {
    print_header "Starting cpp-llama server..."
    
    # Check if already running
    if is_server_running; then
        print_warning "Server is already running on port $SERVER_PORT"
        return 0
    fi
    
    # Optional bridge to new manager/bare backends
    local startup_script="$INSTALL_DIR/start_server.sh"
    local use_bridge=0
    if [[ "$CPP_LLAMA_BACKEND" == "manager" || "$CPP_LLAMA_BACKEND" == "bare" ]]; then
        use_bridge=1
    elif [[ "$CPP_LLAMA_BACKEND" == "auto" && ! -f "$startup_script" ]]; then
        use_bridge=1
    fi

    if [[ $use_bridge -eq 1 ]]; then
        print_status "Using new backend: ${CPP_LLAMA_BACKEND/auto/manager}"
        local config_path="$REPO_ROOT/serverKent/configs/llamacpp/config.json"
        local log_dir="$REPO_ROOT/logs/llamacpp"
        mkdir -p "$log_dir"
        if [[ "$CPP_LLAMA_BACKEND" == "bare" ]]; then
            # Bare server path
            local model_arg=()
            if [[ -n "$CPP_LLAMA_MODEL_PATH" ]]; then
                model_arg=("--model" "$CPP_LLAMA_MODEL_PATH")
            fi
            local dirs_env="${CPP_LLAMA_MODEL_DIRS}"
            if [[ -n "$dirs_env" ]]; then export LLAMACPP_MODEL_DIRS="$dirs_env"; fi
            "$REPO_ROOT/serverKent/scripts/llama_bare.sh" start "${model_arg[@]}" \
                --host 127.0.0.1 --port "$SERVER_PORT" --threads "$(nproc || echo 4)" --ctx 4096 \
                --log-dir "$log_dir"
        else
            # Manager path (default)
            LLAMA_CONFIG="$config_path" LLAMACPP_LOG_DIR="$log_dir" \
                "$REPO_ROOT/serverKent/scripts/llamacpp_service.sh" start --config "$config_path" --log-dir "$log_dir"
        fi
        return $?
    fi
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Start server in background
    print_action "Starting server with startup script..."
    nohup "$startup_script" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait for server to start
    local timeout=30
    local count=0
    
    print_status "Waiting for server to start (timeout: ${timeout}s)..."
    
    while [[ $count -lt $timeout ]]; do
        if is_server_running; then
            print_success "Server started successfully (PID: $pid)"
            print_status "Server URL: http://127.0.0.1:$SERVER_PORT"
            print_status "Health check: http://127.0.0.1:$SERVER_PORT/health"
            print_status "Log file: $LOG_FILE"
            return 0
        fi
        
        sleep 1
        ((count++))
        
        # Show progress
        if [[ $((count % 5)) -eq 0 ]]; then
            print_status "Still waiting... (${count}s/${timeout}s)"
        fi
    done
    
    print_error "Server failed to start within ${timeout}s"
    print_status "Check the log file for details: $LOG_FILE"
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    return 1
}

# Function to stop server
stop_server() {
    print_header "Stopping cpp-llama server..."
    
    # Bridge to new backend if selected
    if [[ "$CPP_LLAMA_BACKEND" == "manager" || ( "$CPP_LLAMA_BACKEND" == "auto" && ! -f "$INSTALL_DIR/start_server.sh" ) ]]; then
        "$REPO_ROOT/scripts/llamacpp_service.sh" stop --log-dir "$REPO_ROOT/logs/llamacpp"
        return $?
    elif [[ "$CPP_LLAMA_BACKEND" == "bare" ]]; then
        "$REPO_ROOT/scripts/llama_bare.sh" stop --log-dir "$REPO_ROOT/logs/llamacpp"
        return $?
    fi
    
    # Fallback: manual stop
    local pids=($(get_server_pid))
    
    if [[ ${#pids[@]} -eq 0 ]]; then
        print_warning "No server processes found"
        return 0
    fi
    
    # Try graceful shutdown first
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            print_action "Sending SIGTERM to process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait for graceful shutdown
    local timeout=10
    local count=0
    
    while [[ $count -lt $timeout ]]; do
        local running_pids=()
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                running_pids+=("$pid")
            fi
        done
        
        if [[ ${#running_pids[@]} -eq 0 ]]; then
            print_success "Server stopped gracefully"
            rm -f "$PID_FILE"
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    # Force stop if graceful failed
    print_warning "Graceful shutdown timed out, forcing stop..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    sleep 2
    rm -f "$PID_FILE"
    print_success "Server force stopped"
    return 0
}

# Function to restart server
restart_server() {
    print_header "Restarting cpp-llama server..."
    
    stop_server
    sleep 2
    start_server
}

# Function to show server status
show_status() {
    print_header "cpp-llama Server Status"
    echo "========================"
    
    local running=false
    
    # Check if server is responding
    if is_server_running; then
        print_success "✅ Server is running and responding"
        print_status "   URL: http://127.0.0.1:$SERVER_PORT"
        running=true
        
        # Get server info
        if command -v curl >/dev/null 2>&1; then
            local health=$(curl -s --max-time 5 "http://127.0.0.1:$SERVER_PORT/health" 2>/dev/null || echo "")
            if [[ -n "$health" ]]; then
                print_status "   Health: $health"
            fi
            
            local models=$(curl -s --max-time 5 "http://127.0.0.1:$SERVER_PORT/v1/models" 2>/dev/null || echo "")
            if [[ -n "$models" ]]; then
                local model_count=$(echo "$models" | grep -o '"id"' | wc -l)
                print_status "   Models: $model_count available"
            fi
        fi
    else
        print_error "❌ Server is not responding"
    fi
    
    # Check processes
    local pids=($(get_server_pid))
    if [[ ${#pids[@]} -gt 0 ]]; then
        print_status "📊 Process info:"
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null || echo "Unknown")
                local mem=$(ps -p "$pid" -o rss= 2>/dev/null || echo "0")
                local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null || echo "0")
                print_status "   PID $pid: ${mem}KB RAM, ${cpu}% CPU"
                print_status "   Command: ${cmd:0:80}..."
            fi
        done
        running=true
    else
        print_status "📊 No processes found"
    fi
    
    # Check files
    print_status "📁 File info:"
    if [[ -f "$PID_FILE" ]]; then
        print_status "   PID file: $PID_FILE ($(cat "$PID_FILE" 2>/dev/null || echo "empty"))"
    else
        print_status "   PID file: Not found"
    fi
    
    if [[ -f "$LOG_FILE" ]]; then
        local log_size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        local log_size_mb=$((log_size / 1024 / 1024))
        print_status "   Log file: $LOG_FILE (${log_size_mb}MB)"
    else
        print_status "   Log file: Not found"
    fi
    
    if [[ -f "$CONFIG_FILE" ]]; then
        print_status "   Config: $CONFIG_FILE"
    else
        print_status "   Config: Not found"
    fi
    
    # Check Docker containers
    if command -v docker >/dev/null 2>&1; then
        local containers=$(docker ps --filter "name=codekent-cpp-llama" --format "{{.Names}}: {{.Status}}" 2>/dev/null || true)
        if [[ -n "$containers" ]]; then
            print_status "🐳 Docker containers:"
            echo "$containers" | while read -r line; do
                print_status "   $line"
            done
            running=true
        fi
    fi
    
    # Overall status
    echo ""
    if [[ "$running" == true ]]; then
        print_success "Overall Status: RUNNING"
        return 0
    else
        print_error "Overall Status: STOPPED"
        # Extra diagnostics for new backends (manager/bare)
        echo ""
        print_status "🔎 Backend diagnostics (manager/bare):"
        local LOG_DIR="$REPO_ROOT/logs/llamacpp"
        local MGR_PID_FILE="$LOG_DIR/manager.pid"
        local SRV_PID_FILE="$LOG_DIR/llama-server.pid"
        if [[ -f "$MGR_PID_FILE" ]]; then
            local mpid=$(cat "$MGR_PID_FILE" 2>/dev/null)
            if [[ -n "$mpid" && $(kill -0 "$mpid" 2>/dev/null; echo $?) -eq 0 ]]; then
                print_status "   Manager PID: $mpid (alive)"
            else
                print_status "   Manager PID: $mpid (not running)"
            fi
        else
            print_status "   Manager PID file: not found ($MGR_PID_FILE)"
        fi

        if [[ -f "$SRV_PID_FILE" ]]; then
            local spid=$(cat "$SRV_PID_FILE" 2>/dev/null)
            if [[ -n "$spid" && $(kill -0 "$spid" 2>/dev/null; echo $?) -eq 0 ]]; then
                # Quick CPU/RAM snapshot
                local smem=$(ps -p "$spid" -o rss= 2>/dev/null || echo "0")
                local scpu=$(ps -p "$spid" -o %cpu= 2>/dev/null || echo "0")
                print_status "   Server PID: $spid (alive) — ${smem}KB RAM, ${scpu}% CPU"
            else
                print_status "   Server PID: $spid (not running)"
            fi
        else
            print_status "   Server PID file: not found ($SRV_PID_FILE)"
        fi

        # Probe /health explicitly on configured port
        if command -v curl >/dev/null 2>&1; then
            local hc=$(curl -s -m 2 -w "\n%{http_code}" "http://127.0.0.1:$SERVER_PORT/health" 2>/dev/null || true)
            local hc_body=$(echo "$hc" | sed '$d')
            local hc_code=$(echo "$hc" | tail -n1)
            if [[ -n "$hc_code" ]]; then
                print_status "   Health probe: HTTP $hc_code"
                [[ -n "$hc_body" ]] && print_status "   Body: ${hc_body:0:160}"
            fi
        fi

        # Point to logs
        local MSTDERR="$LOG_DIR/manager.stderr"
        local MSTDOUT="$LOG_DIR/manager.stdout"
        local SERR="$LOG_DIR/stderr.log"
        local SOUT="$LOG_DIR/stdout.log"
        print_status "   Logs (manager): $MSTDERR | $MSTDOUT"
        print_status "   Logs (server):  $SERR | $SOUT"
        return 1
    fi
}

# Function to show logs
show_logs() {
    local lines=${1:-50}
    
    print_header "cpp-llama Server Logs (last $lines lines)"
    echo "========================================="
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -n "$lines" "$LOG_FILE"
    else
        print_warning "Log file not found: $LOG_FILE"
    fi
}

# Function to follow logs
follow_logs() {
    print_header "Following cpp-llama Server Logs (Ctrl+C to stop)"
    echo "================================================="
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        print_warning "Log file not found: $LOG_FILE"
        print_status "Waiting for log file to be created..."
        
        # Wait for log file to be created
        while [[ ! -f "$LOG_FILE" ]]; do
            sleep 1
        done
        
        tail -f "$LOG_FILE"
    fi
}

# Function to run health check
health_check() {
    print_header "Running health check..."
    
    if [[ -f "$INSTALL_DIR/health_check.sh" ]]; then
        "$INSTALL_DIR/health_check.sh"
    else
        # Manual health check
        if is_server_running; then
            print_success "✅ Server is healthy"
            return 0
        else
            print_error "❌ Server is not responding"
            return 1
        fi
    fi
}

# Function to show help
show_help() {
    echo "cpp-llama Management Script"
    echo "=========================="
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start         Start the server"
    echo "  stop          Stop the server"
    echo "  restart       Restart the server"
    echo "  status        Show server status"
    echo "  health        Run health check"
    echo "  logs [N]      Show last N lines of logs (default: 50)"
    echo "  follow        Follow logs in real-time"
    echo "  setup         Run initial setup"
    echo "  help          Show this help message"
    echo ""
    echo "Options:"
    echo "  --port PORT   Specify server port (default: $SERVER_PORT)"
    echo "  --quiet       Suppress output"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start server"
    echo "  $0 status             # Check status"
    echo "  $0 logs 100           # Show last 100 log lines"
    echo "  $0 --port 8081 start  # Start on port 8081"
    echo ""
    echo "Configuration:"
    echo "  Config file: $CONFIG_FILE"
    echo "  Install dir: $INSTALL_DIR"
    echo "  Log file: $LOG_FILE"
}

# Main execution function
main() {
    local command="status"
    local quiet=false
    local log_lines=50
    
    # Load configuration first
    load_config
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                SERVER_PORT="$2"
                shift 2
                ;;
            --quiet)
                quiet=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            start|stop|restart|status|health|logs|follow|setup|help)
                command="$1"
                shift
                ;;
            [0-9]*)
                if [[ "$command" == "logs" ]]; then
                    log_lines="$1"
                fi
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Redirect output if quiet mode
    if [[ "$quiet" == true ]]; then
        exec >/dev/null 2>&1
    fi
    
    # Execute command
    case $command in
        "start")
            start_server
            ;;
        "stop")
            stop_server
            ;;
        "restart")
            restart_server
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "logs")
            show_logs "$log_lines"
            ;;
        "follow")
            follow_logs
            ;;
        "setup")
            if [[ -f "$SCRIPT_DIR/setup_cpp_llama.sh" ]]; then
                "$SCRIPT_DIR/setup_cpp_llama.sh"
            else
                print_error "Setup script not found: $SCRIPT_DIR/setup_cpp_llama.sh"
                exit 1
            fi
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
