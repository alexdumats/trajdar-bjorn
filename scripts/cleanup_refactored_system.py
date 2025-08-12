#!/usr/bin/env python3
"""
Cleanup Script for Refactored Trading System
Removes unused files and directories after the refactoring to agent-based architecture
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemCleanup:
    """Handles cleanup of unused files after refactoring"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "deleted_files": [],
            "deleted_directories": [],
            "retained_files": [],
            "retained_directories": [],
            "errors": [],
            "summary": {}
        }
        
        # Files and directories to delete (unused after refactor)
        self.files_to_delete = [
            # Legacy combined analyst service
            "src/data_service.py",  # Replaced by separate market/news analysts
            
            # Old mutual scheduler (replaced by enhanced version)
            "src/mutual_scheduler.py",  # Replaced by enhanced_mutual_scheduler.py
            
            # Old MCP configurations (replaced by agent-specific configs)
            "config/agent_mcps/market_news_analyst_mcps.yaml",  # Split into separate configs
            
            # Old docker compose (replaced by refactored version)
            "docker-compose.agents.yml",  # Replaced by docker-compose.refactored.yml
            
            # Incomplete parameter updater
            "src/slack_parameter_updater.py",  # Replaced by slack_integration_service.py
            
            # Legacy configuration files
            "config/trading_parameters.yaml",  # Consolidated into agent_parameters.yaml
            
            # Old cleanup reports
            "cleanup_report.json",
            "CLEANUP_SUMMARY.md",
            "config/mcp_cleanup_report.md",
        ]
        
        self.directories_to_delete = [
            # Empty or unused directories
            "mcp_agent_system",  # Unused agent system structure
            "test_results/htmlcov",  # Old test coverage reports
            "test_results/coverage",  # Old coverage data
            ".pytest_cache",  # Pytest cache
            ".serena",  # Serena coding service cache
            "grafana/provisioning/dashboards",  # Unused grafana configs
        ]
        
        # Files and directories to retain (active services)
        self.retain_patterns = [
            # Active agent services
            "src/market_analyst/",
            "src/news_analyst/",
            "src/enhanced_mutual_scheduler.py",
            "src/slack_integration_service.py",
            
            # Active configurations
            "config/agent_parameters.yaml",
            "config/market_analyst/",
            "config/news_analyst/",
            "config/agent_mcps/risk_manager_mcps.yaml",
            "config/agent_mcps/trade_executor_mcps.yaml",
            "config/agent_mcps/parameter_optimizer_mcps.yaml",
            
            # Core services (still needed)
            "src/orchestrator_service.py",
            "src/portfolio_service.py",
            "src/notification_service.py",
            "src/market_executor_service.py",
            "src/parameter_optimizer_service.py",
            "src/signal_service.py",  # Used by risk manager
            "src/paper_trading_engine.py",
            "src/backtesting_engine.py",
            "src/slack_webhook_logger.py",
            
            # MCP and infrastructure
            "src/mcp_hub/",
            "mcp-servers/slack/",
            
            # Configuration and deployment
            "docker-compose.refactored.yml",
            "config/production_config.yaml",
            "config/message_templates.yaml",
            "config/mcp_servers.yaml",
            
            # Database and logs
            "database/",
            "logs/",
            "pids/",
            
            # Scripts and utilities
            "scripts/",
            "src/utils/",
            
            # Tests and documentation
            "tests/",
            "README.md",
            "requirements.txt",
            "Dockerfile",
            ".env",
            ".env.production",
        ]
    
    def is_retained(self, path: Path) -> bool:
        """Check if a path should be retained"""
        path_str = str(path.relative_to(self.base_path))
        
        for pattern in self.retain_patterns:
            if path_str.startswith(pattern) or pattern in path_str:
                return True
        
        return False
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a single file"""
        try:
            full_path = self.base_path / file_path
            if full_path.exists() and full_path.is_file():
                if self.is_retained(full_path):
                    logger.info(f"⚠️ Skipping retained file: {file_path}")
                    self.cleanup_report["retained_files"].append(file_path)
                    return False
                
                full_path.unlink()
                logger.info(f"🗑️ Deleted file: {file_path}")
                self.cleanup_report["deleted_files"].append(file_path)
                return True
            else:
                logger.info(f"ℹ️ File not found (already deleted?): {file_path}")
                return False
                
        except Exception as e:
            error_msg = f"Error deleting file {file_path}: {e}"
            logger.error(f"❌ {error_msg}")
            self.cleanup_report["errors"].append(error_msg)
            return False
    
    def delete_directory(self, dir_path: str) -> bool:
        """Delete a directory and its contents"""
        try:
            full_path = self.base_path / dir_path
            if full_path.exists() and full_path.is_dir():
                if self.is_retained(full_path):
                    logger.info(f"⚠️ Skipping retained directory: {dir_path}")
                    self.cleanup_report["retained_directories"].append(dir_path)
                    return False
                
                # Check if directory has any retained files
                has_retained_files = False
                for item in full_path.rglob("*"):
                    if self.is_retained(item):
                        has_retained_files = True
                        break
                
                if has_retained_files:
                    logger.info(f"⚠️ Directory contains retained files, skipping: {dir_path}")
                    self.cleanup_report["retained_directories"].append(dir_path)
                    return False
                
                shutil.rmtree(full_path)
                logger.info(f"🗑️ Deleted directory: {dir_path}")
                self.cleanup_report["deleted_directories"].append(dir_path)
                return True
            else:
                logger.info(f"ℹ️ Directory not found (already deleted?): {dir_path}")
                return False
                
        except Exception as e:
            error_msg = f"Error deleting directory {dir_path}: {e}"
            logger.error(f"❌ {error_msg}")
            self.cleanup_report["errors"].append(error_msg)
            return False
    
    def cleanup_empty_directories(self):
        """Remove empty directories"""
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Skip if this is a retained directory
            if self.is_retained(root_path):
                continue
            
            # Check if directory is empty
            if not dirs and not files:
                try:
                    relative_path = root_path.relative_to(self.base_path)
                    empty_dirs.append(str(relative_path))
                except ValueError:
                    continue
        
        # Delete empty directories
        for empty_dir in empty_dirs:
            self.delete_directory(empty_dir)
    
    def cleanup_log_files(self):
        """Clean up old log files (keep recent ones)"""
        logs_dir = self.base_path / "logs"
        if not logs_dir.exists():
            return
        
        try:
            for log_file in logs_dir.glob("*.log"):
                # Keep log files, just log their presence
                relative_path = log_file.relative_to(self.base_path)
                self.cleanup_report["retained_files"].append(str(relative_path))
                logger.info(f"📋 Retained log file: {relative_path}")
                
        except Exception as e:
            error_msg = f"Error processing log files: {e}"
            logger.error(f"❌ {error_msg}")
            self.cleanup_report["errors"].append(error_msg)
    
    def generate_summary(self):
        """Generate cleanup summary"""
        self.cleanup_report["summary"] = {
            "total_files_deleted": len(self.cleanup_report["deleted_files"]),
            "total_directories_deleted": len(self.cleanup_report["deleted_directories"]),
            "total_files_retained": len(self.cleanup_report["retained_files"]),
            "total_directories_retained": len(self.cleanup_report["retained_directories"]),
            "total_errors": len(self.cleanup_report["errors"]),
            "cleanup_successful": len(self.cleanup_report["errors"]) == 0
        }
    
    def save_report(self, report_path: str = "refactor_cleanup_report.json"):
        """Save cleanup report to file"""
        try:
            with open(self.base_path / report_path, 'w') as f:
                json.dump(self.cleanup_report, f, indent=2)
            logger.info(f"📊 Cleanup report saved to: {report_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save cleanup report: {e}")
    
    def run_cleanup(self):
        """Execute the complete cleanup process"""
        logger.info("🧹 Starting refactored system cleanup...")
        
        # Delete specified files
        logger.info("🗑️ Deleting unused files...")
        for file_path in self.files_to_delete:
            self.delete_file(file_path)
        
        # Delete specified directories
        logger.info("🗑️ Deleting unused directories...")
        for dir_path in self.directories_to_delete:
            self.delete_directory(dir_path)
        
        # Clean up empty directories
        logger.info("🧹 Cleaning up empty directories...")
        self.cleanup_empty_directories()
        
        # Process log files
        logger.info("📋 Processing log files...")
        self.cleanup_log_files()
        
        # Generate summary
        self.generate_summary()
        
        # Save report
        self.save_report()
        
        # Print summary
        summary = self.cleanup_report["summary"]
        logger.info("✅ Cleanup completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   • Files deleted: {summary['total_files_deleted']}")
        logger.info(f"   • Directories deleted: {summary['total_directories_deleted']}")
        logger.info(f"   • Files retained: {summary['total_files_retained']}")
        logger.info(f"   • Directories retained: {summary['total_directories_retained']}")
        logger.info(f"   • Errors: {summary['total_errors']}")
        
        if summary["cleanup_successful"]:
            logger.info("🎉 Cleanup completed successfully!")
        else:
            logger.warning("⚠️ Cleanup completed with errors. Check the report for details.")
        
        return summary

def main():
    """Main cleanup function"""
    cleanup = SystemCleanup()
    
    # Ask for confirmation
    print("🧹 Refactored System Cleanup")
    print("=" * 50)
    print("This script will delete unused files and directories after the refactoring.")
    print("\nFiles to be deleted:")
    for file_path in cleanup.files_to_delete:
        print(f"  • {file_path}")
    
    print("\nDirectories to be deleted:")
    for dir_path in cleanup.directories_to_delete:
        print(f"  • {dir_path}")
    
    print("\n⚠️ This action cannot be undone!")
    
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        summary = cleanup.run_cleanup()
        return summary["cleanup_successful"]
    else:
        print("❌ Cleanup cancelled.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)