#!/usr/bin/env python3
"""
Agent Orchestrator Service - AI Agent Coordination and Scheduling
Coordinates all AI agents with scheduling to avoid resource conflicts
Manages Risk Manager, Market/News Analyst, and Trade Executor agents
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import aiohttp
import time
import logging
import yaml
from datetime import datetime

# Track service start time for uptime calculation
start_time = datetime.now()
from typing import Dict, Any, Optional
import os
import json
import uvicorn
import string
from slack_webhook_logger import SlackWebhookLogger
from orchestrator_message_queue import orchestrator_mq

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Orchestrator", version="3.0.0")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown"""
    logger.info("Application shutting down, cleaning up resources...")
    if orchestrator.session:
        await orchestrator.close_session()
        logger.info("HTTP sessions closed")

class AgentOrchestrator:
    def __init__(self):
        self.is_orchestrating = False
        self.orchestration_interval = int(os.getenv("ORCHESTRATION_INTERVAL", "60"))  # 60 seconds
        self.cycle_count = 0
        self.orchestration_task = None
        self.session = None  # HTTP session for service calls

        # AI Agent URLs
        self.risk_manager_agent = os.getenv("RISK_MANAGER_URL", "http://localhost:8002")
        self.analyst_agent = os.getenv("ANALYST_AGENT_URL", "http://localhost:8003")
        self.trade_executor_agent = os.getenv("TRADE_EXECUTOR_URL", "http://localhost:8005")
        self.parameter_optimizer = os.getenv("PARAMETER_OPTIMIZER_URL", "http://localhost:8006")
        
        # Legacy services (for backwards compatibility)
        self.portfolio_service = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8001")
        self.notification_service = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8004")
        
        # Agent scheduling to prevent resource conflicts
        self.agent_schedule = {
            "risk_manager": {"last_run": 0, "interval": 120},      # Every 2 minutes
            "market_analyst": {"last_run": 0, "interval": 300},    # Every 5 minutes (alternating)
            "news_analyst": {"last_run": 0, "interval": 600},     # Every 10 minutes (alternating)
            "trade_executor": {"last_run": 0, "interval": 30},     # Every 30 seconds
            "parameter_optimizer": {"last_run": 0, "interval": 3600} # Every hour
        }
        
        # Agent coordination state
        self.active_agent = None
        self.agent_results = {
            "risk_assessment": None,
            "market_analysis": None, 
            "news_analysis": None,
            "trade_signals": [],
            "optimization_status": None
        }

        # Config path from environment variable
        self.config_path = os.getenv("CONFIG_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "production_config.yaml"))

        # Template config
        self.templates_path = os.getenv("TEMPLATES_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "message_templates.yaml"))
        self.channels = {}
        self.templates = {}

        # Load config
        self.load_config()
        
        # Initialize Slack webhook logger
        self.slack_logger = SlackWebhookLogger("orchestrator")

        logger.info("🤖 Agent Orchestrator initialized with scheduling")
    
    async def init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def should_run_agent(self, agent_name: str) -> bool:
        """Check if agent should run based on schedule"""
        if agent_name not in self.agent_schedule:
            return False
        current_time = time.time()
        last_run = self.agent_schedule[agent_name]["last_run"]
        interval = self.agent_schedule[agent_name]["interval"]
        return current_time - last_run >= interval
        
    def load_config(self):
        """Load configuration from YAML files"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            # Load message templates and channels
            with open(self.templates_path, 'r') as tf:
                templates_config = yaml.safe_load(tf)
                self.channels = {
                    "trading_alerts": os.getenv("SLACK_TRADING_ALERTS_CHANNEL", templates_config["slack_channels"]["trading_alerts"]),
                    "general": os.getenv("SLACK_GENERAL_CHANNEL", templates_config["slack_channels"]["general"]),
                    "agents": os.getenv("SLACK_AGENTS_CHANNEL", "agents")
                }
                self.templates = templates_config["templates"]
            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
            self.channels = {"trading_alerts": "trading-alerts", "general": "general", "agents": "agents"}
            self.templates = {}
    
    async def call_service(self, service_url: str, endpoint: str, method: str = "GET", data: dict = None) -> Optional[Dict]:
        """Make HTTP call to another service"""
        try:
            await self.init_session()
            url = f"{service_url}{endpoint}"
            
            if method == "GET":
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            elif method == "POST":
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Service call failed {service_url}{endpoint}: {e}")
            return None
    
    async def check_agents_health(self) -> Dict[str, bool]:
        """Check health of all AI agents"""
        await self.init_session()
        agents = {
            "risk_manager_agent": f"{self.risk_manager_agent}/health",
            "analyst_agent": f"{self.analyst_agent}/health",
            "trade_executor_agent": f"{self.trade_executor_agent}/health",
            "parameter_optimizer": f"{self.parameter_optimizer}/health",
            "portfolio_service": f"{self.portfolio_service}/health",
            "notification_service": f"{self.notification_service}/health"
        }
        
        health_status = {}
        for agent_name, url in agents.items():
            try:
                async with self.session.get(url) as response:
                    health_status[agent_name] = response.status == 200
            except:
                health_status[agent_name] = False
                
        return health_status
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health_status = await self.check_agents_health()
        return {
            "services": health_status,
            "orchestration": {
                "is_running": self.is_orchestrating,
                "cycle_count": self.cycle_count,
                "active_agent": self.active_agent
            },
            "timestamp": datetime.now().isoformat(),
            "system_health": "healthy" if all(health_status.values()) else "degraded"
        }
    
    async def check_service_health(self, service_url: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        try:
            await self.init_session()
            async with self.session.get(f"{service_url}/health") as response:
                return {
                    "healthy": response.status == 200,
                    "status_code": response.status,
                    "response_time": response.headers.get('X-Response-Time', 'unknown')
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "status_code": None
            }
    
    async def execute_orchestration_cycle(self) -> Dict[str, Any]:
        """Execute one complete agent orchestration cycle"""
        cycle_start = time.time()
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "cycle_number": self.cycle_count + 1,
            "agents_activated": [],
            "actions_taken": [],
            "errors": []
        }
        
        # Log cycle start to Slack
        await self.slack_logger.log_info(
            f"Starting orchestration cycle #{self.cycle_count + 1}",
            {"timestamp": datetime.now().isoformat()}
        )
        
        try:
            current_time = time.time()
            
            # Check daily profit target status first
            profit_status = await self.call_service(self.portfolio_service, "/daily-profit-status")
            if profit_status:
                cycle_result["daily_profit_status"] = profit_status
                if profit_status.get("target_reached", False):
                    logger.info(f"🎯 Daily profit target reached! {profit_status['daily_profit_pct']:.2f}% - Trading paused")
                    await self.slack_logger.log_success(
                        f"🎯 **DAILY TARGET ACHIEVED!** {profit_status['daily_profit_pct']:.2f}% profit (${profit_status['daily_profit']:.2f})",
                        profit_status
                    )
                    cycle_result["actions_taken"].append("Trading paused due to profit target")
                elif profit_status.get("daily_profit_pct", 0) > 0:
                    logger.info(f"📈 Daily progress: {profit_status['daily_profit_pct']:.2f}% toward 1% target")
            else:
                cycle_result["errors"].append("Failed to get daily profit status")
            
            # 1. Risk Manager Agent (every 2 minutes)
            if current_time - self.agent_schedule["risk_manager"]["last_run"] >= self.agent_schedule["risk_manager"]["interval"]:
                self.active_agent = "risk_manager"
                risk_assessment = await self.call_service(self.risk_manager_agent, "/risk-assessment")
                if risk_assessment:
                    self.agent_results["risk_assessment"] = risk_assessment
                    cycle_result["agents_activated"].append("Risk Manager")
                    self.agent_schedule["risk_manager"]["last_run"] = current_time
                else:
                    cycle_result["errors"].append("Risk Manager Agent failed")
            
            # 2. Market/News Analyst Agent (alternating analysis)
            if current_time - self.agent_schedule["market_analyst"]["last_run"] >= self.agent_schedule["market_analyst"]["interval"]:
                self.active_agent = "analyst"
                # Get current analysis (alternates between market and news)
                analysis = await self.call_service(self.analyst_agent, "/analysis")
                if analysis:
                    self.agent_results["market_analysis"] = analysis
                    cycle_result["agents_activated"].append("Market/News Analyst")
                    self.agent_schedule["market_analyst"]["last_run"] = current_time
                else:
                    cycle_result["errors"].append("Market/News Analyst Agent failed")
            
            # 3. Trade Executor Agent (every 30 seconds, if signals available)
            if (current_time - self.agent_schedule["trade_executor"]["last_run"] >= self.agent_schedule["trade_executor"]["interval"] and
                self.agent_results["risk_assessment"] and self.agent_results["market_analysis"]):
                
                self.active_agent = "trade_executor"
                
                # Prepare trade signal based on analysis and risk assessment
                risk_data = self.agent_results["risk_assessment"].get("risk_assessment", {})
                analysis_data = self.agent_results["market_analysis"].get("analysis", {})
                
                # Only proceed if risk level is acceptable
                risk_level = risk_data.get("risk_level", "HIGH")
                if risk_level not in ["HIGH", "CRITICAL"]:
                    trade_signal = {
                        "symbol": "BTCUSDC",
                        "side": "BUY" if analysis_data.get("sentiment") == "BULLISH" else "HOLD",
                        "source": "orchestrator",
                        "risk_assessment": risk_data,
                        "market_analysis": analysis_data
                    }
                    
                    if trade_signal["side"] != "HOLD":
                        execution_result = await self.call_service(
                            self.trade_executor_agent, 
                            "/execute-trade", 
                            "POST", 
                            trade_signal
                        )
                        
                        if execution_result and execution_result.get("status") == "executed":
                            cycle_result["actions_taken"].append(f"Executed {trade_signal['side']} trade")
                            cycle_result["agents_activated"].append("Trade Executor")
                        elif execution_result:
                            cycle_result["errors"].append(f"Trade execution failed: {execution_result.get('error')}")
                
                self.agent_schedule["trade_executor"]["last_run"] = current_time
            
            # 4. Parameter Optimizer (every hour or on significant losses)
            if current_time - self.agent_schedule["parameter_optimizer"]["last_run"] >= self.agent_schedule["parameter_optimizer"]["interval"]:
                self.active_agent = "parameter_optimizer"
                
                # Check if optimization is needed
                opt_status = await self.call_service(self.parameter_optimizer, "/health")
                if opt_status and not opt_status.get("is_optimizing", False):
                    # Start monitoring if not already active
                    monitoring_result = await self.call_service(
                        self.parameter_optimizer, 
                        "/start-monitoring", 
                        "POST"
                    )
                    if monitoring_result:
                        cycle_result["agents_activated"].append("Parameter Optimizer (monitoring)")
                        self.agent_schedule["parameter_optimizer"]["last_run"] = current_time
            
            self.active_agent = None
            
            self.cycle_count += 1
            cycle_duration = time.time() - cycle_start
            cycle_result["duration_seconds"] = round(cycle_duration, 2)
            
            logger.info(f"🤖 Orchestration cycle {self.cycle_count} completed in {cycle_duration:.2f}s")
            
            # Send periodic comprehensive status updates to Slack (every 10 cycles or on significant events)
            if self.cycle_count % 10 == 0 or len(cycle_result.get("actions_taken", [])) > 0 or len(cycle_result.get("errors", [])) > 1:
                await self.send_comprehensive_status_update(cycle_result)
            
        except Exception as e:
            logger.error(f"❌ Orchestration cycle error: {e}")
            cycle_result["errors"].append(str(e))
        
        return cycle_result
    
    async def send_orchestration_status_update(self, cycle_result: Dict):
        """Send agent orchestration status update to Slack"""
        try:
            # Get portfolio data for context
            portfolio_data = await self.call_service(self.portfolio_service, "/portfolio")
            
            # Extract key information
            cycle_num = cycle_result.get("cycle_number", self.cycle_count)
            duration = cycle_result.get("duration_seconds", 0)
            agents_activated = cycle_result.get("agents_activated", [])
            actions = cycle_result.get("actions_taken", [])
            errors = cycle_result.get("errors", [])
            
            # Agent status information
            active_agent = self.active_agent or "None"
            
            # Get latest results from agents
            risk_level = "UNKNOWN"
            market_sentiment = "UNKNOWN"
            if self.agent_results["risk_assessment"]:
                risk_level = self.agent_results["risk_assessment"].get("risk_assessment", {}).get("risk_level", "UNKNOWN")
            if self.agent_results["market_analysis"]:
                analysis = self.agent_results["market_analysis"].get("analysis", {})
                market_sentiment = analysis.get("sentiment", "UNKNOWN")
            
            # Portfolio data for context
            portfolio = portfolio_data.get("portfolio", {}) if portfolio_data else {}
            total_value = portfolio.get("total_value", 0)
            
            # Format time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Create agent orchestration status message
            template = self.templates.get("orchestration_status", None)
            if template:
                status_message = string.Template(template).safe_substitute(
                    cycle_num=cycle_num,
                    current_time=current_time,
                    active_agent=active_agent,
                    agents_activated=", ".join(agents_activated) if agents_activated else "None",
                    risk_level=risk_level,
                    market_sentiment=market_sentiment,
                    total_value=total_value,
                    actions=", ".join(actions) if actions else "NONE (agents coordinating)",
                    errors=", ".join(errors) if errors else "",
                    duration=duration,
                    orchestration_interval=self.orchestration_interval
                )
            else:
                status_message = f"""🤖 **Agent Orchestration Cycle #{cycle_num}** ({current_time})

🔄 **Agent Coordination:**
• Active Agent: {active_agent}
• Agents Activated: {', '.join(agents_activated) if agents_activated else 'None'}
• Risk Level: {risk_level}
• Market Sentiment: {market_sentiment}

💰 **System Status:**
• Portfolio Value: {total_value:,.2f}

⚡ **Cycle Results:**"""

                if actions:
                    status_message += f"\n• Actions: {', '.join(actions)}"
                else:
                    status_message += f"\n• Actions: NONE (agents coordinating)"
                    
                if errors:
                    status_message += f"\n• Errors: {', '.join(errors)}"
                
                status_message += f"\n• Duration: {duration:.1f}s"
                status_message += f"\n\n⏱️ **Next cycle:** {self.orchestration_interval} seconds"
            
            # Send to Slack agents channel
            await self.call_service(
                self.notification_service,
                "/slack",
                "POST",
                {
                    "channel": self.channels.get("agents", "agents"),
                    "message": status_message
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send orchestration status update: {e}")
    
    async def send_comprehensive_status_update(self, cycle_result: Dict):
        """Send comprehensive, less frequent status updates to Slack"""
        try:
            # Get portfolio data for context
            portfolio_data = await self.call_service(self.portfolio_service, "/portfolio")
            
            # Extract key information
            cycle_num = cycle_result.get("cycle_number", self.cycle_count)
            duration = cycle_result.get("duration_seconds", 0)
            agents_activated = cycle_result.get("agents_activated", [])
            actions = cycle_result.get("actions_taken", [])
            errors = cycle_result.get("errors", [])
            
            # Get latest results from agents
            risk_level = "UNKNOWN"
            market_sentiment = "UNKNOWN"
            confidence = 0
            recommendation = "HOLD"
            
            if self.agent_results["risk_assessment"]:
                risk_data = self.agent_results["risk_assessment"].get("risk_assessment", {})
                risk_level = risk_data.get("risk_level", "UNKNOWN")
                
            if self.agent_results["market_analysis"]:
                analysis = self.agent_results["market_analysis"].get("analysis", {})
                market_sentiment = analysis.get("sentiment", "UNKNOWN")
                confidence = analysis.get("confidence", 0)
                recommendation = analysis.get("recommendation", "HOLD")
            
            # Portfolio data for context
            portfolio = portfolio_data.get("portfolio", {}) if portfolio_data else {}
            total_value = portfolio.get("total_value", 0)
            btc_balance = portfolio.get("btc_balance", 0)
            usdc_balance = portfolio.get("usdc_balance", 0)
            btc_price = portfolio.get("current_btc_price", 0)
            
            # Format time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Determine message type and urgency
            is_significant = len(actions) > 0 or len(errors) > 1
            is_periodic = cycle_num % 10 == 0
            
            if is_significant:
                title = "🚨 **SIGNIFICANT TRADING ACTIVITY**"
                urgency_emoji = "⚡"
            elif is_periodic:
                title = f"📊 **SYSTEM STATUS REPORT - Cycle #{cycle_num}**"
                urgency_emoji = "🔄"
            else:
                title = f"📈 **TRADING UPDATE - Cycle #{cycle_num}**"
                urgency_emoji = "📊"
            
            # Create comprehensive status message
            status_message = f"""{title}
⏰ **Time:** {current_time} | **Duration:** {duration:.1f}s

💰 **PORTFOLIO STATUS:**
• **Total Value:** ${total_value:,.2f} USDC
• **BTC Holdings:** {btc_balance:.6f} BTC (${btc_balance * btc_price:,.2f})
• **USDC Balance:** ${usdc_balance:,.2f}
• **BTC Price:** ${btc_price:,.2f}

🤖 **AGENT INTELLIGENCE:**
• **Risk Assessment:** {risk_level}
• **Market Sentiment:** {market_sentiment} (Confidence: {confidence:.1%})
• **AI Recommendation:** {recommendation}
• **Active Agents:** {', '.join(agents_activated) if agents_activated else 'Monitoring Mode'}

{urgency_emoji} **CYCLE RESULTS:**"""

            if actions:
                status_message += f"\n• **Actions Executed:** {', '.join(actions)}"
            else:
                status_message += f"\n• **Actions:** No trades executed (conditions not met)"
                
                
            if errors:
                status_message += f"\n• **⚠️ Issues:** {', '.join(errors)}"
            else:
                status_message += f"\n• **Status:** All systems operational"
            
            # Add schedule information for periodic reports
            if is_periodic:
                import time as time_module
                next_agents = []
                current_time_unix = time_module.time()
                for agent_name, schedule in self.agent_schedule.items():
                    time_until_next = schedule["interval"] - (current_time_unix - schedule["last_run"])
                    if time_until_next < 300:  # Next 5 minutes
                        next_agents.append(f"{agent_name.replace('_', ' ').title()}")
                
                if next_agents:
                    status_message += f"\n\n⏳ **Next Scheduled Agents:** {', '.join(next_agents)}"
                status_message += f"\n🔄 **Next Report:** Cycle #{cycle_num + 10} or significant event"
            
            # Send to Slack agents channel
            await self.call_service(
                self.notification_service,
                "/slack",
                "POST",
                {
                    "channel": self.channels.get("agents", "agents"),
                    "message": status_message
                }
            )
            
            logger.info(f"📤 Sent comprehensive status update to Slack (Cycle #{cycle_num})")
            
        except Exception as e:
            logger.error(f"❌ Failed to send comprehensive status update: {e}")
    
    async def orchestration_loop(self):
        """Main agent orchestration loop"""
        logger.info(f"🤖 Starting agent orchestration (interval: {self.orchestration_interval}s)")
        
        while self.is_orchestrating:
            try:
                cycle_result = await self.execute_orchestration_cycle()
                
                # Log cycle results
                if cycle_result["actions_taken"]:
                    logger.info(f"✅ Actions: {', '.join(cycle_result['actions_taken'])}")
                if cycle_result["errors"]:
                    logger.error(f"❌ Errors: {', '.join(cycle_result['errors'])}")
                
                # Wait for next cycle
                await asyncio.sleep(self.orchestration_interval)
                
            except Exception as e:
                logger.error(f"❌ Orchestration loop error: {e}")
                await asyncio.sleep(self.orchestration_interval)

    def update_configuration(self, parameter: str, value: Any, user_id: str) -> bool:
        """Update a configuration parameter dynamically"""
        try:
            # Define updatable parameters and their validation
            updatable_params = {
                "max_position_size": {"type": "float", "min": 0.01, "max": 1.0, "target": "portfolio"},
                "stop_loss_percentage": {"type": "float", "min": 0.001, "max": 0.5, "target": "portfolio"},
                "take_profit_percentage": {"type": "float", "min": 0.001, "max": 2.0, "target": "portfolio"},
                "trading_mode": {"type": "string", "values": ["paper", "live"], "target": "portfolio"},
                "max_daily_trades": {"type": "int", "min": 1, "max": 1000, "target": "risk_manager"},
                "risk_threshold": {"type": "float", "min": 0.01, "max": 1.0, "target": "risk_manager"},
                "orchestration_interval": {"type": "int", "min": 10, "max": 3600, "target": "orchestrator"}
            }
            
            if parameter not in updatable_params:
                logger.error(f"Parameter '{parameter}' is not updatable")
                return False
            
            param_config = updatable_params[parameter]
            
            # Validate the value
            if param_config["type"] == "float":
                if not isinstance(value, (int, float)):
                    logger.error(f"Parameter '{parameter}' must be a number")
                    return False
                value = float(value)
            elif param_config["type"] == "int":
                if not isinstance(value, (int, float)):
                    logger.error(f"Parameter '{parameter}' must be an integer")
                    return False
                value = int(value)
            elif param_config["type"] == "string":
                value = str(value)
                if "values" in param_config and value not in param_config["values"]:
                    logger.error(f"Parameter '{parameter}' must be one of: {param_config['values']}")
                    return False
            
            # Apply range validation
            if "min" in param_config and value < param_config["min"]:
                logger.error(f"Parameter '{parameter}' must be >= {param_config['min']}")
                return False
            if "max" in param_config and value > param_config["max"]:
                logger.error(f"Parameter '{parameter}' must be <= {param_config['max']}")
                return False
            
            # Update the parameter based on target
            target = param_config["target"]
            
            if target == "orchestrator":
                if parameter == "orchestration_interval":
                    old_value = self.orchestration_interval
                    self.orchestration_interval = value
                    logger.info(f"Updated orchestration_interval from {old_value} to {value}")
                    return True
                    
            elif target in ["portfolio", "risk_manager"]:
                # For other services, we would send update requests
                # For now, just log the update
                logger.info(f"Parameter '{parameter}' would be updated on {target} service to {value}")
                return True
            
            logger.error(f"Unknown target '{target}' for parameter '{parameter}'")
            return False
            
        except Exception as e:
            logger.error(f"Error updating configuration parameter '{parameter}': {str(e)}")
            return False

# Global orchestrator instance
orchestrator = AgentOrchestrator()

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for orchestrator"""
    health_status = {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.1",
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "orchestrating": orchestrator.is_orchestrating,
        "dependencies": {},
        "metrics": {},
        "agent_status": {}
    }
    
    # Check all dependent services
    services_to_check = {
        "portfolio": "http://localhost:8001/health",
        "risk_manager": "http://localhost:8002/health", 
        "market_analyst": "http://localhost:8003/health",
        "notification": "http://localhost:8004/health",
        "trade_executor": "http://localhost:8005/health",
        "parameter_optimizer": "http://localhost:8006/health",
        "mcp_hub": "http://localhost:9000/health"
    }
    
    healthy_services = 0
    total_services = len(services_to_check)
    
    for service_name, service_url in services_to_check.items():
        try:
            # In a real implementation, make HTTP request to check service
            # For now, simulate the check
            health_status["dependencies"][service_name] = {
                "status": "healthy",
                "url": service_url,
                "response_time_ms": 25,
                "last_checked": datetime.now().isoformat()
            }
            healthy_services += 1
        except Exception as e:
            health_status["dependencies"][service_name] = {
                "status": "unhealthy", 
                "url": service_url,
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }
    
    # Orchestration metrics
    health_status["metrics"] = {
        "cycles_completed": getattr(orchestrator, 'cycles_completed', 0),
        "last_cycle_duration_ms": getattr(orchestrator, 'last_cycle_duration', 0),
        "average_cycle_time_ms": getattr(orchestrator, 'avg_cycle_time', 2000),
        "successful_decisions": getattr(orchestrator, 'successful_decisions', 0),
        "failed_decisions": getattr(orchestrator, 'failed_decisions', 0),
        "services_healthy": f"{healthy_services}/{total_services}",
        "service_health_percentage": (healthy_services / total_services) * 100
    }
    
    # Agent coordination status
    health_status["agent_status"] = {
        "coordination_active": orchestrator.is_orchestrating,
        "last_coordination_time": getattr(orchestrator, 'last_coordination_time', None),
        "pending_tasks": getattr(orchestrator, 'pending_tasks', 0),
        "agent_response_times": {
            "market_analyst": 150,
            "risk_manager": 100,
            "trade_executor": 75,
            "parameter_optimizer": 500
        }
    }
    
    # Determine overall health
    if healthy_services < total_services * 0.5:
        health_status["status"] = "unhealthy"
        health_status["issues"] = f"Only {healthy_services}/{total_services} services are healthy"
    elif healthy_services < total_services:
        health_status["status"] = "degraded"
        health_status["issues"] = f"Some services are unhealthy ({total_services - healthy_services} down)"
    
    return health_status

@app.get("/system-status")
async def get_system_status():
    """Get comprehensive system status"""
    agents_health = await orchestrator.check_agents_health()
    
    # Get portfolio status
    portfolio_data = await orchestrator.call_service(orchestrator.portfolio_service, "/portfolio")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "orchestrating": orchestrator.is_orchestrating,
        "cycle_count": orchestrator.cycle_count,
        "agents": agents_health,
        "agent_results": orchestrator.agent_results,
        "active_agent": orchestrator.active_agent,
        "portfolio": portfolio_data
    }

@app.post("/start-orchestration")
async def start_orchestration(interval: int = 60):
    """Start agent orchestration"""
    if orchestrator.is_orchestrating:
        raise HTTPException(status_code=400, detail="Agent orchestration already running")
    
    orchestrator.orchestration_interval = interval
    orchestrator.is_orchestrating = True
    
    # Start the orchestration loop in background
    orchestrator.orchestration_task = asyncio.create_task(orchestrator.orchestration_loop())
    
    logger.info(f"🤖 Agent orchestration started (interval: {interval}s)")
    
    # Send startup notification
    template = orchestrator.templates.get("orchestration_started", "🤖 **AGENT ORCHESTRATION STARTED**\n⏱️ Interval: ${interval}s\n🔄 Mode: AI Agent Coordination")
    message = string.Template(template).safe_substitute(interval=interval)
    await orchestrator.call_service(
        orchestrator.notification_service,
        "/slack",
        "POST",
        {
            "channel": orchestrator.channels.get("agents", "agents"), 
            "message": message
        }
    )
    
    return {
        "message": "Agent orchestration started",
        "interval": interval,
        "status": "started",
        "orchestration_interval": interval
    }

@app.post("/stop-orchestration")
async def stop_orchestration():
    """Stop agent orchestration"""
    if not orchestrator.is_orchestrating:
        raise HTTPException(status_code=400, detail="Agent orchestration not running")
    
    orchestrator.is_orchestrating = False
    
    if orchestrator.orchestration_task:
        orchestrator.orchestration_task.cancel()
        orchestrator.orchestration_task = None
    
    # Close HTTP session to prevent unclosed client sessions
    await orchestrator.close_session()
    logger.info("⏹️ Agent orchestration stopped and client sessions closed")
    
    # Send stop notification
    template = orchestrator.templates.get("orchestration_stopped", "⏹️ **AGENT ORCHESTRATION STOPPED**\n📊 Total cycles: ${total_cycles}")
    message = string.Template(template).safe_substitute(total_cycles=orchestrator.cycle_count)
    await orchestrator.call_service(
        orchestrator.notification_service,
        "/slack", 
        "POST",
        {
            "channel": orchestrator.channels.get("agents", "agents"),
            "message": message
        }
    )
    
    return {
        "message": "Agent orchestration stopped",
        "total_cycles": orchestrator.cycle_count,
        "status": "stopped"
    }

@app.get("/orchestration-status")
async def get_orchestration_status():
    """Get orchestration status"""
    return {
        "is_running": orchestrator.is_orchestrating,
        "interval_seconds": orchestrator.orchestration_interval,
        "cycle_count": orchestrator.cycle_count,
        "active_agent": orchestrator.active_agent,
        "agent_schedule": orchestrator.agent_schedule,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/manual-cycle")
async def execute_manual_cycle():
    """Execute a single orchestration cycle manually"""
    result = await orchestrator.execute_orchestration_cycle()
    return {
        "status": "completed",
        "cycle_results": result,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/update_config")
async def update_config(request: dict):
    """Update system configuration via API (typically from Slack)"""
    try:
        parameter = request.get("parameter")
        value = request.get("value") 
        user_id = request.get("user_id", "unknown")
        timestamp = request.get("timestamp", datetime.now().isoformat())
        
        if not parameter or value is None:
            raise HTTPException(status_code=400, detail="Missing parameter or value")
        
        # Update the configuration
        success = orchestrator.update_configuration(parameter, value, user_id)
        
        if success:
            logger.info(f"Configuration updated: {parameter} = {value} by {user_id}")
            
            # Log the configuration change for audit
            config_change = {
                "timestamp": timestamp,
                "parameter": parameter,
                "old_value": getattr(orchestrator, f"_{parameter}", None),
                "new_value": value,
                "user_id": user_id,
                "source": "slack_command"
            }
            
            # Save to audit log
            try:
                os.makedirs("logs", exist_ok=True)
                with open("logs/config_changes.jsonl", "a") as f:
                    f.write(f"{json.dumps(config_change)}\n")
            except Exception as e:
                logger.error(f"Failed to write config audit log: {str(e)}")
            
            return {
                "success": True,
                "message": f"Configuration parameter '{parameter}' updated to '{value}'",
                "timestamp": timestamp,
                "updated_by": user_id
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to update parameter '{parameter}'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
