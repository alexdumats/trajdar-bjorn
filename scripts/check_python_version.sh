#!/bin/bash

# Check Python version for Hetzner MCP compatibility
# The mcp-hetzner package requires Python 3.11 or higher

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Checking Python Version for Hetzner MCP Compatibility${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

# Check current Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${BLUE}Current Python version: $PYTHON_VERSION${NC}"

# Extract major.minor version numbers
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

# Check if version meets requirements (>= 3.11)
if [[ $PYTHON_MAJOR -gt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 11 ]]; then
    echo -e "${GREEN}✅ Python version is compatible with Hetzner MCP${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ Python version is not compatible with Hetzner MCP${NC}"
    echo -e "${RED}❌ Required: Python 3.11 or higher${NC}"
    echo -e "${BLUE}Current: Python $PYTHON_VERSION${NC}"
    echo ""
    
    # Check if pyenv is available for easy version switching
    if command -v pyenv &> /dev/null; then
        echo -e "${BLUE}🔧 pyenv detected - You can install Python 3.11:${NC}"
        echo -e "   pyenv install 3.11.0"
        echo -e "   pyenv global 3.11.0"
        echo ""
    fi
    
    # Provide installation instructions for different systems
    echo -e "${BLUE}🔧 Installation options:${NC}"
    
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo -e "${BLUE}macOS:${NC}"
        echo -e "  Option 1: Using Homebrew"
        echo -e "    brew install python@3.11"
        echo -e "    brew link python@3.11"
        echo -e ""
        echo -e "  Option 2: Using pyenv (recommended)"
        echo -e "    brew install pyenv"
        echo -e "    pyenv install 3.11.0"
        echo -e "    pyenv global 3.11.0"
        echo -e "    # Add to ~/.zshrc or ~/.bash_profile:"
        echo -e "    # export PATH=\"\$HOME/.pyenv/shims:\$PATH\""
        echo -e "    # eval \"\$(pyenv init -)\""
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo -e "${BLUE}Linux:${NC}"
        echo -e "  Ubuntu/Debian:"
        echo -e "    sudo apt update"
        echo -e "    sudo apt install software-properties-common"
        echo -e "    sudo add-apt-repository ppa:deadsnakes/ppa"
        echo -e "    sudo apt update"
        echo -e "    sudo apt install python3.11 python3.11-venv python3.11-dev"
        echo -e "    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1"
        echo -e ""
        echo -e "  Or using pyenv:"
        echo -e "    curl https://pyenv.run | bash"
        echo -e "    # Add pyenv to PATH in ~/.bashrc or ~/.zshrc"
        echo -e "    pyenv install 3.11.0"
        echo -e "    pyenv global 3.11.0"
    else
        echo -e "${BLUE}General:${NC}"
        echo -e "  Download from: https://www.python.org/downloads/"
        echo -e "  Or use pyenv: https://github.com/pyenv/pyenv"
    fi
    
    echo ""
    echo -e "${YELLOW}After installing Python 3.11+, run:${NC}"
    echo -e "  ./scripts/setup_hetzner_mcp.sh"
    echo ""
    
    exit 1
fi