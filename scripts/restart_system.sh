#!/bin/bash

# AI Trading System Restart Script
# Restarts all services with enhanced architecture improvements

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="logs/system_restart_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Service definitions with startup order
SERVICES=(
    "mcp_hub:8000:src/mcp_hub/main.py"
    "orchestrator:8001:src/orchestrator_service.py"
    "portfolio:8002:src/portfolio_service.py"
    "market_analyst:8003:src/market_analyst/market_analyst_service.py"
    "news_analyst:8004:src/news_analyst/news_analyst_service.py"
    "notification:8005:src/notification_service.py"
    "trade_executor:8006:src/market_executor_service.py"
    "parameter_optimizer:8007:src/parameter_optimizer_service.py"
)

# Check dependencies
check_dependencies() {
    log_info "🔍 Checking system dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required but not installed"
        exit 1
    fi
    
    # Check required directories
    for dir in logs data config; do
        if [[ ! -d "$dir" ]]; then
            log_warning "Creating missing directory: $dir"
            mkdir -p "$dir"
        fi
    done
    
    # Check configuration files
    if [[ ! -f "config/production_config.yaml" ]]; then
        log_error "Missing production_config.yaml"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Stop existing services
stop_services() {
    log_info "🛑 Stopping existing services..."
    
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name port script_path <<< "$service_def"
        
        # Find and kill processes on the port
        if lsof -ti:$port &> /dev/null; then
            log_info "Stopping $service_name on port $port"
            lsof -ti:$port | xargs kill -TERM 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if lsof -ti:$port &> /dev/null; then
                log_warning "Force killing $service_name"
                lsof -ti:$port | xargs kill -KILL 2>/dev/null || true
            fi
        fi
    done
    
    # Wait for ports to be free
    log_info "Waiting for ports to be released..."
    sleep 3
    
    log_success "All services stopped"
}

# Start individual service
start_service() {
    local service_name=$1
    local port=$2
    local script_path=$3
    
    log_info "🚀 Starting $service_name on port $port..."
    
    # Check if script exists
    if [[ ! -f "$script_path" ]]; then
        log_error "Script not found: $script_path"
        return 1
    fi
    
    # Start the service in background
    python3 "$script_path" > "logs/${service_name}.log" 2>&1 &
    local pid=$!
    
    # Store PID for monitoring
    echo $pid > "logs/${service_name}.pid"
    
    # Wait for service to start
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s -f "http://localhost:$port/health" &> /dev/null; then
            log_success "$service_name started successfully (PID: $pid)"
            return 0
        fi
        
        # Check if process is still running
        if ! kill -0 $pid 2>/dev/null; then
            log_error "$service_name failed to start (process died)"
            return 1
        fi
        
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name failed to start (timeout after ${max_attempts} attempts)"
    return 1
}

# Start all services
start_services() {
    log_info "🚀 Starting all services with enhanced features..."
    
    local failed_services=()
    
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name port script_path <<< "$service_def"
        
        if ! start_service "$service_name" "$port" "$script_path"; then
            failed_services+=("$service_name")
        fi
        
        # Small delay between service starts
        sleep 2
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All services started successfully"
    else
        log_error "Failed to start services: ${failed_services[*]}"
        return 1
    fi
}

# Verify system health
verify_health() {
    log_info "🔍 Verifying system health..."
    
    # Wait a moment for services to fully initialize
    sleep 5
    
    # Run health check
    if python3 scripts/health_monitor.py --format console > /tmp/health_check.log 2>&1; then
        log_success "Health check passed"
        
        # Show summary
        grep "Overall Status" /tmp/health_check.log || true
        grep "Services:" /tmp/health_check.log || true
    else
        log_warning "Health check detected issues"
        cat /tmp/health_check.log
    fi
}

# Test new features
test_enhanced_features() {
    log_info "🧪 Testing enhanced features..."
    
    # Test orchestrator health endpoint with detailed metrics
    log_info "Testing orchestrator health endpoint..."
    if curl -s "http://localhost:8001/health" | jq . > /dev/null 2>&1; then
        log_success "Orchestrator health endpoint working"
    else
        log_warning "Orchestrator health endpoint not responding"
    fi
    
    # Test Slack webhook endpoint (if configured)
    log_info "Testing notification service Slack endpoints..."
    if curl -s -f "http://localhost:8005/health" > /dev/null 2>&1; then
        log_success "Notification service ready for Slack integration"
    else
        log_warning "Notification service not responding"
    fi
    
    log_success "Enhanced features verification complete"
}

# Display service status
show_status() {
    log_info "📊 Current service status:"
    echo ""
    
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name port script_path <<< "$service_def"
        
        if curl -s -f "http://localhost:$port/health" &> /dev/null; then
            echo -e "  ✅ ${service_name} (port $port) - ${GREEN}Running${NC}"
        else
            echo -e "  ❌ ${service_name} (port $port) - ${RED}Not responding${NC}"
        fi
    done
    
    echo ""
    log_info "🔗 Service URLs:"
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name port script_path <<< "$service_def"
        echo "  • $service_name: http://localhost:$port"
    done
    
    echo ""
    log_info "📖 New Documentation:"
    echo "  • Architecture: docs/architecture/"
    echo "  • API Specs: docs/schemas/"
    echo "  • Health Monitoring: scripts/health_monitor.py"
    echo "  • System Cleanup: scripts/cleanup_system.py"
    
    echo ""
    log_info "🎛️ New Slack Commands (if configured):"
    echo "  • /trading-status - Check system status"
    echo "  • /trading-config - Update configuration"
    echo "  • /trading-stop - Emergency stop"
    echo "  • /trading-start - Start trading"
}

# Main execution
main() {
    echo "🚀 AI Trading System Restart with Enhanced Features"
    echo "=================================================="
    echo ""
    
    log_info "Starting system restart at $(date)"
    
    # Run restart sequence
    check_dependencies
    stop_services
    start_services
    verify_health
    test_enhanced_features
    show_status
    
    echo ""
    log_success "🎉 System restart completed successfully!"
    log_info "📄 Restart log saved: $LOG_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Monitor system with: python3 scripts/health_monitor.py"
    echo "  2. Setup automated cleanup: scripts/setup_cleanup_cron.sh install"
    echo "  3. Configure Slack webhooks in config/production_config.yaml"
    echo "  4. Review architecture diagrams in docs/architecture/"
}

# Handle script interruption
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"