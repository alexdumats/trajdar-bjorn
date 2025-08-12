#!/usr/bin/env python3
"""
AI Trading System - Smoke Tests
Basic functionality tests to verify system is deployment-ready
"""

import os
import sys
import sqlite3
import requests
import subprocess
import tempfile
from pathlib import Path

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_colored(message, color=Colors.NC):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")

def run_smoke_tests():
    """Run basic smoke tests"""
    print_colored("🧪 AI Trading System - Smoke Tests", Colors.CYAN)
    print_colored("=" * 40, Colors.CYAN)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Check Python imports
    print_colored("\n1. Testing Python imports...", Colors.BLUE)
    tests_total += 1
    try:
        # Test basic imports
        import fastapi
        import uvicorn
        import pandas
        import numpy
        import aiohttp
        import yaml
        import sqlite3
        
        print_colored("✅ All required Python packages available", Colors.GREEN)
        tests_passed += 1
    except ImportError as e:
        print_colored(f"❌ Import error: {e}", Colors.RED)
    
    # Test 2: Check configuration files
    print_colored("\n2. Testing configuration files...", Colors.BLUE)
    tests_total += 1
    try:
        project_root = Path(__file__).parent.parent
        config_files = [
            "config/production_config.yaml",
            "config/trading_parameters.yaml", 
            "config/mcp_servers.yaml"
        ]
        
        missing_files = []
        for config_file in config_files:
            config_path = project_root / config_file
            if not config_path.exists():
                missing_files.append(config_file)
        
        if missing_files:
            print_colored(f"❌ Missing config files: {missing_files}", Colors.RED)
        else:
            print_colored("✅ All configuration files present", Colors.GREEN)
            tests_passed += 1
            
    except Exception as e:
        print_colored(f"❌ Configuration test error: {e}", Colors.RED)
    
    # Test 3: Database operations
    print_colored("\n3. Testing database operations...", Colors.BLUE)
    tests_total += 1
    try:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Test database creation
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_portfolio (
                id INTEGER PRIMARY KEY,
                balance REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_portfolio (balance) VALUES (10000.0)")
        
        # Query test data
        cursor.execute("SELECT balance FROM test_portfolio WHERE id = 1")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if result and result[0] == 10000.0:
            print_colored("✅ Database operations working", Colors.GREEN)
            tests_passed += 1
        else:
            print_colored("❌ Database query failed", Colors.RED)
            
        # Cleanup
        os.unlink(db_path)
        
    except Exception as e:
        print_colored(f"❌ Database test error: {e}", Colors.RED)
    
    # Test 4: Configuration loading
    print_colored("\n4. Testing configuration loading...", Colors.BLUE)
    tests_total += 1
    try:
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / "src"))
        
        # Test config manager import
        from utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        trading_config = config_manager.get_trading_config()
        
        if 'symbol' in trading_config:
            print_colored("✅ Configuration manager working", Colors.GREEN)
            tests_passed += 1
        else:
            print_colored("❌ Configuration loading failed", Colors.RED)
            
    except Exception as e:
        print_colored(f"❌ Configuration manager test error: {e}", Colors.RED)
    
    # Test 5: Service module imports
    print_colored("\n5. Testing service module imports...", Colors.BLUE)
    tests_total += 1
    try:
        # Test service imports (without running them)
        service_modules = [
            "portfolio_service",
            "orchestrator_service", 
            "signal_service",
            "data_service",
            "notification_service"
        ]
        
        import_errors = []
        for module in service_modules:
            try:
                __import__(module)
            except ImportError as e:
                import_errors.append(f"{module}: {e}")
        
        if import_errors:
            print_colored(f"❌ Service import errors:", Colors.RED)
            for error in import_errors:
                print_colored(f"  - {error}", Colors.RED)
        else:
            print_colored("✅ All service modules can be imported", Colors.GREEN)
            tests_passed += 1
            
    except Exception as e:
        print_colored(f"❌ Service import test error: {e}", Colors.RED)
    
    # Test 6: Docker configuration
    print_colored("\n6. Testing Docker configuration...", Colors.BLUE)
    tests_total += 1
    try:
        project_root = Path(__file__).parent.parent
        docker_files = [
            "docker-compose.production.yml",
            "docker-compose.agents.yml",
            "Dockerfile"
        ]
        
        missing_docker_files = []
        for docker_file in docker_files:
            docker_path = project_root / docker_file
            if not docker_path.exists():
                missing_docker_files.append(docker_file)
        
        if missing_docker_files:
            print_colored(f"❌ Missing Docker files: {missing_docker_files}", Colors.RED)
        else:
            print_colored("✅ All Docker configuration files present", Colors.GREEN)
            tests_passed += 1
            
    except Exception as e:
        print_colored(f"❌ Docker configuration test error: {e}", Colors.RED)
    
    # Test 7: Deployment scripts
    print_colored("\n7. Testing deployment scripts...", Colors.BLUE)
    tests_total += 1
    try:
        project_root = Path(__file__).parent.parent
        deployment_scripts = [
            "scripts/deploy_hetzner.sh",
            "scripts/setup_hetzner_mcp.sh",
            "scripts/run_tests.sh"
        ]
        
        missing_scripts = []
        for script in deployment_scripts:
            script_path = project_root / script
            if not script_path.exists():
                missing_scripts.append(script)
            elif not os.access(script_path, os.X_OK):
                missing_scripts.append(f"{script} (not executable)")
        
        if missing_scripts:
            print_colored(f"❌ Missing/non-executable scripts: {missing_scripts}", Colors.RED)
        else:
            print_colored("✅ All deployment scripts present and executable", Colors.GREEN)
            tests_passed += 1
            
    except Exception as e:
        print_colored(f"❌ Deployment scripts test error: {e}", Colors.RED)
    
    # Test Results Summary
    print_colored(f"\n📊 Smoke Test Results", Colors.CYAN)
    print_colored("=" * 25, Colors.CYAN)
    print_colored(f"Tests Passed: {tests_passed}/{tests_total}", Colors.GREEN if tests_passed == tests_total else Colors.YELLOW)
    
    if tests_passed == tests_total:
        print_colored("🎉 All smoke tests passed! System is ready for deployment.", Colors.GREEN)
        return True
    else:
        failed_tests = tests_total - tests_passed
        print_colored(f"⚠️  {failed_tests} test(s) failed. Please fix issues before deployment.", Colors.YELLOW)
        return False

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)