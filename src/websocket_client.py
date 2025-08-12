#!/usr/bin/env python3
"""
WebSocket Client - Example client for real-time data streaming
Demonstrates how to connect to and use the WebSocket service
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, uri: str = "ws://localhost:8007"):
        """Initialize WebSocket client"""
        self.uri = uri
        self.websocket = None
        self.connected = False
        
        logger.info(f"📱 WebSocket client initialized for {uri}")
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            logger.info("✅ Connected to WebSocket server")
            
            # Start listening for messages
            asyncio.create_task(self.listen())
            
            # Wait for connection confirmation
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket server: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔌 Disconnected from WebSocket server")
    
    async def listen(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"❌ Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"❌ Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 Connection closed by server")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Error in listener: {e}")
            self.connected = False
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle message from server"""
        message_type = message.get("type")
        
        if message_type == "connection_confirmed":
            logger.info(f"🤝 Connection confirmed. Server has {message.get('client_count', 0)} clients")
            
        elif message_type == "subscription_confirmed":
            symbols = message.get("symbols", [])
            logger.info(f"📈 Subscribed to symbols: {symbols}")
            
        elif message_type == "unsubscription_confirmed":
            symbols = message.get("symbols", [])
            logger.info(f"📉 Unsubscribed from symbols: {symbols}")
            
        elif message_type == "price_update":
            data = message.get("data", {})
            timestamp = message.get("timestamp")
            logger.info(f"💰 Price update received at {timestamp}:")
            for symbol, price_info in data.items():
                logger.info(f"  {symbol}: ${price_info.get('price', 0)}")
                
        elif message_type == "price_data":
            data = message.get("data", {})
            timestamp = message.get("timestamp")
            logger.info(f"📊 Current price data at {timestamp}:")
            for symbol, price_info in data.items():
                logger.info(f"  {symbol}: ${price_info.get('price', 0)}")
                
        else:
            logger.info(f"📥 Received message: {message}")
    
    async def subscribe(self, symbols: List[str]):
        """Subscribe to price updates for symbols"""
        if not self.connected:
            logger.warning("⚠️ Not connected to server")
            return
            
        message = {
            "type": "subscribe",
            "symbols": symbols
        }
        await self.websocket.send(json.dumps(message))
        logger.info(f"📤 Sent subscription request for: {symbols}")
    
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from price updates for symbols"""
        if not self.connected:
            logger.warning("⚠️ Not connected to server")
            return
            
        message = {
            "type": "unsubscribe",
            "symbols": symbols
        }
        await self.websocket.send(json.dumps(message))
        logger.info(f"📤 Sent unsubscription request for: {symbols}")
    
    async def request_price_data(self):
        """Request current price data"""
        if not self.connected:
            logger.warning("⚠️ Not connected to server")
            return
            
        message = {
            "type": "get_price_data"
        }
        await self.websocket.send(json.dumps(message))
        logger.info("📤 Requested current price data")

async def main():
    """Example usage of WebSocket client"""
    # Create client
    client = WebSocketClient("ws://localhost:8007")
    
    # Connect to server
    await client.connect()
    
    if client.connected:
        # Subscribe to some symbols
        await client.subscribe(["BTCUSDC", "ETHUSDC", "SOLUSDC"])
        
        # Request current price data
        await client.request_price_data()
        
        # Keep client running for 30 seconds
        logger.info("⏳ Client running for 30 seconds...")
        await asyncio.sleep(30)
        
        # Unsubscribe
        await client.unsubscribe(["BTCUSDC", "ETHUSDC", "SOLUSDC"])
        
        # Disconnect
        await client.disconnect()
    
    logger.info("👋 Client example finished")

if __name__ == "__main__":
    asyncio.run(main())