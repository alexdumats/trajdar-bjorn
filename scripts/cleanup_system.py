#!/usr/bin/env python3
"""
System Cleanup Script for AI Trading System
Performs maintenance tasks including log rotation, cache clearing, and resource optimization
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import gzip
from typing import Dict, List, Any

class SystemCleaner:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.logs_dir = self.project_root / "logs"
        self.database_dir = self.project_root / "database"
        self.cache_dir = self.project_root / ".cache"
        self.temp_dir = self.project_root / "temp"
        
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "actions_taken": [],
            "files_processed": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
    def log_action(self, action: str, details: str = ""):
        """Log a cleanup action"""
        entry = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.cleanup_report["actions_taken"].append(entry)
        print(f"{'[DRY RUN] ' if self.dry_run else ''}✅ {action}: {details}")
    
    def log_error(self, error: str, details: str = ""):
        """Log an error"""
        entry = {
            "error": error,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.cleanup_report["errors"].append(entry)
        print(f"❌ Error: {error}: {details}")
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except:
            return 0
    
    def rotate_logs(self, max_age_days: int = 30, max_size_mb: int = 100):
        """Rotate and compress old log files"""
        print(f"\n🔄 Starting log rotation (max age: {max_age_days} days, max size: {max_size_mb}MB)")
        
        if not self.logs_dir.exists():
            self.log_action("Log rotation", "No logs directory found")
            return
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        total_size_freed = 0
        
        for log_file in self.logs_dir.rglob("*.log"):
            try:
                # Check file age
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                file_size_mb = self.get_file_size_mb(log_file)
                
                if file_mtime < cutoff_date or file_size_mb > max_size_mb:
                    # Compress old/large log files
                    compressed_name = f"{log_file.name}.{file_mtime.strftime('%Y%m%d')}.gz"
                    compressed_path = log_file.parent / compressed_name
                    
                    if not self.dry_run:
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        log_file.unlink()
                    
                    total_size_freed += file_size_mb
                    self.log_action(
                        "Log compressed", 
                        f"{log_file.name} -> {compressed_name} ({file_size_mb:.1f}MB)"
                    )
            except Exception as e:
                self.log_error("Failed to compress log", f"{log_file}: {str(e)}")
        
        # Remove very old compressed logs (90 days)
        old_cutoff = datetime.now() - timedelta(days=90)
        for gz_file in self.logs_dir.rglob("*.gz"):
            try:
                file_mtime = datetime.fromtimestamp(gz_file.stat().st_mtime)
                if file_mtime < old_cutoff:
                    file_size_mb = self.get_file_size_mb(gz_file)
                    if not self.dry_run:
                        gz_file.unlink()
                    total_size_freed += file_size_mb
                    self.log_action("Old log deleted", f"{gz_file.name} ({file_size_mb:.1f}MB)")
            except Exception as e:
                self.log_error("Failed to delete old log", f"{gz_file}: {str(e)}")
        
        self.cleanup_report["space_freed_mb"] += total_size_freed
        print(f"📊 Log rotation completed: {total_size_freed:.1f}MB freed")
    
    def clean_temp_files(self):
        """Clean temporary files and directories"""
        print(f"\n🧹 Cleaning temporary files")
        
        temp_dirs = [self.temp_dir, self.project_root / "tmp", Path("/tmp/trading_*")]
        total_size_freed = 0
        
        for temp_path in temp_dirs:
            if temp_path.exists():
                for item in temp_path.rglob("*"):
                    if item.is_file():
                        file_size_mb = self.get_file_size_mb(item)
                        if not self.dry_run:
                            item.unlink()
                        total_size_freed += file_size_mb
                        self.cleanup_report["files_processed"] += 1
                
                if not self.dry_run and temp_path.exists():
                    shutil.rmtree(temp_path)
                
                self.log_action("Temp directory cleaned", f"{temp_path} ({total_size_freed:.1f}MB)")
        
        # Clean Python cache files
        for cache_file in self.project_root.rglob("__pycache__"):
            if cache_file.is_dir():
                cache_size = sum(self.get_file_size_mb(f) for f in cache_file.rglob("*") if f.is_file())
                if not self.dry_run:
                    shutil.rmtree(cache_file)
                total_size_freed += cache_size
                self.log_action("Python cache cleaned", f"{cache_file} ({cache_size:.1f}MB)")
        
        self.cleanup_report["space_freed_mb"] += total_size_freed
        print(f"📊 Temp cleanup completed: {total_size_freed:.1f}MB freed")
    
    def vacuum_databases(self):
        """Vacuum SQLite databases to reclaim space"""
        print(f"\n🗄️ Vacuuming databases")
        
        if not self.database_dir.exists():
            self.log_action("Database vacuum", "No database directory found")
            return
        
        total_size_freed = 0
        
        for db_file in self.database_dir.glob("*.db"):
            try:
                original_size = self.get_file_size_mb(db_file)
                
                if not self.dry_run:
                    conn = sqlite3.connect(str(db_file))
                    conn.execute("VACUUM")
                    conn.close()
                
                new_size = self.get_file_size_mb(db_file) if not self.dry_run else original_size * 0.9
                size_freed = original_size - new_size
                total_size_freed += size_freed
                
                self.log_action(
                    "Database vacuumed", 
                    f"{db_file.name}: {original_size:.1f}MB -> {new_size:.1f}MB ({size_freed:.1f}MB freed)"
                )
                
            except Exception as e:
                self.log_error("Database vacuum failed", f"{db_file}: {str(e)}")
        
        self.cleanup_report["space_freed_mb"] += total_size_freed
        print(f"📊 Database vacuum completed: {total_size_freed:.1f}MB freed")
    
    def clean_old_backtest_results(self, max_age_days: int = 60):
        """Clean old backtest result files"""
        print(f"\n📈 Cleaning old backtest results (older than {max_age_days} days)")
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        total_size_freed = 0
        files_cleaned = 0
        
        # Look for backtest result files
        patterns = ["backtest_results_*.json", "optimization_results_*.json"]
        
        for pattern in patterns:
            for result_file in self.project_root.glob(pattern):
                try:
                    file_mtime = datetime.fromtimestamp(result_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size_mb = self.get_file_size_mb(result_file)
                        if not self.dry_run:
                            result_file.unlink()
                        total_size_freed += file_size_mb
                        files_cleaned += 1
                        self.log_action("Old backtest result deleted", f"{result_file.name} ({file_size_mb:.1f}MB)")
                except Exception as e:
                    self.log_error("Failed to delete backtest result", f"{result_file}: {str(e)}")
        
        self.cleanup_report["space_freed_mb"] += total_size_freed
        self.cleanup_report["files_processed"] += files_cleaned
        print(f"📊 Backtest cleanup completed: {files_cleaned} files, {total_size_freed:.1f}MB freed")
    
    def clean_docker_resources(self):
        """Clean Docker resources if Docker is available"""
        print(f"\n🐳 Cleaning Docker resources")
        
        try:
            import subprocess
            
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_action("Docker cleanup", "Docker not available")
                return
            
            # Get Docker system info before cleanup
            if not self.dry_run:
                # Remove unused containers
                result = subprocess.run(["docker", "container", "prune", "-f"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_action("Docker containers pruned", result.stdout.strip())
                
                # Remove unused images
                result = subprocess.run(["docker", "image", "prune", "-f"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_action("Docker images pruned", result.stdout.strip())
                
                # Remove unused volumes
                result = subprocess.run(["docker", "volume", "prune", "-f"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_action("Docker volumes pruned", result.stdout.strip())
            else:
                self.log_action("Docker cleanup", "Would prune unused containers, images, and volumes")
                
        except Exception as e:
            self.log_error("Docker cleanup failed", str(e))
    
    def update_refactor_cleanup_report(self):
        """Update the refactor cleanup report"""
        print(f"\n📋 Updating refactor cleanup report")
        
        report_file = self.project_root / "refactor_cleanup_report.json"
        
        try:
            # Load existing report if it exists
            if report_file.exists():
                with open(report_file, 'r') as f:
                    existing_report = json.load(f)
            else:
                existing_report = {
                    "cleanup_history": [],
                    "last_cleanup": None,
                    "total_space_freed_mb": 0,
                    "total_files_processed": 0
                }
            
            # Add current cleanup to history
            cleanup_entry = {
                "timestamp": self.cleanup_report["timestamp"],
                "dry_run": self.cleanup_report["dry_run"],
                "space_freed_mb": self.cleanup_report["space_freed_mb"],
                "files_processed": self.cleanup_report["files_processed"],
                "actions_count": len(self.cleanup_report["actions_taken"]),
                "errors_count": len(self.cleanup_report["errors"])
            }
            
            existing_report["cleanup_history"].append(cleanup_entry)
            existing_report["last_cleanup"] = self.cleanup_report["timestamp"]
            
            if not self.dry_run:
                existing_report["total_space_freed_mb"] += self.cleanup_report["space_freed_mb"]
                existing_report["total_files_processed"] += self.cleanup_report["files_processed"]
            
            # Keep only last 50 cleanup entries
            existing_report["cleanup_history"] = existing_report["cleanup_history"][-50:]
            
            # Save updated report
            if not self.dry_run:
                with open(report_file, 'w') as f:
                    json.dump(existing_report, f, indent=2)
            
            self.log_action("Refactor cleanup report updated", f"Added cleanup entry to {report_file}")
            
        except Exception as e:
            self.log_error("Failed to update refactor cleanup report", str(e))
    
    def generate_cleanup_summary(self):
        """Generate and save cleanup summary"""
        print(f"\n📊 Cleanup Summary")
        print(f"{'='*50}")
        print(f"Timestamp: {self.cleanup_report['timestamp']}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Actions taken: {len(self.cleanup_report['actions_taken'])}")
        print(f"Files processed: {self.cleanup_report['files_processed']}")
        print(f"Space freed: {self.cleanup_report['space_freed_mb']:.1f} MB")
        print(f"Errors: {len(self.cleanup_report['errors'])}")
        
        if self.cleanup_report['errors']:
            print(f"\n❌ Errors encountered:")
            for error in self.cleanup_report['errors']:
                print(f"  - {error['error']}: {error['details']}")
        
        # Save detailed report
        report_file = self.logs_dir / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if not self.dry_run:
            self.logs_dir.mkdir(exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(self.cleanup_report, f, indent=2)
            print(f"\n📄 Detailed report saved: {report_file}")
    
    def run_full_cleanup(self, 
                        log_max_age_days: int = 30,
                        log_max_size_mb: int = 100,
                        backtest_max_age_days: int = 60):
        """Run complete system cleanup"""
        print(f"🧹 Starting AI Trading System Cleanup")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Project root: {self.project_root}")
        
        try:
            self.rotate_logs(log_max_age_days, log_max_size_mb)
            self.clean_temp_files()
            self.vacuum_databases()
            self.clean_old_backtest_results(backtest_max_age_days)
            self.clean_docker_resources()
            self.update_refactor_cleanup_report()
            
            self.generate_cleanup_summary()
            
        except Exception as e:
            self.log_error("Cleanup failed", str(e))
            raise

def main():
    parser = argparse.ArgumentParser(description="AI Trading System Cleanup")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be cleaned without making changes")
    parser.add_argument("--log-max-age", type=int, default=30,
                       help="Maximum age for log files in days (default: 30)")
    parser.add_argument("--log-max-size", type=int, default=100,
                       help="Maximum size for log files in MB (default: 100)")
    parser.add_argument("--backtest-max-age", type=int, default=60,
                       help="Maximum age for backtest results in days (default: 60)")
    parser.add_argument("--logs-only", action="store_true",
                       help="Only rotate logs")
    parser.add_argument("--temp-only", action="store_true", 
                       help="Only clean temporary files")
    parser.add_argument("--db-only", action="store_true",
                       help="Only vacuum databases")
    
    args = parser.parse_args()
    
    cleaner = SystemCleaner(dry_run=args.dry_run)
    
    try:
        if args.logs_only:
            cleaner.rotate_logs(args.log_max_age, args.log_max_size)
        elif args.temp_only:
            cleaner.clean_temp_files()
        elif args.db_only:
            cleaner.vacuum_databases()
        else:
            cleaner.run_full_cleanup(
                args.log_max_age,
                args.log_max_size, 
                args.backtest_max_age
            )
        
        print(f"\n✅ Cleanup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()