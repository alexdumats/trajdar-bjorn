#!/bin/bash
set -e

echo "🚀 Starting AI Trading System deployment to 91.99.103.119"

# Variables
SERVER_IP="91.99.103.119"
PROJECT_DIR="/opt/ai-trading-system"

# Function to run commands on remote server
run_remote() {
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 trading@$SERVER_IP "$@"
}

# Function to copy files to remote server
copy_to_remote() {
    scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -r "$1" trading@$SERVER_IP:"$2"
}

echo "🔄 Testing connection to server..."
if ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 trading@$SERVER_IP "echo 'Connection successful'"; then
    echo "❌ Cannot connect to server. Please check:"
    echo "   1. Server is running"
    echo "   2. SSH key is properly configured"
    echo "   3. Firewall allows SSH (port 22)"
    exit 1
fi

echo "📂 Preparing project directory..."
run_remote "sudo mkdir -p $PROJECT_DIR && sudo chown trading:trading $PROJECT_DIR"

echo "📦 Copying project files..."
copy_to_remote "." "$PROJECT_DIR/"

echo "🔑 Setting up environment variables..."
copy_to_remote ".env.production" "$PROJECT_DIR/.env.production"

echo "🐳 Building and starting Docker containers..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml pull || true"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml build"
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml up -d"

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service health..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml ps"

echo "🌐 Testing system endpoints..."
if run_remote "curl -f http://localhost:8000/health"; then
    echo "✅ Orchestrator is healthy"
else
    echo "⚠️ Orchestrator not ready yet"
fi

if run_remote "curl -f http://localhost:9000/health"; then
    echo "✅ MCP Hub is healthy"
else
    echo "⚠️ MCP Hub not ready yet"
fi

echo "✅ Deployment complete!"
echo "🌐 Access your trading system at: http://$SERVER_IP:8000"
echo "📊 MCP Hub available at: http://$SERVER_IP:9000"
echo "📱 Slack notifications should now be active"

echo "🎉 AI Trading System is now running in production!"
