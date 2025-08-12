#!/usr/bin/env python3
"""
Test script to verify the portfolio service works with Redis fallback modes.
This script tests the portfolio service's ability to function without Redis.
"""

import sys
import os
import logging
import time
from datetime import datetime
import requests

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("portfolio_service_test")

def test_portfolio_service_directly():
    """Test the portfolio service directly by importing it"""
    logger.info("Testing portfolio service directly...")
    
    try:
        from portfolio_service import portfolio_manager
        
        # Test getting portfolio
        logger.info("Getting portfolio...")
        portfolio = portfolio_manager.get_portfolio()
        logger.info(f"Portfolio: {portfolio}")
        
        # Test getting performance summary
        logger.info("Getting performance summary...")
        performance = portfolio_manager.get_performance_summary()
        logger.info(f"Performance summary: {performance}")
        
        # Test getting cache stats
        logger.info("Getting cache stats...")
        from cache import cache
        cache_stats = cache.get_cache_stats()
        logger.info(f"Cache stats: {cache_stats}")
        
        if portfolio and performance:
            logger.info("✅ Portfolio service direct test passed")
            return True
        else:
            logger.error("❌ Portfolio service direct test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing portfolio service directly: {e}")
        return False

def test_portfolio_service_api():
    """Test the portfolio service API by starting the service and making requests"""
    logger.info("Testing portfolio service API...")
    
    # Start the portfolio service in a separate process
    import subprocess
    import time
    
    # Initialize process variable
    process = None
    
    try:
        # Start the portfolio service
        logger.info("Starting portfolio service...")
        process = subprocess.Popen(
            ["python", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "portfolio_service.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the service to start
        logger.info("Waiting for service to start...")
        time.sleep(5)
        
        # Test the API
        base_url = "http://localhost:8001"
        
        # Test health endpoint
        logger.info("Testing health endpoint...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        logger.info(f"Health response: {health_response.json()}")
        
        # Test portfolio endpoint
        logger.info("Testing portfolio endpoint...")
        portfolio_response = requests.get(f"{base_url}/portfolio", timeout=10)
        logger.info(f"Portfolio response: {portfolio_response.json()}")
        
        # Test cache stats endpoint
        logger.info("Testing cache stats endpoint...")
        cache_stats_response = requests.get(f"{base_url}/cache-stats", timeout=10)
        logger.info(f"Cache stats response: {cache_stats_response.json()}")
        
        # Stop the service
        logger.info("Stopping portfolio service...")
        process.terminate()
        process.wait(timeout=5)
        
        if health_response.status_code == 200 and portfolio_response.status_code == 200:
            logger.info("✅ Portfolio service API test passed")
            return True
        else:
            logger.error("❌ Portfolio service API test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing portfolio service API: {e}")
        # Make sure to terminate the process if it's still running
        try:
            if 'process' in locals() and process is not None:
                process.terminate()
                process.wait(timeout=5)
        except Exception as term_error:
            logger.error(f"Error terminating process: {term_error}")
        return False

def main():
    """Main test function"""
    logger.info("Starting portfolio service tests with Redis fallback mode...")
    
    # Test portfolio service directly
    direct_result = test_portfolio_service_directly()
    
    # Test portfolio service API
    api_result = test_portfolio_service_api()
    
    # Print summary
    logger.info("\n--- Test Summary ---")
    logger.info(f"Portfolio Service Direct Test: {'✅ PASS' if direct_result else '❌ FAIL'}")
    logger.info(f"Portfolio Service API Test: {'✅ PASS' if api_result else '❌ FAIL'}")
    
    if direct_result and api_result:
        logger.info("✅ All portfolio service tests passed with Redis fallback mode")
        return 0
    else:
        logger.error("❌ Some portfolio service tests failed with Redis fallback mode")
        return 1

if __name__ == "__main__":
    sys.exit(main())