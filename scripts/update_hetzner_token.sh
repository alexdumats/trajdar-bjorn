#!/bin/bash

# Update Hetzner API token in Claude Code MCP configuration
# Usage: ./scripts/update_hetzner_token.sh YOUR_HETZNER_API_TOKEN

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Updating Hetzner API Token in Claude Code MCP Configuration${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Check if token is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: Hetzner API token is required${NC}"
    echo "Usage: $0 YOUR_HETZNER_API_TOKEN"
    exit 1
fi

HETZNER_API_TOKEN="$1"

# Configuration file path
CONFIG_FILE="$HOME/.config/claude-code/mcp/claude_desktop_config.json"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️ Configuration file not found. Creating directory...${NC}"
    mkdir -p "$(dirname "$CONFIG_FILE")"
    
    # Create basic configuration
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "hetzner": {
      "command": "python",
      "args": ["-m", "mcp_hetzner.server"],
      "env": {
        "HETZNER_API_TOKEN": "your_hetzner_api_token_here"
      }
    },
    "sqlite": {
      "command": "python",
      "args": ["-m", "mcp_sqlite"],
      "env": {
        "SQLITE_DB_PATH": "./database/paper_trading.db"
      }
    }
  }
}
EOF
fi

# Update the token in the configuration file
echo -e "${BLUE}📝 Updating Hetzner API token...${NC}"

# Use sed to replace the token
sed -i.bak "s/\"HETZNER_API_TOKEN\": \"[^\"]*\"/\"HETZNER_API_TOKEN\": \"$HETZNER_API_TOKEN\"/" "$CONFIG_FILE"

# Check if the update was successful
if grep -q "$HETZNER_API_TOKEN" "$CONFIG_FILE"; then
    echo -e "${GREEN}✅ Hetzner API token updated successfully!${NC}"
    echo -e "${BLUE}📁 Config file: $CONFIG_FILE${NC}"
    
    # Remove backup file
    rm -f "$CONFIG_FILE.bak"
else
    echo -e "${RED}❌ Failed to update Hetzner API token${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    
    # Restore backup if it exists
    if [ -f "$CONFIG_FILE.bak" ]; then
        mv "$CONFIG_FILE.bak" "$CONFIG_FILE"
    fi
    
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Configuration updated!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "${BLUE}1. Restart Claude Code to load the new MCP server${NC}"
echo -e "${BLUE}2. You can now use Hetzner cloud features directly in Claude Code!${NC}"