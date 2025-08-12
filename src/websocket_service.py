#!/usr/bin/env python3
"""
WebSocket Service - Real-time Data Streaming
Implements WebSocket connections for real-time market data and trading updates
"""

import asyncio
import websockets
import json
import logging
import os
import requests
from typing import Dict, Any, Set, Optional
from datetime import datetime
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        """Initialize WebSocket service"""
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.binance_api = os.getenv("BINANCE_API_URL", "https://api.binance.com/api/v3")
        self.binance_ws_url = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")
        self.running = False
        self.price_data = {}
        self.subscribed_symbols = set()
        
        logger.info("🔌 WebSocket service initialized")
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"👤 Client connected. Total clients: {len(self.clients)}")
        
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "connection_confirmed",
            "timestamp": datetime.now().isoformat(),
            "client_count": len(self.clients)
        }))
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"👤 Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            # Convert to JSON string once
            message_str = json.dumps(message)
            
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"❌ Invalid JSON received from client: {message}")
                except Exception as e:
                    logger.error(f"❌ Error handling client message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 Client connection closed")
        except Exception as e:
            logger.error(f"❌ Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """Handle message from client"""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            symbols = message.get("symbols", [])
            for symbol in symbols:
                self.subscribed_symbols.add(symbol.upper())
            logger.info(f"📈 Subscribed to symbols: {symbols}")
            
            # Confirm subscription
            await websocket.send(json.dumps({
                "type": "subscription_confirmed",
                "symbols": list(self.subscribed_symbols),
                "timestamp": datetime.now().isoformat()
            }))
            
        elif message_type == "unsubscribe":
            symbols = message.get("symbols", [])
            for symbol in symbols:
                self.subscribed_symbols.discard(symbol.upper())
            logger.info(f"📉 Unsubscribed from symbols: {symbols}")
            
            # Confirm unsubscription
            await websocket.send(json.dumps({
                "type": "unsubscription_confirmed",
                "symbols": list(self.subscribed_symbols),
                "timestamp": datetime.now().isoformat()
            }))
            
        elif message_type == "get_price_data":
            # Send current price data
            await websocket.send(json.dumps({
                "type": "price_data",
                "data": self.price_data,
                "timestamp": datetime.now().isoformat()
            }))
    
    async def fetch_binance_prices(self):
        """Fetch current prices from Binance API"""
        if not self.subscribed_symbols:
            return
            
        try:
            # Fetch prices for all subscribed symbols
            symbols_list = list(self.subscribed_symbols)
            if len(symbols_list) == 1:
                # Single symbol request
                symbol = symbols_list[0]
                url = f"{self.binance_api}/ticker/price"
                params = {"symbol": symbol}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                price = float(data["price"])
                self.price_data[symbol] = {
                    "price": price,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Multiple symbols request
                url = f"{self.binance_api}/ticker/price"
                params = {"symbols": json.dumps(symbols_list)}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                for item in data:
                    symbol = item["symbol"]
                    price = float(item["price"])
                    self.price_data[symbol] = {
                        "price": price,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            # Broadcast price updates
            await self.broadcast({
                "type": "price_update",
                "data": self.price_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error fetching Binance prices: {e}")
    
    async def start_price_updates(self):
        """Start periodic price updates"""
        while self.running:
            try:
                await self.fetch_binance_prices()
                # Wait 5 seconds between updates
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Error in price update loop: {e}")
                await asyncio.sleep(5)
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8007):
        """Start WebSocket server"""
        self.running = True
        
        # Start price update task
        price_task = asyncio.create_task(self.start_price_updates())
        
        # Start WebSocket server
        server = await websockets.serve(self.handle_client, host, port)
        logger.info(f"🚀 WebSocket server started on {host}:{port}")
        
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            logger.info("🛑 WebSocket server shutting down...")
        finally:
            self.running = False
            price_task.cancel()
            server.close()
            await server.wait_closed()

# Global WebSocket service instance
websocket_service = WebSocketService()

if __name__ == "__main__":
    # Example usage
    async def main():
        # Start WebSocket server
        await websocket_service.start_server()
    
    # Run the server
    asyncio.run(main())