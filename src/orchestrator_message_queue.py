#!/usr/bin/env python3
"""
Message Queue Client for Orchestrator Service
Implements Redis-based Pub/Sub for orchestrator to agent communication
"""

import redis
import json
import logging
import os
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorMessageQueue:
    def __init__(self):
        """Initialize Redis connection for message queue"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis message queue for orchestrator")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a channel
        
        Args:
            channel: Channel name to publish to
            message: Message payload as dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp and metadata
            message_with_metadata = {
                "timestamp": datetime.now().isoformat(),
                "channel": channel,
                "source": "orchestrator",
                **message
            }
            
            # Convert to JSON and publish
            message_json = json.dumps(message_with_metadata)
            self.redis_client.publish(channel, message_json)
            logger.info(f"📤 Published message to {channel}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to publish message to {channel}: {e}")
            return False
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> threading.Thread:
        """
        Subscribe to a channel and process messages with a callback function
        
        Args:
            channel: Channel name to subscribe to
            callback: Function to call when message is received
            
        Returns:
            threading.Thread: Subscription thread
        """
        def subscription_worker():
            try:
                pubsub = self.redis_client.pubsub()
                pubsub.subscribe(channel)
                logger.info(f"📥 Subscribed to {channel}")
                
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            # Parse JSON message
                            data = json.loads(message['data'])
                            # Call callback function
                            callback(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Failed to parse message: {e}")
                        except Exception as e:
                            logger.error(f"❌ Error in callback: {e}")
            except Exception as e:
                logger.error(f"❌ Subscription error for {channel}: {e}")
        
        # Start subscription in a separate thread
        thread = threading.Thread(target=subscription_worker, daemon=True)
        thread.start()
        return thread
    
    def publish_trade_signal(self, symbol: str, side: str, confidence: float, strategy: str, risk_assessment: Optional[Dict] = None, market_analysis: Optional[Dict] = None) -> bool:
        """Publish a trade signal message"""
        message = {
            "type": "trade_signal",
            "symbol": symbol,
            "side": side,
            "confidence": confidence,
            "strategy": strategy,
            "risk_assessment": risk_assessment,
            "market_analysis": market_analysis
        }
        return self.publish("trade_signals", message)
    
    def publish_risk_assessment_request(self) -> bool:
        """Publish a risk assessment request"""
        message = {
            "type": "risk_assessment_request"
        }
        return self.publish("risk_manager_requests", message)
    
    def publish_market_analysis_request(self) -> bool:
        """Publish a market analysis request"""
        message = {
            "type": "market_analysis_request"
        }
        return self.publish("analyst_requests", message)
    
    def publish_trade_execution_request(self, trade_signal: Dict[str, Any]) -> bool:
        """Publish a trade execution request"""
        message = {
            "type": "trade_execution_request",
            "trade_signal": trade_signal
        }
        return self.publish("trade_executor_requests", message)
    
    def publish_parameter_optimization_request(self) -> bool:
        """Publish a parameter optimization request"""
        message = {
            "type": "parameter_optimization_request"
        }
        return self.publish("parameter_optimizer_requests", message)

# Global message queue instance for orchestrator
orchestrator_mq = OrchestratorMessageQueue()

if __name__ == "__main__":
    # Example usage
    mq = OrchestratorMessageQueue()
    
    # Example publisher
    def publish_example():
        # Publish trade signal
        mq.publish_trade_signal("BTCUSDC", "BUY", 0.85, "RSI")
        
        # Publish requests
        mq.publish_risk_assessment_request()
        mq.publish_market_analysis_request()
        mq.publish_parameter_optimization_request()
        
        # Publish trade execution request
        trade_signal = {
            "symbol": "BTCUSDC",
            "side": "BUY",
            "confidence": 0.85,
            "strategy": "RSI"
        }
        mq.publish_trade_execution_request(trade_signal)
    
    # Example subscriber callback
    def handle_response(message):
        print(f"Received response: {message}")
    
    # Subscribe to response channels
    mq.subscribe("risk_manager_responses", handle_response)
    mq.subscribe("analyst_responses", handle_response)
    mq.subscribe("trade_executor_responses", handle_response)
    mq.subscribe("parameter_optimizer_responses", handle_response)
    
    # Publish example messages
    publish_example()
    
    # Keep the program running to receive messages
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")