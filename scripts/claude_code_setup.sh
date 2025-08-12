#!/bin/bash

# Claude Code Setup for AI Trading System
# Configures Claude Code for optimal use with the modular agent architecture

echo "🤖 Setting up Claude Code for AI Trading System"
echo "================================================"

# Set project-specific configurations
echo "📁 Setting up project workspace..."

# Allow specific tools for trading system development
claude config set allowedTools "Bash,Edit,Read,Glob,Grep,Write,MultiEdit,LS,WebFetch"

echo "✅ Claude Code tools configured for trading system development"

# Create a Claude Code project configuration
cat > .claude-project.json << 'EOF'
{
  "name": "AI Trading System",
  "description": "Modular agent-based trading system with Ollama integration",
  "version": "3.0.0",
  "allowedTools": [
    "Bash",
    "Edit", 
    "Read",
    "Glob",
    "Grep",
    "Write",
    "MultiEdit",
    "LS",
    "WebFetch"
  ],
  "directories": {
    "src": "AI agent services and utilities",
    "config": "Agent configurations and MCP settings",
    "scripts": "Management and deployment scripts",
    "database": "Trading database",
    "logs": "System logs"
  },
  "key_components": {
    "agents": [
      "src/signal_service.py - Risk Manager (mistral7b)",
      "src/data_service.py - Market/News Analyst (mistral7b)",
      "src/market_executor_service.py - Trade Executor (phi3)",
      "src/parameter_optimizer_service.py - Parameter Optimizer"
    ],
    "orchestration": "src/orchestrator_service.py",
    "deployment": "docker-compose.agents.yml"
  }
}
EOF

echo "📝 Created .claude-project.json with project structure"

# Create helpful Claude Code aliases
cat > .claude-shortcuts.md << 'EOF'
# Claude Code Shortcuts for AI Trading System

## Quick Commands

### System Management
- `claude "Start the agent system"` - Analyze and start all agents
- `claude "Check agent health"` - Monitor system status
- `claude "Review agent logs"` - Examine recent log files

### Development  
- `claude "Analyze agent architecture"` - Review current system design
- `claude "Debug agent issues"` - Troubleshoot problems
- `claude "Update agent configuration"` - Modify configurations

### MCP Integration
- `claude "Show MCP assignments"` - Display agent-specific MCP servers
- `claude "Add new MCP server"` - Configure additional MCP servers

## Example Usage

```bash
# Interactive session for system development
claude 

# Quick system status check
claude -p "Show me the current status of all AI agents"

# Analyze specific agent
claude -p "Review the Trade Executor agent configuration"
```

## Project Context

Claude Code is configured with access to:
- Source code in src/ (all AI agents)  
- Configuration files in config/
- Management scripts in scripts/
- System logs and database

The AI agents use:
- Risk Manager: mistral7b:latest
- Market/News Analyst: mistral7b:latest  
- Trade Executor: phi3
- Parameter Optimizer: Python (no LLM)
EOF

echo "📚 Created .claude-shortcuts.md with helpful commands"

# Show current configuration
echo ""
echo "🔧 Current Claude Code Configuration:"
claude config list

echo ""
echo "✅ Claude Code setup complete!"
echo ""
echo "🚀 Next steps:"
echo "  1. Start an interactive session: claude"
echo "  2. Quick system check: claude -p 'Check agent system health'"
echo "  3. Review shortcuts: cat .claude-shortcuts.md"
echo ""
echo "💡 Claude Code can now assist with:"
echo "  - Agent development and debugging"
echo "  - Configuration management"  
echo "  - System monitoring and analysis"
echo "  - MCP server integration"