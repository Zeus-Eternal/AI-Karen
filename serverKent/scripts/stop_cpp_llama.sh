#!/bin/bash
echo "[DEPRECATED] Use scripts/llamacpp_service.sh stop or manage_cpp_llama.sh stop with CPP_LLAMA_BACKEND=manager." >&2
exit 1
# Stop script for cpp-llama server
# This script provides various methods to stop the cpp-llama server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.kiro/cpp-llama"
SERVER_PORT=8080
PID_FILE="$INSTALL_DIR/server.pid"
LOG_FILE="$INSTALL_DIR/server.log"

# Function to print colored output
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

# Function to check if server is running
is_server_running() {
    local port=${1:-$SERVER_PORT}
    
    # Check if port is in use
    if command -v lsof >/dev/null 2>&1; then
        lsof -i ":$port" >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -ln | grep ":$port " >/dev/null 2>&1
    elif command -v ss >/dev/null 2>&1; then
        ss -ln | grep ":$port " >/dev/null 2>&1
    else
        # Fallback: try to connect to the port
        if command -v curl >/dev/null 2>&1; then
            curl -s --max-time 2 "http://127.0.0.1:$port/health" >/dev/null 2>&1
        else
            return 1
        fi
    fi
}

# Function to get server PID
get_server_pid() {
    local pids=()
    
    # Method 1: Check PID file
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            pids+=("$pid")
        fi
    fi
    
    # Method 2: Find by process name
    if command -v pgrep >/dev/null 2>&1; then
        local found_pids=$(pgrep -f "server.*--port.*$SERVER_PORT" 2>/dev/null || true)
        if [[ -n "$found_pids" ]]; then
            pids+=($found_pids)
        fi
        
        # Also check for llama.cpp server
        found_pids=$(pgrep -f "llama.*server" 2>/dev/null || true)
        if [[ -n "$found_pids" ]]; then
            pids+=($found_pids)
        fi
    fi
    
    # Method 3: Find by port
    if command -v lsof >/dev/null 2>&1; then
        local port_pid=$(lsof -t -i ":$SERVER_PORT" 2>/dev/null || true)
        if [[ -n "$port_pid" ]]; then
            pids+=($port_pid)
        fi
    fi
    
    # Remove duplicates and return
    printf '%s\n' "${pids[@]}" | sort -u
}

# Function to stop server gracefully
stop_server_graceful() {
    print_status "Attempting graceful shutdown..."
    
    local pids=($(get_server_pid))
    
    if [[ ${#pids[@]} -eq 0 ]]; then
        print_warning "No cpp-llama server processes found"
        return 1
    fi
    
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Sending SIGTERM to process $pid..."
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
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    print_warning "Graceful shutdown timed out after ${timeout}s"
    return 1
}

# Function to force stop server
stop_server_force() {
    print_status "Force stopping server..."
    
    local pids=($(get_server_pid))
    
    if [[ ${#pids[@]} -eq 0 ]]; then
        print_warning "No cpp-llama server processes found"
        return 1
    fi
    
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Sending SIGKILL to process $pid..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait a moment and verify
    sleep 2
    
    local still_running=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            still_running+=("$pid")
        fi
    done
    
    if [[ ${#still_running[@]} -eq 0 ]]; then
        print_success "Server force stopped"
        return 0
    else
        print_error "Failed to stop processes: ${still_running[*]}"
        return 1
    fi
}

# Function to stop Docker containers
stop_docker_containers() {
    print_status "Stopping Docker containers..."
    
    local containers_found=false
    
    # Stop cpp-llama containers
    if command -v docker >/dev/null 2>&1; then
        local containers=$(docker ps -q --filter "name=codekent-cpp-llama" 2>/dev/null || true)
        if [[ -n "$containers" ]]; then
            containers_found=true
            print_status "Stopping cpp-llama Docker containers..."
            docker stop $containers >/dev/null 2>&1 || true
            print_success "Docker containers stopped"
        fi
        
        # Also check for containers using the cpp-llama image
        containers=$(docker ps -q --filter "ancestor=codekent/cpp-llama" 2>/dev/null || true)
        if [[ -n "$containers" ]]; then
            containers_found=true
            print_status "Stopping cpp-llama image containers..."
            docker stop $containers >/dev/null 2>&1 || true
        fi
    fi
    
    # Stop using docker-compose if available
    local docker_dir="$(dirname "$0")/../docker"
    if [[ -f "$docker_dir/docker-compose.yml" ]]; then
        cd "$docker_dir"
        
        if command -v docker-compose >/dev/null 2>&1; then
            if docker-compose ps | grep -q "cpp-llama"; then
                containers_found=true
                print_status "Stopping services with docker-compose..."
                docker-compose stop cpp-llama cpp-llama-gpu >/dev/null 2>&1 || true
                print_success "Docker Compose services stopped"
            fi
        elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
            if docker compose ps | grep -q "cpp-llama"; then
                containers_found=true
                print_status "Stopping services with docker compose..."
                docker compose stop cpp-llama cpp-llama-gpu >/dev/null 2>&1 || true
                print_success "Docker Compose services stopped"
            fi
        fi
    fi
    
    if [[ "$containers_found" == false ]]; then
        print_warning "No cpp-llama Docker containers found"
    fi
}

# Function to stop systemd service
stop_systemd_service() {
    if [[ ! -f "/etc/systemd/system/cpp-llama.service" ]]; then
        return 1
    fi
    
    print_status "Stopping systemd service..."
    
    if systemctl is-active --quiet cpp-llama 2>/dev/null; then
        sudo systemctl stop cpp-llama
        print_success "Systemd service stopped"
        return 0
    else
        print_warning "Systemd service is not running"
        return 1
    fi
}

# Function to cleanup resources
cleanup_resources() {
    print_status "Cleaning up resources..."
    
    # Remove PID file
    if [[ -f "$PID_FILE" ]]; then
        rm -f "$PID_FILE"
        print_status "Removed PID file"
    fi
    
    # Rotate log file if it's large
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        print_status "Rotated large log file"
    fi
    
    # Clean up any temporary files
    find /tmp -name "cpp-llama-*" -type f -mtime +1 -delete 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Function to show server status
show_status() {
    print_status "Checking cpp-llama server status..."
    
    local running=false
    
    # Check if server is responding
    if is_server_running; then
        print_success "✅ Server is responding on port $SERVER_PORT"
        running=true
        
        # Try to get server info
        if command -v curl >/dev/null 2>&1; then
            local health=$(curl -s --max-time 5 "http://127.0.0.1:$SERVER_PORT/health" 2>/dev/null || echo "")
            if [[ -n "$health" ]]; then
                print_status "Health check: $health"
            fi
            
            local models=$(curl -s --max-time 5 "http://127.0.0.1:$SERVER_PORT/v1/models" 2>/dev/null || echo "")
            if [[ -n "$models" ]]; then
                print_status "Models endpoint accessible"
            fi
        fi
    else
        print_warning "❌ Server is not responding on port $SERVER_PORT"
    fi
    
    # Check for running processes
    local pids=($(get_server_pid))
    if [[ ${#pids[@]} -gt 0 ]]; then
        print_status "Running processes: ${pids[*]}"
        running=true
    else
        print_status "No cpp-llama processes found"
    fi
    
    # Check systemd service
    if systemctl is-active --quiet cpp-llama 2>/dev/null; then
        print_status "Systemd service: active"
        running=true
    fi
    
    # Check Docker containers
    if command -v docker >/dev/null 2>&1; then
        local containers=$(docker ps --filter "name=codekent-cpp-llama" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || true)
        if [[ -n "$containers" ]] && [[ "$containers" != "NAMES	STATUS" ]]; then
            print_status "Docker containers:"
            echo "$containers"
            running=true
        fi
    fi
    
    if [[ "$running" == true ]]; then
        return 0
    else
        return 1
    fi
}

# Function to show help
show_help() {
    echo "cpp-llama Stop Script"
    echo "===================="
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  stop          Stop server gracefully (default)"
    echo "  force         Force stop server (SIGKILL)"
    echo "  docker        Stop Docker containers"
    echo "  systemd       Stop systemd service"
    echo "  all           Stop all (processes, Docker, systemd)"
    echo "  status        Show server status"
    echo "  cleanup       Clean up resources after stopping"
    echo "  help          Show this help message"
    echo ""
    echo "Options:"
    echo "  --port PORT   Specify server port (default: $SERVER_PORT)"
    echo "  --quiet       Suppress output"
    echo "  --force       Use force stop method"
    echo ""
    echo "Examples:"
    echo "  $0                    # Graceful stop"
    echo "  $0 force              # Force stop"
    echo "  $0 all                # Stop everything"
    echo "  $0 status             # Check status"
    echo "  $0 --port 8081 stop   # Stop server on port 8081"
}

# Main execution function
main() {
    local command="stop"
    local quiet=false
    local force_mode=false
    
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
            --force)
                force_mode=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            stop|force|docker|systemd|all|status|cleanup|help)
                command="$1"
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
        "stop")
            if [[ "$force_mode" == true ]]; then
                stop_server_force
            else
                if ! stop_server_graceful; then
                    print_warning "Graceful stop failed, trying force stop..."
                    stop_server_force
                fi
            fi
            cleanup_resources
            ;;
        "force")
            stop_server_force
            cleanup_resources
            ;;
        "docker")
            stop_docker_containers
            ;;
        "systemd")
            if ! stop_systemd_service; then
                print_warning "Systemd service not available or not running"
            fi
            ;;
        "all")
            print_status "Stopping all cpp-llama services..."
            
            # Try systemd first
            stop_systemd_service || true
            
            # Stop Docker containers
            stop_docker_containers || true
            
            # Stop processes
            if ! stop_server_graceful; then
                stop_server_force || true
            fi
            
            cleanup_resources
            print_success "All services stopped"
            ;;
        "status")
            if show_status; then
                exit 0
            else
                exit 1
            fi
            ;;
        "cleanup")
            cleanup_resources
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
