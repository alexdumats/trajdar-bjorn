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
