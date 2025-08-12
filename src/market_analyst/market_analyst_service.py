#!/usr/bin/env python3
"""
Market Analyst Agent - AI-Powered Market Analysis
Uses mistral7b:latest for intelligent market analysis
Connects to Market Data MCPs and Slack MCP for notifications
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
import requests
import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import os
import uvicorn
import yaml
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Analyst Agent", version="3.0.0")

class MarketAnalystAgent:
    def __init__(self):
        # Load configuration
        self.config_path = os.getenv("CONFIG_PATH", "config/production_config.yaml")
        self.load_config()
        
        # Ollama configuration for mistral7b:latest
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = "mistral7b:latest"
        
        # Analysis scheduling
        self.analysis_interval = int(os.getenv("MARKET_ANALYSIS_INTERVAL", "300"))  # 5 minutes
        self.last_analysis = None
        self.analysis_history = []
        self.is_running = False
        self.scheduler_task = None
        
        # Slack MCP configuration
        self.slack_channel = "#market-analyst"
        
        logger.info("📊 Market Analyst Agent initialized with mistral7b:latest")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
    
    async def start_analysis_scheduler(self):
        """Start the market analysis scheduler"""
        if self.scheduler_task:
            return {"message": "Scheduler already running"}
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self.analysis_loop())
        
        # Notify Slack about startup
        await self.notify_slack("🚀 Market Analyst Agent started", "startup")
        
        logger.info("🚀 Market analysis scheduler started")
        return {"message": "Market analysis scheduler started", "interval": self.analysis_interval}
    
    async def stop_analysis_scheduler(self):
        """Stop the market analysis scheduler"""
        if not self.scheduler_task:
            return {"message": "Scheduler not running"}
        
        self.is_running = False
        self.scheduler_task.cancel()
        self.scheduler_task = None
        
        # Notify Slack about shutdown
        await self.notify_slack("⏹️ Market Analyst Agent stopped", "shutdown")
        
        logger.info("⏹️ Market analysis scheduler stopped")
        return {"message": "Market analysis scheduler stopped"}
    
    async def analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                # Perform market analysis
                analysis = await self.perform_market_analysis()
                
                if analysis and not analysis.get("error"):
                    # Notify Slack with analysis results
                    await self.notify_slack_analysis(analysis)
                
                # Wait for next analysis
                await asyncio.sleep(self.analysis_interval)
                
            except asyncio.CancelledError:
                logger.info("Analysis loop cancelled")
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def perform_market_analysis(self) -> Dict[str, Any]:
        """Perform AI-powered market analysis"""
        try:
            # Get market data from MCPs
            market_data = await self.get_market_data_from_mcps()
            
            # Prepare context for AI analysis
            analysis_context = {
                "market_data": market_data,
                "analysis_type": "market",
                "timestamp": datetime.now().isoformat(),
                "config": self.config.get("trading", {})
            }
            
            # Get AI market analysis from mistral7b
            analysis = await self.get_ai_analysis(analysis_context)
            
            self.last_analysis = analysis
            self.analysis_history.append(analysis)
            
            # Keep only last 100 analyses
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
            
            logger.info("📊 Market analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"error": str(e), "type": "market_analysis_error"}
    
    async def get_ai_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered market analysis from mistral7b:latest"""
        try:
            # Extract trading parameters from config
            trading_config = context.get("config", {})
            risk_config = trading_config.get("risk_management", {})
            
            prompt = f"""
            You are an expert cryptocurrency market analyst. Analyze the following market data and provide actionable insights:
            
            Market Data: {json.dumps(context['market_data'], indent=2)}
            
            Trading Configuration:
            - Symbol: {trading_config.get('symbol', 'BTCUSDC')}
            - Max Position Size: {risk_config.get('max_position_size', 0.1)}
            - Stop Loss: {risk_config.get('stop_loss_percentage', 0.05)}
            - Take Profit: {risk_config.get('take_profit_percentage', 0.1)}
            
            Provide a comprehensive market analysis including:
            1. Overall market sentiment (BULLISH/BEARISH/NEUTRAL)
            2. Key price levels and support/resistance
            3. Volume analysis and momentum indicators
            4. Short-term and medium-term outlook
            5. Risk factors and opportunities
            6. Trading recommendation (BUY/SELL/HOLD)
            7. Confidence level (0.0 to 1.0)
            8. Position size recommendation based on risk parameters
            
            Respond in JSON format with the following structure:
            {{
                "sentiment": "BULLISH|BEARISH|NEUTRAL",
                "recommendation": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "key_levels": {{"support": price, "resistance": price}},
                "outlook": {{"short_term": "description", "medium_term": "description"}},
                "risk_factors": ["factor1", "factor2"],
                "opportunities": ["opportunity1", "opportunity2"],
                "position_size": 0.0-1.0,
                "reasoning": "detailed explanation"
            }}
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
                        
                        # Parse AI response
                        try:
                            analysis_data = json.loads(ai_response)
                        except json.JSONDecodeError:
                            # Fallback if AI doesn't return valid JSON
                            analysis_data = {
                                "sentiment": "NEUTRAL",
                                "recommendation": "HOLD",
                                "confidence": 0.5,
                                "raw_response": ai_response,
                                "parsed": False
                            }
                        
                        analysis_data.update({
                            "timestamp": datetime.now().isoformat(),
                            "model_used": self.model,
                            "agent": "market_analyst",
                            "analysis_type": "market"
                        })
                        
                        return analysis_data
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return self.get_fallback_analysis()
                        
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self.get_fallback_analysis()
    
    def get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        return {
            "sentiment": "NEUTRAL",
            "recommendation": "HOLD",
            "confidence": 0.5,
            "key_levels": {"support": 0, "resistance": 0},
            "outlook": {"short_term": "Uncertain", "medium_term": "Uncertain"},
            "risk_factors": ["AI unavailable"],
            "opportunities": [],
            "position_size": 0.0,
            "reasoning": "Fallback analysis - AI model unavailable",
            "timestamp": datetime.now().isoformat(),
            "model_used": "fallback_rules",
            "agent": "market_analyst"
        }
    
    async def get_market_data_from_mcps(self) -> Dict[str, Any]:
        """Get market data from various MCP sources"""
        market_data = {}
        
        try:
            # This would connect to actual MCP servers
            # For now, using mock data
            market_data = self.get_mock_market_data()
        
        except Exception as e:
            logger.error(f"Failed to get market data from MCPs: {e}")
            market_data = self.get_mock_market_data()
        
        return market_data
    
    def get_mock_market_data(self) -> Dict[str, Any]:
        """Mock market data for testing"""
        import random
        base_price = 45000
        price_change = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_change)
        
        return {
            "prices": {
                "BTCUSDC": {
                    "price": current_price,
                    "volume": random.uniform(800000, 1200000),
                    "change_24h": price_change * 100
                },
                "ETHUSDC": {
                    "price": 3000 * (1 + price_change * 0.8),
                    "volume": random.uniform(400000, 600000),
                    "change_24h": price_change * 80
                }
            },
            "indicators": {
                "rsi": random.uniform(30, 70),
                "macd": random.uniform(-100, 100),
                "volume_ratio": random.uniform(0.8, 1.5)
            },
            "timestamp": datetime.now().isoformat(),
            "source": "mock_data"
        }
    
    async def notify_slack(self, message: str, event_type: str = "info"):
        """Send notification to Slack via MCP"""
        try:
            # This would use the Slack MCP server
            # For now, just log the message
            logger.info(f"Slack notification ({event_type}): {message}")
            
            # TODO: Implement actual Slack MCP call
            # await self.call_slack_mcp("conversations_add_message", {
            #     "channel_id": self.slack_channel,
            #     "payload": message,
            #     "content_type": "text/markdown"
            # })
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def notify_slack_analysis(self, analysis: Dict[str, Any]):
        """Send analysis results to Slack"""
        try:
            sentiment = analysis.get("sentiment", "UNKNOWN")
            recommendation = analysis.get("recommendation", "HOLD")
            confidence = analysis.get("confidence", 0.0)
            
            # Format analysis message
            message = f"""📊 **Market Analysis Update**

🎯 **Sentiment**: {sentiment}
💡 **Recommendation**: {recommendation}
📈 **Confidence**: {confidence:.1%}

🔍 **Key Insights**:
{analysis.get('reasoning', 'No detailed reasoning available')}

⏰ **Analysis Time**: {datetime.now().strftime('%H:%M:%S')}
🤖 **Model**: {analysis.get('model_used', 'Unknown')}
"""
            
            await self.notify_slack(message, "analysis")
            
        except Exception as e:
            logger.error(f"Failed to send analysis to Slack: {e}")

# Global market analyst agent instance
market_analyst = MarketAnalystAgent()

@app.on_event("startup")
async def startup_event():
    """Start the analysis scheduler when FastAPI starts"""
    await market_analyst.start_analysis_scheduler()

@app.on_event("shutdown")  
async def shutdown_event():
    """Clean up scheduler task on shutdown"""
    await market_analyst.stop_analysis_scheduler()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "market-analyst-agent",
        "is_running": market_analyst.is_running,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analysis")
async def get_current_analysis():
    """Get current market analysis from AI agent"""
    try:
        if not market_analyst.last_analysis:
            # Trigger analysis if none exists
            analysis = await market_analyst.perform_market_analysis()
        else:
            analysis = market_analyst.last_analysis
            
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-analysis")
async def trigger_analysis():
    """Manually trigger market analysis"""
    try:
        analysis = await market_analyst.perform_market_analysis()
        return {
            "message": "Analysis triggered successfully",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error triggering analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-scheduler")
async def start_scheduler():
    """Start the analysis scheduler"""
    try:
        result = await market_analyst.start_analysis_scheduler()
        return result
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-scheduler")
async def stop_scheduler():
    """Stop the analysis scheduler"""
    try:
        result = await market_analyst.stop_analysis_scheduler()
        return result
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get agent status"""
    return {
        "is_running": market_analyst.is_running,
        "last_analysis_time": market_analyst.last_analysis.get("timestamp") if market_analyst.last_analysis else None,
        "analysis_count": len(market_analyst.analysis_history),
        "analysis_interval": market_analyst.analysis_interval,
        "model": market_analyst.model,
        "slack_channel": market_analyst.slack_channel
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)