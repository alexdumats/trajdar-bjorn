#!/bin/bash

# Setup Hetzner MCP Server for Claude Code Integration
# This enables direct cloud deployment from Claude Code

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🔧 Setting up Hetzner MCP Server for Claude Code${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Install Hetzner MCP server
echo -e "${BLUE}📦 Installing Hetzner MCP server...${NC}"
pip install git+https://github.com/dkruyt/mcp-hetzner.git

# Create configuration directory if it doesn't exist
mkdir -p ~/.config/claude-code/mcp

# Create Claude Code MCP configuration
echo -e "${BLUE}⚙️ Creating Claude Code MCP configuration...${NC}"

cat > ~/.config/claude-code/mcp/claude_desktop_config.json << 'EOF'
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

echo -e "${YELLOW}⚠️ IMPORTANT: Update your Hetzner API token${NC}"
echo -e "${BLUE}1. Go to Hetzner Cloud Console: https://console.hetzner.cloud${NC}"
echo -e "${BLUE}2. Go to 'Security' → 'API Tokens'${NC}"
echo -e "${BLUE}3. Generate a new token with 'Read & Write' permissions${NC}"
echo -e "${BLUE}4. Edit the config file and replace 'your_hetzner_api_token_here'${NC}"
echo ""
echo -e "${YELLOW}Config file location: ~/.config/claude-code/mcp/claude_desktop_config.json${NC}"

# Test the installation
echo -e "${BLUE}🧪 Testing Hetzner MCP server installation...${NC}"

python3 -c "
try:
    import mcp_hetzner.server
    print('✅ Hetzner MCP server installed successfully')
except ImportError as e:
    print(f'❌ Installation failed: {e}')
    exit(1)
"

echo -e "${GREEN}✅ Hetzner MCP server setup complete!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo -e "${BLUE}1. Add your Hetzner API token to the config file${NC}"
echo -e "${BLUE}2. Restart Claude Code to load the new MCP server${NC}"
echo -e "${BLUE}3. You can now use Hetzner cloud features directly in Claude Code!${NC}"

echo ""
echo -e "${CYAN}Available Hetzner MCP capabilities:${NC}"
echo -e "  • Server management (create, delete, power operations)"
echo -e "  • Network configuration"
echo -e "  • Volume management"
echo -e "  • Firewall configuration"
echo -e "  • Resource monitoring"
echo -e "  • Deployment automation"