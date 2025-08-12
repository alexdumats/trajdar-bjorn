#!/usr/bin/env python3
"""
System Maintenance Protocol - Fault-Tolerant Daily Restart

Features:
- Scheduled daily restart at 00:00
- Pre-restart data preservation
- Post-restart integrity verification
- Comprehensive event logging
- Robust failure recovery procedures with automated fallback
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import yaml
import requests
try:
    import schedule
except ImportError:
    print("Schedule package not installed. Run: pip install schedule")
    sys.exit(1)
try:
    import docker
except ImportError:
    print("Docker package not installed. Run: pip install docker")
    sys.exit(1)
try:
    import psutil
except ImportError:
    print("Psutil package not installed. Run: pip install psutil")
    sys.exit(1)
import signal
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "system_maintenance.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemMaintenanceProtocol:
    def __init__(self):
        """Initialize the system maintenance protocol"""
        self.config_path = os.getenv("CONFIG_PATH", "config/production_config.yaml")
        self.db_path = os.getenv("DB_PATH", "database/paper_trading.db")
        self.backup_dir = os.getenv("BACKUP_DIR", "backups")
        self.docker_compose_file = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.production.yml")
        self.restart_time = os.getenv("RESTART_TIME", "00:00")
        self.max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "300"))  # 5 minutes
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        # Load configuration
        self.config = self._load_config()
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Track service states
        self.service_states = {}
        
        # Track restart status
        self.restart_in_progress = False
        self.last_restart_time = None
        self.last_restart_status = None
        self.restart_attempt = 0
        
        logger.info("🔧 System Maintenance Protocol initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def start_scheduled_maintenance(self):
        """Start scheduled maintenance"""
        logger.info(f"📅 Scheduling daily system restart at {self.restart_time}")
        
        # Schedule daily restart
        schedule.every().day.at(self.restart_time).do(self.perform_system_restart)
        
        # Also schedule health checks every hour
        schedule.every(1).hours.do(self.perform_health_check)
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def perform_system_restart(self) -> bool:
        """Perform complete system restart procedure"""
        if self.restart_in_progress:
            logger.warning("⚠️ Restart already in progress, skipping")
            return False
        
        self.restart_in_progress = True
        self.restart_attempt = 0
        restart_start_time = datetime.now()
        
        logger.info("🔄 Starting system restart procedure")
        self._log_event("system_restart_started", {"timestamp": restart_start_time.isoformat()})
        
        try:
            # Step 1: Pre-restart data preservation
            if not self._preserve_data():
                raise Exception("Pre-restart data preservation failed")
            
            # Step 2: Stop services
            if not self._stop_services():
                raise Exception("Failed to stop services")
            
            # Step 3: Start services
            if not self._start_services():
                raise Exception("Failed to start services")
            
            # Step 4: Post-restart integrity verification
            if not self._verify_integrity():
                raise Exception("Post-restart integrity verification failed")
            
            # Success
            restart_end_time = datetime.now()
            duration = (restart_end_time - restart_start_time).total_seconds()
            
            self.last_restart_time = restart_end_time
            self.last_restart_status = "success"
            
            logger.info(f"✅ System restart completed successfully in {duration:.1f} seconds")
            self._log_event("system_restart_completed", {
                "status": "success",
                "duration_seconds": duration,
                "timestamp": restart_end_time.isoformat()
            })
            
            # Send success notification
            self._send_notification(
                "✅ System Restart Completed",
                f"System restart completed successfully in {duration:.1f} seconds."
            )
            
            self.restart_in_progress = False
            return True
            
        except Exception as e:
            logger.error(f"❌ System restart failed: {e}")
            
            # Attempt recovery
            if self.restart_attempt < self.max_retry_attempts:
                self.restart_attempt += 1
                logger.warning(f"⚠️ Attempting restart recovery (attempt {self.restart_attempt}/{self.max_retry_attempts})")
                
                # Send warning notification
                self._send_notification(
                    "⚠️ System Restart Failed - Attempting Recovery",
                    f"Restart failed: {str(e)}\nAttempting recovery ({self.restart_attempt}/{self.max_retry_attempts})"
                )
                
                # Wait a bit before retrying
                time.sleep(30)
                
                # Try again
                return self.perform_system_restart()
            else:
                # All recovery attempts failed
                self.last_restart_status = "failed"
                
                logger.critical("❌ All restart recovery attempts failed")
                self._log_event("system_restart_failed", {
                    "status": "failed",
                    "error": str(e),
                    "attempts": self.restart_attempt,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Send critical notification
                self._send_notification(
                    "🔴 CRITICAL: System Restart Failed",
                    f"All restart recovery attempts failed. Manual intervention required.\nError: {str(e)}"
                )
                
                # Attempt emergency fallback
                self._emergency_fallback()
                
                self.restart_in_progress = False
                return False
    
    def _preserve_data(self) -> bool:
        """Pre-restart data preservation"""
        logger.info("💾 Performing pre-restart data preservation")
        
        try:
            # 1. Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"pre_restart_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # 2. Backup database
            if os.path.exists(self.db_path):
                # Create database connection
                conn = sqlite3.connect(self.db_path)
                
                # Backup database to SQL file
                with open(os.path.join(backup_path, "database_backup.sql"), 'w') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")
                
                # Also copy the database file directly
                shutil.copy2(self.db_path, os.path.join(backup_path, os.path.basename(self.db_path)))
                
                conn.close()
                logger.info(f"✅ Database backed up to {backup_path}")
            
            # 3. Backup configuration files
            config_backup_dir = os.path.join(backup_path, "config")
            os.makedirs(config_backup_dir, exist_ok=True)
            
            # Copy all YAML files from config directory
            config_dir = os.path.dirname(self.config_path)
            for file in os.listdir(config_dir):
                if file.endswith((".yaml", ".yml", ".json")):
                    src_path = os.path.join(config_dir, file)
                    dst_path = os.path.join(config_backup_dir, file)
                    shutil.copy2(src_path, dst_path)
            
            logger.info(f"✅ Configuration files backed up to {config_backup_dir}")
            
            # 4. Backup logs
            logs_backup_dir = os.path.join(backup_path, "logs")
            os.makedirs(logs_backup_dir, exist_ok=True)
            
            # Copy all log files
            logs_dir = "logs"
            if os.path.exists(logs_dir):
                for file in os.listdir(logs_dir):
                    if file.endswith(".log"):
                        src_path = os.path.join(logs_dir, file)
                        dst_path = os.path.join(logs_backup_dir, file)
                        shutil.copy2(src_path, dst_path)
            
            logger.info(f"✅ Log files backed up to {logs_backup_dir}")
            
            # 5. Create backup manifest
            manifest = {
                "timestamp": timestamp,
                "backup_type": "pre_restart",
                "database": os.path.basename(self.db_path),
                "config_files": [f for f in os.listdir(config_backup_dir)],
                "log_files": [f for f in os.listdir(logs_backup_dir)],
                "system_info": {
                    "hostname": os.uname().nodename,
                    "platform": sys.platform,
                    "python_version": sys.version
                }
            }
            
            with open(os.path.join(backup_path, "manifest.json"), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✅ Backup manifest created at {backup_path}/manifest.json")
            
            # 6. Create backup checksum file
            checksums = {}
            for root, _, files in os.walk(backup_path):
                for file in files:
                    if file != "checksums.json":  # Skip the checksum file itself
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, backup_path)
                        with open(file_path, 'rb') as f:
                            checksums[rel_path] = hashlib.sha256(f.read()).hexdigest()
            
            with open(os.path.join(backup_path, "checksums.json"), 'w') as f:
                json.dump(checksums, f, indent=2)
            
            logger.info(f"✅ Backup checksums created at {backup_path}/checksums.json")
            
            # Store backup path for later verification
            self.last_backup_path = backup_path
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data preservation failed: {e}")
            return False
    
    def _stop_services(self) -> bool:
        """Stop all services"""
        logger.info("🛑 Stopping services")
        
        try:
            # 1. Save current service states
            self.service_states = self._get_service_states()
            
            # 2. Stop services using docker-compose
            if os.path.exists(self.docker_compose_file):
                result = subprocess.run(
                    ["docker-compose", "-f", self.docker_compose_file, "down"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to stop services: {result.stderr}")
                    return False
                
                logger.info("✅ Services stopped successfully")
                return True
            else:
                logger.error(f"Docker compose file not found: {self.docker_compose_file}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to stop services: {e}")
            return False
    
    def _start_services(self) -> bool:
        """Start all services"""
        logger.info("🚀 Starting services")
        
        try:
            # Start services using docker-compose
            if os.path.exists(self.docker_compose_file):
                result = subprocess.run(
                    ["docker-compose", "-f", self.docker_compose_file, "up", "-d"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to start services: {result.stderr}")
                    return False
                
                # Wait for services to be healthy
                logger.info("⏳ Waiting for services to be healthy...")
                start_time = time.time()
                
                while time.time() - start_time < self.health_check_timeout:
                    if self._check_services_health():
                        logger.info("✅ All services started and healthy")
                        return True
                    
                    # Wait a bit before checking again
                    time.sleep(5)
                
                logger.error(f"Timeout waiting for services to be healthy after {self.health_check_timeout} seconds")
                return False
            else:
                logger.error(f"Docker compose file not found: {self.docker_compose_file}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}")
            return False
    
    def _verify_integrity(self) -> bool:
        """Post-restart integrity verification"""
        logger.info("🔍 Performing post-restart integrity verification")
        
        try:
            # 1. Verify database integrity
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                
                if result[0] != "ok":
                    logger.error(f"Database integrity check failed: {result[0]}")
                    conn.close()
                    return False
                
                # Check if we can query tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                if not tables:
                    logger.error("Database appears empty or corrupted")
                    conn.close()
                    return False
                
                conn.close()
                logger.info("✅ Database integrity verified")
            else:
                logger.error(f"Database file not found: {self.db_path}")
                return False
            
            # 2. Verify service health
            if not self._check_services_health():
                logger.error("Service health check failed")
                return False
            
            # 3. Verify API endpoints
            if not self._check_api_endpoints():
                logger.error("API endpoint check failed")
                return False
            
            logger.info("✅ System integrity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Integrity verification failed: {e}")
            return False
    
    def _get_service_states(self) -> Dict[str, Any]:
        """Get current state of all services"""
        states = {}
        
        try:
            if self.docker_client:
                containers = self.docker_client.containers.list(all=True)
                
                for container in containers:
                    states[container.name] = {
                        "id": container.id,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else container.image.id,
                        "created": container.attrs.get("Created", ""),
                        "ports": container.ports
                    }
            
            return states
            
        except Exception as e:
            logger.error(f"Failed to get service states: {e}")
            return {}
    
    def _check_services_health(self) -> bool:
        """Check if all services are healthy"""
        try:
            if self.docker_client:
                containers = self.docker_client.containers.list()
                
                for container in containers:
                    # Check if container is running
                    if container.status != "running":
                        logger.warning(f"Container {container.name} is not running (status: {container.status})")
                        return False
                    
                    # Check health status if available
                    health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                    if health and health != "healthy":
                        logger.warning(f"Container {container.name} is not healthy (health: {health})")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check services health: {e}")
            return False
    
    def _check_api_endpoints(self) -> bool:
        """Check if API endpoints are responding"""
        try:
            # Get services from config
            services = self.config.get("services", {})
            
            for service_name, service_config in services.items():
                port = service_config.get("port")
                
                if port:
                    url = f"http://localhost:{port}/health"
                    
                    try:
                        response = requests.get(url, timeout=5)
                        
                        if response.status_code != 200:
                            logger.warning(f"Service {service_name} health check failed: HTTP {response.status_code}")
                            return False
                        
                    except requests.RequestException as e:
                        logger.warning(f"Failed to connect to service {service_name}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check API endpoints: {e}")
            return False
    
    def _emergency_fallback(self):
        """Emergency fallback procedure when all restart attempts fail"""
        logger.critical("🚨 Initiating emergency fallback procedure")
        
        try:
            # 1. Restore from last backup if available
            if hasattr(self, 'last_backup_path') and os.path.exists(self.last_backup_path):
                logger.info(f"Attempting to restore from backup: {self.last_backup_path}")
                
                # Restore database
                db_backup = os.path.join(self.last_backup_path, os.path.basename(self.db_path))
                if os.path.exists(db_backup):
                    shutil.copy2(db_backup, self.db_path)
                    logger.info(f"Database restored from {db_backup}")
                
                # Restore config files
                config_backup_dir = os.path.join(self.last_backup_path, "config")
                if os.path.exists(config_backup_dir):
                    config_dir = os.path.dirname(self.config_path)
                    for file in os.listdir(config_backup_dir):
                        src_path = os.path.join(config_backup_dir, file)
                        dst_path = os.path.join(config_dir, file)
                        shutil.copy2(src_path, dst_path)
                    
                    logger.info(f"Configuration files restored from {config_backup_dir}")
            
            # 2. Try to start services with minimal configuration
            logger.info("Attempting to start services with minimal configuration")
            
            # Use fallback docker-compose file if available
            fallback_compose = "docker-compose.fallback.yml"
            if os.path.exists(fallback_compose):
                result = subprocess.run(
                    ["docker-compose", "-f", fallback_compose, "up", "-d"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("Services started with fallback configuration")
                else:
                    logger.error(f"Failed to start services with fallback configuration: {result.stderr}")
            
            # 3. Send critical alert
            self._send_notification(
                "🚨 EMERGENCY FALLBACK ACTIVATED",
                "System restart failed and emergency fallback procedure has been activated. "
                "The system may be in a degraded state. Immediate manual intervention required."
            )
            
            logger.critical("Emergency fallback procedure completed")
            
        except Exception as e:
            logger.critical(f"Emergency fallback procedure failed: {e}")
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log event to event log file"""
        try:
            event_log_path = os.path.join("logs", "system_events.jsonl")
            
            # Create event object
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data
            }
            
            # Append to event log file
            with open(event_log_path, 'a') as f:
                f.write(json.dumps(event) + "\n")
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    def _send_notification(self, title: str, message: str):
        """Send notification to configured channels"""
        try:
            # Send to Slack if webhook URL is configured
            if self.slack_webhook_url:
                payload = {
                    "text": f"*{title}*\n\n{message}"
                }
                
                response = requests.post(self.slack_webhook_url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Failed to send Slack notification: HTTP {response.status_code}")
            
            # Log notification
            logger.info(f"Notification sent: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def perform_health_check(self) -> bool:
        """Perform system health check"""
        logger.info("🏥 Performing system health check")
        
        try:
            # 1. Check if services are running
            services_healthy = self._check_services_health()
            
            # 2. Check API endpoints
            apis_healthy = self._check_api_endpoints()
            
            # 3. Check database
            db_healthy = False
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Run quick integrity check
                cursor.execute("PRAGMA quick_check")
                result = cursor.fetchone()
                
                db_healthy = result[0] == "ok"
                conn.close()
            
            # 4. Check disk space
            disk_healthy = True
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 90:  # Warning if disk usage > 90%
                logger.warning(f"Disk usage is high: {disk_usage.percent}%")
                disk_healthy = False
            
            # 5. Check memory usage
            memory_healthy = True
            memory = psutil.virtual_memory()
            if memory.percent > 90:  # Warning if memory usage > 90%
                logger.warning(f"Memory usage is high: {memory.percent}%")
                memory_healthy = False
            
            # Overall health status
            overall_healthy = services_healthy and apis_healthy and db_healthy and disk_healthy and memory_healthy
            
            # Log health check result
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "services_healthy": services_healthy,
                "apis_healthy": apis_healthy,
                "db_healthy": db_healthy,
                "disk_healthy": disk_healthy,
                "memory_healthy": memory_healthy,
                "overall_healthy": overall_healthy
            }
            
            self._log_event("health_check", health_data)
            
            # Send notification if not healthy
            if not overall_healthy:
                issues = []
                if not services_healthy:
                    issues.append("Services not healthy")
                if not apis_healthy:
                    issues.append("API endpoints not responding")
                if not db_healthy:
                    issues.append("Database integrity issues")
                if not disk_healthy:
                    issues.append(f"Disk usage high ({disk_usage.percent}%)")
                if not memory_healthy:
                    issues.append(f"Memory usage high ({memory.percent}%)")
                
                self._send_notification(
                    "⚠️ System Health Warning",
                    f"System health check detected issues:\n• " + "\n• ".join(issues)
                )
            
            logger.info(f"Health check completed: {'Healthy' if overall_healthy else 'Issues detected'}")
            return overall_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="System Maintenance Protocol")
    parser.add_argument("--now", action="store_true", help="Perform system restart immediately")
    parser.add_argument("--health-check", action="store_true", help="Perform health check only")
    args = parser.parse_args()
    
    protocol = SystemMaintenanceProtocol()
    
    if args.now:
        # Perform restart immediately
        success = protocol.perform_system_restart()
        sys.exit(0 if success else 1)
    elif args.health_check:
        # Perform health check only
        healthy = protocol.perform_health_check()
        sys.exit(0 if healthy else 1)
    else:
        # Start scheduled maintenance
        protocol.start_scheduled_maintenance()

if __name__ == "__main__":
    main()