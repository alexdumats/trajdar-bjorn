#!/usr/bin/env python3
"""
Test script for Sentry integration.
This script will trigger a test error to verify that Sentry is properly configured.

Usage:
    python scripts/test_sentry.py

Environment variables:
    SENTRY_DSN: The Sentry DSN to use for reporting errors
    SENTRY_ENVIRONMENT: The environment to report errors for (default: development)
    SENTRY_TEST_ERROR: Set to "true" to trigger a test error
"""

import os
import sys
import time
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_sentry():
    """Initialize Sentry with environment variables"""
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn or sentry_dsn == "https://examplePublicKey@o0.ingest.sentry.io/0":
        logger.error("❌ SENTRY_DSN environment variable not set or using default value")
        logger.info("Please set the SENTRY_DSN environment variable to your Sentry DSN")
        return False
    
    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        debug=os.getenv("SENTRY_DEBUG", "false").lower() == "true",
        release=f"sentry-test@1.0.0",
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
        ]
    )
    
    logger.info("✅ Sentry initialized successfully")
    return True

def test_error_capture():
    """Test error capture with Sentry"""
    logger.info("Testing error capture with Sentry...")
    
    # Test message capture
    logger.info("Capturing a test message...")
    sentry_sdk.capture_message("This is a test message from the Sentry test script", level="info")
    
    # Test error capture
    try:
        logger.info("Triggering a test error...")
        # Create a transaction for performance monitoring
        with sentry_sdk.start_transaction(op="test", name="test_error_transaction") as transaction:
            # Add a span
            with sentry_sdk.start_span(op="test.operation", description="Test operation") as span:
                span.set_data("test_key", "test_value")
                # Trigger a division by zero error
                result = 1 / 0
    except Exception as e:
        logger.error(f"Test error triggered: {e}")
        sentry_sdk.capture_exception(e)
        logger.info("✅ Test error captured and sent to Sentry")
        return True
    
    return False

def main():
    """Main function"""
    logger.info("Starting Sentry test script...")
    
    # Initialize Sentry
    if not init_sentry():
        sys.exit(1)
    
    # Test error capture
    if not test_error_capture():
        logger.error("❌ Failed to trigger test error")
        sys.exit(1)
    
    logger.info("✅ Sentry test completed successfully")
    logger.info("Waiting for events to be sent to Sentry...")
    time.sleep(2)  # Give Sentry time to send events
    
    logger.info("Check your Sentry dashboard to verify that the events were received")
    sys.exit(0)

if __name__ == "__main__":
    main()