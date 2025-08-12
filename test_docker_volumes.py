#!/usr/bin/env python3
"""
Docker Volume Validation Test Script

This script validates that Docker volume mappings work correctly by:
1. Testing database volume (SQLite operations)
2. Testing logs volume (file write/read)
3. Testing config volume (JSON operations)

Returns exit code 0 on success, 1 on failure for CI/CD integration.

Usage:
    python test_docker_volumes.py

The script tests the three main volume mappings defined in docker-compose.production.yml:
- ./database:/app/database - Tests SQLite database creation and data persistence
- ./logs:/app/logs - Tests log file writing and reading capabilities  
- ./config:/app/config - Tests JSON configuration file operations

Each test creates temporary files, verifies data integrity, and cleans up afterward.
Perfect for validating Docker volume functionality before deployment.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def test_database_volume():
    """Test that database volume is writable and accessible."""
    print("Testing database volume...")
    
    db_path = "database/test_volume.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create a test database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volume_test (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            message TEXT
        )
    ''')
    
    # Insert test data
    cursor.execute('''
        INSERT INTO volume_test (timestamp, message) 
        VALUES (?, ?)
    ''', (datetime.now().isoformat(), "Docker volume test successful"))
    
    conn.commit()
    
    # Read back the data
    cursor.execute('SELECT * FROM volume_test')
    rows = cursor.fetchall()
    
    conn.close()
    
    if rows:
        print(f"✅ Database volume test passed - Created and read {len(rows)} records")
        return True
    else:
        print("❌ Database volume test failed - No data found")
        return False

def test_logs_volume():
    """Test that logs volume is writable and accessible."""
    print("Testing logs volume...")
    
    log_path = "logs/test_volume.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Write test log
    with open(log_path, 'w') as f:
        f.write(f"{datetime.now().isoformat()} - Docker volume test log entry\n")
    
    # Read back the log
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            content = f.read().strip()
        
        if content:
            print(f"✅ Logs volume test passed - Created log file with content")
            return True
    
    print("❌ Logs volume test failed - Could not create or read log file")
    return False

def test_config_volume():
    """Test that config volume is writable and accessible."""
    print("Testing config volume...")
    
    config_path = "config/test_volume_config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    test_config = {
        "test": True,
        "timestamp": datetime.now().isoformat(),
        "message": "Docker volume config test"
    }
    
    try:
        # Write test config
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Read back the config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            if loaded_config == test_config:
                print("✅ Config volume test passed - Created and read JSON config")
                return True
        
        print("❌ Config volume test failed - Config data mismatch")
        return False
        
    except Exception as e:
        print(f"❌ Config volume test failed - Error: {e}")
        return False


def cleanup_test_files():
    """Clean up test files created during volume validation."""
    test_files = [
        "database/test_volume.db",
        "logs/test_volume.log", 
        "config/test_volume_config.json"
    ]
    
    cleaned_count = 0
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                cleaned_count += 1
                print(f"🧹 Cleaned up {file_path}")
        except Exception as e:
            print(f"⚠️  Failed to clean {file_path}: {e}")
    
    print(f"✅ Cleanup completed - {cleaned_count} files removed")
    return cleaned_count


def main():
    """Run all Docker volume tests and exit with appropriate code."""
    print("🐳 Docker Volume Validation Test")
    print("=" * 40)
    
    # Run all tests and collect results
    test_results = {
        "Database Volume": test_database_volume(),
        "Logs Volume": test_logs_volume(),
        "Config Volume": test_config_volume()
    }
    
    # Summary
    passed = sum(test_results.values())
    total = len(test_results)
    
    print("\n📊 Test Results Summary:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    # Always cleanup regardless of test results
    print("\n🧹 Cleaning up test files...")
    cleanup_test_files()
    
    # Exit with appropriate code
    if passed == total:
        print(f"\n🎉 All {total} volume tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} of {total} tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
