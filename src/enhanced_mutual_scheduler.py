#!/usr/bin/env python3
"""
Enhanced Mutual Scheduler - Prevents Resource Conflicts Between AI Agents
Ensures only one mistral7b agent runs at a time to prevent resource overload
Manages scheduling for Market Analyst and News Analyst agents with Slack integration
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from enum import Enum
import json
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SCHEDULED = "scheduled"
    ERROR = "error"
    COOLDOWN = "cooldown"

class EnhancedMutualScheduler:
    """Enhanced mutual exclusion scheduler for AI agents with Slack integration"""
    
    def __init__(self):
        # Load configuration
        self.config_path = os.getenv("CONFIG_PATH", "config/production_config.yaml")
        self.load_config()
        
        # Agent configurations
        self.agents = {
            "market_analyst": {
                "url": os.getenv("MARKET_ANALYST_URL", "http://localhost:8007"),
                "interval": int(os.getenv("MARKET_ANALYSIS_INTERVAL", "300")),  # 5 minutes
                "priority": 1,  # Higher priority
                "last_run": 0,
                "status": AgentStatus.IDLE,
                "model": "mistral7b:latest",
                "resource_intensive": True,
                "slack_channel": "#market-analyst",
                "max_runtime": 180,  # 3 minutes max
                "retry_count": 0,
                "max_retries": 3
            },
            "news_analyst": {
                "url": os.getenv("NEWS_ANALYST_URL", "http://localhost:8008"),
                "interval": int(os.getenv("NEWS_ANALYSIS_INTERVAL", "600")),  # 10 minutes
                "priority": 2,  # Lower priority
                "last_run": 0,
                "status": AgentStatus.IDLE,
                "model": "mistral7b:latest",
                "resource_intensive": True,
                "slack_channel": "#news-analyst",
                "max_runtime": 240,  # 4 minutes max
                "retry_count": 0,
                "max_retries": 3
            },
            "risk_manager": {
                "url": os.getenv("RISK_MANAGER_URL", "http://localhost:8002"),
                "interval": int(os.getenv("RISK_ANALYSIS_INTERVAL", "120")),  # 2 minutes
                "priority": 0,  # Highest priority (safety first)
                "last_run": 0,
                "status": AgentStatus.IDLE,
                "model": "mistral7b:latest",
                "resource_intensive": True,
                "slack_channel": "#risk-manager",
                "max_runtime": 120,  # 2 minutes max
                "retry_count": 0,
                "max_retries": 3
            },
            "trade_executor": {
                "url": os.getenv("TRADE_EXECUTOR_URL", "http://localhost:8005"),
                "interval": int(os.getenv("TRADE_EXECUTION_INTERVAL", "30")),  # 30 seconds
                "priority": 0,  # Highest priority (time-sensitive)
                "last_run": 0,
                "status": AgentStatus.IDLE,
                "model": "phi3",  # Uses different model
                "resource_intensive": False,
                "slack_channel": "#trade-executor",
                "max_runtime": 60,  # 1 minute max
                "retry_count": 0,
                "max_retries": 3
            },
            "parameter_optimizer": {
                "url": os.getenv("PARAMETER_OPTIMIZER_URL", "http://localhost:8006"),
                "interval": int(os.getenv("OPTIMIZATION_INTERVAL", "3600")),  # 1 hour
                "priority": 3,  # Lowest priority
                "last_run": 0,
                "status": AgentStatus.IDLE,
                "model": "none",  # Python service
                "resource_intensive": False,
                "slack_channel": "#parameter-optimizer",
                "max_runtime": 300,  # 5 minutes max
                "retry_count": 0,
                "max_retries": 2
            }
        }
        
        # Scheduling state
        self.active_agent = None
        self.schedule_queue = []
        self.cooldown_period = int(os.getenv("AGENT_COOLDOWN_SECONDS", "30"))  # 30 seconds between agents
        self.last_agent_finish_time = 0
        self.scheduler_running = False
        self.scheduler_task = None
        
        # Slack MCP configuration
        self.slack_mcp_enabled = True
        self.orchestrator_channel = "#orchestrator"
        
        # Performance tracking
        self.performance_stats = {
            "total_cycles": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_runtime": {},
            "last_24h_runs": []
        }
        
        logger.info("🔄 Enhanced Mutual Scheduler initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
    
    async def start_scheduler(self):
        """Start the mutual scheduler"""
        if self.scheduler_running:
            return {"message": "Scheduler already running"}
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self.scheduling_loop())
        
        # Notify Slack about scheduler startup
        await self.notify_slack("🚀 Enhanced Mutual Scheduler started", "startup")
        
        logger.info("🚀 Enhanced mutual scheduler started")
        return {"message": "Enhanced mutual scheduler started"}
    
    async def stop_scheduler(self):
        """Stop the mutual scheduler"""
        if not self.scheduler_running:
            return {"message": "Scheduler not running"}
        
        self.scheduler_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            self.scheduler_task = None
        
        # Notify Slack about scheduler shutdown
        await self.notify_slack("⏹️ Enhanced Mutual Scheduler stopped", "shutdown")
        
        logger.info("⏹️ Enhanced mutual scheduler stopped")
        return {"message": "Enhanced mutual scheduler stopped"}
    
    async def should_run_agent(self, agent_name: str) -> bool:
        """Check if agent should run based on schedule and resource availability"""
        agent = self.agents.get(agent_name)
        if not agent:
            return False
        
        current_time = time.time()
        
        # Check if enough time has passed since last run
        if current_time - agent["last_run"] < agent["interval"]:
            return False
        
        # Check if agent is in error state and needs cooldown
        if agent["status"] == AgentStatus.ERROR:
            if current_time - agent["last_run"] < 300:  # 5 minute cooldown after error
                return False
            else:
                agent["status"] = AgentStatus.IDLE  # Reset error state
                agent["retry_count"] = 0
        
        # Check if another resource-intensive agent is running
        if agent["resource_intensive"] and self.active_agent and self.active_agent != agent_name:
            active_agent_config = self.agents.get(self.active_agent)
            if active_agent_config and active_agent_config["resource_intensive"]:
                logger.debug(f"Agent {agent_name} waiting for {self.active_agent} to finish")
                return False
        
        # Check cooldown period
        if current_time - self.last_agent_finish_time < self.cooldown_period:
            logger.debug(f"Agent {agent_name} waiting for cooldown period")
            return False
        
        return True
    
    async def get_next_agent_to_run(self) -> Optional[str]:
        """Get the next agent that should run based on priority and schedule"""
        eligible_agents = []
        
        for agent_name in self.agents:
            if await self.should_run_agent(agent_name):
                eligible_agents.append((agent_name, self.agents[agent_name]["priority"]))
        
        if not eligible_agents:
            return None
        
        # Sort by priority (lower number = higher priority)
        eligible_agents.sort(key=lambda x: x[1])
        return eligible_agents[0][0]
    
    async def trigger_agent_analysis(self, agent_name: str) -> Dict[str, Any]:
        """Trigger analysis for a specific agent with timeout and error handling"""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        
        start_time = time.time()
        
        try:
            # Mark agent as running
            self.active_agent = agent_name
            agent["status"] = AgentStatus.RUNNING
            agent["last_run"] = start_time
            
            logger.info(f"🚀 Starting {agent_name} analysis")
            
            # Send notification to Slack
            await self.notify_slack_agent_start(agent_name)
            
            # Call the agent's analysis endpoint with timeout
            timeout = aiohttp.ClientTimeout(total=agent["max_runtime"])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{agent['url']}/analysis") as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Calculate runtime
                        runtime = time.time() - start_time
                        
                        # Mark agent as idle
                        agent["status"] = AgentStatus.IDLE
                        agent["retry_count"] = 0
                        self.active_agent = None
                        self.last_agent_finish_time = time.time()
                        
                        # Update performance stats
                        self.update_performance_stats(agent_name, runtime, True)
                        
                        logger.info(f"✅ {agent_name} analysis completed in {runtime:.1f}s")
                        await self.notify_slack_agent_success(agent_name, runtime, result)
                        
                        return {
                            "success": True,
                            "agent": agent_name,
                            "result": result,
                            "runtime": runtime,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            error_msg = f"Analysis timeout after {agent['max_runtime']}s"
            await self.handle_agent_error(agent_name, error_msg, start_time)
            return {"success": False, "agent": agent_name, "error": error_msg}
            
        except Exception as e:
            await self.handle_agent_error(agent_name, str(e), start_time)
            return {"success": False, "agent": agent_name, "error": str(e)}
    
    async def handle_agent_error(self, agent_name: str, error_msg: str, start_time: float):
        """Handle agent errors with retry logic"""
        agent = self.agents[agent_name]
        runtime = time.time() - start_time
        
        agent["retry_count"] += 1
        
        if agent["retry_count"] >= agent["max_retries"]:
            agent["status"] = AgentStatus.ERROR
            logger.error(f"❌ {agent_name} failed permanently after {agent['max_retries']} retries: {error_msg}")
            await self.notify_slack_agent_error(agent_name, error_msg, True)
        else:
            agent["status"] = AgentStatus.IDLE
            logger.warning(f"⚠️ {agent_name} failed (retry {agent['retry_count']}/{agent['max_retries']}): {error_msg}")
            await self.notify_slack_agent_error(agent_name, error_msg, False)
        
        self.active_agent = None
        self.last_agent_finish_time = time.time()
        self.update_performance_stats(agent_name, runtime, False)
    
    def update_performance_stats(self, agent_name: str, runtime: float, success: bool):
        """Update performance statistics"""
        self.performance_stats["total_cycles"] += 1
        
        if success:
            self.performance_stats["successful_runs"] += 1
        else:
            self.performance_stats["failed_runs"] += 1
        
        # Update average runtime
        if agent_name not in self.performance_stats["average_runtime"]:
            self.performance_stats["average_runtime"][agent_name] = []
        
        self.performance_stats["average_runtime"][agent_name].append(runtime)
        
        # Keep only last 10 runtimes for average calculation
        if len(self.performance_stats["average_runtime"][agent_name]) > 10:
            self.performance_stats["average_runtime"][agent_name] = \
                self.performance_stats["average_runtime"][agent_name][-10:]
        
        # Track last 24h runs
        current_time = time.time()
        self.performance_stats["last_24h_runs"].append({
            "agent": agent_name,
            "timestamp": current_time,
            "runtime": runtime,
            "success": success
        })
        
        # Clean up old entries (older than 24h)
        cutoff_time = current_time - 86400  # 24 hours
        self.performance_stats["last_24h_runs"] = [
            run for run in self.performance_stats["last_24h_runs"]
            if run["timestamp"] > cutoff_time
        ]
    
    async def scheduling_loop(self):
        """Main scheduling loop with enhanced error handling"""
        logger.info("🔄 Starting enhanced mutual scheduling loop")
        
        while self.scheduler_running:
            try:
                # Get next agent to run
                next_agent = await self.get_next_agent_to_run()
                
                if next_agent:
                    # Run the agent
                    result = await self.trigger_agent_analysis(next_agent)
                    
                    # Log result
                    if result.get("success"):
                        logger.info(f"✅ {next_agent} completed successfully")
                    else:
                        logger.error(f"❌ {next_agent} failed: {result.get('error')}")
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Scheduling loop error: {e}")
                await self.notify_slack(f"❌ Scheduler error: {e}", "error")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def notify_slack(self, message: str, level: str = "info"):
        """Send notification to Slack via MCP"""
        try:
            if not self.slack_mcp_enabled:
                return
            
            emoji_map = {
                "info": "ℹ️",
                "success": "✅",
                "error": "❌",
                "warning": "⚠️",
                "startup": "🚀",
                "shutdown": "⏹️"
            }
            
            emoji = emoji_map.get(level, "ℹ️")
            formatted_message = f"{emoji} **Enhanced Mutual Scheduler**: {message}"
            
            # TODO: Implement actual Slack MCP call
            logger.info(f"Slack notification ({level}): {formatted_message}")
            
        except Exception as e:
            logger.warning(f"Failed to send Slack notification: {e}")
    
    async def notify_slack_agent_start(self, agent_name: str):
        """Notify Slack when agent starts"""
        agent = self.agents[agent_name]
        message = f"🚀 **{agent_name.replace('_', ' ').title()}** analysis started"
        await self.notify_slack(message, "info")
    
    async def notify_slack_agent_success(self, agent_name: str, runtime: float, result: Dict):
        """Notify Slack when agent completes successfully"""
        agent = self.agents[agent_name]
        
        # Extract key insights from result
        analysis = result.get("analysis", {})
        if agent_name == "market_analyst":
            sentiment = analysis.get("sentiment", "UNKNOWN")
            recommendation = analysis.get("recommendation", "HOLD")
            confidence = analysis.get("confidence", 0.0)
            
            message = f"""✅ **Market Analysis Complete** ({runtime:.1f}s)
📊 Sentiment: {sentiment} | 💡 Rec: {recommendation} | 📈 Conf: {confidence:.1%}"""
            
        elif agent_name == "news_analyst":
            sentiment_score = analysis.get("sentiment_score", 0.0)
            impact_level = analysis.get("impact_level", "UNKNOWN")
            recommendation = analysis.get("recommendation", "HOLD")
            
            message = f"""✅ **News Analysis Complete** ({runtime:.1f}s)
📰 Sentiment: {sentiment_score:+.2f} | ⚡ Impact: {impact_level} | 💡 Rec: {recommendation}"""
            
        else:
            message = f"✅ **{agent_name.replace('_', ' ').title()}** completed in {runtime:.1f}s"
        
        await self.notify_slack(message, "success")
    
    async def notify_slack_agent_error(self, agent_name: str, error: str, permanent: bool):
        """Notify Slack when agent fails"""
        agent = self.agents[agent_name]
        
        if permanent:
            message = f"❌ **{agent_name.replace('_', ' ').title()}** failed permanently: {error}"
        else:
            message = f"⚠️ **{agent_name.replace('_', ' ').title()}** failed (retry {agent['retry_count']}/{agent['max_retries']}): {error}"
        
        await self.notify_slack(message, "error" if permanent else "warning")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status with performance metrics"""
        current_time = time.time()
        
        # Calculate average runtimes
        avg_runtimes = {}
        for agent_name, runtimes in self.performance_stats["average_runtime"].items():
            if runtimes:
                avg_runtimes[agent_name] = sum(runtimes) / len(runtimes)
        
        return {
            "scheduler_running": self.scheduler_running,
            "active_agent": self.active_agent,
            "agents": {
                name: {
                    "status": agent["status"].value,
                    "last_run": agent["last_run"],
                    "next_run": agent["last_run"] + agent["interval"],
                    "priority": agent["priority"],
                    "model": agent["model"],
                    "resource_intensive": agent["resource_intensive"],
                    "retry_count": agent["retry_count"],
                    "max_retries": agent["max_retries"],
                    "slack_channel": agent["slack_channel"]
                }
                for name, agent in self.agents.items()
            },
            "cooldown_remaining": max(0, self.cooldown_period - (current_time - self.last_agent_finish_time)),
            "performance_stats": {
                "total_cycles": self.performance_stats["total_cycles"],
                "successful_runs": self.performance_stats["successful_runs"],
                "failed_runs": self.performance_stats["failed_runs"],
                "success_rate": (self.performance_stats["successful_runs"] / max(1, self.performance_stats["total_cycles"])) * 100,
                "average_runtimes": avg_runtimes,
                "last_24h_runs": len(self.performance_stats["last_24h_runs"])
            },
            "timestamp": datetime.now().isoformat()
        }

# Global scheduler instance
enhanced_scheduler = EnhancedMutualScheduler()

# Async function to start the scheduler
async def start_enhanced_scheduler():
    """Start the enhanced mutual scheduler"""
    await enhanced_scheduler.start_scheduler()

if __name__ == "__main__":
    asyncio.run(start_enhanced_scheduler())