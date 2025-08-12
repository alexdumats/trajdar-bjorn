#!/bin/bash

# Deploy Nova Workspace Slack MCP to Hetzner Server
# Integrates Slack MCP server with the existing AI trading system

set -e

# Configuration
SERVER_IP="135.181.164.232"
DEPLOYMENT_USER="root"
PROJECT_PATH="/opt/ai-trading-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Nova Workspace Slack MCP to Hetzner Server${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

# Test SSH connection
echo -e "${BLUE}🔍 Testing SSH connection to Hetzner server...${NC}"
if ! ssh -o ConnectTimeout=10 "$DEPLOYMENT_USER@$SERVER_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed to $SERVER_IP${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Deploy updated configuration files
echo -e "${BLUE}📤 Deploying updated configuration files...${NC}"

# Copy updated environment files
scp .env.production "$DEPLOYMENT_USER@$SERVER_IP:$PROJECT_PATH/"
scp mcp-servers/slack/.env "$DEPLOYMENT_USER@$SERVER_IP:$PROJECT_PATH/mcp-servers/slack/"

# Copy updated Docker Compose file
scp docker-compose.production.yml "$DEPLOYMENT_USER@$SERVER_IP:$PROJECT_PATH/"

# Copy updated MCP configuration
scp config/mcp_servers.yaml "$DEPLOYMENT_USER@$SERVER_IP:$PROJECT_PATH/config/"

echo -e "${GREEN}✅ Configuration files deployed${NC}"

# Deploy and start Slack MCP server
echo -e "${BLUE}🐳 Deploying Slack MCP server on Hetzner...${NC}"

ssh "$DEPLOYMENT_USER@$SERVER_IP" << 'EOF'
cd /opt/ai-trading-system

echo "🔄 Updating Docker Compose setup..."

# Create cache directory for MCP
mkdir -p mcp-cache

# Pull latest Slack MCP server image
echo "📥 Pulling Slack MCP server image..."
docker pull ghcr.io/korotovsky/slack-mcp-server:latest

# Stop existing services if running
echo "⏹️ Stopping existing services..."
docker-compose -f docker-compose.production.yml stop slack-mcp 2>/dev/null || true
docker-compose -f docker-compose.production.yml stop mcp-hub 2>/dev/null || true

# Start Slack MCP server
echo "🚀 Starting Slack MCP server..."
docker-compose -f docker-compose.production.yml up -d slack-mcp

# Wait for Slack MCP to be ready
echo "⏳ Waiting for Slack MCP server to start..."
sleep 15

# Check Slack MCP health
max_attempts=30
attempt=0

while [[ $attempt -lt $max_attempts ]]; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo "✅ Slack MCP server is healthy!"
        break
    fi
    
    echo "   Attempt $((attempt + 1))/$max_attempts - waiting..."
    sleep 2
    ((attempt++))
done

if [[ $attempt -eq $max_attempts ]]; then
    echo "❌ Slack MCP server failed to start"
    docker-compose -f docker-compose.production.yml logs slack-mcp --tail=20
    exit 1
fi

# Start MCP Hub (depends on Slack MCP)
echo "🚀 Starting MCP Hub..."
docker-compose -f docker-compose.production.yml up -d mcp-hub

# Wait for MCP Hub to be ready
echo "⏳ Waiting for MCP Hub to start..."
sleep 10

# Check MCP Hub health
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "✅ MCP Hub is healthy!"
else
    echo "⚠️ MCP Hub may not be fully ready yet"
fi

# Show service status
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps slack-mcp mcp-hub

echo "✅ Nova Workspace Slack MCP deployment complete!"
EOF

# Test the deployment
echo -e "${BLUE}🧪 Testing Nova Workspace integration...${NC}"

ssh "$DEPLOYMENT_USER@$SERVER_IP" << 'EOF'
cd /opt/ai-trading-system

echo "🔍 Testing Slack MCP server endpoints..."

# Test health endpoint
echo "1. Health Check:"
curl -s http://localhost:3001/health | jq . || echo "Health check failed"

# Test MCP Hub integration
echo "2. MCP Hub Integration:"
curl -s http://localhost:9000/servers/slack | jq . || echo "MCP Hub integration test failed"

echo "3. Container Status:"
docker-compose -f docker-compose.production.yml ps slack-mcp mcp-hub

echo "4. Recent Logs:"
echo "--- Slack MCP Logs ---"
docker-compose -f docker-compose.production.yml logs slack-mcp --tail=5

echo "--- MCP Hub Logs ---"
docker-compose -f docker-compose.production.yml logs mcp-hub --tail=5
EOF

echo -e "${GREEN}🎉 Nova Workspace Slack MCP Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo -e "  Server: $SERVER_IP"
echo -e "  Workspace: nova-mir4286.slack.com"
echo -e "  Target Channel: C097REMKVK3"
echo -e "  Slack MCP Port: 3001"
echo -e "  MCP Hub Port: 9000"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo -e "  Slack MCP Health: http://$SERVER_IP:3001/health"
echo -e "  MCP Hub Status: http://$SERVER_IP:9000/status"
echo -e "  Nova Workspace: https://nova-mir4286.slack.com/archives/C097REMKVK3"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "  1. Test message sending to Nova workspace"
echo -e "  2. Verify trading alerts are delivered"
echo -e "  3. Monitor logs for any issues"
echo -e "  4. Update service integrations to use Slack MCP"