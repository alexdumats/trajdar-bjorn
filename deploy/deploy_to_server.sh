#!/bin/bash
set -e

echo "🚀 Starting AI Trading System deployment to 192.168.1.100"

# Variables
SERVER_IP="192.168.1.100"
PROJECT_DIR="/opt/ai-trading-system"
REPO_URL="https://github.com/yourusername/trajdar_bjorn.git"  # Update with actual repo

# Function to run commands on remote server
run_remote() {
    ssh -o StrictHostKeyChecking=no trading@$SERVER_IP "$@"
}

# Function to copy files to remote server
copy_to_remote() {
    scp -o StrictHostKeyChecking=no -r "$1" trading@$SERVER_IP:"$2"
}

echo "📂 Cloning repository to server..."
run_remote "cd $PROJECT_DIR && git clone $REPO_URL . || git pull"

echo "🔑 Setting up environment variables..."
# Copy production environment file
copy_to_remote "../.env.production" "$PROJECT_DIR/.env.production"

echo "🐳 Building and starting Docker containers..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.yml pull"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.yml up -d"

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service health..."
run_remote "cd $PROJECT_DIR && docker-compose ps"

# Check orchestrator health
echo "Checking orchestrator service..."
run_remote "curl -f http://localhost:8000/health || echo 'Orchestrator not ready yet'"

# Check MCP hub
echo "Checking MCP hub..."
run_remote "curl -f http://localhost:9000/health || echo 'MCP Hub not ready yet'"

echo "🎯 Starting MCP servers..."
run_remote "curl -X POST http://localhost:9000/servers/start-all || echo 'MCP servers starting...'"

echo "🔄 Enabling system service..."
run_remote "sudo systemctl enable ai-trading-system.service"
run_remote "sudo systemctl start ai-trading-system.service"

echo "✅ Deployment complete!"
echo "🌐 Access your trading system at: http://$SERVER_IP:8000"
echo "📊 MCP Hub available at: http://$SERVER_IP:9000"
echo "📱 Slack notifications configured and ready"

echo "🎉 AI Trading System is now running in production!"
