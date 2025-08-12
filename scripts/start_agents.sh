#!/bin/bash

# AI Agent Trading System - Startup Script
# Launches all AI agents with proper scheduling and MCP configurations

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
PID_DIR="$PROJECT_ROOT/pids"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

# Source environment file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}🔍 Loading environment variables from .env${NC}"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Ensure all Python dependencies are installed
echo -e "${BLUE}🔍 Installing Python dependencies from requirements.txt...${NC}"
pip install -r "$PROJECT_ROOT/requirements.txt"

echo -e "${CYAN}🤖 AI Agent Trading System - Startup${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}Log Directory: $LOG_DIR${NC}"

# Function to check if a service is running
check_service() {
    local port=$1
    local service_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name (port $port) - Already running${NC}"
        return 0
    else
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local script_path=$3
    local mcp_config=$4
    
    echo -e "${YELLOW}🚀 Starting $service_name...${NC}"
    
    # Set environment variables
    export SERVICE_PORT=$port
    export MCP_CONFIG_FILE="$PROJECT_ROOT/config/agent_mcps/$mcp_config"
    
    # Start the service in background
    cd "$PROJECT_ROOT"
    nohup python "$script_path" > "$LOG_DIR/$service_name.log" 2>&1 &
    echo $! > "$PID_DIR/$service_name.pid"
    
    # Wait a moment for service to start
    sleep 3
    
    # Check if service started successfully
    if check_service $port "$service_name"; then
        echo -e "${GREEN}✅ $service_name started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        cat "$LOG_DIR/$service_name.log" | tail -10
        return 1
    fi
}

# Function to check Ollama availability
check_ollama() {
    echo -e "${BLUE}🔍 Checking Ollama availability...${NC}"
    
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is available at $OLLAMA_URL${NC}"
        
        # Check for required models
        echo -e "${BLUE}🔍 Checking required AI models...${NC}"
        
        models=$(curl -s "$OLLAMA_URL/api/tags" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [model['name'] for model in data.get('models', [])]
print(' '.join(models))
")
        
        if echo "$models" | grep -q "mistral"; then
            echo -e "${GREEN}✅ mistral model available${NC}"
        else
            echo -e "${YELLOW}⚠️  mistral model not found - Risk Manager and Analyst agents may not work${NC}"
        fi
        
        if echo "$models" | grep -q "phi3"; then
            echo -e "${GREEN}✅ phi3 model available${NC}"
        else
            echo -e "${YELLOW}⚠️  phi3 model not found - Trade Executor agent may not work${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️  Ollama not available at $OLLAMA_URL - AI agents will use fallback mode${NC}"
    fi
}

# Function to check database
check_database() {
    echo -e "${BLUE}🔍 Checking database...${NC}"
    
    DB_PATH="${DB_PATH:-$PROJECT_ROOT/database/paper_trading.db}"
    
    if [ -f "$DB_PATH" ]; then
        echo -e "${GREEN}✅ Database found at $DB_PATH${NC}"
    else
        echo -e "${YELLOW}⚠️  Database not found - will be created automatically${NC}"
        mkdir -p "$(dirname "$DB_PATH")"
    fi
}

# Main startup sequence
main() {
    echo -e "${CYAN}🔧 Pre-flight checks...${NC}"
    
    # Check prerequisites  
    check_ollama
    check_database
    
    echo ""
    echo -e "${CYAN}🚀 Starting AI Agents...${NC}"
    
    # 1. Start Risk Manager Agent (mistral7b:latest)
    if ! check_service 8002 "Risk Manager Agent"; then
        start_service "risk-manager" 8002 "src/signal_service.py" "risk_manager_mcps.yaml"
    fi
    
    # 2. Start Market/News Analyst Agent (mistral7b:latest)
    if ! check_service 8003 "Market/News Analyst Agent"; then
        start_service "market-news-analyst" 8003 "src/market_analyst/market_analyst_service.py" "market_news_analyst_mcps.yaml"
    fi
    
    # 3. Start Trade Executor Agent (phi3)
    if ! check_service 8005 "Trade Executor Agent"; then
        start_service "trade-executor" 8005 "src/market_executor_service.py" "trade_executor_mcps.yaml"
    fi
    
    # 4. Start Parameter Optimizer (Python service)
    if ! check_service 8006 "Parameter Optimizer"; then
        start_service "parameter-optimizer" 8006 "src/parameter_optimizer_service.py" "parameter_optimizer_mcps.yaml"
    fi
    
    # 5. Start supporting services
    echo ""
    echo -e "${CYAN}🔧 Starting supporting services...${NC}"
    
    # Portfolio service
    if ! check_service 8001 "Portfolio Service"; then
        start_service "portfolio" 8001 "src/portfolio_service.py" ""
    fi
    
    # Notification service
    if ! check_service 8004 "Notification Service"; then
        start_service "notification" 8004 "src/notification_service.py" ""
    fi
    
    # 6. Start Agent Orchestrator (main coordinator)
    if ! check_service 8000 "Agent Orchestrator"; then
        start_service "orchestrator" 8000 "src/orchestrator_service.py" ""
    fi
    
    echo ""
    echo -e "${GREEN}🎉 AI Agent Trading System Startup Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    
    # Display service status
    echo -e "${CYAN}📊 Service Status:${NC}"
    echo -e "  • Risk Manager Agent:      http://localhost:8002/health"
    echo -e "  • Market/News Analyst:     http://localhost:8003/health"
    echo -e "  • Trade Executor Agent:    http://localhost:8005/health"
    echo -e "  • Parameter Optimizer:     http://localhost:8006/health"
    echo -e "  • Portfolio Service:       http://localhost:8001/health"
    echo -e "  • Notification Service:    http://localhost:8004/health"
    echo -e "  • Agent Orchestrator:      http://localhost:8000/health"
    
    echo ""
    echo -e "${PURPLE}🤖 AI Agent Architecture:${NC}"
    echo -e "  • Risk Manager:     mistral7b:latest → Portfolio/Database MCPs"
    echo -e "  • Market Analyst:   mistral7b:latest → Market Data MCPs (alternating)"
    echo -e "  • Trade Executor:   phi3 → Broker/Exchange MCPs"
    echo -e "  • Optimizer:        Python → Optuna MCP (loss event monitoring)"
    
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo -e "  • Start orchestration: curl -X POST http://localhost:8000/start-orchestration"
    echo -e "  • Stop orchestration:  curl -X POST http://localhost:8000/stop-orchestration"
    echo -e "  • System status:       curl http://localhost:8000/system-status"
    echo -e "  • Stop all services:   $PROJECT_ROOT/scripts/stop_agents.sh"
    
    echo ""
    echo -e "${GREEN}✅ All systems operational! Ready for agent orchestration.${NC}"
}

# Handle script termination
cleanup() {
    echo -e "\n${YELLOW}🛑 Startup interrupted${NC}"
    exit 1
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@"
