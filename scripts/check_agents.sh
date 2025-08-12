#!/bin/bash

# AI Agent Trading System - Status Check Script
# Displays comprehensive status of all agents and services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

echo -e "${CYAN}🔍 AI Agent Trading System - Status Check${NC}"
echo -e "${CYAN}═════════════════════════════════════════════${NC}"

# Function to check service health
check_service_health() {
    local port=$1
    local service_name=$2
    local model=$3
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        local health_data=$(curl -s "http://localhost:$port/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"{data.get('status', 'unknown')} | {data.get('timestamp', 'N/A')}\")
except:
    print('healthy | N/A')
" 2>/dev/null || echo "healthy | N/A")
        
        echo -e "${GREEN}✅ $service_name${NC} (port $port) - $health_data"
        if [ -n "$model" ]; then
            echo -e "   🤖 Model: $model"
        fi
        return 0
    else
        echo -e "${RED}❌ $service_name${NC} (port $port) - Not responding"
        if [ -n "$model" ]; then
            echo -e "   🤖 Model: $model"
        fi
        return 1
    fi
}

# Function to get detailed service info
get_service_details() {
    local port=$1
    local endpoint=${2:-"/status"}
    
    local details=$(curl -s "http://localhost:$port$endpoint" 2>/dev/null || echo "{}")
    if [ "$details" != "{}" ] && [ "$details" != "" ]; then
        echo "$details" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for key, value in data.items():
        if key not in ['status', 'timestamp', 'service']:
            if isinstance(value, (int, float)):
                print(f'   📊 {key}: {value}')
            elif isinstance(value, bool):
                status = '✅' if value else '❌'
                print(f'   {status} {key}: {value}')
            elif isinstance(value, str) and len(value) < 50:
                print(f'   📝 {key}: {value}')
            elif isinstance(value, list) and len(value) < 10:
                print(f'   📋 {key}: {len(value)} items')
except:
    pass
" 2>/dev/null
    fi
}

# Function to check Ollama models
check_ollama_models() {
    echo -e "${BLUE}🤖 Ollama Models Status:${NC}"
    
    OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
    
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        local models=$(curl -s "$OLLAMA_URL/api/tags" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    for model in models:
        name = model.get('name', 'unknown')
        size = model.get('size', 0)
        size_gb = size / (1024**3)
        print(f'   ✅ {name} ({size_gb:.1f}GB)')
    if not models:
        print('   ⚠️  No models found')
except Exception as e:
    print(f'   ❌ Error parsing models: {e}')
" 2>/dev/null)
        echo "$models"
    else
        echo -e "   ${RED}❌ Ollama not accessible at $OLLAMA_URL${NC}"
    fi
}

# Function to check system resources
check_system_resources() {
    echo -e "${BLUE}💻 System Resources:${NC}"
    
    # CPU usage
    local cpu_usage=$(python3 -c "
import psutil
print(f'   🔥 CPU Usage: {psutil.cpu_percent(interval=1)}%')
print(f'   💾 Memory Usage: {psutil.virtual_memory().percent}%')
print(f'   💿 Disk Usage: {psutil.disk_usage(\"/\").percent}%')
" 2>/dev/null || echo "   ⚠️  Unable to get system stats")
    echo "$cpu_usage"
}

# Function to check log files
check_logs() {
    echo -e "${BLUE}📋 Recent Log Activity:${NC}"
    
    if [ -d "$LOG_DIR" ]; then
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                local service=$(basename "$log_file" .log)
                local errors=$(tail -100 "$log_file" 2>/dev/null | grep -i error | wc -l)
                local warnings=$(tail -100 "$log_file" 2>/dev/null | grep -i warning | wc -l)
                local size=$(du -h "$log_file" 2>/dev/null | cut -f1)
                
                if [ $errors -gt 0 ] || [ $warnings -gt 0 ]; then
                    echo -e "   ${YELLOW}⚠️  $service${NC}: ${size}, ${errors} errors, ${warnings} warnings"
                else
                    echo -e "   ${GREEN}✅ $service${NC}: ${size}, clean"
                fi
            fi
        done
    else
        echo -e "   ${YELLOW}⚠️  Log directory not found${NC}"
    fi
}

# Function to get orchestration status
check_orchestration_status() {
    echo -e "${PURPLE}🎯 Agent Orchestration Status:${NC}"
    
    if curl -s "http://localhost:8000/orchestration-status" > /dev/null 2>&1; then
        local orch_status=$(curl -s "http://localhost:8000/orchestration-status" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    running = data.get('running', False)
    status = '✅ ACTIVE' if running else '⏸️  PAUSED'
    print(f'   {status}')
    print(f'   📊 Cycle Count: {data.get(\"cycle_count\", 0)}')
    print(f'   ⏱️  Interval: {data.get(\"interval\", 0)}s')
    active_agent = data.get('active_agent')
    if active_agent:
        print(f'   🤖 Active Agent: {active_agent}')
    else:
        print(f'   🤖 Active Agent: None')
except Exception as e:
    print(f'   ❌ Error: {e}')
" 2>/dev/null)
        echo "$orch_status"
    else
        echo -e "   ${RED}❌ Orchestrator not responding${NC}"
    fi
}

# Main status check
main() {
    echo -e "${CYAN}🔧 Core AI Agents:${NC}"
    
    local agents_healthy=0
    local total_agents=4
    
    # Check AI agents
    if check_service_health 8002 "Risk Manager Agent" "mistral7b:latest"; then
        get_service_details 8002
        agents_healthy=$((agents_healthy + 1))
    fi
    echo ""
    
    if check_service_health 8003 "Market/News Analyst Agent" "mistral7b:latest"; then
        get_service_details 8003
        agents_healthy=$((agents_healthy + 1))
    fi
    echo ""
    
    if check_service_health 8005 "Trade Executor Agent" "phi3"; then
        get_service_details 8005
        agents_healthy=$((agents_healthy + 1))
    fi
    echo ""
    
    if check_service_health 8006 "Parameter Optimizer" "Python (no LLM)"; then
        get_service_details 8006
        agents_healthy=$((agents_healthy + 1))
    fi
    echo ""
    
    echo -e "${CYAN}🔧 Supporting Services:${NC}"
    
    local services_healthy=0
    local total_services=3
    
    # Check supporting services
    if check_service_health 8001 "Portfolio Service"; then
        get_service_details 8001
        services_healthy=$((services_healthy + 1))
    fi
    echo ""
    
    if check_service_health 8004 "Notification Service"; then
        get_service_details 8004
        services_healthy=$((services_healthy + 1))
    fi
    echo ""
    
    if check_service_health 8000 "Agent Orchestrator"; then
        get_service_details 8000
        services_healthy=$((services_healthy + 1))
    fi
    echo ""
    
    # Check additional system components
    check_orchestration_status
    echo ""
    
    check_ollama_models
    echo ""
    
    check_system_resources
    echo ""
    
    check_logs
    echo ""
    
    # Summary
    echo -e "${CYAN}📊 System Health Summary:${NC}"
    echo -e "${CYAN}═══════════════════════════${NC}"
    
    local agent_percentage=$((agents_healthy * 100 / total_agents))
    local service_percentage=$((services_healthy * 100 / total_services))
    
    if [ $agent_percentage -eq 100 ] && [ $service_percentage -eq 100 ]; then
        echo -e "${GREEN}🎉 All Systems Operational!${NC}"
        echo -e "   🤖 AI Agents: $agents_healthy/$total_agents (${agent_percentage}%)"
        echo -e "   🔧 Services: $services_healthy/$total_services (${service_percentage}%)"
    elif [ $agent_percentage -ge 75 ] && [ $service_percentage -ge 75 ]; then
        echo -e "${YELLOW}⚠️  System Partially Operational${NC}"
        echo -e "   🤖 AI Agents: $agents_healthy/$total_agents (${agent_percentage}%)"
        echo -e "   🔧 Services: $services_healthy/$total_services (${service_percentage}%)"
    else
        echo -e "${RED}❌ System Issues Detected${NC}"
        echo -e "   🤖 AI Agents: $agents_healthy/$total_agents (${agent_percentage}%)"
        echo -e "   🔧 Services: $services_healthy/$total_services (${service_percentage}%)"
    fi
    
    echo ""
    echo -e "${BLUE}💡 Management Commands:${NC}"
    echo -e "   • Restart system:    $PROJECT_ROOT/scripts/start_agents.sh"
    echo -e "   • Stop system:       $PROJECT_ROOT/scripts/stop_agents.sh"
    echo -e "   • Start orchestration: curl -X POST http://localhost:8000/start-orchestration"
    echo -e "   • Manual test cycle:   curl -X POST http://localhost:8000/manual-cycle"
}

# Run main function
main "$@"