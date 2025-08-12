#!/usr/bin/env python3
"""
News Analyst Agent - AI-Powered News Sentiment Analysis
Uses mistral7b:latest for intelligent news interpretation
Connects to News MCPs and Slack MCP for notifications
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

app = FastAPI(title="News Analyst Agent", version="3.0.0")

class NewsAnalystAgent:
    def __init__(self):
        # Load configuration
        self.config_path = os.getenv("CONFIG_PATH", "config/production_config.yaml")
        self.load_config()
        
        # Ollama configuration for mistral7b:latest
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = "mistral7b:latest"
        
        # Analysis scheduling
        self.analysis_interval = int(os.getenv("NEWS_ANALYSIS_INTERVAL", "600"))  # 10 minutes
        self.last_analysis = None
        self.analysis_history = []
        self.is_running = False
        self.scheduler_task = None
        
        # Slack MCP configuration
        self.slack_channel = "#news-analyst"
        
        logger.info("📰 News Analyst Agent initialized with mistral7b:latest")
    
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
        """Start the news analysis scheduler"""
        if self.scheduler_task:
            return {"message": "Scheduler already running"}
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self.analysis_loop())
        
        # Notify Slack about startup
        await self.notify_slack("🚀 News Analyst Agent started", "startup")
        
        logger.info("🚀 News analysis scheduler started")
        return {"message": "News analysis scheduler started", "interval": self.analysis_interval}
    
    async def stop_analysis_scheduler(self):
        """Stop the news analysis scheduler"""
        if not self.scheduler_task:
            return {"message": "Scheduler not running"}
        
        self.is_running = False
        self.scheduler_task.cancel()
        self.scheduler_task = None
        
        # Notify Slack about shutdown
        await self.notify_slack("⏹️ News Analyst Agent stopped", "shutdown")
        
        logger.info("⏹️ News analysis scheduler stopped")
        return {"message": "News analysis scheduler stopped"}
    
    async def analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                # Perform news analysis
                analysis = await self.perform_news_analysis()
                
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
    
    async def perform_news_analysis(self) -> Dict[str, Any]:
        """Perform AI-powered news sentiment analysis"""
        try:
            # Get news data from MCPs
            news_data = await self.get_news_data_from_mcps()
            
            # Prepare context for AI analysis
            analysis_context = {
                "news_data": news_data,
                "analysis_type": "news",
                "timestamp": datetime.now().isoformat(),
                "config": self.config.get("trading", {})
            }
            
            # Get AI news analysis from mistral7b
            analysis = await self.get_ai_analysis(analysis_context)
            
            self.last_analysis = analysis
            self.analysis_history.append(analysis)
            
            # Keep only last 100 analyses
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
            
            logger.info("📰 News analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"News analysis failed: {e}")
            return {"error": str(e), "type": "news_analysis_error"}
    
    async def get_ai_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered news analysis from mistral7b:latest"""
        try:
            # Extract trading parameters from config
            trading_config = context.get("config", {})
            
            prompt = f"""
            You are an expert financial news analyst specializing in cryptocurrency markets.
            Analyze the following news data for market sentiment and potential impact:
            
            News Data: {json.dumps(context['news_data'], indent=2)}
            
            Trading Context:
            - Primary Symbol: {trading_config.get('symbol', 'BTCUSDC')}
            - Trading Mode: {trading_config.get('mode', 'paper')}
            
            Provide a comprehensive news sentiment analysis including:
            1. Overall sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
            2. Key themes and topics affecting the market
            3. Regulatory and institutional developments
            4. Market impact assessment (HIGH/MEDIUM/LOW)
            5. Time horizon for impact (SHORT/MEDIUM/LONG)
            6. Recommended position adjustments (BUY/SELL/HOLD)
            7. Confidence level (0.0 to 1.0)
            8. Risk factors identified from news
            
            Respond in JSON format with the following structure:
            {{
                "sentiment_score": -1.0 to 1.0,
                "sentiment_label": "VERY_NEGATIVE|NEGATIVE|NEUTRAL|POSITIVE|VERY_POSITIVE",
                "recommendation": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "impact_level": "HIGH|MEDIUM|LOW",
                "time_horizon": "SHORT|MEDIUM|LONG",
                "key_themes": ["theme1", "theme2"],
                "regulatory_developments": ["development1", "development2"],
                "risk_factors": ["risk1", "risk2"],
                "opportunities": ["opportunity1", "opportunity2"],
                "reasoning": "detailed explanation of the analysis"
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
                                "sentiment_score": 0.0,
                                "sentiment_label": "NEUTRAL",
                                "recommendation": "HOLD",
                                "confidence": 0.5,
                                "raw_response": ai_response,
                                "parsed": False
                            }
                        
                        analysis_data.update({
                            "timestamp": datetime.now().isoformat(),
                            "model_used": self.model,
                            "agent": "news_analyst",
                            "analysis_type": "news"
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
            "sentiment_score": 0.0,
            "sentiment_label": "NEUTRAL",
            "recommendation": "HOLD",
            "confidence": 0.5,
            "impact_level": "LOW",
            "time_horizon": "SHORT",
            "key_themes": [],
            "regulatory_developments": [],
            "risk_factors": ["AI unavailable"],
            "opportunities": [],
            "reasoning": "Fallback analysis - AI model unavailable",
            "timestamp": datetime.now().isoformat(),
            "model_used": "fallback_rules",
            "agent": "news_analyst"
        }
    
    async def get_news_data_from_mcps(self) -> Dict[str, Any]:
        """Get news data from various MCP sources"""
        news_data = {}
        
        try:
            # This would connect to actual MCP servers
            # For now, using mock data
            news_data = self.get_mock_news_data()
        
        except Exception as e:
            logger.error(f"Failed to get news data from MCPs: {e}")
            news_data = self.get_mock_news_data()
        
        return news_data
    
    def get_mock_news_data(self) -> Dict[str, Any]:
        """Mock news data for testing"""
        import random
        
        sample_headlines = [
            "Bitcoin reaches new monthly high amid institutional adoption",
            "Ethereum network upgrade scheduled for next quarter",
            "Regulatory clarity improves cryptocurrency market outlook",
            "Major exchange announces new security measures",
            "Central bank digital currency pilot program launched",
            "Cryptocurrency trading volumes surge in emerging markets"
        ]
        
        articles = []
        for i in range(random.randint(3, 6)):
            sentiment_score = random.uniform(-0.5, 0.8)  # Slightly positive bias
            articles.append({
                "title": random.choice(sample_headlines),
                "sentiment_score": sentiment_score,
                "source": random.choice(["CoinDesk", "CoinTelegraph", "Reuters", "Bloomberg"]),
                "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat(),
                "relevance": random.uniform(0.6, 1.0)
            })
        
        return {
            "articles": articles,
            "total_articles": len(articles),
            "average_sentiment": sum(a["sentiment_score"] for a in articles) / len(articles),
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
            sentiment_label = analysis.get("sentiment_label", "UNKNOWN")
            sentiment_score = analysis.get("sentiment_score", 0.0)
            recommendation = analysis.get("recommendation", "HOLD")
            confidence = analysis.get("confidence", 0.0)
            impact_level = analysis.get("impact_level", "UNKNOWN")
            
            # Choose emoji based on sentiment
            sentiment_emoji = "📰"
            if sentiment_score > 0.3:
                sentiment_emoji = "📈"
            elif sentiment_score < -0.3:
                sentiment_emoji = "📉"
            
            # Format analysis message
            message = f"""{sentiment_emoji} **News Sentiment Analysis**

📊 **Sentiment**: {sentiment_label} ({sentiment_score:+.2f})
💡 **Recommendation**: {recommendation}
📈 **Confidence**: {confidence:.1%}
⚡ **Impact Level**: {impact_level}

🔍 **Key Insights**:
{analysis.get('reasoning', 'No detailed reasoning available')}

⏰ **Analysis Time**: {datetime.now().strftime('%H:%M:%S')}
🤖 **Model**: {analysis.get('model_used', 'Unknown')}
"""
            
            await self.notify_slack(message, "analysis")
            
        except Exception as e:
            logger.error(f"Failed to send analysis to Slack: {e}")

# Global news analyst agent instance
news_analyst = NewsAnalystAgent()

@app.on_event("startup")
async def startup_event():
    """Start the analysis scheduler when FastAPI starts"""
    await news_analyst.start_analysis_scheduler()

@app.on_event("shutdown")  
async def shutdown_event():
    """Clean up scheduler task on shutdown"""
    await news_analyst.stop_analysis_scheduler()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "news-analyst-agent",
        "is_running": news_analyst.is_running,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analysis")
async def get_current_analysis():
    """Get current news analysis from AI agent"""
    try:
        if not news_analyst.last_analysis:
            # Trigger analysis if none exists
            analysis = await news_analyst.perform_news_analysis()
        else:
            analysis = news_analyst.last_analysis
            
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger-analysis")
async def trigger_analysis():
    """Manually trigger news analysis"""
    try:
        analysis = await news_analyst.perform_news_analysis()
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
        result = await news_analyst.start_analysis_scheduler()
        return result
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-scheduler")
async def stop_scheduler():
    """Stop the analysis scheduler"""
    try:
        result = await news_analyst.stop_analysis_scheduler()
        return result
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get agent status"""
    return {
        "is_running": news_analyst.is_running,
        "last_analysis_time": news_analyst.last_analysis.get("timestamp") if news_analyst.last_analysis else None,
        "analysis_count": len(news_analyst.analysis_history),
        "analysis_interval": news_analyst.analysis_interval,
        "model": news_analyst.model,
        "slack_channel": news_analyst.slack_channel
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)