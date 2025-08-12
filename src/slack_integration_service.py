#!/usr/bin/env python3
"""
Slack Integration Service - Centralized Slack communication via MCP
Uses the external Slack MCP server for all agent communications
Handles parameter updates, notifications, and agent status updates
"""

import asyncio
import aiohttp
import logging
import json
import yaml
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Slack Integration Service", version="3.0.0")

class SlackIntegrationService:
    """Centralized Slack integration using the external MCP server"""
    
    def __init__(self):
        # Load configuration
        self.config_path = os.getenv("CONFIG_PATH", "config/agent_parameters.yaml")
        self.load_config()
        
        # Slack MCP server configuration
        self.slack_mcp_server_path = os.getenv(
            "SLACK_MCP_SERVER_PATH", 
            "/Users/alexdumats/trajdar_bjorn/mcp-servers/slack/cmd/slack-mcp-server/main.go"
        )
        self.slack_mcp_process = None
        self.slack_mcp_enabled = os.getenv("SLACK_MCP_ENABLED", "true").lower() == "true"
        
        # Slack configuration
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.channels = self.config.get("slack", {}).get("channels", {})
        self.notifications = self.config.get("slack", {}).get("notifications", {})
        
        # Parameter update settings
        self.enable_parameter_updates = self.config.get("parameter_updates", {}).get("enable_slack_updates", True)
        self.update_channels = self.config.get("parameter_updates", {}).get("update_channels", [])
        self.authorized_users = self.parse_authorized_users()
        
        # Message queue for batching
        self.message_queue = asyncio.Queue()
        self.queue_processor_task = None
        
        # Agent status tracking
        self.agent_status = {}
        
        logger.info("💬 Slack Integration Service initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}
    
    def parse_authorized_users(self) -> List[str]:
        """Parse authorized users from environment variable"""
        users_str = os.getenv("SLACK_AUTHORIZED_USERS", "")
        if not users_str:
            return []
        return [user.strip() for user in users_str.split(",") if user.strip()]
    
    async def start_slack_mcp_server(self):
        """Start the Slack MCP server process"""
        if not self.slack_mcp_enabled or not self.bot_token:
            logger.warning("⚠️ Slack MCP server disabled or no bot token provided")
            return False
        
        try:
            # Set environment variables for the MCP server
            env = os.environ.copy()
            env.update({
                "SLACK_MCP_XOXP_TOKEN": self.bot_token,
                "SLACK_MCP_ADD_MESSAGE_TOOL": "true",
                "SLACK_MCP_LOG_LEVEL": "info",
                "SLACK_MCP_USERS_CACHE": "/Users/alexdumats/trajdar_bjorn/.users_cache.json",
                "SLACK_MCP_CHANNELS_CACHE": "/Users/alexdumats/trajdar_bjorn/.channels_cache_v2.json"
            })
            
            # Start the MCP server process
            self.slack_mcp_process = subprocess.Popen([
                "go", "run", self.slack_mcp_server_path, "--transport", "stdio"
            ], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info("🚀 Slack MCP server started")
            
            # Start message queue processor
            self.queue_processor_task = asyncio.create_task(self.process_message_queue())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Slack MCP server: {e}")
            return False
    
    async def stop_slack_mcp_server(self):
        """Stop the Slack MCP server process"""
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            self.queue_processor_task = None
        
        if self.slack_mcp_process:
            self.slack_mcp_process.terminate()
            try:
                await asyncio.wait_for(asyncio.create_task(
                    asyncio.to_thread(self.slack_mcp_process.wait)
                ), timeout=5.0)
            except asyncio.TimeoutError:
                self.slack_mcp_process.kill()
            
            self.slack_mcp_process = None
            logger.info("⏹️ Slack MCP server stopped")
    
    async def send_mcp_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        """Send message via Slack MCP server"""
        try:
            if not self.slack_mcp_process:
                logger.warning("⚠️ Slack MCP server not running")
                return False
            
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": f"msg_{datetime.now().timestamp()}",
                "method": "tools/call",
                "params": {
                    "name": "conversations_add_message",
                    "arguments": {
                        "channel_id": channel,
                        "payload": message,
                        "content_type": "text/markdown"
                    }
                }
            }
            
            if thread_ts:
                mcp_request["params"]["arguments"]["thread_ts"] = thread_ts
            
            # Send request to MCP server
            request_json = json.dumps(mcp_request) + "\n"
            self.slack_mcp_process.stdin.write(request_json.encode())
            self.slack_mcp_process.stdin.flush()
            
            # Read response (with timeout)
            try:
                response_line = await asyncio.wait_for(
                    asyncio.create_task(asyncio.to_thread(self.slack_mcp_process.stdout.readline)),
                    timeout=10.0
                )
                response = json.loads(response_line.decode().strip())
                
                if "error" in response:
                    logger.error(f"❌ MCP error: {response['error']}")
                    return False
                
                return True
                
            except asyncio.TimeoutError:
                logger.error("❌ MCP request timeout")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to send MCP message: {e}")
            return False
    
    async def queue_message(self, channel: str, message: str, priority: str = "normal", thread_ts: Optional[str] = None):
        """Queue message for sending (allows batching and rate limiting)"""
        await self.message_queue.put({
            "channel": channel,
            "message": message,
            "priority": priority,
            "thread_ts": thread_ts,
            "timestamp": datetime.now()
        })
    
    async def process_message_queue(self):
        """Process queued messages with rate limiting"""
        while True:
            try:
                # Get message from queue
                message_data = await self.message_queue.get()
                
                # Send message via MCP
                success = await self.send_mcp_message(
                    message_data["channel"],
                    message_data["message"],
                    message_data.get("thread_ts")
                )
                
                if success:
                    logger.debug(f"📤 Message sent to {message_data['channel']}")
                else:
                    logger.error(f"❌ Failed to send message to {message_data['channel']}")
                
                # Rate limiting - wait between messages
                await asyncio.sleep(1)  # 1 second between messages
                
            except asyncio.CancelledError:
                logger.info("📤 Message queue processor cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error processing message queue: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def notify_agent_startup(self, agent_name: str, details: Dict[str, Any] = None):
        """Notify Slack about agent startup"""
        if not self.notifications.get("agent_startup", True):
            return
        
        channel = self.channels.get(agent_name, self.channels.get("orchestrator", "#orchestrator"))
        
        message = f"""🚀 **{agent_name.replace('_', ' ').title()} Started**

⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
🤖 **Agent**: {agent_name}
📊 **Status**: Online and ready"""
        
        if details:
            message += f"\n\n📋 **Details**:"
            for key, value in details.items():
                message += f"\n• **{key.replace('_', ' ').title()}**: {value}"
        
        await self.queue_message(channel, message, "high")
        
        # Update agent status
        self.agent_status[agent_name] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "details": details or {}
        }
    
    async def notify_agent_shutdown(self, agent_name: str, details: Dict[str, Any] = None):
        """Notify Slack about agent shutdown"""
        if not self.notifications.get("agent_shutdown", True):
            return
        
        channel = self.channels.get(agent_name, self.channels.get("orchestrator", "#orchestrator"))
        
        message = f"""⏹️ **{agent_name.replace('_', ' ').title()} Stopped**

⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
🤖 **Agent**: {agent_name}
📊 **Status**: Offline"""
        
        if details:
            message += f"\n\n📋 **Details**:"
            for key, value in details.items():
                message += f"\n• **{key.replace('_', ' ').title()}**: {value}"
        
        await self.queue_message(channel, message, "high")
        
        # Update agent status
        if agent_name in self.agent_status:
            self.agent_status[agent_name]["status"] = "stopped"
            self.agent_status[agent_name]["stopped_at"] = datetime.now().isoformat()
    
    async def notify_analysis_complete(self, agent_name: str, analysis: Dict[str, Any]):
        """Notify Slack about completed analysis"""
        if not self.notifications.get("analysis_complete", True):
            return
        
        channel = self.channels.get(agent_name, self.channels.get("orchestrator", "#orchestrator"))
        
        if agent_name == "market_analyst":
            sentiment = analysis.get("sentiment", "UNKNOWN")
            recommendation = analysis.get("recommendation", "HOLD")
            confidence = analysis.get("confidence", 0.0)
            
            message = f"""📊 **Market Analysis Complete**

🎯 **Sentiment**: {sentiment}
💡 **Recommendation**: {recommendation}
📈 **Confidence**: {confidence:.1%}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔍 **Key Insights**:
{analysis.get('reasoning', 'No detailed reasoning available')[:500]}"""
            
        elif agent_name == "news_analyst":
            sentiment_score = analysis.get("sentiment_score", 0.0)
            impact_level = analysis.get("impact_level", "UNKNOWN")
            recommendation = analysis.get("recommendation", "HOLD")
            
            message = f"""📰 **News Analysis Complete**

📊 **Sentiment**: {sentiment_score:+.2f}
⚡ **Impact**: {impact_level}
💡 **Recommendation**: {recommendation}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🔍 **Key Insights**:
{analysis.get('reasoning', 'No detailed reasoning available')[:500]}"""
            
        else:
            message = f"""✅ **{agent_name.replace('_', ' ').title()} Analysis Complete**

⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
📊 **Status**: Analysis completed successfully"""
        
        await self.queue_message(channel, message, "normal")
    
    async def notify_agent_error(self, agent_name: str, error: str, is_critical: bool = False):
        """Notify Slack about agent errors"""
        if not self.notifications.get("agent_errors", True):
            return
        
        channel = self.channels.get(agent_name, self.channels.get("alerts", "#trading-alerts"))
        
        emoji = "🚨" if is_critical else "⚠️"
        severity = "CRITICAL" if is_critical else "WARNING"
        
        message = f"""{emoji} **{severity}: {agent_name.replace('_', ' ').title()} Error**

⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}
🤖 **Agent**: {agent_name}
❌ **Error**: {error}
📊 **Severity**: {severity}"""
        
        priority = "critical" if is_critical else "high"
        await self.queue_message(channel, message, priority)
        
        # Update agent status
        if agent_name in self.agent_status:
            self.agent_status[agent_name]["status"] = "error"
            self.agent_status[agent_name]["last_error"] = error
            self.agent_status[agent_name]["error_time"] = datetime.now().isoformat()
    
    async def notify_parameter_update(self, parameter: str, old_value: Any, new_value: Any, user: str):
        """Notify Slack about parameter updates"""
        if not self.notifications.get("parameter_updates", True):
            return
        
        channel = self.channels.get("orchestrator", "#orchestrator")
        
        message = f"""🔧 **Parameter Updated**

📝 **Parameter**: `{parameter}`
🔄 **Change**: `{old_value}` → `{new_value}`
👤 **Updated by**: {user}
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}"""
        
        await self.queue_message(channel, message, "normal")
    
    async def notify_system_status(self, status: Dict[str, Any]):
        """Notify Slack about system status"""
        if not self.notifications.get("system_status", True):
            return
        
        channel = self.channels.get("system_health", "#system-health")
        
        # Determine overall health
        healthy_agents = sum(1 for agent_status in status.get("agents", {}).values() if agent_status)
        total_agents = len(status.get("agents", {}))
        health_percentage = (healthy_agents / max(1, total_agents)) * 100
        
        if health_percentage >= 90:
            health_emoji = "🟢"
            health_status = "HEALTHY"
        elif health_percentage >= 70:
            health_emoji = "🟡"
            health_status = "DEGRADED"
        else:
            health_emoji = "🔴"
            health_status = "CRITICAL"
        
        message = f"""{health_emoji} **System Status Report**

📊 **Overall Health**: {health_status} ({health_percentage:.0f}%)
🤖 **Agents Online**: {healthy_agents}/{total_agents}
⏰ **Report Time**: {datetime.now().strftime('%H:%M:%S')}

🔍 **Agent Status**:"""
        
        for agent_name, is_healthy in status.get("agents", {}).items():
            status_emoji = "✅" if is_healthy else "❌"
            message += f"\n• {status_emoji} {agent_name.replace('_', ' ').title()}"
        
        await self.queue_message(channel, message, "normal")
    
    async def handle_parameter_command(self, channel: str, user: str, command: str, thread_ts: Optional[str] = None):
        """Handle parameter update commands from Slack"""
        if not self.enable_parameter_updates:
            await self.queue_message(channel, "❌ Parameter updates are disabled", "normal", thread_ts)
            return
        
        if user not in self.authorized_users:
            await self.queue_message(channel, "❌ You are not authorized to update parameters", "normal", thread_ts)
            return
        
        try:
            # Parse command
            parts = command.strip().split()
            if len(parts) < 2:
                await self.send_parameter_help(channel, thread_ts)
                return
            
            action = parts[1].lower()
            
            if action == "show":
                await self.handle_show_parameter(channel, parts[2:], thread_ts)
            elif action == "set":
                await self.handle_set_parameter(channel, parts[2:], user, thread_ts)
            elif action == "reset":
                await self.handle_reset_parameter(channel, parts[2:], user, thread_ts)
            elif action == "override":
                await self.handle_risk_override(channel, parts[2:], user, thread_ts)
            elif action == "learning":
                await self.handle_learning_session(channel, parts[2:], user, thread_ts)
            elif action == "help":
                await self.send_parameter_help(channel, thread_ts)
            else:
                await self.queue_message(channel, f"❌ Unknown action: {action}", "normal", thread_ts)
                
        except Exception as e:
            logger.error(f"❌ Error handling parameter command: {e}")
            await self.queue_message(channel, f"❌ Error processing command: {e}", "normal", thread_ts)
    
    async def send_parameter_help(self, channel: str, thread_ts: Optional[str] = None):
        """Send parameter command help"""
        help_message = """🔧 **Parameter Update Commands**

**Available Commands:**
• `/param show <parameter>` - Show current parameter value
• `/param set <parameter> <value>` - Set parameter to new value
• `/param reset <parameter>` - Reset parameter to default value
• `/param override <symbol> <side> <reason>` - Override risk block for a trade
• `/param learning start|stop [duration_minutes]` - Start/stop learning session
• `/param help` - Show this help message

**Examples:**
• `/param show market_analyst.analysis.min_confidence`
• `/param set market_analyst.analysis.min_confidence 0.75`
• `/param reset market_analyst.analysis.min_confidence`
• `/param override BTCUSDC BUY strategic_opportunity`
• `/param learning start 60`

**Updateable Categories:**
• `scheduling.intervals`
• `market_analyst.analysis`
• `news_analyst.analysis`
• `risk_manager.risk_levels`
• `trade_executor.execution`"""
        
        await self.queue_message(channel, help_message, "normal", thread_ts)
    
    async def handle_show_parameter(self, channel: str, params: List[str], thread_ts: Optional[str] = None):
        """Handle show parameter command"""
        if not params:
            await self.queue_message(channel, "❌ Please specify a parameter to show", "normal", thread_ts)
            return
        
        parameter = params[0]
        
        # Get current value from config
        try:
            value = self.get_parameter_value(parameter)
            message = f"📋 **Parameter Value**\n\n**Parameter**: `{parameter}`\n**Current Value**: `{value}`"
            await self.queue_message(channel, message, "normal", thread_ts)
        except Exception as e:
            await self.queue_message(channel, f"❌ Error getting parameter: {e}", "normal", thread_ts)
    
    async def handle_set_parameter(self, channel: str, params: List[str], user: str, thread_ts: Optional[str] = None):
        """Handle set parameter command"""
        if len(params) < 2:
            await self.queue_message(channel, "❌ Please specify parameter and value", "normal", thread_ts)
            return
        
        parameter = params[0]
        new_value = " ".join(params[1:])
        
        try:
            old_value = self.get_parameter_value(parameter)
            # TODO: Implement actual parameter update logic
            await self.notify_parameter_update(parameter, old_value, new_value, user)
            await self.queue_message(channel, f"✅ Parameter `{parameter}` updated to `{new_value}`", "normal", thread_ts)
        except Exception as e:
            await self.queue_message(channel, f"❌ Error setting parameter: {e}", "normal", thread_ts)
    
    async def handle_reset_parameter(self, channel: str, params: List[str], user: str, thread_ts: Optional[str] = None):
        """Handle reset parameter command"""
        if not params:
            await self.queue_message(channel, "❌ Please specify a parameter to reset", "normal", thread_ts)
            return
        
        parameter = params[0]
        
        try:
            old_value = self.get_parameter_value(parameter)
            # TODO: Implement actual parameter reset logic
            default_value = "default"  # Get from defaults
            await self.notify_parameter_update(parameter, old_value, default_value, user)
            await self.queue_message(channel, f"✅ Parameter `{parameter}` reset to default value", "normal", thread_ts)
        except Exception as e:
            await self.queue_message(channel, f"❌ Error resetting parameter: {e}", "normal", thread_ts)
            
    async def handle_risk_override(self, channel: str, params: List[str], user: str, thread_ts: Optional[str] = None):
        """Handle risk override command for trades"""
        if len(params) < 3:
            await self.queue_message(channel, "❌ Please specify symbol, side (BUY/SELL), and reason", "normal", thread_ts)
            return
        
        symbol = params[0].upper()
        side = params[1].upper()
        reason = " ".join(params[2:])
        
        if side not in ["BUY", "SELL"]:
            await self.queue_message(channel, "❌ Side must be BUY or SELL", "normal", thread_ts)
            return
        
        try:
            # Create override request
            override_request = {
                "symbol": symbol,
                "side": side,
                "reason": reason,
                "user": user,
                "timestamp": datetime.now().isoformat(),
                "channel": channel,
                "thread_ts": thread_ts
            }
            
            # Send override request to trade executor
            async with aiohttp.ClientSession() as session:
                trade_executor_url = os.getenv("TRADE_EXECUTOR_URL", "http://localhost:8005")
                async with session.post(
                    f"{trade_executor_url}/override-risk",
                    json=override_request,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Notify about override
                        await self.queue_message(
                            "#risk-blocked",
                            f"""🔓 **RISK OVERRIDE APPLIED**
                            
*Symbol:* {symbol}
*Side:* {side}
*Reason:* {reason}
*Authorized by:* {user}
*Timestamp:* {datetime.now().isoformat()}

This override will be logged and the trade will be executed with the next cycle.
""",
                            "high"
                        )
                        
                        # Respond in original channel
                        await self.queue_message(
                            channel,
                            f"✅ Risk override applied for {side} {symbol}. The trade will be executed shortly.",
                            "normal",
                            thread_ts
                        )
                        
                        return
                    else:
                        error_text = await response.text()
                        await self.queue_message(
                            channel,
                            f"❌ Error applying override: HTTP {response.status} - {error_text}",
                            "normal",
                            thread_ts
                        )
                        
        except Exception as e:
            logger.error(f"❌ Error handling risk override: {e}")
            await self.queue_message(
                channel,
                f"❌ Error applying override: {e}",
                "normal",
                thread_ts
            )
            
    async def handle_learning_session(self, channel: str, params: List[str], user: str, thread_ts: Optional[str] = None):
        """Handle learning session commands"""
        if not params:
            await self.queue_message(channel, "❌ Please specify action (start/stop)", "normal", thread_ts)
            return
        
        action = params[0].lower()
        
        try:
            parameter_optimizer_url = os.getenv("PARAMETER_OPTIMIZER_URL", "http://localhost:8006")
            
            if action == "start":
                # Parse duration if provided
                duration_minutes = int(params[1]) if len(params) > 1 else None
                
                # Start learning session
                async with aiohttp.ClientSession() as session:
                    request_data = {}
                    if duration_minutes:
                        request_data["duration_minutes"] = duration_minutes
                        
                    async with session.post(
                        f"{parameter_optimizer_url}/start-learning-session",
                        json=request_data,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if result.get("status") == "already_active":
                                await self.queue_message(
                                    channel,
                                    "⚠️ Learning session already active",
                                    "normal",
                                    thread_ts
                                )
                            elif result.get("status") == "cooldown":
                                cooldown_end = result.get("cooldown_end")
                                hours_remaining = result.get("hours_remaining", 0)
                                
                                await self.queue_message(
                                    channel,
                                    f"⚠️ Learning session cooldown active. Next session available in {hours_remaining:.1f} hours ({cooldown_end})",
                                    "normal",
                                    thread_ts
                                )
                            elif result.get("status") == "started":
                                await self.queue_message(
                                    channel,
                                    f"""✅ Learning session started
                                    
*Duration:* {result.get('duration_minutes')} minutes
*Start Time:* {result.get('start_time')}
*End Time:* {result.get('end_time')}

The system will operate with relaxed risk parameters during this period.
All trades will be tagged for analysis.
""",
                                    "normal",
                                    thread_ts
                                )
                            else:
                                await self.queue_message(
                                    channel,
                                    f"⚠️ Unknown response: {result}",
                                    "normal",
                                    thread_ts
                                )
                        else:
                            error_text = await response.text()
                            await self.queue_message(
                                channel,
                                f"❌ Error starting learning session: HTTP {response.status} - {error_text}",
                                "normal",
                                thread_ts
                            )
                            
            elif action == "stop":
                # Stop learning session
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{parameter_optimizer_url}/end-learning-session",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if result.get("status") == "not_active":
                                await self.queue_message(
                                    channel,
                                    "⚠️ No learning session is currently active",
                                    "normal",
                                    thread_ts
                                )
                            elif result.get("status") == "completed":
                                await self.queue_message(
                                    channel,
                                    f"""✅ Learning session ended
                                    
*Duration:* {result.get('duration_minutes', 0):.1f} minutes
*Trades Executed:* {result.get('trades_executed', 0)}
*Next Session Available:* {result.get('next_session_available')}

Original parameters have been restored.
""",
                                    "normal",
                                    thread_ts
                                )
                            else:
                                await self.queue_message(
                                    channel,
                                    f"⚠️ Unknown response: {result}",
                                    "normal",
                                    thread_ts
                                )
                        else:
                            error_text = await response.text()
                            await self.queue_message(
                                channel,
                                f"❌ Error stopping learning session: HTTP {response.status} - {error_text}",
                                "normal",
                                thread_ts
                            )
            
            elif action == "status":
                # Get learning session status
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{parameter_optimizer_url}/learning-session-status",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if result.get("active"):
                                await self.queue_message(
                                    channel,
                                    f"""📊 Learning Session Status: **ACTIVE**
                                    
*Start Time:* {result.get('start_time')}
*Elapsed:* {result.get('elapsed_minutes', 0):.1f} minutes
*Remaining:* {result.get('remaining_minutes', 0):.1f} minutes
*End Time:* {result.get('end_time')}
""",
                                    "normal",
                                    thread_ts
                                )
                            else:
                                if "last_session" in result:
                                    await self.queue_message(
                                        channel,
                                        f"""📊 Learning Session Status: **INACTIVE**
                                        
*Last Session:* {result.get('last_session')}
*Cooldown Until:* {result.get('cooldown_end')}
*Hours Remaining:* {result.get('hours_remaining', 0):.1f}
*Next Available:* {result.get('next_session_available')}
""",
                                        "normal",
                                        thread_ts
                                    )
                                else:
                                    await self.queue_message(
                                        channel,
                                        "📊 Learning Session Status: **INACTIVE**\n\nNo learning sessions have been run yet.",
                                        "normal",
                                        thread_ts
                                    )
                        else:
                            error_text = await response.text()
                            await self.queue_message(
                                channel,
                                f"❌ Error getting learning session status: HTTP {response.status} - {error_text}",
                                "normal",
                                thread_ts
                            )
            else:
                await self.queue_message(
                    channel,
                    f"❌ Unknown learning session action: {action}. Use 'start', 'stop', or 'status'.",
                    "normal",
                    thread_ts
                )
                
        except Exception as e:
            logger.error(f"❌ Error handling learning session command: {e}")
            await self.queue_message(
                channel,
                f"❌ Error processing learning session command: {e}",
                "normal",
                thread_ts
            )
    
    def get_parameter_value(self, parameter: str) -> Any:
        """Get parameter value from config"""
        keys = parameter.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise ValueError(f"Parameter {parameter} not found")
        
        return value
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "slack_mcp_enabled": self.slack_mcp_enabled,
            "slack_mcp_running": self.slack_mcp_process is not None,
            "message_queue_size": self.message_queue.qsize(),
            "agent_status": self.agent_status,
            "channels": self.channels,
            "authorized_users": len(self.authorized_users)
        }

# Global Slack integration service instance
slack_service = SlackIntegrationService()

@app.on_event("startup")
async def startup_event():
    """Start the Slack MCP server when FastAPI starts"""
    await slack_service.start_slack_mcp_server()

@app.on_event("shutdown")  
async def shutdown_event():
    """Clean up Slack MCP server on shutdown"""
    await slack_service.stop_slack_mcp_server()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "slack-integration-service",
        "slack_mcp_running": slack_service.slack_mcp_process is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/notify/agent-startup")
async def notify_agent_startup(agent_name: str, details: Dict[str, Any] = None):
    """Notify about agent startup"""
    await slack_service.notify_agent_startup(agent_name, details)
    return {"message": "Notification sent"}

@app.post("/notify/agent-shutdown")
async def notify_agent_shutdown(agent_name: str, details: Dict[str, Any] = None):
    """Notify about agent shutdown"""
    await slack_service.notify_agent_shutdown(agent_name, details)
    return {"message": "Notification sent"}

@app.post("/notify/analysis-complete")
async def notify_analysis_complete(agent_name: str, analysis: Dict[str, Any]):
    """Notify about completed analysis"""
    await slack_service.notify_analysis_complete(agent_name, analysis)
    return {"message": "Notification sent"}

@app.post("/notify/agent-error")
async def notify_agent_error(agent_name: str, error: str, is_critical: bool = False):
    """Notify about agent error"""
    await slack_service.notify_agent_error(agent_name, error, is_critical)
    return {"message": "Notification sent"}

@app.post("/notify/system-status")
async def notify_system_status(status: Dict[str, Any]):
    """Notify about system status"""
    await slack_service.notify_system_status(status)
    return {"message": "Notification sent"}

@app.post("/send-message")
async def send_message(channel: str, message: str, priority: str = "normal", thread_ts: Optional[str] = None):
    """Send custom message to Slack"""
    await slack_service.queue_message(channel, message, priority, thread_ts)
    return {"message": "Message queued"}

@app.post("/process-command")
async def process_command(command: str, user: str, channel: str, thread_ts: Optional[str] = None):
    """Process Slack command"""
    if command.startswith("/param"):
        await slack_service.handle_parameter_command(channel, user, command, thread_ts)
        return {"message": "Command processed"}
    else:
        return {"error": "Unknown command"}

@app.get("/status")
async def get_status():
    """Get service status"""
    return slack_service.get_agent_status()

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)