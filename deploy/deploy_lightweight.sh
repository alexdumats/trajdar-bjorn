#!/bin/bash
set -e

echo "🚀 Deploying Lightweight AI Trading System to 135.181.164.232"
echo "📊 Optimized for resource constraints - using external MCP servers only"

# Variables
SERVER_IP="135.181.164.232"
SERVER_USER="root"
PROJECT_DIR="/opt/ai-trading-system"

# Function to run commands on remote server
run_remote() {
    sshpass -p 'CQGT8hcWLZCV8G' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "$@"
}

# Function to copy files to remote server
copy_to_remote() {
    sshpass -p 'CQGT8hcWLZCV8G' scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -r "$1" $SERVER_USER@$SERVER_IP:"$2"
}

echo "📦 Copying optimized configuration files..."
copy_to_remote "config/mcp_servers_optimized.yaml" "$PROJECT_DIR/config/"
copy_to_remote "config/lightweight_trading_config.yaml" "$PROJECT_DIR/config/"
copy_to_remote "docker-compose.production.yml" "$PROJECT_DIR/"
copy_to_remote ".env.production" "$PROJECT_DIR/"

echo "🔄 Restarting with lightweight configuration..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml down"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml up -d"

echo "⏳ Waiting for optimized services to start..."
sleep 20

echo "🔍 Checking optimized system status..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml ps"

echo "🌐 Testing optimized system health..."
echo "Orchestrator:"
run_remote "curl -s http://localhost:8000/health || echo 'Starting...'"

echo "MCP Hub (lightweight):"
run_remote "curl -s http://localhost:9000/health || echo 'Starting...'"

echo "📊 Checking resource usage..."
run_remote "docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'"

echo "✅ Lightweight deployment complete!"
echo "🌐 System: http://$SERVER_IP:8000"
echo "📊 MCP Hub: http://$SERVER_IP:9000"
echo ""
echo "💡 Optimizations applied:"
echo "  - Only 4 essential MCP servers (was 16+)"
echo "  - External APIs instead of local processing"
echo "  - Reduced logging and health checks"
echo "  - Simplified trading logic"
echo "  - Memory and CPU limits applied"