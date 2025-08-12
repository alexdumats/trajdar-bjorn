#!/bin/bash

# Start Nova Workspace Slack MCP Server
# This script starts the Slack MCP server for local testing

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Nova Workspace Slack MCP Server${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if environment variables are set
if [[ -z "$SLACK_MCP_XOXP_TOKEN" ]]; then
    echo -e "${YELLOW}⚠️ Loading environment variables from .env file...${NC}"
    if [[ -f ".env" ]]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo -e "${RED}❌ .env file not found and SLACK_MCP_XOXP_TOKEN not set${NC}"
        exit 1
    fi
fi

# Verify Nova workspace configuration
echo -e "${BLUE}📋 Nova Workspace Configuration:${NC}"
echo -e "  Workspace: ${SLACK_NOVA_WORKSPACE:-nova-mir4286.slack.com}"
echo -e "  Team ID: ${SLACK_NOVA_TEAM_ID:-T096HMD0FDH}"
echo -e "  Target Channel: ${SLACK_NOVA_TARGET_CHANNEL:-C097REMKVK3}"
echo -e "  MCP Port: ${SLACK_MCP_PORT:-3001}"
echo ""

# Create cache directory
mkdir -p mcp-cache

# Check if Slack MCP server is already running
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Slack MCP server is already running on port 3001${NC}"
    echo -e "${YELLOW}   Stopping existing server...${NC}"
    docker stop ai-trading-slack-mcp 2>/dev/null || true
    docker rm ai-trading-slack-mcp 2>/dev/null || true
    sleep 2
fi

# Start Slack MCP server using Docker
echo -e "${BLUE}🐳 Starting Slack MCP server container...${NC}"

docker run -d \
    --name ai-trading-slack-mcp \
    --restart unless-stopped \
    -p 3001:3001 \
    -e SLACK_MCP_HOST=0.0.0.0 \
    -e SLACK_MCP_PORT=3001 \
    -e SLACK_MCP_LOG_LEVEL=info \
    -e SLACK_MCP_ADD_MESSAGE_TOOL=true \
    -e SLACK_MCP_XOXP_TOKEN="$SLACK_MCP_XOXP_TOKEN" \
    -e SLACK_MCP_USERS_CACHE=/app/.users_cache.json \
    -e SLACK_MCP_CHANNELS_CACHE=/app/.channels_cache_v2.json \
    -v "$PROJECT_ROOT/mcp-cache:/app/cache" \
    -v "$PROJECT_ROOT/logs:/app/logs" \
    ghcr.io/korotovsky/slack-mcp-server:latest

# Wait for server to start
echo -e "${YELLOW}⏳ Waiting for Slack MCP server to start...${NC}"
sleep 10

# Check if server is healthy
max_attempts=30
attempt=0

while [[ $attempt -lt $max_attempts ]]; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Slack MCP server is running and healthy!${NC}"
        break
    fi
    
    echo -e "${YELLOW}   Attempt $((attempt + 1))/$max_attempts - waiting...${NC}"
    sleep 2
    ((attempt++))
done

if [[ $attempt -eq $max_attempts ]]; then
    echo -e "${RED}❌ Slack MCP server failed to start properly${NC}"
    echo -e "${RED}   Checking container logs:${NC}"
    docker logs ai-trading-slack-mcp --tail=20
    exit 1
fi

# Show server status
echo -e "${BLUE}📊 Server Status:${NC}"
echo -e "  Health Check: $(curl -s http://localhost:3001/health | jq -r '.status // "Unknown"' 2>/dev/null || echo 'Unknown')"
echo -e "  Container: $(docker ps --filter name=ai-trading-slack-mcp --format 'table {{.Status}}')"
echo ""

# Show next steps
echo -e "${GREEN}🎉 Nova Workspace Slack MCP Server Started Successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "  1. Test the integration: ${YELLOW}python3 scripts/test_nova_slack_mcp.py${NC}"
echo -e "  2. View server logs: ${YELLOW}docker logs ai-trading-slack-mcp -f${NC}"
echo -e "  3. Stop the server: ${YELLOW}docker stop ai-trading-slack-mcp${NC}"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo -e "  Health Check: http://localhost:3001/health"
echo -e "  Nova Workspace: https://nova-mir4286.slack.com"
echo -e "  Target Channel: https://nova-mir4286.slack.com/archives/C097REMKVK3"