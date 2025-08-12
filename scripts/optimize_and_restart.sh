#!/bin/bash

# AI Trading System - Optimize and Restart Script
# Runs the Parameter Optimizer and then restarts the system with optimized parameters

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
OPTIMIZER_PORT=8006
ORCHESTRATOR_PORT=8000

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

echo -e "${CYAN}🔄 AI Trading System - Optimize and Restart${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"

# Function to check if a service is running
check_service() {
    local port=$1
    local service_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name (port $port) - Running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (port $port) - Not running${NC}"
        return 1
    fi
}

# Step 1: Stop the current system
echo -e "${YELLOW}🛑 Stopping the current system...${NC}"
"$PROJECT_ROOT/scripts/stop_agents.sh"

# Step 2: Start only the Parameter Optimizer
echo -e "${YELLOW}🚀 Starting Parameter Optimizer...${NC}"
export SERVICE_PORT=$OPTIMIZER_PORT
export MCP_CONFIG_FILE="$PROJECT_ROOT/config/agent_mcps/parameter_optimizer_mcps.yaml"
cd "$PROJECT_ROOT"

# Start the Parameter Optimizer and capture its PID
OPTIMIZER_PID=""
python "src/parameter_optimizer_service.py" > "$LOG_DIR/parameter-optimizer.log" 2>&1 &
OPTIMIZER_PID=$!
echo -e "${BLUE}📝 Parameter Optimizer started with PID: $OPTIMIZER_PID${NC}"

# Wait for Parameter Optimizer to start
echo -e "${BLUE}⏳ Waiting for Parameter Optimizer to start...${NC}"
for i in {1..10}; do
    if check_service $OPTIMIZER_PORT "Parameter Optimizer"; then
        break
    fi
    sleep 2
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Parameter Optimizer failed to start${NC}"
        # Kill the process if it's still running
        if kill -0 $OPTIMIZER_PID 2>/dev/null; then
            kill $OPTIMIZER_PID
        fi
        exit 1
    fi
done

# Step 3: Run optimization
echo -e "${YELLOW}🧠 Running parameter optimization...${NC}"
OPTIMIZATION_RESULT=$(curl -s -X POST "http://localhost:$OPTIMIZER_PORT/force-optimize")
echo -e "${BLUE}📊 Optimization result:${NC}"
echo "$OPTIMIZATION_RESULT" | python3 -m json.tool

# Step 4: Stop the Parameter Optimizer
echo -e "${YELLOW}🛑 Stopping Parameter Optimizer...${NC}"
if kill -0 $OPTIMIZER_PID 2>/dev/null; then
    kill $OPTIMIZER_PID
    echo -e "${GREEN}✅ Parameter Optimizer stopped${NC}"
else
    echo -e "${YELLOW}⚠️ Parameter Optimizer already stopped${NC}"
fi

# Step 5: Start the full system with optimized parameters
echo -e "${YELLOW}🚀 Starting the system with optimized parameters...${NC}"
"$PROJECT_ROOT/scripts/start_agents.sh"

# Step 6: Start orchestration
echo -e "${YELLOW}🤖 Starting orchestration...${NC}"
ORCHESTRATION_RESULT=$(curl -s -X POST "http://localhost:$ORCHESTRATOR_PORT/start-orchestration")
echo -e "${BLUE}📊 Orchestration result:${NC}"
echo "$ORCHESTRATION_RESULT" | python3 -m json.tool

echo -e "${GREEN}✅ System optimized and restarted successfully!${NC}"
echo -e "${BLUE}💡 System status: http://localhost:$ORCHESTRATOR_PORT/system-status${NC}"