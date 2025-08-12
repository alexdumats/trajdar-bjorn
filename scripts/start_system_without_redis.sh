#!/bin/bash
# Start the trading system without Redis
# This script starts all the necessary services with Redis fallback modes

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# Create necessary directories
mkdir -p logs
mkdir -p database

# Update the database schema if needed
echo "Updating database schema..."
python scripts/update_db_schema.py

# Start the portfolio service
echo "Starting portfolio service..."
python src/portfolio_service.py > logs/portfolio_service.log 2>&1 &
PORTFOLIO_PID=$!
echo "Portfolio service started with PID: $PORTFOLIO_PID"

# Start the parameter optimizer service
echo "Starting parameter optimizer service..."
python src/parameter_optimizer_service.py > logs/parameter_optimizer_service.log 2>&1 &
OPTIMIZER_PID=$!
echo "Parameter optimizer service started with PID: $OPTIMIZER_PID"

# Start the orchestrator service
echo "Starting orchestrator service..."
python src/orchestrator_service.py > logs/orchestrator_service.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "Orchestrator service started with PID: $ORCHESTRATOR_PID"

# Start the market data service
echo "Starting market data service..."
python src/market_data_service.py > logs/market_data_service.log 2>&1 &
MARKET_DATA_PID=$!
echo "Market data service started with PID: $MARKET_DATA_PID"

# Start the trading strategy service
echo "Starting trading strategy service..."
python src/trading_strategy_service.py > logs/trading_strategy_service.log 2>&1 &
STRATEGY_PID=$!
echo "Trading strategy service started with PID: $STRATEGY_PID"

# Save PIDs to a file for easy shutdown
echo "$PORTFOLIO_PID $OPTIMIZER_PID $ORCHESTRATOR_PID $MARKET_DATA_PID $STRATEGY_PID" > .running_pids

echo "All services started successfully!"
echo "To stop all services, run: scripts/stop_system.sh"
echo "To view logs, check the logs directory"

# Create a stop script if it doesn't exist
if [ ! -f scripts/stop_system.sh ]; then
  cat > scripts/stop_system.sh << 'EOF'
#!/bin/bash
# Stop all running services

# Set the working directory to the project root
cd "$(dirname "$0")/.."

# Check if PID file exists
if [ -f .running_pids ]; then
  # Read PIDs from file
  PIDS=$(cat .running_pids)
  
  # Kill each process
  for PID in $PIDS; do
    if ps -p $PID > /dev/null; then
      echo "Stopping process with PID: $PID"
      kill $PID
    fi
  done
  
  # Remove PID file
  rm .running_pids
  echo "All services stopped"
else
  echo "No running services found"
fi
EOF
  chmod +x scripts/stop_system.sh
  echo "Created stop script: scripts/stop_system.sh"
fi