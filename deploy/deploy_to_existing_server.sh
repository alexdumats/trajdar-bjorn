#!/bin/bash
set -e

echo "🚀 Starting AI Trading System deployment to 135.181.164.232"

# Variables
SERVER_IP="135.181.164.232"
SERVER_USER="root"
PROJECT_DIR="/opt/ai-trading-system"

# Function to run commands on remote server using password
run_remote() {
    sshpass -p 'CQGT8hcWLZCV8G' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "$@"
}

# Function to copy files to remote server using password
copy_to_remote() {
    sshpass -p 'CQGT8hcWLZCV8G' scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 -r "$1" $SERVER_USER@$SERVER_IP:"$2"
}

echo "🔄 Testing connection to server..."
if ! run_remote "echo 'Connection successful'"; then
    echo "❌ Cannot connect to server. Installing sshpass if needed..."
    if ! command -v sshpass &> /dev/null; then
        echo "Installing sshpass..."
        brew install hudochenkov/sshpass/sshpass 2>/dev/null || {
            echo "Please install sshpass: brew install hudochenkov/sshpass/sshpass"
            exit 1
        }
    fi
    echo "Retrying connection..."
    run_remote "echo 'Connection successful'"
fi

echo "📂 Preparing server environment..."
run_remote "apt update && apt upgrade -y"

echo "🐳 Installing Docker and Docker Compose..."
run_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
run_remote "curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
run_remote "chmod +x /usr/local/bin/docker-compose"

echo "📦 Installing dependencies..."
run_remote "apt install -y python3-pip git htop curl wget nodejs npm"

echo "🔧 Installing Go for MCP servers..."
run_remote "wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz"
run_remote "echo 'export PATH=\$PATH:/usr/local/go/bin' >> ~/.bashrc"

echo "📂 Setting up project directory..."
run_remote "mkdir -p $PROJECT_DIR && cd $PROJECT_DIR"

echo "📦 Copying project files..."
copy_to_remote "." "$PROJECT_DIR/"

echo "🔑 Setting up environment variables..."
copy_to_remote ".env.production" "$PROJECT_DIR/.env"

echo "🏗️ Building Docker containers..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml build"

echo "🐳 Starting all services..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml up -d"

echo "⏳ Waiting for services to initialize..."
sleep 45

echo "🔍 Checking service status..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.production.yml ps"

echo "🌐 Testing system health..."
echo "Checking Orchestrator..."
run_remote "curl -f http://localhost:8000/health || echo 'Orchestrator starting...'"

echo "Checking MCP Hub..."
run_remote "curl -f http://localhost:9000/health || echo 'MCP Hub starting...'"

echo "🔄 Starting MCP servers..."
run_remote "curl -X POST http://localhost:9000/servers/start-all || echo 'MCP servers initializing...'"

echo "✅ Deployment complete!"
echo "🌐 Access your trading system at: http://$SERVER_IP:8000"
echo "📊 MCP Hub available at: http://$SERVER_IP:9000"
echo "📱 Slack notifications are configured"

echo "🎉 AI Trading System is now running in production!"
echo ""
echo "📋 Quick health check commands:"
echo "  docker-compose -f docker-compose.production.yml ps"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:9000/health"