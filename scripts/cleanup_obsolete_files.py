#!/usr/bin/env python3
"""
Obsolete File Cleanup Script for Modular Agent-Based Trading System
Removes files and folders that are no longer part of the updated system
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class TradingSystemCleaner:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.deleted_files = []
        self.deleted_folders = []
        self.retained_files = []
        self.skipped_files = []
        
        # Define active components in the modular agent system
        self.active_components = {
            # Core agent services (transformed from original)
            'src/signal_service.py',           # Risk Manager Agent (mistral7b)
            'src/data_service.py',             # Market/News Analyst Agent (mistral7b) 
            'src/market_executor_service.py',  # Trade Executor Agent (phi3)
            'src/parameter_optimizer_service.py', # Parameter Optimizer (Python)
            'src/orchestrator_service.py',     # Agent Orchestrator
            
            # Supporting services
            'src/portfolio_service.py',        # Portfolio management
            'src/notification_service.py',     # Slack notifications
            'src/backtesting_engine.py',       # Backtester service (Python, no LLM)
            'src/paper_trading_engine.py',     # Paper trading engine
            
            # Utilities
            'src/utils/config_manager.py',     # Centralized configuration
            'src/slack_webhook_logger.py',     # Slack logging utility
            
            # MCP Hub (if used)
            'src/mcp_hub/',                    # MCP coordination
        }
        
        # Configuration files for agent system
        self.active_configs = {
            'config/agent_system_config.yaml',
            'config/agent_mcps/',
            'config/mcp_servers.yaml', 
            'config/mcp_servers_agents.yaml',
            'config/production_config.yaml',
            'config/trading_parameters.yaml',
            'config/message_templates.yaml',
            'config/mcp_cleanup_report.md',
        }
        
        # Scripts for agent management
        self.active_scripts = {
            'scripts/start_agents.sh',
            'scripts/stop_agents.sh', 
            'scripts/check_agents.sh',
            'scripts/configure_agent_mcps.py',
            'scripts/cleanup_mcp_servers.py',
        }
        
        # Docker and deployment files
        self.active_deployment = {
            'docker-compose.agents.yml',
            'Dockerfile',
            '.env',
            'requirements.txt',
        }
        
        # Database and logs (keep for data persistence)
        self.preserve_data = {
            'database/',
            'logs/',
        }
        
        # MCP servers (keep Slack integration)
        self.active_mcp = {
            'mcp-servers/slack/',
        }
        
        # Obsolete files and folders to remove
        self.obsolete_items = {
            # Old service folders that were replaced by agent architecture
            'src/api_gateway/',
            'src/assistant_service/', 
            'src/config_service/',
            'src/trading_bot_service/',
            
            # Test files for old architecture
            'test_market_executor.py',
            'test_parameter_optimizer.py', 
            'test_slack_integration.py',
            'test_webhook_integration.py',
            'tests/',
            'mcp_agent_system/tests/',
            
            # Old backtest runners (replaced by backtesting_engine.py)
            'backtest_runner.py',
            'run_backtest.py',
            'run_complete_backtest.py',
            
            # Archive folders
            'archive/',
            'backups/',
            'serena/',  # External AI agent, not needed
            
            # Old system reports and analysis files
            'HARDCODED_VALUES_ELIMINATION_REPORT.md',
            'MCP_INTEGRATION_GUIDE.md',
            'WORKSPACE_CLEANUP_REPORT.md',
            'optimization_analysis.md',
            'SYSTEM_TEST_REPORT_*.json',
            
            # Old Docker files
            'docker-compose.income-optimized.yml',
            'docker-compose.mcp.yml', 
            'docker-compose.yml',  # Keep only docker-compose.agents.yml
            'Dockerfile.mcp',
            'deploy_optimized_system.sh',
            
            # Obsolete scripts
            'scripts/backtest_optimize_deploy.sh',
            'scripts/start_income_optimized.sh',
            'scripts/start_mcp_system.sh',
            'scripts/start_trading_system.sh',
            'scripts/start_with_optimization.sh',
            'scripts/monitor_optimized_system.sh',
            'scripts/monitor_trading.sh',
            'scripts/setup_slack_integration.sh',
            'scripts/setup_slack_oauth.py',
            'scripts/notify_deployment_success.py',
            'scripts/serena_chat_cli.py',
            
            # Old config files
            'config/mcp_servers_backup_*.yaml',
            'config/mcp_servers_clean.yaml',
            'config/mcp_servers_optimized.yaml',
            'config/assistant_command_templates.yaml',
            'config/cicd-pipeline.yaml',
            'config/monitoring-dashboard.yaml',
            'config/orchestrator-deployment.yaml',
            'config/routes.yaml',
            'config/startup_message.txt',
            'config/trading-secrets.yaml',
            'config/mcp_tools.yaml',
            
            # Old monitoring/deployment files
            'prometheus.yml',
            'grafana/',
            
            # Obsolete system components
            'mcp_agent_system/',  # Old MCP system
            'system_status.json',
            'backtest_results/',
        }
    
    def is_active_component(self, path_str):
        """Check if a path is part of the active agent system"""
        path = Path(path_str)
        
        # Check against active components
        for active in self.active_components:
            active_path = self.project_root / active
            try:
                if path.samefile(active_path) or path.is_relative_to(active_path):
                    return True
            except (OSError, ValueError):
                if str(path).endswith(active) or active in str(path):
                    return True
        
        # Check against active configs
        for active in self.active_configs:
            active_path = self.project_root / active
            try:
                if path.samefile(active_path) or path.is_relative_to(active_path):
                    return True
            except (OSError, ValueError):
                if str(path).endswith(active) or active in str(path):
                    return True
        
        # Check against active scripts
        for active in self.active_scripts:
            active_path = self.project_root / active
            try:
                if path.samefile(active_path) or path.is_relative_to(active_path):
                    return True
            except (OSError, ValueError):
                if str(path).endswith(active) or active in str(path):
                    return True
                    
        # Check against deployment files
        for active in self.active_deployment:
            active_path = self.project_root / active
            try:
                if path.samefile(active_path) or path.is_relative_to(active_path):
                    return True
            except (OSError, ValueError):
                if str(path).endswith(active) or active in str(path):
                    return True
        
        # Check preserve data directories
        for preserve in self.preserve_data:
            preserve_path = self.project_root / preserve
            try:
                if path.is_relative_to(preserve_path):
                    return True
            except (OSError, ValueError):
                if preserve in str(path):
                    return True
                    
        # Check active MCP servers
        for active in self.active_mcp:
            active_path = self.project_root / active
            try:
                if path.is_relative_to(active_path):
                    return True
            except (OSError, ValueError):
                if active in str(path):
                    return True
        
        return False
    
    def is_obsolete(self, path_str):
        """Check if a path should be removed"""
        path = Path(path_str)
        
        for obsolete in self.obsolete_items:
            if obsolete.endswith('*'):
                # Pattern matching
                pattern = obsolete[:-1]
                if pattern in str(path):
                    return True
            else:
                obsolete_path = self.project_root / obsolete
                try:
                    if path.samefile(obsolete_path) or path.is_relative_to(obsolete_path):
                        return True
                except (OSError, ValueError):
                    if str(path).endswith(obsolete) or obsolete in str(path):
                        return True
        
        return False
    
    def should_clean_file(self, file_path):
        """Determine if a file should be cleaned up"""
        path = Path(file_path)
        
        # Skip if it's an active component
        if self.is_active_component(file_path):
            return False
            
        # Remove if it's explicitly obsolete
        if self.is_obsolete(file_path):
            return True
            
        # Remove temp files
        if path.suffix in ['.pyc', '.pyo', '.pyd', '__pycache__']:
            return True
            
        # Remove log files (except in logs/ directory)
        if path.suffix == '.log' and 'logs/' not in str(path):
            return True
            
        # Remove backup files
        if path.suffix in ['.bak', '.backup', '.tmp', '.old']:
            return True
            
        # Remove system test reports
        if 'SYSTEM_TEST_REPORT' in path.name:
            return True
            
        return False
    
    def clean_directory(self, directory):
        """Clean files and subdirectories in a directory"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return
            
        items = list(dir_path.iterdir())
        
        for item in items:
            if item.is_file():
                if self.should_clean_file(item):
                    try:
                        item.unlink()
                        self.deleted_files.append(str(item.relative_to(self.project_root)))
                        print(f"🗑️  Deleted file: {item.relative_to(self.project_root)}")
                    except Exception as e:
                        print(f"❌ Error deleting {item}: {e}")
                        self.skipped_files.append(str(item.relative_to(self.project_root)))
                elif self.is_active_component(item):
                    self.retained_files.append(str(item.relative_to(self.project_root)))
                else:
                    self.skipped_files.append(str(item.relative_to(self.project_root)))
                    
            elif item.is_dir():
                if self.is_obsolete(item):
                    try:
                        shutil.rmtree(item)
                        self.deleted_folders.append(str(item.relative_to(self.project_root)))
                        print(f"🗑️  Deleted folder: {item.relative_to(self.project_root)}")
                    except Exception as e:
                        print(f"❌ Error deleting {item}: {e}")
                        self.skipped_files.append(str(item.relative_to(self.project_root)))
                elif self.is_active_component(item):
                    self.retained_files.append(str(item.relative_to(self.project_root)))
                    # Recursively clean the directory
                    self.clean_directory(item)
                else:
                    # Check if directory has any active components
                    has_active = any(self.is_active_component(subitem) for subitem in item.rglob('*'))
                    if has_active:
                        self.clean_directory(item)
                    else:
                        # Consider for manual review
                        self.skipped_files.append(str(item.relative_to(self.project_root)))
    
    def generate_report(self):
        """Generate cleanup report"""
        report = {
            'cleanup_timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'summary': {
                'deleted_files': len(self.deleted_files),
                'deleted_folders': len(self.deleted_folders),
                'retained_files': len(self.retained_files),
                'skipped_files': len(self.skipped_files)
            },
            'deleted_files': sorted(self.deleted_files),
            'deleted_folders': sorted(self.deleted_folders),
            'retained_files': sorted(self.retained_files),
            'skipped_files': sorted(self.skipped_files)
        }
        
        # Save report
        report_path = self.project_root / 'cleanup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_cleanup(self):
        """Execute the cleanup process"""
        print("🧹 Starting obsolete file cleanup for Agent-Based Trading System")
        print("=" * 70)
        
        # Start cleanup from project root
        self.clean_directory(self.project_root)
        
        # Generate and display report
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("📊 CLEANUP SUMMARY")
        print("=" * 70)
        
        print(f"🗑️  Deleted Files: {len(self.deleted_files)}")
        if self.deleted_files:
            for file in sorted(self.deleted_files):
                print(f"   • {file}")
        
        print(f"\n📁 Deleted Folders: {len(self.deleted_folders)}")
        if self.deleted_folders:
            for folder in sorted(self.deleted_folders):
                print(f"   • {folder}")
        
        print(f"\n✅ Retained Files/Folders: {len(self.retained_files)}")
        if len(self.retained_files) <= 20:  # Show first 20
            for file in sorted(self.retained_files)[:20]:
                print(f"   • {file}")
            if len(self.retained_files) > 20:
                print(f"   ... and {len(self.retained_files) - 20} more")
        else:
            print(f"   (Too many to list - {len(self.retained_files)} total)")
        
        print(f"\n⚠️  Skipped (Manual Review): {len(self.skipped_files)}")
        if self.skipped_files:
            for file in sorted(self.skipped_files):
                print(f"   • {file}")
        
        print(f"\n📝 Detailed report saved to: cleanup_report.json")
        print("\n✅ Cleanup completed!")

if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent
    cleaner = TradingSystemCleaner(project_root)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("🔍 DRY RUN MODE - No files will be deleted")
        print("This would show what files would be cleaned up")
        # Add dry run logic here
    else:
        cleaner.run_cleanup()