#!/usr/bin/env python3
"""
Agent MCP Configuration Script
Configures MCP servers for each AI agent based on their specific roles and requirements
"""

import yaml
import os
import json
from pathlib import Path

def load_agent_mcp_config():
    """Load agent-specific MCP configuration"""
    config_path = Path(__file__).parent.parent / "config" / "mcp_servers_agents.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_agent_mcp_configs(output_dir: str = None):
    """Create individual MCP configuration files for each agent"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "config" / "agent_mcps"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    config = load_agent_mcp_config()
    
    # Process each agent configuration
    for agent_name, agent_config in config['agent_configurations'].items():
        print(f"📝 Creating MCP configuration for {agent_config['name']}")
        
        # Create agent-specific MCP configuration
        agent_mcp_config = {
            "agent_name": agent_name,
            "agent_description": agent_config['description'],
            "model": agent_config['model'],
            "servers": agent_config['mcp_servers']
        }
        
        # Add shared services that this agent might use
        if 'shared_services' in config:
            agent_mcp_config["shared_services"] = config['shared_services']
        
        # Add environment variables
        if 'environment_variables' in config:
            agent_mcp_config["environment_variables"] = config['environment_variables']
        
        # Write agent-specific configuration file
        output_file = output_dir / f"{agent_name}_mcps.yaml"
        with open(output_file, 'w') as f:
            yaml.dump(agent_mcp_config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Created: {output_file}")
    
    # Create master agent mapping file
    agent_mapping = {
        "agent_mcp_assignments": {
            agent_name: {
                "config_file": f"{agent_name}_mcps.yaml",
                "model": agent_config['model'],
                "description": agent_config['description'],
                "mcp_count": len(agent_config['mcp_servers'])
            }
            for agent_name, agent_config in config['agent_configurations'].items()
        }
    }
    
    mapping_file = output_dir / "agent_mcp_mapping.yaml"
    with open(mapping_file, 'w') as f:
        yaml.dump(agent_mapping, f, default_flow_style=False, indent=2)
    
    print(f"✅ Created agent mapping: {mapping_file}")
    return output_dir

def validate_mcp_assignments():
    """Validate that MCP assignments make sense for each agent"""
    config = load_agent_mcp_config()
    
    print("🔍 Validating MCP assignments...")
    
    validation_results = {}
    
    for agent_name, agent_config in config['agent_configurations'].items():
        agent_mcps = list(agent_config['mcp_servers'].keys())
        model = agent_config['model']
        
        validation_results[agent_name] = {
            "model": model,
            "mcp_count": len(agent_mcps),
            "mcps": agent_mcps,
            "valid": True,
            "warnings": []
        }
        
        # Validate Risk Manager
        if agent_name == "risk_manager":
            expected_mcps = ["sqlite", "phoenix"]  # Database and monitoring
            for expected in expected_mcps:
                if expected not in agent_mcps:
                    validation_results[agent_name]["warnings"].append(f"Missing expected MCP: {expected}")
        
        # Validate Market/News Analyst
        elif agent_name == "market_news_analyst":
            expected_mcps = ["yfinance", "coinpaprika", "fred"]  # Market and economic data
            for expected in expected_mcps:
                if expected not in agent_mcps:
                    validation_results[agent_name]["warnings"].append(f"Missing expected MCP: {expected}")
        
        # Validate Trade Executor
        elif agent_name == "trade_executor":
            expected_mcps = ["trade_agent"]  # Trading execution
            for expected in expected_mcps:
                if expected not in agent_mcps:
                    validation_results[agent_name]["warnings"].append(f"Missing expected MCP: {expected}")
        
        # Validate Parameter Optimizer
        elif agent_name == "parameter_optimizer":
            expected_mcps = ["optuna"]  # Optimization
            for expected in expected_mcps:
                if expected not in agent_mcps:
                    validation_results[agent_name]["warnings"].append(f"Missing expected MCP: {expected}")
        
        # Check for model compatibility
        if model == "phi3" and agent_name != "trade_executor":
            validation_results[agent_name]["warnings"].append("phi3 model should only be used by trade_executor")
        elif model == "mistral7b:latest" and agent_name in ["parameter_optimizer"]:
            validation_results[agent_name]["warnings"].append("Parameter optimizer should not use LLM model")
    
    # Print validation results
    for agent_name, results in validation_results.items():
        print(f"\n📊 {agent_name.upper()}:")
        print(f"  Model: {results['model']}")
        print(f"  MCPs: {results['mcp_count']} configured")
        
        if results['warnings']:
            print(f"  ⚠️  Warnings:")
            for warning in results['warnings']:
                print(f"    - {warning}")
        else:
            print(f"  ✅ Configuration looks good")
    
    return validation_results

def generate_startup_commands():
    """Generate startup commands for each agent with their MCP configurations"""
    config = load_agent_mcp_config()
    
    commands = []
    
    for agent_name, agent_config in config['agent_configurations'].items():
        service_name = agent_name.replace('_', '-')
        
        if agent_name == "risk_manager":
            port = 8002
            service_file = "signal_service.py"  # Transformed to Risk Manager
        elif agent_name == "market_news_analyst":
            port = 8003
            service_file = "data_service.py"  # Transformed to Market/News Analyst
        elif agent_name == "trade_executor":
            port = 8005
            service_file = "market_executor_service.py"  # Transformed to Trade Executor
        elif agent_name == "parameter_optimizer":
            port = 8006
            service_file = "parameter_optimizer_service.py"
        else:
            continue
        
        # Create startup command
        cmd = f"""# Start {agent_config['name']}
export MCP_CONFIG_FILE=config/agent_mcps/{agent_name}_mcps.yaml
export SERVICE_PORT={port}
python src/{service_file}"""
        
        commands.append(cmd)
    
    return "\\n\\n".join(commands)

if __name__ == "__main__":
    print("🤖 Agent MCP Configuration Tool")
    print("=" * 50)
    
    # Create agent-specific MCP configurations
    output_dir = create_agent_mcp_configs()
    
    print("\\n" + "=" * 50)
    
    # Validate configurations
    validation_results = validate_mcp_assignments()
    
    print("\\n" + "=" * 50)
    
    # Generate startup commands
    startup_commands = generate_startup_commands()
    
    print("\\n🚀 Agent Startup Commands:")
    print(startup_commands)
    
    # Save startup commands to file
    commands_file = output_dir / "agent_startup_commands.sh"
    with open(commands_file, 'w') as f:
        f.write(f"#!/bin/bash\\n# Agent Startup Commands\\n# Generated by configure_agent_mcps.py\\n\\n")
        f.write(startup_commands.replace("\\n", "\\n"))
    
    print(f"\\n✅ Startup commands saved to: {commands_file}")
    print(f"\\n📁 All agent configurations saved to: {output_dir}")