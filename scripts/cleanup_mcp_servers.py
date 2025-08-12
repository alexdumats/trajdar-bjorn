#!/usr/bin/env python3
"""
MCP Server Cleanup Script
Removes unnecessary MCP servers and creates a clean configuration for agent-based architecture
"""

import yaml
import os
from pathlib import Path
import shutil
from datetime import datetime

def load_original_config():
    """Load original MCP configuration"""
    config_path = Path(__file__).parent.parent / "config" / "mcp_servers.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_clean_config():
    """Load clean MCP configuration"""
    config_path = Path(__file__).parent.parent / "config" / "mcp_servers_clean.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def compare_configurations():
    """Compare original and clean configurations"""
    original = load_original_config()
    clean = load_clean_config()
    
    original_servers = set(original['servers'].keys())
    clean_servers = set(clean['servers'].keys())
    
    removed_servers = original_servers - clean_servers
    kept_servers = original_servers & clean_servers
    
    print("🧹 MCP Server Cleanup Analysis")
    print("=" * 50)
    
    print(f"📊 Original servers: {len(original_servers)}")
    print(f"📊 Clean servers: {len(clean_servers)}")
    print(f"📊 Removed servers: {len(removed_servers)}")
    
    print("\\n✅ KEPT SERVERS (needed by agents):")
    for server in sorted(kept_servers):
        description = original['servers'][server].get('description', 'No description')
        print(f"  - {server}: {description}")
    
    print("\\n❌ REMOVED SERVERS (unnecessary):")
    for server in sorted(removed_servers):
        description = original['servers'][server].get('description', 'No description')
        print(f"  - {server}: {description}")
    
    return {
        'original_count': len(original_servers),
        'clean_count': len(clean_servers),
        'removed_count': len(removed_servers),
        'removed_servers': list(removed_servers),
        'kept_servers': list(kept_servers)
    }

def backup_original_config():
    """Create backup of original configuration"""
    config_dir = Path(__file__).parent.parent / "config"
    original_path = config_dir / "mcp_servers.yaml"
    backup_path = config_dir / f"mcp_servers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    
    shutil.copy2(original_path, backup_path)
    print(f"💾 Backup created: {backup_path}")
    return backup_path

def apply_clean_configuration():
    """Replace original configuration with clean version"""
    config_dir = Path(__file__).parent.parent / "config"
    original_path = config_dir / "mcp_servers.yaml"
    clean_path = config_dir / "mcp_servers_clean.yaml"
    
    # Create backup first
    backup_path = backup_original_config()
    
    # Replace original with clean configuration
    shutil.copy2(clean_path, original_path)
    
    print(f"✅ Applied clean configuration to {original_path}")
    print(f"💾 Original backed up to {backup_path}")
    
    return True

def verify_agent_requirements():
    """Verify that clean configuration meets agent requirements"""
    clean_config = load_clean_config()
    servers = set(clean_config['servers'].keys())
    
    # Check agent requirements
    requirements = {
        'Risk Manager': {'required': ['sqlite', 'phoenix'], 'optional': ['slack']},
        'Market/News Analyst': {'required': ['yfinance', 'coinpaprika', 'fred'], 'optional': ['chronulus', 'slack']},
        'Trade Executor': {'required': ['trade_agent'], 'optional': ['slack']},
        'Parameter Optimizer': {'required': ['optuna'], 'optional': ['slack']}
    }
    
    print("\\n🔍 Agent Requirement Verification:")
    print("=" * 50)
    
    all_satisfied = True
    
    for agent, reqs in requirements.items():
        print(f"\\n🤖 {agent}:")
        
        # Check required servers
        missing_required = set(reqs['required']) - servers
        if missing_required:
            print(f"  ❌ Missing required: {', '.join(missing_required)}")
            all_satisfied = False
        else:
            print(f"  ✅ All required servers present: {', '.join(reqs['required'])}")
        
        # Check optional servers
        available_optional = set(reqs['optional']) & servers
        if available_optional:
            print(f"  ➕ Optional servers available: {', '.join(available_optional)}")
    
    print(f"\\n{'✅ All agent requirements satisfied!' if all_satisfied else '❌ Some requirements not met!'}")
    return all_satisfied

def generate_cleanup_report():
    """Generate comprehensive cleanup report"""
    comparison = compare_configurations()
    
    report = f"""
# MCP Server Cleanup Report
Generated: {datetime.now().isoformat()}

## Summary
- **Original servers**: {comparison['original_count']}
- **Clean servers**: {comparison['clean_count']} 
- **Removed servers**: {comparison['removed_count']}
- **Reduction**: {(comparison['removed_count']/comparison['original_count']*100):.1f}%

## Kept Servers (Required by Agents)
{chr(10).join(f'- {server}' for server in sorted(comparison['kept_servers']))}

## Removed Servers (Unnecessary)
{chr(10).join(f'- {server}' for server in sorted(comparison['removed_servers']))}

## Rationale for Removal
The removed servers were eliminated because:
1. **debugg_ai**: Debugging functionality not needed in production
2. **pipedream**: Workflow automation handled by orchestrator service
3. **zapier**: External automation not required for agent-based system
4. **graphlit**: Graph analytics not needed for trading operations
5. **serena**: Redundant AI agent (we have specialized agents)
6. **compass**: Navigation utilities not applicable to trading system
7. **server_generator**: Development tool, not needed in production

## Agent-Server Mapping
- **Risk Manager**: sqlite, phoenix, slack (optional)
- **Market/News Analyst**: yfinance, coinpaprika, fred, chronulus (optional), slack (optional)  
- **Trade Executor**: trade_agent, slack (optional)
- **Parameter Optimizer**: optuna, slack (optional)
"""
    
    report_path = Path(__file__).parent.parent / "config" / "mcp_cleanup_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"📝 Cleanup report saved: {report_path}")
    return report_path

if __name__ == "__main__":
    print("🧹 MCP Server Cleanup Tool")
    print("=" * 50)
    
    # Compare configurations
    comparison_results = compare_configurations()
    
    # Verify agent requirements  
    requirements_met = verify_agent_requirements()
    
    # Generate report
    report_path = generate_cleanup_report()
    
    print("\\n" + "=" * 50)
    print("🎯 Cleanup Summary:")
    print(f"  📉 Reduced from {comparison_results['original_count']} to {comparison_results['clean_count']} servers")
    print(f"  🗑️ Removed {comparison_results['removed_count']} unnecessary servers")
    print(f"  ✅ Agent requirements: {'Met' if requirements_met else 'Not met'}")
    print(f"  📝 Report saved: {report_path}")
    
    if requirements_met:
        print("\\n🚀 Ready to apply clean configuration!")
        print("Run with --apply flag to replace original configuration")
    else:
        print("\\n⚠️  Please review agent requirements before applying")
    
    # Check for --apply flag
    import sys
    if '--apply' in sys.argv:
        print("\\n🔄 Applying clean configuration...")
        apply_clean_configuration()
        print("✅ Clean configuration applied successfully!")
    else:
        print("\\n💡 Add --apply flag to replace original configuration with clean version")