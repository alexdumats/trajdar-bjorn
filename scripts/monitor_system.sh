#!/bin/bash

# AI Trading System - Production Monitoring Script
# Monitors system health and performance on Hetzner server

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="/opt/ai-trading-system"
LOG_DIR="$PROJECT_ROOT/logs"
MONITORING_LOG="$LOG_DIR/monitoring.log"

# Create monitoring directory
mkdir -p "$LOG_DIR"

# Log function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$MONITORING_LOG"
}

# Check system resources
check_system_resources() {
    echo -e "${BLUE}💻 System Resources${NC}"
    echo "===================="
    
    # CPU Usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "CPU Usage: ${cpu_usage}%"
    
    # Memory Usage
    local mem_info=$(free -h | grep '^Mem:')
    local mem_used=$(echo $mem_info | awk '{print $3}')
    local mem_total=$(echo $mem_info | awk '{print $2}')
    echo -e "Memory: $mem_used / $mem_total"
    
    # Disk Usage
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    echo -e "Disk Usage: ${disk_usage}%"
    
    # Load Average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "Load Average:$load_avg"
    
    # Log high resource usage
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log_message "WARNING" "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( disk_usage > 85 )); then
        log_message "WARNING" "High disk usage: ${disk_usage}%"
    fi
    
    echo ""
}

# Check Docker containers
check_docker_containers() {
    echo -e "${BLUE}🐳 Docker Containers${NC}"
    echo "====================="
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not installed${NC}"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Get container status
    local containers=$(docker-compose -f docker-compose.production.yml ps --format table)
    echo "$containers"
    
    # Check unhealthy containers
    local unhealthy=$(docker ps --filter health=unhealthy --format "table {{.Names}}\t{{.Status}}")
    if [[ -n "$unhealthy" && "$unhealthy" != "NAMES	STATUS" ]]; then
        echo -e "\n${RED}⚠️  Unhealthy Containers:${NC}"
        echo "$unhealthy"
        log_message "ERROR" "Unhealthy containers detected"
    fi
    
    echo ""
}

# Check service health endpoints
check_service_health() {
    echo -e "${BLUE}🔍 Service Health Checks${NC}"
    echo "========================="
    
    local services=(
        "orchestrator:8000"
        "portfolio:8001" 
        "risk-manager:8002"
        "market-analyst:8003"
        "notification:8004"
        "trade-executor:8005"
        "parameter-optimizer:8006"
    )
    
    for service_info in "${services[@]}"; do
        local service_name=$(echo "$service_info" | cut -d':' -f1)
        local port=$(echo "$service_info" | cut -d':' -f2)
        
        if curl -s -f "http://localhost:$port/health" > /dev/null; then
            local health_data=$(curl -s "http://localhost:$port/health")
            local status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo -e "${GREEN}✅${NC} $service_name ($port): $status"
        else
            echo -e "${RED}❌${NC} $service_name ($port): Not responding"
            log_message "ERROR" "$service_name service not responding on port $port"
        fi
    done
    
    echo ""
}

# Check Ollama service
check_ollama() {
    echo -e "${BLUE}🤖 Ollama AI Service${NC}"
    echo "==================="
    
    if curl -s "http://localhost:11434/api/tags" > /dev/null; then
        local models=$(curl -s "http://localhost:11434/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅${NC} Ollama service: Running"
        echo "Available models:"
        echo "$models" | sed 's/^/  - /'
    else
        echo -e "${RED}❌${NC} Ollama service: Not responding"
        log_message "ERROR" "Ollama service not responding"
    fi
    
    echo ""
}

# Check database
check_database() {
    echo -e "${BLUE}🗄️  Database Status${NC}"
    echo "=================="
    
    local db_path="$PROJECT_ROOT/database/paper_trading.db"
    
    if [[ -f "$db_path" ]]; then
        local db_size=$(du -h "$db_path" | cut -f1)
        echo -e "${GREEN}✅${NC} Database file exists: $db_size"
        
        # Check table count and recent activity
        local table_count=$(sqlite3 "$db_path" "SELECT count(name) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
        echo -e "Tables: $table_count"
        
        # Check recent trades
        local recent_trades=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM paper_trades WHERE datetime(timestamp) > datetime('now', '-1 hour');" 2>/dev/null || echo "0")
        echo -e "Trades (last hour): $recent_trades"
        
        # Check portfolio balance
        local portfolio_balance=$(sqlite3 "$db_path" "SELECT total_value FROM paper_portfolio ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "unknown")
        echo -e "Current portfolio value: $portfolio_balance"
        
    else
        echo -e "${RED}❌${NC} Database file not found"
        log_message "ERROR" "Database file not found at $db_path"
    fi
    
    echo ""
}

# Check log files
check_log_files() {
    echo -e "${BLUE}📋 Log Files Status${NC}"
    echo "==================="
    
    if [[ -d "$LOG_DIR" ]]; then
        local log_count=$(find "$LOG_DIR" -name "*.log" | wc -l)
        echo -e "Log files: $log_count"
        
        # Show recent log files
        echo "Recent log files:"
        find "$LOG_DIR" -name "*.log" -mtime -1 -exec ls -lh {} \; | head -5 | awk '{print "  " $9 ": " $5}'
        
        # Check for error patterns
        local error_count=$(find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -c "ERROR\|CRITICAL\|FATAL" {} \; | awk '{sum += $1} END {print sum}' || echo "0")
        if (( error_count > 0 )); then
            echo -e "${YELLOW}⚠️  Errors found in logs (last 24h): $error_count${NC}"
            log_message "WARNING" "$error_count errors found in recent logs"
        fi
        
    else
        echo -e "${RED}❌${NC} Log directory not found"
    fi
    
    echo ""
}

# Check network connectivity
check_network() {
    echo -e "${BLUE}🌐 Network Connectivity${NC}"
    echo "======================="
    
    # Check internet connectivity
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Internet connectivity: OK"
    else
        echo -e "${RED}❌${NC} Internet connectivity: Failed"
        log_message "ERROR" "Internet connectivity check failed"
    fi
    
    # Check DNS resolution
    if nslookup google.com > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} DNS resolution: OK"
    else
        echo -e "${RED}❌${NC} DNS resolution: Failed"
        log_message "ERROR" "DNS resolution failed"
    fi
    
    echo ""
}

# Generate system report
generate_report() {
    local report_file="$PROJECT_ROOT/system_report_$(date +%Y%m%d_%H%M%S).txt"
    
    echo -e "${BLUE}📊 Generating system report...${NC}"
    
    {
        echo "AI Trading System - Health Report"
        echo "=================================="
        echo "Generated: $(date)"
        echo "Server: $(hostname)"
        echo ""
        
        echo "SYSTEM RESOURCES"
        echo "================"
        uptime
        free -h
        df -h
        echo ""
        
        echo "DOCKER STATUS"
        echo "============="
        docker --version
        cd "$PROJECT_ROOT" && docker-compose -f docker-compose.production.yml ps
        echo ""
        
        echo "SERVICE HEALTH"
        echo "=============="
        for port in 8000 8001 8002 8003 8004 8005 8006; do
            if curl -s -f "http://localhost:$port/health" > /dev/null; then
                echo "Port $port: OK"
            else
                echo "Port $port: NOT RESPONDING"
            fi
        done
        echo ""
        
        echo "RECENT LOGS (ERRORS)"
        echo "==================="
        find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -H "ERROR\|CRITICAL\|FATAL" {} \; | tail -10
        
    } > "$report_file"
    
    echo -e "${GREEN}✅${NC} Report saved to: $report_file"
}

# Auto-restart unhealthy services
restart_unhealthy_services() {
    echo -e "${BLUE}🔄 Checking for services to restart...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Get unhealthy containers
    local unhealthy_containers=$(docker ps --filter health=unhealthy --format "{{.Names}}")
    
    if [[ -n "$unhealthy_containers" ]]; then
        echo -e "${YELLOW}⚠️  Found unhealthy containers, attempting restart...${NC}"
        
        for container in $unhealthy_containers; do
            echo -e "Restarting $container..."
            docker-compose -f docker-compose.production.yml restart "$container"
            log_message "INFO" "Restarted unhealthy container: $container"
        done
        
        # Wait and check again
        sleep 30
        echo -e "${BLUE}Checking health after restart...${NC}"
        check_service_health
    else
        echo -e "${GREEN}✅${NC} No unhealthy services found"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  health       Check all system health (default)"
    echo "  services     Check only service health"
    echo "  resources    Check only system resources"
    echo "  database     Check only database status"
    echo "  logs         Check only log files"
    echo "  report       Generate detailed system report"
    echo "  restart      Restart unhealthy services"
    echo "  watch        Continuous monitoring (updates every 30s)"
    echo ""
    echo "Examples:"
    echo "  $0           # Full health check"
    echo "  $0 services  # Check service endpoints only"
    echo "  $0 watch     # Continuous monitoring"
}

# Watch mode - continuous monitoring
watch_system() {
    echo -e "${CYAN}👀 Continuous System Monitoring${NC}"
    echo -e "${CYAN}Press Ctrl+C to stop${NC}"
    echo ""
    
    while true; do
        clear
        echo -e "${CYAN}=== AI Trading System Monitor - $(date) ===${NC}"
        echo ""
        
        check_system_resources
        check_docker_containers
        check_service_health
        
        echo -e "${BLUE}Next update in 30 seconds...${NC}"
        sleep 30
    done
}

# Main function
main() {
    local command="${1:-health}"
    
    case $command in
        "health")
            echo -e "${CYAN}🏥 AI Trading System - Health Check${NC}"
            echo -e "${CYAN}====================================${NC}"
            echo ""
            check_system_resources
            check_docker_containers
            check_service_health
            check_ollama
            check_database
            check_log_files
            check_network
            ;;
        "services")
            check_service_health
            ;;
        "resources")
            check_system_resources
            ;;
        "database")
            check_database
            ;;
        "logs")
            check_log_files
            ;;
        "report")
            generate_report
            ;;
        "restart")
            restart_unhealthy_services
            ;;
        "watch")
            watch_system
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"