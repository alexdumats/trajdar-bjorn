#!/usr/bin/env python3
"""
Message Queue Service - Redis-based Pub/Sub for Microservice Communication
Implements message queue functionality for inter-service communication
"""

import redis
import json
import logging
import os
from typing import Dict, Any, Callable, Optional, Union
from datetime import datetime
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageQueue:
    def __init__(self):
        """Initialize Redis connection for message queue"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.fallback_mode = False
        self.redis_client = None
        
        # In-memory structures for fallback mode
        self.memory_channels = {}  # Channel -> list of messages
        self.memory_subscribers = {}  # Channel -> list of callbacks
        self.max_channel_size = int(os.getenv("FALLBACK_MAX_CHANNEL_SIZE", 100))
        
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
            logger.info("✅ Connected to Redis message queue")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Redis: {e}")
            logger.warning("⚠️ Using in-memory fallback message queue")
            self.fallback_mode = True
    
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
                **message
            }
            
            # In fallback mode, store the message in memory
            if self.fallback_mode:
                if channel not in self.memory_channels:
                    self.memory_channels[channel] = []
                
                # Add message to channel with timestamp
                self.memory_channels[channel].append(message_with_metadata)
                
                # Limit channel size to prevent memory issues
                if len(self.memory_channels[channel]) > self.max_channel_size:
                    self.memory_channels[channel].pop(0)  # Remove oldest message
                
                logger.info(f"📤 [FALLBACK] Published to {channel}: {message}")
                
                # Deliver to any subscribers
                if channel in self.memory_subscribers:
                    for callback in self.memory_subscribers[channel]:
                        try:
                            callback(message_with_metadata)
                        except Exception as e:
                            logger.error(f"❌ Error in fallback subscriber callback: {e}")
                
                return True
                
            # Convert to JSON and publish
            message_json = json.dumps(message_with_metadata)
            if self.redis_client:
                self.redis_client.publish(channel, message_json)
                logger.info(f"📤 Published message to {channel}")
            else:
                logger.warning(f"⚠️ Redis client not available for publish operation on channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to publish message to {channel}: {e}")
            return False
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> Optional[threading.Thread]:
        """
        Subscribe to a channel and process messages with a callback function
        
        Args:
            channel: Channel name to subscribe to
            callback: Function to call when message is received
            
        Returns:
            threading.Thread: Subscription thread, or None in fallback mode
        """
        # In fallback mode, register the callback
        if self.fallback_mode:
            if channel not in self.memory_subscribers:
                self.memory_subscribers[channel] = []
            
            self.memory_subscribers[channel].append(callback)
            logger.info(f"📥 [FALLBACK] Subscribed to {channel}")
            
            # Create a dummy thread that does nothing but allows for API compatibility
            class FallbackSubscriptionThread(threading.Thread):
                def __init__(self):
                    super().__init__(daemon=True)
                    self.running = True
                
                def run(self):
                    while self.running:
                        time.sleep(1)
                
                def stop(self):
                    self.running = False
            
            thread = FallbackSubscriptionThread()
            thread.start()
            return thread
            
        def subscription_worker():
            try:
                if not self.redis_client:
                    logger.warning(f"⚠️ Redis client not available for subscription worker on channel: {channel}")
                    return
                    
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
    
    def publish_trade_signal(self, symbol: str, side: str, confidence: float, strategy: str) -> bool:
        """Publish a trade signal message"""
        message = {
            "type": "trade_signal",
            "symbol": symbol,
            "side": side,
            "confidence": confidence,
            "strategy": strategy
        }
        return self.publish("trade_signals", message)
    
    def publish_price_update(self, symbol: str, price: float, timestamp: str) -> bool:
        """Publish a price update message"""
        message = {
            "type": "price_update",
            "symbol": symbol,
            "price": price,
            "timestamp": timestamp
        }
        return self.publish("price_updates", message)
    
    def publish_risk_alert(self, alert_type: str, message: str, severity: str) -> bool:
        """Publish a risk alert message"""
        alert_message = {
            "type": "risk_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        return self.publish("risk_alerts", alert_message)
    
    def publish_performance_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Publish performance metrics message"""
        message = {
            "type": "performance_metrics",
            "metrics": metrics
        }
        return self.publish("performance_metrics", message)

# Global message queue instance
message_queue = MessageQueue()

if __name__ == "__main__":
    # Example usage
    mq = MessageQueue()
    
    # Example publisher
    def publish_example():
        mq.publish_trade_signal("BTCUSDC", "BUY", 0.85, "RSI")
        mq.publish_price_update("BTCUSDC", 50000.0, datetime.now().isoformat())
        mq.publish_risk_alert("high_volatility", "Market volatility exceeded threshold", "HIGH")
        
        metrics = {
            "portfolio_value": 10500.0,
            "daily_pnl": 250.0,
            "win_rate": 0.65
        }
        mq.publish_performance_metrics(metrics)
    
    # Example subscriber
    def handle_trade_signal(message):
        print(f"Received trade signal: {message}")
    
    def handle_price_update(message):
        print(f"Received price update: {message}")
    
    # Subscribe to channels
    mq.subscribe("trade_signals", handle_trade_signal)
    mq.subscribe("price_updates", handle_price_update)
    
    # Publish some example messages
    publish_example()
    
    # Keep the program running to receive messages
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")