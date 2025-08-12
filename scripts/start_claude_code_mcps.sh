#!/bin/bash
# Script to start all Claude Code MCP servers using Docker Compose

set -e

echo "Starting Claude Code MCP servers..."
echo "-----------------------------------"

# Create data directory if it doesn't exist
mkdir -p ./mcp-data
mkdir -p ./mcp-data/git

# Start all MCP servers using Docker Compose
docker-compose -f docker-compose.claude-code-mcps.yml up -d

echo "-----------------------------------"
echo "All MCP servers started successfully!"
echo ""
echo "MCP servers are running on the following ports:"
echo "- Fetch MCP Server: http://localhost:3001"
echo "- Filesystem MCP Server: http://localhost:3002"
echo "- Memory MCP Server: http://localhost:3003"
echo "- Git MCP Server: http://localhost:3004"
echo "- Sequential Thinking MCP Server: http://localhost:3005"
echo "- Time MCP Server: http://localhost:3006"
echo "- Context7 Documentation Server: http://localhost:3007"
echo ""
echo "To stop all MCP servers, run:"
echo "docker-compose -f docker-compose.claude-code-mcps.yml down"
echo ""
echo "To view logs for all MCP servers, run:"
echo "docker-compose -f docker-compose.claude-code-mcps.yml logs -f"
echo ""
echo "To update the Claude Code configuration to use these servers,"
echo "edit your Claude settings to use the HTTP transport instead of stdio,"
echo "and update the URLs to point to the local ports above."