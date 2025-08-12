#!/bin/bash
# Setup script for Claude Code MCP servers
# This script installs and configures the recommended MCP servers for Claude Code

set -e

echo "Setting up MCP servers for Claude Code..."
echo "----------------------------------------"

# Create directory for MCP server data if it doesn't exist
mkdir -p ./mcp-data

# Install Node.js packages for MCP servers
echo "Installing Node.js MCP servers..."
npm install -g @modelcontextprotocol/server-fetch
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-sequential-thinking
npm install -g @upstash/context7-mcp

# Install Python packages for MCP servers
echo "Installing Python MCP servers..."
pip install mcp-server-time

# Create .env file for MCP server configuration if it doesn't exist
if [ ! -f .env.mcp ]; then
  echo "Creating .env.mcp file..."
  cat > .env.mcp << EOF
# MCP Server Environment Variables
MCP_LOG_LEVEL=INFO
MCP_TIMEOUT=30

# Filesystem MCP Server
ALLOWED_DIRECTORIES=$(pwd)
EOF
  echo ".env.mcp file created"
else
  echo ".env.mcp file already exists"
fi

echo "----------------------------------------"
echo "MCP servers setup complete!"
echo ""
echo "To use these MCP servers with Claude Code:"
echo "1. Add the configuration from config/claude_code_mcp_servers.yaml to your Claude settings"
echo "2. Make sure to set the correct environment variables in your .env.mcp file"
echo "3. Start using the enhanced capabilities in your Claude Code sessions"
echo ""
echo "For more information, see the documentation for each MCP server:"
echo "- Fetch: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch"
echo "- Filesystem: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"
echo "- Memory: https://github.com/modelcontextprotocol/servers/tree/main/src/memory"
echo "- Git: https://github.com/modelcontextprotocol/servers/tree/main/src/git"
echo "- SequentialThinking: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"
echo "- Time: https://github.com/modelcontextprotocol/servers/tree/main/src/time"
echo "- Context7: https://github.com/upstash/context7-mcp"