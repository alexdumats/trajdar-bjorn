#!/bin/bash

# AI Agent Trading System - Stop Script
# Gracefully stops all AI agents and services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/pids"

echo -e "${CYAN}🛑 AI Agent Trading System - Shutdown${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"

# Function to stop a service
stop_service() {
    local service_name=$1
    local port=$2
    
    echo -e "${YELLOW}🛑 Stopping $service_name...${NC}"
    
    # Try graceful shutdown via API first
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${BLUE}  📡 Attempting graceful shutdown via API...${NC}"
        
        # Try service-specific shutdown endpoints
        case $service_name in
            "orchestrator")
                curl -s -X POST "http://localhost:$port/stop-orchestration" > /dev/null 2>&1 || true
                ;;
            "parameter-optimizer")
                curl -s -X POST "http://localhost:$port/stop-monitoring" > /dev/null 2>&1 || true
                ;;
            "trade-executor")
                curl -s -X POST "http://localhost:$port/stop-execution" > /dev/null 2>&1 || true
                ;;
        esac
        
        # Give service time to shutdown gracefully
        sleep 2
    fi
    
    # Stop via PID file
    local pid_file="$PID_DIR/$service_name.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${BLUE}  🔪 Terminating process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
            
            # Wait for process to terminate
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}  💀 Force killing process $pid...${NC}"
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        
        rm -f "$pid_file"
    fi
    
    # Verify service is stopped
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${RED}⚠️  $service_name may still be running${NC}"
    else
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    fi
}

# Function to kill processes by port
kill_by_port() {
    local port=$1
    local service_name=$2
    
    echo -e "${YELLOW}🔍 Checking for processes on port $port...${NC}"
    
    # Find process using the port
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pid" ]; then
        echo -e "${BLUE}  🔪 Killing process $pid using port $port...${NC}"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ Port $port freed${NC}"
    fi
}

# Main shutdown sequence
main() {
    echo -e "${BLUE}🔍 Checking running services...${NC}"
    
    # Stop services in reverse order of startup
    echo ""
    echo -e "${CYAN}🛑 Stopping AI Agent services...${NC}"
    
    # 1. Stop Agent Orchestrator first (stops coordination)
    stop_service "orchestrator" 8000
    
    # 2. Stop supporting services
    stop_service "notification" 8004
    stop_service "portfolio" 8001
    
    # 3. Stop AI agents
    stop_service "parameter-optimizer" 8006
    stop_service "trade-executor" 8005
    stop_service "market-news-analyst" 8003
    stop_service "risk-manager" 8002
    
    echo ""
    echo -e "${CYAN}🧹 Cleanup operations...${NC}"
    
    # Clean up any remaining processes on our ports
    local ports=(8000 8001 8002 8003 8004 8005 8006)
    local service_names=("orchestrator" "portfolio" "risk-manager" "market-news-analyst" "notification" "trade-executor" "parameter-optimizer")
    
    for i in "${!ports[@]}"; do
        kill_by_port "${ports[i]}" "${service_names[i]}"
    done
    
    # Clean up PID directory
    if [ -d "$PID_DIR" ]; then
        echo -e "${BLUE}🧹 Cleaning up PID files...${NC}"
        rm -f "$PID_DIR"/*.pid
        rmdir "$PID_DIR" 2>/dev/null || true
    fi
    
    # Check for any remaining Python processes with our service names
    echo -e "${BLUE}🔍 Checking for remaining Python processes...${NC}"
    local remaining_procs=$(ps aux | grep python | grep -E "(signal_service|data_service|market_executor_service|parameter_optimizer_service|orchestrator_service|portfolio_service|notification_service)" | grep -v grep || true)
    
    if [ -n "$remaining_procs" ]; then
        echo -e "${YELLOW}⚠️  Found remaining processes:${NC}"
        echo "$remaining_procs"
        echo -e "${YELLOW}Consider manually terminating these if needed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 AI Agent Trading System Shutdown Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    
    # Final status check
    echo -e "${CYAN}📊 Final Status Check:${NC}"
    local ports_to_check=(8000 8001 8002 8003 8004 8005 8006)
    local all_stopped=true
    
    for port in "${ports_to_check[@]}"; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${RED}❌ Port $port still responding${NC}"
            all_stopped=false
        else
            echo -e "${GREEN}✅ Port $port stopped${NC}"
        fi
    done
    
    if [ "$all_stopped" = true ]; then
        echo ""
        echo -e "${GREEN}✅ All services successfully stopped!${NC}"
        echo -e "${BLUE}💡 To restart: $PROJECT_ROOT/scripts/start_agents.sh${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Some services may still be running${NC}"
        echo -e "${BLUE}💡 Check 'ps aux | grep python' for remaining processes${NC}"
    fi
}

# Handle script termination
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutdown interrupted${NC}"
    exit 1
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@"