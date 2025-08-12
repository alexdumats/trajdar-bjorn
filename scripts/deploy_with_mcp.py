#!/usr/bin/env python3
"""
AI Trading System - MCP-Enabled Deployment Script
Uses Hetzner MCP server for cloud deployment automation
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_colored(message, color=Colors.NC):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")

class HetznerMCPDeployer:
    """Deployment manager using Hetzner MCP server"""
    
    def __init__(self, server_ip="135.181.164.232"):
        self.server_ip = server_ip
        self.project_root = Path(__file__).parent.parent
        self.deployment_path = "/opt/ai-trading-system"
        
    def check_mcp_server(self):
        """Check if Hetzner MCP server is available"""
        print_colored("🔍 Checking Hetzner MCP server availability...", Colors.BLUE)
        
        try:
            # Test if mcp_hetzner module is available
            import mcp_hetzner.server
            print_colored("✅ Hetzner MCP server is available", Colors.GREEN)
            return True
        except ImportError:
            print_colored("❌ Hetzner MCP server not found", Colors.RED)
            print_colored("Run: ./scripts/setup_hetzner_mcp.sh", Colors.YELLOW)
            return False
    
    def create_deployment_package(self):
        """Create deployment package"""
        print_colored("📦 Creating deployment package...", Colors.BLUE)
        
        # Files to include in deployment
        include_patterns = [
            "src/",
            "config/",
            "scripts/",
            "requirements.txt",
            "docker-compose.production.yml",
            "Dockerfile",
            "pytest.ini",
            ".env.production.template"
        ]
        
        # Files to exclude
        exclude_patterns = [
            ".git/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            "test_results/",
            "test_data/",
            "logs/*.log",
            ".DS_Store"
        ]
        
        deployment_info = {
            "project_name": "ai-trading-system",
            "version": "1.0.0",
            "deployment_time": subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip(),
            "server_ip": self.server_ip,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
        
        # Save deployment info
        with open(self.project_root / "deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print_colored("✅ Deployment package ready", Colors.GREEN)
        return deployment_info
    
    def prepare_environment(self):
        """Prepare environment configuration"""
        print_colored("⚙️ Preparing environment configuration...", Colors.BLUE)
        
        env_template = self.project_root / ".env.production.template"
        env_production = self.project_root / ".env"
        
        if not env_production.exists():
            print_colored("📋 Creating production environment file...", Colors.YELLOW)
            
            # Copy template
            subprocess.run(["cp", str(env_template), str(env_production)])
            
            # Update with server IP
            with open(env_production, "r") as f:
                content = f.read()
            
            content = content.replace("your.server.ip.here", self.server_ip)
            
            with open(env_production, "w") as f:
                f.write(content)
            
            print_colored("⚠️ Please edit .env file with your API tokens:", Colors.YELLOW)
            print_colored("  - SLACK_BOT_TOKEN", Colors.YELLOW)
            print_colored("  - HETZNER_API_TOKEN", Colors.YELLOW)
            print_colored("  - Other optional API keys", Colors.YELLOW)
            
            return False  # Need manual configuration
        
        print_colored("✅ Environment configuration ready", Colors.GREEN)
        return True
    
    def deploy_via_mcp(self):
        """Deploy using Hetzner MCP server capabilities"""
        print_colored("🚀 Starting MCP-based deployment...", Colors.CYAN)
        
        # This would use the actual MCP server when integrated with Claude Code
        # For now, we'll create the deployment structure
        
        deployment_commands = [
            {
                "action": "server_status",
                "description": "Check server status",
                "mcp_tool": "hetzner_server_info",
                "params": {"server_ip": self.server_ip}
            },
            {
                "action": "setup_environment", 
                "description": "Setup server environment",
                "commands": [
                    "apt-get update -y",
                    "apt-get install -y docker.io docker-compose git curl",
                    "systemctl start docker",
                    "systemctl enable docker",
                    "curl -fsSL https://ollama.ai/install.sh | sh",
                    "systemctl start ollama",
                    "ollama pull mistral",
                    "ollama pull phi3"
                ]
            },
            {
                "action": "deploy_application",
                "description": "Deploy AI trading system",
                "commands": [
                    f"mkdir -p {self.deployment_path}",
                    # File upload would happen here via MCP
                    f"cd {self.deployment_path}",
                    "docker-compose -f docker-compose.production.yml build",
                    "docker-compose -f docker-compose.production.yml up -d"
                ]
            },
            {
                "action": "verify_deployment",
                "description": "Verify deployment health",
                "health_checks": [
                    f"http://{self.server_ip}:8000/health",
                    f"http://{self.server_ip}:8001/health",
                    f"http://{self.server_ip}:8002/health"
                ]
            }
        ]
        
        # Save deployment plan
        with open(self.project_root / "deployment_plan.json", "w") as f:
            json.dump(deployment_commands, f, indent=2)
        
        print_colored("📋 Deployment plan created: deployment_plan.json", Colors.BLUE)
        print_colored("🎯 This plan will be executed via Hetzner MCP when integrated", Colors.YELLOW)
        
        return deployment_commands
    
    def create_monitoring_setup(self):
        """Create monitoring configuration"""
        print_colored("📊 Setting up monitoring configuration...", Colors.BLUE)
        
        monitoring_config = {
            "services": [
                {"name": "orchestrator", "port": 8000, "health_path": "/health"},
                {"name": "portfolio", "port": 8001, "health_path": "/health"},
                {"name": "risk_manager", "port": 8002, "health_path": "/health"},
                {"name": "market_analyst", "port": 8003, "health_path": "/health"},
                {"name": "notification", "port": 8004, "health_path": "/health"},
                {"name": "trade_executor", "port": 8005, "health_path": "/health"},
                {"name": "parameter_optimizer", "port": 8006, "health_path": "/health"}
            ],
            "monitoring": {
                "check_interval": 30,
                "alert_threshold": 3,
                "log_retention_days": 7
            },
            "alerts": {
                "slack_webhook": "${SLACK_WEBHOOK_URL}",
                "channels": ["trading-alerts", "system-alerts"]
            }
        }
        
        with open(self.project_root / "monitoring_config.json", "w") as f:
            json.dump(monitoring_config, f, indent=2)
        
        print_colored("✅ Monitoring configuration created", Colors.GREEN)
        
    def show_deployment_status(self):
        """Show deployment status and next steps"""
        print_colored("🎉 MCP Deployment Setup Complete!", Colors.GREEN)
        print_colored("═" * 50, Colors.CYAN)
        print()
        
        print_colored("📁 Files created:", Colors.BLUE)
        print(f"  • deployment_info.json - Deployment metadata")
        print(f"  • deployment_plan.json - MCP deployment commands")
        print(f"  • monitoring_config.json - Monitoring setup")
        print(f"  • .env - Production environment (if created)")
        print()
        
        print_colored("🔧 Next steps with Claude Code:", Colors.YELLOW)
        print("1. Ensure Hetzner MCP server is configured")
        print("2. Set your HETZNER_API_TOKEN in Claude Code settings")
        print("3. Use Claude Code to execute the deployment plan")
        print("4. Monitor deployment through MCP tools")
        print()
        
        print_colored("🖥️ Manual deployment alternative:", Colors.BLUE)
        print(f"./scripts/deploy_hetzner.sh setup")
        print(f"./scripts/deploy_hetzner.sh deploy")
        print()
        
        print_colored("📊 Service URLs (after deployment):", Colors.CYAN)
        print(f"  • Main Dashboard: http://{self.server_ip}:8000/system-status")
        print(f"  • Portfolio: http://{self.server_ip}:8001/portfolio")
        print(f"  • Health Checks: http://{self.server_ip}:8000/health")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy AI Trading System via MCP")
    parser.add_argument("--server-ip", default="135.181.164.232", 
                       help="Hetzner server IP address")
    parser.add_argument("--setup-only", action="store_true",
                       help="Only create deployment package, don't deploy")
    
    args = parser.parse_args()
    
    print_colored("🤖 AI Trading System - MCP Deployment", Colors.CYAN)
    print_colored("═" * 50, Colors.CYAN)
    
    deployer = HetznerMCPDeployer(args.server_ip)
    
    # Check MCP server availability
    if not deployer.check_mcp_server():
        print_colored("Please install Hetzner MCP server first:", Colors.YELLOW)
        print_colored("./scripts/setup_hetzner_mcp.sh", Colors.BLUE)
        return 1
    
    # Create deployment package
    deployer.create_deployment_package()
    
    # Prepare environment
    env_ready = deployer.prepare_environment()
    
    if not env_ready:
        print_colored("Please configure .env file before deployment", Colors.YELLOW)
        return 1
    
    if not args.setup_only:
        # Create deployment plan for MCP execution
        deployer.deploy_via_mcp()
        
        # Setup monitoring
        deployer.create_monitoring_setup()
    
    # Show status and next steps
    deployer.show_deployment_status()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())