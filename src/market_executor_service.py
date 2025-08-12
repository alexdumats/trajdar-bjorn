#!/usr/bin/env python3
"""
Trade Executor Agent - AI-Powered Fast Order Execution and Compliance
Uses phi3 for fast order placement and compliance checks
Connects to broker/exchange MCPs (Alpaca, Composer Trade MCP, Trade-Agent MCP)
"""

import asyncio
import aiohttp
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
import uvicorn

# Import centralized configuration manager
try:
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.config_manager import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trade Executor Agent", version="3.0.0")

class TradeExecutorAgent:
    def __init__(self):
        # Ollama configuration for phi3 (fast execution model)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = "phi3"  # Fast model for quick execution decisions
        
        # MCP connections for Trade Executor
        self.alpaca_mcp = os.getenv("ALPACA_MCP_URL", "http://localhost:8211")
        self.composer_trade_mcp = os.getenv("COMPOSER_TRADE_MCP_URL", "http://localhost:8212")
        self.trade_agent_mcp = os.getenv("TRADE_AGENT_MCP_URL", "http://localhost:8213")
        
        # Centralized configuration
        try:
            from utils.config_manager import get_config
            self.config_manager = get_config()
            execution_config = self.config_manager.get_execution_config()
            risk_config = self.config_manager.get_risk_management_config()
        except ImportError:
            logger.warning("Config manager not available, using defaults")
            self.config_manager = None
            execution_config = {}
            risk_config = {}
        
        # Execution parameters
        self.max_position_size = risk_config.get('max_position_size', 0.25)
        self.stop_loss_pct = risk_config.get('stop_loss_pct', 0.03)
        self.take_profit_pct = risk_config.get('take_profit_pct', 0.06)
        self.min_confidence = risk_config.get('min_confidence', 0.6)
        
        # Trade execution state
        self.pending_orders = {}
        self.execution_history = []
        self.compliance_cache = {}
        
        logger.info("⚡ Trade Executor Agent initialized with phi3")
    
    async def get_ai_compliance_check(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI compliance check from phi3 for fast execution decisions"""
        try:
            prompt = f"""
            You are a fast trade execution compliance checker. 
            Review this trade request for compliance and risk:
            
            Trade Request: {json.dumps(trade_request, indent=2)}
            
            Check for:
            1. Position size compliance (max 25% per trade)
            2. Risk parameters within limits
            3. Market conditions suitability
            4. Execution timing appropriateness
            
            Respond with JSON: {{"approved": boolean, "confidence": float, "reasons": ["reason1", "reason2"]}}
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_response = result.get('response', '')
                        
                        try:
                            compliance_data = json.loads(ai_response)
                        except json.JSONDecodeError:
                            # Fallback if AI doesn't return valid JSON
                            compliance_data = {
                                "approved": True,
                                "confidence": 0.5,
                                "reasons": ["AI parsing failed, using fallback approval"]
                            }
                        
                        compliance_data.update({
                            "timestamp": datetime.now().isoformat(),
                            "model_used": self.model,
                            "agent": "trade_executor"
                        })
                        
                        return compliance_data
                    else:
                        return self.get_fallback_compliance(trade_request)
                        
        except Exception as e:
            logger.error(f"AI compliance check failed: {e}")
            return self.get_fallback_compliance(trade_request)
    
    def get_fallback_compliance(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback compliance check when AI is unavailable"""
        # Simple rule-based compliance check
        position_size = trade_request.get('position_size', 0)
        trade_type = trade_request.get('side', '')
        
        # Basic compliance rules
        approved = True
        reasons = []
        
        if position_size > self.max_position_size:
            approved = False
            reasons.append(f"Position size {position_size} exceeds limit {self.max_position_size}")
        
        if trade_type not in ['BUY', 'SELL']:
            approved = False
            reasons.append(f"Invalid trade type: {trade_type}")
        
        return {
            "approved": approved,
            "confidence": 0.8 if approved else 0.2,
            "reasons": reasons if reasons else ["Basic compliance checks passed"],
            "timestamp": datetime.now().isoformat(),
            "model_used": "fallback_rules",
            "agent": "trade_executor"
        }
    
    async def execute_via_mcp(self, trade_request: Dict[str, Any], mcp_endpoint: str) -> Dict[str, Any]:
        """Execute trade via specific MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{mcp_endpoint}/execute_trade",
                    json=trade_request,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"MCP execution failed: HTTP {response.status}"}
        except Exception as e:
            logger.error(f"MCP execution error: {e}")
            return {"error": str(e)}
    
    async def execute_trade_order(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade order with AI compliance and MCP routing"""
        try:
            # Step 1: AI Compliance Check with phi3
            compliance = await self.get_ai_compliance_check(trade_request)
            
            if not compliance.get('approved', False):
                return {
                    "success": False,
                    "error": "Compliance check failed",
                    "compliance": compliance,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Route to appropriate MCP based on symbol/exchange
            symbol = trade_request.get('symbol', '')
            
            # Determine best MCP for execution (priority order)
            mcp_endpoints = [
                self.alpaca_mcp,      # Primary: Alpaca for stocks/crypto
                self.trade_agent_mcp,  # Secondary: Trade Agent MCP
                self.composer_trade_mcp # Tertiary: Composer Trade MCP
            ]
            
            execution_result = None
            last_error = None
            
            # Try each MCP endpoint until successful
            for mcp_endpoint in mcp_endpoints:
                try:
                    result = await self.execute_via_mcp(trade_request, mcp_endpoint)
                    if not result.get('error'):
                        execution_result = result
                        execution_result['mcp_used'] = mcp_endpoint
                        break
                    else:
                        last_error = result.get('error')
                        logger.warning(f"MCP {mcp_endpoint} failed: {last_error}")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"MCP {mcp_endpoint} exception: {e}")
            
            if not execution_result:
                return {
                    "success": False,
                    "error": f"All MCP endpoints failed. Last error: {last_error}",
                    "compliance": compliance,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Log successful execution
            execution_record = {
                "trade_id": execution_result.get('trade_id'),
                "symbol": symbol,
                "side": trade_request.get('side'),
                "quantity": execution_result.get('quantity'),
                "price": execution_result.get('price'),
                "mcp_used": execution_result.get('mcp_used'),
                "compliance": compliance,
                "timestamp": datetime.now().isoformat()
            }
            
            self.execution_history.append(execution_record)
            # Keep only last 1000 executions
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            logger.info(f"✅ Trade executed: {symbol} {trade_request.get('side')} via {execution_result.get('mcp_used')}")
            
            return {
                "success": True,
                "execution_result": execution_result,
                "compliance": compliance,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_trade_signal(self, trade_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming trade signal and execute if approved by AI"""
        try:
            # Extract signal information
            symbol = trade_signal.get('symbol', '')
            side = trade_signal.get('side', '')
            quantity = trade_signal.get('quantity', 0)
            price = trade_signal.get('price', 0)
            signal_source = trade_signal.get('source', 'unknown')
            
            # Prepare trade request for AI compliance check
            trade_request = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "position_size": quantity / 10000.0 if quantity > 0 else 0.1,  # Estimate position size
                "signal_source": signal_source,
                "timestamp": datetime.now().isoformat()
            }
            
            # Execute trade with AI compliance and MCP routing
            execution_result = await self.execute_trade_order(trade_request)
            
            if execution_result.get('success'):
                logger.info(f"✅ Trade signal processed: {symbol} {side}")
                return {
                    "status": "executed",
                    "symbol": symbol,
                    "side": side,
                    "execution_result": execution_result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"⚠️ Trade signal rejected: {execution_result.get('error')}")
                return {
                    "status": "rejected",
                    "symbol": symbol,
                    "side": side,
                    "error": execution_result.get('error'),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Trade signal processing error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_pending_orders(self) -> Dict[str, Any]:
        """Get all pending orders from connected MCPs"""
        pending_orders = {}
        
        mcp_endpoints = [
            self.alpaca_mcp,
            self.trade_agent_mcp, 
            self.composer_trade_mcp
        ]
        
        for mcp_endpoint in mcp_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{mcp_endpoint}/orders", timeout=5) as response:
                        if response.status == 200:
                            orders = await response.json()
                            pending_orders[mcp_endpoint] = orders
            except Exception as e:
                logger.warning(f"Failed to get orders from {mcp_endpoint}: {e}")
        
        return pending_orders

# Global trade executor agent instance
trade_executor = TradeExecutorAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trade-executor-agent",
        "model": trade_executor.model,
        "timestamp": datetime.now().isoformat(),
        "executions_today": len(trade_executor.execution_history),
        "pending_orders": len(trade_executor.pending_orders)
    }

@app.get("/status")
async def get_status():
    """Get detailed executor status"""
    return {
        "service": "trade-executor-agent",
        "model": trade_executor.model,
        "mcp_endpoints": {
            "alpaca": trade_executor.alpaca_mcp,
            "composer_trade": trade_executor.composer_trade_mcp,
            "trade_agent": trade_executor.trade_agent_mcp
        },
        "execution_history": len(trade_executor.execution_history),
        "recent_executions": trade_executor.execution_history[-5:] if trade_executor.execution_history else [],
        "pending_orders": trade_executor.pending_orders,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/execute-trade")
async def execute_trade_endpoint(trade_signal: Dict[str, Any]):
    """Execute trade from trade signal"""
    try:
        result = await trade_executor.process_trade_signal(trade_signal)
        return result
    except Exception as e:
        logger.error(f"Trade execution endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compliance-check")
async def compliance_check_endpoint(trade_request: Dict[str, Any]):
    """Check trade compliance with AI"""
    try:
        compliance = await trade_executor.get_ai_compliance_check(trade_request)
        return compliance
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending-orders")
async def get_pending_orders_endpoint():
    """Get pending orders from all MCP endpoints"""
    try:
        pending_orders = await trade_executor.get_pending_orders()
        return {
            "pending_orders": pending_orders,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get pending orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/execution-history")
async def get_execution_history(limit: int = 50):
    """Get recent execution history"""
    try:
        recent_history = trade_executor.execution_history[-limit:] if trade_executor.execution_history else []
        return {
            "execution_history": recent_history,
            "total_executions": len(trade_executor.execution_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get execution history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("TRADE_EXECUTOR_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)